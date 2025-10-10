"""
规则加载器模块

功能：
1. 从 Markdown 文件加载检查规则
2. 从配置文件加载规则配置
3. 根据文件类型选择适用的规则
4. 支持规则缓存以提高性能

作者: Claude AI
创建时间: 2025-10-10
"""

import os
import re
import json
from typing import List, Dict, Optional, Set
from pathlib import Path
import fnmatch

from autocoder.checker.types import Rule, Severity


class RulesLoader:
    """
    规则加载器

    负责加载和管理代码检查规则，支持从 Markdown 文件解析规则，
    并根据配置文件过滤和选择规则。
    """

    def __init__(self, rules_dir: str = "rules"):
        """
        初始化规则加载器

        Args:
            rules_dir: 规则文件所在目录，默认为 "rules"
        """
        self.rules_dir = rules_dir
        self._rule_cache: Dict[str, List[Rule]] = {}
        self._config: Optional[Dict] = None
        self._file_pattern_cache: Dict[str, str] = {}  # 文件路径 -> 规则类型映射

    def load_rules(self, rule_type: str) -> List[Rule]:
        """
        加载指定类型的规则

        Args:
            rule_type: 规则类型，可选值: "backend", "frontend"

        Returns:
            规则列表

        Raises:
            FileNotFoundError: 规则文件不存在
            ValueError: 规则类型不支持
        """
        # 检查缓存
        if rule_type in self._rule_cache:
            return self._rule_cache[rule_type]

        # 确定规则文件路径
        rule_file = os.path.join(self.rules_dir, f"{rule_type}_rules.md")

        if not os.path.exists(rule_file):
            raise FileNotFoundError(f"规则文件不存在: {rule_file}")

        # 解析规则文件
        rules = self._parse_markdown_rules(rule_file, rule_type)

        # 应用配置过滤
        if self._config is not None:
            rules = self._apply_config_filters(rules, rule_type)

        # 缓存规则
        self._rule_cache[rule_type] = rules

        return rules

    def get_applicable_rules(self, file_path: str) -> List[Rule]:
        """
        根据文件路径获取适用的规则

        Args:
            file_path: 文件路径

        Returns:
            适用于该文件的规则列表
        """
        # 确定规则类型
        rule_type = self._determine_rule_type(file_path)

        if rule_type is None:
            return []

        # 加载规则
        return self.load_rules(rule_type)

    def reload_rules(self) -> None:
        """
        重新加载所有规则

        清空缓存并重新加载规则，用于规则文件更新后的刷新。
        """
        self._rule_cache.clear()
        self._file_pattern_cache.clear()

    def load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载规则配置文件

        Args:
            config_path: 配置文件路径，默认为 rules/rules_config.json

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        if config_path is None:
            config_path = os.path.join(self.rules_dir, "rules_config.json")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

        return self._config

    def _parse_markdown_rules(self, file_path: str, rule_type: str) -> List[Rule]:
        """
        解析 Markdown 格式的规则文件

        Args:
            file_path: Markdown 文件路径
            rule_type: 规则类型（backend/frontend）

        Returns:
            解析出的规则列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        rules = []
        current_category = "未分类"

        # 按行分割处理
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # 检测类别标题（## 开头）
            if line.startswith('## ') and not line.startswith('###'):
                current_category = line[3:].strip()
                i += 1
                continue

            # 检测规则开始（### 规则ID:）
            if line.startswith('### 规则ID:'):
                rule_id = line.split(':', 1)[1].strip()

                # 初始化规则字段
                title = ""
                severity = Severity.INFO
                description = ""
                explanation = ""
                examples = ""

                # 解析规则字段
                i += 1
                while i < len(lines):
                    line = lines[i].strip()

                    # 遇到下一个规则或类别，停止
                    if line.startswith('###') or (line.startswith('##') and not line.startswith('###')):
                        break

                    # 提取字段
                    if line.startswith('**标题**:'):
                        title = line.split(':', 1)[1].strip()
                    elif line.startswith('**严重程度**:'):
                        severity_str = line.split(':', 1)[1].strip().lower()
                        severity = Severity(severity_str)
                    elif line.startswith('**描述**:'):
                        description = line.split(':', 1)[1].strip()
                    elif line.startswith('**说明**:'):
                        explanation = line.split(':', 1)[1].strip()
                    elif line.startswith('**错误示例**:') or line.startswith('**正确示例**:'):
                        # 收集示例代码块
                        example_lines = [line]
                        i += 1
                        in_code_block = False
                        while i < len(lines):
                            example_line = lines[i]
                            if example_line.strip().startswith('```'):
                                in_code_block = not in_code_block
                                example_lines.append(example_line)
                                if not in_code_block:
                                    # 代码块结束
                                    i += 1
                                    break
                            elif in_code_block or example_line.strip():
                                example_lines.append(example_line)
                            else:
                                # 空行且不在代码块中，示例结束
                                break
                            i += 1
                        examples += '\n'.join(example_lines) + '\n\n'
                        continue

                    i += 1

                # 合并描述和说明
                full_description = description
                if explanation:
                    full_description = f"{description}\n\n{explanation}"

                # 创建规则对象
                rule = Rule(
                    id=rule_id,
                    category=current_category,
                    title=title,
                    description=full_description,
                    severity=severity,
                    enabled=True,
                    examples=examples.strip() if examples else None
                )

                rules.append(rule)
                continue

            i += 1

        return rules

    def _determine_rule_type(self, file_path: str) -> Optional[str]:
        """
        根据文件路径确定规则类型

        Args:
            file_path: 文件路径

        Returns:
            规则类型（backend/frontend），如果无法确定则返回 None
        """
        # 检查缓存
        if file_path in self._file_pattern_cache:
            return self._file_pattern_cache[file_path]

        # 如果没有配置，根据扩展名判断
        if self._config is None:
            rule_type = self._determine_by_extension(file_path)
            self._file_pattern_cache[file_path] = rule_type
            return rule_type

        # 根据配置的 file_patterns 判断
        rule_sets = self._config.get("rule_sets", {})

        for rule_type, config in rule_sets.items():
            if not config.get("enabled", True):
                continue

            patterns = config.get("file_patterns", [])
            for pattern in patterns:
                if self._match_pattern(file_path, pattern):
                    self._file_pattern_cache[file_path] = rule_type
                    return rule_type

        # 无法确定类型
        self._file_pattern_cache[file_path] = None
        return None

    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """
        匹配文件路径和模式

        支持 glob 模式，包括 ** 通配符

        Args:
            file_path: 文件路径
            pattern: glob 模式

        Returns:
            是否匹配
        """
        from pathlib import PurePosixPath

        # 标准化文件路径（确保有路径前缀）
        normalized_path = file_path if ('/' in file_path or '\\' in file_path) else f"a/{file_path}"
        file_obj = PurePosixPath(normalized_path)

        # 尝试使用 pathlib 的 match 方法
        try:
            if file_obj.match(pattern):
                return True
        except Exception:
            pass

        # 对于 **/*.ext 这样的模式，也匹配 *.ext
        if pattern.startswith('**/'):
            simple_pattern = pattern[3:]  # 去掉 **/
            if fnmatch.fnmatch(os.path.basename(file_path), simple_pattern):
                return True

        # 尝试 fnmatch
        if fnmatch.fnmatch(file_path, pattern):
            return True

        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True

        return False

    def _determine_by_extension(self, file_path: str) -> Optional[str]:
        """
        根据文件扩展名确定规则类型

        Args:
            file_path: 文件路径

        Returns:
            规则类型或 None
        """
        ext = os.path.splitext(file_path)[1].lower()

        backend_extensions = {'.py', '.java'}
        frontend_extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue'}

        if ext in backend_extensions:
            return 'backend'
        elif ext in frontend_extensions:
            return 'frontend'
        else:
            return None

    def _apply_config_filters(self, rules: List[Rule], rule_type: str) -> List[Rule]:
        """
        应用配置文件中的过滤规则

        Args:
            rules: 原始规则列表
            rule_type: 规则类型

        Returns:
            过滤后的规则列表
        """
        if self._config is None:
            return rules

        rule_sets = self._config.get("rule_sets", {})
        config = rule_sets.get(rule_type, {})

        # 获取禁用的规则列表
        disabled_rules: Set[str] = set(config.get("disabled_rules", []))

        # 获取严重程度阈值
        severity_threshold = config.get("severity_threshold", "info")
        severity_order = {
            "error": 1,
            "warning": 2,
            "info": 3
        }
        threshold_level = severity_order.get(severity_threshold, 3)

        # 过滤规则
        filtered_rules = []
        for rule in rules:
            # 跳过禁用的规则
            if rule.id in disabled_rules:
                continue

            # 跳过低于阈值的规则
            # Severity 是继承自 str 的 Enum，直接转换为字符串
            severity_str = str(rule.severity) if hasattr(rule.severity, 'value') else rule.severity
            rule_level = severity_order.get(severity_str, 3)
            if rule_level > threshold_level:
                continue

            # 检查规则是否启用
            if not rule.enabled:
                continue

            filtered_rules.append(rule)

        return filtered_rules

    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """
        根据规则 ID 获取规则

        Args:
            rule_id: 规则 ID

        Returns:
            规则对象，如果未找到则返回 None
        """
        # 确定规则类型（从 ID 前缀判断）
        if rule_id.startswith("backend_"):
            rule_type = "backend"
        elif rule_id.startswith("frontend_"):
            rule_type = "frontend"
        else:
            return None

        # 加载规则
        rules = self.load_rules(rule_type)

        # 查找规则
        for rule in rules:
            if rule.id == rule_id:
                return rule

        return None

    def list_rule_types(self) -> List[str]:
        """
        列出所有可用的规则类型

        Returns:
            规则类型列表
        """
        rule_types = []

        # 扫描规则目录
        if os.path.exists(self.rules_dir):
            for filename in os.listdir(self.rules_dir):
                if filename.endswith("_rules.md"):
                    rule_type = filename.replace("_rules.md", "")
                    rule_types.append(rule_type)

        return sorted(rule_types)

    def get_statistics(self) -> Dict[str, int]:
        """
        获取规则统计信息

        Returns:
            统计信息字典，包含各规则类型的规则数量
        """
        stats = {}

        for rule_type in self.list_rule_types():
            rules = self.load_rules(rule_type)
            stats[rule_type] = len(rules)

        return stats
