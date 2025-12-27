from pydantic import BaseModel, Field, validator
from typing import Optional, Union, Dict, Any
from pathlib import Path


class LLMModel(BaseModel):
    """大语言模型配置数据模型"""

    name: str = Field(..., description="模型唯一标识符，如 'deepseek/v3'")
    description: str = Field(default="", description="模型描述信息")
    model_name: str = Field(..., description="模型实际名称，用于 API 调用")
    model_type: str = Field(..., description="模型类型，如 'saas/openai'")
    base_url: str = Field(..., description="API 基础 URL")
    provider: Optional[str] = Field(
        default=None, description="模型提供商，如 'deepseek', 'openai'"
    )
    is_reasoning: bool = Field(default=False, description="是否为推理模型")
    input_price: float = Field(
        default=0.0, ge=0.0, description="输入价格(美元/百万tokens)"
    )
    output_price: float = Field(
        default=0.0, ge=0.0, description="输出价格(美元/百万tokens)"
    )
    max_output_tokens: int = Field(
        default=8096, gt=0, description="单次响应最大输出tokens"
    )
    context_window: int = Field(
        default=128000, gt=0, description="最大上下文窗口tokens"
    )
    api_key_path: Optional[str] = Field(default=None, description="API密钥文件路径")
    api_key: Optional[str] = Field(default=None, description="API密钥(内存中)")
    base_keys_dir: Optional[str] = Field(
        default=None, description="API密钥基础目录路径"
    )
    thinking: Optional[Union[Dict[str, Any], bool, str]] = Field(
        default=None, description="思考模式配置，支持字典、布尔值或字符串"
    )
    extra_body: Optional[Dict[str, Any]] = Field(
        default=None, description="额外的请求体参数，用于传递自定义参数到 API"
    )

    class Config:
        validate_assignment = True

    @validator("api_key_path", pre=True, always=True)
    def normalize_key_path(cls, v, values):
        """如果没有 api_key_path 但有 api_key，生成默认路径"""
        if not v and values.get("api_key"):
            # 将斜杠转换为下划线，生成合法文件名
            return values["name"].replace("/", "_")
        return v

    def _get_keys_dir(self) -> Path:
        """获取API密钥基础目录"""
        if self.base_keys_dir:
            return Path(self.base_keys_dir)
        return Path.home() / ".auto-coder/keys"

    @property
    def has_api_key(self) -> bool:
        """判断是否已配置密钥"""
        # 如果内存中有 API key
        if self.api_key:
            return True

        # 如果有 api_key_path，检查文件是否存在
        if self.api_key_path:
            key_file = self._get_keys_dir() / self.api_key_path
            return key_file.exists()

        return False

    def get_api_key(self) -> Optional[str]:
        """获取 API 密钥，优先从内存，其次从文件"""
        # 优先使用内存中的 key
        if self.api_key:
            return self.api_key

        # 从文件读取
        if self.api_key_path:
            key_file = self._get_keys_dir() / self.api_key_path
            if key_file.exists():
                return key_file.read_text(encoding="utf-8").strip()

        return None

    def dict(self, *args, **kwargs):
        """覆盖 dict 方法，导出时不包含 api_key 和 base_keys_dir"""
        d = super().dict(*args, **kwargs)
        # 安全考虑：不将 api_key 和 base_keys_dir 序列化到文件
        if "api_key" in d:
            d["api_key"] = None
        if "base_keys_dir" in d:
            d.pop("base_keys_dir", None)
        return d
