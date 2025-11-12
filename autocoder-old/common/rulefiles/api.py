# -*- coding: utf-8 -*-
"""
RuleFiles API 接口

提供所有公共 API 函数和便利函数。
"""

import os
from typing import Dict, List, Optional, Union, Any
from loguru import logger

# 导入第三方依赖
import byzerllm
from autocoder.common import AutoCoderArgs

# 导入数据模型
from .models.rule_file import RuleFile
from .models.summary import AlwaysApplyRuleSummary
from .models.index import ConditionalRulesIndex
from .models.init_rule import InitRule

# 导入核心组件
from .core.manager import AutocoderRulesManager
from .core.selector import RuleSelector


# 对外提供单例
_rules_manager = None


def get_rules(project_root: Optional[str] = None) -> Dict[str, str]:
    """获取所有规则文件内容，可指定项目根目录"""
    global _rules_manager
    if _rules_manager is None:
        _rules_manager = AutocoderRulesManager(project_root=project_root)
    return _rules_manager.get_rules()


def get_parsed_rules(project_root: Optional[str] = None) -> List[RuleFile]:
    """获取所有解析后的规则文件，可指定项目根目录"""
    global _rules_manager
    if _rules_manager is None:
        _rules_manager = AutocoderRulesManager(project_root=project_root)
    return _rules_manager.get_parsed_rules()


def parse_rule_file(file_path: str, project_root: Optional[str] = None) -> RuleFile:
    """解析指定的规则文件，可指定项目根目录"""
    global _rules_manager
    if _rules_manager is None:
        _rules_manager = AutocoderRulesManager(project_root=project_root)
    return _rules_manager.parse_rule_file(file_path)


def reset_rules_manager():
    """重置AutocoderRulesManager单例实例"""
    AutocoderRulesManager.reset_instance()
    global _rules_manager
    _rules_manager = None


def auto_select_rules(context: str, llm: Optional[byzerllm.ByzerLLM] = None, args: Optional[AutoCoderArgs] = None) -> Dict[str, str]:
    """
    根据LLM的判断和规则元数据选择适用的规则。
    
    Args:
        context: 上下文信息
        llm: ByzerLLM 实例
        args: 可选的 AutoCoderArgs 参数
        
    Returns:
        Dict[str, str]: 选定规则的 {file_path: content} 字典
    """
    selector = RuleSelector(llm=llm, args=args)    
    return selector.get_selected_rules_content(context=context)


def get_required_and_index_rules() -> Dict[str, str]:
    """
    获取所有必须应用的规则文件(always_apply=True)和Index.md文件。
    
    Returns:
        Dict[str, str]: 包含必须应用的规则和Index.md文件的{file_path: content}字典。
    """
    # 获取所有解析后的规则文件
    parsed_rules = get_parsed_rules()
    result: Dict[str, str] = {}
    logger.info(f"获取所有解析后的规则文件完成，总数: {len(parsed_rules)}")
    
    for rule in parsed_rules:
        # 检查是否是always_apply=True的规则
        if rule.always_apply:
            result[rule.file_path] = rule.content
            logger.info(f"添加必须应用的规则: {os.path.basename(rule.file_path)}")
        
        # 检查是否是Index.md文件
        if os.path.basename(rule.file_path).lower() == "index.md":
            result[rule.file_path] = rule.content
            logger.info(f"添加Index.md文件: {rule.file_path}")
    
    logger.info(f"获取必须应用的规则和Index.md文件完成，总数: {len(result)}")
    return result


def generate_always_apply_summary(llm: Optional[Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]], args: Optional[AutoCoderArgs] = None) -> Optional[AlwaysApplyRuleSummary]:
    """
    便利函数：生成所有必须应用规则的合并摘要。

    Args:
        llm: ByzerLLM 实例
        args: 可选的 AutoCoderArgs 参数

    Returns:
        AlwaysApplyRuleSummary: 合并后的规则摘要，如果没有 LLM 则返回 None
    """
    selector = RuleSelector(llm=llm, args=args)
    return selector.generate_always_apply_summary()


def generate_conditional_rules_index(llm: Optional[Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]], args: Optional[AutoCoderArgs] = None) -> Optional[ConditionalRulesIndex]:
    """
    便利函数：生成所有条件规则的索引目录。

    Args:
        llm: ByzerLLM 实例
        args: 可选的 AutoCoderArgs 参数

    Returns:
        ConditionalRulesIndex: 条件规则索引，如果没有 LLM 则返回 None
    """
    selector = RuleSelector(llm=llm, args=args)
    return selector.generate_conditional_rules_index()


