from byzerllm.utils.client import EventCallbackResult,EventName
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import FormattedText
from typing import List,Dict,Any
from loguru import logger
from autocoder.db.store import Store


def token_counter_interceptor(llm,model,response) -> EventCallbackResult:
    """
    Token 统计拦截器，统计模型调用的 token 使用情况

    Args:
        llm: LLM 实例
        model: 模型名称
        response: 模型响应（可能为 None、空列表或包含 SingleOutput 对象的列表）

    Returns:
        EventCallbackResult: (True, None) 表示继续执行
    """
    store = Store()

    # 检查响应是否为空
    if not response:
        logger.warning(f"模型 {model} 响应为 None，跳过 token 统计")
        return True, None

    if not isinstance(response, list) or len(response) == 0:
        logger.warning(f"模型 {model} 响应为空列表，跳过 token 统计")
        return True, None

    try:
        v = response[0]

        # 处理字典格式的响应
        if isinstance(v, dict):
            if "metadata" in v:
                metadata = v["metadata"]
                input_tokens_count = metadata.get("input_tokens_count", 0)
                generated_tokens_count = metadata.get("generated_tokens_count", 0)
                store.update_token_counter(
                    project=None,
                    input_tokens_count=input_tokens_count,
                    generated_tokens_count=generated_tokens_count
                )
                logger.debug(f"{model} token 统计 - 输入: {input_tokens_count}, 生成: {generated_tokens_count}")
        # 处理 SingleOutput 对象格式的响应
        elif hasattr(v, 'meta'):
            meta = v.meta
            if meta:
                input_tokens_count = meta.get("input_tokens_count", 0)
                generated_tokens_count = meta.get("generated_tokens_count", 0)
                store.update_token_counter(
                    project=None,
                    input_tokens_count=input_tokens_count,
                    generated_tokens_count=generated_tokens_count
                )
                logger.debug(f"{model} token 统计 - 输入: {input_tokens_count}, 生成: {generated_tokens_count}")
        else:
            logger.debug(f"模型 {model} 响应格式不包含 token 统计信息")

    except Exception as e:
        # 捕获所有异常，避免拦截器崩溃影响主流程
        logger.error(f"token_counter_interceptor 处理响应时出错: {e}", exc_info=True)

    return True, None    
        
                        

    