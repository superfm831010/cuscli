"""
AutoCoder RAG SDK 工具函数

提供辅助函数，提升SDK的可用性。
"""

from typing import List


def format_contexts_for_display(
    contexts: List[str], max_length: int = 100
) -> List[str]:
    """
    格式化上下文用于显示

    Args:
        contexts: 上下文列表
        max_length: 每个上下文的最大显示长度

    Returns:
        格式化后的上下文列表
    """
    return [
        ctx[:max_length] + "..." if len(ctx) > max_length else ctx for ctx in contexts
    ]


def validate_doc_dir(doc_dir: str) -> bool:
    """
    验证文档目录是否有效

    Args:
        doc_dir: 文档目录路径

    Returns:
        是否有效
    """
    from pathlib import Path

    path = Path(doc_dir)
    return path.exists() and path.is_dir()


def print_response_summary(response) -> None:
    """
    打印响应摘要

    Args:
        response: RAGResponse 对象
    """
    print("=" * 60)
    print("RAG 查询结果")
    print("=" * 60)

    if response.success:
        print(f"\n✅ 查询成功")
        print(f"\n答案:\n{response.answer}")

        if response.contexts:
            print(f"\n参考文档 ({len(response.contexts)}个):")
            for i, ctx in enumerate(response.contexts[:3], 1):  # 只显示前3个
                preview = ctx[:150] + "..." if len(ctx) > 150 else ctx
                print(f"  {i}. {preview}")
            if len(response.contexts) > 3:
                print(f"  ... 还有 {len(response.contexts) - 3} 个文档")
    else:
        print(f"\n❌ 查询失败")
        print(f"错误: {response.error}")

    print("=" * 60)


def create_simple_config(doc_dir: str, **kwargs) -> "RAGConfig":
    """
    创建简化的配置对象

    快捷函数，避免导入 RAGConfig

    Args:
        doc_dir: 文档目录
        **kwargs: 其他配置参数

    Returns:
        RAGConfig 对象

    Example::

        config = create_simple_config("./docs", agentic=True, product_mode="pro")
    """
    from .models import RAGConfig

    return RAGConfig(doc_dir=doc_dir, **kwargs)


if __name__ == "__main__":
    # 测试工具函数
    contexts = ["这是一个很长的文档内容" * 10, "短文档"]
    formatted = format_contexts_for_display(contexts, max_length=50)
    print("格式化上下文测试:")
    for ctx in formatted:
        print(f"  - {ctx}")

    print(f"\n目录验证测试:")
    print(f"  当前目录有效: {validate_doc_dir('.')}")
    print(f"  无效目录: {validate_doc_dir('/nonexistent')}")
