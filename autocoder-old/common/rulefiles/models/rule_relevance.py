# -*- coding: utf-8 -*-
"""
RuleRelevance 数据模型

用于规则相关性判断的返回模型。
"""

from pydantic import BaseModel, Field


class RuleRelevance(BaseModel):
    """用于规则相关性判断的返回模型"""
    is_relevant: bool = Field(description="规则是否与当前任务相关")
    reason: str = Field(default="", description="判断理由") 