import byzerllm
from typing import Union, Optional, List

# Import the new LLM module
from autocoder.common.llms import LLMManager

# Global LLM manager instances cache (keyed by model_file path)
_llm_managers = {}


def _get_llm_manager(model_file: Optional[str] = None) -> LLMManager:
    """Get or create LLM manager instance for the given model_file

    Args:
        model_file: Optional path to models.json file. None uses default path.

    Returns:
        LLMManager instance for the specified model_file
    """
    global _llm_managers

    # Use model_file as cache key (None for default)
    cache_key = model_file if model_file else "__default__"

    if cache_key not in _llm_managers:
        _llm_managers[cache_key] = LLMManager(models_json_path=model_file)

    return _llm_managers[cache_key]


def get_llm_names(
    llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM, str, List],
    target_model_type: Optional[str] = None,
) -> List[str]:
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
            return [
                _llm.default_model_name
                for _llm in llm
                if hasattr(_llm, "default_model_name") and _llm.default_model_name
            ]
        elif isinstance(llm, str):
            return llm.split(",") if llm else []
        elif hasattr(llm, "default_model_name") and llm.default_model_name:
            return [llm.default_model_name]
        else:
            return []

    # Handle target_model_type case
    if not isinstance(llm, (str, list)) and hasattr(llm, "get_sub_client"):
        llms = llm.get_sub_client(target_model_type)

        if llms is None:
            if isinstance(llm, list):
                return [
                    _llm.default_model_name
                    for _llm in llm
                    if hasattr(_llm, "default_model_name") and _llm.default_model_name
                ]
            elif hasattr(llm, "default_model_name") and llm.default_model_name:
                return [llm.default_model_name]
            else:
                return []
        elif isinstance(llms, list):
            return [
                _llm.default_model_name
                for _llm in llms
                if hasattr(_llm, "default_model_name") and _llm.default_model_name
            ]
        elif isinstance(llms, str) and llms:
            return llms.split(",")
        elif hasattr(llms, "default_model_name") and llms.default_model_name:
            return [llms.default_model_name]
        else:
            return []

    return []


def get_model_info(
    model_names: str, product_mode: str, model_file: Optional[str] = None
):
    """
    Get model information using the new LLM module

    Args:
        model_names: Comma-separated model names or single model name
        product_mode: Product mode ("pro" or "lite")
        model_file: Optional path to models.json file

    Returns:
        Model info dictionary or None
    """
    manager = _get_llm_manager(model_file)

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


def get_single_llm(
    model_names: str, product_mode: str, model_file: Optional[str] = None
):
    """
    Get a single LLM instance using the new LLM module

    Args:
        model_names: Comma-separated model names or single model name
        product_mode: Product mode ("pro" or "lite")
        model_file: Optional path to models.json file

    Returns:
        LLM instance or None
    """
    manager = _get_llm_manager(model_file)
    return manager.get_single_llm(model_names, product_mode)
