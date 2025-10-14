"""
TempFileManager 单元测试

测试临时文件管理器的各项功能，包括：
- 基本文件创建和清理
- 多文件管理
- 嵌套路径处理
- 路径映射（原始路径 <-> 临时路径）
- Context manager 自动清理
- 跨平台兼容性（Windows/Linux）
"""

import pytest
import os
import tempfile
from pathlib import Path
from autocoder.checker.git_helper import TempFileManager


class TestTempFileManager:
    """TempFileManager 单元测试"""

    def test_init_creates_temp_dir(self):
        """测试初始化时创建临时目录"""
        manager = TempFileManager()

        assert manager.temp_dir is not None
        assert os.path.exists(manager.temp_dir)
        assert os.path.isdir(manager.temp_dir)
        assert "codechecker_git_" in manager.temp_dir

        # 清理
        manager.cleanup()

    def test_create_temp_file_basic(self):
        """测试基本的临时文件创建"""
        manager = TempFileManager()

        try:
            content = "print('hello world')\n"
            temp_path = manager.create_temp_file("test.py", content)

            # 验证文件存在
            assert os.path.exists(temp_path)

            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                assert f.read() == content

            # 验证路径映射
            assert manager.get_temp_path("test.py") == temp_path
            assert manager.get_original_path(temp_path) == "test.py"

        finally:
            manager.cleanup()

    def test_create_temp_file_with_nested_path(self):
        """测试嵌套路径的临时文件创建"""
        manager = TempFileManager()

        try:
            content = "# nested file\n"
            temp_path = manager.create_temp_file("src/utils/helper.py", content)

            # 验证文件存在
            assert os.path.exists(temp_path)

            # 验证保留了目录结构
            assert "src" in temp_path
            assert "utils" in temp_path
            assert temp_path.endswith("helper.py")

            # 验证父目录存在
            assert os.path.isdir(os.path.dirname(temp_path))

            # 验证路径映射
            assert manager.get_original_path(temp_path) == "src/utils/helper.py"

        finally:
            manager.cleanup()

    def test_multiple_files(self):
        """测试管理多个临时文件"""
        manager = TempFileManager()

        try:
            files = [
                ("file1.py", "# file 1\n"),
                ("file2.py", "# file 2\n"),
                ("src/file3.py", "# file 3\n"),
            ]

            temp_paths = []
            for file_path, content in files:
                temp_path = manager.create_temp_file(file_path, content)
                temp_paths.append(temp_path)
                assert os.path.exists(temp_path)

            # 验证文件数量
            assert len(manager) == 3

            # 验证所有文件都存在
            for temp_path in temp_paths:
                assert os.path.exists(temp_path)

            # 验证路径映射正确
            assert manager.get_original_path(temp_paths[0]) == "file1.py"
            assert manager.get_original_path(temp_paths[1]) == "file2.py"
            assert manager.get_original_path(temp_paths[2]) == "src/file3.py"

        finally:
            manager.cleanup()

    def test_context_manager(self):
        """测试 context manager 自动清理"""
        temp_dir = None
        temp_file = None

        with TempFileManager() as manager:
            temp_dir = manager.temp_dir
            temp_file = manager.create_temp_file("test.py", "# test\n")

            # 在 context 内，文件应该存在
            assert os.path.exists(temp_dir)
            assert os.path.exists(temp_file)

        # 退出 context 后，临时目录应该被清理
        assert not os.path.exists(temp_dir)
        assert not os.path.exists(temp_file)

    def test_cleanup_removes_all_files(self):
        """测试 cleanup 删除所有文件"""
        manager = TempFileManager()

        # 创建多个文件
        temp_path1 = manager.create_temp_file("file1.py", "# 1\n")
        temp_path2 = manager.create_temp_file("dir/file2.py", "# 2\n")
        temp_dir = manager.temp_dir

        # 确认文件存在
        assert os.path.exists(temp_path1)
        assert os.path.exists(temp_path2)
        assert os.path.exists(temp_dir)

        # 清理
        manager.cleanup()

        # 确认文件被删除
        assert not os.path.exists(temp_dir)
        assert not os.path.exists(temp_path1)
        assert not os.path.exists(temp_path2)

    def test_get_temp_path_nonexistent(self):
        """测试获取不存在文件的临时路径"""
        manager = TempFileManager()

        try:
            # 不存在的文件应该返回 None
            assert manager.get_temp_path("nonexistent.py") is None
        finally:
            manager.cleanup()

    def test_get_original_path_nonexistent(self):
        """测试反查不存在的原始路径"""
        manager = TempFileManager()

        try:
            # 不存在的临时路径应该返回 None
            assert manager.get_original_path("/nonexistent/path.py") is None
        finally:
            manager.cleanup()

    def test_special_characters_in_path(self):
        """测试路径中的特殊字符处理"""
        manager = TempFileManager()

        try:
            # 包含空格的路径
            temp_path = manager.create_temp_file("my file.py", "# test\n")
            assert os.path.exists(temp_path)

            # 包含中文的路径
            temp_path2 = manager.create_temp_file("测试文件.py", "# 测试\n")
            assert os.path.exists(temp_path2)

        finally:
            manager.cleanup()

    def test_path_sanitization(self):
        """测试路径清理（移除危险字符）"""
        manager = TempFileManager()

        try:
            # 包含 ".." 的路径应该被替换
            temp_path = manager.create_temp_file("../evil.py", "# test\n")

            # 路径中不应包含 ".."
            assert ".." not in temp_path
            assert "_" in temp_path  # 应该被替换为 "_"

        finally:
            manager.cleanup()

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only")
    def test_windows_path_compatibility(self):
        """测试 Windows 路径兼容性"""
        manager = TempFileManager()

        try:
            # Windows 风格路径（反斜杠）
            content = "# windows test\n"
            temp_path = manager.create_temp_file("src\\utils\\helper.py", content)

            # 应该能正常创建
            assert os.path.exists(temp_path)

            # 路径应该使用正斜杠（内部标准化）
            assert os.path.exists(temp_path)

        finally:
            manager.cleanup()

    @pytest.mark.skipif(os.name == 'nt', reason="Linux only")
    def test_linux_path_compatibility(self):
        """测试 Linux 路径兼容性"""
        manager = TempFileManager()

        try:
            # Linux 风格路径
            content = "# linux test\n"
            temp_path = manager.create_temp_file("src/utils/helper.py", content)

            # 应该能正常创建
            assert os.path.exists(temp_path)
            assert "src" in temp_path
            assert "utils" in temp_path

        finally:
            manager.cleanup()

    def test_large_number_of_files(self):
        """测试大量文件管理"""
        manager = TempFileManager()

        try:
            # 创建 100 个文件
            for i in range(100):
                temp_path = manager.create_temp_file(f"file_{i}.py", f"# file {i}\n")
                assert os.path.exists(temp_path)

            # 验证文件数量
            assert len(manager) == 100

        finally:
            manager.cleanup()

    def test_unicode_content(self):
        """测试 Unicode 内容"""
        manager = TempFileManager()

        try:
            # 包含中文、emoji 等
            content = "# 这是中文注释 🚀\nprint('你好世界')\n"
            temp_path = manager.create_temp_file("unicode.py", content)

            # 验证文件存在和内容
            assert os.path.exists(temp_path)
            with open(temp_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
                assert read_content == content
                assert "你好世界" in read_content
                assert "🚀" in read_content

        finally:
            manager.cleanup()

    def test_empty_file(self):
        """测试空文件"""
        manager = TempFileManager()

        try:
            temp_path = manager.create_temp_file("empty.py", "")

            assert os.path.exists(temp_path)
            with open(temp_path, 'r', encoding='utf-8') as f:
                assert f.read() == ""

        finally:
            manager.cleanup()

    def test_cleanup_idempotent(self):
        """测试多次 cleanup 是安全的"""
        manager = TempFileManager()
        manager.create_temp_file("test.py", "# test\n")

        # 第一次清理
        manager.cleanup()

        # 第二次清理不应该报错
        manager.cleanup()

    def test_len_method(self):
        """测试 __len__ 方法"""
        manager = TempFileManager()

        try:
            assert len(manager) == 0

            manager.create_temp_file("file1.py", "# 1\n")
            assert len(manager) == 1

            manager.create_temp_file("file2.py", "# 2\n")
            assert len(manager) == 2

        finally:
            manager.cleanup()
