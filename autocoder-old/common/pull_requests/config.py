"""
Pull Request 配置管理
"""
import os
from typing import Dict, Any, Optional
from loguru import logger
from .models import PRConfig, PlatformType
from .exceptions import ConfigurationError


def _convert_git_config_to_pr_config(git_config, **overrides) -> PRConfig:
    """
    将 GitPlatformConfig 转换为 PRConfig

    Args:
        git_config: GitPlatformConfig 对象
        **overrides: 配置覆盖参数

    Returns:
        PRConfig 对象
    """
    config_dict = {
        'platform': PlatformType(git_config.platform),
        'token': git_config.token,
        'base_url': git_config.base_url,
        'timeout': git_config.timeout,
        'verify_ssl': git_config.verify_ssl,
    }

    # 应用覆盖参数
    config_dict.update(overrides)

    return PRConfig(**config_dict)


def get_config(platform: str, **overrides) -> PRConfig:
    """
    获取平台配置

    优先级：
    1. GitPlatformManager 的当前配置（如果可用）
    2. 环境变量配置（后备方案）

    Args:
        platform: 平台名称
        **overrides: 配置覆盖参数

    Returns:
        配置对象
    """
    # 尝试从 GitPlatformManager 获取配置（优先）
    try:
        from autocoder.common.git_platform_config import GitPlatformManager

        # 创建管理器实例（会自动加载配置文件）
        manager = GitPlatformManager()

        # 如果当前平台匹配，使用当前配置
        if manager.current_platform == platform:
            git_config = manager.get_current_config()
            if git_config:
                logger.info(f"从 GitPlatformManager 获取 {platform} 配置: {git_config.name}")
                return _convert_git_config_to_pr_config(git_config, **overrides)

        # 如果当前平台不匹配，但该平台有配置，使用该平台的第一个配置
        if manager.has_config(platform):
            configs = manager.list_configs(platform)
            if configs:
                git_config = configs[0]
                logger.info(f"从 GitPlatformManager 获取 {platform} 配置: {git_config.name}")
                return _convert_git_config_to_pr_config(git_config, **overrides)
    except Exception as e:
        logger.debug(f"无法从 GitPlatformManager 获取配置: {e}, 将使用环境变量")

    # 后备方案：从环境变量加载配置
    env_config = _load_from_env(platform)

    # 合并配置
    merged_config = {}
    if env_config:
        merged_config.update(env_config)
    merged_config.update(overrides)

    # 验证必需的配置
    if 'token' not in merged_config:
        raise ConfigurationError(
            f"平台 {platform} 缺少必需的 token 配置。\n"
            f"请通过以下方式之一配置：\n"
            f"1. 使用 Git 插件配置: /git /{platform} /setup\n"
            f"2. 设置环境变量: {_get_token_env_name(platform)}"
        )

    logger.info(f"从环境变量获取 {platform} 配置")
    return PRConfig(platform=PlatformType(platform), **merged_config)


def _get_token_env_name(platform: str) -> str:
    """获取平台对应的环境变量名"""
    env_mappings = {
        'github': 'GITHUB_TOKEN',
        'gitlab': 'GITLAB_TOKEN',
        'gitee': 'GITEE_TOKEN',
        'gitcode': 'GITCODE_TOKEN'
    }
    return env_mappings.get(platform, f'{platform.upper()}_TOKEN')


def _load_from_env(platform: str) -> Dict[str, Any]:
    """从环境变量加载配置"""
    env_mappings = {
        'github': {
            'token': 'GITHUB_TOKEN',
            'base_url': 'GITHUB_BASE_URL'
        },
        'gitlab': {
            'token': 'GITLAB_TOKEN',
            'base_url': 'GITLAB_BASE_URL'
        },
        'gitee': {
            'token': 'GITEE_TOKEN',
            'base_url': 'GITEE_BASE_URL'
        },
        'gitcode': {
            'token': 'GITCODE_TOKEN',
            'base_url': 'GITCODE_BASE_URL'
        }
    }

    mapping = env_mappings.get(platform, {})
    config = {}

    for key, env_var in mapping.items():
        value = os.getenv(env_var)
        if value:
            config[key] = value

    return config