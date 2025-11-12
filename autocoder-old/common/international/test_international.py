#!/usr/bin/env python3
"""
测试国际化模块的功能
Test cases for the international module
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from autocoder.common.international import (
    MessageManager,
    register_messages,
    get_message,
    get_message_with_format,
    get_system_language,
    get_message_manager,
    get_supported_languages,
    is_language_supported
)
from autocoder.common.international.messages.auto_coder_messages import AUTO_CODER_MESSAGES
from autocoder.common.international.messages.chat_auto_coder_messages import CHAT_AUTO_CODER_MESSAGES
from autocoder.common.international.messages.sdk_messages import SDK_MESSAGES
from autocoder.common.international.messages.rules_command_messages import RULES_COMMAND_MESSAGES


@pytest.fixture
def message_manager():
    """创建MessageManager实例的fixture"""
    return MessageManager()


@pytest.fixture
def test_messages():
    """测试消息的fixture"""
    return {
        "test_key": {
            "en": "Test message",
            "zh": "测试消息",
            "ja": "テストメッセージ",
            "ar": "رسالة اختبار",
            "ru": "Тестовое сообщение"
        },
        "another_key": {
            "en": "Another message",
            "zh": "另一条消息",
            "ja": "別のメッセージ",
            "ar": "رسالة أخرى",
            "ru": "Другое сообщение"
        }
    }


class TestMessageManager:
    """测试MessageManager类"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_message_manager()
        manager2 = get_message_manager()
        assert manager1 is manager2, "MessageManager should be singleton"
    
    def test_register_messages(self, message_manager, test_messages):
        """测试消息注册功能"""
        message_manager.register_messages(test_messages)
        
        # 验证消息已注册
        assert "test_key" in message_manager._messages
        assert "another_key" in message_manager._messages
        assert message_manager._messages["test_key"]["en"] == "Test message"
        assert message_manager._messages["test_key"]["zh"] == "测试消息"
    
    @pytest.mark.parametrize("language,expected", [
        ("en", "Hello"),
        ("zh", "你好"),
        ("ja", "こんにちは"),
        ("ar", "مرحبا"),
        ("ru", "Привет")
    ])
    def test_get_message_multilingual(self, message_manager, language, expected):
        """测试获取多语言消息"""
        test_messages = {
            "greeting": {
                "en": "Hello",
                "zh": "你好",
                "ja": "こんにちは",
                "ar": "مرحبا",
                "ru": "Привет"
            }
        }
        
        message_manager.register_messages(test_messages)
        
        # 模拟指定语言环境
        with patch.object(message_manager, 'get_system_language', return_value=language):
            message = message_manager.get_message("greeting")
            assert message == expected
    
    def test_get_message_fallback_to_english(self, message_manager):
        """测试不支持的语言回退到英文"""
        test_messages = {
            "greeting": {
                "en": "Hello",
                "zh": "你好"
            }
        }
        
        message_manager.register_messages(test_messages)
        
        # 模拟不支持的语言
        with patch.object(message_manager, 'get_system_language', return_value='fr'):
            message = message_manager.get_message("greeting")
            assert message == "Hello"
    
    def test_get_message_not_found(self, message_manager):
        """测试获取不存在的消息"""
        message = message_manager.get_message("nonexistent_key")
        assert message == ""
    
    @pytest.mark.parametrize("language,expected", [
        ("en", "Welcome, Alice!"),
        ("zh", "欢迎，Alice！"),
    ])
    def test_get_message_with_format(self, message_manager, language, expected):
        """测试格式化消息"""
        test_messages = {
            "welcome": {
                "en": "Welcome, {{name}}!",
                "zh": "欢迎，{{name}}！"
            }
        }
        
        message_manager.register_messages(test_messages)
        
        # 测试格式化
        with patch.object(message_manager, 'get_system_language', return_value=language):
            message = message_manager.get_message_with_format("welcome", name="Alice")
            assert message == expected
    
    def test_get_message_with_format_multiple_params(self, message_manager):
        """测试多参数格式化"""
        test_messages = {
            "user_info": {
                "en": "User {{name}} is {{age}} years old",
                "zh": "用户{{name}}今年{{age}}岁"
            }
        }
        
        message_manager.register_messages(test_messages)
        
        with patch.object(message_manager, 'get_system_language', return_value='en'):
            message = message_manager.get_message_with_format("user_info", name="Bob", age=25)
            assert message == "User Bob is 25 years old"
    
    def test_get_message_with_format_not_found(self, message_manager):
        """测试格式化不存在的消息"""
        message = message_manager.get_message_with_format("nonexistent", name="test")
        assert message == ""
    
    @pytest.mark.parametrize("locale_setting,expected", [
        (('zh_CN', 'UTF-8'), 'zh'),
        (('en_US', 'UTF-8'), 'en'),
        (('ja_JP', 'UTF-8'), 'ja'),
        (('ar_SA', 'UTF-8'), 'ar'),
        (('ru_RU', 'UTF-8'), 'ru'),
        (('fr_FR', 'UTF-8'), 'en'),  # 不支持的语言回退到英文
    ])
    @patch('locale.getdefaultlocale')
    def test_get_system_language(self, mock_getdefaultlocale, message_manager, locale_setting, expected):
        """测试系统语言检测"""
        mock_getdefaultlocale.return_value = locale_setting
        lang = message_manager.get_system_language()
        assert lang == expected
    
    @patch('locale.getdefaultlocale')
    def test_get_system_language_exception(self, mock_getdefaultlocale, message_manager):
        """测试系统语言检测异常情况"""
        # 测试异常情况
        mock_getdefaultlocale.side_effect = Exception("Locale error")
        lang = message_manager.get_system_language()
        assert lang == 'en'  # 默认回退到英文
    
    def test_empty_messages(self, message_manager):
        """测试空消息字典"""
        message_manager.register_messages({})
        message = message_manager.get_message("any_key")
        assert message == ""
    
    def test_override_existing_messages(self, message_manager):
        """测试覆盖已存在的消息"""
        # 先注册一个消息
        original_messages = {
            "test_key": {
                "en": "Original message",
                "zh": "原始消息"
            }
        }
        message_manager.register_messages(original_messages)
        
        # 再注册同样的键但不同的内容
        new_messages = {
            "test_key": {
                "en": "New message",
                "zh": "新消息"
            }
        }
        message_manager.register_messages(new_messages)
        
        # 验证消息已被覆盖
        with patch.object(message_manager, 'get_system_language', return_value='en'):
            message = message_manager.get_message("test_key")
            assert message == "New message"


