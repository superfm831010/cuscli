import pytest
from .tool_content_detector import ToolContentDetector


class TestToolContentDetector:
    """测试 ToolContentDetector 类的各种功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.detector = ToolContentDetector()

    def test_init(self):
        """测试初始化"""
        detector = ToolContentDetector()
        assert detector.replacement_message == "Content cleared to save tokens"
        assert len(detector.supported_tools) == 2
        assert "write_to_file" in detector.supported_tools
        assert "replace_in_file" in detector.supported_tools

    def test_init_with_custom_message(self):
        """测试自定义替换消息的初始化"""
        custom_message = "Custom replacement message"
        detector = ToolContentDetector(replacement_message=custom_message)
        assert detector.replacement_message == custom_message

    def test_detect_tool_call_write_to_file(self):
        """测试检测 write_to_file 工具调用"""
        content = """Some text before
<write_to_file>
<path>test.py</path>
<content>
def hello():
    print("Hello, World!")
</content>
</write_to_file>
Some text after"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert result['tool_name'] == 'write_to_file'
        assert 'def hello():' in result['content_inner']
        assert result['start_pos'] > 0
        assert result['end_pos'] > result['start_pos']

    def test_detect_tool_call_replace_in_file(self):
        """测试检测 replace_in_file 工具调用"""
        content = """Some text before
<replace_in_file>
<path>test.py</path>
<diff>
- old_function()
+ new_function()
</diff>
</replace_in_file>
Some text after"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert result['tool_name'] == 'replace_in_file'
        assert 'old_function()' in result['content_inner']
        assert 'new_function()' in result['content_inner']

    def test_detect_tool_call_case_insensitive(self):
        """测试大小写不敏感的工具调用检测"""
        content = """
