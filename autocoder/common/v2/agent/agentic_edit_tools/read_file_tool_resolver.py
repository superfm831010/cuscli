import os
from typing import Dict, Any, Optional, List, Tuple
from autocoder.common import AutoCoderArgs,SourceCode
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import ReadFileTool, ToolResult
from autocoder.common.pruner.context_pruner import PruneContext
from autocoder.common import SourceCode
from autocoder.common.tokens import count_string_tokens as count_tokens
from loguru import logger
import typing
import json
from autocoder.rag.loaders import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_ppt
)
from autocoder.common.llms.manager import LLMManager
from autocoder.common.wrap_llm_hint.utils import add_hint_to_text

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ReadFileToolResolver(BaseToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: ReadFileTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: ReadFileTool = tool  # For type hinting
        
        # Initialize AutoCoderArgs parser for flexible parameter parsing
        self.args_parser = AutoCoderArgsParser()
        
        # 解析 context_prune_safe_zone_tokens 参数
        parsed_safe_zone_tokens = self._get_parsed_safe_zone_tokens()
        
        self.context_pruner = PruneContext(
            max_tokens=parsed_safe_zone_tokens,
            args=self.args,
            llm=self.agent.context_prune_llm
        ) if self.agent and self.agent.context_prune_llm else None

        # LLM manager for model context window queries
        self.llm_manager = LLMManager()

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

    def _extract_lines_by_range(self, content: str, start_line: Optional[int], end_line: Optional[int]) -> str:
        """根据行号范围提取文件内容
        
        参数说明:
        - start_line: 起始行号。正数表示从第N行开始(1-based)，负数表示从倒数第N行开始
        - end_line: 结束行号。正数表示到第N行结束(1-based)，-1表示到文件末尾
        """
        if start_line is None and end_line is None:
            return content
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 处理行号参数（转换为0-based索引）
        start_idx = 0
        end_idx = total_lines
        
        if start_line is not None:
            if start_line < 0:
                # 负数表示从倒数第N行开始
                start_idx = max(0, total_lines + start_line)
            else:
                # 正数表示从第N行开始(1-based)
                start_idx = max(0, start_line - 1)
        
        if end_line is not None:
            if end_line == -1:
                # -1 表示到文件末尾
                end_idx = total_lines
            elif end_line < -1:
                # 其他负数表示到倒数第N行结束
                end_idx = max(0, total_lines + end_line + 1)
            else:
                # 正数表示到第N行结束(1-based)
                end_idx = min(total_lines, end_line)
        
        # 验证行号范围
        if start_line is not None and start_line > 0 and start_idx >= total_lines:
            return f"Error: start_line {start_line} exceeds total lines {total_lines}"
        
        if start_line is not None and start_line < 0 and abs(start_line) > total_lines:
            return f"Error: start_line {start_line} (倒数第{abs(start_line)}行) exceeds total lines {total_lines}"
        
        if start_idx >= end_idx and not (end_line == -1 and start_idx == total_lines):
            if start_line is not None and start_line < 0:
                start_desc = f"倒数第{abs(start_line)}行"
            else:
                start_desc = f"第{start_line}行"
            
            if end_line == -1:
                end_desc = "文件末尾"
            elif end_line is not None and end_line < -1:
                end_desc = f"倒数第{abs(end_line)}行"
            else:
                end_desc = f"第{end_line}行"
            
            return f"Error: start_line ({start_desc}) should be before end_line ({end_desc})"
        
        # 提取指定行范围
        extracted_lines = lines[start_idx:end_idx]
        return '\n'.join(extracted_lines)

    def _extract_content_by_query(self, content: str, query: str, file_path: str) -> str:
        """根据查询描述提取最相关的内容"""
        if not query or not self.context_pruner:
            return content
        
        # 使用 context_pruner 的查询功能提取相关内容
        try:
            # 创建一个包含查询的伪对话
            query_conversation = {
                "role": "user",
                "content": query
            }
            
            source_code = SourceCode(
                module_name=file_path,
                source_code=content,
                tokens=count_tokens(content)
            )
            
            # 使用 context_pruner 根据查询提取相关内容
            pruned_sources = self.context_pruner.handle_overflow(
                file_sources=[source_code],
                conversations=[query_conversation],
                strategy=self.args.context_prune_strategy
            )
            
            if pruned_sources:
                return pruned_sources[0].source_code
            else:
                return content
                
        except Exception as e:
            logger.warning(f"Error extracting content by query '{query}': {str(e)}")
            return content

    def _prune_file_content(self, content: str, file_path: str) -> str:
        """对文件内容进行剪枝处理"""
        if not self.context_pruner:
            return content

        # 计算 token 数量
        tokens = count_tokens(content)
        parsed_safe_zone_tokens = self._get_parsed_safe_zone_tokens()
        if tokens <= parsed_safe_zone_tokens:
            return content

        # 创建 SourceCode 对象
        source_code = SourceCode(
            module_name=file_path,
            source_code=content,
            tokens=tokens
        )

        # 使用 context_pruner 进行剪枝
        pruned_sources = self.context_pruner.handle_overflow(
            file_sources=[source_code],
            conversations=self.agent.current_conversations if self.agent else [],
            strategy=self.args.context_prune_strategy
        )

        if not pruned_sources:
            return content

        return pruned_sources[0].source_code

    def _get_model_context_window(self) -> int:
        """获取当前代码模型的上下文窗口大小，默认 128000"""
        try:
            model_name = self.args.code_model or self.args.model
            model = self.llm_manager.get_model(model_name)
            if model and model.context_window:
                return int(model.context_window)
        except Exception as e:
            logger.warning(f"Failed to get model context window: {e}")
        return 128000

    def _get_pruned_conversations(self) -> List[Dict[str, Any]]:
        """获取已按 agent 逻辑剪枝后的对话，用于计算 token 开销"""
        try:
            if not self.agent:
                return []
            conversations = self.agent.current_conversations or []
            # 复用 Agentic 对话修剪器，保持与主循环一致
            agentic_pruner = self.agent.agentic_pruner
            if agentic_pruner and conversations:
                from copy import deepcopy
                return agentic_pruner.prune_conversations(deepcopy(conversations))
            return conversations
        except Exception as e:
            logger.warning(f"Failed to get pruned conversations: {e}")
            return []

    def _prune_file_to_fit_context_window(self, content: str, file_path: str) -> Tuple[bool, str]:
        """
        如果 对话token + 文件token 可能超出模型上下文窗口，不在此处裁剪文件，
        而是返回带有提示信息的结果，提示大模型应先对会话进行删减后再读取文件。
        """
        if not self.agent:
            return False, content

        try:
            model_window = self._get_model_context_window()
            pruned_convs = self._get_pruned_conversations()
            conv_tokens = count_tokens(json.dumps(pruned_convs, ensure_ascii=False))
            file_tokens = count_tokens(content)

            if conv_tokens + file_tokens <= model_window:
                return False, content

            # 构造提示信息，指导大模型优先裁剪会话（如使用 conversation_message_ids_write），然后再调用 read_file
            hint = (
                "The combined size of current conversation and requested file likely exceeds the model context window. "
                "Please prune the conversation first (e.g., delete unnecessary tool_result messages using conversation_message_ids_write), "
                "then call read_file again. "
                f"Details: conversation_tokens={conv_tokens}, file_tokens={file_tokens}, window={model_window}, file={file_path}"
            )

            logger.info(
                f"Conversation + file tokens exceed window ({conv_tokens}+{file_tokens}>{model_window}). Returning hint instead of file content.")

            # 返回包含提示的包装文本，前置文件前500字符作为上下文
            prefix = content[:500] if content else ""
            return True, add_hint_to_text(prefix, hint)
        except Exception as e:
            logger.warning(f"Failed to calculate context window overflow: {e}")
            return False, content

    def _read_file_content(self, file_path_to_read: str) -> str:
        content = ""
        ext = os.path.splitext(file_path_to_read)[1].lower()

        if ext == '.pdf':
            logger.info(f"Extracting text from PDF: {file_path_to_read}")
            content = extract_text_from_pdf(file_path_to_read)
        elif ext == '.docx':
            logger.info(f"Extracting text from DOCX: {file_path_to_read}")
            content = extract_text_from_docx(file_path_to_read)
        elif ext in ('.pptx', '.ppt'):
            logger.info(f"Extracting text from PPT/PPTX: {file_path_to_read}")
            slide_texts = []
            for slide_identifier, slide_text_content in extract_text_from_ppt(file_path_to_read):
                slide_texts.append(f"--- Slide {slide_identifier} ---\n{slide_text_content}")
            content = "\n\n".join(slide_texts) if slide_texts else ""
        else:
            logger.info(f"Reading plain text file: {file_path_to_read}")
            with open(file_path_to_read, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

        # 处理新参数
        # 1. 先根据行号范围提取内容
        if self.tool.start_line is not None or self.tool.end_line is not None:
            content = self._extract_lines_by_range(content, self.tool.start_line, self.tool.end_line)
            
        # 2. 如果有查询，根据查询提取相关内容
        if self.tool.query:
            content = self._extract_content_by_query(content, self.tool.query, file_path_to_read)
        
        # 3. 检查当前对话 + 文件是否超出模型窗口，若需要提示会话剪枝则直接返回带提示内容
        should_prune, maybe_hinted_content = self._prune_file_to_fit_context_window(content, file_path_to_read)
        if should_prune:
            return maybe_hinted_content

        # 4. 最后进行常规的剪枝处理（基于 safe_zone_tokens 的兜底）
        return self._prune_file_content(maybe_hinted_content, file_path_to_read)

    def read_file_normal(self, file_path: str) -> ToolResult:
        """Read file directly without using shadow manager"""
        try:
            if not os.path.exists(file_path):
                return ToolResult(success=False, message=f"Error: File not found at path: {file_path}")
            if not os.path.isfile(file_path):
                return ToolResult(success=False, message=f"Error: Path is not a file: {file_path}")

            content = self._read_file_content(file_path)
            
            # 构建详细的成功消息
            message_parts = [f"{file_path}"]
            if self.tool.start_line is not None or self.tool.end_line is not None:
                # 构建起始行描述
                if self.tool.start_line is not None:
                    if self.tool.start_line < 0:
                        start = f"-{abs(self.tool.start_line)}"  # 负数行号显示为 -N
                    else:
                        start = str(self.tool.start_line)
                else:
                    start = "1"
                
                # 构建结束行描述
                if self.tool.end_line == -1:
                    end = "end"
                elif self.tool.end_line is not None:
                    if self.tool.end_line < -1:
                        end = str(self.tool.end_line)  # 其他负数行号直接显示
                    else:
                        end = str(self.tool.end_line)
                else:
                    end = "end"
                
                message_parts.append(f"lines {start}-{end}")
            if self.tool.query:
                message_parts.append(f"filtered by query: '{self.tool.query}'")
            
            message = " ".join(message_parts)
            
            logger.info(f"Successfully processed file: {message}")
            return ToolResult(success=True, message=message, content=content)

        except Exception as e:
            logger.warning(f"Error processing file '{file_path}': {str(e)}")
            logger.exception(e)
            return ToolResult(success=False, message=f"An error occurred while processing the file '{file_path}': {str(e)}")

    def resolve(self) -> ToolResult:
        """Resolve the read file tool by calling the appropriate implementation"""
        file_path = self.tool.path                        
        return self.read_file_normal(file_path)
