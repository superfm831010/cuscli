import byzerllm
from typing import Union, List, Optional, Dict

from .schema import LLMModel
from .registry import ModelRegistry
from .factory import LLMFactory
from .pricing import PricingManager


class LLMManager:
    """大语言模型管理器，统一管理所有 LLM 的配置、实例化和操作"""

    def __init__(self, models_json_path: Optional[str] = None):
        """
        初始化 LLM 管理器

        Args:
            models_json_path: 模型配置文件路径，默认为 ~/.auto-coder/keys/models.json
        """
        self.registry = ModelRegistry(models_json_path)
        self.pricing = PricingManager(self.registry)
        # 立即加载模型以初始化缓存
        self.registry.load()

    def get_model(self, name: str) -> Optional[LLMModel]:
        """
        获取模型配置信息

        Args:
            name: 模型名称

        Returns:
            LLMModel 对象，如果不存在则返回 None
        """
        return self.registry.get(name)

    def get_all_models(self) -> Dict[str, LLMModel]:
        """获取所有模型配置"""
        return self.registry.get_all()

    def get_model_info(self, name: str, product_mode: str) -> Optional[Dict]:
        """
        获取模型信息（兼容旧版本接口）

        Args:
            name: 模型名称
            product_mode: 产品模式（pro 或 lite）

        Returns:
            模型信息字典，如果不存在则返回 None
        """
        if product_mode == "pro":
            # Pro 模式下直接返回 None（与原实现保持一致）
            return None

        model = self.get_model(name)
        if not model:
            return None

        # 转换为字典格式，保持兼容性
        return {
            "name": model.name,
            "description": model.description,
            "model_name": model.model_name,
            "model_type": model.model_type,
            "base_url": model.base_url,
            "provider": model.provider,
            "api_key": model.get_api_key(),
            "is_reasoning": model.is_reasoning,
            "input_price": model.input_price,
            "output_price": model.output_price,
            "max_output_tokens": model.max_output_tokens,
            "context_window": model.context_window,
            "thinking": model.thinking,
        }

    def get_single_llm(
        self, model_names: str, product_mode: str
    ) -> Optional[Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]]:
        """
        根据模型名称和产品模式获取 LLM 实例

        Args:
            model_names: 逗号分隔的模型名称列表
            product_mode: 产品模式（pro 或 lite）

        Returns:
            配置好的 LLM 实例

        Raises:
            ValueError: 当所有指定的模型都无法创建时，包含详细的错误信息
        """
        models = list(self.registry.get_all().values())
        return LLMFactory.create_llm_from_names(model_names, models, product_mode)

    def get_llm_names(
        self,
        llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM, str, List],
        target_model_type: Optional[str] = None,
    ) -> List[str]:
        """
        获取 LLM 的模型名称列表

        Args:
            llm: LLM 实例或模型名称
            target_model_type: 目标模型类型（可选）

        Returns:
            模型名称列表
        """
        return LLMFactory.get_llm_names(llm, target_model_type)

    def add_models(self, models: List[Union[LLMModel, Dict]]) -> None:
        """
        批量添加模型

        Args:
            models: 模型列表，可以是 LLMModel 对象或字典
        """
        for model_data in models:
            if isinstance(model_data, dict):
                # 如果是字典，转换为 LLMModel，设置 base_keys_dir
                model_data_with_keys_dir = model_data.copy()
                model_data_with_keys_dir["base_keys_dir"] = str(
                    self.registry.models_json_path.parent
                )
                model = LLMModel(**model_data_with_keys_dir)
            else:
                model = model_data
                # 确保已有的 LLMModel 对象也设置了 base_keys_dir
                if not model.base_keys_dir:
                    model.base_keys_dir = str(self.registry.models_json_path.parent)

            # 保存 api_key 的副本（如果有的话）
            api_key_to_save = model.api_key

            # 如果有 api_key，设置 api_key_path（如果没有的话）
            if api_key_to_save and not model.api_key_path:
                model.api_key_path = model.name.replace("/", "_")

            # 清除内存中的 api_key，以便正确保存到文件
            model.api_key = None

            # 首先添加模型配置
            self.registry.add_or_update(model)

            # 如果有 api_key，再保存密钥
            if api_key_to_save and model.api_key_path:
                # 使用文件锁保存密钥到文件
                api_key_file = (
                    self.registry.models_json_path.parent / model.api_key_path
                )
                self.registry._ensure_dir()

                # 导入文件锁上下文管理器
                from filelock import FileLock

                with FileLock(self.registry._get_lock_path(api_key_file), timeout=5):
                    with open(api_key_file, "w", encoding="utf-8") as f:
                        f.write(api_key_to_save.strip())

    def update_model_with_api_key(self, name: str, api_key: str) -> bool:
        """
        更新模型的 API 密钥

        Args:
            name: 模型名称
            api_key: API 密钥

        Returns:
            是否成功更新
        """
        return self.registry.save_api_key(name, api_key)

    def update_model(self, name: str, model_data: Dict) -> Optional[LLMModel]:
        """
        更新模型信息

        Args:
            name: 要更新的模型名称
            model_data: 包含新信息的字典

        Returns:
            更新后的模型，如果未找到则返回 None
        """
        model = self.registry.get(name)
        if not model:
            return None

        # 更新字段
        if "description" in model_data:
            model.description = model_data["description"]
        if "model_name" in model_data:
            model.model_name = model_data["model_name"]
        if "model_type" in model_data:
            model.model_type = model_data["model_type"]
        if "base_url" in model_data:
            model.base_url = model_data["base_url"]
        if "provider" in model_data:
            model.provider = model_data["provider"]
        if "is_reasoning" in model_data:
            model.is_reasoning = model_data["is_reasoning"]
        if "input_price" in model_data:
            model.input_price = float(model_data["input_price"])
        if "output_price" in model_data:
            model.output_price = float(model_data["output_price"])
        if "max_output_tokens" in model_data:
            model.max_output_tokens = int(model_data["max_output_tokens"])
        if "context_window" in model_data:
            model.context_window = int(model_data["context_window"])
        if "thinking" in model_data:
            model.thinking = model_data["thinking"]

        # 保存更新
        self.registry.add_or_update(model)

        # 如果提供了 API 密钥，单独处理
        if "api_key" in model_data and model_data["api_key"]:
            self.update_model_with_api_key(name, model_data["api_key"])

        return model

    def has_key(self, name: str) -> bool:
        """
        检查模型是否已配置密钥

        Args:
            name: 模型名称

        Returns:
            是否已配置密钥
        """
        model = self.get_model(name)
        return model.has_api_key if model else False

    def check_model_exists(self, name: str) -> bool:
        """
        检查模型是否存在

        Args:
            name: 模型名称

        Returns:
            是否存在
        """
        return self.get_model(name) is not None

    # 价格管理相关方法
    def update_input_price(self, name: str, price: float) -> bool:
        """更新模型输入价格"""
        return self.pricing.update_input_price(name, price)

    def update_output_price(self, name: str, price: float) -> bool:
        """更新模型输出价格"""
        return self.pricing.update_output_price(name, price)

    def update_price(
        self,
        name: str,
        input_price: Optional[float] = None,
        output_price: Optional[float] = None,
    ) -> bool:
        """同时更新输入和输出价格"""
        return self.pricing.update_prices(name, input_price, output_price)

    def get_cost_estimate(
        self, name: str, input_tokens: int, output_tokens: int
    ) -> Optional[float]:
        """估算使用成本"""
        return self.pricing.get_cost_estimate(name, input_tokens, output_tokens)

    def remove_model(self, name: str) -> bool:
        """
        删除模型

        Args:
            name: 模型名称

        Returns:
            是否成功删除
        """
        return self.registry.remove_model(name)
