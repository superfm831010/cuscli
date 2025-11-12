"""
Version information for cuscli

Cuscli 基于 auto-coder 进行二次开发
"""

__version__ = "1.1.5"
__base_version__ = "2.0.2"  # 基于的 auto-coder 版本
__architecture__ = "terminal"  # 使用的架构

def get_version_info():
    """获取完整的版本信息"""
    return f"cuscli {__version__} (based on auto-coder {__base_version__}, {__architecture__} architecture)"
