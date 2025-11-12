import os
import tempfile
import requests
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import ExtractToTextTool, ToolResult
from autocoder.common import AutoCoderArgs
from loguru import logger
import typing

# 导入文档解析相关模块
from autocoder.rag.loaders import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_ppt
)

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ExtractToTextToolResolver(BaseToolResolver):
    """文本提取工具解析器，将各种格式文件转换为文本文件"""
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: ExtractToTextTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: ExtractToTextTool = tool  # 类型提示

    def _is_url(self, path: str) -> bool:
        """检查路径是否为URL"""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _download_from_url(self, url: str) -> str:
        """从URL下载文件到临时路径"""
        try:
            logger.info(f"Downloading file from URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 从URL或Content-Disposition头获取文件名
            filename = None
            if 'content-disposition' in response.headers:
                content_disposition = response.headers['content-disposition']
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
            
            if not filename:
                # 从URL路径提取文件名
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    # 根据Content-Type猜测扩展名
                    content_type = response.headers.get('content-type', '')
                    if 'pdf' in content_type:
                        filename = 'downloaded_file.pdf'
                    elif 'word' in content_type or 'officedocument' in content_type:
                        filename = 'downloaded_file.docx'
                    elif 'powerpoint' in content_type or 'presentation' in content_type:
                        filename = 'downloaded_file.pptx'
                    else:
                        filename = 'downloaded_file.txt'
            
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, filename)
            
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(response.content)
            
            logger.info(f"Downloaded file to: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            raise Exception(f"Failed to download file from URL '{url}': {str(e)}")

    def _extract_text_content(self, file_path: str) -> str:
        """提取文件的文本内容，支持多种格式"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                logger.info(f"Extracting text from PDF: {file_path}")
                return extract_text_from_pdf(file_path)
            elif ext == '.docx':
                logger.info(f"Extracting text from DOCX: {file_path}")
                return extract_text_from_docx(file_path)
            elif ext in ('.pptx', '.ppt'):
                logger.info(f"Extracting text from PPT/PPTX: {file_path}")
                slide_texts = []
                for slide_identifier, slide_text_content in extract_text_from_ppt(file_path):
                    slide_texts.append(f"--- Slide {slide_identifier} ---\n{slide_text_content}")
                return "\n\n".join(slide_texts) if slide_texts else ""
            else:
                # 处理普通文本文件
                logger.info(f"Reading plain text file: {file_path}")
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
                    
        except Exception as e:
            raise Exception(f"Failed to extract text from file '{file_path}': {str(e)}")

    def _write_text_to_file(self, content: str, target_path: str) -> None:
        """将文本内容写入目标文件"""
        try:
            # 确保目标目录存在
            target_dir = os.path.dirname(target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            
            # 写入文件
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully wrote text content to: {target_path}")
            
        except Exception as e:
            raise Exception(f"Failed to write text to file '{target_path}': {str(e)}")

    def _cleanup_temp_file(self, temp_path: str) -> None:
        """清理临时文件"""
        try:
            if os.path.exists(temp_path):
                # 如果是临时目录中的文件，删除整个临时目录
                temp_dir = os.path.dirname(temp_path)
                if temp_dir.startswith(tempfile.gettempdir()):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                else:
                    os.remove(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file '{temp_path}': {str(e)}")

    def resolve(self) -> ToolResult:
        """
        执行文本提取工具
        
        Returns:
            ToolResult: 工具执行结果
        """
        source_path = self.tool.source_path
        target_path = self.tool.target_path
        temp_file_path = None
        
        try:
            # 第一步：获取源文件路径
            if self._is_url(source_path):
                # 从URL下载文件
                temp_file_path = self._download_from_url(source_path)
                actual_source_path = temp_file_path
                logger.info(f"Processing URL: {source_path} -> {temp_file_path}")
            else:
                # 本地文件路径
                if not os.path.exists(source_path):
                    return ToolResult(
                        success=False,
                        message=f"Error: Source file not found at path: {source_path}"
                    )
                if not os.path.isfile(source_path):
                    return ToolResult(
                        success=False,
                        message=f"Error: Source path is not a file: {source_path}"
                    )
                actual_source_path = source_path
                logger.info(f"Processing local file: {source_path}")

            # 第二步：提取文本内容
            text_content = self._extract_text_content(actual_source_path)
            
            if not text_content.strip():
                return ToolResult(
                    success=False,
                    message=f"Warning: No text content extracted from file: {source_path}"
                )

            # 第三步：写入目标文件
            self._write_text_to_file(text_content, target_path)

            # 记录文件变更（如果需要）
            if self.agent:
                self.agent.record_file_change(
                    file_path=target_path,
                    change_type="added",
                    content=text_content
                )

            # 统计信息
            line_count = len(text_content.split('\n'))
            char_count = len(text_content)
            
            success_message = f"Successfully extracted text from '{source_path}' to '{target_path}'"
            if self._is_url(source_path):
                success_message += f" (downloaded from URL)"
            success_message += f" - {line_count} lines, {char_count} characters"

            return ToolResult(
                success=True,
                message=success_message,
                content={
                    "source_path": source_path,
                    "target_path": target_path,
                    "line_count": line_count,
                    "char_count": char_count,
                    "is_url": self._is_url(source_path)
                }
            )

        except Exception as e:
            logger.error(f"ExtractToTextTool execution failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"文本提取失败: {str(e)}"
            )
        
        finally:
            # 清理临时文件
            if temp_file_path:
                self._cleanup_temp_file(temp_file_path)
