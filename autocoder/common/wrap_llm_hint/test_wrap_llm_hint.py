"""
Wrap LLM Hint 模块测试套件

完整测试 WrapLLMHint 核心类、工具函数和集成功能。
使用 pytest 框架进行测试。
"""

import pytest
import unittest
from typing import List, Dict, Any

from .wrap_llm_hint import WrapLLMHint, HintConfig
from .utils import (
    add_hint_to_text,
    create_hint_wrapper,
    extract_hint_from_text,
    extract_content_from_text,
    has_hint_in_text,
    replace_hint_in_text,
    add_multiple_hints_to_text,
    get_text_statistics,
    batch_add_hints,
    safe_add_hint,
    create_conversation_hint,
    merge_with_last_user_message,
    append_hint_to_text,
    safe_append_hint
)


class TestWrapLLMHint(unittest.TestCase):
    """测试核心 WrapLLMHint 类"""
    
    def setUp(self):
        """测试前置设置"""
        self.wrapper = WrapLLMHint()
        self.custom_config = HintConfig(
            separator="\n===\n",
            prefix="[HINT] ",
            suffix=" [/HINT]",
            allow_empty_hint=True,
            strip_whitespace=False
        )
        self.custom_wrapper = WrapLLMHint(self.custom_config)
    
    def test_init_default_config(self):
        """测试默认配置初始化"""
        wrapper = WrapLLMHint()
        self.assertEqual(wrapper.config.separator, "\n---\n")
        self.assertEqual(wrapper.config.prefix, "[[")
        self.assertEqual(wrapper.config.suffix, "]]")
        self.assertFalse(wrapper.config.allow_empty_hint)
        self.assertTrue(wrapper.config.strip_whitespace)
    
    def test_init_custom_config(self):
        """测试自定义配置初始化"""
        self.assertEqual(self.custom_wrapper.config.separator, "\n===\n")
        self.assertEqual(self.custom_wrapper.config.prefix, "[HINT] ")
        self.assertEqual(self.custom_wrapper.config.suffix, " [/HINT]")
        self.assertTrue(self.custom_wrapper.config.allow_empty_hint)
        self.assertFalse(self.custom_wrapper.config.strip_whitespace)
    
    def test_add_hint_basic(self):
        """测试基本提示添加功能"""
        content = "这是原始内容"
        hint = "这是提示信息"
        expected = "这是原始内容\n---\n[[这是提示信息]]"
        
        result = self.wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_with_custom_config(self):
        """测试自定义配置的提示添加"""
        content = "测试内容"
        hint = "测试提示"
        expected = "测试内容\n===\n[HINT] 测试提示 [/HINT]"
        
        result = self.custom_wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_empty_content(self):
        """测试空内容的提示添加"""
        content = ""
        hint = "提示信息"
        expected = "\n---\n[[提示信息]]"
        
        result = self.wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_whitespace_content(self):
        """测试只有空白字符的内容"""
        content = "   \n  \t  "
        hint = "提示信息"
        expected = "\n---\n[[提示信息]]"
        
        result = self.wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_strip_whitespace(self):
        """测试去除提示空白字符"""
        content = "内容"
        hint = "   提示信息   "
        expected = "内容\n---\n[[提示信息]]"
        
        result = self.wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_no_strip_whitespace(self):
        """测试不去除提示空白字符"""
        content = "内容"
        hint = "   提示信息   "
        expected = "内容\n===\n[HINT]    提示信息    [/HINT]"
        
        result = self.custom_wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_empty_hint_not_allowed(self):
        """测试不允许空提示时的错误处理"""
        content = "内容"
        hint = ""
        
        with self.assertRaises(ValueError):
            self.wrapper.add_hint(content, hint)
    
    def test_add_hint_empty_hint_allowed(self):
        """测试允许空提示时的处理"""
        content = "内容"
        hint = ""
        expected = "内容\n===\n[HINT]  [/HINT]"  # 空提示时仍然添加前缀后缀
        
        result = self.custom_wrapper.add_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_type_validation(self):
        """测试输入类型验证"""
        with self.assertRaises(TypeError):
            self.wrapper.add_hint(123, "hint")  # type: ignore
        
        with self.assertRaises(TypeError):
            self.wrapper.add_hint("content", 123)  # type: ignore
    
    def test_add_hint_safe_success(self):
        """测试安全添加提示成功的情况"""
        content = "内容"
        hint = "提示"
        fallback = "备用提示"
        expected = "内容\n---\n[[提示]]"
        
        result = self.wrapper.add_hint_safe(content, hint, fallback)
        self.assertEqual(result, expected)
    
    def test_add_hint_safe_fallback(self):
        """测试安全添加提示使用备用提示"""
        content = "内容"
        hint = ""  # 空提示会出错
        fallback = "备用提示"
        expected = "内容\n---\n[[备用提示]]"
        
        result = self.wrapper.add_hint_safe(content, hint, fallback)
        self.assertEqual(result, expected)
    
    def test_add_hint_safe_no_fallback(self):
        """测试安全添加提示无备用提示"""
        content = "内容"
        hint = ""
        fallback = ""
        
        result = self.wrapper.add_hint_safe(content, hint, fallback)
        self.assertEqual(result, content)  # 返回原内容
    
    def test_add_multiple_hints_basic(self):
        """测试添加多个提示"""
        content = "内容"
        hints = ["提示1", "提示2", "提示3"]
        
        result = self.wrapper.add_multiple_hints(content, hints)
        
        self.assertIn("提示1", result)
        self.assertIn("提示2", result)
        self.assertIn("提示3", result)
        # 验证分隔符数量
        self.assertEqual(result.count("\n---\n"), 3)
    
    def test_add_multiple_hints_empty_list(self):
        """测试添加空提示列表"""
        content = "内容"
        hints = []
        
        result = self.wrapper.add_multiple_hints(content, hints)
        self.assertEqual(result, content)
    
    def test_add_multiple_hints_with_empty_hints(self):
        """测试添加包含空提示的列表"""
        content = "内容"
        hints = ["提示1", "", "提示3"]
        
        result = self.wrapper.add_multiple_hints(content, hints)
        
        # 只应添加非空提示
        self.assertIn("提示1", result)
        self.assertIn("提示3", result)
        self.assertEqual(result.count("\n---\n"), 2)
    
    def test_extract_hint_basic(self):
        """测试基本提示提取"""
        wrapped_content = "内容\n---\n[[提示信息]]"
        
        result = self.wrapper.extract_hint(wrapped_content)
        self.assertEqual(result, "提示信息")
    
    def test_extract_hint_no_hint(self):
        """测试无提示内容的提取"""
        content = "只有内容，没有提示"
        
        result = self.wrapper.extract_hint(content)
        self.assertIsNone(result)
    
    def test_extract_hint_multiple_separators(self):
        """测试多个分隔符时提取最后一个提示"""
        wrapped_content = "内容\n---\n[[提示1]]\n---\n[[提示2]]"
        
        result = self.wrapper.extract_hint(wrapped_content)
        self.assertEqual(result, "提示2")
    
    def test_extract_hint_custom_config(self):
        """测试自定义配置的提示提取"""
        wrapped_content = "内容\n===\n[HINT] 提示信息 [/HINT]"
        
        result = self.custom_wrapper.extract_hint(wrapped_content)
        self.assertEqual(result, "提示信息")  # 实际实现仍然去除了空白字符
    
    def test_extract_hint_invalid_input(self):
        """测试无效输入的提示提取"""
        result = self.wrapper.extract_hint(123)  # type: ignore
        self.assertIsNone(result)
    
    def test_extract_content_basic(self):
        """测试基本内容提取"""
        wrapped_content = "原始内容\n---\n[[提示信息]]"
        
        result = self.wrapper.extract_content(wrapped_content)
        self.assertEqual(result, "原始内容")
    
    def test_extract_content_no_hint(self):
        """测试无提示内容的内容提取"""
        content = "只有内容"
        
        result = self.wrapper.extract_content(content)
        self.assertEqual(result, content)
    
    def test_extract_content_multiple_separators(self):
        """测试多个分隔符时提取内容"""
        wrapped_content = "第一部分\n---\n[[提示1]]\n---\n[[提示2]]"
        
        result = self.wrapper.extract_content(wrapped_content)
        self.assertEqual(result, "第一部分\n---\n[[提示1]]")
    
    def test_extract_content_invalid_input(self):
        """测试无效输入的内容提取"""
        result = self.wrapper.extract_content(123)  # type: ignore
        self.assertEqual(result, "")
    
    def test_has_hint_true(self):
        """测试包含提示的内容检查"""
        content = "内容\n---\n[[提示]]"
        
        result = self.wrapper.has_hint(content)
        self.assertTrue(result)
    
    def test_has_hint_false(self):
        """测试不包含提示的内容检查"""
        content = "只有内容"
        
        result = self.wrapper.has_hint(content)
        self.assertFalse(result)
    
    def test_has_hint_invalid_input(self):
        """测试无效输入的检查"""
        result = self.wrapper.has_hint(123)  # type: ignore
        self.assertFalse(result)
    
    def test_replace_hint_basic(self):
        """测试基本提示替换"""
        wrapped_content = "内容\n---\n[[旧提示]]"
        new_hint = "新提示"
        expected = "内容\n---\n[[新提示]]"
        
        result = self.wrapper.replace_hint(wrapped_content, new_hint)
        self.assertEqual(result, expected)
    
    def test_replace_hint_no_existing_hint(self):
        """测试替换不存在的提示"""
        content = "只有内容"
        new_hint = "新提示"
        expected = "只有内容\n---\n[[新提示]]"
        
        result = self.wrapper.replace_hint(content, new_hint)
        self.assertEqual(result, expected)
    
    def test_get_statistics_basic(self):
        """测试基本统计信息获取"""
        wrapped_content = "内容\n---\n[[提示]]"
        
        stats = self.wrapper.get_statistics(wrapped_content)
        
        self.assertEqual(stats["total_length"], len(wrapped_content))
        self.assertEqual(stats["content_length"], 2)  # "内容"
        self.assertEqual(stats["hint_length"], 2)     # "提示"
        self.assertTrue(stats["has_hint"])
        self.assertEqual(stats["separator_count"], 1)
        self.assertEqual(stats["separator"], "\n---\n")
    
    def test_get_statistics_no_hint(self):
        """测试无提示内容的统计信息"""
        content = "只有内容"
        
        stats = self.wrapper.get_statistics(content)
        
        self.assertEqual(stats["total_length"], len(content))
        self.assertEqual(stats["content_length"], len(content))
        self.assertEqual(stats["hint_length"], 0)
        self.assertFalse(stats["has_hint"])
        self.assertEqual(stats["separator_count"], 0)
    
    def test_get_statistics_invalid_input(self):
        """测试无效输入的统计信息"""
        stats = self.wrapper.get_statistics(123)  # type: ignore
        
        expected = {
            "total_length": 0,
            "content_length": 0,
            "hint_length": 0,
            "has_hint": False,
            "separator_count": 0
        }
        
        for key, value in expected.items():
            self.assertEqual(stats[key], value)
    
    # 新增：append_hint 功能测试
    def test_append_hint_no_existing_hint(self):
        """测试追加提示到没有现有提示的内容"""
        content = "原始内容"
        hint = "新提示"
        expected = "原始内容\n---\n[[新提示]]"
        
        result = self.wrapper.append_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_with_existing_hint(self):
        """测试追加提示到已有提示的内容"""
        content = "原始内容\n---\n[[现有提示]]"
        hint = "追加提示"
        expected = "原始内容\n---\n[[现有提示\n追加提示]]"
        
        result = self.wrapper.append_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_multiple_times(self):
        """测试多次追加提示"""
        content = "原始内容"
        
        # 第一次追加
        result1 = self.wrapper.append_hint(content, "提示1")
        expected1 = "原始内容\n---\n[[提示1]]"
        self.assertEqual(result1, expected1)
        
        # 第二次追加
        result2 = self.wrapper.append_hint(result1, "提示2")
        expected2 = "原始内容\n---\n[[提示1\n提示2]]"
        self.assertEqual(result2, expected2)
        
        # 第三次追加
        result3 = self.wrapper.append_hint(result2, "提示3")
        expected3 = "原始内容\n---\n[[提示1\n提示2\n提示3]]"
        self.assertEqual(result3, expected3)
    
    def test_append_hint_with_custom_config(self):
        """测试自定义配置的追加提示"""
        content = "内容\n===\n[HINT] 现有提示 [/HINT]"
        hint = "追加提示"
        expected = "内容\n===\n[HINT] 现有提示\n追加提示 [/HINT]"
        
        result = self.custom_wrapper.append_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_empty_hint_not_allowed(self):
        """测试追加空提示时的错误处理"""
        content = "内容\n---\n[[现有提示]]"
        hint = ""
        
        with self.assertRaises(ValueError):
            self.wrapper.append_hint(content, hint)
    
    def test_append_hint_empty_hint_allowed(self):
        """测试允许空提示时的追加"""
        content = "内容\n===\n[HINT] 现有提示 [/HINT]"
        hint = ""
        
        # 空提示被允许但实际不会追加
        result = self.custom_wrapper.append_hint(content, hint)
        self.assertEqual(result, content)  # 返回原内容
    
    def test_append_hint_type_validation(self):
        """测试追加提示的输入类型验证"""
        content = "内容\n---\n[[提示]]"
        
        with self.assertRaises(TypeError):
            self.wrapper.append_hint(123, "hint")  # type: ignore
        
        with self.assertRaises(TypeError):
            self.wrapper.append_hint(content, 123)  # type: ignore
    
    def test_append_hint_strip_whitespace(self):
        """测试追加提示时去除空白字符"""
        content = "内容\n---\n[[现有提示]]"
        hint = "   追加提示   "
        expected = "内容\n---\n[[现有提示\n追加提示]]"
        
        result = self.wrapper.append_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_no_strip_whitespace(self):
        """测试追加提示时不去除空白字符"""
        content = "内容\n===\n[HINT] 现有提示 [/HINT]"
        hint = "   追加提示   "
        expected = "内容\n===\n[HINT] 现有提示\n   追加提示    [/HINT]"
        
        result = self.custom_wrapper.append_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_extract_verification(self):
        """测试追加提示后的提取验证"""
        content = "原始内容\n---\n[[第一个提示]]"
        hint = "第二个提示"
        
        result = self.wrapper.append_hint(content, hint)
        
        # 验证可以正确提取内容
        extracted_content = self.wrapper.extract_content(result)
        self.assertEqual(extracted_content, "原始内容")
        
        # 验证可以正确提取合并后的提示
        extracted_hint = self.wrapper.extract_hint(result)
        self.assertEqual(extracted_hint, "第一个提示\n第二个提示")


