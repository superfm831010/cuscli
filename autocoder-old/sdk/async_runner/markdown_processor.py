

"""
Markdown 处理器模块

提供智能 Markdown 解析和分割功能，支持多种分割模式。
"""

import re
import yaml
import hashlib
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from autocoder.common.international import get_message, get_message_with_format


class SplitMode(Enum):
    """分割模式枚举"""
    DELIMITER = "delimiter"          # 按分隔符分割（兼容模式）
    HEADING1 = "h1"                 # 按 H1 标题分割
    HEADING2 = "h2"                 # 按 H2 标题分割
    HEADING3 = "h3"                 # 按 H3 标题分割
    ANY_HEADING = "any"             # 按任何标题分割
    FRONT_MATTER = "frontmatter"    # 按 YAML front matter 分割
    CUSTOM_PATTERN = "custom"       # 按自定义正则模式分割


@dataclass
class SplitterConfig:
    """分割器配置"""
    pattern: str = ""                                    # 自定义正则模式
    min_length: int = 50                                # 最小文档长度
    max_length: int = 10000                             # 最大文档长度
    overlap_size: int = 100                             # 重叠大小（用于长文档分割）
    preserve_context: bool = True                       # 是否保留上下文
    custom_splitter: Optional[Callable[[str], List[str]]] = None  # 自定义分割函数


