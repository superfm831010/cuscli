"""
Tools Manager Unit Tests

工具管理器的单元测试套件。
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from autocoder.common.tools_manager import ToolsManager, ToolCommand, ToolsLoadResult
from autocoder.common.tools_manager.utils import (
    is_tool_command_file,
    extract_tool_help,
    get_project_name,
    _extract_help_from_file_comments
)


class TestToolsManager(unittest.TestCase):
    """工具管理器测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.tools_dir = Path(self.temp_dir) / ".autocodertools"
        self.tools_dir.mkdir(parents=True)

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_tool(self, name: str, content: str, executable: bool = True) -> Path:
        """创建测试工具文件"""
        tool_path = self.tools_dir / name
        tool_path.write_text(content)
        if executable:
            tool_path.chmod(0o755)
        return tool_path

    def test_init_with_custom_dirs(self):
        """测试使用自定义目录初始化"""
        custom_dirs = [str(self.tools_dir)]
        manager = ToolsManager(tools_dirs=custom_dirs)
        self.assertEqual(manager.tools_dirs, custom_dirs)

    def test_init_with_auto_discovery(self):
        """测试自动发现目录初始化"""
        with patch.object(ToolsManager, '_find_tools_directories') as mock_find:
            mock_find.return_value = ['/mock/dir']
            manager = ToolsManager()
            self.assertEqual(manager.tools_dirs, ['/mock/dir'])
            mock_find.assert_called_once()

    def test_load_tools_success(self):
        """测试成功加载工具"""
        # 创建测试工具
        self.create_test_tool("test_tool.py", """#!/usr/bin/env python3
# 描述: 测试工具
def main():
    pass
""")

        self.create_test_tool("deploy.sh", """#!/bin/bash
# 用法: deploy.sh [环境]
echo "deploying..."
""")

        manager = ToolsManager(tools_dirs=[str(self.tools_dir)])
        result = manager.load_tools()

        self.assertTrue(result.success)
        self.assertEqual(len(result.tools), 2)
        self.assertEqual(result.failed_count, 0)

        # 检查工具名称
        tool_names = [tool.name for tool in result.tools]
        self.assertIn("test_tool", tool_names)
        self.assertIn("deploy", tool_names)

    def test_load_tools_cache(self):
        """测试工具缓存机制"""
        self.create_test_tool("test.py", "#!/usr/bin/env python3\npass")

        manager = ToolsManager(tools_dirs=[str(self.tools_dir)])

        # 第一次加载
        result1 = manager.load_tools()
        self.assertTrue(result1.success)

        # 第二次加载（应该使用缓存）
        result2 = manager.load_tools()
        self.assertTrue(result2.success)
        self.assertIs(result1.tools, result2.tools)  # 应该是同一个对象

        # 强制重新加载
        result3 = manager.load_tools(force_reload=True)
        self.assertTrue(result3.success)
        self.assertIsNot(result1.tools, result3.tools)  # 应该是不同对象

    def test_get_tool_by_name(self):
        """测试根据名称获取工具"""
        self.create_test_tool("finder.py", "#!/usr/bin/env python3\n# 查找工具")

        manager = ToolsManager(tools_dirs=[str(self.tools_dir)])

        # 查找存在的工具
        tool = manager.get_tool_by_name("finder")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "finder")

        # 查找不存在的工具
        tool = manager.get_tool_by_name("nonexistent")
        self.assertIsNone(tool)

    def test_list_tool_names(self):
        """测试列出工具名称"""
        self.create_test_tool("tool1.py", "#!/usr/bin/env python3")
        self.create_test_tool("tool2.sh", "#!/bin/bash")

        manager = ToolsManager(tools_dirs=[str(self.tools_dir)])
        names = manager.list_tool_names()

        self.assertEqual(len(names), 2)
        self.assertIn("tool1", names)
        self.assertIn("tool2", names)

    def test_deduplicate_tools(self):
        """测试工具去重"""
        # 创建两个目录，都有同名工具
        dir1 = Path(self.temp_dir) / "dir1"
        dir2 = Path(self.temp_dir) / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # 在dir1中创建工具（高优先级）
        tool1_path = dir1 / "same_tool.py"
        tool1_path.write_text("# 来自dir1的工具")
        tool1_path.chmod(0o755)

        # 在dir2中创建同名工具（低优先级）
        tool2_path = dir2 / "same_tool.py"
        tool2_path.write_text("# 来自dir2的工具")
        tool2_path.chmod(0o755)

        manager = ToolsManager(tools_dirs=[str(dir1), str(dir2)])
        result = manager.load_tools()

        self.assertTrue(result.success)
        self.assertEqual(len(result.tools), 1)  # 应该只有一个工具

        # 应该选择高优先级目录（dir1）中的工具
        tool = result.tools[0]
        self.assertEqual(tool.name, "same_tool")
        self.assertEqual(tool.source_directory, str(dir1))

    def test_get_tools_prompt(self):
        """测试生成工具prompt"""
        self.create_test_tool("helper.py", """#!/usr/bin/env python3
# 描述: 帮助工具
# 用法: helper.py [选项]
""")

        manager = ToolsManager(tools_dirs=[str(self.tools_dir)])

        # 测试prompt方法存在
        self.assertTrue(hasattr(manager.get_tools_prompt, 'prompt'))

        # 获取prompt内容
        prompt = manager.get_tools_prompt.prompt()

        # 检查prompt内容包含预期信息
        self.assertIn("How to Create External Tools", prompt)


