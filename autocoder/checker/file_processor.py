"""
代码检查模块的文件处理器

负责文件扫描、过滤、分块等功能。
"""

import os
from pathlib import Path
from typing import List, Optional
from loguru import logger

from autocoder.checker.types import CodeChunk, FileFilters
from autocoder.common.buildin_tokenizer import BuildinTokenizer


class FileProcessor:
    """
    文件处理器

    负责：
    1. 扫描目录并过滤文件
    2. 判断文件是否可检查
    3. 为大文件进行分块处理
    4. 为代码添加行号

    Attributes:
        chunk_size: 单个 chunk 的最大 token 数
        overlap: chunk 之间的重叠行数
        tokenizer: 用于计算 token 数的分词器
    """

    def __init__(self, chunk_size: int = 4000, overlap: int = 200):
        """
        初始化文件处理器

        Args:
            chunk_size: 单个 chunk 的最大 token 数，默认 4000
            overlap: chunk 之间的重叠行数，默认 200
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = BuildinTokenizer()

        logger.info(
            f"FileProcessor initialized: chunk_size={chunk_size}, overlap={overlap}"
        )

    def scan_files(
        self,
        path: str,
        filters: Optional[FileFilters] = None
    ) -> List[str]:
        """
        扫描目录，返回符合条件的文件列表

        Args:
            path: 要扫描的目录路径或文件路径
            filters: 文件过滤条件（扩展名、忽略模式等）

        Returns:
            符合条件的文件路径列表（绝对路径）

        Examples:
            >>> processor = FileProcessor()
            >>> filters = FileFilters(extensions=[".py"], ignored=["__pycache__"])
            >>> files = processor.scan_files("autocoder", filters)
            >>> len(files) > 0
            True
        """
        path_obj = Path(path)
        result_files = []

        # 如果是单个文件
        if path_obj.is_file():
            if self.is_checkable(str(path_obj)):
                # 应用过滤条件
                if filters:
                    if filters.matches_extension(str(path_obj)) and not filters.should_ignore(str(path_obj)):
                        result_files.append(str(path_obj.absolute()))
                else:
                    result_files.append(str(path_obj.absolute()))
            return result_files

        # 如果是目录
        if not path_obj.is_dir():
            logger.warning(f"Path does not exist: {path}")
            return []

        logger.info(f"Scanning directory: {path}")

        # 遍历目录
        for file_path in path_obj.rglob("*"):
            # 只处理文件，跳过目录
            if not file_path.is_file():
                continue

            # 转换为字符串路径
            file_str = str(file_path)
            relative_path = str(file_path.relative_to(path_obj))

            # 应用忽略模式
            if filters and filters.should_ignore(relative_path):
                logger.debug(f"Ignored by filter: {relative_path}")
                continue

            # 跳过隐藏文件和目录
            if any(part.startswith('.') for part in file_path.parts):
                logger.debug(f"Ignored hidden file: {relative_path}")
                continue

            # 应用扩展名过滤
            if filters and not filters.matches_extension(file_str):
                continue

            # 检查文件是否可检查
            if not self.is_checkable(file_str):
                logger.debug(f"Not checkable: {relative_path}")
                continue

            result_files.append(str(file_path.absolute()))

        logger.info(f"Found {len(result_files)} checkable files in {path}")
        return result_files

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """
        将文件分块，确保每块不超过 token 限制

        对于小文件，直接返回单个 chunk。
        对于大文件，分成多个 chunk，chunk 之间有重叠以避免边界问题。

        Args:
            file_path: 文件路径

        Returns:
            代码块列表，每个块包含代码内容、行号范围等信息

        Raises:
            FileNotFoundError: 文件不存在
            UnicodeDecodeError: 文件编码错误

        Examples:
            >>> processor = FileProcessor(chunk_size=1000, overlap=100)
            >>> chunks = processor.chunk_file("small_file.py")
            >>> len(chunks) == 1
            True
        """
        # 读取文件内容
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

        # 分割成行
        lines = content.split('\n')
        total_lines = len(lines)

        # 为每行添加行号
        numbered_lines = [f"{i+1} {line}" for i, line in enumerate(lines)]

        # 计算总 token 数
        total_content = '\n'.join(numbered_lines)
        total_tokens = self.tokenizer.count_tokens(total_content)

        # 如果文件小于 chunk_size，直接返回单个 chunk
        if total_tokens <= self.chunk_size:
            logger.debug(
                f"File {file_path} fits in single chunk: "
                f"{total_lines} lines, {total_tokens} tokens"
            )
            return [
                CodeChunk(
                    content=total_content,
                    start_line=1,
                    end_line=total_lines,
                    chunk_index=0,
                    file_path=file_path
                )
            ]

        # 文件需要分块
        logger.info(
            f"Chunking file {file_path}: "
            f"{total_lines} lines, {total_tokens} tokens"
        )

        chunks = []
        current_line = 0
        chunk_index = 0

        while current_line < len(numbered_lines):
            # 计算当前 chunk 的结束行
            end_line = self._calculate_chunk_end(
                numbered_lines,
                current_line,
                self.chunk_size
            )

            # 创建 chunk
            chunk_content = '\n'.join(numbered_lines[current_line:end_line])
            chunks.append(
                CodeChunk(
                    content=chunk_content,
                    start_line=current_line + 1,  # 转换为 1-based 行号
                    end_line=end_line,
                    chunk_index=chunk_index,
                    file_path=file_path
                )
            )

            logger.debug(
                f"Created chunk {chunk_index}: "
                f"lines {current_line + 1}-{end_line}, "
                f"tokens {self.tokenizer.count_tokens(chunk_content)}"
            )

            # 移动到下一个 chunk（考虑重叠）
            if end_line >= len(numbered_lines):
                break

            # 计算重叠的起始位置
            overlap_start = max(0, end_line - self.overlap)
            current_line = overlap_start
            chunk_index += 1

        logger.info(
            f"File {file_path} split into {len(chunks)} chunks"
        )

        return chunks

    def is_checkable(self, file_path: str) -> bool:
        """
        判断文件是否可检查

        检查条件：
        1. 文件存在且可读
        2. 文件是文本文件（非二进制）
        3. 文件大小在合理范围内（< 10MB）
        4. 文件编码为 UTF-8

        Args:
            file_path: 文件路径

        Returns:
            True 表示可检查，False 表示不可检查

        Examples:
            >>> processor = FileProcessor()
            >>> processor.is_checkable("autocoder/checker/types.py")
            True
            >>> processor.is_checkable("nonexistent.py")
            False
        """
        # 1. 检查文件是否存在
        if not os.path.exists(file_path):
            return False

        # 2. 检查是否为文件（非目录）
        if not os.path.isfile(file_path):
            return False

        # 3. 检查文件大小（< 10MB）
        file_size_mb = self._get_file_size_mb(file_path)
        if file_size_mb > 10:
            logger.debug(f"File too large: {file_path} ({file_size_mb:.2f}MB)")
            return False

        # 4. 检查是否为二进制文件
        if self._is_binary_file(file_path):
            logger.debug(f"Binary file: {file_path}")
            return False

        # 5. 检查文件是否可读且为 UTF-8 编码
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 尝试读取前 100 行来验证编码
                for _ in range(100):
                    line = f.readline()
                    if not line:
                        break
            return True
        except (UnicodeDecodeError, PermissionError) as e:
            logger.debug(f"Cannot read file as UTF-8: {file_path}, error: {e}")
            return False
        except Exception as e:
            logger.debug(f"Error checking file: {file_path}, error: {e}")
            return False

    def add_line_numbers(self, content: str) -> str:
        """
        为代码添加行号

        格式：{行号} {代码内容}
        行号从 1 开始，使用空格分隔。

        Args:
            content: 原始代码内容

        Returns:
            添加行号后的代码内容

        Examples:
            >>> processor = FileProcessor()
            >>> code = "def foo():\\n    pass"
            >>> numbered = processor.add_line_numbers(code)
            >>> numbered.startswith("1 def foo():")
            True
        """
        lines = content.split('\n')
        numbered_lines = [f"{i+1} {line}" for i, line in enumerate(lines)]
        return '\n'.join(numbered_lines)

    def _calculate_chunk_end(
        self,
        lines: List[str],
        start_index: int,
        token_limit: int
    ) -> int:
        """
        计算 chunk 的结束行索引

        从 start_index 开始，逐行累加 token 数，
        直到超过 token_limit 或到达文件末尾。

        Args:
            lines: 所有行的列表（已添加行号）
            start_index: 起始行索引
            token_limit: token 数量限制

        Returns:
            结束行索引（不包含该行）

        Note:
            这是内部方法，用于 chunk_file() 方法
        """
        current_tokens = 0
        end_index = start_index

        for i in range(start_index, len(lines)):
            line = lines[i]
            line_tokens = self.tokenizer.count_tokens(line)

            # 如果加上这一行会超过限制，则在此处结束
            if current_tokens + line_tokens > token_limit and i > start_index:
                break

            current_tokens += line_tokens
            end_index = i + 1

        return end_index

    def _is_binary_file(self, file_path: str) -> bool:
        """
        判断文件是否为二进制文件

        通过读取文件前 1024 字节，检查是否包含非文本字符。

        Args:
            file_path: 文件路径

        Returns:
            True 表示二进制文件，False 表示文本文件
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if not chunk:
                    return False

                # 检查是否包含 NULL 字节
                if b'\x00' in chunk:
                    return True

                # 检查文本字符的比例
                # 文本字符包括：制表符(9)、换行(10)、回车(13)、
                # 可打印 ASCII (32-126)、以及高位字节(128-255, UTF-8)
                text_characters = 0
                for byte in chunk:
                    if byte in (9, 10, 13) or (32 <= byte <= 126) or byte >= 128:
                        text_characters += 1

                text_ratio = text_characters / len(chunk)
                # 如果文本字符比例低于 85%，认为是二进制文件
                return text_ratio < 0.85
        except Exception:
            return True

    def _get_file_size_mb(self, file_path: str) -> float:
        """
        获取文件大小（MB）

        Args:
            file_path: 文件路径

        Returns:
            文件大小（MB）
        """
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