<WRITE_TO_FILE>
<path>test.py</path>
<CONTENT>
print("test")
</CONTENT>
</WRITE_TO_FILE>"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert result['tool_name'] == 'write_to_file'

    def test_detect_tool_call_no_tool(self):
        """测试不包含工具调用的内容"""
        content = "This is just plain text without any tool calls."
        result = self.detector.detect_tool_call(content)
        assert result is None

    def test_detect_tool_call_empty_content(self):
        """测试空内容"""
        result = self.detector.detect_tool_call("")
        assert result is None

        result = self.detector.detect_tool_call(None)
        assert result is None

    def test_detect_tool_call_incomplete_tool(self):
        """测试不完整的工具调用"""
        content = "<write_to_file><path>test.py</path>"
        result = self.detector.detect_tool_call(content)
        assert result is None

    def test_replace_tool_content_short_content(self):
        """测试替换短内容（不应该替换）"""
        content = """
<write_to_file>
<path>test.py</path>
<content>
print("short")
</content>
</write_to_file>"""

        new_content, replaced = self.detector.replace_tool_content(content, max_content_length=500)
        assert not replaced
        assert new_content == content

    def test_replace_tool_content_long_content(self):
        """测试替换长内容"""
        long_code = "def test():\n    " + "print('line')\n    " * 50
        content = f"""
<write_to_file>
<path>test.py</path>
<content>
{long_code}
</content>
</write_to_file>"""

        new_content, replaced = self.detector.replace_tool_content(content, max_content_length=100)
        assert replaced
        assert "Content cleared to save tokens" in new_content
        assert long_code not in new_content
        assert "<write_to_file>" in new_content
        assert "</write_to_file>" in new_content

    def test_replace_tool_content_replace_in_file(self):
        """测试替换 replace_in_file 中的长内容"""
        long_diff = "- old_line\n+ new_line\n" * 50
        content = f"""
<replace_in_file>
<path>test.py</path>
<diff>
{long_diff}
</diff>
</replace_in_file>"""

        new_content, replaced = self.detector.replace_tool_content(content, max_content_length=100)
        assert replaced
        assert "Content cleared to save tokens" in new_content
        assert long_diff not in new_content
        assert "<diff>" in new_content
        assert "</diff>" in new_content

    def test_replace_tool_content_no_tool(self):
        """测试替换不包含工具调用的内容"""
        content = "This is just plain text."
        new_content, replaced = self.detector.replace_tool_content(content)
        assert not replaced
        assert new_content == content

    def test_get_tool_content_stats_with_tool(self):
        """测试获取包含工具调用的统计信息"""
        content = """Some prefix
<write_to_file>
<path>test.py</path>
<content>
def hello():
    print("Hello!")
</content>
</write_to_file>
Some suffix"""

        stats = self.detector.get_tool_content_stats(content)
        assert stats['has_tool_call'] is True
        assert stats['tool_name'] == 'write_to_file'
        assert stats['total_length'] == len(content)
        assert stats['tool_content_length'] > 0
        assert stats['prefix_length'] > 0
        assert stats['suffix_length'] > 0

    def test_get_tool_content_stats_no_tool(self):
        """测试获取不包含工具调用的统计信息"""
        content = "This is just plain text."
        stats = self.detector.get_tool_content_stats(content)
        assert stats['has_tool_call'] is False
        assert stats['total_length'] == len(content)

    def test_get_tool_content_stats_empty(self):
        """测试获取空内容的统计信息"""
        stats = self.detector.get_tool_content_stats("")
        assert stats['has_tool_call'] is False
        assert stats['total_length'] == 0

    def test_is_tool_call_content_true(self):
        """测试判断包含工具调用的内容"""
        content = """
<write_to_file>
<path>test.py</path>
<content>print("test")</content>
</write_to_file>"""

        assert self.detector.is_tool_call_content(content) is True

    def test_is_tool_call_content_false(self):
        """测试判断不包含工具调用的内容"""
        content = "This is just plain text."
        assert self.detector.is_tool_call_content(content) is False

    def test_extract_tool_content_write_to_file(self):
        """测试提取 write_to_file 的内容"""
        content = """
<write_to_file>
<path>test.py</path>
<content>
def hello():
    print("Hello!")
</content>
</write_to_file>"""

        extracted = self.detector.extract_tool_content(content)
        assert extracted is not None
        assert "def hello():" in extracted
        assert 'print("Hello!")' in extracted

    def test_extract_tool_content_replace_in_file(self):
        """测试提取 replace_in_file 的内容"""
        content = """
<replace_in_file>
<path>test.py</path>
<diff>
- old_function()
+ new_function()
</diff>
</replace_in_file>"""

        extracted = self.detector.extract_tool_content(content)
        assert extracted is not None
        assert "old_function()" in extracted
        assert "new_function()" in extracted

    def test_extract_tool_content_no_tool(self):
        """测试提取不包含工具调用的内容"""
        content = "This is just plain text."
        extracted = self.detector.extract_tool_content(content)
        assert extracted is None

    def test_get_supported_tools(self):
        """测试获取支持的工具列表"""
        tools = self.detector.get_supported_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2
        assert "write_to_file" in tools
        assert "replace_in_file" in tools

    def test_multiple_tool_calls(self):
        """测试包含多个工具调用的内容（应该只检测第一个）"""
        content = """
<write_to_file>
<path>test1.py</path>
<content>print("first")</content>
</write_to_file>

<write_to_file>
<path>test2.py</path>
<content>print("second")</content>
</write_to_file>"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert result['tool_name'] == 'write_to_file'
        assert 'print("first")' in result['content_inner']

    def test_nested_tags(self):
        """测试嵌套标签的处理"""
        content = """
<write_to_file>
<path>test.py</path>
<content>
<div>
    <p>This is HTML content</p>
</div>
</content>
</write_to_file>"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert "<div>" in result['content_inner']
        assert "<p>This is HTML content</p>" in result['content_inner']

    def test_multiline_content(self):
        """测试多行内容的处理"""
        content = """
<write_to_file>
<path>test.py</path>
<content>
class TestClass:
    def __init__(self):
        self.value = 42
    
    def method(self):
        return self.value
</content>
</write_to_file>"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert "class TestClass:" in result['content_inner']
        assert "def __init__(self):" in result['content_inner']
        assert "def method(self):" in result['content_inner']

    def test_content_with_special_characters(self):
        """测试包含特殊字符的内容"""
        content = """
<write_to_file>
<path>test.py</path>
<content>
# This is a comment with special chars: !@#$%^&*()
print("String with 'quotes' and \"double quotes\"")
regex = r"[a-zA-Z0-9]+"
</content>
</write_to_file>"""

        result = self.detector.detect_tool_call(content)
        assert result is not None
        assert "!@#$%^&*()" in result['content_inner']
        assert "'quotes'" in result['content_inner']  # 修复：查找单引号包围的quotes
        assert r'[a-zA-Z0-9]+' in result['content_inner']


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 