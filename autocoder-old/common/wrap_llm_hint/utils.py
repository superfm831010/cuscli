

"""
Wrap LLM Hint 工具函数模块

提供简化的接口函数，用于快速添加和处理提示信息。
"""

from typing import List, Optional, Dict, Any, Union
from .wrap_llm_hint import WrapLLMHint, HintConfig


def add_hint_to_text(content: str, hint: str, separator: str = "\n---\n") -> str:
    """
    简单的文本提示添加函数
    
    Args:
        content: 原始文本内容
        hint: 要添加的提示信息
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        添加提示后的文本内容
        
    Example:
        >>> result = add_hint_to_text("Hello world", "This is a hint")
        >>> print(result)
        Hello world
        ---
        [[This is a hint]]
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.add_hint(content, hint)


def create_hint_wrapper(separator: str = "\n---\n", 
                       prefix: str = "[[", 
                       suffix: str = "]]",
                       allow_empty_hint: bool = False,
                       strip_whitespace: bool = True) -> WrapLLMHint:
    """
    创建自定义配置的提示包装器
    
    Args:
        separator: 分隔符
        prefix: 提示前缀
        suffix: 提示后缀
        allow_empty_hint: 是否允许空提示
        strip_whitespace: 是否去除空白字符
        
    Returns:
        配置好的 WrapLLMHint 实例
        
    Example:
        >>> wrapper = create_hint_wrapper(prefix="[HINT] ", suffix=" [/HINT]")
        >>> result = wrapper.add_hint("Content", "Important note")
        >>> print(result)
        Content
        ---
        [HINT] Important note [/HINT]
    """
    config = HintConfig(
        separator=separator,
        prefix=prefix,
        suffix=suffix,
        allow_empty_hint=allow_empty_hint,
        strip_whitespace=strip_whitespace
    )
    return WrapLLMHint(config)


def extract_hint_from_text(wrapped_content: str, separator: str = "\n---\n") -> Optional[str]:
    """
    从包装后的文本中提取提示信息
    
    Args:
        wrapped_content: 包装后的文本内容
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        提取的提示信息，如果没有找到则返回None
        
    Example:
        >>> text = "Content\n---\n[[This is a hint]]"
        >>> hint = extract_hint_from_text(text)
        >>> print(hint)
        This is a hint
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.extract_hint(wrapped_content)


def extract_content_from_text(wrapped_content: str, separator: str = "\n---\n") -> str:
    """
    从包装后的文本中提取原始内容（去除提示部分）
    
    Args:
        wrapped_content: 包装后的文本内容
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        原始文本内容
        
    Example:
        >>> text = "Content\n---\nThis is a hint"
        >>> content = extract_content_from_text(text)
        >>> print(content)
        Content
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.extract_content(wrapped_content)


def has_hint_in_text(content: str, separator: str = "\n---\n") -> bool:
    """
    检查文本是否包含提示信息
    
    Args:
        content: 要检查的文本内容
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        如果包含提示信息返回True，否则返回False
        
    Example:
        >>> has_hint = has_hint_in_text("Content\n---\nHint")
        >>> print(has_hint)
        True
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.has_hint(content)


def replace_hint_in_text(wrapped_content: str, new_hint: str, separator: str = "\n---\n") -> str:
    """
    替换文本中的提示信息
    
    Args:
        wrapped_content: 包装后的文本内容
        new_hint: 新的提示信息
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        替换提示后的文本内容
        
    Example:
        >>> text = "Content\n---\n[[Old hint]]"
        >>> result = replace_hint_in_text(text, "New hint")
        >>> print(result)
        Content
        ---
        [[New hint]]
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.replace_hint(wrapped_content, new_hint)


def add_multiple_hints_to_text(content: str, hints: List[str], separator: str = "\n---\n") -> str:
    """
    给文本添加多个提示信息
    
    Args:
        content: 原始文本内容
        hints: 提示信息列表
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        添加所有提示后的文本内容
        
    Example:
        >>> result = add_multiple_hints_to_text("Content", ["Hint 1", "Hint 2"])
        >>> print(result)
        Content
        ---
        [[Hint 1]]
        ---
        [[Hint 2]]
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.add_multiple_hints(content, hints)


def get_text_statistics(wrapped_content: str, separator: str = "\n---\n") -> Dict[str, Any]:
    """
    获取包装文本的统计信息
    
    Args:
        wrapped_content: 包装后的文本内容
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        包含统计信息的字典
        
    Example:
        >>> stats = get_text_statistics("Content\n---\nHint")
        >>> print(stats)
        {
            'total_length': 15,
            'content_length': 7,
            'hint_length': 4,
            'has_hint': True,
            'separator_count': 1,
            'separator': '\n---\n'
        }
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.get_statistics(wrapped_content)


def batch_add_hints(contents: List[str], hints: List[str], separator: str = "\n---\n") -> List[str]:
    """
    批量给多个文本添加提示信息
    
    Args:
        contents: 原始文本内容列表
        hints: 提示信息列表
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        添加提示后的文本内容列表
        
    Raises:
        ValueError: 当内容列表和提示列表长度不匹配时
        
    Example:
        >>> contents = ["Content 1", "Content 2"]
        >>> hints = ["Hint 1", "Hint 2"]
        >>> results = batch_add_hints(contents, hints)
        >>> print(results[0])
        Content 1
        ---
        [[Hint 1]]
    """
    if len(contents) != len(hints):
        raise ValueError(f"Contents list length ({len(contents)}) must match hints list length ({len(hints)})")
    
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    
    results = []
    for content, hint in zip(contents, hints):
        try:
            result = wrapper.add_hint(content, hint)
            results.append(result)
        except (ValueError, TypeError) as e:
            # 如果添加失败，保留原始内容
            results.append(content)
    
    return results


def safe_add_hint(content: str, hint: str, fallback_hint: str = "Content processed", separator: str = "\n---\n") -> str:
    """
    安全地添加提示信息，出错时使用备用提示
    
    Args:
        content: 原始文本内容
        hint: 要添加的提示信息
        fallback_hint: 备用提示信息
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        添加提示后的文本内容
        
    Example:
        >>> result = safe_add_hint("Content", "", "Default hint")
        >>> print(result)
        Content
        ---
        [[Default hint]]
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.add_hint_safe(content, hint, fallback_hint)


