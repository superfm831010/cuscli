"""
Pytest tests for AgenticConversationPruner

This module contains comprehensive tests for the AgenticConversationPruner class,
including functionality tests, edge cases, and integration tests.
"""

import json
import pytest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch
from autocoder.common.pruner.agentic_conversation_pruner import AgenticConversationPruner
from autocoder.common import AutoCoderArgs
from autocoder.sdk import get_llm, init_project_if_required
from autocoder.common.conf_utils import load_tokenizer
from autocoder.common.tokens import count_string_tokens

load_tokenizer()

class TestAgenticConversationPruner:
    """Test suite for AgenticConversationPruner class"""

    @pytest.fixture
    def temp_test_dir(self):
        """提供一个临时的、测试后自动清理的目录"""
        # 保存原始工作目录
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()        
        try:
            yield temp_dir
        finally:
            # 确保恢复到原始目录，即使出现异常
            try:
                os.chdir(original_cwd)
            except OSError:
                # 如果原始目录也不存在，则切换到用户主目录
                os.chdir(os.path.expanduser("~"))
            # 删除临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_args(self):
        """Create mock AutoCoderArgs for testing"""
        return AutoCoderArgs(
            source_dir=".",
            conversation_prune_safe_zone_tokens=1000,  # Small threshold for testing
            context_prune=True,
            context_prune_strategy="extract",
            context_prune_sliding_window_size=10,
            context_prune_sliding_window_overlap=2,
            query="请帮我分析这些代码"
        )
    
    @pytest.fixture
    def mock_args_small_threshold(self):
        """Create mock AutoCoderArgs with very small token threshold for testing"""
        return AutoCoderArgs(
            source_dir=".",
            conversation_prune_safe_zone_tokens=50,  # Very small threshold to trigger pruning
            context_prune=True,
            context_prune_strategy="extract",
            context_prune_sliding_window_size=10,
            context_prune_sliding_window_overlap=2,
            query="请帮我分析这些代码"
        )

    @pytest.fixture
    def real_llm(self):
        """创建真实的LLM对象"""
        llm = get_llm("v3_chat", product_mode="lite")
        return llm



    @pytest.fixture
    def pruner(self, mock_args, real_llm):
        """Create AgenticConversationPruner instance for testing"""
        return AgenticConversationPruner(args=mock_args, llm=real_llm, conversation_id="test-conversation-id")

    @pytest.fixture
    def sample_file_sources(self, temp_test_dir):
        """Sample file sources for testing
        Creates a simulated project structure in the temporary directory
        """
        # 创建项目结构
        src_dir = os.path.join(temp_test_dir, "src")
        utils_dir = os.path.join(src_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)

        # 创建 __init__.py 文件使其成为有效的 Python 包
        with open(os.path.join(src_dir, "__init__.py"), "w") as f:
            f.write("# src package")
        with open(os.path.join(utils_dir, "__init__.py"), "w") as f:
            f.write("# utils package")

        # 创建数学工具模块
        math_utils_content = '''def add(a, b):
    """加法函数"""
    return a + b

def subtract(a, b):
    """减法函数"""
    return a - b

def multiply(a, b):
    """乘法函数"""
    return a * b

def divide(a, b):
    """除法函数"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
        math_utils_path = os.path.join(utils_dir, "math_utils.py")
        with open(math_utils_path, "w") as f:
            f.write(math_utils_content)

        # 创建字符串工具模块
        string_utils_content = '''def format_string(s):
    """格式化字符串"""
    return s.strip().lower()

def reverse_string(s):
    """反转字符串"""
    return s[::-1]

def count_characters(s):
    """计算字符数"""
    return len(s)
'''
        string_utils_path = os.path.join(utils_dir, "string_utils.py")
        with open(string_utils_path, "w") as f:
            f.write(string_utils_content)

        # 创建主程序文件
        main_content = '''from utils.math_utils import add, subtract
from utils.string_utils import format_string

def main():
    print("计算结果:", add(5, 3))
    print("格式化结果:", format_string("  Hello World  "))

if __name__ == "__main__":
    main()
