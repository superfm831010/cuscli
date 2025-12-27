#!/usr/bin/env python3
"""
Run Named Subagents Tool Resolver

工具解析器，用于运行指定名称的子代理。支持 JSON 和 YAML 格式的解析，
通过 agent 名字获取 agent 详情，并通过 auto-coder.run 并行或串行执行多个子代理任务。
"""

import json
import platform
import shutil
import yaml
import shlex
import tempfile
import os
from typing import Optional, List, Dict, Any
import typing
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import (
    BaseToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import (
    RunNamedSubagentsTool,
    ToolResult,
)
from autocoder.common.agents import AgentManager
from autocoder.common.shell_commands import (
    execute_commands,
    execute_command_background,
    get_background_processes,
    get_background_process_info,
)
from autocoder.common.shell_commands import get_background_process_notifier
from loguru import logger


def _get_command_path(command: str) -> str:
    """获取命令的完整路径，确保 Windows 兼容性"""
    if os.path.isabs(command):
        return command
    full_path = shutil.which(command)
    if full_path:
        return full_path
    if platform.system() == "Windows":
        full_path = shutil.which(f"{command}.exe")
        if full_path:
            return full_path
    return command


if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class RunNamedSubagentsToolResolver(BaseToolResolver):
    """
    运行指定名称子代理的工具解析器

    功能：
    1. 支持 JSON 和 YAML 格式的子代理配置解析
    2. 通过 agent 名字从 AgentManager 获取 agent 详情
    3. 构建 auto-coder.run 命令
    4. 使用 shell_commands 模块实现并行或串行执行
    """

    def __init__(
        self,
        agent: Optional["AgenticEdit"],
        tool: RunNamedSubagentsTool,
        args: AutoCoderArgs,
    ):
        super().__init__(agent, tool, args)
        self.tool = tool  # 运行时导入的工具实例

        # 初始化 AgentManager
        project_root = args.source_dir if args.source_dir else "."
        self.agent_manager = AgentManager(project_root)

        # 用于管理临时文件的列表
        self.temp_files = []

    def resolve(self) -> ToolResult:
        """
        执行指定名称的子代理

        Returns:
            ToolResult: 执行结果
        """
        subagents_str = self.tool.subagents
        background = getattr(
            self.tool, "background", False
        )  # 获取后台运行参数，默认为False

        logger.info(
            f"正在解析 RunNamedSubagentsTool: Subagents='{subagents_str}', Background={background}"
        )

        try:
            # 1. 解析子代理配置
            subagents_config = self._parse_subagents_config(subagents_str)
            if not subagents_config["success"]:
                return ToolResult(
                    success=False,
                    message=subagents_config["error"],
                    content={"error_type": "config_parse_error"},
                )

            subagents_list = subagents_config["subagents"]
            execution_mode = subagents_config["mode"]

            logger.info(
                f"解析到 {len(subagents_list)} 个子代理，执行模式: {execution_mode}"
            )

            # 2. 验证所有子代理是否存在
            validation_result = self._validate_subagents(subagents_list)
            if not validation_result["success"]:
                return ToolResult(
                    success=False,
                    message=validation_result["error"],
                    content={
                        "error_type": "agent_validation_error",
                        "details": validation_result["details"],
                    },
                )

            # 3. 构建所有子代理的命令
            commands_result = self._build_subagent_commands(subagents_list)
            if not commands_result["success"]:
                # 如果命令构建失败，清理可能已创建的临时文件
                self._cleanup_temp_files()
                return ToolResult(
                    success=False,
                    message=commands_result["error"],
                    content={"error_type": "command_build_error"},
                )

            commands = commands_result["commands"]
            logger.info(f"构建了 {len(commands)} 个命令")

            # 格式化打印所有子代理的完整命令
            self._print_formatted_commands(commands, subagents_list)

            # 4. 根据 background 参数选择执行方式
            if background:
                # 后台运行模式
                logger.info(f"以后台模式启动 {len(commands)} 个子代理")
                background_processes = self._execute_commands_background(
                    commands, subagents_list
                )

                # 返回后台进程信息
                return ToolResult(
                    success=True,
                    message=f"成功启动 {len(background_processes)} 个后台子代理",
                    content={
                        "execution_mode": "background",
                        "total_subagents": len(subagents_list),
                        "background_processes": background_processes,
                    },
                )
            else:
                # 前台运行模式（原有逻辑）
                parallel = execution_mode == "parallel"
                # 从 AutoCoderArgs 获取子代理调用超时时间（秒），默认 30 分钟
                timeout_seconds = self.args.call_subagent_timeout
                results = execute_commands(
                    commands=commands,
                    parallel=parallel,
                    timeout=timeout_seconds + 60,
                    per_command_timeout=timeout_seconds,
                )

                # 5. 处理执行结果
                execution_summary = self._process_execution_results(
                    results, subagents_list
                )

            # 6. 清理临时文件
            self._cleanup_temp_files()

            if execution_summary["all_successful"]:
                logger.info(f"所有 {len(subagents_list)} 个子代理执行成功")
                return ToolResult(
                    success=True,
                    message=f"所有 {len(subagents_list)} 个子代理执行成功",
                    content={
                        "execution_mode": execution_mode,
                        "total_subagents": len(subagents_list),
                        "successful_count": execution_summary["successful_count"],
                        "failed_count": execution_summary["failed_count"],
                        "timed_out_count": execution_summary["timed_out_count"],
                        "results": execution_summary["detailed_results"],
                    },
                )
            else:
                error_msg = f"子代理执行完成，但有失败: {execution_summary['successful_count']}/{len(subagents_list)} 成功"
                logger.warning(error_msg)
                return ToolResult(
                    success=False,
                    message=error_msg,
                    content={
                        "execution_mode": execution_mode,
                        "total_subagents": len(subagents_list),
                        "successful_count": execution_summary["successful_count"],
                        "failed_count": execution_summary["failed_count"],
                        "timed_out_count": execution_summary["timed_out_count"],
                        "results": execution_summary["detailed_results"],
                    },
                )

        except Exception as e:
            logger.error(f"RunNamedSubagentsTool 执行出错: {str(e)}")
            # 确保在异常情况下也清理临时文件
            self._cleanup_temp_files()
            return ToolResult(
                success=False,
                message=f"执行子代理时发生错误: {str(e)}",
                content={"error_type": "execution_error", "error_details": str(e)},
            )

    def _parse_subagents_config(self, subagents_str: str) -> Dict[str, Any]:
        """
        解析子代理配置，支持 JSON 和 YAML 格式

        Args:
            subagents_str: 子代理配置字符串

        Returns:
            解析结果字典
        """
        try:
            # 尝试 JSON 格式解析
            try:
                json_data = json.loads(subagents_str)
                if isinstance(json_data, list):
                    # JSON 数组格式: [{"name": "xxx", "task": "task here"}]
                    return {
                        "success": True,
                        "subagents": json_data,
                        "mode": "parallel",  # JSON 格式默认并行
                    }
                else:
                    return {
                        "success": False,
                        "error": "JSON 格式必须是数组格式: [{'name': 'xxx', 'task': 'task here'}]",
                    }
            except json.JSONDecodeError:
                pass

            # 尝试 YAML 格式解析
            try:
                yaml_data = yaml.safe_load(subagents_str)
                if isinstance(yaml_data, dict):
                    if "subagents" in yaml_data:
                        # YAML 字典格式
                        mode = yaml_data.get("mode", "parallel")
                        if mode not in ["parallel", "serial"]:
                            return {
                                "success": False,
                                "error": f"无效的执行模式: {mode}。必须是 'parallel' 或 'serial'",
                            }

                        subagents = yaml_data["subagents"]
                        if not isinstance(subagents, list):
                            return {
                                "success": False,
                                "error": "YAML 格式中的 subagents 必须是列表",
                            }

                        return {"success": True, "subagents": subagents, "mode": mode}
                    else:
                        return {
                            "success": False,
                            "error": "YAML 格式必须包含 'subagents' 字段",
                        }
                elif isinstance(yaml_data, list):
                    # YAML 数组格式，当作 JSON 数组处理
                    return {"success": True, "subagents": yaml_data, "mode": "parallel"}
                else:
                    return {"success": False, "error": "YAML 格式必须是字典或数组"}
            except yaml.YAMLError as e:
                return {"success": False, "error": f"YAML 解析错误: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"配置解析失败: {str(e)}"}

    def _validate_subagents(
        self, subagents_list: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        验证所有子代理是否存在且格式正确

        Args:
            subagents_list: 子代理列表

        Returns:
            验证结果字典
        """
        validation_errors = []
        available_agents = self.agent_manager.get_agent_names()

        for i, subagent in enumerate(subagents_list):
            # 检查格式
            if not isinstance(subagent, dict):
                validation_errors.append(f"子代理 {i}: 必须是字典格式")
                continue

            if "name" not in subagent:
                validation_errors.append(f"子代理 {i}: 缺少 'name' 字段")
                continue

            if "task" not in subagent:
                validation_errors.append(f"子代理 {i}: 缺少 'task' 字段")
                continue

            agent_name = subagent["name"]
            task = subagent["task"]

            # 检查 agent 是否存在
            agent = self.agent_manager.get_agent(agent_name)
            if not agent:
                validation_errors.append(
                    f"子代理 {i}: 未找到名为 '{agent_name}' 的代理"
                )
                continue

            # 检查 task 是否为空
            if not task or not task.strip():
                validation_errors.append(f"子代理 {i}: task 不能为空")
                continue

        if validation_errors:
            error_msg = f"子代理验证失败:\n" + "\n".join(validation_errors)
            error_msg += f"\n\n可用的代理有：{', '.join(available_agents)}"
            return {"success": False, "error": error_msg, "details": validation_errors}

        return {"success": True}

    def _build_subagent_commands(
        self, subagents_list: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        为所有子代理构建 auto-coder.run 命令

        Args:
            subagents_list: 子代理列表

        Returns:
            命令构建结果字典
        """
        commands = []
        build_errors = []

        for i, subagent in enumerate(subagents_list):
            agent_name = subagent["name"]
            task = subagent["task"]

            try:
                # 获取 agent 详情
                agent = self.agent_manager.get_agent(agent_name)
                if not agent:
                    build_errors.append(f"子代理 {i} ({agent_name}): 无法获取代理详情")
                    continue

                # 获取模型
                current_model = self._get_current_model()
                model_to_use = agent.model or current_model

                if not model_to_use:
                    build_errors.append(f"子代理 {i} ({agent_name}): 没有可用的模型")
                    continue

                # 构建命令
                logger.info(f"构建命令: {task}, {model_to_use}, {agent.content}")
                command = self._build_autocoder_command(
                    task, model_to_use, agent.content
                )
                commands.append(command)

            except Exception as e:
                build_errors.append(
                    f"子代理 {i} ({agent_name}): 构建命令时出错: {str(e)}"
                )
                continue

        if build_errors:
            error_msg = f"命令构建失败:\n" + "\n".join(build_errors)
            return {"success": False, "error": error_msg}

        return {"success": True, "commands": commands}

    def _process_execution_results(
        self, results: List[Dict[str, Any]], subagents_list: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        处理执行结果

        Args:
            results: shell_commands 的执行结果
            subagents_list: 原始子代理列表

        Returns:
            处理后的结果摘要
        """
        successful_count = 0
        failed_count = 0
        timed_out_count = 0
        detailed_results = []

        for i, result in enumerate(results):
            subagent = (
                subagents_list[i]
                if i < len(subagents_list)
                else {"name": "unknown", "task": "unknown"}
            )

            if result["timed_out"]:
                timed_out_count += 1
                status = "timed_out"
            elif result["exit_code"] == 0:
                successful_count += 1
                status = "success"
            else:
                failed_count += 1
                status = "failed"

            detailed_results.append(
                {
                    "agent_name": subagent["name"],
                    "task": subagent["task"],
                    "status": status,
                    "exit_code": result["exit_code"],
                    "duration": result["duration"],
                    "output": (
                        result["output"][:1000] if result["output"] else ""
                    ),  # 限制输出长度
                    "error": result.get("error", ""),
                    "timed_out": result["timed_out"],
                }
            )

        return {
            "all_successful": failed_count == 0 and timed_out_count == 0,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "timed_out_count": timed_out_count,
            "detailed_results": detailed_results,
        }

    def _get_current_model(self) -> Optional[str]:
        """
        获取当前可用的模型

        Returns:
            当前模型名称，如果没有则返回 None
        """
        try:
            # 尝试从 args 中获取模型信息
            if hasattr(self.args, "model") and self.args.model:
                return self.args.model

            # 尝试从环境变量获取
            import os

            env_model = os.getenv("AUTO_CODER_MODEL")
            if env_model:
                return env_model

            # 如果有 agent 实例，尝试从其 llm 获取
            if self.agent and hasattr(self.agent, "llm") and self.agent.llm:
                if hasattr(self.agent.llm, "model_name"):
                    return self.agent.llm.model_name
                elif hasattr(self.agent.llm, "model"):
                    return self.agent.llm.model

            return None

        except Exception as e:
            logger.warning(f"获取当前模型时出错: {str(e)}")
            return None

    def _build_autocoder_command(
        self, query: str, model: str, system_prompt: str
    ) -> str:
        """
        构建 auto-coder.run 命令，将系统提示写入临时文件并使用 --system-prompt-path

        Args:
            query: 用户查询
            model: 模型名称
            system_prompt: 系统提示词

        Returns:
            构建的命令字符串
        """
        # 创建临时文件存储系统提示
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )

        try:
            # 写入系统提示内容
            temp_file.write(system_prompt)
            temp_file.flush()
            temp_file_path = temp_file.name

            # 记录临时文件路径，用于后续清理
            self.temp_files.append(temp_file_path)

        finally:
            temp_file.close()

        # 获取 auto-coder.run 的完整路径（Windows 兼容性）
        autocoder_cmd = _get_command_path("auto-coder.run")

        # 根据操作系统选择不同的引号转义方式
        if platform.system() == "Windows":
            # Windows: 使用双引号，内部双引号用 \" 转义
            safe_query = '"' + query.replace('"', '\\"') + '"'
            safe_model = '"' + model.replace('"', '\\"') + '"'
            safe_prompt_path = '"' + temp_file_path.replace('"', '\\"') + '"'
        else:
            # Unix: 使用 shlex.quote 进行安全的 shell 转义
            safe_query = shlex.quote(query)
            safe_model = shlex.quote(model)
            safe_prompt_path = shlex.quote(temp_file_path)

        # 构建命令，使用 --system-prompt-path 而不是 --system-prompt
        command = f"echo {safe_query} | {autocoder_cmd} --model {safe_model} --system-prompt-path {safe_prompt_path} --is-sub-agent"

        return command

    def _print_formatted_commands(
        self, commands: List[str], subagents_list: List[Dict[str, str]]
    ) -> None:
        """
        格式化打印所有子代理的完整命令

        Args:
            commands: 构建的命令列表
            subagents_list: 子代理列表
        """
        logger.info("=" * 80)
        logger.info("📋 SUBAGENT COMMANDS OVERVIEW")
        logger.info("=" * 80)

        for i, (command, subagent) in enumerate(zip(commands, subagents_list), 1):
            agent_name = subagent["name"]
            task = subagent["task"]

            logger.info(f"\n🤖 Subagent #{i}: {agent_name}")
            logger.info("─" * 60)
            logger.info(f"📝 Task: {task}")
            logger.info(f"💻 Command:")

            # 将长命令进行换行处理，便于阅读
            formatted_command = self._format_command_for_display(command)
            for line in formatted_command:
                logger.info(f"    {line}")

            if i < len(commands):
                logger.info("")  # 添加空行分隔不同的子代理

        logger.info("=" * 80)
        logger.info(f"📊 Total: {len(commands)} subagent(s) ready for execution")
        logger.info("=" * 80)

    def _format_command_for_display(self, command: str) -> List[str]:
        """
        将长命令格式化为易读的多行形式

        Args:
            command: 原始命令字符串

        Returns:
            格式化后的命令行列表
        """
        # 如果命令不太长，直接返回
        if len(command) <= 120:
            return [command]

        # 尝试在管道符号处分割
        if " | " in command:
            parts = command.split(" | ")
            lines = []
            for i, part in enumerate(parts):
                if i == 0:
                    lines.append(part + " \\")
                elif i == len(parts) - 1:
                    lines.append("  | " + part)
                else:
                    lines.append("  | " + part + " \\")
            return lines

        # 如果没有管道符号，尝试在重要的选项参数处分割
        # 查找 --model 和 --system-prompt 等关键参数
        import re

        # 尝试在重要参数前分割
        patterns = [r"(\s+--model\s+)", r"(\s+--system-prompt\s+)", r"(\s+--\w+\s+)"]

        for pattern in patterns:
            if re.search(pattern, command):
                # 在参数前分割
                parts = re.split(pattern, command)
                if len(parts) > 1:
                    lines = []
                    current_line = parts[0]

                    for i in range(1, len(parts), 2):
                        if i + 1 < len(parts):
                            param = parts[i]
                            value = parts[i + 1]

                            # 检查是否应该换行
                            next_part = param + value
                            if len(current_line + next_part) > 120:
                                lines.append(current_line + " \\")
                                current_line = "  " + param.strip() + value
                            else:
                                current_line += param + value

                    if current_line.strip():
                        lines.append(current_line)

                    return lines if len(lines) > 1 else [command]

        # 如果上述方法都失败，按空格进行简单分割
        words = command.split()
        lines = []
        current_line = words[0]

        for word in words[1:]:
            if len(current_line + " " + word) <= 120:
                current_line += " " + word
            else:
                lines.append(current_line + " \\")
                current_line = "  " + word

        if current_line.strip():
            lines.append(current_line)

        return lines

    def _execute_commands_background(
        self, commands: List[str], subagents_list: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        在后台执行所有子代理命令

        Args:
            commands: 构建的命令列表
            subagents_list: 子代理列表

        Returns:
            后台进程信息列表
        """
        background_processes = []

        for i, (command, subagent) in enumerate(zip(commands, subagents_list)):
            agent_name = subagent["name"]
            task = subagent["task"]

            try:
                logger.info(f"启动后台子代理 {i+1}/{len(commands)}: {agent_name}")

                # 使用 execute_command_background 启动后台进程
                process_info = execute_command_background(command=command, verbose=True)

                # 添加子代理相关信息
                background_process = {
                    "agent_name": agent_name,
                    "task": task,
                    "pid": process_info["pid"],
                    "process_uniq_id": process_info.get("process_uniq_id"),
                    "command": process_info["command"],
                    "working_directory": process_info["working_directory"],
                    "start_time": process_info["start_time"],
                    "status": process_info["status"],
                }

                # Register with BackgroundProcessNotifier
                try:
                    conversation_id = (
                        self.agent.conversation_config.conversation_id
                        if self.agent
                        else None
                    )
                    if conversation_id:
                        notifier = get_background_process_notifier()
                        notifier.register_process(
                            conversation_id=conversation_id,
                            pid=process_info["pid"],
                            tool_name="RunNamedSubagentsTool",
                            command=process_info["command"],
                            cwd=process_info.get("working_directory"),
                            agent_name=agent_name,
                            task=task,
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to register subagent background process to notifier: {e}"
                    )

                background_processes.append(background_process)
                logger.info(
                    f"成功启动后台子代理 '{agent_name}' (PID: {process_info['pid']}, ID: {process_info.get('process_uniq_id')})"
                )

            except Exception as e:
                logger.error(f"启动后台子代理 '{agent_name}' 失败: {str(e)}")
                # 添加失败的进程信息
                background_process = {
                    "agent_name": agent_name,
                    "task": task,
                    "pid": None,
                    "command": command,
                    "working_directory": None,
                    "start_time": None,
                    "status": "failed",
                    "error": str(e),
                }
                background_processes.append(background_process)

        return background_processes

    def _cleanup_temp_files(self) -> None:
        """
        清理创建的临时文件
        """
        for temp_file_path in self.temp_files:
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.debug(f"已清理临时文件: {temp_file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file_path}: {str(e)}")

        # 清空临时文件列表
        self.temp_files.clear()