def create_conversation_hint(cleanup_message: str) -> str:
    """
    创建对话清理提示信息（参考 agentic_conversation_pruner.py 的实现）
    
    Args:
        cleanup_message: 清理消息内容
        
    Returns:
        格式化的提示信息
        
    Example:
        >>> hint = create_conversation_hint("Conversation is too long")
        >>> content = "User message content"
        >>> result = add_hint_to_text(content, hint)
        >>> print(result)
        User message content
        ---
        [[Conversation is too long]]
    """
    return cleanup_message


def append_hint_to_text(content: str, hint: str, separator: str = "\n---\n") -> str:
    """
    追加提示信息到文本内容
    
    如果文本已经包含提示信息，则在现有提示后追加新提示；
    如果文本不包含提示信息，则等同于 add_hint_to_text 函数。
    
    Args:
        content: 原始文本内容（可能已经包含提示）
        hint: 要追加的提示信息
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        追加提示后的文本内容
        
    Example:
        >>> content = "Hello world\n---\n[[hint1]]"
        >>> result = append_hint_to_text(content, "hint2")
        >>> print(result)
        Hello world
        ---
        [[hint1
        hint2]]
        
        >>> content = "Hello world"
        >>> result = append_hint_to_text(content, "first hint")
        >>> print(result)
        Hello world
        ---
        [[first hint]]
    """
    config = HintConfig(separator=separator)
    wrapper = WrapLLMHint(config)
    return wrapper.append_hint(content, hint)


def safe_append_hint(content: str, hint: str, fallback_hint: str = "", separator: str = "\n---\n") -> str:
    """
    安全地追加提示信息，出错时使用备用提示或保持原内容
    
    Args:
        content: 原始文本内容（可能已经包含提示）
        hint: 要追加的提示信息
        fallback_hint: 备用提示信息
        separator: 分隔符，默认为 "\n---\n"
        
    Returns:
        追加提示后的文本内容
        
    Example:
        >>> content = "Hello\n---\n[[hint1]]"
        >>> result = safe_append_hint(content, "", "fallback hint")
        >>> print(result)
        Hello
        ---
        [[hint1
        fallback hint]]
    """
    try:
        return append_hint_to_text(content, hint, separator)
    except (ValueError, TypeError):
        if fallback_hint:
            try:
                return append_hint_to_text(content, fallback_hint, separator)
            except (ValueError, TypeError):
                return content
        return content


def merge_with_last_user_message(conversations: List[Dict[str, Any]], cleanup_message: str, append_mode: bool = False) -> List[Dict[str, Any]]:
    """
    将清理消息合并到最后一个用户消息中（参考 agentic_conversation_pruner.py 的实现）
    
    Args:
        conversations: 对话列表
        cleanup_message: 清理消息内容
        append_mode: 是否使用追加模式。True时追加到现有hint，False时替换现有hint
        
    Returns:
        更新后的对话列表
        
    Example:
        >>> conversations = [{"role": "user", "content": "Hello"}]
        >>> result = merge_with_last_user_message(conversations, "System hint")
        >>> print(result[0]["content"])
        Hello
        ---
        [[System hint]]
        
        >>> conversations = [{"role": "user", "content": "Hello\n---\n[[hint1]]"}]
        >>> result = merge_with_last_user_message(conversations, "hint2", append_mode=True)
        >>> print(result[0]["content"])
        Hello
        ---
        [[hint1
        hint2]]
    """
    if not conversations:
        return conversations
    
    # 复制对话列表以避免修改原始数据
    updated_conversations = conversations.copy()
    
    # 检查最后一个消息是否是用户消息
    if updated_conversations and updated_conversations[-1].get("role") == "user":
        # 合并到最后一个用户消息
        last_message = updated_conversations[-1].copy()
        
        if append_mode:
            # 使用追加模式
            last_message["content"] = append_hint_to_text(last_message["content"], cleanup_message)
        else:
            # 使用替换模式：先提取原始内容，然后添加新hint（替换现有hint）
            original_content = extract_content_from_text(last_message["content"])
            last_message["content"] = add_hint_to_text(original_content, cleanup_message)
            
        updated_conversations[-1] = last_message
    else:
        # 添加新的用户消息
        updated_conversations.append({
            "role": "user",
            "content": cleanup_message
        })
    
    return updated_conversations


