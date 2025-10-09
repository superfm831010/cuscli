import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from autocoder.common.autocoderargs_parser.token_parser import TokenParser
from autocoder.common.llms import LLMManager, LLMModel


@pytest.fixture
def mock_llm_manager():
    """创建 mock LLM manager fixture"""
    return Mock(spec=LLMManager)


@pytest.fixture
def token_parser(mock_llm_manager):
    """创建 TokenParser 实例 fixture"""
    return TokenParser(mock_llm_manager)


@pytest.fixture
def temp_dir():
    """创建临时目录 fixture"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestTokenParser:
    """TokenParser 测试类"""
    
    def test_parse_int_value(self, token_parser):
        """测试整数值解析"""
        result = token_parser.parse_token_value(51200)
        assert result == 51200
        
        # 测试负数会被转为 0
        result = token_parser.parse_token_value(-100)
        assert result == 0
    
    def test_parse_float_value(self, token_parser, mock_llm_manager):
        """测试浮点数值解析"""
        # Mock 模型信息
        mock_model = Mock(spec=LLMModel)
        mock_model.context_window = 100000
        mock_llm_manager.get_model.return_value = mock_model
        
        result = token_parser.parse_token_value(0.1, "test/model")
        assert result == 10000  # 100000 * 0.1
        
        # 测试无效的浮点数范围
        with pytest.raises(ValueError):
            token_parser.parse_token_value(1.5, "test/model")
        
        with pytest.raises(ValueError):
            token_parser.parse_token_value(-0.1, "test/model")
    
    def test_parse_float_value_fallback(self, token_parser, mock_llm_manager):
        """测试浮点数解析的回退机制"""
        # Mock 获取模型失败
        mock_llm_manager.get_model.return_value = None
        
        result = token_parser.parse_token_value(0.1)
        expected = int((120 * 1000) * 0.1)  # 默认 context_window
        assert result == expected
    
    @pytest.mark.parametrize("input_str,expected", [
        ("100k", 100 * 1024),
        ("1m", 1024 * 1024),
        ("2.5k", int(2.5 * 1024)),
        ("1g", 1024 * 1024 * 1024),
        ("50K", 50 * 1024),  # 大写
        ("1M", 1024 * 1024),  # 大写
        ("100kb", 100 * 1024),  # 带 b
        ("2MB", 2 * 1024 * 1024),  # 大写带 b
    ])
    def test_parse_unit_strings(self, token_parser, input_str, expected):
        """测试带单位的字符串解析"""
        result = token_parser.parse_token_value(input_str)
        assert result == expected
    
    @pytest.mark.parametrize("input_str,expected", [
        ("1024", 1024),        # 纯整数字符串
        ("0", 0),              # 零
        ("8", 8),              # 单个数字
        ("123456", 123456),    # 大数字
        ("1024.0", 1024),      # 浮点数字符串（整数值）
        ("1024.5", 1024),      # 浮点数字符串（小数会被截断）
        ("1024.", 1024),       # 末尾有小数点
        (".5", 0),             # 纯小数（< 1 的会被转为 0）
        ("0.8", 0),            # 小数（< 1 的会被转为 0）
        ("100.99", 100),       # 小数截断
        ("-10", 0),            # 负数会被转为 0
        ("-100.5", 0),         # 负浮点数会被转为 0
    ])
    def test_parse_numeric_strings(self, token_parser, input_str, expected):
        """测试纯数字字符串解析"""
        result = token_parser.parse_token_value(input_str)
        assert result == expected
    
    @pytest.mark.parametrize("input_str,expected", [
        ("00123", 123),        # 前导零
        ("123.000", 123),      # 后续零
        ("0000", 0),           # 多个零
        ("1.0000", 1),         # 浮点数后续零
        ("0001.5", 1),         # 前导零加浮点数
    ])
    def test_parse_numeric_strings_edge_cases(self, token_parser, input_str, expected):
        """测试纯数字字符串解析的边界情况"""
        result = token_parser.parse_token_value(input_str)
        assert result == expected
    
    def test_parse_priority_order(self, token_parser):
        """测试解析优先级：纯数字 > 带单位 > 数学表达式"""
        # 确保纯数字不会被误认为是数学表达式
        assert token_parser.parse_token_value("1024") == 1024
        assert token_parser.parse_token_value("1024.0") == 1024
        
        # 确保带单位的解析优先于数学表达式（虽然这种情况不太可能发生冲突）
        assert token_parser.parse_token_value("1k") == 1024
        assert token_parser.parse_token_value("1m") == 1024 * 1024
        
        # 确保数学表达式正常工作
        assert token_parser.parse_token_value("1+1") == 2
        assert token_parser.parse_token_value("2*2") == 4
    
    @pytest.mark.parametrize("expr,expected", [
        ("50*1024", 50 * 1024),
        ("100*1000", 100 * 1000),
        ("2**16", 2**16),
        ("1024+512", 1024 + 512),
        ("2048-512", 2048 - 512),
        ("100*10+50", 100 * 10 + 50),
        ("(100+50)*10", (100 + 50) * 10),
        ("1024//2", 1024 // 2),
        ("1024%100", 1024 % 100),
    ])
    def test_parse_math_expressions(self, token_parser, expr, expected):
        """测试数学表达式解析"""
        result = token_parser.parse_token_value(expr)
        assert result == expected
    
    @pytest.mark.parametrize("invalid_expr", [
        "invalid_string",
        "100x",  # 无效单位
        "1024 + undefined_var",  # 未定义变量
        "1024 / 0",  # 除零
        "",  # 空字符串
        "   ",  # 只有空格
    ])
    def test_parse_invalid_expressions(self, token_parser, invalid_expr):
        """测试无效表达式处理"""
        with pytest.raises(ValueError):
            token_parser.parse_token_value(invalid_expr)
    
    def test_validate_token_value(self, token_parser):
        """测试值验证功能"""
        # 有效值
        assert token_parser.validate_token_value(1024) is True
        assert token_parser.validate_token_value("50k") is True
        assert token_parser.validate_token_value("50*1024") is True
        
        # 范围验证
        assert token_parser.validate_token_value(1024, min_tokens=500, max_tokens=2000) is True
        assert token_parser.validate_token_value(100, min_tokens=500, max_tokens=2000) is False
        assert token_parser.validate_token_value(3000, min_tokens=500, max_tokens=2000) is False
        
        # 无效值
        assert token_parser.validate_token_value("invalid") is False
    
    def test_get_supported_units(self, token_parser):
        """测试获取支持的单位"""
        units = token_parser.get_supported_units()
        assert 'k' in units
        assert 'm' in units
        assert 'g' in units
        assert units['k'] == 1024
        assert units['m'] == 1024 * 1024
    
    def test_get_examples(self, token_parser):
        """测试获取使用示例"""
        examples = token_parser.get_examples()
        assert isinstance(examples, dict)
        assert "整数" in examples
        assert "带单位" in examples
        assert "数学表达式" in examples
    
    @pytest.mark.parametrize("invalid_value", [
        [1, 2, 3],  # 列表类型不支持
        {"value": 1024},  # 字典类型不支持
    ])
    def test_unsupported_type(self, token_parser, invalid_value):
        """测试不支持的类型"""
        with pytest.raises(ValueError):
            token_parser.parse_token_value(invalid_value) 