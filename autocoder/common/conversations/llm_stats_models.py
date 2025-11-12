"""
LLM 调用统计信息的 Pydantic 模型定义
"""

from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
import time
from loguru import logger


class LLMUsageStats(BaseModel):
    """LLM 使用统计信息模型"""
    
    input_tokens: Optional[int] = Field(default=None, description="输入token数量")
    output_tokens: Optional[int] = Field(default=None, description="输出token数量") 
    total_tokens: Optional[int] = Field(default=None, description="总token数量")
    
    # 缓存相关信息
    cache_creation_input_tokens: Optional[int] = Field(default=None, description="缓存创建输入token数量")
    cache_read_input_tokens: Optional[int] = Field(default=None, description="缓存读取输入token数量")
    
    # 成本信息
    input_cost: Optional[float] = Field(default=None, description="输入成本")
    output_cost: Optional[float] = Field(default=None, description="输出成本")
    total_cost: Optional[float] = Field(default=None, description="总成本")
    
    # 模型信息
    model_name: Optional[str] = Field(default=None, description="使用的模型名称")
    
    # 时间信息
    request_time: Optional[float] = Field(default_factory=time.time, description="请求时间戳")
    response_time: Optional[float] = Field(default=None, description="响应时间戳")
    duration_ms: Optional[float] = Field(default=None, description="请求持续时间(毫秒)")
    
    model_config = ConfigDict(
        extra="allow",  # 允许额外字段，以便支持未来扩展
        validate_assignment=True  # 赋值时验证
    )


class LLMCacheInfo(BaseModel):
    """LLM 缓存命中信息模型"""
    
    cache_hit: Optional[bool] = Field(default=None, description="是否命中缓存")
    cache_type: Optional[str] = Field(default=None, description="缓存类型(如: claude_sonnet)")
    cache_key: Optional[str] = Field(default=None, description="缓存键")
    cache_creation_input_tokens: Optional[int] = Field(default=None, description="缓存创建使用的输入token数量")
    cache_read_input_tokens: Optional[int] = Field(default=None, description="从缓存读取的输入token数量")
    
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True
    )