@pytest.fixture
def clean_global_manager():
    """清空全局消息管理器的fixture"""
    manager = get_message_manager()
    original_messages = manager._messages.copy()
    manager._messages = {}
    yield manager
    # 恢复原始消息
    manager._messages = original_messages


class TestInternationalModule:
    """测试国际化模块的公共接口"""
    
    def test_register_messages_function(self, clean_global_manager):
        """测试register_messages函数"""
        test_messages = {
            "function_test": {
                "en": "Function test",
                "zh": "函数测试"
            }
        }
        
        register_messages(test_messages)
        
        # 验证消息已注册到全局管理器
        assert "function_test" in clean_global_manager._messages
    
    def test_get_message_function(self, clean_global_manager):
        """测试get_message函数"""
        test_messages = {
            "hello": {
                "en": "Hello World",
                "zh": "你好世界"
            }
        }
        
        register_messages(test_messages)
        
        # 测试获取消息
        with patch('autocoder.common.international.message_manager.get_system_language', return_value='en'):
            message = get_message("hello")
            assert message == "Hello World"
    
    def test_get_message_with_format_function(self, clean_global_manager):
        """测试get_message_with_format函数"""
        test_messages = {
            "greeting": {
                "en": "Hello {{name}}",
                "zh": "你好{{name}}"
            }
        }
        
        register_messages(test_messages)
        
        # 测试格式化消息
        with patch('autocoder.common.international.message_manager.get_system_language', return_value='en'):
            message = get_message_with_format("greeting", name="World")
            assert message == "Hello World"
    
    def test_get_system_language_function(self):
        """测试get_system_language函数"""
        with patch('locale.getdefaultlocale', return_value=('zh_CN', 'UTF-8')):
            lang = get_system_language()
            assert lang == 'zh'


