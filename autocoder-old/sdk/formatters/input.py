"""
输入格式化器模块

提供输入内容的格式化功能。
"""

import json
from typing import Dict, Any, AsyncIterator


class InputFormatter:
    """输入格式化器，处理不同格式的输入。"""
    
    def format_text(self, content: str) -> str:
        """
        格式化文本输入。
        
        Args:
            content: 输入文本
            
        Returns:
            格式化后的文本
        """
        return content.strip()
    
    def format_json(self, content: str) -> Dict[str, Any]:
        """
        格式化JSON输入。
        
        Args:
            content: JSON格式的输入字符串
            
        Returns:
            解析后的字典
            
        Raises:
            ValueError: 如果输入不是有效的JSON
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON输入: {str(e)}")
    
    async def format_stream_json(self, content: str) -> AsyncIterator[Dict[str, Any]]:
        """
        格式化流式JSON输入。
        
        Args:
            content: 包含多行JSON对象的字符串
            
        Yields:
            解析后的字典
            
        Raises:
            ValueError: 如果某行不是有效的JSON
        """
        for line in content.strip().split("\n"):
            if not line.strip():
                continue
                
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的JSON行: {line}, 错误: {str(e)}") 