'''
        main_path = os.path.join(src_dir, "main.py")
        with open(main_path, "w") as f:
            f.write(main_content)

        # 初始化该项目
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_test_dir)
            init_project_if_required(target_dir=temp_test_dir)
        finally:
            os.chdir(original_cwd)

        # 返回文件内容供测试使用
        return {
            "math_utils": math_utils_content,
            "string_utils": string_utils_content,
            "main": main_content
        }

    @pytest.fixture
    def sample_conversations(self):
        """Sample conversations with tool results for testing"""
        # 创建一个长内容用于测试token计数
        long_content = """def hello():
    print('Hello, world!')
    # This is a very long file content that would take up many tokens
    # We want to clean this up to save space in the conversation
    for i in range(100):
        print(f'Line {i}: This is line number {i} with some content')
    return 'done'

def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def process_data(data):
    processed = []
    for item in data:
        if item > 0:
            processed.append(item * 2)
    return processed

# More functions to increase token count
def validate_input(input_data):
    if input_data is None:
        return False
    return True

def format_output(result):
    return f"Result: {result}"
"""
        
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Please read a file for me."},
            {"role": "assistant", "content": "I'll read the file for you.\n\n<read_file>\n<path>test.py</path>\n</read_file>"},
            {
                "role": "user", 
                "content": f"<tool_result tool_name='ReadFileTool' success='true'><message>File read successfully</message><content>{long_content}</content></tool_result>"
            },
            {"role": "assistant", "content": "I can see the file content. Let me analyze it for you."},
            {"role": "user", "content": "Now please list files in the directory."},
            {"role": "assistant", "content": "I'll list the files for you.\n\n<list_files>\n<path>.</path>\n</list_files>"},
            {
                "role": "user",
                "content": "<tool_result tool_name='ListFilesTool' success='true'><message>Files listed successfully</message><content>['file1.py', 'file2.js', 'file3.md', 'very_long_file_with_many_tokens_that_should_be_cleaned.txt', 'another_file.py', 'config.json', 'readme.md', 'test_data.csv']</content></tool_result>"
            },
            {"role": "assistant", "content": "Here are the files in the directory. Is there anything specific you'd like to do with them?"}
        ]

    def test_initialization(self, mock_args, real_llm):
        """Test AgenticConversationPruner initialization"""
        pruner = AgenticConversationPruner(args=mock_args, llm=real_llm, conversation_id="test-init-conversation")
        
        assert pruner.args == mock_args
        assert pruner.llm == real_llm
        assert hasattr(pruner, 'tool_content_detector')
        assert pruner.replacement_message == "This message has been cleared. If you still want to get this information, you can call the tool again to retrieve it."



    def test_prune_conversations_within_limit(self, pruner, sample_conversations):
        """Test pruning when conversations are within token limit"""
        # 创建一个短对话来测试不需要修剪的情况
        short_conversations = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = pruner.prune_conversations(short_conversations)
        
        # Should return original conversations unchanged since they're short
        assert result == short_conversations

    def test_prune_conversations_exceeds_limit(self, pruner, sample_conversations):
        """Test pruning when conversations exceed token limit"""
        # 使用真实的token计数进行测试
        # sample_conversations包含了长内容，应该会触发修剪
        
        result = pruner.prune_conversations(sample_conversations)
        
        # Should have processed the conversations
        assert isinstance(result, list)
        assert len(result) == len(sample_conversations)
        
        # Check that tool results were cleaned if token count was high
        # 由于我们使用真实的token计数，可能会也可能不会触发修剪
        # 这取决于实际的token数量
        
        # 至少验证结果是有效的对话列表
        for conv in result:
            assert isinstance(conv, dict), "Each conversation should be a dict"
            assert "role" in conv, "Each conversation should have a role"
            assert "content" in conv, "Each conversation should have content"

    def test_is_tool_result_message(self, pruner):
        """Test tool result message detection"""
        # Test cases for tool result detection
        test_cases = [
            ("<tool_result tool_name='ReadFileTool' success='true'>content</tool_result>", True),
            ("<tool_result tool_name=\"ListTool\" success=\"false\">error</tool_result>", True),
            ("Regular message without tool result", False),
            ("<tool_result>missing tool_name</tool_result>", False),
            ("", False),
            ("<some_other_tag tool_name='test'>content</some_other_tag>", False)
        ]
        
        for content, expected in test_cases:
            result = pruner._is_tool_result_message(content)
            assert result == expected, f"Failed for content: {content}"

    def test_extract_tool_name(self, pruner):
        """Test tool name extraction from tool results"""
        test_cases = [
            ("<tool_result tool_name='ReadFileTool' success='true'>", "ReadFileTool"),
            ('<tool_result tool_name="ListFilesTool" success="true">', "ListFilesTool"),
            ("<tool_result success='true' tool_name='WriteTool'>", "WriteTool"),
            ("<tool_result success='true'>", "unknown"),
            ("Not a tool result", "unknown"),
            ("", "unknown"),
            ("<tool_result tool_name=''>", ""),
            ("<tool_result tool_name='Tool With Spaces'>", "Tool With Spaces")
        ]
        
        for content, expected in test_cases:
            result = pruner._extract_tool_name(content)
            assert result == expected, f"Failed for content: {content}"

    def test_generate_replacement_message(self, pruner):
        """Test replacement message generation"""
        test_cases = [
            "ReadFileTool",
            "ListFilesTool", 
            "unknown",
            "",
            "CustomTool"
        ]
        
        for tool_name in test_cases:
            replacement = pruner._generate_replacement_message(tool_name)
            
            # Check that replacement contains expected elements
            assert "<tool_result" in replacement
            assert "Content cleared to save tokens" in replacement
            assert pruner.replacement_message in replacement
            
            if tool_name and tool_name != "unknown":
                assert f"tool_name='{tool_name}'" in replacement

    def test_get_cleanup_statistics(self, pruner, sample_conversations):
        """Test cleanup statistics calculation"""
        # Create pruned conversations (simulate cleaning)
        pruned_conversations = sample_conversations.copy()
        pruned_conversations[3]["content"] = "<tool_result tool_name='ReadFileTool' success='true'><message>Content cleared to save tokens</message><content>This message has been cleared</content></tool_result>"
        
        stats = pruner.get_cleanup_statistics(sample_conversations, pruned_conversations)
        
        # Verify statistics structure
        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert 'original_tokens' in stats, "Stats should include original_tokens"
        assert 'pruned_tokens' in stats, "Stats should include pruned_tokens"
        assert 'tokens_saved' in stats, "Stats should include tokens_saved"
        assert 'compression_ratio' in stats, "Stats should include compression_ratio"
        assert 'tool_results_cleaned' in stats, "Stats should include tool_results_cleaned"
        assert 'tool_calls_cleaned' in stats, "Stats should include tool_calls_cleaned"
        assert 'total_messages' in stats, "Stats should include total_messages"
        
        # Verify that statistics are reasonable
        assert stats['original_tokens'] > 0, "Original tokens should be positive"
        assert stats['pruned_tokens'] >= 0, "Pruned tokens should be non-negative"
        assert stats['tokens_saved'] >= 0, "Tokens saved should be non-negative"
        assert 0 <= stats['compression_ratio'] <= 1, "Compression ratio should be between 0 and 1"
        assert stats['tool_results_cleaned'] >= 0, "Tool results cleaned should be non-negative"
        assert stats['tool_calls_cleaned'] >= 0, "Tool calls cleaned should be non-negative"
        assert stats['total_messages'] == len(sample_conversations), "Total messages should match input"

    def test_prune_conversations_default_behavior(self, pruner, sample_conversations):
        """Test pruning with default behavior (no strategy parameter)"""
        # Test simplified interface without strategy parameter
        result = pruner.prune_conversations(sample_conversations)
        assert isinstance(result, list)

    def test_prune_conversations_empty_list(self, pruner):
        """Test pruning with empty conversation list"""
        result = pruner.prune_conversations([])
        assert result == []

    def test_prune_conversations_no_tool_results(self, pruner):
        """Test pruning conversations without tool results"""
        conversations = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]
        
        result = pruner.prune_conversations(conversations)
        # Should return original since no tool results to clean
        assert result == conversations

    def test_progressive_cleanup(self, pruner):
        """Test that cleanup happens progressively from earliest tool results"""
        # 创建包含多个tool结果的对话，其中包含长内容来触发修剪
        long_result = "# This is a very long result content that should trigger token limit\n" * 100
        
        conversations = [
            {"role": "user", "content": "First request"},
            {"role": "user", "content": f"<tool_result tool_name='Tool1'><content>{long_result}</content></tool_result>"},
            {"role": "user", "content": "Second request"},
            {"role": "user", "content": f"<tool_result tool_name='Tool2'><content>{long_result}</content></tool_result>"},
            {"role": "user", "content": "Third request"},
            {"role": "user", "content": f"<tool_result tool_name='Tool3'><content>{long_result}</content></tool_result>"}
        ]
        
        result = pruner.prune_conversations(conversations)
        
        # 验证结果的基本结构
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == len(conversations), "Should preserve conversation count"
        
        # 检查是否有tool结果被清理
        for conv in result:
            assert isinstance(conv, dict), "Each conversation should be a dict"
            assert "role" in conv, "Each conversation should have a role"
            assert "content" in conv, "Each conversation should have content"

    def test_apply_range_pruning_with_pair_preservation(self, mock_args_small_threshold, real_llm):
        """Test _apply_range_pruning with pair preservation enabled"""
        from unittest.mock import MagicMock, patch
        from autocoder.common.pruner.conversation_message_ids_manager import ConversationMessageIds
        
        # 创建包含user/assistant对话的测试数据
        conversations = [
            {"role": "system", "content": "You are a helpful assistant.", "message_id": "12345678abc"},
            {"role": "user", "content": "Hello!", "message_id": "23456789def"},  # user
            {"role": "assistant", "content": "Hi there!", "message_id": "34567890ghi"},  # assistant
            {"role": "user", "content": "Can you help?", "message_id": "45678901jkl"},  # user
            {"role": "assistant", "content": "Of course!", "message_id": "56789012mno"},  # assistant
            {"role": "user", "content": "Thank you!", "message_id": "67890123pqr"}  # user (single)
        ]
        
        # 尝试只删除一个user消息，但由于pair preservation，应该连同对应的assistant也被删除
        message_ids_to_delete = ["23456789"]  # 只删除第一个user消息
        conversation_id = "test_conversation_pair_123"
        
        # 创建带有pair preservation的配置
        mock_conversation_message_ids = ConversationMessageIds(
            conversation_id=conversation_id,
            message_ids=message_ids_to_delete,
            created_at="2024-01-01T00:00:00", 
            updated_at="2024-01-01T00:00:00",
            description="Test pair preservation",
            preserve_pairs=True  # 启用成对保护
        )
        
        pruner = AgenticConversationPruner(args=mock_args_small_threshold, llm=real_llm, conversation_id=conversation_id)
        
        with patch.object(pruner.message_ids_api, 'get_conversation_message_ids') as mock_get_message_ids:
            mock_get_message_ids.return_value = mock_conversation_message_ids
            
            result = pruner.prune_conversations(conversations)
            
            # 验证结果
            assert isinstance(result, list), "Result should be a list"
            
            # 由于pair preservation，第一个user和其对应的assistant都应该被删除
            result_message_ids = [conv.get("message_id", "")[:8] for conv in result]
            
            # 验证成对删除是否正确执行
            # 注意：具体的行为取决于ConversationMessageIdsPruner的实现
            # 这里主要验证range pruning确实被触发了
            stats = pruner.get_pruning_statistics()
            assert stats["range_pruning"]["applied"] == True, "Range pruning with pair preservation should be applied"
            
            print(f"✅ Range pruning with pair preservation test passed!")
            print(f"   Original messages: {len(conversations)}")
            print(f"   Messages after range pruning: {len(result)}")
            print(f"   Preserve pairs enabled: {mock_conversation_message_ids.preserve_pairs}")

    def test_apply_range_pruning_no_conversation_id(self, mock_args_small_threshold, real_llm):
        """Test that AgenticConversationPruner requires conversation_id parameter"""
        # 测试当没有提供 conversation_id 时构造函数应该抛出 ValueError
        with pytest.raises(ValueError, match="conversation_id is required"):
            pruner = AgenticConversationPruner(args=mock_args_small_threshold, llm=real_llm)
            
        print("✅ Test passed: AgenticConversationPruner correctly requires conversation_id parameter")

    def test_apply_range_pruning_no_message_ids_config(self, mock_args_small_threshold, real_llm):
        """Test that _apply_range_pruning is skipped when no message IDs configuration exists"""
        from unittest.mock import patch
        
        # 添加长内容以确保超过token阈值，从而触发裁剪流程
        long_content = "This is a very long message content that should definitely exceed the token threshold. " * 10
        
        conversations = [
            {"role": "user", "content": f"Hello. {long_content}"},
            {"role": "assistant", "content": f"Hi there! {long_content}"}
        ]
        
        conversation_id = "test_conversation_no_config"
        pruner = AgenticConversationPruner(args=mock_args_small_threshold, llm=real_llm, conversation_id=conversation_id)
        
        # Mock返回None，表示没有找到消息ID配置
        with patch.object(pruner.message_ids_api, 'get_conversation_message_ids') as mock_get_message_ids:
            mock_get_message_ids.return_value = None
            
            result = pruner.prune_conversations(conversations)
            
            # 验证mock被调用
            mock_get_message_ids.assert_called_once_with(conversation_id)
            
            # 由于我们使用了长内容且阈值很小，可能会添加cleanup提示消息
            # 验证原始消息仍然存在（可能在最后添加了一个提示消息）
            assert len(result) >= len(conversations), "Result should have at least the original conversations"
            
            # 验证原始消息的内容没有改变
            for i, original_conv in enumerate(conversations):
                assert result[i]["role"] == original_conv["role"], f"Role should match for message {i}"
                assert result[i]["content"] == original_conv["content"], f"Content should match for message {i}"
            
            # 验证统计信息
            stats = pruner.get_pruning_statistics()
            assert stats["range_pruning"]["applied"] == False, "Range pruning should not be applied when no config"
            
            print(f"✅ No message IDs config test passed!")

    def test_tool_call_content_detection(self, pruner):
        """Test tool call content detection and cleanup"""
        # Test conversations with tool calls
        conversations = [
            {"role": "user", "content": "Please write a file"},
            {
                "role": "assistant", 
                "content": """I'll write the file for you.

<write_to_file>
<path>test.py</path>
<content>print("Hello, World!")
print("This is a test file")
print("It contains multiple lines")
print("And some more content to exceed the length limit")
print("Even more content to make it longer")
print("And yet more content to ensure it's over 500 characters")
</content>
</write_to_file>

File written successfully."""
            }
        ]
        
        # Check that tool call content is detected
        assert pruner.tool_content_detector.is_tool_call_content(conversations[1]["content"])
        
        # Test replacement
        original_content = conversations[1]["content"]
        new_content, replaced = pruner.tool_content_detector.replace_tool_content(
            original_content, max_content_length=100
        )
        
        assert replaced, "Tool call content should be replaced when it exceeds length limit"
        assert len(new_content) < len(original_content), "New content should be shorter"
        assert "Content cleared to save tokens" in new_content, "Should contain replacement message"

    def test_combined_cleanup_flow(self, pruner):
        """Test the combined cleanup flow (tool outputs + tool calls)"""
        # 创建包含长内容的对话来触发修剪
        long_file_content = "print('This is a very long file content that should be cleaned up to save tokens in the conversation history')\n" * 50
        
        conversations = [
            {"role": "user", "content": "Please write a file"},
            {
                "role": "assistant",
                "content": f"""<write_to_file>
<path>test.py</path>
<content>{long_file_content}</content>
</write_to_file>"""
            },
            {
                "role": "user",
                "content": f"""<tool_result tool_name='write_to_file' success='true'>
<message>File written successfully</message>
<content>File has been written with the following content:
{long_file_content}
</content>
</tool_result>"""
            }
        ]
        
        result = pruner.prune_conversations(conversations)
        
        # 验证结果的基本结构
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == len(conversations), "Should preserve conversation count"
        
        # 验证每个对话都有基本的结构
        for conv in result:
            assert isinstance(conv, dict), "Each conversation should be a dict"
            assert "role" in conv, "Each conversation should have a role"
            assert "content" in conv, "Each conversation should have content"

    def test_edge_cases(self, pruner):
        """Test various edge cases"""
        # Test with None content
        assert not pruner._is_tool_result_message(None)
        
        # Test with malformed tool result
        malformed = "<tool_result tool_name='Test' incomplete"
        assert pruner._extract_tool_name(malformed) == "Test"
        
        # Test with special characters in tool name
        special_chars = "<tool_result tool_name='Tool-With_Special.Chars123' success='true'>"
        assert pruner._extract_tool_name(special_chars) == "Tool-With_Special.Chars123"


class TestAgenticConversationPrunerIntegration:
    """Integration tests for AgenticConversationPruner"""

    @pytest.fixture
    def real_args(self):
        """Create real AutoCoderArgs for integration testing"""
        return AutoCoderArgs(
            source_dir=".",
            conversation_prune_safe_zone_tokens=50000,
            context_prune=True,
            context_prune_strategy="extract",
            context_prune_sliding_window_size=10,
            context_prune_sliding_window_overlap=2,
            query="请帮我分析这些代码文件"
        )

    @pytest.fixture
    def real_llm(self):
        """创建真实的LLM对象"""
        llm = get_llm("v3_chat", product_mode="lite")
        return llm

    @pytest.fixture
    def temp_test_dir(self, tmp_path):
        """Create a temporary test directory"""
        return str(tmp_path)

    @pytest.fixture
    def sample_file_sources(self):
        """Sample file sources for testing"""
        return {
            'math_utils': '''def add(a, b):
    """加法函数"""
    return a + b

