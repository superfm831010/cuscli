import re
import ast
import operator
from typing import Union, Optional, Dict, Any
from ..llms import LLMManager, LLMModel


class TokenParser:
    """Token 数量解析器，支持多种格式的 token 数量表示"""
    
    # 单位转换映射
    UNIT_MULTIPLIERS = {
        'k': 1024,
        'm': 1024 * 1024,
        'g': 1024 * 1024 * 1024,
        'kb': 1024,
        'mb': 1024 * 1024,
        'gb': 1024 * 1024 * 1024,
    }
    
    # 支持的数学运算符
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    
    def __init__(self, llm_manager: Optional[LLMManager] = None):
        """
        初始化 TokenParser
        
        Args:
            llm_manager: LLM 管理器，用于获取模型信息
        """
        self.llm_manager = llm_manager or LLMManager()
    
    def parse_token_value(self, value: Union[str, int, float], 
                         code_model: Optional[str] = None) -> int:
        """
        解析 token 数量值
        
        Args:
            value: 要解析的值，可以是字符串、整数或浮点数
            code_model: 代码模型名称，用于 float 类型的解析
            
        Returns:
            解析后的 token 数量（整数）
            
        Raises:
            ValueError: 当解析失败时
        """
        if isinstance(value, int):
            return max(0, value)
        
        if isinstance(value, float):
            return self._parse_float_value(value, code_model)
        
        if isinstance(value, str):
            return self._parse_string_value(value)
        
        raise ValueError(f"Unsupported value type: {type(value)}")
    
    def _parse_float_value(self, value: float, code_model: Optional[str] = None) -> int:
        """
        解析浮点数值，基于模型的 context_window
        
        Args:
            value: 浮点数值（0-1 之间表示比例）
            code_model: 模型名称
            
        Returns:
            计算后的 token 数量
        """
        if not (0 <= value <= 1):
            raise ValueError(f"Float value must be between 0 and 1, got: {value}")
        
        context_window = self._get_context_window(code_model)
        return int(context_window * value)
    
    def _parse_string_value(self, value: str) -> int:
        """
        解析字符串值，支持纯数字、单位和数学表达式
        
        Args:
            value: 字符串值
            
        Returns:
            解析后的 token 数量
        """
        # 移除空格
        value = value.strip()
        
        if not value:
            raise ValueError("Empty string value")
        
        # 先尝试解析纯数字字符串（整数或浮点数）
        numeric_result = self._try_parse_numeric_string(value)
        if numeric_result is not None:
            return numeric_result
        
        # 再尝试解析带单位的简单数字
        unit_result = self._try_parse_with_unit(value)
        if unit_result is not None:
            return unit_result
        
        # 最后尝试解析数学表达式
        return self._parse_math_expression(value)
    
    def _try_parse_numeric_string(self, value: str) -> Optional[int]:
        """
        尝试解析纯数字字符串（整数或浮点数）
        
        Args:
            value: 字符串值
            
        Returns:
            解析结果，如果不是纯数字则返回 None
        """
        try:
            # 使用正则表达式检查是否为纯数字字符串
            
            # 匹配整数（包括负数）
            if re.match(r'^-?\d+$', value):
                return max(0, int(value))
            
            # 匹配浮点数（包括负数）
            if re.match(r'^-?\d+\.\d+$', value) or re.match(r'^-?\d+\.$', value) or re.match(r'^-?\.\d+$', value):
                float_value = float(value)
                return max(0, int(float_value))
                
            return None
                
        except (ValueError, TypeError):
            return None
    
    def _try_parse_with_unit(self, value: str) -> Optional[int]:
        """
        尝试解析带单位的数字（如 100k, 1.5m）
        
        Args:
            value: 字符串值
            
        Returns:
            解析结果，如果不匹配则返回 None
        """
        # 匹配数字+单位的模式
        pattern = r'^(\d+(?:\.\d+)?)\s*([kmgKMG](?:[bB]?)?)$'
        match = re.match(pattern, value)
        
        if not match:
            return None
        
        number_str, unit = match.groups()
        number = float(number_str)
        unit_lower = unit.lower()
        
        if unit_lower in self.UNIT_MULTIPLIERS:
            return int(number * self.UNIT_MULTIPLIERS[unit_lower])
        
        return None
    
    def _parse_math_expression(self, expression: str) -> int:
        """
        安全地解析数学表达式
        
        Args:
            expression: 数学表达式字符串
            
        Returns:
            计算结果
            
        Raises:
            ValueError: 当表达式无效时
        """
        try:
            # 解析 AST
            tree = ast.parse(expression, mode='eval')
            result = self._evaluate_ast_node(tree.body)
            
            # 确保结果是正整数
            if isinstance(result, (int, float)):
                return max(0, int(result))
            else:
                raise ValueError(f"Expression result is not a number: {result}")
                
        except (SyntaxError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid expression '{expression}': {e}")
    
    def _evaluate_ast_node(self, node: ast.AST) -> Union[int, float]:
        """
        递归计算 AST 节点
        
        Args:
            node: AST 节点
            
        Returns:
            计算结果
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._evaluate_ast_node(node.left)
            right = self._evaluate_ast_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            
            # 检查除零情况
            if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
                raise ValueError("Division by zero")
                
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._evaluate_ast_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported AST node type: {type(node)}")
    
    def _get_context_window(self, model_name: Optional[str] = None) -> int:
        """
        获取模型的 context_window
        
        Args:
            model_name: 模型名称
            
        Returns:
            context_window 大小，如果未找到或为 0 则返回默认值 120*1000
        """
        if not model_name:
            return 120 * 1000
        
        try:
            model = self.llm_manager.get_model(model_name)
            if model and model.context_window > 0:
                return model.context_window
        except Exception:
            # 忽略获取模型信息时的错误
            pass
        
        return 120 * 1000
    
    def validate_token_value(self, value: Union[str, int, float], 
                           min_tokens: int = 0, 
                           max_tokens: Optional[int] = None) -> bool:
        """
        验证 token 值是否在有效范围内
        
        Args:
            value: 要验证的值
            min_tokens: 最小 token 数
            max_tokens: 最大 token 数，None 表示无限制
            
        Returns:
            是否有效
        """
        try:
            parsed_value = self.parse_token_value(value)
            if parsed_value < min_tokens:
                return False
            if max_tokens is not None and parsed_value > max_tokens:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    def get_supported_units(self) -> Dict[str, int]:
        """获取支持的单位及其倍数"""
        return self.UNIT_MULTIPLIERS.copy()
    
    def get_examples(self) -> Dict[str, str]:
        """获取使用示例"""
        return {
            "整数": "51200",
            "纯数字字符串": "1024, 8, 1024.5",
            "带单位": "50k, 1m, 2.5k",
            "数学表达式": "50*1024, 100*1000, 2**16",
            "浮点数（比例）": "0.1 (表示 context_window 的 10%)",
            "复合表达式": "50*1024 + 10k"
        } 