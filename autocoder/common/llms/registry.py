
import os
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from filelock import FileLock

from .schema import LLMModel

# 默认内置模型列表 - 已清空，需要用户手动配置
DEFAULT_MODELS = []


class ModelRegistry:
    """模型注册表，负责模型的持久化和加载（无缓存）"""
    
    def __init__(self, models_json_path: Optional[str] = None):
        self.models_json_path = Path(models_json_path or os.path.expanduser("~/.auto-coder/keys/models.json"))
        
    def _ensure_dir(self):
        """确保目录存在"""
        self.models_json_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _get_lock_path(self, file_path: Path) -> str:
        """获取锁文件路径"""
        return str(file_path) + ".lock"
        
    def _load_api_key_from_file(self, model: LLMModel) -> LLMModel:
        """从文件加载 API 密钥"""
        # 设置 base_keys_dir 为配置文件所在目录
        model.base_keys_dir = str(self.models_json_path.parent)
        
        # 如果 api_key 存在但 api_key_path 不存在，生成 api_key_path
        if model.api_key and not model.api_key_path:
            model.api_key_path = model.name.replace("/", "_")
        
        # 如果 api_key_path 存在，以它为准读取文件
        if model.api_key_path:
            api_key_file = self.models_json_path.parent / model.api_key_path
            if api_key_file.exists():
                with FileLock(self._get_lock_path(api_key_file), timeout=5):
                    model.api_key = api_key_file.read_text(encoding="utf-8").strip()
        return model
    
    def load(self) -> List[LLMModel]:
        """每次都重新加载模型列表，合并默认模型和自定义模型"""
        self._ensure_dir()
        
        # 从默认模型开始
        models_dict = {}
        for model_data in DEFAULT_MODELS:
            # 添加 base_keys_dir 到模型数据
            model_data_with_keys_dir = model_data.copy()
            model_data_with_keys_dir["base_keys_dir"] = str(self.models_json_path.parent)
            model = LLMModel(**model_data_with_keys_dir)
            models_dict[model.name] = model
        
        # 如果配置文件存在，读取并合并
        if self.models_json_path.exists():
            try:
                with FileLock(self._get_lock_path(self.models_json_path), timeout=5):
                    with open(self.models_json_path, 'r', encoding='utf-8') as f:
                        custom_models_data = json.load(f)
                
                # 自定义模型会覆盖同名的默认模型
                for model_data in custom_models_data:
                    # 兼容旧版本：添加新字段的默认值
                    if "context_window" not in model_data:
                        model_data["context_window"] = 128*1024
                    if "max_output_tokens" not in model_data:
                        model_data["max_output_tokens"] = 8096
                    if "provider" not in model_data:
                        model_data["provider"] = None
                    
                    # 添加 base_keys_dir
                    model_data["base_keys_dir"] = str(self.models_json_path.parent)
                        
                    model = LLMModel(**model_data)
                    models_dict[model.name] = model
                    
            except (json.JSONDecodeError, Exception) as e:
                # JSON 无效时，使用默认模型并重新保存
                print(f"警告：加载 models.json 失败: {e}，使用默认模型")
                self.save(list(models_dict.values()))
        else:
            # 文件不存在，创建默认配置
            self.save(list(models_dict.values()))
        
        # 加载 API 密钥
        models = []
        for model in models_dict.values():
            models.append(self._load_api_key_from_file(model))
            
        return models
    
    def save(self, models: List[LLMModel]) -> None:
        """使用 filelock 保存模型列表到文件"""
        self._ensure_dir()
        
        # 转换为字典列表，不包含 api_key
        models_data = [model.dict() for model in models]
        
        # 使用 filelock 写入，超时5秒
        lock_path = self._get_lock_path(self.models_json_path)
        with FileLock(lock_path, timeout=5):
            with open(self.models_json_path, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, indent=2, ensure_ascii=False)
    
    def get(self, name: str) -> Optional[LLMModel]:
        """根据名称获取模型（每次重新加载）"""
        models = self.load()
        for model in models:
            if model.name == name.strip():
                return model
        return None
    
    def get_all(self) -> Dict[str, LLMModel]:
        """获取所有模型（每次重新加载）"""
        models = self.load()
        return {model.name: model for model in models}
    
    def add_or_update(self, model: LLMModel) -> None:
        """添加或更新模型"""
        # 先加载所有模型
        models = self.load()
        
        # 查找是否存在同名模型
        updated = False
        for i, existing_model in enumerate(models):
            if existing_model.name == model.name:
                models[i] = model
                updated = True
                break
        
        # 如果没有找到同名模型，添加新模型
        if not updated:
            models.append(model)
        
        # 保存更新后的模型列表
        self.save(models)
    
    def save_api_key(self, model_name: str, api_key: str) -> bool:
        """保存 API 密钥到文件"""
        model = self.get(model_name)
        if not model:
            return False
            
        # 确保有 api_key_path
        if not model.api_key_path:
            model.api_key_path = model_name.replace("/", "_")
        
        # 保存密钥到文件
        api_key_file = self.models_json_path.parent / model.api_key_path
        
        # 使用 filelock 保存密钥，超时5秒
        lock_path = self._get_lock_path(api_key_file)
        with FileLock(lock_path, timeout=5):
            api_key_file.write_text(api_key.strip(), encoding="utf-8")
        
        # 更新模型（清除内存中的 api_key）
        model.api_key = None
        self.add_or_update(model)
        
        return True
    
    def remove_model(self, model_name: str) -> bool:
        """
        删除模型

        Args:
            model_name: 要删除的模型名称

        Returns:
            bool: 是否成功删除
        """
        # 先检查模型是否存在
        model = self.get(model_name)
        if not model:
            return False

        # 加载所有模型
        models = self.load()
        
        # 过滤掉要删除的模型
        filtered_models = [m for m in models if m.name != model_name]
        
        # 如果模型数量没有变化，说明模型不存在于自定义模型中
        if len(filtered_models) == len(models):
            return False
        
        # 删除 API 密钥文件（如果存在）
        if model.api_key_path:
            api_key_file = self.models_json_path.parent / model.api_key_path
            if api_key_file.exists():
                try:
                    # 使用 filelock 删除密钥文件
                    lock_path = self._get_lock_path(api_key_file)
                    with FileLock(lock_path, timeout=5):
                        api_key_file.unlink()
                except OSError:
                    # 忽略删除密钥文件失败的情况
                    pass
        
        # 保存更新后的模型列表
        self.save(filtered_models)
        
        return True
