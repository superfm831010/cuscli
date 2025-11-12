"""
Git 平台配置管理模块

提供 GitHub 和 GitLab 配置的统一管理功能。
"""
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from loguru import logger


# 加密密钥管理
def _get_or_create_key() -> bytes:
    """获取或创建加密密钥"""
    key_file = Path.home() / ".auto-coder" / "keys" / ".platform_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        return key_file.read_bytes()
    else:
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        key_file.chmod(0o600)  # 仅所有者可读写
        return key


_CIPHER = Fernet(_get_or_create_key())


def _encrypt(text: str) -> str:
    """加密文本"""
    return _CIPHER.encrypt(text.encode()).decode()


def _decrypt(encrypted: str) -> str:
    """解密文本"""
    try:
        return _CIPHER.decrypt(encrypted.encode()).decode()
    except Exception as e:
        logger.error(f"解密失败: {e}")
        return ""


@dataclass
class GitPlatformConfig:
    """Git 平台配置"""
    name: str                           # 配置名称（如"公司GitLab"）
    platform: str                       # 平台类型: github/gitlab
    base_url: str                       # API 基础 URL
    token: str                          # 访问令牌
    verify_ssl: bool = True             # 是否验证 SSL
    timeout: int = 30                   # 超时时间（秒）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_tested: Optional[str] = None   # 最后测试时间

    def to_dict(self, encrypt_token: bool = True) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        data = asdict(self)
        if encrypt_token and self.token:
            data['token'] = _encrypt(self.token)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], decrypt_token: bool = True) -> 'GitPlatformConfig':
        """从字典创建（用于反序列化）"""
        data = data.copy()
        if decrypt_token and data.get('token'):
            data['token'] = _decrypt(data['token'])
        return cls(**data)

    def update_last_tested(self):
        """更新最后测试时间"""
        self.last_tested = datetime.now().isoformat()