class TestUtils(unittest.TestCase):
    """测试工具函数模块"""
    
    def test_add_hint_to_text_basic(self):
        """测试基本文本提示添加"""
        content = "测试内容"
        hint = "测试提示"
        expected = "测试内容\n---\n[[测试提示]]"
        
        result = add_hint_to_text(content, hint)
        self.assertEqual(result, expected)
    
    def test_add_hint_to_text_custom_separator(self):
        """测试自定义分隔符的提示添加"""
        content = "测试内容"
        hint = "测试提示"
        separator = "\n===\n"
        expected = "测试内容\n===\n[[测试提示]]"
        
        result = add_hint_to_text(content, hint, separator)
        self.assertEqual(result, expected)
    
    def test_create_hint_wrapper_default(self):
        """测试创建默认配置的包装器"""
        wrapper = create_hint_wrapper()
        
        self.assertEqual(wrapper.config.separator, "\n---\n")
        self.assertEqual(wrapper.config.prefix, "[[")
        self.assertEqual(wrapper.config.suffix, "]]")
    
    def test_create_hint_wrapper_custom(self):
        """测试创建自定义配置的包装器"""
        wrapper = create_hint_wrapper(
            separator="\n***\n",
            prefix="[NOTE] ",
            suffix=" [/NOTE]",
            allow_empty_hint=True,
            strip_whitespace=False
        )
        
        self.assertEqual(wrapper.config.separator, "\n***\n")
        self.assertEqual(wrapper.config.prefix, "[NOTE] ")
        self.assertEqual(wrapper.config.suffix, " [/NOTE]")
        self.assertTrue(wrapper.config.allow_empty_hint)
        self.assertFalse(wrapper.config.strip_whitespace)
    
    def test_extract_hint_from_text_basic(self):
        """测试从文本提取提示"""
        wrapped_content = "内容\n---\n[[提示信息]]"
        
        result = extract_hint_from_text(wrapped_content)
        self.assertEqual(result, "提示信息")
    
    def test_extract_hint_from_text_custom_separator(self):
        """测试使用自定义分隔符提取提示"""
        wrapped_content = "内容\n***\n[[提示信息]]"
        separator = "\n***\n"
        
        result = extract_hint_from_text(wrapped_content, separator)
        self.assertEqual(result, "提示信息")
    
    def test_extract_hint_from_text_no_hint(self):
        """测试从无提示文本提取"""
        content = "只有内容"
        
        result = extract_hint_from_text(content)
        self.assertIsNone(result)
    
    def test_extract_content_from_text_basic(self):
        """测试从文本提取内容"""
        wrapped_content = "原始内容\n---\n[[提示]]"
        
        result = extract_content_from_text(wrapped_content)
        self.assertEqual(result, "原始内容")
    
    def test_extract_content_from_text_custom_separator(self):
        """测试使用自定义分隔符提取内容"""
        wrapped_content = "原始内容\n***\n[[提示]]"
        separator = "\n***\n"
        
        result = extract_content_from_text(wrapped_content, separator)
        self.assertEqual(result, "原始内容")
    
    def test_has_hint_in_text_true(self):
        """测试检查包含提示的文本"""
        content = "内容\n---\n提示"
        
        result = has_hint_in_text(content)
        self.assertTrue(result)
    
    def test_has_hint_in_text_false(self):
        """测试检查不包含提示的文本"""
        content = "只有内容"
        
        result = has_hint_in_text(content)
        self.assertFalse(result)
    
    def test_replace_hint_in_text_basic(self):
        """测试替换文本中的提示"""
        wrapped_content = "内容\n---\n[[旧提示]]"
        new_hint = "新提示"
        expected = "内容\n---\n[[新提示]]"
        
        result = replace_hint_in_text(wrapped_content, new_hint)
        self.assertEqual(result, expected)
    
    def test_add_multiple_hints_to_text_basic(self):
        """测试给文本添加多个提示"""
        content = "内容"
        hints = ["提示1", "提示2"]
        
        result = add_multiple_hints_to_text(content, hints)
        
        self.assertIn("提示1", result)
        self.assertIn("提示2", result)
        self.assertEqual(result.count("\n---\n"), 2)
    
    def test_get_text_statistics_basic(self):
        """测试获取文本统计信息"""
        wrapped_content = "内容\n---\n[[提示]]"
        
        stats = get_text_statistics(wrapped_content)
        
        self.assertIn("total_length", stats)
        self.assertIn("content_length", stats)
        self.assertIn("hint_length", stats)
        self.assertIn("has_hint", stats)
        self.assertIn("separator_count", stats)
        self.assertTrue(stats["has_hint"])
    
    def test_batch_add_hints_basic(self):
        """测试批量添加提示"""
        contents = ["内容1", "内容2", "内容3"]
        hints = ["提示1", "提示2", "提示3"]
        
        results = batch_add_hints(contents, hints)
        
        self.assertEqual(len(results), 3)
        for i, result in enumerate(results):
            self.assertIn(contents[i], result)
            self.assertIn(hints[i], result)
    
    def test_batch_add_hints_length_mismatch(self):
        """测试批量添加提示时长度不匹配"""
        contents = ["内容1", "内容2"]
        hints = ["提示1"]
        
        with self.assertRaises(ValueError):
            batch_add_hints(contents, hints)
    
    def test_batch_add_hints_with_errors(self):
        """测试批量添加提示时有错误的情况"""
        contents = ["内容1", "内容2"]
        hints = ["提示1", ""]  # 空提示会出错
        
        # 应该不抛出异常，错误时保留原内容
        results = batch_add_hints(contents, hints)
        
        self.assertEqual(len(results), 2)
        self.assertIn("提示1", results[0])
        self.assertEqual(results[1], "内容2")  # 保留原内容
    
    def test_safe_add_hint_success(self):
        """测试安全添加提示成功"""
        content = "内容"
        hint = "提示"
        
        result = safe_add_hint(content, hint)
        expected = "内容\n---\n[[提示]]"
        self.assertEqual(result, expected)
    
    def test_safe_add_hint_fallback(self):
        """测试安全添加提示使用备用提示"""
        content = "内容"
        hint = ""  # 空提示
        fallback = "备用提示"
        
        result = safe_add_hint(content, hint, fallback)
        expected = "内容\n---\n[[备用提示]]"
        self.assertEqual(result, expected)
    
    def test_create_conversation_hint(self):
        """测试创建对话提示"""
        cleanup_message = "对话过长需要清理"
        
        result = create_conversation_hint(cleanup_message)
        self.assertEqual(result, cleanup_message)
    
    def test_merge_with_last_user_message_user_last(self):
        """测试合并到最后一个用户消息"""
        conversations = [
            {"role": "user", "content": "用户消息1"},
            {"role": "assistant", "content": "助手消息"},
            {"role": "user", "content": "用户消息2"}
        ]
        cleanup_message = "清理提示"
        
        result = merge_with_last_user_message(conversations, cleanup_message)
        
        self.assertEqual(len(result), 3)
        self.assertIn("用户消息2", result[-1]["content"])
        self.assertIn("清理提示", result[-1]["content"])
        self.assertIn("\n---\n", result[-1]["content"])
    
    def test_merge_with_last_user_message_assistant_last(self):
        """测试最后一个消息不是用户消息时的合并"""
        conversations = [
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手消息"}
        ]
        cleanup_message = "清理提示"
        
        result = merge_with_last_user_message(conversations, cleanup_message)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[-1]["role"], "user")
        self.assertEqual(result[-1]["content"], cleanup_message)
    
    def test_merge_with_last_user_message_empty_list(self):
        """测试空对话列表的合并"""
        conversations = []
        cleanup_message = "清理提示"
        
        result = merge_with_last_user_message(conversations, cleanup_message)
        self.assertEqual(result, [])
    
    # 新增：append_hint_to_text 功能测试
    def test_append_hint_to_text_no_existing_hint(self):
        """测试追加提示到没有现有提示的文本"""
        content = "原始内容"
        hint = "新提示"
        expected = "原始内容\n---\n[[新提示]]"
        
        result = append_hint_to_text(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_to_text_with_existing_hint(self):
        """测试追加提示到已有提示的文本"""
        content = "原始内容\n---\n[[现有提示]]"
        hint = "追加提示"
        expected = "原始内容\n---\n[[现有提示\n追加提示]]"
        
        result = append_hint_to_text(content, hint)
        self.assertEqual(result, expected)
    
    def test_append_hint_to_text_custom_separator(self):
        """测试使用自定义分隔符追加提示"""
        content = "内容\n***\n[[现有提示]]"
        hint = "追加提示"
        separator = "\n***\n"
        expected = "内容\n***\n[[现有提示\n追加提示]]"
        
        result = append_hint_to_text(content, hint, separator)
        self.assertEqual(result, expected)
    
    def test_append_hint_to_text_multiple_times(self):
        """测试多次追加提示到文本"""
        content = "原始内容"
        
        # 第一次追加
        result1 = append_hint_to_text(content, "提示1")
        expected1 = "原始内容\n---\n[[提示1]]"
        self.assertEqual(result1, expected1)
        
        # 第二次追加
        result2 = append_hint_to_text(result1, "提示2")
        expected2 = "原始内容\n---\n[[提示1\n提示2]]"
        self.assertEqual(result2, expected2)
        
        # 第三次追加
        result3 = append_hint_to_text(result2, "提示3")
        expected3 = "原始内容\n---\n[[提示1\n提示2\n提示3]]"
        self.assertEqual(result3, expected3)
    
    def test_safe_append_hint_success(self):
        """测试安全追加提示成功"""
        content = "内容\n---\n[[现有提示]]"
        hint = "追加提示"
        expected = "内容\n---\n[[现有提示\n追加提示]]"
        
        result = safe_append_hint(content, hint)
        self.assertEqual(result, expected)
    
    def test_safe_append_hint_fallback(self):
        """测试安全追加提示使用备用提示"""
        content = "内容\n---\n[[现有提示]]"
        hint = ""  # 空提示会出错
        fallback = "备用提示"
        expected = "内容\n---\n[[现有提示\n备用提示]]"
        
        result = safe_append_hint(content, hint, fallback)
        self.assertEqual(result, expected)
    
    def test_safe_append_hint_no_fallback(self):
        """测试安全追加提示无备用提示"""
        content = "内容\n---\n[[现有提示]]"
        hint = ""
        fallback = ""
        
        result = safe_append_hint(content, hint, fallback)
        self.assertEqual(result, content)  # 返回原内容
    
    def test_merge_with_last_user_message_append_mode(self):
        """测试使用追加模式合并到最后一个用户消息"""
        conversations = [
            {"role": "user", "content": "用户消息\n---\n[[现有提示]]"},
            {"role": "assistant", "content": "助手消息"}
        ]
        cleanup_message = "追加提示"
        
        # 使用追加模式
        result = merge_with_last_user_message(conversations, cleanup_message, append_mode=True)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[-1]["role"], "user")
        self.assertEqual(result[-1]["content"], cleanup_message)
        
        # 测试最后一个是用户消息的情况
        conversations2 = [
            {"role": "user", "content": "用户消息\n---\n[[现有提示]]"}
        ]
        
        result2 = merge_with_last_user_message(conversations2, cleanup_message, append_mode=True)
        
        self.assertEqual(len(result2), 1)
        self.assertIn("用户消息", result2[0]["content"])
        self.assertIn("现有提示", result2[0]["content"])
        self.assertIn("追加提示", result2[0]["content"])
        
        # 验证格式正确
        expected_pattern = "用户消息\n---\n[[现有提示\n追加提示]]"
        self.assertEqual(result2[0]["content"], expected_pattern)
    
    def test_merge_with_last_user_message_replace_mode(self):
        """测试使用替换模式合并到最后一个用户消息（默认行为）"""
        conversations = [
            {"role": "user", "content": "用户消息\n---\n[[现有提示]]"}
        ]
        cleanup_message = "新提示"
        
        # 使用替换模式（默认）
        result = merge_with_last_user_message(conversations, cleanup_message, append_mode=False)
        
        self.assertEqual(len(result), 1)
        self.assertIn("用户消息", result[0]["content"])
        self.assertIn("新提示", result[0]["content"])
        # 应该不包含原有提示（被替换了）
        self.assertNotIn("现有提示", result[0]["content"])


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 1. 创建原始内容
        content = "这是一个重要的用户消息"
        hint = "请注意：这条消息需要特别关注"
        
        # 2. 添加提示
        wrapped_content = add_hint_to_text(content, hint)
        
        # 3. 验证包含提示
        self.assertTrue(has_hint_in_text(wrapped_content))
        
        # 4. 提取内容和提示
        extracted_content = extract_content_from_text(wrapped_content)
        extracted_hint = extract_hint_from_text(wrapped_content)
        
        # 5. 验证提取结果
        self.assertEqual(extracted_content, content)
        self.assertEqual(extracted_hint, hint)
        
        # 6. 替换提示
        new_hint = "更新的提示信息"
        updated_content = replace_hint_in_text(wrapped_content, new_hint)
        
        # 7. 验证替换结果
        updated_hint = extract_hint_from_text(updated_content)
        self.assertEqual(updated_hint, new_hint)
    
    def test_conversation_integration(self):
        """测试对话系统集成"""
        # 模拟 agentic_conversation_pruner.py 的使用场景
        conversations = [
            {"role": "user", "content": "请帮我分析这段代码"},
            {"role": "assistant", "content": "好的，我来为您分析"},
            {"role": "user", "content": "还有其他建议吗？"}
        ]
        
        cleanup_message = "[[对话内容过长，请使用 conversation_message_ids_write 工具保存要删除的消息ID。]]"
        
        # 合并清理消息到最后一个用户消息
        updated_conversations = merge_with_last_user_message(conversations, cleanup_message)
        
        # 验证结果
        self.assertEqual(len(updated_conversations), 3)
        last_message = updated_conversations[-1]
        self.assertEqual(last_message["role"], "user")
        self.assertIn("还有其他建议吗？", last_message["content"])
        self.assertIn(cleanup_message, last_message["content"])
        
        # 验证可以提取原始消息
        original_content = extract_content_from_text(last_message["content"])
        self.assertEqual(original_content, "还有其他建议吗？")
        
        # 验证可以提取清理消息
        extracted_cleanup = extract_hint_from_text(last_message["content"])
        self.assertEqual(extracted_cleanup, cleanup_message)
    
    def test_batch_processing_integration(self):
        """测试批量处理集成"""
        # 准备批量数据
        contents = [
            "第一个文档内容",
            "第二个文档内容", 
            "第三个文档内容"
        ]
        hints = [
            "第一个文档的处理提示",
            "第二个文档的处理提示",
            "第三个文档的处理提示"
        ]
        
        # 批量添加提示
        results = batch_add_hints(contents, hints)
        
        # 验证批量处理结果
        self.assertEqual(len(results), 3)
        
        for i, result in enumerate(results):
            # 验证每个结果都包含原内容和提示
            self.assertIn(contents[i], result)
            self.assertIn(hints[i], result)
            
            # 验证可以单独提取内容和提示
            extracted_content = extract_content_from_text(result)
            extracted_hint = extract_hint_from_text(result)
            
            self.assertEqual(extracted_content, contents[i])
            self.assertEqual(extracted_hint, hints[i])
    
    def test_custom_configuration_integration(self):
        """测试自定义配置集成"""
        # 创建自定义配置
        wrapper = create_hint_wrapper(
            separator="\n+++\n",
            prefix="[SYSTEM] ",
            suffix=" [/SYSTEM]",
            allow_empty_hint=True
        )
        
        content = "系统消息内容"
        hint = "重要的系统提示"
        
        # 使用自定义配置添加提示
        result = wrapper.add_hint(content, hint)
        
        # 验证自定义格式
        self.assertIn("\n+++\n", result)
        self.assertIn("[SYSTEM]", result)
        self.assertIn("[/SYSTEM]", result)
        
        # 验证可以正确提取（需要使用相同配置）
        extracted_content = wrapper.extract_content(result)
        extracted_hint = wrapper.extract_hint(result)
        
        self.assertEqual(extracted_content, content)
        self.assertEqual(extracted_hint, hint)
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试各种错误情况的处理
        
        # 1. 空提示处理
        content = "测试内容"
        empty_hint = ""
        fallback_hint = "备用提示"
        
        result = safe_add_hint(content, empty_hint, fallback_hint)
        self.assertIn(fallback_hint, result)
        
        # 2. 批量处理中的错误处理
        contents = ["内容1", "内容2"]
        hints = ["正常提示", ""]  # 一个正常，一个空提示
        
        results = batch_add_hints(contents, hints)
        self.assertEqual(len(results), 2)
        # 第一个应该成功添加提示
        self.assertIn("正常提示", results[0])
        # 第二个应该保留原内容（因为空提示出错）
        self.assertEqual(results[1], "内容2")
    
    def test_statistics_integration(self):
        """测试统计功能集成"""
        content = "这是一段测试内容"
        hint = "这是测试提示信息"
        
        # 添加提示
        wrapped_content = add_hint_to_text(content, hint)
        
        # 获取统计信息
        stats = get_text_statistics(wrapped_content)
        
        # 验证统计信息
        self.assertEqual(stats["content_length"], len(content))
        self.assertEqual(stats["hint_length"], len(hint))
        self.assertTrue(stats["has_hint"])
        self.assertEqual(stats["separator_count"], 1)
        self.assertEqual(stats["total_length"], len(wrapped_content))
        
        # 添加多个提示并验证统计
        multiple_hints = ["提示1", "提示2", "提示3"]
        multi_wrapped = add_multiple_hints_to_text(content, multiple_hints)
        multi_stats = get_text_statistics(multi_wrapped)
        
        self.assertEqual(multi_stats["separator_count"], 3)
        self.assertTrue(multi_stats["has_hint"])
    
    def test_append_hint_integration(self):
        """测试追加hint功能的集成测试"""
        # 测试用户需求：从 ---\n[[hint1]] 追加后为 ---\n[[hint1\nhint2]]
        
        # 1. 创建带有初始hint的内容
        content = "这是原始文本内容"
        initial_hint = "hint1"
        
        wrapped_content = add_hint_to_text(content, initial_hint)
        expected_initial = "这是原始文本内容\n---\n[[hint1]]"
        self.assertEqual(wrapped_content, expected_initial)
        
        # 2. 追加新的hint
        additional_hint = "hint2"
        appended_content = append_hint_to_text(wrapped_content, additional_hint)
        expected_appended = "这是原始文本内容\n---\n[[hint1\nhint2]]"
        self.assertEqual(appended_content, expected_appended)
        
        # 3. 验证可以正确提取内容和组合后的hint
        extracted_content = extract_content_from_text(appended_content)
        extracted_hint = extract_hint_from_text(appended_content)
        
        self.assertEqual(extracted_content, content)
        self.assertEqual(extracted_hint, "hint1\nhint2")
        
        # 4. 继续追加第三个hint
        third_hint = "hint3"
        final_content = append_hint_to_text(appended_content, third_hint)
        expected_final = "这是原始文本内容\n---\n[[hint1\nhint2\nhint3]]"
        self.assertEqual(final_content, expected_final)
        
        # 5. 验证最终的提取结果
        final_extracted_content = extract_content_from_text(final_content)
        final_extracted_hint = extract_hint_from_text(final_content)
        
        self.assertEqual(final_extracted_content, content)
        self.assertEqual(final_extracted_hint, "hint1\nhint2\nhint3")
    
    def test_append_vs_add_behavior_difference(self):
        """测试追加和添加功能的行为差异"""
        content = "测试内容\n---\n[[现有提示]]"
        new_hint = "新提示"
        
        # 使用 add_hint_to_text（会创建新的分隔符）
        add_result = add_hint_to_text(content, new_hint)
        # 这会导致: "测试内容\n---\n[[现有提示]]\n---\n[[新提示]]"
        self.assertEqual(add_result.count("\n---\n"), 2)
        
        # 使用 append_hint_to_text（会追加到现有hint中）
        append_result = append_hint_to_text(content, new_hint)
        expected_append = "测试内容\n---\n[[现有提示\n新提示]]"
        self.assertEqual(append_result, expected_append)
        self.assertEqual(append_result.count("\n---\n"), 1)
        
        # 验证提取的hint内容不同
        add_hint_extracted = extract_hint_from_text(add_result)
        append_hint_extracted = extract_hint_from_text(append_result)
        
        self.assertEqual(add_hint_extracted, new_hint)  # add 只提取最后一个
        self.assertEqual(append_hint_extracted, "现有提示\n新提示")  # append 提取组合的
    
    def test_conversation_append_integration(self):
        """测试对话系统中的追加功能集成"""
        # 模拟已经有hint的对话消息
        conversations = [
            {"role": "user", "content": "请帮我分析代码\n---\n[[重要：这是复杂的代码]]"},
            {"role": "assistant", "content": "好的，我来分析"},
            {"role": "user", "content": "还有其他问题吗？\n---\n[[请仔细检查]]"}
        ]
        
        cleanup_message = "对话内容过长，请使用 conversation_message_ids_write 工具"
        
        # 使用追加模式合并
        result = merge_with_last_user_message(conversations, cleanup_message, append_mode=True)
        
        # 验证结果
        self.assertEqual(len(result), 3)
        last_message = result[-1]
        
        # 验证内容包含原始消息
        self.assertIn("还有其他问题吗？", last_message["content"])
        
        # 验证包含原有hint和新hint
        self.assertIn("请仔细检查", last_message["content"])
        self.assertIn(cleanup_message, last_message["content"])
        
        # 验证格式正确（应该是追加模式的格式）
        expected_content = "还有其他问题吗？\n---\n[[请仔细检查\n对话内容过长，请使用 conversation_message_ids_write 工具]]"
        self.assertEqual(last_message["content"], expected_content)
        
        # 验证提取功能
        extracted_content = extract_content_from_text(last_message["content"])
        extracted_hint = extract_hint_from_text(last_message["content"])
        
        self.assertEqual(extracted_content, "还有其他问题吗？")
        self.assertEqual(extracted_hint, "请仔细检查\n对话内容过长，请使用 conversation_message_ids_write 工具")


if __name__ == "__main__":
    # 支持直接运行测试文件
    unittest.main(verbosity=2)
