from typing import Union, Optional, Dict, Any, Type
from pydantic import Field
from ..llms import LLMManager
from .token_parser import TokenParser


class AutoCoderArgsParser:
    """AutoCoderArgs 参数解析器，提供高级参数解析功能"""
    
    def __init__(self, llm_manager: Optional[LLMManager] = None):
        """
        初始化参数解析器
        
        Args:
            llm_manager: LLM 管理器实例
        """
        self.llm_manager = llm_manager or LLMManager()
        self.token_parser = TokenParser(self.llm_manager)
    
    def parse_conversation_prune_safe_zone_tokens(self, 
                                                 value: Union[str, int, float],
                                                 code_model: Optional[str] = None) -> int:
        """
        解析 conversation_prune_safe_zone_tokens 参数
        
        Args:
            value: 参数值，支持字符串、整数、浮点数
            code_model: 代码模型名称，用于浮点数解析
            
        Returns:
            解析后的 token 数量
            
        Examples:
            >>> parser = AutoCoderArgsParser()
            >>> parser.parse_conversation_prune_safe_zone_tokens(51200)
            51200
            >>> parser.parse_conversation_prune_safe_zone_tokens("50k")
            51200
            >>> parser.parse_conversation_prune_safe_zone_tokens("50*1024")
            51200
            >>> parser.parse_conversation_prune_safe_zone_tokens(0.1, "deepseek/v3")
            # 返回 deepseek/v3 context_window 的 10%
        """
        try:
            return self.token_parser.parse_token_value(value, code_model)
        except ValueError as e:
            # 如果解析失败，返回默认值并记录警告
            default_value = 50 * 1024
            print(f"Warning: Failed to parse conversation_prune_safe_zone_tokens '{value}': {e}. Using default value: {default_value}")
            return default_value
    
    def parse_context_prune_safe_zone_tokens(self,
                                           value: Union[str, int, float],
                                           code_model: Optional[str] = None) -> int:
        """
        解析 context_prune_safe_zone_tokens 参数
        
        Args:
            value: 参数值
            code_model: 代码模型名称
            
        Returns:
            解析后的 token 数量
        """
        try:
            return self.token_parser.parse_token_value(value, code_model)
        except ValueError as e:
            default_value = 24 * 1024
            print(f"Warning: Failed to parse context_prune_safe_zone_tokens '{value}': {e}. Using default value: {default_value}")
            return default_value
    
    def parse_token_field(self, 
                         field_name: str,
                         value: Union[str, int, float],
                         code_model: Optional[str] = None,
                         default_value: Optional[int] = None) -> int:
        """
        通用的 token 字段解析方法
        
        Args:
            field_name: 字段名称
            value: 字段值
            code_model: 代码模型名称
            default_value: 默认值，如果为 None 则使用 50*1024
            
        Returns:
            解析后的 token 数量
        """
        try:
            return self.token_parser.parse_token_value(value, code_model)
        except ValueError as e:
            fallback_value = default_value or 50 * 1024
            print(f"Warning: Failed to parse {field_name} '{value}': {e}. Using default value: {fallback_value}")
            return fallback_value
    
    def validate_parsed_args(self, args_dict: Dict[str, Any], 
                           code_model: Optional[str] = None) -> Dict[str, Any]:
        """
        验证和解析整个参数字典
        
        Args:
            args_dict: 参数字典
            code_model: 代码模型名称
            
        Returns:
            验证和解析后的参数字典
        """
        # 定义需要解析的 token 字段及其默认值
        token_fields = {
            'conversation_prune_safe_zone_tokens': 50 * 1024,
            'context_prune_safe_zone_tokens': 24 * 1024,
            'context_prune_sliding_window_size': 1000,
            'context_prune_sliding_window_overlap': 100,
            'rag_params_max_tokens': 500000,
            'rag_context_window_limit': 120000,
            'rag_duckdb_vector_dim': 1024,
            'rag_duckdb_query_top_k': 10000,
            'rag_emb_dim': 1024,
            'rag_emb_text_size': 1024,
            'hybrid_index_max_output_tokens': 1000000,
            'data_cells_max_num': 2000,
        }
        
        parsed_dict = args_dict.copy()
        
        for field_name, default_value in token_fields.items():
            if field_name in parsed_dict:
                original_value = parsed_dict[field_name]
                # 如果值不是简单的 int，则进行解析
                if not isinstance(original_value, int):
                    parsed_dict[field_name] = self.parse_token_field(
                        field_name, original_value, code_model, default_value
                    )
        
        return parsed_dict
    
    def get_parsing_info(self) -> Dict[str, Any]:
        """
        获取解析器信息和使用示例
        
        Returns:
            包含解析器信息的字典
        """
        return {
            "supported_types": ["int", "float", "str"],
            "string_formats": self.token_parser.get_examples(),
            "supported_units": self.token_parser.get_supported_units(),
            "float_behavior": "Float values (0-1) are treated as percentages of the code_model's context_window",
            "fallback_context_window": 50 * 1024,
            "safety_notes": [
                "Invalid expressions fall back to default values",
                "Negative results are clamped to 0",
                "Division by zero is handled gracefully"
            ]
        }
    
    def create_flexible_field(self, 
                             default_value: Union[str, int, float],
                             description: str,
                             min_value: Optional[int] = None,
                             max_value: Optional[int] = None) -> Field:
        """
        创建支持灵活解析的 Pydantic 字段
        
        Args:
            default_value: 默认值
            description: 字段描述
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            Pydantic Field 对象
        """
        field_kwargs = {
            "default": default_value,
            "description": description
        }
        
        if min_value is not None:
            field_kwargs["ge"] = min_value
        if max_value is not None:
            field_kwargs["le"] = max_value
            
        return Field(**field_kwargs) 