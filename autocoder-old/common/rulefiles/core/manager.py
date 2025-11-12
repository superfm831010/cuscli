# -*- coding: utf-8 -*-
"""
AutocoderRulesManager 

规则管理器，负责加载、监控和管理规则文件。
实现单例模式，确保全局只有一个规则管理实例。
"""

import os
import re
import yaml
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from threading import Lock
from loguru import logger

# 导入数据模型
from ..models.rule_file import RuleFile

# 导入工具函数
from ..utils.parser import parse_rule_file as parse_rule_file_util

# 条件导入以避免循环依赖
if TYPE_CHECKING:
    pass


class AutocoderRulesManager:
    """
    管理 autocoderrules 目录中的规则文件。
    
    实现单例模式，确保全局只有一个规则管理实例。
    每次访问时都会重新加载规则文件。
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, project_root: Optional[str] = None):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AutocoderRulesManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, project_root: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True
        
        self._rules: Dict[str, str] = {}  # 存储规则文件内容: {file_path: content}
        self._rules_dir: Optional[str] = None  # 当前使用的规则目录
        self._project_root = project_root if project_root is not None else os.getcwd()  # 项目根目录
        
        # 加载规则
        self._load_rules()

    def _load_rules(self):
        """
        重新实现的规则加载逻辑，不使用 FinderConfig。
        加载顺序：
        1. 项目级规则文件（按优先级）
        2. 全局规则文件 (~/.auto-coder/autocoderrules)
        3. 全局 repos 子目录规则（基于当前目录名）
        
        确保不重复加载相同的文件。
        """
        self._rules = {}
        loaded_files: Set[str] = set()  # 跟踪已加载的文件，避免重复
        
        # 1. 加载项目级规则文件（按优先级）
        self._load_project_rules(loaded_files)
        
        # 2. 加载全局规则文件
        self._load_global_rules(loaded_files)
        
        # 3. 加载全局 repos 子目录规则
        self._load_global_repos_rules(loaded_files)
        
        logger.info(f"总共加载了 {len(self._rules)} 个规则文件")
    
    def _load_project_rules(self, loaded_files: Set[str]):
        """加载项目级规则文件，按优先级顺序"""
        project_root = self._project_root
        
        # 按优先级定义项目级规则目录
        project_dirs = [
            os.path.join(project_root, ".autocoderrules"),
            os.path.join(project_root, ".auto-coder", ".autocoderrules"),
            os.path.join(project_root, ".auto-coder", "autocoderrules")
        ]
        
        # 查找第一个包含 .md 文件的目录
        for rules_dir in project_dirs:
            if self._has_md_files(rules_dir):
                self._rules_dir = rules_dir
                logger.info(f"找到项目规则目录: {rules_dir}")
                self._load_rules_from_directory(rules_dir, loaded_files)
                return
        
        logger.info("未找到项目级规则目录")
    
    def _load_global_rules(self, loaded_files: Set[str]):
        """加载全局规则文件 (~/.auto-coder/autocoderrules)"""
        home_dir = os.path.expanduser("~")
        global_rules_dir = os.path.join(home_dir, ".auto-coder", "autocoderrules")
        
        if self._has_md_files(global_rules_dir):
            logger.info(f"找到全局规则目录: {global_rules_dir}")
            self._load_rules_from_directory(global_rules_dir, loaded_files)
        else:
            logger.info("未找到全局规则目录")
    
    def _load_global_repos_rules(self, loaded_files: Set[str]):
        """加载全局 repos 子目录规则（基于当前目录名）"""
        home_dir = os.path.expanduser("~")
        global_rules_dir = os.path.join(home_dir, ".auto-coder", "autocoderrules")
        repos_dir = os.path.join(global_rules_dir, "repos")
        
        if not os.path.isdir(repos_dir):
            logger.info("未找到全局 repos 目录")
            return
        
        # 获取当前目录名
        current_dir_name = os.path.basename(self._project_root)
        repo_specific_dir = os.path.join(repos_dir, current_dir_name)
        
        if self._has_md_files(repo_specific_dir):
            logger.info(f"找到仓库特定规则目录: {repo_specific_dir}")
            self._load_rules_from_directory(repo_specific_dir, loaded_files)
        else:
            logger.info(f"未找到仓库特定规则目录: {repo_specific_dir}")
    
    def _has_md_files(self, directory: str) -> bool:
        """检查目录是否存在且包含 .md 文件"""
        if not os.path.isdir(directory):
            return False
        
        try:
            for fname in os.listdir(directory):
                if fname.endswith(".md"):
                    return True
            return False
        except Exception as e:
            logger.warning(f"检查目录 {directory} 时出错: {e}")
            return False
    
    def _load_rules_from_directory(self, rules_dir: str, loaded_files: Set[str]):
        """从指定目录加载规则文件，避免重复加载"""
        logger.info(f"扫描规则目录: {rules_dir}")
        try:
            for fname in os.listdir(rules_dir):
                if fname.endswith(".md"):
                    fpath = os.path.join(rules_dir, fname)
                    
                    # 使用规范化路径避免重复加载
                    normalized_path = os.path.normpath(os.path.abspath(fpath))
                    if normalized_path in loaded_files:
                        logger.info(f"跳过重复文件: {fpath}")
                        continue
                    
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                            self._rules[fpath] = content
                            loaded_files.add(normalized_path)
                            logger.info(f"已加载规则文件: {fpath}")
                    except Exception as e:
                        logger.warning(f"加载规则文件 {fpath} 时出错: {e}")
                        continue
        except Exception as e:
            logger.warning(f"读取规则目录 {rules_dir} 时出错: {e}")

    def parse_rule_file(self, file_path: str) -> RuleFile:
        """
        解析规则文件并返回结构化的Pydantic模型对象
        
        Args:
            file_path: 规则文件的路径
            
        Returns:
            RuleFile: 包含规则文件结构化内容的Pydantic模型
        """
        if not os.path.exists(file_path) or not file_path.endswith('.md'):
            logger.warning(f"无效的规则文件路径: {file_path}")
            return RuleFile(file_path=file_path)
            
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
            
        except Exception as e:
            logger.warning(f"解析规则文件时出错: {file_path}, 错误: {e}")
            return RuleFile(file_path=file_path)

    def get_rules(self) -> Dict[str, str]:
        """获取所有规则文件内容，总是重新加载"""
        self._load_rules()  # 总是重新加载
        return self._rules.copy()
        
    def get_parsed_rules(self) -> List[RuleFile]:
        """获取所有解析后的规则文件，总是重新加载"""
        self._load_rules()  # 总是重新加载
        parsed_rules = []
        for file_path in self._rules:
            parsed_rule = self.parse_rule_file(file_path)
            parsed_rules.append(parsed_rule)
        return parsed_rules

    @classmethod
    def reset_instance(cls):
        """重置单例实例"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance = None
                logger.info("AutocoderRulesManager单例已被重置") 