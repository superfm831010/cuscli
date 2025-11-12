import os
import json
from typing import List, Dict, Optional, Union, cast
from urllib.parse import urlparse
from autocoder.common.llms import LLMManager, LLMModel

# Backward compatibility - preserve the path constant
MODELS_JSON = os.path.expanduser("~/.auto-coder/keys/models.json")

# Global LLMManager instance for backward compatibility
_llm_manager = None

def _get_llm_manager() -> LLMManager:
    """Get or create the global LLMManager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

def _model_to_dict(model: LLMModel) -> Dict:
    """Convert LLMModel to dictionary format for backward compatibility"""
    return {
        "name": model.name,
        "description": model.description,
        "model_name": model.model_name,
        "model_type": model.model_type,
        "base_url": model.base_url,
        "api_key_path": model.api_key_path or "",
        "is_reasoning": model.is_reasoning,
        "input_price": model.input_price,
        "output_price": model.output_price,
        "average_speed": 0.0,  # Default for backward compatibility
        "context_window": model.context_window,
        "provider": model.provider,        
        "max_output_tokens": model.max_output_tokens,
        "api_key": model.get_api_key()
    }

def process_api_key_path(base_url: str) -> str:
    """
    从 base_url 中提取 host 部分并处理特殊字符
    例如: https://api.example.com:8080/v1 -> api.example.com_8080
    """
    if not base_url:
        return ""
    
    parsed = urlparse(base_url)
    host = parsed.netloc
    
    # 将冒号替换为下划线
    host = host.replace(":", "_")
    
    return host

def load_models() -> List[Dict]:
    """
    Load models from ~/.auto-coder/keys/models.json and merge with default_models_list.
    Models are merged and deduplicated based on their name field.
    If file doesn't exist or is invalid, use default_models_list.
    """
    lm = _get_llm_manager()
    models = lm.get_all_models()
    return [_model_to_dict(model) for model in models.values()]

def save_models(models: List[Dict]) -> None:
    """
    Save models to ~/.auto-coder/keys/models.json
    """
    lm = _get_llm_manager()
    lm.add_models(cast(List[Union[LLMModel, Dict]], models))

def add_and_activate_models(models: List[Dict]) -> None:
    """
    添加模型
    """
    lm = _get_llm_manager()
    
    # First, get existing models to avoid duplicates
    existing_models = lm.get_all_models()
    new_models = []
    
    for model_data in models:
        if model_data["name"] not in existing_models:
            new_models.append(model_data)
    
    if new_models:
        lm.add_models(new_models)
    
    # Handle API keys separately for existing models
    for model_data in models:
        if "api_key" in model_data and model_data["api_key"]:
            lm.update_model_with_api_key(model_data["name"], model_data["api_key"])

def get_model_by_name(name: str) -> Dict:
    """
    根据模型名称查找模型
    """
    from autocoder.common.auto_coder_lang import get_message_with_format
    lm = _get_llm_manager()
    model = lm.get_model(name.strip())
    
    if not model:
        raise Exception(get_message_with_format("model_not_found", model_name=name))
    
    return _model_to_dict(model)

def update_model_input_price(name: str, price: float) -> bool:
    """更新模型输入价格
    
    Args:
        name (str): 要更新的模型名称，必须与models.json中的记录匹配
        price (float): 新的输入价格，单位：美元/百万tokens。必须大于等于0
        
    Returns:
        bool: 是否成功找到并更新了模型价格
        
    Raises:
        ValueError: 如果price为负数时抛出
        
    Example:
        >>> update_model_input_price("gpt-4", 3.0)
        True
        
    Notes:
        1. 价格设置后会立即生效并保存到models.json
        2. 实际费用计算时会按实际使用量精确到小数点后6位
        3. 设置价格为0表示该模型当前不可用
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    
    lm = _get_llm_manager()
    return lm.update_input_price(name, price)

def update_model_output_price(name: str, price: float) -> bool:
    """更新模型输出价格
    
    Args:
        name (str): 要更新的模型名称，必须与models.json中的记录匹配
        price (float): 新的输出价格，单位：美元/百万tokens。必须大于等于0
        
    Returns:
        bool: 是否成功找到并更新了模型价格
        
    Raises:
        ValueError: 如果price为负数时抛出
        
    Example:
        >>> update_model_output_price("gpt-4", 6.0)
        True
        
    Notes:
        1. 输出价格通常比输入价格高30%-50%
        2. 对于按token计费的API，实际收费按(input_tokens * input_price + output_tokens * output_price)计算
        3. 价格变更会影响所有依赖模型计费的功能（如成本预测、用量监控等）
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    
    lm = _get_llm_manager()
    return lm.update_output_price(name, price)

def update_model_speed(name: str, speed: float) -> bool:
    """更新模型平均速度
    
    Args:
        name: 模型名称
        speed: 速度(秒/请求)
        
    Returns:
        bool: 是否更新成功
    """
    lm = _get_llm_manager()
    # Since the new schema doesn't have average_speed, we'll use update_model
    # with a custom field or just return True for backward compatibility
    return lm.check_model_exists(name)  # Just check if model exists

def check_model_exists(name: str) -> bool:
    """
    检查模型是否存在
    """
    lm = _get_llm_manager()
    return lm.check_model_exists(name.strip())

def update_model_with_api_key(name: str, api_key: str) -> Optional[Dict]:
    """
    根据模型名称查找并更新模型的 api_key_path。
    如果找到模型,会根据其 base_url 处理 api_key_path。
    
    Args:
        name: 模型名称
        api_key: API密钥
        
    Returns:
        Dict: 更新后的模型信息,如果未找到则返回None
    """
    lm = _get_llm_manager()
    
    # Check if model exists
    if not lm.check_model_exists(name.strip()):
        return None
    
    # Update API key
    success = lm.update_model_with_api_key(name.strip(), api_key)
    
    if success:
        # Return the updated model as dict for backward compatibility
        model = lm.get_model(name.strip())
        return _model_to_dict(model) if model else None
    
    return None

def update_model(name: str, model_data: Dict) -> Optional[Dict]:
    """
    更新模型信息
    
    Args:
        name: 要更新的模型名称
        model_data: 包含模型新信息的字典，可以包含以下字段:
            - name: 模型名称
            - description: 模型描述
            - model_name: 模型实际名称
            - model_type: 模型类型
            - base_url: 基础URL
            - api_key: API密钥
            - is_reasoning: 是否为推理模型
            - input_price: 输入价格
            - output_price: 输出价格
            - max_output_tokens: 最大输出tokens
            - average_speed: 平均速度（向后兼容，但不会保存）
            
    Returns:
        Dict: 更新后的模型信息，如果未找到则返回None
    """
    lm = _get_llm_manager()
    
    # Filter out fields that don't exist in the new schema
    filtered_data = {k: v for k, v in model_data.items() if k != "average_speed"}
    
    updated_model = lm.update_model(name, filtered_data)
    
    if updated_model:
        return _model_to_dict(updated_model)
    
    return None

# Backward compatibility: preserve the default_models_list for any external usage
default_models_list = load_models()

