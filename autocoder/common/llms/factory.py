import byzerllm
from typing import Union, List, Optional

from .schema import LLMModel


class LLMFactory:
    """LLM 实例化工厂"""
    
    @staticmethod
    def create_llm(model: LLMModel, product_mode: str) -> Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]:
        """
        根据模型配置和产品模式创建 LLM 实例
        
        Args:
            model: LLM 模型配置
            product_mode: 产品模式 ("pro" 或 "lite")
            
        Returns:
            配置好的 byzerllm 客户端实例
            
        Raises:
            ValueError: 当模型未配置 API 密钥时
        """
        # 检查是否有 API 密钥
        api_key = model.get_api_key()
        if not api_key:
            raise ValueError(f"Model {model.name} has no API key configured")
        
        if product_mode == "pro":
            # Pro 模式：使用 ByzerLLM.from_default_model
            return byzerllm.ByzerLLM.from_default_model(model.name)
        
        elif product_mode == "lite":
            # Lite 模式：使用 SimpleByzerLLM
            target_llm = byzerllm.SimpleByzerLLM(default_model_name=model.name)
            
            # 部署配置
            infer_params = {
                "saas.base_url": model.base_url,
                "saas.api_key": api_key,
                "saas.model": model.model_name,
                "saas.is_reasoning": model.is_reasoning,
                "saas.max_output_tokens": model.max_output_tokens
            }
            
            target_llm.deploy(
                model_path="",
                pretrained_model_type=model.model_type,
                udf_name=model.name,
                infer_params=infer_params
            )
            
            return target_llm
        
        else:
            raise ValueError(f"Unsupported product mode: {product_mode}")
    
    @staticmethod
    def create_llm_from_names(model_names: str, models: List[LLMModel], product_mode: str) -> Optional[Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]]:
        """
        根据模型名称列表创建 LLM 实例（返回第一个可用的）
        
        Args:
            model_names: 逗号分隔的模型名称列表
            models: 可用的模型列表
            product_mode: 产品模式
            
        Returns:
            第一个成功创建的 LLM 实例，如果都失败则返回 None
            
        Raises:
            ValueError: 当所有模型都无法创建时，包含详细的错误信息
        """
        # 处理模型名称列表
        if "," in model_names:
            names = [name.strip() for name in model_names.split(",")]
        else:
            names = [model_names.strip()]
        
        # 收集错误信息
        errors = []
        
        # 查找并创建第一个可用的模型
        for name in names:
            # 在模型列表中查找
            model = next((m for m in models if m.name == name), None)
            if not model:
                errors.append(f"Model '{name}' not found")
                continue
                
            try:
                return LLMFactory.create_llm(model, product_mode)
            except ValueError as e:
                errors.append(f"Model '{name}': {str(e)}")
                continue
        
        # 如果所有模型都失败了，抛出包含所有错误信息的异常
        if errors:
            error_msg = f"Failed to create LLM instance for models: {model_names}\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
        
        # 如果没有找到任何模型（理论上不应该到这里）
        raise ValueError(f"No available models found: {model_names}")
    
    @staticmethod
    def get_llm_names(llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM, str, List], 
                      target_model_type: Optional[str] = None) -> List[str]:
        """
        获取 LLM 的模型名称列表
        
        Args:
            llm: LLM 实例或模型名称
            target_model_type: 目标模型类型（可选）
            
        Returns:
            模型名称列表
        """
        if target_model_type is None:
            if isinstance(llm, list):
                return [_llm.default_model_name for _llm in llm if hasattr(_llm, 'default_model_name') and _llm.default_model_name]
            elif isinstance(llm, str):
                return llm.split(",") if llm else []
            return [llm.default_model_name] if hasattr(llm, 'default_model_name') and llm.default_model_name else []
        
        # 处理有 target_model_type 的情况
        if not isinstance(llm, (str, list)) and hasattr(llm, 'get_sub_client'):
            llms = llm.get_sub_client(target_model_type)
            
            if llms is None:
                # 回退到默认处理
                if isinstance(llm, list):
                    return [_llm.default_model_name for _llm in llm if hasattr(_llm, 'default_model_name') and _llm.default_model_name]
                return [llm.default_model_name] if hasattr(llm, 'default_model_name') and llm.default_model_name else []
            elif isinstance(llms, list):
                return [_llm.default_model_name for _llm in llms if hasattr(_llm, 'default_model_name') and _llm.default_model_name]
            elif isinstance(llms, str) and llms:
                return llms.split(",")
            else:
                return [llms.default_model_name] if hasattr(llms, 'default_model_name') and llms.default_model_name else []
        
        return [] 