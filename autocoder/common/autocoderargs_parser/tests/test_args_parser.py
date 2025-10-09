import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from autocoder.common.autocoderargs_parser import AutoCoderArgsParser, TokenParser
from autocoder.common.llms import LLMManager, LLMModel


@pytest.fixture
def mock_llm_manager():
    """创建 mock LLM manager fixture"""
    mock_manager = Mock(spec=LLMManager)
    
    # 设置默认的模型信息
    mock_model = Mock(spec=LLMModel)
    mock_model.context_window = 32768  # deepseek/v3 的默认值
    mock_manager.get_model.return_value = mock_model
    
    return mock_manager


@pytest.fixture
def args_parser(mock_llm_manager):
    """创建 AutoCoderArgsParser 实例 fixture"""
    return AutoCoderArgsParser(mock_llm_manager)


class TestAutoCoderArgsParser:
    """AutoCoderArgsParser 测试类"""
    
    @pytest.mark.parametrize("value,expected", [
        (51200, 51200),  # 整数
        ("50k", 51200),  # 带单位字符串
        ("50*1024", 51200),  # 数学表达式
        (0.1, 3276),  # 浮点数比例 (32768 * 0.1)
    ])
    def test_parse_conversation_prune_safe_zone_tokens(self, args_parser, value, expected):
        """测试 conversation_prune_safe_zone_tokens 解析"""
        result = args_parser.parse_conversation_prune_safe_zone_tokens(value, "deepseek/v3")
        assert result == expected
    
    def test_parse_conversation_prune_safe_zone_tokens_invalid(self, args_parser, capsys):
        """测试无效值的处理"""
        result = args_parser.parse_conversation_prune_safe_zone_tokens("invalid", "deepseek/v3")
        
        # 应该返回默认值
        assert result == 50 * 1024
        
        # 应该有警告信息
        captured = capsys.readouterr()
        assert "Warning: Failed to parse conversation_prune_safe_zone_tokens" in captured.out
    
    @pytest.mark.parametrize("value,expected", [
        (24576, 24576),  # 整数
        ("24k", 24576),  # 带单位字符串
        ("24*1024", 24576),  # 数学表达式
        (0.05, 1638),  # 浮点数比例 (32768 * 0.05)
    ])
    def test_parse_context_prune_safe_zone_tokens(self, args_parser, value, expected):
        """测试 context_prune_safe_zone_tokens 解析"""
        result = args_parser.parse_context_prune_safe_zone_tokens(value, "deepseek/v3")
        assert result == expected
    
    def test_parse_context_prune_safe_zone_tokens_invalid(self, args_parser, capsys):
        """测试 context_prune_safe_zone_tokens 无效值处理"""
        result = args_parser.parse_context_prune_safe_zone_tokens("invalid", "deepseek/v3")
        
        # 应该返回默认值
        assert result == 24 * 1024
        
        # 应该有警告信息
        captured = capsys.readouterr()
        assert "Warning: Failed to parse context_prune_safe_zone_tokens" in captured.out
    
    @pytest.mark.parametrize("field_name,value,default_value,expected", [
        ("rag_params_max_tokens", "500k", 500000, 512000),
        ("data_cells_max_num", "2k", 2000, 2048),
        ("context_prune_sliding_window_size", 1000, 1000, 1000),
        ("hybrid_index_max_output_tokens", "1m", 1000000, 1048576),
    ])
    def test_parse_token_field(self, args_parser, field_name, value, default_value, expected):
        """测试通用 token 字段解析"""
        result = args_parser.parse_token_field(field_name, value, "deepseek/v3", default_value)
        assert result == expected
    
    def test_parse_token_field_invalid(self, args_parser, capsys):
        """测试通用 token 字段无效值处理"""
        field_name = "test_field"
        result = args_parser.parse_token_field(field_name, "invalid", "deepseek/v3", 1000)
        
        # 应该返回提供的默认值
        assert result == 1000
        
        # 应该有警告信息
        captured = capsys.readouterr()
        assert f"Warning: Failed to parse {field_name}" in captured.out
    
    def test_validate_parsed_args(self, args_parser):
        """测试批量参数验证和解析"""
        args_dict = {
            "conversation_prune_safe_zone_tokens": "50k",
            "context_prune_safe_zone_tokens": "24*1024",
            "rag_params_max_tokens": 0.5,  # 比例值
            "data_cells_max_num": "2k",
            "other_field": "not_a_token_field",  # 非 token 字段
            "regular_int_field": 12345  # 已经是 int 的字段
        }
        
        parsed_dict = args_parser.validate_parsed_args(args_dict, "deepseek/v3")
        
        # 检查 token 字段被正确解析
        assert parsed_dict["conversation_prune_safe_zone_tokens"] == 51200
        assert parsed_dict["context_prune_safe_zone_tokens"] == 24576
        assert parsed_dict["rag_params_max_tokens"] == 16384  # 32768 * 0.5
        assert parsed_dict["data_cells_max_num"] == 2048
        
        # 检查非 token 字段保持不变
        assert parsed_dict["other_field"] == "not_a_token_field"
        assert parsed_dict["regular_int_field"] == 12345
    
    def test_validate_parsed_args_with_non_token_fields_only(self, args_parser):
        """测试只包含非 token 字段的参数字典"""
        args_dict = {
            "model": "deepseek/v3",
            "query": "test query",
            "output": "result.txt",
            "skip_confirm": True
        }
        
        parsed_dict = args_parser.validate_parsed_args(args_dict, "deepseek/v3")
        
        # 所有字段应该保持不变
        assert parsed_dict == args_dict
    
    def test_get_parsing_info(self, args_parser):
        """测试获取解析器信息"""
        info = args_parser.get_parsing_info()
        
        # 检查必要的信息字段
        assert "supported_types" in info
        assert "string_formats" in info
        assert "supported_units" in info
        assert "float_behavior" in info
        assert "fallback_context_window" in info
        assert "safety_notes" in info
        
        # 检查支持的类型
        assert "int" in info["supported_types"]
        assert "float" in info["supported_types"]
        assert "str" in info["supported_types"]
        
        # 检查字符串格式示例
        assert isinstance(info["string_formats"], dict)
        assert "整数" in info["string_formats"]
        
        # 检查支持的单位
        assert isinstance(info["supported_units"], dict)
        assert "k" in info["supported_units"]
        assert info["supported_units"]["k"] == 1024
    
    def test_float_value_with_zero_context_window(self, args_parser, mock_llm_manager):
        """测试当模型 context_window 为 0 时的回退机制"""
        # Mock 模型的 context_window 为 0
        mock_model = Mock(spec=LLMModel)
        mock_model.context_window = 0
        mock_llm_manager.get_model.return_value = mock_model
        
        result = args_parser.parse_conversation_prune_safe_zone_tokens(0.1, "test/model")
        # 应该使用默认值 120*1000
        expected = int((120 * 1000) * 0.1)
        assert result == expected
    
    def test_float_value_with_missing_model(self, args_parser, mock_llm_manager):
        """测试当模型不存在时的回退机制"""
        # Mock 获取模型返回 None
        mock_llm_manager.get_model.return_value = None
        
        result = args_parser.parse_conversation_prune_safe_zone_tokens(0.1, "nonexistent/model")
        # 应该使用默认值 120*1000
        expected = int((120 * 1000) * 0.1)
        assert result == expected
    
    def test_args_parser_uses_token_parser(self, args_parser):
        """测试 AutoCoderArgsParser 正确使用 TokenParser"""
        # 确保 AutoCoderArgsParser 内部使用 TokenParser
        assert hasattr(args_parser, 'token_parser')
        assert isinstance(args_parser.token_parser, TokenParser)
        assert args_parser.token_parser.llm_manager == args_parser.llm_manager