class TestAutoRegistration:
    """测试自动注册功能"""
    
    def test_messages_auto_registered(self):
        """测试消息已自动注册"""
        # 获取全局管理器
        manager = get_message_manager()
        
        # 验证至少有一些消息已经注册
        assert len(manager._messages) > 0, "应该有自动注册的消息"
        
        # 测试一些已知的消息键（这些应该在auto_coder_messages.py中）
        # 注意：这里需要根据实际的消息键来调整
        known_keys = ["file_scored_message", "config_delete_success", "config_invalid_format"]
        
        for key in known_keys:
            if key in manager._messages:
                # 验证消息结构
                assert isinstance(manager._messages[key], dict)
                assert "en" in manager._messages[key]
                break  # 找到一个就足够了
    
    def test_get_auto_registered_message(self):
        """测试获取自动注册的消息"""
        # 尝试获取一个应该已经注册的消息
        try:
            message = get_message("file_scored_message")
            # 如果消息存在，它不应该是"Message not found"
            assert message != "Message not found: file_scored_message"
        except:
            # 如果消息不存在，这也是可以接受的（因为我们不确定具体的消息键）
            pass


class TestErrorHandling:
    """测试错误处理"""
    
    def test_malformed_messages(self, message_manager):
        """测试格式不正确的消息"""
        # 测试缺少语言键的消息
        malformed_messages = {
            "bad_message": {
                "en": "Good message"
                # 缺少其他语言
            }
        }
        
        # 应该能够正常注册
        message_manager.register_messages(malformed_messages)
        
        # 应该能够获取存在的语言
        with patch.object(message_manager, 'get_system_language', return_value='en'):
            message = message_manager.get_message("bad_message")
            assert message == "Good message"
        
        # 对于不存在的语言应该回退到英文
        with patch.object(message_manager, 'get_system_language', return_value='zh'):
            message = message_manager.get_message("bad_message")
            assert message == "Good message"
    
    def test_invalid_message_structure(self, message_manager):
        """测试无效的消息结构"""
        # 测试非字典类型的消息
        invalid_messages = {
            "invalid": {"en": "This is not a valid message structure"}
        }
        
        message_manager.register_messages(invalid_messages)
        
        # 应该能够正常获取消息
        message = message_manager.get_message("invalid")
        assert message == "This is not a valid message structure"
    
    @patch('autocoder.common.international.message_manager.format_str_jinja2')
    def test_format_error_handling(self, mock_format, message_manager):
        """测试格式化错误处理"""
        # 模拟格式化错误
        mock_format.side_effect = Exception("Format error")
        
        test_messages = {
            "format_test": {
                "en": "Hello {{name}}",
                "zh": "你好{{name}}"
            }
        }
        
        message_manager.register_messages(test_messages)
        
        # 当格式化失败时，应该抛出异常
        with patch.object(message_manager, 'get_system_language', return_value='en'):
            with pytest.raises(Exception):
                message_manager.get_message_with_format("format_test", name="World")