class LLMCallMetadata(BaseModel):
    """LLM 调用的完整元数据模型"""
    
    usage_stats: Optional[LLMUsageStats] = Field(default=None, description="使用统计信息")
    cache_info: Optional[LLMCacheInfo] = Field(default=None, description="缓存信息")
    
    # 请求相关信息
    request_id: Optional[str] = Field(default=None, description="请求ID")
    conversation_round: Optional[int] = Field(default=None, description="对话轮次")
    
    # 错误信息
    error_message: Optional[str] = Field(default=None, description="错误信息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    
    # 额外的原始数据
    raw_response_metadata: Optional[Dict[str, Any]] = Field(default=None, description="原始响应元数据")
    
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMCallMetadata":
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_raw_metadata(cls, raw_metadata: Dict[str, Any], **extra_fields) -> "LLMCallMetadata":
        """从原始元数据创建实例"""
        # 解析常见的元数据字段
        usage_stats = None
        cache_info = None
        
        # 解析 usage 信息
        usage_data = None
        if "usage" in raw_metadata:
            usage_data = raw_metadata["usage"]
        elif any(key in raw_metadata for key in ["prompt_tokens", "completion_tokens", "input_tokens", "output_tokens", "total_tokens", 
                                                "input_tokens_count", "generated_tokens_count", "total_tokens_count"]):
            # 如果直接包含使用统计字段，则使用 raw_metadata 本身
            usage_data = raw_metadata
        
        if usage_data:
            usage_stats = cls._extract_usage_stats(usage_data, raw_metadata)
        
        # 解析缓存信息
        cache_info = cls._extract_cache_info(raw_metadata)
        
        return cls(
            usage_stats=usage_stats,
            cache_info=cache_info,
            raw_response_metadata=raw_metadata,
            **extra_fields
        )
    
    @classmethod
    def _extract_usage_stats(cls, usage_data: Union[Dict[str, Any], object], raw_metadata: Dict[str, Any]) -> Optional[LLMUsageStats]:
        """从usage数据中提取统计信息，支持dict和对象两种形态"""
        def safe_get(data, *keys):
            """安全获取值，支持dict和对象属性访问"""
            for key in keys:
                if isinstance(data, dict):
                    value = data.get(key)
                else:
                    value = getattr(data, key, None)
                # 检查值是否有效（不是Mock对象或其他无效类型）
                if value is not None and not str(type(value)).startswith("<class 'unittest.mock."):
                    # 验证基本数据类型
                    if isinstance(value, (int, float, str, bool)):
                        return value
            return None
        
        # 提取input tokens (支持多种字段名)
        input_tokens = safe_get(usage_data, "prompt_tokens", "input_tokens", "input_tokens_count")
        
        # 提取output tokens (支持多种字段名)
        output_tokens = safe_get(usage_data, "completion_tokens", "output_tokens", "generated_tokens_count")
        
        # 提取total tokens，如果没有则计算
        total_tokens = safe_get(usage_data, "total_tokens", "total_tokens_count")
        if total_tokens is None and input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens
        
        # 提取模型名称
        model_name = safe_get(usage_data, "model", "model_name") or safe_get(raw_metadata, "model", "model_name")
        
        # 提取缓存相关token数量 (支持多种字段名变体)
        cache_creation_input_tokens = safe_get(usage_data, "cache_creation_input_tokens", "cache_creation_tokens")
        cache_read_input_tokens = safe_get(usage_data, "cache_read_input_tokens", "cache_read_tokens")
        
        # 提取成本信息
        input_cost = safe_get(usage_data, "input_cost", "prompt_cost")
        output_cost = safe_get(usage_data, "output_cost", "completion_cost")
        total_cost = safe_get(usage_data, "total_cost")
        if total_cost is None and input_cost is not None and output_cost is not None:
            total_cost = input_cost + output_cost
        
        # 提取时间信息
        duration_ms = safe_get(usage_data, "duration_ms", "duration", "response_time_ms")
        
        # 如果没有任何有效的token信息，返回None
        if input_tokens is None and output_tokens is None and total_tokens is None:
            return None
        
        return LLMUsageStats(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model_name=model_name,
            duration_ms=duration_ms
        )
    
    @classmethod
    def _extract_cache_info(cls, raw_metadata: Dict[str, Any]) -> Optional[LLMCacheInfo]:
        """从原始元数据中提取缓存信息"""
        # 检查是否有缓存相关字段
        cache_keys = [key for key in raw_metadata.keys() if key.startswith("cache")]
        if not cache_keys:
            return None
        
        def safe_get(data, *keys):
            """安全获取值"""
            for key in keys:
                value = data.get(key) if isinstance(data, dict) else getattr(data, key, None)
                if value is not None:
                    return value
            return None
        
        # 提取缓存信息 (支持多种字段名变体)
        cache_hit = safe_get(raw_metadata, "cache_hit", "is_cache_hit")
        cache_type = safe_get(raw_metadata, "cache_type", "cache_provider")
        cache_key = safe_get(raw_metadata, "cache_key", "cache_id")
        cache_creation_input_tokens = safe_get(raw_metadata, "cache_creation_input_tokens", "cache_creation_tokens")
        cache_read_input_tokens = safe_get(raw_metadata, "cache_read_input_tokens", "cache_read_tokens")
        
        return LLMCacheInfo(
            cache_hit=cache_hit,
            cache_type=cache_type,
            cache_key=cache_key,
            cache_creation_input_tokens=cache_creation_input_tokens,
            cache_read_input_tokens=cache_read_input_tokens
        )


def create_llm_metadata_from_token_usage_event(
    token_usage_event: Any,
    conversation_round: Optional[int] = None,
    request_id: Optional[str] = None
) -> Optional[LLMCallMetadata]:
    """
    从 TokenUsageEvent 创建 LLM 元数据
    
    Args:
        token_usage_event: TokenUsageEvent 实例
        conversation_round: 对话轮次
        request_id: 请求ID
        
    Returns:
        LLMCallMetadata 实例或 None
    """
    try:
        if not hasattr(token_usage_event, 'usage') or not token_usage_event.usage:
            return None
        
        usage_data = token_usage_event.usage
        
        # 如果usage是对象而不是dict，将其转换为dict以便处理
        if not isinstance(usage_data, dict):
            # 尝试将对象转换为dict
            raw_metadata = {}
            
            # 获取对象的所有属性
            for attr_name in dir(usage_data):
                if not attr_name.startswith('_') and not callable(getattr(usage_data, attr_name, None)):  # 跳过私有属性和方法
                    try:
                        attr_value = getattr(usage_data, attr_name)
                        # 只保存基本数据类型
                        if isinstance(attr_value, (int, float, str, bool, type(None))):
                            raw_metadata[attr_name] = attr_value
                    except Exception:
                        continue  # 跳过无法访问的属性
        else:
            raw_metadata = usage_data
        
        # 如果还有其他有用的属性，也加入到metadata中
        if hasattr(token_usage_event, 'model'):
            raw_metadata['model'] = token_usage_event.model
        if hasattr(token_usage_event, 'request_id'):
            raw_metadata['request_id'] = token_usage_event.request_id
        
        return LLMCallMetadata.from_raw_metadata(
            raw_metadata=raw_metadata,
            conversation_round=conversation_round,
            request_id=request_id
        )
    except Exception as e:
        # 记录错误但不抛出异常，确保程序继续运行
        logger.warning(f"Failed to create LLM metadata from token usage event: {e}")
        return None
