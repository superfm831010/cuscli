
"""
Tools Manager Data Models

定义工具管理器使用的数据模型。
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel


class ToolCommand(BaseModel):
    """表示一个工具命令的信息"""
    model_config = {"frozen": True, "extra": "forbid"}
    
    name: str  # 命令名称
    path: str  # 命令文件的完整路径
    help_text: str  # 命令的帮助信息
    is_executable: bool  # 是否可执行
    file_extension: str  # 文件扩展名
    source_directory: str  # 来源目录


class ToolsLoadResult(BaseModel):
    """工具加载结果"""
    model_config = {"frozen": True, "extra": "forbid"}
    
    success: bool
    tools: List[ToolCommand]
    error_message: Optional[str] = None
    total_count: int = 0
    failed_count: int = 0
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to set total_count"""
        if self.success:
            object.__setattr__(self, 'total_count', len(self.tools))