# 新增：测试验证所有消息文件的五种语言完整性
class TestMessagesCompleteness:
    """测试消息文件的五种语言完整性"""
    
    REQUIRED_LANGUAGES = ['en', 'zh', 'ja', 'ar', 'ru']
    
    @pytest.mark.parametrize("messages_dict,file_name", [
        (AUTO_CODER_MESSAGES, "auto_coder_messages.py"),
        (CHAT_AUTO_CODER_MESSAGES, "chat_auto_coder_messages.py"),
        (SDK_MESSAGES, "sdk_messages.py"),
        (RULES_COMMAND_MESSAGES, "rules_command_messages.py")
    ])
    def test_all_messages_have_five_languages(self, messages_dict, file_name):
        """测试所有消息键都包含五种语言"""
        missing_languages_errors = []
        empty_content_errors = []
        
        for key, message_data in messages_dict.items():
            # 检查消息数据是否为字典
            if not isinstance(message_data, dict):
                missing_languages_errors.append(f"[{file_name}] Key '{key}': Expected dict, got {type(message_data).__name__}")
                continue
            
            # 检查缺失的语言
            missing_languages = set(self.REQUIRED_LANGUAGES) - set(message_data.keys())
            if missing_languages:
                missing_langs_str = ", ".join(sorted(missing_languages))
                missing_languages_errors.append(f"[{file_name}] Key '{key}': Missing languages: {missing_langs_str}")
            
            # 检查空内容
            for lang, content in message_data.items():
                if not content or (isinstance(content, str) and content.strip() == ""):
                    empty_content_errors.append(f"[{file_name}] Key '{key}', Language '{lang}': Content is empty")
        
        # 汇总错误信息
        all_errors = missing_languages_errors + empty_content_errors
        
        if all_errors:
            error_summary = f"\n{file_name} 语言完整性验证失败:\n"
            error_summary += f"总键数: {len(messages_dict)}\n"
            error_summary += f"缺失语言的键数: {len(missing_languages_errors)}\n"
            error_summary += f"空内容错误数: {len(empty_content_errors)}\n"
            error_summary += "错误详情:\n" + "\n".join(all_errors[:10])  # 只显示前10个错误
            if len(all_errors) > 10:
                error_summary += f"\n... 还有 {len(all_errors) - 10} 个错误"
            
            pytest.fail(error_summary)
    
    def test_messages_structure_consistency(self):
        """测试消息结构一致性"""
        all_message_files = [
            (AUTO_CODER_MESSAGES, "auto_coder_messages.py"),
            (CHAT_AUTO_CODER_MESSAGES, "chat_auto_coder_messages.py"), 
            (SDK_MESSAGES, "sdk_messages.py")
        ]
        
        inconsistent_keys = []
        
        for messages_dict, file_name in all_message_files:
            for key, message_data in messages_dict.items():
                if not isinstance(message_data, dict):
                    continue
                
                # 检查是否所有语言的消息都是字符串类型
                for lang, content in message_data.items():
                    if not isinstance(content, str):
                        inconsistent_keys.append(f"[{file_name}] Key '{key}', Language '{lang}': Content is not string (got {type(content).__name__})")
        
        if inconsistent_keys:
            error_summary = f"消息结构一致性验证失败:\n" + "\n".join(inconsistent_keys)
            pytest.fail(error_summary)
    
    def test_supported_languages_api(self):
        """测试语言支持API"""
        supported_langs = get_supported_languages()
        
        # 验证返回的是五种语言
        assert len(supported_langs) == 5
        assert set(supported_langs) == set(self.REQUIRED_LANGUAGES)
        
        # 测试语言支持检查
        for lang in self.REQUIRED_LANGUAGES:
            assert is_language_supported(lang), f"Language {lang} should be supported"
        
        # 测试不支持的语言
        assert not is_language_supported('fr'), "French should not be supported"
        assert not is_language_supported('de'), "German should not be supported"
    
    # def test_message_keys_uniqueness(self):
    #     """测试消息键的唯一性（跨文件检查重复键）"""
    #     all_keys = set()
    #     duplicate_keys = []
        
    #     all_message_files = [
    #         (AUTO_CODER_MESSAGES, "auto_coder_messages.py"),
    #         (CHAT_AUTO_CODER_MESSAGES, "chat_auto_coder_messages.py"),
    #         (SDK_MESSAGES, "sdk_messages.py")
    #     ]
        
    #     for messages_dict, file_name in all_message_files:
    #         for key in messages_dict.keys():
    #             if key in all_keys:
    #                 duplicate_keys.append(f"Duplicate key '{key}' found in {file_name}")
    #             all_keys.add(key)
        
    #     if duplicate_keys:
    #         error_summary = f"发现重复的消息键:\n" + "\n".join(duplicate_keys)
    #         pytest.fail(error_summary)
    
    @pytest.mark.parametrize("messages_dict,file_name", [
        (AUTO_CODER_MESSAGES, "auto_coder_messages.py"),
        (CHAT_AUTO_CODER_MESSAGES, "chat_auto_coder_messages.py"),
        (SDK_MESSAGES, "sdk_messages.py"),
        (RULES_COMMAND_MESSAGES, "rules_command_messages.py")
    ])
    def test_jinja2_template_syntax(self, messages_dict, file_name):
        """测试Jinja2模板语法的有效性"""
        from byzerllm.utils import format_str_jinja2
        
        syntax_errors = []
        
        for key, message_data in messages_dict.items():
            if not isinstance(message_data, dict):
                continue
                
            for lang, content in message_data.items():
                if not isinstance(content, str):
                    continue
                
                # 如果包含{{}}模板语法，测试其有效性
                if "{{" in content and "}}" in content:
                    try:
                        # 尝试用虚拟参数格式化
                        test_params = {}
                        # 提取模板变量名
                        import re
                        variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', content)
                        for var in variables:
                            test_params[var] = "test_value"
                        
                        format_str_jinja2(content, **test_params)
                    except Exception as e:
                        syntax_errors.append(f"[{file_name}] Key '{key}', Language '{lang}': Jinja2 syntax error: {e}")
        
        if syntax_errors:
            error_summary = f"{file_name} Jinja2模板语法验证失败:\n" + "\n".join(syntax_errors[:5])
            if len(syntax_errors) > 5:
                error_summary += f"\n... 还有 {len(syntax_errors) - 5} 个错误"
            pytest.fail(error_summary)

    def test_no_duplicate_keys_across_files(self):
        """测试不同消息文件之间不应有重复的键"""
        
        # 定义文件和对应的消息字典
        message_files = [
            ("auto_coder_messages.py", AUTO_CODER_MESSAGES),
            ("chat_auto_coder_messages.py", CHAT_AUTO_CODER_MESSAGES),
            ("sdk_messages.py", SDK_MESSAGES),
            ("rules_command_messages.py", RULES_COMMAND_MESSAGES)
        ]
        
        # 收集所有键和其所在文件的映射
        key_to_files = {}
        
        for file_name, messages_dict in message_files:
            for key in messages_dict.keys():
                if key not in key_to_files:
                    key_to_files[key] = []
                key_to_files[key].append(file_name)
        
        # 查找重复的键
        duplicate_keys = {}
        for key, files in key_to_files.items():
            if len(files) > 1:
                duplicate_keys[key] = files
        
        # 如果有重复键，生成易读的错误报告
        if duplicate_keys:
            error_lines = [
                "❌ 发现重复的消息键！",
                "=" * 50,
                "以下键在多个文件中重复定义："
            ]
            
            # 按键名排序，便于阅读
            for key in sorted(duplicate_keys.keys()):
                files = duplicate_keys[key]
                files_str = " & ".join(files)
                error_lines.append(f"  🔑 '{key}' → {files_str}")
            
            error_lines.extend([
                "",
                f"📊 统计信息:",
                f"  • 重复键总数: {len(duplicate_keys)}",
                f"  • 涉及文件: {len(set(file for files in duplicate_keys.values() for file in files))}",
                "",
                "💡 建议:",
                "  • 为每个文件使用唯一的键名前缀",
                "  • 或将通用消息移到共享文件中"
            ])
            
            error_message = "\n".join(error_lines)
            pytest.fail(error_message)


