# -*- coding: utf-8 -*-
"""
RuleFile 数据模型

规则文件的 Pydantic 模型定义。
"""

from typing import List
from pydantic import BaseModel, Field


class RuleFile(BaseModel):
    """规则文件的Pydantic模型"""
    description: str = Field(default="", description="规则的描述")
    globs: List[str] = Field(default_factory=list, description="文件匹配模式列表")
    always_apply: bool = Field(default=False, description="是否总是应用规则")
    content: str = Field(default="", description="规则文件的正文内容")
    file_path: str = Field(default="", description="规则文件的路径") 