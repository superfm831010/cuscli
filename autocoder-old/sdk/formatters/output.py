"""
输出格式化器模块

提供统一的输出格式化功能。
"""

import json
from typing import Any, Dict, Union, List, Optional


class OutputFormatter:
    """输出格式化器，处理不同格式的输出。"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化输出格式化器。
        
        Args:
            verbose: 是否输出详细信息
        """
        self.verbose = verbose
    
    def format_text(self, content: Union[str, Dict[str, Any]]) -> str:
        """
        格式化为文本输出。
        
        Args:
            content: 要格式化的内容，可以是字符串或字典
            
        Returns:
            格式化后的文本
        """
        if isinstance(content, dict):
            # 如果是字典，提取主要内容
            if "content" in content:
                result = content["content"]
            else:
                result = str(content)
        else:
            result = str(content)
            
        if self.verbose:
            # 在详细模式下添加调试信息
            debug_info = self._get_debug_info(content)
            if debug_info:
                result += f"\n\n[DEBUG]\n{debug_info}"
                
        return result
    
    def format_json(self, content: Any) -> str:
        """
        格式化为JSON输出。
        
        Args:
            content: 要格式化的内容
            
        Returns:
            JSON格式的字符串
        """
        # 确保内容可以被序列化为JSON
        if isinstance(content, str):
            try:
                # 尝试解析为JSON
                parsed = json.loads(content)
                content = parsed
            except json.JSONDecodeError:
                # 如果不是有效的JSON，则包装为字典
                content = {"content": content}
        
        # 添加调试信息（如果启用详细模式）
        if self.verbose and isinstance(content, dict):
            content["debug"] = self._get_debug_info_dict(content)
            
        return json.dumps(content, ensure_ascii=False, indent=2)
    
    def _get_debug_info(self, content: Any) -> str:
        """
        获取调试信息的文本表示。
        
        Args:
            content: 内容对象
            
        Returns:
            调试信息文本
        """
        debug_dict = self._get_debug_info_dict(content)
        if debug_dict:
            return json.dumps(debug_dict, ensure_ascii=False, indent=2)
        return ""
    
    def _get_debug_info_dict(self, content: Any) -> Dict[str, Any]:
        """
        获取调试信息的字典表示。
        
        Args:
            content: 内容对象
            
        Returns:
            调试信息字典
        """
        debug_info = {}
        
        # 从内容中提取元数据
        if isinstance(content, dict):
            if "metadata" in content:
                debug_info["metadata"] = content["metadata"]
            
            # 提取令牌计数信息
            if "tokens" in content:
                debug_info["tokens"] = content["tokens"]
            elif "metadata" in content and "tokens" in content["metadata"]:
                debug_info["tokens"] = content["metadata"]["tokens"]
                
            # 提取模型信息
            if "model" in content:
                debug_info["model"] = content["model"]
            elif "metadata" in content and "model" in content["metadata"]:
                debug_info["model"] = content["metadata"]["model"]
                
            # 提取时间信息
            if "timestamp" in content:
                debug_info["timestamp"] = content["timestamp"]
            elif "metadata" in content and "timestamp" in content["metadata"]:
                debug_info["timestamp"] = content["metadata"]["timestamp"]
        
        return debug_info


def format_output(content: Any, output_format: str = "text") -> str:
    """
    格式化输出内容
    
    Args:
        content: 要格式化的内容
        output_format: 输出格式 (text, json)
        
    Returns:
        str: 格式化后的内容
    """
    formatter = OutputFormatter()
    
    if output_format == "json":
        return formatter.format_json(content)
    else:
        return formatter.format_text(content)


def format_table_output(data: List[Any], headers: Optional[List[str]] = None) -> str:
    """
    格式化表格输出
    
    Args:
        data: 表格数据
        headers: 表头
        
    Returns:
        str: 格式化的表格
    """
    if not data:
        return "No data to display"
    
    if headers is None:
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
        else:
            headers = [f"Column {i+1}" for i in range(len(data[0]) if data[0] else 0)]
    
    # 计算列宽
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in data:
            if isinstance(row, dict):
                cell_value = str(row.get(header, ""))
            elif isinstance(row, (list, tuple)) and i < len(row):
                cell_value = str(row[i])
            else:
                cell_value = ""
            max_width = max(max_width, len(cell_value))
        col_widths.append(max_width + 2)  # 添加padding
    
    # 构建表格
    lines = []
    
    # 表头
    header_line = "|".join(header.center(col_widths[i]) for i, header in enumerate(headers))
    lines.append(header_line)
    
    # 分隔线
    separator = "|".join("-" * width for width in col_widths)
    lines.append(separator)
    
    # 数据行
    for row in data:
        if isinstance(row, dict):
            row_values = [str(row.get(header, "")) for header in headers]
        elif isinstance(row, (list, tuple)):
            row_values = [str(row[i]) if i < len(row) else "" for i in range(len(headers))]
        else:
            row_values = [str(row)]
        
        row_line = "|".join(value.ljust(col_widths[i]) for i, value in enumerate(row_values))
        lines.append(row_line)
    
    return "\n".join(lines)


def format_error_output(error: Exception, verbose: bool = False) -> str:
    """
    格式化错误输出
    
    Args:
        error: 异常对象
        verbose: 是否显示详细信息
        
    Returns:
        str: 格式化的错误信息
    """
    if verbose:
        import traceback
        return f"Error: {str(error)}\n\nTraceback:\n{traceback.format_exc()}"
    else:
        return f"Error: {str(error)}"


def format_progress_output(current: int, total: int, description: str = "") -> str:
    """
    格式化进度输出
    
    Args:
        current: 当前进度
        total: 总数
        description: 描述
        
    Returns:
        str: 格式化的进度信息
    """
    if total == 0:
        percentage = 100
    else:
        percentage = min(100, int((current / total) * 100))
    
    bar_length = 30
    filled_length = int(bar_length * percentage // 100)
    bar = "█" * filled_length + "-" * (bar_length - filled_length)
    
    return f"{description} [{bar}] {percentage}% ({current}/{total})" 