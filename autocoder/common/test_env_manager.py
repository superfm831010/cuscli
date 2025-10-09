
#!/usr/bin/env python3
"""
环境变量管理模块测试脚本

用于测试 env_manager.py 模块的各项功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入模块
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.autocoder.common.env_manager import (
    EnvManager, Environment,
    get_environment, is_production, is_development,
    get_env, get_env_bool, get_env_int, get_env_float,
    set_env, has_env, get_env_info
)


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    # 测试默认环境
    print(f"默认环境: {get_environment()}")
    print(f"是否为生产环境: {is_production()}")
    print(f"是否为开发环境: {is_development()}")
    print()


def test_environment_detection():
    """测试环境检测功能"""
    print("=== 测试环境检测功能 ===")
    
    # 保存原始环境变量
    original_env = os.environ.get("AUTO_CODER_ENV")
    
    # 测试生产环境
    test_cases = [
        ("production", Environment.PRODUCTION),
        ("prod", Environment.PRODUCTION),
        ("PRODUCTION", Environment.PRODUCTION),
        ("development", Environment.DEVELOPMENT),
        ("dev", Environment.DEVELOPMENT),
        ("DEV", Environment.DEVELOPMENT),
        ("unknown", Environment.DEVELOPMENT),  # 未知值默认为开发环境
    ]
    
    for env_value, expected in test_cases:
        set_env("AUTO_CODER_ENV", env_value)
        result = get_environment()
        status = "✓" if result == expected else "✗"
        print(f"{status} 设置 AUTO_CODER_ENV={env_value}, 期望: {expected.value}, 实际: {result.value}")
    
    # 恢复原始环境变量
    if original_env is not None:
        os.environ["AUTO_CODER_ENV"] = original_env
    elif "AUTO_CODER_ENV" in os.environ:
        del os.environ["AUTO_CODER_ENV"]
    
    print()


def test_type_conversion():
    """测试类型转换功能"""
    print("=== 测试类型转换功能 ===")
    
    # 测试布尔值转换
    bool_test_cases = [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("", False),
    ]
    
    for value, expected in bool_test_cases:
        set_env("TEST_BOOL", value)
        result = get_env_bool("TEST_BOOL")
        status = "✓" if result == expected else "✗"
        print(f"{status} 布尔值 '{value}' -> {result} (期望: {expected})")
    
    # 测试整数转换
    set_env("TEST_INT", "42")
    result = get_env_int("TEST_INT")
    print(f"{'✓' if result == 42 else '✗'} 整数 '42' -> {result}")
    
    # 测试浮点数转换
    set_env("TEST_FLOAT", "3.14")
    result = get_env_float("TEST_FLOAT")
    print(f"{'✓' if abs(result - 3.14) < 0.001 else '✗'} 浮点数 '3.14' -> {result}")
    
    # 测试无效值的默认值处理
    set_env("TEST_INVALID_INT", "not_a_number")
    result = get_env_int("TEST_INVALID_INT", 999)
    print(f"{'✓' if result == 999 else '✗'} 无效整数使用默认值 -> {result}")
    
    # 清理测试环境变量
    for key in ["TEST_BOOL", "TEST_INT", "TEST_FLOAT", "TEST_INVALID_INT"]:
        if key in os.environ:
            del os.environ[key]
    
    print()


def test_env_management():
    """测试环境变量管理功能"""
    print("=== 测试环境变量管理功能 ===")
    
    # 测试设置和获取
    set_env("TEST_VAR", "test_value")
    result = get_env("TEST_VAR")
    print(f"{'✓' if result == 'test_value' else '✗'} 设置和获取环境变量: {result}")
    
    # 测试环境变量存在性检查
    exists = has_env("TEST_VAR")
    print(f"{'✓' if exists else '✗'} 环境变量存在性检查: {exists}")
    
    # 测试不存在的环境变量
    not_exists = has_env("NON_EXISTENT_VAR")
    print(f"{'✓' if not not_exists else '✗'} 不存在的环境变量检查: {not_exists}")
    
    # 测试默认值
    default_result = get_env("NON_EXISTENT_VAR", "default_value")
    print(f"{'✓' if default_result == 'default_value' else '✗'} 使用默认值: {default_result}")
    
    # 清理测试环境变量
    if "TEST_VAR" in os.environ:
        del os.environ["TEST_VAR"]
    
    print()


def test_env_info():
    """测试环境信息获取功能"""
    print("=== 测试环境信息获取功能 ===")
    
    env_info = get_env_info()
    print("环境信息:")
    for key, value in env_info.items():
        print(f"  {key}: {value}")
    
    print()


def main():
    """主测试函数"""
    print("环境变量管理模块测试")
    print("=" * 50)
    
    test_basic_functionality()
    test_environment_detection()
    test_type_conversion()
    test_env_management()
    test_env_info()
    
    print("测试完成!")


if __name__ == "__main__":
    main()

