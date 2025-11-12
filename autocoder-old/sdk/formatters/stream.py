"""
流式输出格式化模块

提供流式输出的格式化功能。
"""

import json
from typing import AsyncIterator, Any

from ..models.responses import StreamEvent


async def format_stream_output(stream: AsyncIterator[Any], output_format: str = "stream-json") -> AsyncIterator[str]:
    """
    格式化流式输出
    
    Args:
        stream: 输入流
        output_format: 输出格式
        
    Yields:
        str: 格式化后的内容
    """
    if output_format == "stream-json":
        # 发送开始事件
        start_event = StreamEvent.start_event()
        yield start_event.to_json()
        
        try:
            async for item in stream:
                if isinstance(item, StreamEvent):
                    # 直接输出 StreamEvent
                    yield item.to_json()
                elif hasattr(item, 'to_dict'):
                    # 直接输出有to_dict方法的对象
                    yield json.dumps(item.to_dict(), ensure_ascii=False)
                else:
                    # 包装普通内容为content事件
                    content_event = StreamEvent.content_event(str(item))
                    yield content_event.to_json()
            
            # 发送结束事件
            end_event = StreamEvent.end_event()
            yield end_event.to_json()
            
        except Exception as e:
            # 发送错误事件
            error_event = StreamEvent.error_event(str(e))
            yield error_event.to_json()
    else:
        # 其他格式，直接输出
        from .output import format_output
        async for item in stream:
            yield format_output(item, "text") 