# -*- coding: utf-8 -*-
"""
InitRule 数据模型

用于表示项目初始化规则的生成结果模型。
"""

from typing import List
from pydantic import BaseModel, Field


class InitRule(BaseModel):
    """项目初始化规则"""
    content: str = Field(description="生成的初始化规则内容")
    project_type: str = Field(description="识别的项目类型")
    commands: List[str] = Field(default_factory=list, description="检测到的命令列表")
    technologies: List[str] = Field(default_factory=list, description="检测到的技术栈")
    file_path: str = Field(description="保存的文件路径")