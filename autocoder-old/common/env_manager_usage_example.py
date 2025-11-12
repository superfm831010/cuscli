
#!/usr/bin/env python3
"""
环境变量管理模块使用示例

展示如何在项目中使用 env_manager 模块
"""

from env_manager import (
    # 类和枚举
    EnvManager, Environment,
    # 便捷函数
    get_environment, is_production, is_development,
    get_env, get_env_bool, get_env_int, get_env_float,
    set_env, has_env, get_env_info
)


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 1. 检查当前环境
    current_env = get_environment()
    print(f"当前环境: {current_env.value}")
    
    # 2. 根据环境执行不同逻辑
    if is_production():
        print("运行在生产环境，启用严格模式")
        # 生产环境的特殊配置
        debug_mode = False
        log_level = "INFO"
    else:
        print("运行在开发环境，启用调试模式")
        # 开发环境的特殊配置
        debug_mode = True
        log_level = "DEBUG"
    
    print(f"调试模式: {debug_mode}")
    print(f"日志级别: {log_level}")
    print()


def example_env_configuration():
    """环境变量配置示例"""
    print("=== 环境变量配置示例 ===")
    
    # 获取各种类型的环境变量，带默认值
    database_url = get_env("DATABASE_URL", "sqlite:///default.db")
    max_connections = get_env_int("MAX_CONNECTIONS", 10)
    enable_cache = get_env_bool("ENABLE_CACHE", True)
    timeout = get_env_float("TIMEOUT", 30.0)
    
    print(f"数据库URL: {database_url}")
    print(f"最大连接数: {max_connections}")
    print(f"启用缓存: {enable_cache}")
    print(f"超时时间: {timeout}秒")
    print()


def example_dynamic_configuration():
    """动态配置示例"""
    print("=== 动态配置示例 ===")
    
    # 根据环境动态调整配置
    if is_production():
        # 生产环境配置
        worker_count = get_env_int("WORKER_COUNT", 4)
        enable_debug = False
        cache_timeout = get_env_int("CACHE_TIMEOUT", 3600)
    else:
        # 开发环境配置
        worker_count = get_env_int("WORKER_COUNT", 1)
        enable_debug = get_env_bool("DEBUG", True)
        cache_timeout = get_env_int("CACHE_TIMEOUT", 60)
    
    print(f"工作进程数: {worker_count}")
    print(f"调试模式: {enable_debug}")
    print(f"缓存超时: {cache_timeout}秒")
    print()


def example_feature_flags():
    """功能开关示例"""
    print("=== 功能开关示例 ===")
    
    # 使用环境变量控制功能开关
    features = {
        "NEW_UI": get_env_bool("FEATURE_NEW_UI", False),
        "EXPERIMENTAL_API": get_env_bool("FEATURE_EXPERIMENTAL_API", False),
        "ANALYTICS": get_env_bool("FEATURE_ANALYTICS", is_production()),  # 生产环境默认开启
        "DEBUG_TOOLBAR": get_env_bool("FEATURE_DEBUG_TOOLBAR", is_development()),  # 开发环境默认开启
    }
    
    print("功能开关状态:")
    for feature, enabled in features.items():
        status = "启用" if enabled else "禁用"
        print(f"  {feature}: {status}")
    print()


def example_configuration_validation():
    """配置验证示例"""
    print("=== 配置验证示例 ===")
    
    # 检查必需的环境变量
    required_vars = ["API_KEY", "SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not has_env(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"警告: 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请设置这些环境变量后重新启动应用")
    else:
        print("所有必需的环境变量都已设置")
    
    # 验证环境变量值的有效性
    max_retries = get_env_int("MAX_RETRIES", 3)
    if max_retries < 1 or max_retries > 10:
        print(f"警告: MAX_RETRIES 值 {max_retries} 不在有效范围内 (1-10)")
    
    print()


def example_logging_configuration():
    """日志配置示例"""
    print("=== 日志配置示例 ===")
    
    # 根据环境配置日志
    log_config = {
        "level": get_env("LOG_LEVEL", "INFO" if is_production() else "DEBUG"),
        "format": get_env("LOG_FORMAT", "json" if is_production() else "console"),
        "output": get_env("LOG_OUTPUT", "file" if is_production() else "console"),
        "max_size": get_env_int("LOG_MAX_SIZE", 100),  # MB
        "backup_count": get_env_int("LOG_BACKUP_COUNT", 5),
    }
    
    print("日志配置:")
    for key, value in log_config.items():
        print(f"  {key}: {value}")
    print()


def example_service_configuration():
    """服务配置示例"""
    print("=== 服务配置示例 ===")
    
    # Web 服务配置
    web_config = {
        "host": get_env("HOST", "0.0.0.0" if is_production() else "127.0.0.1"),
        "port": get_env_int("PORT", 8000),
        "workers": get_env_int("WORKERS", 4 if is_production() else 1),
        "reload": get_env_bool("RELOAD", is_development()),
        "access_log": get_env_bool("ACCESS_LOG", is_production()),
    }
    
    print("Web服务配置:")
    for key, value in web_config.items():
        print(f"  {key}: {value}")
    print()


def example_environment_info():
    """环境信息示例"""
    print("=== 环境信息示例 ===")
    
    # 获取完整的环境信息
    env_info = get_env_info()
    print("完整环境信息:")
    for key, value in env_info.items():
        print(f"  {key}: {value}")
    print()


def main():
    """主函数"""
    print("环境变量管理模块使用示例")
    print("=" * 50)
    
    example_basic_usage()
    example_env_configuration()
    example_dynamic_configuration()
    example_feature_flags()
    example_configuration_validation()
    example_logging_configuration()
    example_service_configuration()
    example_environment_info()
    
    print("示例演示完成!")


if __name__ == "__main__":
    # 设置一些示例环境变量
    import os
    os.environ.update({
        "DATABASE_URL": "postgresql://user:pass@localhost/mydb",
        "MAX_CONNECTIONS": "20",
        "ENABLE_CACHE": "true",
        "TIMEOUT": "45.5",
        "FEATURE_NEW_UI": "true",
        "API_KEY": "your-api-key-here",
        "SECRET_KEY": "your-secret-key-here",
        "LOG_LEVEL": "INFO",
        "PORT": "8080",
    })
    
    main()

