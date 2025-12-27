# -*- coding: utf-8 -*-
"""
AutoCoder Skills 模块

负责读取和管理项目级别及全局级别的 Skills。

Skills 存储位置：
- 项目级别: {project_root}/.autocoderskills/
- 全局级别: ~/.auto-coder/.autocoderskills/
"""

from .manager import SkillManager, SkillIndex

__all__ = [
    "SkillManager",
    "SkillIndex",
]