def init_rule(llm: Optional[Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]] = None, 
              args: Optional[AutoCoderArgs] = None, 
              project_root: Optional[str] = None) -> Optional[InitRule]:
    """
    使用 subagent 机制探索项目结构并生成初始化规则，自动保存到 .autocoderrules/init.md 文件。

    Args:
        llm: ByzerLLM 实例（可选，因为使用 subagent 机制）
        args: 可选的 AutoCoderArgs 参数
        project_root: 项目根目录，如果为 None 则使用当前目录

    Returns:
        InitRule: 生成的初始化规则对象，如果失败则返回 None
    """
    try:
        # 确定项目根目录
        if project_root is None:
            project_root = os.getcwd()

        logger.info(f"使用 subagent 机制开始为项目生成初始化规则: {project_root}")

        # 使用 RuleSelector 生成初始化规则，subagent 机制会自动处理文件写入
        selector = RuleSelector(llm=llm, args=args)
        init_rule_result = selector.generate_init_rule(project_root=project_root)

        if init_rule_result is None:
            logger.error("使用 subagent 机制生成初始化规则失败")
            return None

        logger.info(f"成功使用 subagent 机制生成初始化规则")
        logger.info(f"初始化规则文件: {init_rule_result.file_path}")
        logger.info(f"项目类型: {init_rule_result.project_type}")
        logger.info(f"检测到的技术栈: {', '.join(init_rule_result.technologies)}")
        logger.info(f"检测到的命令: {', '.join(init_rule_result.commands)}")
        
        return init_rule_result

    except Exception as e:
        logger.error(f"使用 subagent 机制生成初始化规则时出错: {e}", exc_info=True)
        return None


def get_rules_for_conversation(project_root: Optional[str] = None) -> Optional[str]:
    """
    获取格式化的规则文本，用于添加到对话中。
    
    将必须规则（alwaysApply=true）的完整内容和条件规则（alwaysApply=false）的描述信息
    格式化为适合对话的文本格式。
    
    Args:
        project_root: 项目根目录，如果为 None 则使用当前目录
        
    Returns:
        str: 格式化的规则文本，如果没有规则则返回 None
    """
    try:
        # 获取所有解析后的规则
        all_rules = get_parsed_rules(project_root)
        
        if not all_rules:
            logger.info("未找到任何规则文件")
            return None
        
        # 分离必须规则和条件规则
        required_rules = [rule for rule in all_rules if rule.always_apply]
        conditional_rules = [rule for rule in all_rules if not rule.always_apply]
        
        # 构建消息内容
        message_parts = []
        
        # 添加必须规则的完整内容
        if required_rules:
            message_parts.append("## Required Rules (Always Applied)")
            message_parts.append("The following rules must always be followed:")
            message_parts.append("")
            
            for rule in required_rules:
                rule_name = os.path.basename(rule.file_path)
                message_parts.append(f"### {rule_name}")
                if rule.description:
                    message_parts.append(f"**Description**: {rule.description}")
                if rule.globs:
                    message_parts.append(f"**Applicable Files**: {', '.join(rule.globs)}")
                message_parts.append("")
                message_parts.append(rule.content)
                message_parts.append("")
        
        # 添加条件规则的描述和路径
        if conditional_rules:
            message_parts.append("## Conditional Rules (Apply as Needed)")
            message_parts.append("The following rules are available for specific contexts. Use the read_file tool to read their full content when needed:")
            message_parts.append("")
            
            for rule in conditional_rules:
                rule_name = os.path.basename(rule.file_path)
                message_parts.append(f"### {rule_name}")
                message_parts.append(f"**Path**: `{rule.file_path}`")
                if rule.description:
                    message_parts.append(f"**Description**: {rule.description}")
                if rule.globs:
                    message_parts.append(f"**Applicable Files**: {', '.join(rule.globs)}")
                message_parts.append("")
        
        # 如果没有任何规则，返回 None
        if not message_parts:
            return None
            
        combined_rules = "\n".join(message_parts)
        logger.info(f"成功格式化规则文本，必须规则: {len(required_rules)}, 条件规则: {len(conditional_rules)}")
        return combined_rules
        
    except Exception as e:
        logger.error(f"获取对话规则时出错: {e}", exc_info=True)
        return None

 