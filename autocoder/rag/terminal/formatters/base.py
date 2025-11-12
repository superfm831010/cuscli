"""
格式化器基类和工具函数
"""


def format_rag_output(result_generator, contexts, output_format: str):
    """
    统一的RAG输出格式化接口
    
    Args:
        result_generator: RAG返回的生成器 (产生 (chunk, meta) 元组)
        contexts: 使用的上下文文档列表
        output_format: 输出格式 (text/json/stream-json)
    """
    # 延迟导入避免循环依赖
    if output_format == "text":
        from .text import TextFormatter
        formatter = TextFormatter()
    elif output_format == "json":
        from .json_format import JSONFormatter
        formatter = JSONFormatter()
    elif output_format == "stream-json":
        from .stream_json import StreamJSONFormatter
        formatter = StreamJSONFormatter()
    else:
        raise ValueError(f"不支持的输出格式: {output_format}")
    
    formatter.format(result_generator, contexts)


def detect_stage_from_reasoning(reasoning_content: str) -> str:
    """
    根据 reasoning_content 检测当前处理阶段

    Args:
        reasoning_content: 推理内容（通常包含阶段提示信息）

    Returns:
        阶段类型: retrieval/filtering/chunking/generation/processing
    """
    if not reasoning_content:
        return "processing"

    content_lower = reasoning_content.lower()

    # 检测文档检索阶段
    if (
        "rag_processing" in content_lower
        or "searching" in content_lower
        or "搜索" in reasoning_content
    ):
        return "retrieval"

    # 检测文档过滤阶段
    if "filter" in content_lower or "过滤" in reasoning_content:
        return "filtering"

    # 检测文档分块阶段
    if "chunk" in content_lower or "分块" in reasoning_content:
        return "chunking"

    # 检测答案生成阶段
    if (
        "thinking" in content_lower
        or "send_to_model" in reasoning_content
        or "model" in reasoning_content
    ):
        return "generation"

    return "processing"