class TestAutoCoderArgsParserIntegration:
    """AutoCoderArgsParser 集成测试"""
    
    def test_integration_with_real_llm_manager(self):
        """测试与真实 LLM Manager 的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            models_json = Path(temp_dir) / "models.json"
            
            # 创建真实的 LLM Manager（使用临时目录）
            from autocoder.common.llms import LLMManager
            llm_manager = LLMManager(str(models_json))
            
            # 创建 AutoCoderArgsParser
            parser = AutoCoderArgsParser(llm_manager)
            
            # 测试基本功能
            result = parser.parse_conversation_prune_safe_zone_tokens("50k")
            assert result == 51200
            
            # 测试浮点数（由于使用默认模型，会使用回退值）
            result = parser.parse_conversation_prune_safe_zone_tokens(0.1)
            expected = int((120 * 1000) * 0.1)
            assert result == expected
    
    @pytest.mark.parametrize("field_value", [
        "50k",
        "50*1024", 
        0.1,
        51200
    ])
    def test_all_supported_formats(self, field_value):
        """测试所有支持的格式都能正常工作"""
        # 使用临时 LLM Manager
        with tempfile.TemporaryDirectory() as temp_dir:
            models_json = Path(temp_dir) / "models.json"
            
            from autocoder.common.llms import LLMManager
            llm_manager = LLMManager(str(models_json))
            parser = AutoCoderArgsParser(llm_manager)
            
            # 所有格式都应该成功解析，不抛出异常
            result = parser.parse_conversation_prune_safe_zone_tokens(field_value)
            assert isinstance(result, int)
            assert result >= 0 