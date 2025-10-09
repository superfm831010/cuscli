
# -*- coding: utf-8 -*-
"""
AutoCoder 规则文件管理模块

提供读取、解析和监控 AutoCoder 规则文件的功能。

重构后的模块结构：
- models/: 数据模型 (RuleFile, RuleRelevance, AlwaysApplyRuleSummary, ConditionalRulesIndex)
- core/: 核心功能 (AutocoderRulesManager, RuleSelector)  
- utils/: 工具函数 (parser, monitor)
- api.py: 统一的 API 接口
"""

# 导入数据模型
from .models import (
    RuleFile,
    RuleRelevance,
    AlwaysApplyRuleSummary,
    ConditionalRulesIndex,
    InitRule,
)

# 导入核心组件
from .core import (
    AutocoderRulesManager,
    RuleSelector,
)

# 导入公共 API 函数
from .api import (
    get_rules,
    get_parsed_rules,
    parse_rule_file,
    reset_rules_manager,
    auto_select_rules,
    get_required_and_index_rules,
    generate_always_apply_summary,
    generate_conditional_rules_index,
    init_rule,
    get_rules_for_conversation,
)

__all__ = [
    # 数据模型
    'RuleFile',
    'RuleRelevance',
    'AlwaysApplyRuleSummary',
    'ConditionalRulesIndex',
    'InitRule',
    
    # 核心组件
    'AutocoderRulesManager',
    'RuleSelector',
    
    # 公共 API 函数
    'get_rules',
    'get_parsed_rules',
    'parse_rule_file',
    'reset_rules_manager',
    'auto_select_rules',
    'get_required_and_index_rules',
    'generate_always_apply_summary',
    'generate_conditional_rules_index',
    'init_rule',
    'get_rules_for_conversation',
]