class TestToolsUtils(unittest.TestCase):
    """工具函数测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, name: str, content: str, executable: bool = False) -> Path:
        """创建临时文件"""
        file_path = Path(self.temp_dir) / name
        file_path.write_text(content)
        if executable:
            file_path.chmod(0o755)
        return file_path

    def test_is_tool_command_file_valid_extensions(self):
        """测试有效的工具文件扩展名"""
        valid_files = [
            "tool.py", "script.sh", "app.js",
            "program.rb", "script.pl", "web.php",
            "binary"  # 无扩展名的可执行文件
        ]

        for filename in valid_files:
            file_path = self.create_temp_file(filename, "content", executable=True)
            self.assertTrue(is_tool_command_file(str(file_path)), f"{filename} 应该是有效的工具文件")

    def test_is_tool_command_file_invalid_extensions(self):
        """测试无效的工具文件扩展名"""
        invalid_files = [
            "document.txt", "data.json", "config.yml", "image.png"
        ]

        for filename in invalid_files:
            file_path = self.create_temp_file(filename, "content")
            self.assertFalse(is_tool_command_file(str(file_path)), f"{filename} 不应该是有效的工具文件")

    def test_is_tool_command_file_nonexistent(self):
        """测试不存在的文件"""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.py")
        self.assertFalse(is_tool_command_file(nonexistent_path))

    def test_extract_help_from_file_comments_python(self):
        """测试从Python文件注释提取帮助信息"""
        content = """#!/usr/bin/env python3
# 描述: 这是一个测试工具
# 用法: test_tool.py [选项]
#
# 选项:
#   -h, --help  显示帮助信息
#   -v, --version  显示版本信息

def main():
    pass
"""
        file_path = self.create_temp_file("test.py", content)
        help_text = _extract_help_from_file_comments(str(file_path))

        self.assertIn("描述: 这是一个测试工具", help_text)
        self.assertIn("用法: test_tool.py [选项]", help_text)
        self.assertIn("选项:", help_text)

    def test_extract_help_from_file_comments_shell(self):
        """测试从Shell脚本注释提取帮助信息"""
        content = """#!/bin/bash
# 用法: deploy.sh [环境]
#
# 环境:
#   dev   开发环境
#   prod  生产环境

echo "deploying..."
"""
        file_path = self.create_temp_file("deploy.sh", content)
        help_text = _extract_help_from_file_comments(str(file_path))

        self.assertIn("用法: deploy.sh [环境]", help_text)
        self.assertIn("环境:", help_text)

    def test_get_project_name(self):
        """测试获取项目名称"""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/home/user/my_project")
            name = get_project_name()
            self.assertEqual(name, "my_project")

    @patch('subprocess.run')
    def test_extract_tool_help_with_help_command(self, mock_run):
        """测试通过help命令提取帮助信息"""
        # 模拟成功的help命令输出
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "工具使用说明：\n  tool help - 显示帮助\n  tool run - 运行工具"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        file_path = self.create_temp_file("tool.py", "#!/usr/bin/env python3", executable=True)
        help_text = extract_tool_help(str(file_path))

        self.assertIn("工具使用说明", help_text)
        self.assertIn("tool help", help_text)

    @patch('subprocess.run')
    def test_extract_tool_help_fallback_to_comments(self, mock_run):
        """测试当help命令失败时回退到注释提取"""
        # 模拟help命令失败
        mock_run.side_effect = Exception("Command failed")

        content = """#!/usr/bin/env python3
# 用法: tool.py [选项]
# 这是一个测试工具
"""
        file_path = self.create_temp_file("tool.py", content, executable=True)
        help_text = extract_tool_help(str(file_path))

        self.assertIn("用法: tool.py [选项]", help_text)


if __name__ == '__main__':
    unittest.main()
