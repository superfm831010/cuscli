import byzerllm
from typing import Union, Optional, List

# Import the new LLM module
from autocoder.common.llms import LLMManager

# Global LLM manager instance
_llm_manager = None

def _get_llm_manager() -> LLMManager:
    """Get or create the global LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

def get_llm_names(llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM, str, List], 
                  target_model_type: Optional[str] = None) -> List[str]:
    """
    Get LLM model names from various input types
    
    Args:
        llm: LLM instance, model name string, or list of LLMs
        target_model_type: Optional target model type filter
        
    Returns:
        List of model names
    """
    if target_model_type is None:
        if isinstance(llm, list):
            return [_llm.default_model_name for _llm in llm if hasattr(_llm, 'default_model_name') and _llm.default_model_name]
        elif isinstance(llm, str):
            return llm.split(",") if llm else []
        elif hasattr(llm, 'default_model_name') and llm.default_model_name:
            return [llm.default_model_name]
        else:
            return []
   
    # Handle target_model_type case
    if not isinstance(llm, (str, list)) and hasattr(llm, 'get_sub_client'):
        llms = llm.get_sub_client(target_model_type)
        
        if llms is None:
            if isinstance(llm, list):
                return [_llm.default_model_name for _llm in llm if hasattr(_llm, 'default_model_name') and _llm.default_model_name]
            elif hasattr(llm, 'default_model_name') and llm.default_model_name:
                return [llm.default_model_name]
            else:
                return []
        elif isinstance(llms, list):
            return [_llm.default_model_name for _llm in llms if hasattr(_llm, 'default_model_name') and _llm.default_model_name]
        elif isinstance(llms, str) and llms:
            return llms.split(",")
        elif hasattr(llms, 'default_model_name') and llms.default_model_name:
            return [llms.default_model_name]
        else:
            return []
    
    return []

def get_model_info(model_names: str, product_mode: str):
    """
    Get model information using the new LLM module
    
    Args:
        model_names: Comma-separated model names or single model name
        product_mode: Product mode ("pro" or "lite")
        
    Returns:
        Model info dictionary or None
    """
    manager = _get_llm_manager()
    
    if product_mode == "pro":
        return None

    if product_mode == "lite":
        if "," in model_names:
            # Multiple code models specified
            names = model_names.split(",")
            for model_name in names:
                model_name = model_name.strip()
                model_info = manager.get_model_info(model_name, product_mode)
                if model_info:
                    return model_info
            return None
        else:
            # Single code model
            return manager.get_model_info(model_names.strip(), product_mode)

def get_single_llm(model_names: str, product_mode: str):
    """
    Get a single LLM instance using the new LLM module
    
    Args:
        model_names: Comma-separated model names or single model name
        product_mode: Product mode ("pro" or "lite")
        
    Returns:
        LLM instance or None
    """
    manager = _get_llm_manager()
    return manager.get_single_llm(model_names, product_mode)