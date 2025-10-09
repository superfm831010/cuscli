import subprocess
import os
import time
import uuid
from typing import Dict, Any, Optional
from autocoder.common.run_cmd import run_cmd_subprocess
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
# Import ToolResult from types
from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool, ToolResult
from autocoder.common.v2.agent.agentic_edit_tools.dangerous_command_checker import DangerousCommandChecker
from autocoder.common import shells
from autocoder.common.printer import Printer
from loguru import logger
import typing
from autocoder.common.pruner.context_pruner import PruneContext
from autocoder.common.tokens import count_string_tokens as count_tokens
from autocoder.common import SourceCode
from autocoder.common import AutoCoderArgs
from autocoder.events.event_manager_singleton import get_event_manager
from autocoder.run_context import get_run_context
from autocoder.common.shell_commands import (
    execute_command, 
    execute_command_background,
    execute_commands,
    CommandTimeoutError, 
    CommandExecutionError
)
from autocoder.common.shell_commands import get_background_process_notifier
from autocoder.common.wrap_llm_hint.utils import add_hint_to_text
import shlex
import json
import yaml
from typing import List, Union
import textwrap
from pydantic import BaseModel
from datetime import datetime

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class BackgroundCommandInfo(BaseModel):
    """Information about a background command execution."""
    model_config = {"frozen": True, "extra": "forbid"}
    
    pid: int
    process_uniq_id: str
    command: str
    working_directory: str
    background: bool = True
    start_time: Optional[str] = None
    status: str = "running"


class CommandErrorInfo(BaseModel):
    """Information about a command execution error."""
    model_config = {"frozen": True, "extra": "forbid"}
    
    output: str
    returncode: int


class BatchCommandSummary(BaseModel):
    """Summary information for batch command execution."""
    model_config = {"frozen": True, "extra": "forbid"}
    
    total: int
    successful: int
    failed: int
    timed_out: int
    execution_mode: str


class BatchCommandContent(BaseModel):
    """Content for batch command execution results."""
    model_config = {"frozen": True, "extra": "forbid"}
    
    batch_results: List[Dict[str, Any]]
    summary: BatchCommandSummary


class TimeoutErrorInfo(BaseModel):
    """Information about a command timeout error."""
    model_config = {"frozen": True, "extra": "forbid"}
    
    error_type: str = "timeout"
    command: str
    timeout_seconds: int
    working_directory: str
    suggested_timeout: int
    original_error: str


