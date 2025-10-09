"""
命令处理器模块

提供统一的命令处理器，支持单次运行和会话复用功能。
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from ..core import AutoCoderCore
from ..models import AutoCodeOptions
from ..models.responses import CLIResult  # 从正确的位置导入
from ..exceptions import AutoCoderSDKError
from .options import CLIOptions
from ..formatters import OutputFormatter, InputFormatter, format_stream_output  # 使用新的 formatters 模块
from autocoder.common.international import get_message
from autocoder.common.llm_friendly_package import get_package_manager


class CommandHandler:
    """命令处理器基类，提供通用功能。"""
    
    def __init__(self, options: CLIOptions, cwd: Optional[str] = None):
        """
        初始化命令处理器。
        
        Args:
            options: CLI选项
            cwd: 当前工作目录，如果为None则使用系统当前目录
        """
        self.options = options
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.output_formatter = OutputFormatter(verbose=options.verbose)
        self.input_formatter = InputFormatter()
        
    def _create_core_options(self) -> AutoCodeOptions:
        """
        创建核心选项。
        
        Returns:
            AutoCodeOptions实例
        """
        # 处理 system_prompt 和 system_prompt_path
        system_prompt = self.options.system_prompt
        if self.options.system_prompt_path:
            try:
                with open(self.options.system_prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read().strip()
            except Exception as e:
                raise ValueError(f"无法读取系统提示文件 {self.options.system_prompt_path}: {str(e)}")
        
        return AutoCodeOptions(
            max_turns=self.options.max_turns,
            system_prompt=system_prompt,
            cwd=str(self.cwd),
            allowed_tools=self.options.allowed_tools,
            permission_mode=self.options.permission_mode,
            output_format=self.options.output_format,
            stream=self.options.output_format.startswith("stream"),
            session_id=self.options.resume_session,
            continue_session=self.options.continue_session,
            model=self.options.model,
            verbose=self.options.verbose,
            include_rules=self.options.include_rules,
            pr=self.options.pr,
            is_sub_agent=self.options.is_sub_agent,
            loop=self.options.loop,
            loop_keep_conversation=self.options.loop_keep_conversation,
            loop_additional_prompt=self.options.loop_additional_prompt,
            include_libs=self.options.include_libs
        )
        
    def _get_prompt(self) -> str:
        """
        获取提示内容，如果未提供则从stdin读取。
        
        Returns:
            提示内容
            
        Raises:
            ValueError: 如果未提供提示且stdin为空
        """
        if self.options.prompt:
            return self.options.prompt
            
        # 从stdin读取
        if not sys.stdin.isatty():
            content = sys.stdin.read()
            if not content.strip():
                raise ValueError(get_message("prompt_not_provided_empty_stdin"))
                
            # 根据输入格式处理
            if self.options.input_format == "text":
                return self.input_formatter.format_text(content)
            elif self.options.input_format == "json":
                result = self.input_formatter.format_json(content)
                # 尝试提取提示内容
                if isinstance(result, dict):
                    if "prompt" in result:
                        return result["prompt"]
                    elif "message" in result:
                        message = result["message"]
                        if isinstance(message, dict) and "content" in message:
                            return message["content"]
                        elif isinstance(message, str):
                            return message
                return content  # 如果无法提取，则返回原始内容
            else:
                # 对于流式输入，暂时只支持直接传递
                return content
        else:
            raise ValueError(get_message("prompt_not_provided_no_stdin"))
    
    def _add_libraries(self) -> None:
        """自动添加指定的 LLM friendly packages"""
        try:
            manager = get_package_manager(str(self.cwd))
            
            for lib_name in self.options.include_libs:
                if lib_name.strip():  # 确保库名不为空
                    manager.add_library(lib_name.strip())
                            
        except Exception:
            # 不抛出异常，只是静默失败，因为这不应该阻止主要功能
            pass


class PrintModeHandler(CommandHandler):
    """统一的命令处理器，支持单次运行和会话复用。"""
    
    def handle(self) -> CLIResult:
        """
        处理命令，支持会话复用。
        
        Returns:
            命令执行结果
        """
        try:
            prompt = self._get_prompt()
            
            # 自动添加指定的 LLM friendly packages
            if self.options.include_libs:
                self._add_libraries()
                
            core_options = self._create_core_options()
            core = AutoCoderCore(core_options)

            # 根据会话参数构建完整的 prompt
            final_prompt = prompt
            
            # 根据输出格式选择不同的处理方式
            if self.options.output_format == "stream-json":
                # 流式JSON输出
                result = asyncio.run(self._handle_stream(core, final_prompt))
            else:
                # 同步查询
                if self.options.output_format == "json":
                    # JSON格式：使用事件流方式，禁用终端输出
                    events = core.query_sync(final_prompt, show_terminal=False)
                    json_data = {
                        "events": [event.to_dict() for event in events],
                        "summary": {
                            "total_events": len(events),
                            "start_events": len([e for e in events if e.event_type == "start"]),
                            "completion_events": len([e for e in events if e.event_type == "completion"]),
                            "error_events": len([e for e in events if e.event_type == "error"])
                        }
                    }
                    result = self.output_formatter.format_json(json_data)
                else:                    
                    events = core.query_sync(final_prompt, show_terminal=self.options.verbose)                                        
                    completion_content = ""
                    for event in events:
                        if event.event_type == "tool_call" and event.data["tool_name"] == "AttemptCompletionTool":
                            completion_content = event.data["args"]["result"]
                            break                        
                                                            
                    result = self.output_formatter.format_text(completion_content)
                    
            return CLIResult(success=True, output=result)
            
        except Exception as e:
            return CLIResult(success=False, output="", error=str(e))
        
            
    async def _handle_stream(self, core: AutoCoderCore, prompt: str) -> str:
        """
        处理流式输出，正常打印所有事件。
        
        Args:
            core: AutoCoderCore实例
            prompt: 提示内容
            
        Returns:
            空字符串
        """
        # 使用 query_stream 方法获取 StreamEvent 流，正常打印所有事件
        async for event in core.query_stream(prompt, show_terminal=True):
            # 所有事件都会通过 core.query_stream 的内部渲染机制正常打印
            # 这里不需要额外的打印逻辑
            pass
        
        # 返回空字符串
        return ""


