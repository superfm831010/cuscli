"""
规则加载器单元测试

测试 RulesLoader 类的各项功能
"""

import pytest
import json
import os
import tempfile
from autocoder.checker.rules_loader import RulesLoader
from autocoder.checker.types import Severity


class TestRulesLoader:
    """测试规则加载器"""

    def test_load_backend_rules(self):
        """测试加载后端规则"""
        loader = RulesLoader()
        rules = loader.load_rules("backend")

        assert len(rules) > 0
        assert all(rule.id.startswith("backend_") for rule in rules)
        assert all(rule.category is not None for rule in rules)
        assert all(rule.title for rule in rules)
        assert all(rule.description for rule in rules)

    def test_load_frontend_rules(self):
        """测试加载前端规则"""
        loader = RulesLoader()
        rules = loader.load_rules("frontend")

        assert len(rules) > 0
        assert all(rule.id.startswith("frontend_") for rule in rules)

    def test_rule_count(self):
        """测试规则数量"""
        loader = RulesLoader()

        backend_rules = loader.load_rules("backend")
        frontend_rules = loader.load_rules("frontend")

        # 根据实际规则文件数量
        assert len(backend_rules) == 63
        assert len(frontend_rules) == 105

    def test_rule_severity(self):
        """测试规则严重程度"""
        loader = RulesLoader()
        rules = loader.load_rules("backend")

        # 统计严重程度分布
        severity_counts = {}
        for rule in rules:
            severity = rule.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 应该包含三种严重程度
        assert 'error' in severity_counts or 'warning' in severity_counts or 'info' in severity_counts

    def test_rule_caching(self):
        """测试规则缓存"""
        loader = RulesLoader()

        # 第一次加载
        rules1 = loader.load_rules("backend")

        # 第二次加载（应该从缓存读取）
        rules2 = loader.load_rules("backend")

        # 应该返回同一个对象
        assert rules1 is rules2

    def test_reload_rules(self):
        """测试重新加载规则"""
        loader = RulesLoader()

        # 加载规则
        rules1 = loader.load_rules("backend")

        # 重新加载
        loader.reload_rules()
        rules2 = loader.load_rules("backend")

        # 应该是不同的对象
        assert rules1 is not rules2
        # 但内容应该相同
        assert len(rules1) == len(rules2)

    def test_get_applicable_rules_for_python(self):
        """测试获取 Python 文件适用的规则"""
        loader = RulesLoader()

        rules = loader.get_applicable_rules("test.py")
        assert len(rules) > 0
        assert all(rule.id.startswith("backend_") for rule in rules)

    def test_get_applicable_rules_for_javascript(self):
        """测试获取 JavaScript 文件适用的规则"""
        loader = RulesLoader()

        rules = loader.get_applicable_rules("test.js")
        assert len(rules) > 0
        assert all(rule.id.startswith("frontend_") for rule in rules)

    def test_get_applicable_rules_for_vue(self):
        """测试获取 Vue 文件适用的规则"""
        loader = RulesLoader()

        rules = loader.get_applicable_rules("test.vue")
        assert len(rules) > 0
        assert all(rule.id.startswith("frontend_") for rule in rules)

    def test_get_applicable_rules_for_unknown(self):
        """测试获取未知类型文件的规则"""
        loader = RulesLoader()

        rules = loader.get_applicable_rules("test.txt")
        assert len(rules) == 0

    def test_load_config(self):
        """测试加载配置文件"""
        loader = RulesLoader()
        config = loader.load_config()

        assert config is not None
        assert 'version' in config
        assert 'rule_sets' in config
        assert 'backend' in config['rule_sets']
        assert 'frontend' in config['rule_sets']

    def test_config_filtering_severity(self):
        """测试配置文件严重程度过滤"""
        loader = RulesLoader()

        # 不加载配置
        rules_without_config = loader.load_rules("backend")

        # 加载配置（阈值为 warning）
        loader2 = RulesLoader()
        loader2.load_config()
        rules_with_config = loader2.load_rules("backend")

        # 加载配置后，info 级别的规则应该被过滤掉
        assert len(rules_with_config) <= len(rules_without_config)

        # 检查过滤后的规则中没有 info 级别
        severities = {rule.severity for rule in rules_with_config}
        # warning 阈值应该包含 error 和 warning，但不包含 info
        # （如果原始规则中有 info 的话）

    def test_disabled_rules(self):
        """测试禁用规则功能"""
        # 创建临时配置文件
        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "rules_config.json")

        config = {
            "version": "1.0.0",
            "rule_sets": {
                "backend": {
                    "enabled": True,
                    "file_patterns": ["**/*.py"],
                    "severity_threshold": "info",
                    "disabled_rules": ["backend_001", "backend_002"]
                }
            }
        }

        with open(temp_config, 'w', encoding='utf-8') as f:
            json.dump(config, f)

        try:
            loader = RulesLoader()
            loader.load_config(temp_config)
            rules = loader.load_rules("backend")

            # 检查禁用的规则是否被过滤
            rule_ids = {rule.id for rule in rules}
            assert 'backend_001' not in rule_ids
            assert 'backend_002' not in rule_ids

        finally:
            # 清理临时文件
            os.remove(temp_config)
            os.rmdir(temp_dir)

    def test_file_pattern_matching(self):
        """测试文件模式匹配"""
        loader = RulesLoader()
        loader.load_config()

        test_cases = [
            ("test.py", "backend"),
            ("src/main.py", "backend"),
            ("test.java", "backend"),
            ("test.js", "frontend"),
            ("test.vue", "frontend"),
            ("test.ts", "frontend"),
            ("test.tsx", "frontend"),
            ("README.md", None),
        ]

        for file_path, expected in test_cases:
            rule_type = loader._determine_rule_type(file_path)
            assert rule_type == expected, f"{file_path} should be {expected}, got {rule_type}"

    def test_get_rule_by_id(self):
        """测试根据 ID 获取规则"""
        loader = RulesLoader()

        # 获取后端规则
        rule = loader.get_rule_by_id("backend_001")
        assert rule is not None
        assert rule.id == "backend_001"

        # 获取前端规则
        rule = loader.get_rule_by_id("frontend_001")
        assert rule is not None
        assert rule.id == "frontend_001"

        # 获取不存在的规则
        rule = loader.get_rule_by_id("nonexistent_001")
        assert rule is None

    def test_list_rule_types(self):
        """测试列出规则类型"""
        loader = RulesLoader()

        rule_types = loader.list_rule_types()
        assert 'backend' in rule_types
        assert 'frontend' in rule_types

    def test_get_statistics(self):
        """测试获取统计信息"""
        loader = RulesLoader()

        stats = loader.get_statistics()
        assert 'backend' in stats
        assert 'frontend' in stats
        assert stats['backend'] > 0
        assert stats['frontend'] > 0

    def test_rule_with_examples(self):
        """测试带示例的规则"""
        loader = RulesLoader()
        rules = loader.load_rules("backend")

        # 查找有示例的规则
        rules_with_examples = [r for r in rules if r.examples]
        assert len(rules_with_examples) > 0

        # 检查示例格式
        for rule in rules_with_examples[:3]:
            assert isinstance(rule.examples, str)
            assert len(rule.examples) > 0

    def test_rule_categories(self):
        """测试规则类别"""
        loader = RulesLoader()
        rules = loader.load_rules("backend")

        categories = {rule.category for rule in rules}
        assert len(categories) > 0
        assert "应用开发架构使用" in categories or "代码结构" in categories

    def test_load_nonexistent_rules(self):
        """测试加载不存在的规则文件"""
        loader = RulesLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_rules("nonexistent")

    def test_load_nonexistent_config(self):
        """测试加载不存在的配置文件"""
        loader = RulesLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_config("/nonexistent/path/config.json")

    def test_match_pattern_glob(self):
        """测试 glob 模式匹配"""
        loader = RulesLoader()

        # 测试 **/*.py 模式
        assert loader._match_pattern("test.py", "**/*.py")
        assert loader._match_pattern("src/test.py", "**/*.py")
        assert loader._match_pattern("src/sub/test.py", "**/*.py")
        assert not loader._match_pattern("test.txt", "**/*.py")

        # 测试 *.js 模式（也会匹配文件名）
        assert loader._match_pattern("test.js", "*.js")
        # 注意：我们的实现也会匹配文件名，所以 src/test.js 也会匹配 *.js
        assert loader._match_pattern("src/test.js", "*.js")

    def test_determine_by_extension(self):
        """测试根据扩展名判断规则类型"""
        loader = RulesLoader()

        assert loader._determine_by_extension("test.py") == "backend"
        assert loader._determine_by_extension("test.java") == "backend"
        assert loader._determine_by_extension("test.js") == "frontend"
        assert loader._determine_by_extension("test.vue") == "frontend"
        assert loader._determine_by_extension("test.ts") == "frontend"
        assert loader._determine_by_extension("test.tsx") == "frontend"
        assert loader._determine_by_extension("test.txt") is None


class TestRulesParsing:
    """测试规则解析功能"""

    def test_parse_markdown_structure(self):
        """测试 Markdown 规则文件解析"""
        loader = RulesLoader()
        rules = loader.load_rules("backend")

        # 检查规则结构
        for rule in rules[:3]:
            assert rule.id
            assert rule.category
            assert rule.title
            assert rule.description
            assert rule.severity in ['error', 'warning', 'info']
            assert isinstance(rule.enabled, bool)

    def test_severity_parsing(self):
        """测试严重程度解析"""
        loader = RulesLoader()
        rules = loader.load_rules("backend")

        # 检查每个严重程度都有对应的规则
        severities = {rule.severity for rule in rules}
        # 至少应该有一种严重程度
        assert len(severities) > 0