class GitPlatformManager:
    """Git 平台配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为插件配置文件
        """
        self.config_file = config_file
        self.configs: Dict[str, Dict[str, GitPlatformConfig]] = {
            "github": {},
            "gitlab": {}
        }
        self.current_platform: str = "github"  # 默认平台
        self.current_config: Dict[str, str] = {
            "github": "",
            "gitlab": ""
        }

        if self.config_file:
            self.load_configs()

    def load_configs(self) -> bool:
        """
        从文件加载配置

        Returns:
            bool: 是否成功加载
        """
        if not self.config_file or not os.path.exists(self.config_file):
            return False

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载平台配置
            platforms_data = data.get('platforms', {})
            for platform, configs in platforms_data.items():
                if platform not in self.configs:
                    self.configs[platform] = {}
                for name, config_data in configs.items():
                    self.configs[platform][name] = GitPlatformConfig.from_dict(
                        config_data, decrypt_token=True
                    )

            # 加载当前选择
            self.current_platform = data.get('current_platform', 'github')
            self.current_config = data.get('current_config', {"github": "", "gitlab": ""})

            logger.info(f"已加载 Git 平台配置: {sum(len(c) for c in self.configs.values())} 个配置")
            return True

        except Exception as e:
            logger.error(f"加载 Git 平台配置失败: {e}")
            return False

    def save_configs(self) -> bool:
        """
        保存配置到文件

        Returns:
            bool: 是否成功保存
        """
        if not self.config_file:
            return False

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # 构建保存数据
            platforms_data = {}
            for platform, configs in self.configs.items():
                platforms_data[platform] = {
                    name: config.to_dict(encrypt_token=True)
                    for name, config in configs.items()
                }

            data = {
                'current_platform': self.current_platform,
                'current_config': self.current_config,
                'platforms': platforms_data
            }

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Git 平台配置已保存到: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存 Git 平台配置失败: {e}")
            return False

    def add_config(self, config: GitPlatformConfig) -> bool:
        """
        添加新配置

        Args:
            config: 配置对象

        Returns:
            bool: 是否成功添加
        """
        if config.platform not in self.configs:
            logger.error(f"不支持的平台: {config.platform}")
            return False

        if config.name in self.configs[config.platform]:
            logger.warning(f"配置 '{config.name}' 已存在，将被覆盖")

        self.configs[config.platform][config.name] = config

        # 如果是该平台的第一个配置，设为默认
        if not self.current_config.get(config.platform):
            self.current_config[config.platform] = config.name

        self.save_configs()
        logger.info(f"已添加 {config.platform} 配置: {config.name}")
        return True

    def update_config(self, platform: str, name: str, **updates) -> bool:
        """
        更新配置

        Args:
            platform: 平台类型
            name: 配置名称
            **updates: 要更新的字段

        Returns:
            bool: 是否成功更新
        """
        config = self.get_config(platform, name)
        if not config:
            logger.error(f"配置不存在: {platform}/{name}")
            return False

        # 更新字段
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.save_configs()
        logger.info(f"已更新 {platform} 配置: {name}")
        return True

    def delete_config(self, platform: str, name: str) -> bool:
        """
        删除配置

        Args:
            platform: 平台类型
            name: 配置名称

        Returns:
            bool: 是否成功删除
        """
        if platform not in self.configs:
            return False

        if name not in self.configs[platform]:
            logger.warning(f"配置不存在: {platform}/{name}")
            return False

        del self.configs[platform][name]

        # 如果删除的是当前配置，清除当前配置
        if self.current_config.get(platform) == name:
            # 尝试选择该平台的其他配置
            remaining = list(self.configs[platform].keys())
            self.current_config[platform] = remaining[0] if remaining else ""

        self.save_configs()
        logger.info(f"已删除 {platform} 配置: {name}")
        return True

    def get_config(self, platform: str, name: str) -> Optional[GitPlatformConfig]:
        """
        获取配置

        Args:
            platform: 平台类型
            name: 配置名称

        Returns:
            GitPlatformConfig: 配置对象，不存在返回 None
        """
        return self.configs.get(platform, {}).get(name)

    def list_configs(self, platform: str) -> List[GitPlatformConfig]:
        """
        列出指定平台的所有配置

        Args:
            platform: 平台类型

        Returns:
            List[GitPlatformConfig]: 配置列表
        """
        return list(self.configs.get(platform, {}).values())

    def get_current_config(self) -> Optional[GitPlatformConfig]:
        """
        获取当前激活的配置

        Returns:
            GitPlatformConfig: 当前配置对象，未设置返回 None
        """
        config_name = self.current_config.get(self.current_platform)
        if not config_name:
            return None
        return self.get_config(self.current_platform, config_name)

    def switch_platform(self, platform: str, config_name: Optional[str] = None) -> Optional[GitPlatformConfig]:
        """
        切换平台

        Args:
            platform: 目标平台
            config_name: 配置名称（可选，默认使用该平台的当前配置）

        Returns:
            GitPlatformConfig: 切换后的配置对象，失败返回 None
        """
        if platform not in self.configs:
            logger.error(f"不支持的平台: {platform}")
            return None

        # 如果未指定配置名，使用该平台的当前配置
        if not config_name:
            config_name = self.current_config.get(platform)

        # 如果该平台没有配置，返回 None
        if not config_name or config_name not in self.configs[platform]:
            logger.error(f"平台 {platform} 没有可用的配置")
            return None

        # 切换平台和配置
        self.current_platform = platform
        self.current_config[platform] = config_name

        self.save_configs()

        config = self.get_config(platform, config_name)
        logger.info(f"已切换到 {platform}/{config_name}")
        return config

    def has_config(self, platform: str) -> bool:
        """
        检查平台是否有配置

        Args:
            platform: 平台类型

        Returns:
            bool: 是否有配置
        """
        return len(self.configs.get(platform, {})) > 0
