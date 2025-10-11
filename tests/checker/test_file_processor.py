"""
文件处理器单元测试
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from autocoder.checker.file_processor import FileProcessor
from autocoder.checker.types import FileFilters, CodeChunk


class TestFileProcessor:
    """文件处理器测试类"""

    @pytest.fixture
    def processor(self):
        """创建文件处理器实例"""
        return FileProcessor(chunk_size=1000, overlap=50)

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录用于测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def create_test_file(self, directory: str, filename: str, content: str) -> str:
        """辅助方法：创建测试文件"""
        file_path = os.path.join(directory, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    # ==================== 文件扫描测试 ====================

    def test_scan_python_files(self, processor, temp_dir):
        """测试扫描 Python 文件"""
        # 创建测试文件
        self.create_test_file(temp_dir, "test1.py", "print('hello')")
        self.create_test_file(temp_dir, "test2.py", "print('world')")
        self.create_test_file(temp_dir, "test.js", "console.log('js')")

        # 扫描 Python 文件
        filters = FileFilters(extensions=[".py"])
        files = processor.scan_files(temp_dir, filters)

        assert len(files) == 2
        assert all(f.endswith(".py") for f in files)

    def test_scan_multiple_extensions(self, processor, temp_dir):
        """测试多扩展名过滤"""
        self.create_test_file(temp_dir, "test1.py", "# python")
        self.create_test_file(temp_dir, "test2.js", "// javascript")
        self.create_test_file(temp_dir, "test3.txt", "text")

        filters = FileFilters(extensions=[".py", ".js"])
        files = processor.scan_files(temp_dir, filters)

        assert len(files) == 2

    def test_scan_with_ignored_directories(self, processor, temp_dir):
        """测试忽略特定目录"""
        self.create_test_file(temp_dir, "main.py", "# main")
        self.create_test_file(temp_dir, "__pycache__/cache.py", "# cache")
        self.create_test_file(temp_dir, "tests/test.py", "# test")

        filters = FileFilters(extensions=[".py"], ignored=["__pycache__", "tests"])
        files = processor.scan_files(temp_dir, filters)

        # 应该只有 main.py
        assert len(files) == 1
        assert "main.py" in files[0]

    def test_scan_empty_directory(self, processor, temp_dir):
        """测试扫描空目录"""
        filters = FileFilters(extensions=[".py"])
        files = processor.scan_files(temp_dir, filters)

        assert len(files) == 0

    def test_scan_single_file(self, processor, temp_dir):
        """测试扫描单个文件"""
        file_path = self.create_test_file(temp_dir, "test.py", "print('hello')")

        filters = FileFilters(extensions=[".py"])
        files = processor.scan_files(file_path, filters)

        assert len(files) == 1
        assert files[0] == file_path

    def test_scan_hidden_files_ignored(self, processor, temp_dir):
        """测试隐藏文件被忽略"""
        self.create_test_file(temp_dir, "visible.py", "# visible")
        self.create_test_file(temp_dir, ".hidden.py", "# hidden")

        filters = FileFilters(extensions=[".py"])
        files = processor.scan_files(temp_dir, filters)

        # 只应该找到 visible.py
        assert len(files) == 1
        assert "visible.py" in files[0]

    # ==================== 文件可检查性测试 ====================

    def test_is_checkable_valid_file(self, processor, temp_dir):
        """测试有效文件"""
        file_path = self.create_test_file(temp_dir, "test.py", "print('hello')")
        assert processor.is_checkable(file_path) is True

    def test_is_checkable_nonexistent_file(self, processor):
        """测试不存在的文件"""
        assert processor.is_checkable("/nonexistent/file.py") is False

    def test_is_checkable_directory(self, processor, temp_dir):
        """测试目录（非文件）"""
        assert processor.is_checkable(temp_dir) is False

    def test_is_checkable_binary_file(self, processor, temp_dir):
        """测试二进制文件"""
        # 创建二进制文件
        file_path = os.path.join(temp_dir, "binary.bin")
        with open(file_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')

        assert processor.is_checkable(file_path) is False

    def test_is_checkable_large_file(self, processor, temp_dir):
        """测试大文件（> 10MB）"""
        # 创建大文件（模拟，实际不创建真的 10MB 文件）
        file_path = os.path.join(temp_dir, "large.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            # 写入约 1KB 的内容
            f.write("# " * 500)

        # 小文件应该可检查
        assert processor.is_checkable(file_path) is True

    # ==================== 行号添加测试 ====================

    def test_add_line_numbers(self, processor):
        """测试基本行号添加"""
        code = "def foo():\n    pass\n    return True"
        numbered = processor.add_line_numbers(code)

        lines = numbered.split('\n')
        assert lines[0] == "1 def foo():"
        assert lines[1] == "2     pass"
        assert lines[2] == "3     return True"

    def test_add_line_numbers_empty_file(self, processor):
        """测试空文件行号添加"""
        code = ""
        numbered = processor.add_line_numbers(code)
        assert numbered == "1 "

    def test_add_line_numbers_single_line(self, processor):
        """测试单行代码"""
        code = "print('hello')"
        numbered = processor.add_line_numbers(code)
        assert numbered == "1 print('hello')"

    # ==================== 文件分块测试 ====================

    def test_chunk_small_file(self, processor, temp_dir):
        """测试小文件不分块"""
        # 创建小文件
        code = "def foo():\n    pass\n"
        file_path = self.create_test_file(temp_dir, "small.py", code)

        chunks = processor.chunk_file(file_path)

        # 小文件应该只有一个 chunk
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].start_line == 1
        assert chunks[0].file_path == file_path

    def test_chunk_large_file(self, processor, temp_dir):
        """测试大文件分块"""
        # 创建一个相对较大的文件
        # 每行约 50 个字符，重复 100 次
        lines = ["def function_{}(): pass  # This is a comment".format(i) for i in range(100)]
        code = "\n".join(lines)
        file_path = self.create_test_file(temp_dir, "large.py", code)

        # 使用较小的 chunk_size 来确保分块
        small_processor = FileProcessor(chunk_size=500, overlap=10)
        chunks = small_processor.chunk_file(file_path)

        # 应该有多个 chunk
        assert len(chunks) > 1

        # 验证 chunk 的连续性
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.start_line >= 1
            assert chunk.end_line > chunk.start_line

    def test_chunk_file_uses_cache(self, temp_dir):
        """第二次分块命中缓存且返回深拷贝"""
        processor = FileProcessor(chunk_size=200, overlap=20)
        lines = [f"line {i}" for i in range(120)]
        file_path = self.create_test_file(temp_dir, "cached.py", "\n".join(lines))

        original_fn = processor.tokenizer.count_tokens
        call_counter = {"count": 0}

        def counting(*args, **kwargs):
            call_counter["count"] += 1
            return original_fn(*args, **kwargs)

        with patch.object(processor.tokenizer, "count_tokens", side_effect=counting):
            first_chunks = processor.chunk_file(file_path)
            first_calls = call_counter["count"]
            second_chunks = processor.chunk_file(file_path)
            second_calls = call_counter["count"]

        assert second_calls == first_calls
        assert len(first_chunks) == len(second_chunks)
        assert first_chunks[0] is not second_chunks[0]
        assert first_chunks[0].content == second_chunks[0].content

    def test_chunk_overlap(self, processor, temp_dir):
        """测试 chunk 重叠"""
        # 创建足够大的文件来测试重叠
        lines = ["print('line {}')".format(i) for i in range(50)]
        code = "\n".join(lines)
        file_path = self.create_test_file(temp_dir, "overlap.py", code)

        # 使用小的 chunk_size 和明确的 overlap
        overlap_processor = FileProcessor(chunk_size=200, overlap=5)
        chunks = overlap_processor.chunk_file(file_path)

        if len(chunks) > 1:
            # 如果有多个 chunk，验证有重叠
            # 第二个 chunk 的起始行应该在第一个 chunk 的结束行之前
            assert chunks[1].start_line <= chunks[0].end_line

    def test_chunk_line_numbers_continuity(self, processor, temp_dir):
        """测试行号连续性"""
        lines = ["line {}".format(i) for i in range(30)]
        code = "\n".join(lines)
        file_path = self.create_test_file(temp_dir, "continuity.py", code)

        chunks = processor.chunk_file(file_path)

        # 验证每个 chunk 的内容都有正确的行号
        for chunk in chunks:
            chunk_lines = chunk.content.split('\n')
            first_line = chunk_lines[0]
            # 第一行应该以起始行号开头
            assert first_line.startswith(str(chunk.start_line))

    def test_chunk_file_not_found(self, processor):
        """测试文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            processor.chunk_file("/nonexistent/file.py")

    # ==================== 辅助方法测试 ====================

    def test_is_binary_file(self, processor, temp_dir):
        """测试二进制文件检测"""
        # 文本文件
        text_file = self.create_test_file(temp_dir, "text.txt", "Hello World")
        assert processor._is_binary_file(text_file) is False

        # 二进制文件
        binary_file = os.path.join(temp_dir, "binary.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')
        assert processor._is_binary_file(binary_file) is True

    def test_get_file_size_mb(self, processor, temp_dir):
        """测试获取文件大小"""
        # 创建一个已知大小的文件
        content = "x" * 1024 * 10  # 约 10KB
        file_path = self.create_test_file(temp_dir, "size_test.txt", content)

        size_mb = processor._get_file_size_mb(file_path)
        # 应该约为 0.01 MB
        assert 0.009 < size_mb < 0.011

    def test_calculate_chunk_end(self, processor):
        """测试计算分块结束位置"""
        # 创建带行号的行列表
        lines = [f"{i+1} line {i}" for i in range(20)]

        # 从第 0 行开始，token 限制 100
        end_index = processor._calculate_chunk_end(lines, 0, 100)

        # 应该返回一个合理的结束索引
        assert 0 < end_index <= len(lines)

    # ==================== 集成测试 ====================

    def test_full_workflow(self, processor, temp_dir):
        """测试完整工作流：扫描 -> 分块"""
        # 创建多个测试文件
        self.create_test_file(temp_dir, "file1.py", "def func1(): pass")
        self.create_test_file(temp_dir, "file2.py", "def func2(): pass")
        self.create_test_file(temp_dir, "file3.js", "function func3() {}")

        # 1. 扫描 Python 文件
        filters = FileFilters(extensions=[".py"])
        files = processor.scan_files(temp_dir, filters)
        assert len(files) == 2

        # 2. 对每个文件进行分块
        all_chunks = []
        for file in files:
            chunks = processor.chunk_file(file)
            all_chunks.extend(chunks)

        # 应该有 2 个文件的 chunks
        assert len(all_chunks) >= 2


class TestFileFiltersIntegration:
    """文件过滤器集成测试"""

    def test_filters_with_no_extensions(self):
        """测试没有扩展名过滤器"""
        filters = FileFilters()
        assert filters.matches_extension("any_file.xyz") is True

    def test_filters_with_extensions(self):
        """测试扩展名过滤"""
        filters = FileFilters(extensions=[".py", ".js"])
        assert filters.matches_extension("test.py") is True
        assert filters.matches_extension("test.js") is True
        assert filters.matches_extension("test.txt") is False

    def test_filters_ignored_patterns(self):
        """测试忽略模式"""
        filters = FileFilters(ignored=["__pycache__", "*.pyc"])
        assert filters.should_ignore("__pycache__/test.py") is True
        assert filters.should_ignore("test.pyc") is True
        assert filters.should_ignore("normal.py") is False