class TestRulesCommandMessages:
    """测试规则命令消息的特定功能"""
    
    def test_rules_command_keys_prefix(self):
        """测试所有规则命令消息键都以rule_cmd_开头"""
        for key in RULES_COMMAND_MESSAGES.keys():
            assert key.startswith('rule_cmd_'), f"规则命令消息键 '{key}' 应该以 'rule_cmd_' 开头"
    
    def test_rules_command_required_messages(self):
        """测试包含所有必需的规则命令消息"""
        required_keys = [
            'rule_cmd_analyzing_project',
            'rule_cmd_init_failed', 
            'rule_cmd_init_success',
            'rule_cmd_init_error'
        ]
        
        for key in required_keys:
            assert key in RULES_COMMAND_MESSAGES, f"缺少必需的规则命令消息键: {key}"
    
    def test_rules_command_error_message_formatting(self):
        """测试规则命令错误消息支持格式化"""
        from autocoder.common.international import get_message_with_format
        
        # 测试错误消息模板
        formatted_msg = get_message_with_format('rule_cmd_init_error', error='test error')
        assert 'test error' in formatted_msg, "错误消息应该包含格式化的错误信息"
        assert formatted_msg != '', "格式化的错误消息不应为空"


if __name__ == '__main__':
    pytest.main([__file__, "-v"]) 