class ExecuteCommandToolResolver(BaseToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: ExecuteCommandTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: ExecuteCommandTool = tool  # For type hinting
        
        # Initialize AutoCoderArgs parser for flexible parameter parsing
        self.args_parser = AutoCoderArgsParser()
        
        # 初始化 context_pruner，使用解析后的 token 值
        max_tokens = self._get_parsed_safe_zone_tokens()
        llm = self.agent.context_prune_llm if self.agent else None
        if llm:
            self.context_pruner = PruneContext(
                max_tokens=max_tokens,
                args=self.args,
                llm=llm
            )
        else:
            self.context_pruner = None
        # 初始化危险命令检查器
        self.danger_checker = DangerousCommandChecker()

    def _get_parsed_safe_zone_tokens(self) -> int:
        """
        解析 context_prune_safe_zone_tokens 参数，支持多种格式
        
        Returns:
            解析后的 token 数量
        """
        return self.args_parser.parse_context_prune_safe_zone_tokens(
            self.args.context_prune_safe_zone_tokens,
            self.args.code_model
        )

    def _prune_command_output_with_file_backup(self, output: str, context_name: str = "command_output") -> str:
        """
        检查输出是否超过60k tokens，如果超过则裁剪并保存完整输出到文件
        
        Args:
            output: 命令输出内容
            context_name: 上下文名称，用于标识输出来源
            
        Returns:
            str: 处理后的输出内容
        """
        if not output:
            return output
            
        try:
            # 使用 tokens 模块检查 token 数量
            token_count = count_tokens(output)
            
            # 如果不超过 6k tokens，直接返回原输出
            if token_count <= 6000:
                return output
            
            # 超过 6k tokens，需要裁剪并保存完整文件
            logger.info(f"Output token count ({token_count}) exceeds 6k, pruning and saving to file")
            
            # 创建保存目录
            home_dir = os.path.expanduser("~")
            save_dir = os.path.join(home_dir, ".auto-coder", "tool-result", "execute_command")
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名（时间+uuid）
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_uuid = str(uuid.uuid4())[:8]  # 使用前8位UUID
            filename = f"{timestamp}_{file_uuid}.txt"
            full_file_path = os.path.join(save_dir, filename)
            
            # 保存完整输出到文件
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Command Output - Full Content\n")
                f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Context: {context_name}\n")
                f.write(f"# Token count: {token_count}\n")
                f.write(f"# File size: {len(output)} characters\n")
                f.write(f"{'='*60}\n\n")
                f.write(output)
            
            # 获取最后6000个字符
            pruned_output = output[-6000:]
            
            # 使用 wrap_llm_hint 模块添加标准化提示信息
            hint_message = f"""⚠️  OUTPUT TRUNCATED - Only showing last 6,000 characters

📊 Original output: {token_count:,} tokens, {len(output):,} characters
💾 Full content saved to: {full_file_path}

💡 To read the full output or search within it, use:
   read_file tool with path: {full_file_path}
   
   You can also use the query parameter to search for specific content:
   <read_file>
   <path>{full_file_path}</path>
   <query>your search term</query>
   </read_file>"""
            
            return add_hint_to_text(pruned_output, hint_message)
            
        except Exception as e:
            logger.error(f"Error in _prune_command_output_with_file_backup: {str(e)}")
            # 如果处理失败，回退到原始的剪枝方法
            return self._prune_file_content(output, context_name)

    def _prune_file_content(self, content: str, file_path: str) -> str:
        """对文件内容进行剪枝处理"""
        if not self.context_pruner:
            return content

        # 计算 token 数量
        tokens = count_tokens(content)
        safe_zone_tokens = self._get_parsed_safe_zone_tokens()
        if tokens <= safe_zone_tokens:
            return content

        # 创建 SourceCode 对象
        source_code = SourceCode(
            module_name=file_path,
            source_code=content,
            tokens=tokens
        )

        # 使用 context_pruner 进行剪枝
        strategy = self.args.context_prune_strategy or "extract"  # 默认策略
        pruned_sources = self.context_pruner.handle_overflow(
            file_sources=[source_code],
            conversations=self.agent.current_conversations if self.agent else [],
            strategy=strategy
        )

        if not pruned_sources:
            return content

        return pruned_sources[0].source_code

    def _execute_background_command(self, command: str, source_dir: str) -> ToolResult:
        """执行后台命令并返回PID"""
        try:
            # 使用 shell_commands 模块的后台执行功能
            process_info = execute_command_background(
                command=command,
                cwd=source_dir,
                verbose=False  # Use default verbose setting
            )
            
            pid = process_info["pid"]
            logger.info(f"Started background command: {command} with PID: {pid}\n. Don't forget to kill the process when you don't need it.")

            # Register with BackgroundProcessNotifier
            try:
                conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                if conversation_id:
                    notifier = get_background_process_notifier()
                    notifier.register_process(
                        conversation_id=conversation_id,
                        pid=pid,
                        tool_name="ExecuteCommandTool",
                        command=command,
                        cwd=source_dir,
                    )
            except Exception as e:
                logger.warning(f"Failed to register background process to notifier: {e}")
            
            # 获取 process_uniq_id
            process_uniq_id = process_info.get("process_uniq_id")
            
            # 返回成功结果，包含PID和process_uniq_id信息
            background_info = BackgroundCommandInfo(
                pid=pid,
                process_uniq_id=process_uniq_id,
                command=command,
                working_directory=source_dir,
                background=True,
                start_time=process_info.get("start_time"),
                status=process_info.get("status", "running")
            )
            
            return ToolResult(
                success=True,
                message=f"Background command started successfully with PID: {pid}, ID: {process_uniq_id}",
                content=background_info.model_dump()
            )
            
        except Exception as e:
            logger.error(f"Error starting background command '{command}': {str(e)}")
            return ToolResult(
                success=False,
                message=f"Failed to start background command: {str(e)}"
            )

    def _parse_batch_commands(self, command_str: str) -> Optional[Union[List[str], Dict[str, Any]]]:
        """
        解析批量命令，支持 JSON、YAML 和换行分隔格式
        
        返回:
            - List[str]: 命令列表
            - Dict: 包含 'mode' 和 'cmds' 的字典
            - None: 如果不是批量命令格式
        """
        # 去除整体缩进，兼容 <execute_command> 标签内被统一缩进的情况
        command_str = textwrap.dedent(command_str).strip()
        if not command_str:
            return None
        
        # 1. 尝试 JSON 解析
        try:
            parsed = json.loads(command_str)
            if isinstance(parsed, list) and all(isinstance(cmd, str) for cmd in parsed):
                return parsed
            elif isinstance(parsed, dict) and ('cmds' in parsed or 'commands' in parsed):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 2. 尝试 YAML 解析
        try:
            parsed = yaml.safe_load(command_str)
            if isinstance(parsed, list) and all(isinstance(cmd, str) for cmd in parsed):
                return parsed
            elif isinstance(parsed, dict):
                # 处理类似 "mode: serial\ncmds:\n  - cmd1\n  - cmd2" 的格式
                if 'cmds' in parsed:
                    return parsed
                # 处理简单的 key-value 对，但不是命令格式
                elif not any(key in parsed for key in ['mode', 'cmds', 'commands']):
                    return None
        except (yaml.YAMLError, ValueError):
            pass
        
        # 3. 尝试换行分隔
        lines = [line.strip() for line in command_str.splitlines() if line.strip()]
        if len(lines) > 1:
            # 检查是否是 shell 脚本格式（第一行是 shebang 或注释）
            if lines[0].startswith('#'):
                # 如果第一行是 "# serial" 或 "# parallel"，提取模式
                if lines[0].lower() in ['# serial', '#serial']:
                    return {'mode': 'serial', 'cmds': lines[1:]}
                elif lines[0].lower() in ['# parallel', '#parallel']:
                    return {'mode': 'parallel', 'cmds': lines[1:]}
            # 否则当做一个命令，而不是批量命令
            return None
        
        # 不是批量命令格式
        return None

    def _execute_batch_commands(self, commands: Union[List[str], Dict[str, Any]], source_dir: str, 
                               timeout: Optional[int], requires_approval: bool) -> ToolResult:
        """执行批量命令"""
        # 解析命令和模式
        if isinstance(commands, dict):
            mode = commands.get('mode', 'parallel').lower()
            cmd_list = commands.get('cmds', commands.get('commands', []))
            parallel = mode != 'serial'
        else:
            cmd_list = commands
            parallel = True  # 默认并行
        
        # 确保 cmd_list 是字符串列表
        if not isinstance(cmd_list, list):
            return ToolResult(
                success=False,
                message="Invalid command list format"
            )
        
        # 类型转换和验证
        validated_cmds: List[str] = []
        for cmd in cmd_list:
            if isinstance(cmd, str):
                validated_cmds.append(cmd)
            else:
                return ToolResult(
                    success=False,
                    message=f"Invalid command type: expected string, got {type(cmd).__name__}"
                )
        
        if not validated_cmds:
            return ToolResult(
                success=False,
                message="No commands found in batch command list"
            )
        
        # 危险命令检查
        if self.args.enable_agentic_dangerous_command_check:
            for cmd in validated_cmds:
                is_safe, danger_reason = self.danger_checker.check_command_safety(
                    cmd, allow_whitelist_bypass=True)
                if not is_safe:
                    recommendations = self.danger_checker.get_safety_recommendations(cmd)
                    error_message = f"检测到危险命令: {cmd}\n原因: {danger_reason}"
                    if recommendations:
                        error_message += f"\n安全建议:\n" + "\n".join(f"- {rec}" for rec in recommendations)
                    return ToolResult(success=False, message=error_message)
        
        # 批量审批
        if not self.args.enable_agentic_auto_approve and requires_approval:
            approval_message = f"Allow to execute {len(validated_cmds)} commands"
            if not parallel:
                approval_message += " (serial execution)"
            approval_message += "?\n\nCommands:\n" + "\n".join(f"  {i+1}. {cmd}" for i, cmd in enumerate(validated_cmds))
            
            try:
                if get_run_context().is_web():
                    answer = get_event_manager(self.args.event_file).ask_user(
                        prompt=approval_message, 
                        options=["yes", "no"]
                    )
                    if answer != "yes":
                        return ToolResult(
                            success=False, 
                            message=f"Batch command execution denied by user."
                        )
            except Exception as e:
                logger.error(f"Error when asking user to approve batch commands: {str(e)}")
                return ToolResult(
                    success=False, 
                    message=f"An unexpected error occurred while asking for approval: {str(e)}"
                )
        
        # 执行批量命令
        try:
            logger.info(f"Executing {len(validated_cmds)} commands ({'parallel' if parallel else 'serial'} mode)")
            
            # 计算超时参数
            per_command_timeout = None
            if timeout:
                if parallel:
                    # 并行模式：每个命令都可以用完整的超时时间
                    per_command_timeout = timeout
                else:
                    # 串行模式：平分超时时间（至少给每个命令10秒）
                    per_command_timeout = max(timeout / len(validated_cmds), 10.0)
            
            # 使用 shell_commands 的批量执行功能
            # 创建符合 execute_commands 类型要求的命令列表
            typed_commands: List[Union[str, List[str]]] = validated_cmds  # type: ignore
            results = execute_commands(
                commands=typed_commands,
                parallel=parallel,
                per_command_timeout=per_command_timeout,
                timeout=timeout,
                cwd=source_dir,
                verbose=True
            )
            
            # 统计结果
            successful = sum(1 for r in results if r['exit_code'] == 0)
            failed = sum(1 for r in results if r['exit_code'] != 0 and not r['timed_out'])
            timed_out = sum(1 for r in results if r['timed_out'])
            
            # 构建汇总消息
            summary_parts = []
            if successful > 0:
                summary_parts.append(f"{successful} succeeded")
            if failed > 0:
                summary_parts.append(f"{failed} failed")
            if timed_out > 0:
                summary_parts.append(f"{timed_out} timed out")
            
            summary = f"Batch execution completed: {', '.join(summary_parts)}"
            
            # 对每个命令的输出进行裁剪
            for result in results:
                if 'output' in result and result['output']:
                    result['output'] = self._prune_command_output_with_file_backup(
                        result['output'], 
                        f"command_{result['index']}_output"
                    )
            
            batch_summary = BatchCommandSummary(
                total=len(results),
                successful=successful,
                failed=failed,
                timed_out=timed_out,
                execution_mode='parallel' if parallel else 'serial'
            )
            
            batch_content = BatchCommandContent(
                batch_results=results,
                summary=batch_summary
            )
            
            return ToolResult(
                success=all(r['exit_code'] == 0 for r in results),
                message=summary,
                content=batch_content.model_dump()
            )
            
        except Exception as e:
            logger.error(f"Error executing batch commands: {str(e)}")
            return ToolResult(
                success=False,
                message=f"An unexpected error occurred while executing batch commands: {str(e)}"
            )

    def resolve(self) -> ToolResult:
        command = self.tool.command
        requires_approval = self.tool.requires_approval
        background = self.tool.background  # 获取后台运行选项
        source_dir = self.args.source_dir or "."
        
        # 尝试解析批量命令
        batch_commands = self._parse_batch_commands(command)
        if batch_commands is not None:
            # 检查是否是批量命令（多于1个命令）
            if isinstance(batch_commands, list) and len(batch_commands) > 1:
                # 是批量命令列表
                return self._execute_batch_commands(batch_commands, source_dir, self.tool.timeout, requires_approval)
            elif isinstance(batch_commands, dict) and (batch_commands.get('cmds') or batch_commands.get('commands')):
                # 是包含命令列表的字典格式
                return self._execute_batch_commands(batch_commands, source_dir, self.tool.timeout, requires_approval)
            # 如果只有一个命令，继续按单个命令处理
            elif isinstance(batch_commands, list) and len(batch_commands) == 1:
                command = batch_commands[0]
            elif isinstance(batch_commands, dict):
                # 检查是否只有一个命令
                cmd_list = batch_commands.get('cmds', batch_commands.get('commands', []))
                if len(cmd_list) == 1:
                    command = cmd_list[0]

        if self.args.enable_agentic_dangerous_command_check:
            # 使用新的危险命令检查器进行安全检查
            is_safe, danger_reason = self.danger_checker.check_command_safety(
                command, allow_whitelist_bypass=True)

            if not is_safe:
                # 获取安全建议
                recommendations = self.danger_checker.get_safety_recommendations(
                    command)

                error_message = f"检测到危险命令: {danger_reason}"
                if recommendations:
                    error_message += f"\n安全建议:\n" + \
                        "\n".join(f"- {rec}" for rec in recommendations)

                logger.warning(f"阻止执行危险命令: {command}, 原因: {danger_reason}")
                return ToolResult(success=False, message=error_message)

        # Approval mechanism (simplified)
        if not self.args.enable_agentic_auto_approve and requires_approval:
            logger.info(
                f"Executing command: {command} in {os.path.abspath(source_dir)}")
            try:
                # 使用封装的run_cmd方法执行命令
                if get_run_context().is_web():
                    answer = get_event_manager(
                        self.args.event_file).ask_user(prompt=f"Allow to execute the `{command}`?", options=["yes", "no"])
                    if answer == "yes":
                        pass
                    else:
                        return ToolResult(success=False, message=f"Command '{command}' execution denied by user.")
            except Exception as e:
                logger.error(
                    f"Error when ask the user to approve the command '{command}': {str(e)}")
                return ToolResult(success=False, message=f"An unexpected error occurred while asking the user to approve the command: {str(e)}")

        # 如果是后台运行，使用专门的后台执行方法
        if background:
            return self._execute_background_command(command, source_dir)

        # 如果不是后台运行，继续使用原来的前台执行逻辑
        try:
            # 根据配置选择使用新的 shell_commands 模块还是旧的 run_cmd 模块
            use_shell_commands = self.args.use_shell_commands

            # 获取超时参数
            timeout = self.tool.timeout  # 使用工具中的超时参数

            if use_shell_commands:
                # 使用新的 shell_commands 模块
                logger.debug(
                    f"Using shell_commands module for command execution (timeout: {timeout}s)")
                try:
                    exit_code, output = execute_command(
                        command, timeout=timeout, verbose=True, cwd=source_dir)
                except CommandTimeoutError as e:
                    logger.error(f"Command timed out: {e}")
                    return self._build_timeout_error_result(command, timeout, source_dir, e)
                except CommandExecutionError as e:
                    logger.error(f"Command execution failed: {e}")
                    return ToolResult(success=False, message=f"Command execution failed: {str(e)}")
            else:
                # 使用旧的 run_cmd 模块（不支持超时）
                logger.debug("Using run_cmd module for command execution (note: timeout not supported)")
                exit_code, output = run_cmd_subprocess(
                    command, verbose=True, cwd=source_dir)

            logger.info(f"Command executed: {command}")
            logger.info(f"Return Code: {exit_code}")
            if output:
                # Avoid logging potentially huge output directly
                logger.info(f"Original Output (length: {len(output)} chars)")

            final_output = self._prune_command_output_with_file_backup(output, "command_output")

            if exit_code == 0:
                return ToolResult(success=True, message="Command executed successfully.", content=final_output)
            else:
                # For the human-readable error message, we might prefer the original full output.
                # For the agent-consumable content, we provide the (potentially pruned) final_output.
                error_message_for_human = f"Command failed with return code {exit_code}.\nOutput:\n{output}"
                
                error_info = CommandErrorInfo(
                    output=final_output,
                    returncode=exit_code
                )
                
                return ToolResult(success=False, message=error_message_for_human, content=error_info.model_dump())

        except FileNotFoundError:
            return ToolResult(success=False, message=f"Error: The command '{command.split()[0]}' was not found. Please ensure it is installed and in the system's PATH.")
        except PermissionError:
            return ToolResult(success=False, message=f"Error: Permission denied when trying to execute '{command}'.")
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return ToolResult(success=False, message=f"An unexpected error occurred while executing the command: {str(e)}")

    def _build_timeout_error_result(self, command: str, timeout: Optional[int], source_dir: str, error: Exception) -> ToolResult:
        """构建超时错误结果"""
        # 处理超时值，确保不为 None
        actual_timeout = timeout if timeout is not None else 60
        suggested_timeout = actual_timeout * 2
        
        # 构建基本错误信息
        basic_error = f"""COMMAND TIMEOUT ERROR

Command: {command}
Timeout: {actual_timeout} seconds
Directory: {source_dir}

The command failed to complete within the specified timeout period."""
        
        # 构建详细的建议信息作为 hint
        suggestions_hint = f"""This usually indicates that:
1. The command is taking longer than expected to execute
2. The command may be waiting for user input or hanging
3. The command is processing large amounts of data

Suggestions:
• Increase the timeout value using: <timeout>{suggested_timeout}</timeout>
• Check if the command requires user interaction
• Consider breaking down complex commands into smaller steps
• Verify the command syntax and parameters are correct

Error details: {str(error)}"""
        
        # 使用 wrap_llm_hint 模块添加标准化提示信息
        timeout_message = add_hint_to_text(basic_error, suggestions_hint)
        
        timeout_info = TimeoutErrorInfo(
            error_type="timeout",
            command=command,
            timeout_seconds=actual_timeout,
            working_directory=source_dir,
            suggested_timeout=suggested_timeout,
            original_error=str(error)
        )
        
        return ToolResult(
            success=False, 
            message=timeout_message,
            content=timeout_info.model_dump()
        )
