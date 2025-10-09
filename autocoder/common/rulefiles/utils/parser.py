# -*- coding: utf-8 -*-
"""
规则文件解析工具

提供规则文件解析相关的实用工具函数。
"""

import os
import re
import yaml
from typing import Dict, Any
from loguru import logger

from ..models.rule_file import RuleFile

# 导入优先级目录查找器
from autocoder.common.priority_directory_finder import (
    PriorityDirectoryFinder, FinderConfig, SearchStrategy, 
    ValidationMode, create_file_filter
)


def parse_rule_file(file_path: str) -> RuleFile:
    """
    解析规则文件并返回结构化的Pydantic模型对象
    
    Args:
        file_path: 规则文件的路径
        
    Returns:
        RuleFile: 包含规则文件结构化内容的Pydantic模型
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当文件格式无效时
    """
    if not os.path.exists(file_path):
        logger.error(f"规则文件不存在: {file_path}")
        raise FileNotFoundError(f"规则文件不存在: {file_path}")
        
    if not file_path.endswith('.md'):
        logger.error(f"无效的规则文件格式，必须是.md文件: {file_path}")
        raise ValueError(f"无效的规则文件格式，必须是.md文件: {file_path}")
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 解析YAML头部和Markdown内容
        yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        yaml_match = yaml_pattern.search(content)
        
        metadata = {}
        markdown_content = content
        
        if yaml_match:
            yaml_content = yaml_match.group(1)
            try:
                metadata = yaml.safe_load(yaml_content)
                # 移除YAML部分，仅保留Markdown内容
                markdown_content = content[yaml_match.end():]
            except Exception as e:
                logger.warning(f"解析规则文件YAML头部时出错: {e}")
        
        # 创建并返回Pydantic模型            
        rule = RuleFile(
            description=metadata.get('description', ''),
            globs=metadata.get('globs', []),
            always_apply=metadata.get('alwaysApply', False),
            content=markdown_content.strip(),
            file_path=file_path
        )                                    
        return rule
        
    except (FileNotFoundError, ValueError):
        # 重新抛出已知的异常
        raise
    except Exception as e:
        logger.error(f"解析规则文件时出现未知错误: {file_path}, 错误: {e}")
        raise RuntimeError(f"解析规则文件失败: {file_path}") from e


def extract_yaml_metadata(content: str) -> tuple[Dict[str, Any], str]:
    """
    从文件内容中提取 YAML 前置元数据和 Markdown 内容
    
    Args:
        content: 文件内容
        
    Returns:
        tuple: (元数据字典, Markdown内容)
    """
    yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    yaml_match = yaml_pattern.search(content)
    
    metadata = {}
    markdown_content = content
    
    if yaml_match:
        yaml_content = yaml_match.group(1)
        try:
            metadata = yaml.safe_load(yaml_content) or {}
            # 移除YAML部分，仅保留Markdown内容
            markdown_content = content[yaml_match.end():]
        except Exception as e:
            logger.warning(f"解析YAML头部时出错: {e}")
    
    return metadata, markdown_content.strip()


def validate_rule_file_format(file_path: str) -> bool:
    """
    验证规则文件格式是否正确
    
    Args:
        file_path: 规则文件路径
        
    Returns:
        bool: 是否为有效的规则文件格式
    """
    if not os.path.exists(file_path):
        return False
        
    if not file_path.endswith('.md'):
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否可以正常解析
        metadata, markdown_content = extract_yaml_metadata(content)
        
        # 基本验证：确保有内容
        if not markdown_content.strip():
            return False
            
        return True
        
    except Exception:
        return False


def get_rule_directories(project_root: str) -> list[str]:
    """
    获取所有可能的规则目录路径（按优先级排序）
    
    Args:
        project_root: 项目根目录
        
    Returns:
        list[str]: 规则目录路径列表（按优先级排序）
    """
    return [
        os.path.join(project_root, ".autocoderrules"),
        os.path.join(project_root, ".auto-coder", ".autocoderrules"),
        os.path.join(project_root, ".auto-coder", "autocoderrules")
    ]


def find_existing_rule_directories(project_root: str) -> list[str]:
    """
    使用优先级目录查找器查找实际存在且包含规则文件的目录。
    
    Args:
        project_root: 项目根目录
        
    Returns:
        list[str]: 实际存在且包含规则文件的目录路径列表
    """
    try:
        # 创建文件过滤器，只查找.md文件
        md_filter = create_file_filter(extensions=[".md"], recursive=True)
        
        # 创建查找器配置，使用LIST_ALL策略返回所有有效目录
        config = FinderConfig(strategy=SearchStrategy.LIST_ALL)
        
        # 按优先级添加目录配置
        config.add_directory(
            path=os.path.join(project_root, ".autocoderrules"),
            priority=1,
            validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
            file_filter=md_filter,
            description="项目级规则目录"
        )
        config.add_directory(
            path=os.path.join(project_root, ".auto-coder", ".autocoderrules"),
            priority=2,
            validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
            file_filter=md_filter,
            description="项目.auto-coder规则目录"
        )
        config.add_directory(
            path=os.path.join(project_root, ".auto-coder", "autocoderrules"),
            priority=3,
            validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
            file_filter=md_filter,
            description="项目.auto-coder/autocoderrules目录"
        )
        
        # 执行查找
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        if result.success:
            logger.info(f"使用优先级查找器找到 {len(result.selected_directories)} 个有效规则目录")
            return result.selected_directories
        else:
            logger.info("优先级查找器未找到包含规则文件的目录")
            return []
            
    except Exception as e:
        logger.error(f"使用优先级查找器查找规则目录时出错: {e}")
        # 回退到传统方法
        return _find_existing_rule_directories_fallback(project_root)


def _find_existing_rule_directories_fallback(project_root: str) -> list[str]:
    """
    回退到传统的目录查找方法。
    
    Args:
        project_root: 项目根目录
        
    Returns:
        list[str]: 实际存在的规则目录路径列表
    """
    logger.info("回退到传统的规则目录查找方法")
    potential_dirs = get_rule_directories(project_root)
    return [d for d in potential_dirs if os.path.isdir(d)] 