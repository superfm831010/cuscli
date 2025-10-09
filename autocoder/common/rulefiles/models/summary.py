# -*- coding: utf-8 -*-
"""
AlwaysApplyRuleSummary 数据模型

合并后的必须应用规则摘要模型。
"""

from typing import List
from pydantic import BaseModel, Field


class AlwaysApplyRuleSummary(BaseModel):
    """合并后的必须应用规则摘要"""
    summary: str = Field(description="合并后的规则内容")
    rule_count: int = Field(description="合并的规则数量")
    covered_areas: List[str] = Field(default_factory=list, description="覆盖的主要领域") 