import re
from typing import Optional, Tuple, Dict, Any
from loguru import logger


class ToolContentDetector:
    """
    工具内容检测器，用于识别和处理工具调用内容，特别是处理包含大量内容的工具调用。
    
    主要功能：
    1. 检测content是否包含工具调用（write_to_file, replace_in_file等）
    2. 替换工具调用中的大量内容部分，以减少token使用
    """
    
    def __init__(self, replacement_message: str = "Content cleared to save tokens"):
        """
        初始化工具内容检测器
        
        Args:
            replacement_message: 替换大量内容时使用的消息
        """
        self.replacement_message = replacement_message
        
        # 支持的工具列表
        self.supported_tools = [
            'write_to_file',
            'replace_in_file'
        ]
        
        # 为每个工具定义正则表达式模式
        self.tool_patterns = {
            'write_to_file': {
                'start': r'<write_to_file>',
                'end': r'</write_to_file>',
                'content_pattern': r'<content>(.*?)</content>',
                'content_start': r'<content>',
                'content_end': r'</content>'
            },
            'replace_in_file': {
                'start': r'<replace_in_file>',
                'end': r'</replace_in_file>',
                'content_pattern': r'<diff>(.*?)</diff>',
                'content_start': r'<diff>',
                'content_end': r'</diff>'
            }
        }
    
    def detect_tool_call(self, content: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        检测content是否包含工具调用
        
        Args:
            content: 要检测的内容
            
        Returns:
            Dict包含工具信息，如果没有检测到工具调用则返回None
            返回格式: {
                'tool_name': str,
                'start_pos': int,
                'end_pos': int,
                'full_match': str,
                'content_start': int,
                'content_end': int,
                'content_match': str
            }
        """
        if not content:
            return None
        
        for tool_name in self.supported_tools:
            pattern_info = self.tool_patterns[tool_name]
            
            # 检查是否包含工具调用的开始和结束标签
            start_pattern = pattern_info['start']
            end_pattern = pattern_info['end']
            
            start_match = re.search(start_pattern, content, re.IGNORECASE)
            if not start_match:
                continue
            
            # 从start_match位置开始查找结束标签
            start_pos = start_match.start()
            remaining_content = content[start_pos:]
            
            end_match = re.search(end_pattern, remaining_content, re.IGNORECASE)
            if not end_match:
                continue
            
            end_pos = start_pos + end_match.end()
            full_tool_match = content[start_pos:end_pos]
            
            # 查找content/diff部分
            content_pattern = pattern_info['content_pattern']
            content_match = re.search(content_pattern, full_tool_match, re.DOTALL | re.IGNORECASE)
            
            if content_match:
                # 找到完整的工具调用
                return {
                    'tool_name': tool_name,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'full_match': full_tool_match,
                    'content_start': start_pos + content_match.start(),
                    'content_end': start_pos + content_match.end(),
                    'content_match': content_match.group(0),
                    'content_inner': content_match.group(1)
                }
        
        return None
    
    def replace_tool_content(self, content: Optional[str], max_content_length: int = 500) -> Tuple[str, bool]:
        """
        替换工具调用中的大量内容
        
        Args:
            content: 原始内容
            max_content_length: 内容超过这个长度时才进行替换
            
        Returns:
            Tuple[替换后的内容, 是否进行了替换]
        """
        if not content:
            return content or "", False
        
        tool_info = self.detect_tool_call(content)
        if not tool_info:
            return content, False
        
        # 检查content部分的长度
        content_inner = tool_info['content_inner']
        if len(content_inner) <= max_content_length:
            return content, False
        
        # 构造替换后的内容
        tool_name = tool_info['tool_name']
        pattern_info = self.tool_patterns[tool_name]
        
        # 生成替换的内容标签
        if tool_name == 'write_to_file':
            replacement_content = f"<content>{self.replacement_message}</content>"
        elif tool_name == 'replace_in_file':
            replacement_content = f"<diff>{self.replacement_message}</diff>"
        else:
            replacement_content = f"<content>{self.replacement_message}</content>"
        
        # 替换原内容
        new_content = (
            content[:tool_info['start_pos']] +
            content[tool_info['start_pos']:tool_info['content_start']] +
            replacement_content +
            content[tool_info['content_end']:tool_info['end_pos']] +
            content[tool_info['end_pos']:]
        )
        
        logger.info(f"Replaced {tool_name} content: {len(content_inner)} chars -> {len(self.replacement_message)} chars")
        
        return new_content, True
    
    def get_tool_content_stats(self, content: Optional[str]) -> Dict[str, Any]:
        """
        获取工具调用内容的统计信息
        
        Args:
            content: 要分析的内容
            
        Returns:
            Dict包含统计信息
        """
        if not content:
            return {
                'has_tool_call': False,
                'total_length': 0
            }
        
        tool_info = self.detect_tool_call(content)
        if not tool_info:
            return {
                'has_tool_call': False,
                'total_length': len(content)
            }
        
        return {
            'has_tool_call': True,
            'tool_name': tool_info['tool_name'],
            'total_length': len(content),
            'tool_content_length': len(tool_info['content_inner']),
            'tool_full_length': len(tool_info['full_match']),
            'prefix_length': tool_info['start_pos'],
            'suffix_length': len(content) - tool_info['end_pos']
        }
    
    def is_tool_call_content(self, content: Optional[str]) -> bool:
        """
        简单判断content是否包含工具调用
        
        Args:
            content: 要检测的内容
            
        Returns:
            bool: 是否包含工具调用
        """
        return self.detect_tool_call(content) is not None
    
    def extract_tool_content(self, content: Optional[str]) -> Optional[str]:
        """
        提取工具调用中的内容部分
        
        Args:
            content: 原始内容
            
        Returns:
            工具调用中的内容部分，如果没有工具调用则返回None
        """
        tool_info = self.detect_tool_call(content)
        if not tool_info:
            return None
        
        return tool_info['content_inner']
    
    def get_supported_tools(self) -> list:
        """
        获取支持的工具列表
        
        Returns:
            支持的工具名称列表
        """
        return self.supported_tools.copy() 