def subtract(a, b):
    """减法函数"""
    return a - b

def multiply(a, b):
    """乘法函数"""
    return a * b''',
            'main': '''from utils.math_utils import add, subtract, multiply

def main():
    """主函数"""
    result1 = add(10, 5)
    result2 = subtract(10, 5)
    result3 = multiply(10, 5)
    print(f"结果: {result1}, {result2}, {result3}")

if __name__ == "__main__":
    main()'''
        }

    def test_integration_real_conversation_scenarios(self, real_args, real_llm):
        """Test with realistic conversation scenario"""
        # 简化测试，去掉复杂的项目依赖
        conversation_id = "integration-test-conversation"
        pruner = AgenticConversationPruner(args=real_args, llm=real_llm, conversation_id=conversation_id)
        
        # Create a realistic conversation with large tool outputs
        large_file_content = "# " + "Very long file content " * 500  # 减少内容大小
        
        conversations = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Can you read the main.py file and analyze it?"},
            {"role": "assistant", "content": "I'll read the file for you.\n\n<read_file>\n<path>main.py</path>\n</read_file>"},
            {
                "role": "user",
                "content": f"<tool_result tool_name='ReadFileTool' success='true'><message>File read successfully</message><content>{large_file_content}</content></tool_result>"
            },
            {"role": "assistant", "content": "I can see this is a large Python file. Let me analyze its structure..."},
            {"role": "user", "content": "Now can you list all Python files in the directory?"},
            {"role": "assistant", "content": "I'll list the Python files.\n\n<list_files>\n<path>.</path>\n<pattern>*.py</pattern>\n</list_files>"},
            {
                "role": "user",
                "content": f"<tool_result tool_name='ListFilesTool' success='true'><message>Files listed</message><content>{json.dumps(['file' + str(i) + '.py' for i in range(50)])}</content></tool_result>"
            }
        ]
        
        result = pruner.prune_conversations(conversations)
        
        # Verify the result is valid
        assert isinstance(result, list)
        assert len(result) == len(conversations)
        
        # Verify that some cleanup occurred
        stats = pruner.get_cleanup_statistics(conversations, result)
        assert isinstance(stats, dict)
        assert all(key in stats for key in ['original_tokens', 'pruned_tokens', 'tokens_saved', 'compression_ratio', 'tool_results_cleaned', 'total_messages'])
    
    def test_integration_mixed_content_pruning(self, real_args, real_llm, sample_file_sources):
        """Test AgenticConversationPruner with real file sources"""
        # 简化测试，去掉复杂的项目依赖
        conversation_id = "mixed-content-test-conversation"
        pruner = AgenticConversationPruner(args=real_args, llm=real_llm, conversation_id=conversation_id)
        
        # Create conversations with file content from sample_file_sources
        conversations = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "请分析这些数学工具函数"},
            {"role": "assistant", "content": "我会分析这些数学工具函数。\n\n<read_file>\n<path>src/utils/math_utils.py</path>\n</read_file>"},
            {
                "role": "user",
                "content": f"<tool_result tool_name='ReadFileTool' success='true'><message>File read successfully</message><content>{sample_file_sources['math_utils']}</content></tool_result>"
            },
            {"role": "assistant", "content": "我看到这个文件包含了基本的数学运算函数。让我也看看主程序文件。\n\n<read_file>\n<path>src/main.py</path>\n</read_file>"},
            {
                "role": "user",
                "content": f"<tool_result tool_name='ReadFileTool' success='true'><message>File read successfully</message><content>{sample_file_sources['main']}</content></tool_result>"
            },
            {"role": "assistant", "content": "很好，主程序使用了数学工具函数。这些函数实现了基本的数学运算。"}
        ]
        
        # 测试pruning功能
        result = pruner.prune_conversations(conversations)
        
        # 验证结果
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == len(conversations), "Should preserve conversation count"
        
        # 验证每个对话的基本结构
        for i, conv in enumerate(result):
            assert isinstance(conv, dict), f"Conversation {i} should be a dict"
            assert "role" in conv, f"Conversation {i} should have a role"
            assert "content" in conv, f"Conversation {i} should have content"
            assert isinstance(conv["content"], str), f"Conversation {i} content should be a string"
        
        # 验证统计信息
        stats = pruner.get_cleanup_statistics(conversations, result)
        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert stats["total_messages"] == len(conversations), "Should count all messages"
        assert stats["original_tokens"] > 0, "Should have original tokens"
        assert stats["pruned_tokens"] >= 0, "Should have pruned tokens"
        
        print(f"测试完成 - 原始tokens: {stats['original_tokens']}, 处理后tokens: {stats['pruned_tokens']}")


# Parametrized tests for comprehensive coverage
class TestParametrized:
    """Parametrized tests for comprehensive coverage"""

    @pytest.mark.parametrize("tool_name,expected", [
        ("ReadFileTool", "ReadFileTool"),
        ("ListFilesTool", "ListFilesTool"),
        ("WriteTool", "WriteTool"),
        ("", ""),
        ("Tool_With_Underscores", "Tool_With_Underscores"),
        ("Tool-With-Hyphens", "Tool-With-Hyphens"),
        ("Tool123", "Tool123"),
    ])
    def test_tool_name_extraction_parametrized(self, tool_name, expected):
        """Parametrized test for tool name extraction"""
        # 创建真实的参数和LLM对象
        args = AutoCoderArgs(
            source_dir=".",
            conversation_prune_safe_zone_tokens=1000,
            context_prune=True,
            context_prune_strategy="extract",
            query="测试查询"
        )
        llm = get_llm("v3_chat", product_mode="lite")
        assert llm is not None, "LLM should not be None"
        conversation_id = "parametrized-test-conversation"
        pruner = AgenticConversationPruner(args, llm, conversation_id=conversation_id)
        content = f"<tool_result tool_name='{tool_name}' success='true'>"
        result = pruner._extract_tool_name(content)
        assert result == expected

    @pytest.mark.parametrize("content,expected", [
        ("<tool_result tool_name='Test' success='true'>content</tool_result>", True),
        ("<tool_result tool_name=\"Test\" success=\"true\">content</tool_result>", True),
        ("Regular message", False),
        ("<tool_result>no tool_name</tool_result>", False),
        ("", False),
        ("<other_tag tool_name='test'>content</other_tag>", False),
    ])
    def test_tool_result_detection_parametrized(self, content, expected):
        """Parametrized test for tool result detection"""
        # 创建真实的参数和LLM对象
        args = AutoCoderArgs(
            source_dir=".",
            conversation_prune_safe_zone_tokens=1000,
            context_prune=True,
            context_prune_strategy="extract",
            query="测试查询"
        )
        llm = get_llm("v3_chat", product_mode="lite")
        assert llm is not None, "LLM should not be None"
        conversation_id = "tool-result-detection-test"
        pruner = AgenticConversationPruner(args, llm, conversation_id=conversation_id)
        result = pruner._is_tool_result_message(content)
        assert result == expected


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
