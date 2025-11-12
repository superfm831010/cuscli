import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
from pydantic import BaseModel
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import CountTokensTool, ToolResult
from autocoder.common.tokens import count_string_tokens as count_tokens
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


@dataclass
class TokenCountInfo:
    """Token统计信息"""
    filename: str
    tokens: int
    file_size: int
    relative_path: str

class CountTokensToolResolver(BaseToolResolver):
    """Token统计工具解析器"""
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: CountTokensTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: CountTokensTool = tool  # For type hinting
        
    def _is_text_file(self, file_path: str) -> bool:
        """判断是否是文本文件"""
        # 跳过隐藏文件和常见的二进制文件
        filename = os.path.basename(file_path)
        if filename.startswith('.'):
            return False
            
        # 跳过常见的二进制文件扩展名
        binary_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin', '.jpg', '.jpeg', 
            '.png', '.gif', '.bmp', '.ico', '.zip', '.tar', '.gz', '.rar',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac'
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext not in binary_extensions
    
    def _should_include_file(self, file_path: str) -> bool:
        """判断是否应该包含此文件"""
        if not self._is_text_file(file_path):
            return False
            
        return True
    
    def _count_tokens_single_file(self, file_path: str, source_dir: str) -> Optional[TokenCountInfo]:
        """统计单个文件的Token数量"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            tokens = count_tokens(content)
            file_size = len(content)
            relative_path = os.path.relpath(file_path, source_dir)
            
            return TokenCountInfo(
                filename=file_path,
                tokens=tokens,
                file_size=file_size,
                relative_path=relative_path
            )
            
        except Exception as e:
            logger.warning(f"Error processing file '{file_path}': {str(e)}")
            return None
    
    def _count_tokens_directory(self, dir_path: str, source_dir: str) -> Tuple[List[TokenCountInfo], Dict[str, Any]]:
        """统计目录下所有文件的Token数量"""
        token_infos = []
        stats = {
            'total_files': 0,
            'total_tokens': 0,
            'total_size': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'by_extension': defaultdict(lambda: {"files": 0, "tokens": 0, "size": 0})
        }
        
        if self.tool.recursive:
            # 递归遍历目录
            for root, dirs, files in os.walk(dir_path):
                # 跳过常见的忽略目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    '__pycache__', 'node_modules', 'dist', 'build', 'target', 
                    '.git', '.svn', '.hg', '.vscode', '.idea'
                ]]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    stats['total_files'] += 1
                    
                    if not self._should_include_file(file_path):
                        stats['skipped_files'] += 1
                        continue
                        
                    token_info = self._count_tokens_single_file(file_path, source_dir)
                    if token_info:
                        token_infos.append(token_info)
                        stats['processed_files'] += 1
                        stats['total_tokens'] += token_info.tokens
                        stats['total_size'] += token_info.file_size
                        
                        # 按扩展名分类统计
                        ext = os.path.splitext(file_path)[1].lower() or "no_extension"
                        stats['by_extension'][ext]["files"] += 1
                        stats['by_extension'][ext]["tokens"] += token_info.tokens
                        stats['by_extension'][ext]["size"] += token_info.file_size
                    else:
                        stats['skipped_files'] += 1
        else:
            # 非递归，只处理当前目录的文件
            if os.path.isdir(dir_path):
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path):
                        stats['total_files'] += 1
                        
                        if not self._should_include_file(file_path):
                            stats['skipped_files'] += 1
                            continue
                            
                        token_info = self._count_tokens_single_file(file_path, source_dir)
                        if token_info:
                            token_infos.append(token_info)
                            stats['processed_files'] += 1
                            stats['total_tokens'] += token_info.tokens
                            stats['total_size'] += token_info.file_size
                            
                            # 按扩展名分类统计
                            ext = os.path.splitext(file_path)[1].lower() or "no_extension"
                            stats['by_extension'][ext]["files"] += 1
                            stats['by_extension'][ext]["tokens"] += token_info.tokens
                            stats['by_extension'][ext]["size"] += token_info.file_size
                        else:
                            stats['skipped_files'] += 1
        
        return token_infos, stats
    
    def _format_summary_report(self, token_infos: List[TokenCountInfo], stats: Dict[str, Any], target_path: str) -> str:
        """生成汇总报告"""
        report_lines = []
        
        # 基本统计信息
        report_lines.append(f"Token统计报告 - {target_path}")
        report_lines.append("=" * 60)
        report_lines.append(f"总文件数: {stats['total_files']:,}")
        report_lines.append(f"处理文件数: {stats['processed_files']:,}")
        report_lines.append(f"跳过文件数: {stats['skipped_files']:,}")
        report_lines.append(f"总Token数: {stats['total_tokens']:,}")
        report_lines.append(f"总文件大小: {stats['total_size']/1024/1024:.2f} MB")
        
        if stats['processed_files'] > 0:
            avg_tokens = stats['total_tokens'] / stats['processed_files']
            report_lines.append(f"平均Token数/文件: {avg_tokens:.2f}")
        
        report_lines.append("")
        
        # 按文件扩展名分类的统计
        if self.tool.include_summary and stats['by_extension']:
            report_lines.append("按文件类型统计:")
            report_lines.append(f"{'扩展名':<12} {'文件数':<8} {'Token数':<12} {'占比%':<8} {'大小(KB)':<12}")
            report_lines.append("-" * 60)
            
            total_tokens = stats['total_tokens']
            for ext, data in sorted(stats['by_extension'].items(), key=lambda x: x[1]["tokens"], reverse=True):
                percent = (data["tokens"] / total_tokens * 100) if total_tokens > 0 else 0
                size_kb = data["size"] / 1024
                report_lines.append(f"{ext:<12} {data['files']:<8} {data['tokens']:<12,} {percent:<8.1f} {size_kb:<12.1f}")
        
        report_lines.append("")
        
        # Top 10 文件列表
        if token_infos:
            report_lines.append("Token数最多的文件 (Top 10):")
            report_lines.append(f"{'Token数':<10} {'大小(KB)':<12} {'文件路径'}")
            report_lines.append("-" * 60)
            
            sorted_infos = sorted(token_infos, key=lambda x: x.tokens, reverse=True)
            for info in sorted_infos[:10]:
                size_kb = info.file_size / 1024
                report_lines.append(f"{info.tokens:<10,} {size_kb:<12.1f} {info.relative_path}")
        
        return "\n".join(report_lines)
    
    def resolve(self) -> ToolResult:
        """解析Token统计工具"""
        path = self.tool.path
        source_dir = self.args.source_dir or "."
        
        # 计算绝对路径
        if os.path.isabs(path):
            abs_path = path
        else:
            abs_path = os.path.abspath(os.path.join(source_dir, path))
        
        # 检查路径是否存在
        if not os.path.exists(abs_path):
            return ToolResult(
                success=False,
                message=f"路径不存在: {path}"
            )
        
        try:
            if os.path.isfile(abs_path):
                # 处理单个文件
                if not self._should_include_file(abs_path):
                    return ToolResult(
                        success=False,
                        message=f"文件类型不支持统计: {path}"
                    )
                
                token_info = self._count_tokens_single_file(abs_path, source_dir)
                if not token_info:
                    return ToolResult(
                        success=False,
                        message=f"无法读取文件: {path}"
                    )
                
                # 格式化单文件结果
                message = f"文件Token统计完成: {path}"
                content = {
                    "type": "single_file",
                    "path": path,
                    "tokens": token_info.tokens,
                    "file_size": token_info.file_size,
                    "details": {
                        "relative_path": token_info.relative_path,
                        "size_mb": token_info.file_size / 1024 / 1024,
                        "avg_bytes_per_token": token_info.file_size / token_info.tokens if token_info.tokens > 0 else 0
                    }
                }
                
                return ToolResult(
                    success=True,
                    message=message,
                    content=content
                )
                
            elif os.path.isdir(abs_path):
                # 处理目录
                token_infos, stats = self._count_tokens_directory(abs_path, source_dir)
                
                # 生成汇总报告
                summary_report = self._format_summary_report(token_infos, stats, path)
                
                message = f"目录Token统计完成: {path}"
                content = {
                    "type": "directory",
                    "path": path,
                    "summary": stats,
                    "files": [
                        {
                            "relative_path": info.relative_path,
                            "tokens": info.tokens,
                            "file_size": info.file_size
                        }
                        for info in token_infos
                    ],
                    "report": summary_report
                }
                
                return ToolResult(
                    success=True,
                    message=message,
                    content=content
                )
            
            else:
                return ToolResult(
                    success=False,
                    message=f"路径既不是文件也不是目录: {path}"
                )
                
        except Exception as e:
            logger.error(f"Token统计过程中发生错误: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Token统计失败: {str(e)}"
            ) 