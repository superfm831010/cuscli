# -*- coding: utf-8 -*-
"""
ConditionalRulesIndex 数据模型

条件规则索引模型。
"""

from typing import List
from pydantic import BaseModel, Field


class ConditionalRulesIndex(BaseModel):
    """条件规则索引"""
    index_content: str = Field(description="规则索引内容")
    rule_count: int = Field(description="规则总数")
    categories: List[str] = Field(default_factory=list, description="规则分类") 