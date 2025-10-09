import os
import concurrent.futures
from typing import List, Dict, Optional, Union, Callable
from pathlib import Path
import time
import re
import importlib.resources as resources

from autocoder.rag.variable_holder import VariableHolder
from .models import TokenResult, DirectoryTokenResult
from .file_detector import FileTypeDetector
from .filters import FileFilter


class TokenCounter:
    """Token 计数器，用于统计文件和目录的 token 数量"""
    
    def __init__(self, 
                 timeout: int = 30, 
                 parallel: bool = True, 
                 max_workers: int = 4):
        """
        初始化 Token 计数器
        
        Args:
            timeout: 单文件处理超时时间（秒）
            parallel: 是否并行处理
            max_workers: 最大工作线程数
        """
        self.timeout = timeout
        self.parallel = parallel
        self.max_workers = max_workers
        
        # 确保 tokenizer 已经加载，如果没有则自动初始化
        self._ensure_tokenizer_initialized()
    
    def _ensure_tokenizer_initialized(self):
        """
        确保 tokenizer 已经初始化，如果没有则自动初始化
        """
        if VariableHolder.TOKENIZER_MODEL is None:
            self._initialize_tokenizer()
    
    def _initialize_tokenizer(self):
        """
        初始化 tokenizer，参考 auto_coder_runner.py 中的 load_tokenizer 实现
        """
        try:
            from tokenizers import Tokenizer
            tokenizer_path = str(resources.files("autocoder") / "data" / "tokenizer.json")
            VariableHolder.TOKENIZER_PATH = tokenizer_path
            VariableHolder.TOKENIZER_MODEL = Tokenizer.from_file(tokenizer_path)
        except (FileNotFoundError, ImportError) as e:
            raise RuntimeError(
                f"Failed to initialize tokenizer: {str(e)}. "
                f"Make sure tokenizer.json exists in the autocoder package data directory."
            )
    
    def count_file(self, file_path: str) -> TokenResult:
        """
        统计单个文件的 token 数量
        
        Args:
            file_path: 文件路径
            
        Returns:
            TokenResult: 统计结果
        """
        try:
            if not os.path.isfile(file_path):
                return TokenResult(
                    file_path=file_path,
                    token_count=0,
                    char_count=0,
                    line_count=0,
                    success=False,
                    error="File does not exist"
                )
            
            # 检查是否为文本文件
            if not FileTypeDetector.is_text_file(file_path):
                return TokenResult(
                    file_path=file_path,
                    token_count=0,
                    char_count=0,
                    line_count=0,
                    success=False,
                    error="Not a text file"
                )
            
            # 检测文件编码
            encoding = FileTypeDetector.detect_encoding(file_path)
            
            # 读取文件内容
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            
            # 统计行数
            line_count = content.count('\n') + (0 if content == "" or content.endswith('\n') else 1)
            
            # 统计字符数
            char_count = len(content)
            
            # 统计 token 数量
            tokens = VariableHolder.TOKENIZER_MODEL.encode(content)
            token_count = len(tokens)
            
            return TokenResult(
                file_path=file_path,
                token_count=token_count,
                char_count=char_count,
                line_count=line_count
            )
        except Exception as e:
            return TokenResult(
                file_path=file_path,
                token_count=0,
                char_count=0,
                line_count=0,
                success=False,
                error=str(e)
            )
    
    def count_files(self, file_paths: List[str]) -> List[TokenResult]:
        """
        批量统计多个文件的 token 数量
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            List[TokenResult]: 统计结果列表
        """
        if not self.parallel or len(file_paths) <= 1:
            return [self.count_file(file_path) for file_path in file_paths]
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.count_file, file_path): file_path 
                for file_path in file_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_file):
                results.append(future.result())
                
        return results
    
    def count_directory(self, 
                        dir_path: str, 
                        pattern: str = None,
                        exclude_pattern: str = None,
                        recursive: bool = True,
                        max_depth: int = None) -> DirectoryTokenResult:
        """
        统计目录中所有文件的 token 数量
        
        Args:
            dir_path: 目录路径
            pattern: 文件名匹配模式（正则表达式）
            exclude_pattern: 排除的文件名模式（正则表达式）
            recursive: 是否递归处理子目录
            max_depth: 最大递归深度
            
        Returns:
            DirectoryTokenResult: 目录统计结果
        """
        if not os.path.isdir(dir_path):
            return DirectoryTokenResult(
                directory_path=dir_path,
                total_tokens=0,
                file_count=0,
                skipped_count=0,
                files=[],
                errors=["Directory does not exist"]
            )
        
        # 创建文件过滤器
        patterns = [pattern] if pattern else []
        exclude_patterns = [exclude_pattern] if exclude_pattern else []
        file_filter = FileFilter(patterns=patterns, exclude_patterns=exclude_patterns)
        
        # 收集所有匹配的文件
        all_files = []
        skipped_count = 0
        
        for root, dirs, files in os.walk(dir_path):
            # 检查递归深度
            if max_depth is not None:
                current_depth = root[len(dir_path):].count(os.sep)
                if current_depth >= max_depth:
                    dirs.clear()  # 不再递归子目录
            
            for file in files:
                file_path = os.path.join(root, file)
                if file_filter.matches(file_path):
                    all_files.append(file_path)
                else:
                    skipped_count += 1
            
            if not recursive:
                break  # 不递归处理子目录
        
        # 统计所有文件
        file_results = self.count_files(all_files)
        
        # 计算总 token 数
        total_tokens = sum(result.token_count for result in file_results if result.success)
        
        # 收集错误
        errors = [
            f"{result.file_path}: {result.error}" 
            for result in file_results if not result.success
        ]
        
        return DirectoryTokenResult(
            directory_path=dir_path,
            total_tokens=total_tokens,
            file_count=len(file_results),
            skipped_count=skipped_count,
            files=file_results,
            errors=errors
        )
    
    def count_string_tokens(self, text: str) -> int:
        """
        统计字符串的 token 数量
        
        Args:
            text: 要统计的字符串内容
            
        Returns:
            int: token 数量
        """
        try:
            if not isinstance(text, str):
                raise ValueError("Input must be a string")
            
            # 使用 tokenizer 编码字符串并统计 token 数量
            tokens = VariableHolder.TOKENIZER_MODEL.encode(text)
            return len(tokens)
        except Exception as e:
            raise RuntimeError(f"Failed to count tokens: {str(e)}")
    
    def set_tokenizer(self, tokenizer_name: str) -> None:
        """
        更改 tokenizer（目前不支持，仅为接口预留）
        
        Args:
            tokenizer_name: tokenizer 名称
        """
        # 目前仅支持默认的 tokenizer
        pass
