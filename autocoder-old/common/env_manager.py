"""
环境变量管理模块

该模块提供了一个统一的环境变量管理接口，方便项目中各个组件获取和使用环境变量。
支持环境变量的获取、默认值设置、类型转换等功能。
"""

import os
from typing import Optional, Union, Dict, Any
from enum import Enum


class Environment(Enum):
    """环境类型枚举"""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    DEV = "dev"  # development 的简写
    PROD = "prod"  # production 的简写
    

class EnvManager:
    """环境变量管理器
    
    提供统一的环境变量访问接口，支持类型转换和默认值设置。
    """
    
    # 预定义的环境变量配置
    ENV_CONFIGS = {
        "AUTO_CODER_ENV": {
            "description": "当前运行环境，支持 production/prod 或 development/dev",
            "default": "development",
            "type": str
        },
        # 可以在这里添加更多需要管理的环境变量
    }
    
    @classmethod
    def get_environment(cls) -> Environment:
        """获取当前运行环境
        
        Returns:
            Environment: 当前环境类型
        """
        env_value = cls.get_env("AUTO_CODER_ENV", "development").lower()
        
        # 标准化环境值
        if env_value in ["production", "prod"]:
            return Environment.PRODUCTION
        elif env_value in ["development", "dev"]:
            return Environment.DEVELOPMENT
        else:
            # 默认返回开发环境
            return Environment.DEVELOPMENT
    
    @classmethod
    def is_production(cls) -> bool:
        """判断是否为生产环境
        
        Returns:
            bool: True 如果是生产环境，False 否则
        """
        return cls.get_environment() == Environment.PRODUCTION
    
    @classmethod
    def is_development(cls) -> bool:
        """判断是否为开发环境
        
        Returns:
            bool: True 如果是开发环境，False 否则
        """
        return cls.get_environment() == Environment.DEVELOPMENT
    
    @classmethod
    def get_env(cls, key: str, default: Optional[Union[str, int, float, bool]] = None) -> Any:
        """获取环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值，如果环境变量不存在则返回此值
            
        Returns:
            Any: 环境变量的值，类型取决于默认值类型
        """
        value = os.environ.get(key)
        
        if value is None:
            return default
        
        # 根据默认值类型进行类型转换
        if default is not None:
            if isinstance(default, bool):
                return cls._str_to_bool(value)
            elif isinstance(default, int):
                try:
                    return int(value)
                except ValueError:
                    return default
            elif isinstance(default, float):
                try:
                    return float(value)
                except ValueError:
                    return default
        
        return value
    
    @classmethod
    def get_env_bool(cls, key: str, default: bool = False) -> bool:
        """获取布尔类型环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            bool: 环境变量的布尔值
        """
        value = os.environ.get(key)
        if value is None:
            return default
        return cls._str_to_bool(value)
    
    @classmethod
    def get_env_int(cls, key: str, default: int = 0) -> int:
        """获取整数类型环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            int: 环境变量的整数值
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    @classmethod
    def get_env_float(cls, key: str, default: float = 0.0) -> float:
        """获取浮点数类型环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            float: 环境变量的浮点数值
        """
        value = os.environ.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    @classmethod
    def set_env(cls, key: str, value: Union[str, int, float, bool]) -> None:
        """设置环境变量
        
        Args:
            key: 环境变量名
            value: 环境变量值
        """
        os.environ[key] = str(value)
    
    @classmethod
    def has_env(cls, key: str) -> bool:
        """检查环境变量是否存在
        
        Args:
            key: 环境变量名
            
        Returns:
            bool: True 如果环境变量存在，False 否则
        """
        return key in os.environ
    
    @classmethod
    def get_all_managed_envs(cls) -> Dict[str, Any]:
        """获取所有被管理的环境变量及其当前值
        
        Returns:
            Dict[str, Any]: 环境变量名到值的映射
        """
        result = {}
        for key, config in cls.ENV_CONFIGS.items():
            result[key] = cls.get_env(key, config.get("default"))
        return result
    
    @classmethod
    def get_env_info(cls) -> Dict[str, Any]:
        """获取环境信息摘要
        
        Returns:
            Dict[str, Any]: 包含环境信息的字典
        """
        return {
            "environment": cls.get_environment().value,
            "is_production": cls.is_production(),
            "is_development": cls.is_development(),
            "managed_envs": cls.get_all_managed_envs()
        }
    
    @staticmethod
    def _str_to_bool(value: str) -> bool:
        """将字符串转换为布尔值
        
        Args:
            value: 字符串值
            
        Returns:
            bool: 转换后的布尔值
        """
        if isinstance(value, bool):
            return value
        
        value_lower = value.lower().strip()
        
        # True 值
        if value_lower in ("true", "1", "yes", "on", "y", "t"):
            return True
        # False 值
        elif value_lower in ("false", "0", "no", "off", "n", "f", ""):
            return False
        else:
            # 其他值默认为 True（非空字符串）
            return bool(value.strip())


# 便捷函数，直接使用类方法
def get_environment() -> Environment:
    """获取当前运行环境"""
    return EnvManager.get_environment()


def is_production() -> bool:
    """判断是否为生产环境"""
    return EnvManager.is_production()


def is_development() -> bool:
    """判断是否为开发环境"""
    return EnvManager.is_development()


def get_env(key: str, default: Optional[Union[str, int, float, bool]] = None) -> Any:
    """获取环境变量值"""
    return EnvManager.get_env(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔类型环境变量"""
    return EnvManager.get_env_bool(key, default)


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数类型环境变量"""
    return EnvManager.get_env_int(key, default)


def get_env_float(key: str, default: float = 0.0) -> float:
    """获取浮点数类型环境变量"""
    return EnvManager.get_env_float(key, default)


def set_env(key: str, value: Union[str, int, float, bool]) -> None:
    """设置环境变量"""
    return EnvManager.set_env(key, value)


def has_env(key: str) -> bool:
    """检查环境变量是否存在"""
    return EnvManager.has_env(key)


def get_env_info() -> Dict[str, Any]:
    """获取环境信息摘要"""
    return EnvManager.get_env_info()