@dataclass
class DocumentPart:
    """文档部分"""
    content: str
    title: str
    level: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Markdown 文档"""
    original_file: str
    index: int
    content: str
    temp_filename: str
    title: str
    heading_level: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarkdownProcessor:
    """Markdown 处理器，用于解析和分割 Markdown 内容"""
    
    def __init__(self):
        """初始化处理器"""
        self.split_mode = SplitMode.HEADING1
        self.delimiter = "==="
        self.min_heading_level = 1
        self.max_heading_level = 6
        self.config = SplitterConfig()
    
    def process_content(self, content: str, filename: str = "stdin") -> List[Document]:
        """
        处理 Markdown 内容，返回分割后的文档列表
        
        Args:
            content: Markdown 内容
            filename: 文件名
            
        Returns:
            分割后的文档列表
        """
        parts = []
        
        # 首先检测文档是否包含多个独立文档
        if self._contains_multiple_documents(content):
            print(get_message("detected_multi_document_structure"))
            try:
                parts = self._parse_multiple_documents(content)
            except Exception as e:
                print(get_message_with_format("multi_document_parse_failed_fallback", error=str(e)))
                parts = []
        
        # 如果没有检测到多文档或解析失败，使用原有分割逻辑
        if not parts:
            if self.split_mode != SplitMode.DELIMITER:
                try:
                    parts = self._split_by_headings(content)
                    if len(parts) <= 1:
                        # 如果没有找到标题，回退到分隔符模式
                        parts = self._split_by_delimiter(content)
                except Exception:
                    # 如果解析失败，回退到分隔符模式
                    parts = self._split_by_delimiter(content)
            else:
                # 使用分隔符模式
                parts = self._split_by_delimiter(content)
        
        # 使用自定义分割器（如果配置了）
        if self.config.custom_splitter:
            print(get_message("using_custom_splitter"))
            custom_parts = self.config.custom_splitter(content)
            parts = self._convert_to_document_parts(custom_parts)
        
        # 如果没有找到任何分割，将整个内容作为一个文档
        if not parts:
            parts = [DocumentPart(
                content=content.strip(),
                title=self._extract_title(content),
                level=1
            )]
        
        # 应用长度和重叠配置
        parts = self._apply_length_constraints(parts)
        
        # 转换为 Document 对象
        documents = []
        base_name = self._get_base_name(filename)
        
        for i, part in enumerate(parts):
            doc = Document(
                original_file=filename,
                index=i,
                content=part.content,
                title=part.title,
                heading_level=part.level,
                temp_filename=self._generate_temp_filename(base_name, i, len(parts), part.content),
                metadata=part.metadata
            )
            documents.append(doc)
        
        return documents
    
    def _contains_multiple_documents(self, content: str) -> bool:
        """检测内容是否包含多个独立文档"""
        # 检测 YAML front matter 分隔符
        front_matter_pattern = re.compile(r'^---\s*$', re.MULTILINE)
        matches = front_matter_pattern.findall(content)
        if len(matches) >= 3:  # 至少有3个分隔符才认为是多文档
            return True
        
        # 检测连续的空行分隔（可能是多文档）
        empty_line_pattern = re.compile(r'\n\s*\n\s*\n')
        if len(empty_line_pattern.findall(content)) >= 2:
            # 进一步检查是否有标题结构
            heading_pattern = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)
            headings = heading_pattern.findall(content)
            return len(headings) >= 2
        
        return False
    
    def _parse_multiple_documents(self, content: str) -> List[DocumentPart]:
        """解析多文档结构"""
        parts = []
        
        # 尝试按 YAML front matter 分割
        if "---" in content:
            yaml_parts = self._split_by_front_matter(content)
            if len(yaml_parts) > 1:
                parts = yaml_parts
        
        # 如果没有找到 YAML 分割，抛出异常
        if not parts:
            raise ValueError(get_message("cannot_parse_multi_document_structure"))
        
        return parts
    
    def _split_by_front_matter(self, content: str) -> List[DocumentPart]:
        """按 YAML front matter 分割"""
        doc_parts = []
        lines = content.split('\n')
        current_doc = []
        current_yaml = []
        in_yaml = False
        in_content = False
        
        for line in lines:
            trimmed = line.strip()
            
            if trimmed == "---":
                if not in_yaml and not in_content:
                    # 开始新的 YAML block
                    in_yaml = True
                    continue
                elif in_yaml and not in_content:
                    # YAML block 结束，内容开始
                    in_yaml = False
                    in_content = True
                    continue
                elif in_content:
                    # 当前文档结束，保存并开始新文档
                    if current_doc or current_yaml:
                        self._add_front_matter_doc(doc_parts, '\n'.join(current_yaml), '\n'.join(current_doc))
                    
                    # 重置状态
                    current_doc = []
                    current_yaml = []
                    in_yaml = True
                    in_content = False
                    continue
            
            if in_yaml:
                current_yaml.append(line)
            elif in_content:
                current_doc.append(line)
            else:
                # 没有 YAML header 的情况，直接当作内容处理
                current_doc.append(line)
                in_content = True
        
        # 添加最后一个文档
        if current_doc or current_yaml:
            self._add_front_matter_doc(doc_parts, '\n'.join(current_yaml), '\n'.join(current_doc))
        
        # 如果没有找到任何文档，返回整个内容作为一个文档
        if not doc_parts:
            doc_parts = [DocumentPart(
                content=content.strip(),
                title=self._extract_title(content),
                level=1,
                metadata={}
            )]
        
        return doc_parts
    
    def _add_front_matter_doc(self, doc_parts: List[DocumentPart], yaml_content: str, markdown_content: str):
        """添加一个 front matter 文档"""
        metadata = self._parse_yaml_metadata(yaml_content)
        content = markdown_content.strip()
        
        title = self._extract_title(content)
        if 'title' in metadata and metadata['title']:
            title = str(metadata['title'])
        
        if content or metadata:
            doc_parts.append(DocumentPart(
                content=content,
                title=title,
                level=1,
                metadata=metadata
            ))
    
    def _parse_yaml_metadata(self, yaml_content: str) -> Dict[str, Any]:
        """解析 YAML 元数据"""
        if not yaml_content.strip():
            return {}
        
        try:
            return yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError:
            # 简单解析失败时的备用方案
            metadata = {}
            lines = yaml_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().strip('"\'')
                        metadata[key] = value
            
            return metadata
    
    def _convert_to_document_parts(self, parts: List[str]) -> List[DocumentPart]:
        """将字符串数组转换为 DocumentPart"""
        doc_parts = []
        for part in parts:
            if part.strip():
                doc_parts.append(DocumentPart(
                    content=part.strip(),
                    title=self._extract_title(part),
                    level=1
                ))
        return doc_parts
    
    def _apply_length_constraints(self, parts: List[DocumentPart]) -> List[DocumentPart]:
        """应用长度约束和重叠配置"""
        result = []
        too_short_parts = []
        
        for part in parts:
            # 如果文档太短，先保存起来
            if len(part.content) < self.config.min_length:
                too_short_parts.append(part)
                continue
            
            # 如果文档太长，分割
            if len(part.content) > self.config.max_length:
                sub_parts = self._split_long_document(part)
                result.extend(sub_parts)
            else:
                result.append(part)
        
        # 如果所有文档都被过滤掉了（因为太短），至少保留一个最长的
        if not result and too_short_parts:
            longest = max(too_short_parts, key=lambda x: len(x.content))
            result.append(longest)
        
        return result
    
    def _split_long_document(self, part: DocumentPart) -> List[DocumentPart]:
        """分割过长的文档"""
        parts = []
        content = part.content
        max_len = self.config.max_length
        overlap = self.config.overlap_size
        
        # 安全检查：防止无限循环
        max_iterations = 100
        iterations = 0
        
        while len(content) > max_len and iterations < max_iterations:
            iterations += 1
            
            # 找到合适的分割点
            split_pos = self._find_best_split_position(content, max_len)
            
            # 安全检查
            if split_pos <= 0:
                split_pos = max_len // 2
            if split_pos >= len(content):
                break
            
            # 创建当前部分
            current_part = DocumentPart(
                content=content[:split_pos],
                title=f"{part.title} (第{len(parts)+1}部分)",
                level=part.level,
                metadata=part.metadata.copy()
            )
            parts.append(current_part)
            
            # 计算下一部分的起始位置（考虑重叠）
            next_start = max(0, split_pos - overlap)
            if next_start >= split_pos:
                next_start = split_pos
            
            if next_start >= len(content):
                break
            
            content = content[next_start:]
            
            if len(content) <= overlap:
                break
        
        # 添加最后一部分
        if len(content) > self.config.min_length:
            parts.append(DocumentPart(
                content=content,
                title=f"{part.title} (第{len(parts)+1}部分)",
                level=part.level,
                metadata=part.metadata.copy()
            ))
        
        # 如果没有成功分割，返回原文档
        if not parts:
            return [part]
        
        return parts
    
    def _find_best_split_position(self, content: str, max_pos: int) -> int:
        """找到最佳分割位置"""
        if max_pos >= len(content):
            return len(content)
        
        # 优先在句号后分割
        for i in range(max_pos - 1, max(0, max_pos - 100), -1):
            if i < len(content) and content[i] == '.' and i + 1 < len(content) and content[i + 1] == ' ':
                return i + 1
        
        # 其次在换行符处分割
        for i in range(max_pos - 1, max(0, max_pos - 100), -1):
            if i < len(content) and content[i] == '\n':
                return i + 1
        
        # 最后在空格处分割
        for i in range(max_pos - 1, max(0, max_pos - 50), -1):
            if i < len(content) and content[i] == ' ':
                return i + 1
        
        return max_pos
    
    def _split_by_headings(self, content: str) -> List[DocumentPart]:
        """按标题分割 Markdown 内容"""
        lines = content.split('\n')
        parts = []
        current_part = DocumentPart(content="", title="", level=1)
        current_lines = []
        
        for line in lines:
            # 检查是否是标题行
            if line.strip().startswith('#'):
                level = self._get_heading_level(line)
                title = self._extract_title_from_line(line)
                
                # 如果这是我们要分割的标题级别
                if self._should_split_at_level(level):
                    # 保存之前的部分
                    if current_lines:
                        current_part.content = '\n'.join(current_lines)
                        if not current_part.title:
                            current_part.title = self._extract_title(current_part.content)
                            current_part.level = 1
                        parts.append(current_part)
                    
                    # 开始新的部分
                    current_part = DocumentPart(
                        content="",
                        title=title,
                        level=level
                    )
                    current_lines = [line]
                else:
                    # 不是分割级别的标题，添加到当前部分
                    current_lines.append(line)
            else:
                # 普通行，添加到当前部分
                current_lines.append(line)
        
        # 添加最后一个部分
        if current_lines:
            current_part.content = '\n'.join(current_lines)
            if not current_part.title:
                current_part.title = self._extract_title(current_part.content)
                current_part.level = 1
            parts.append(current_part)
        
        # 如果没有找到任何部分，使用整个内容
        if not parts:
            parts = [DocumentPart(
                content=content,
                title=self._extract_title(content),
                level=1
            )]
        
        return parts
    
    def _get_heading_level(self, line: str) -> int:
        """获取标题级别"""
        trimmed = line.strip()
        level = 0
        for char in trimmed:
            if char == '#':
                level += 1
            else:
                break
        return level
    
    def _extract_title_from_line(self, line: str) -> str:
        """从标题行提取标题文本"""
        title = re.sub(r'^#+\s*', '', line.strip())
        title = title.strip()
        return title if title else "Untitled"
    
    def _should_split_at_level(self, level: int) -> bool:
        """判断是否应该在指定级别分割"""
        if self.split_mode == SplitMode.HEADING1:
            return level == 1
        elif self.split_mode == SplitMode.HEADING2:
            return level <= 2
        elif self.split_mode == SplitMode.HEADING3:
            return level <= 3
        elif self.split_mode == SplitMode.ANY_HEADING:
            return self.min_heading_level <= level <= self.max_heading_level
        else:
            return False
    
    def _split_by_delimiter(self, content: str) -> List[DocumentPart]:
        """按分隔符分割内容（向后兼容）"""
        parts = content.split(self.delimiter)
        result = []
        
        for part in parts:
            trimmed = part.strip()
            if trimmed:
                result.append(DocumentPart(
                    content=trimmed,
                    title=self._extract_title(trimmed),
                    level=1
                ))
        
        return result
    
    def _extract_title(self, content: str) -> str:
        """从内容中提取标题"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                # 移除 # 符号和前后空格
                title = re.sub(r'^#+\s*', '', line)
                title = title.strip()
                if title:
                    return title
        
        # 如果没有找到标题，使用前50个字符
        if len(content) > 50:
            return content[:50] + "..."
        return content
    
    def _get_base_name(self, filename: str) -> str:
        """获取文件的基本名称（不包含扩展名）"""
        if not filename or filename == "stdin":
            return "stdin"
        
        return Path(filename).stem
    
    def _generate_temp_filename(self, base_name: str, index: int, total: int, content: str) -> str:
        """生成临时文件名，基于内容MD5哈希"""
        # 生成内容的MD5哈希（取前8位）
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        
        if total == 1:
            return f"{base_name}_{content_hash}.md"
        
        return f"{base_name}_{index+1:02d}_{content_hash}.md"
    
    def _sanitize_filename(self, title: str) -> str:
        """清理文件名，移除不安全字符"""
        # 移除或替换不安全的文件名字符
        safe = re.sub(r'[<>:"/\\|?*\s]+', '_', title)
        
        # 移除多余的下划线
        safe = re.sub(r'_+', '_', safe)
        
        # 移除开头和结尾的下划线
        safe = safe.strip('_')
        
        # 限制长度
        if len(safe) > 50:
            safe = safe[:50]
        
        return safe.lower()
    
    def validate_content(self, content: str) -> None:
        """验证 Markdown 内容"""
        if not content.strip():
            raise ValueError(get_message("content_empty"))
    
    def get_document_info(self, doc: Document) -> str:
        """获取文档信息摘要"""
        content_preview = doc.content
        if len(content_preview) > 100:
            content_preview = content_preview[:100] + "..."
        
        title = doc.title if doc.title else "无标题"
        
        return (f"标题: {title} (H{doc.heading_level}), 文件: {doc.original_file}, "
                f"部分: {doc.index+1}, 临时文件: {doc.temp_filename}, 内容预览: {content_preview}")
    
    def set_split_mode(self, mode: SplitMode):
        """设置分割模式"""
        self.split_mode = mode
    
    def set_delimiter(self, delimiter: str):
        """设置自定义分隔符（用于兼容模式）"""
        if delimiter:
            self.delimiter = delimiter
        self.split_mode = SplitMode.DELIMITER
    
    def set_heading_level_range(self, min_level: int, max_level: int):
        """设置标题级别范围"""
        if 1 <= min_level <= 6 and min_level <= max_level <= 6:
            self.min_heading_level = min_level
            self.max_heading_level = max_level
    
    def set_custom_splitter(self, splitter: Callable[[str], List[str]]):
        """设置自定义分割器"""
        self.config.custom_splitter = splitter
    
    def set_length_constraints(self, min_length: int, max_length: int):
        """设置长度约束"""
        self.config.min_length = min_length
        self.config.max_length = max_length
    
    def set_overlap_size(self, size: int):
        """设置重叠大小"""
        self.config.overlap_size = size

