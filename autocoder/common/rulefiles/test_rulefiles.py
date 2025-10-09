# -*- coding: utf-8 -*-
"""
AutoCoder 规则文件管理模块测试

测试重点：
1. 基本的规则文件加载和解析功能
2. 缓存机制，特别是基于文件 MD5 的缓存失效检测
3. generate_always_apply_summary 和 generate_conditional_rules_index 的缓存失效
4. 使用临时目录进行隔离测试
"""

import pytest
import tempfile
import os
import json
import time
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

# 导入要测试的模块
from autocoder.common.rulefiles import (
    get_rules, get_parsed_rules, parse_rule_file, reset_rules_manager,
    auto_select_rules, get_required_and_index_rules,
    generate_always_apply_summary, generate_conditional_rules_index,
    invalidate_rules_cache, get_rules_cache_stats, check_rules_cache_validity,
    AutocoderRulesManager, RuleSelector
)
from autocoder.common.rulefiles.models import (
    RuleFile, AlwaysApplyRuleSummary, ConditionalRulesIndex, RuleRelevance
)
from autocoder.common.rulefiles.utils.cache import RuleCacheManager


class MockLLM:
    """模拟 LLM，用于测试"""
    
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.call_count = 0
        
    def chat_oai(self, messages, **kwargs):
        """模拟 chat_oai 方法"""
        self.call_count += 1
        # 根据消息内容返回不同的响应
        message_content = str(messages)
        
        if "判断规则是否适用" in message_content:
            return [{
                "content": json.dumps({
                    "is_relevant": True,
                    "reason": "测试相关规则"
                })
            }]
        elif "Merge all always-apply rules" in message_content:
            return [{
                "content": f"合并的必须应用规则摘要 (调用次数: {self.call_count})"
            }]
        elif "Generate an index directory" in message_content:
            return [{
                "content": f"条件规则索引目录 (调用次数: {self.call_count})"
            }]
        
        return [{"content": "模拟响应"}]


class MockPromptFunction:
    """模拟 byzerllm.prompt 装饰器生成的函数"""
    
    def __init__(self, return_value: str = "默认返回值"):
        self.return_value = return_value
        
    def with_llm(self, llm):
        return self
        
    def run(self, **kwargs):
        return self.return_value
        
    def with_return_type(self, return_type):
        if return_type == RuleRelevance:
            # 为 RuleRelevance 返回特殊的模拟对象
            class MockRuleRelevance:
                def __init__(self):
                    self.is_relevant = True
                    self.reason = "测试理由"
            return MockWithReturnType(MockRuleRelevance())
        return self
        

class MockWithReturnType:
    """模拟 with_return_type 后的对象"""
    
    def __init__(self, return_obj):
        self.return_obj = return_obj
        
    def run(self, **kwargs):
        return self.return_obj


@pytest.fixture
def temp_project_dir():
    """创建临时项目目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def rules_dir(temp_project_dir):
    """创建临时规则目录"""
    rules_path = os.path.join(temp_project_dir, ".autocoderrules")
    os.makedirs(rules_path, exist_ok=True)
    return rules_path


@pytest.fixture
def mock_llm():
    """创建模拟 LLM"""
    return MockLLM()


@pytest.fixture(autouse=True)
def cleanup_rules_manager():
    """每个测试后清理单例"""
    yield
    reset_rules_manager()


def create_rule_file(rules_dir: str, filename: str, content: str, 
                    description: str = "", globs: list = None, always_apply: bool = False):
    """帮助函数：创建规则文件"""
    globs = globs or []
    
    # 构建 YAML 前置元数据
    yaml_content = f"""---
description: "{description}"
globs: {json.dumps(globs)}
alwaysApply: {str(always_apply).lower()}
---
{content}"""
    
    file_path = os.path.join(rules_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    return file_path


def modify_rule_file(file_path: str, new_content: str):
    """帮助函数：修改规则文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 保持 YAML 头部，只修改内容部分
    if '---' in content:
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_part = f"---{parts[1]}---"
            modified_content = f"{yaml_part}\n{new_content}"
        else:
            modified_content = new_content
    else:
        modified_content = new_content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)


class TestBasicFunctionality:
    """测试基本功能"""
    
    def test_get_rules_empty_directory(self, temp_project_dir, rules_dir):
        """测试空目录的规则获取"""
        with patch('os.getcwd', return_value=temp_project_dir):
            rules = get_rules()
            assert rules == {}
    
    def test_get_rules_with_files(self, temp_project_dir, rules_dir):
        """测试有规则文件的目录"""
        # 创建测试规则文件
        create_rule_file(rules_dir, "rule1.md", "规则1内容", "测试规则1")
        create_rule_file(rules_dir, "rule2.md", "规则2内容", "测试规则2", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            rules = get_rules()
            assert len(rules) == 2
            assert any("规则1内容" in content for content in rules.values())
            assert any("规则2内容" in content for content in rules.values())
    
    def test_get_parsed_rules(self, temp_project_dir, rules_dir):
        """测试解析后的规则获取"""
        create_rule_file(rules_dir, "rule1.md", "规则1内容", "测试规则1", ["*.py"], True)
        create_rule_file(rules_dir, "rule2.md", "规则2内容", "测试规则2", ["*.js"], False)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            parsed_rules = get_parsed_rules()
            assert len(parsed_rules) == 2
            
            # 检查解析的内容
            always_apply_rules = [r for r in parsed_rules if r.always_apply]
            conditional_rules = [r for r in parsed_rules if not r.always_apply]
            
            assert len(always_apply_rules) == 1
            assert len(conditional_rules) == 1
            assert always_apply_rules[0].description == "测试规则1"
            assert always_apply_rules[0].globs == ["*.py"]
    
    def test_parse_single_rule_file(self, rules_dir):
        """测试单个规则文件解析"""
        file_path = create_rule_file(
            rules_dir, "test.md", "测试内容", 
            "测试描述", ["*.py", "*.js"], True
        )
        
        rule = parse_rule_file(file_path)
        assert rule.description == "测试描述"
        assert rule.globs == ["*.py", "*.js"]
        assert rule.always_apply is True
        assert rule.content == "测试内容"
        assert rule.file_path == file_path
    
    def test_get_required_and_index_rules(self, temp_project_dir, rules_dir):
        """测试获取必须应用的规则和 Index.md 文件"""
        create_rule_file(rules_dir, "rule1.md", "普通规则", "普通规则", always_apply=False)
        create_rule_file(rules_dir, "rule2.md", "必须应用规则", "必须应用", always_apply=True)
        create_rule_file(rules_dir, "Index.md", "索引文件", "索引", always_apply=False)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            required_rules = get_required_and_index_rules()
            assert len(required_rules) == 2  # 一个 always_apply=True，一个 Index.md
            
            contents = list(required_rules.values())
            assert "必须应用规则" in contents
            assert "索引文件" in contents


class TestRuleSelection:
    """测试规则选择功能"""
    
    def test_auto_select_rules_without_llm(self, temp_project_dir, rules_dir):
        """测试没有 LLM 时的规则选择（只选择 always_apply=True 的规则）"""
        create_rule_file(rules_dir, "rule1.md", "普通规则", always_apply=False)
        create_rule_file(rules_dir, "rule2.md", "必须应用规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            selected_rules = auto_select_rules("测试上下文")
            assert len(selected_rules) == 1
            assert "必须应用规则" in list(selected_rules.values())[0]
    
    def test_auto_select_rules_with_llm(self, temp_project_dir, rules_dir, mock_llm):
        """测试有 LLM 时的规则选择"""
        create_rule_file(rules_dir, "rule1.md", "条件规则", always_apply=False)
        create_rule_file(rules_dir, "rule2.md", "必须应用规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            with patch('autocoder.common.rulefiles.core.selector.byzerllm.prompt') as mock_prompt:
                # 模拟 prompt 函数
                mock_prompt_func = MockPromptFunction()
                mock_prompt.return_value = mock_prompt_func
                
                # 模拟 RuleSelector
                selector = RuleSelector(llm=mock_llm)
                
                # 模拟 _evaluate_rule 方法返回相关规则
                with patch.object(selector, '_evaluate_rule') as mock_eval:
                    mock_eval.return_value = (Mock(file_path="rule1.md", content="条件规则"), True, "相关")
                    
                    selected_rules = selector.get_selected_rules_content("测试上下文")
                    # 应该包含 always_apply 规则和被 LLM 选择的条件规则
                    assert len(selected_rules) >= 1


class TestCacheFunctionality:
    """测试缓存功能"""
    
    def test_cache_manager_basic_operations(self, temp_project_dir, rules_dir):
        """测试缓存管理器基本操作"""
        cache_dir = os.path.join(rules_dir, ".cache")
        cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
        
        # 创建测试规则
        create_rule_file(rules_dir, "rule1.md", "测试规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            rules = get_parsed_rules()
            
        # 测试摘要缓存
        summary = AlwaysApplyRuleSummary(
            summary="测试摘要", 
            rule_count=1, 
            covered_areas=["测试"]
        )
        
        # 保存缓存
        cache_manager.save_summary_cache(summary, rules)
        
        # 获取缓存
        cached_summary = cache_manager.get_summary_cache(rules)
        assert cached_summary is not None
        assert cached_summary.summary == "测试摘要"
        assert cached_summary.rule_count == 1
        
        # 清理
        cache_manager.cleanup()
    
    def test_cache_invalidation_on_content_change(self, temp_project_dir, rules_dir, mock_llm):
        """测试内容变更时缓存失效"""
        # 创建初始规则文件
        rule_file = create_rule_file(rules_dir, "rule1.md", "初始内容", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取初始规则
            rules = get_parsed_rules()
            assert len(rules) == 1
            initial_rule = rules[0]
            assert initial_rule.content == "初始内容"
            
            # 创建模拟摘要
            summary1 = AlwaysApplyRuleSummary(
                summary="初始摘要内容",
                rule_count=1,
                covered_areas=[]
            )
            
            # 保存缓存
            cache_manager.save_summary_cache(summary1, rules)
            
            # 验证缓存可以获取
            cached_summary = cache_manager.get_summary_cache(rules)
            assert cached_summary is not None
            assert cached_summary.summary == "初始摘要内容"
            
            # 修改规则文件内容
            modify_rule_file(rule_file, "修改后的内容")
            
            # 重新获取规则，内容应该已经变化
            reset_rules_manager()  # 重置管理器以重新加载文件
            updated_rules = get_parsed_rules()
            assert len(updated_rules) == 1
            updated_rule = updated_rules[0]
            assert updated_rule.content == "修改后的内容"
            
            # 验证缓存应该失效（因为文件内容变了）
            cached_summary_after = cache_manager.get_summary_cache(updated_rules)
            assert cached_summary_after is None  # 缓存应该失效
            
            cache_manager.cleanup()
    
    def test_cache_invalidation_on_file_addition(self, temp_project_dir, rules_dir, mock_llm):
        """测试添加文件时缓存失效"""
        # 创建初始规则文件
        create_rule_file(rules_dir, "rule1.md", "规则1", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取初始规则
            rules = get_parsed_rules()
            assert len(rules) == 1
            
            # 创建模拟摘要
            summary1 = AlwaysApplyRuleSummary(
                summary="单个规则摘要",
                rule_count=1,
                covered_areas=[]
            )
            
            # 保存缓存
            cache_manager.save_summary_cache(summary1, rules)
            
            # 验证缓存可以获取
            cached_summary = cache_manager.get_summary_cache(rules)
            assert cached_summary is not None
            assert cached_summary.rule_count == 1
            
            # 添加新的规则文件
            create_rule_file(rules_dir, "rule2.md", "规则2", always_apply=True)
            
            # 重新获取规则，应该有两个规则了
            reset_rules_manager()  # 重置管理器以重新加载文件
            updated_rules = get_parsed_rules()
            assert len(updated_rules) == 2
            
            # 验证缓存应该失效（因为规则数量变化了）
            cached_summary_after = cache_manager.get_summary_cache(updated_rules)
            assert cached_summary_after is None  # 缓存应该失效
            
            cache_manager.cleanup()
    
    def test_cache_invalidation_on_file_deletion(self, temp_project_dir, rules_dir, mock_llm):
        """测试删除文件时缓存失效"""
        # 创建两个规则文件
        rule_file1 = create_rule_file(rules_dir, "rule1.md", "规则1", always_apply=True)
        rule_file2 = create_rule_file(rules_dir, "rule2.md", "规则2", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取初始规则
            rules = get_parsed_rules()
            assert len(rules) == 2
            
            # 创建模拟摘要
            summary1 = AlwaysApplyRuleSummary(
                summary="两个规则摘要",
                rule_count=2,
                covered_areas=[]
            )
            
            # 保存缓存
            cache_manager.save_summary_cache(summary1, rules)
            
            # 验证缓存可以获取
            cached_summary = cache_manager.get_summary_cache(rules)
            assert cached_summary is not None
            assert cached_summary.rule_count == 2
            
            # 删除一个规则文件
            os.remove(rule_file2)
            
            # 重新获取规则，应该只有一个规则了
            reset_rules_manager()  # 重置管理器以重新加载文件
            updated_rules = get_parsed_rules()
            assert len(updated_rules) == 1
            
            # 验证缓存应该失效（因为规则数量减少了）
            cached_summary_after = cache_manager.get_summary_cache(updated_rules)
            assert cached_summary_after is None  # 缓存应该失效
            
            cache_manager.cleanup()
    
    def test_conditional_rules_index_cache_invalidation(self, temp_project_dir, rules_dir, mock_llm):
        """测试条件规则索引的缓存失效"""
        # 创建条件规则文件
        rule_file = create_rule_file(rules_dir, "conditional.md", "条件规则内容", always_apply=False)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取初始规则
            rules = get_parsed_rules()
            conditional_rules = [rule for rule in rules if not rule.always_apply]
            assert len(conditional_rules) == 1
            assert conditional_rules[0].content == "条件规则内容"
            
            # 创建模拟索引
            index1 = ConditionalRulesIndex(
                index_content="初始索引内容",
                rule_count=1,
                categories=[]
            )
            
            # 保存缓存
            cache_manager.save_index_cache(index1, conditional_rules)
            
            # 验证缓存可以获取
            cached_index = cache_manager.get_index_cache(conditional_rules)
            assert cached_index is not None
            assert cached_index.index_content == "初始索引内容"
            
            # 修改条件规则文件
            modify_rule_file(rule_file, "修改后的条件规则内容")
            
            # 重新获取规则，内容应该已经变化
            reset_rules_manager()  # 重置管理器以重新加载文件
            updated_rules = get_parsed_rules()
            updated_conditional_rules = [rule for rule in updated_rules if not rule.always_apply]
            assert len(updated_conditional_rules) == 1
            assert updated_conditional_rules[0].content == "修改后的条件规则内容"
            
            # 验证缓存应该失效（因为文件内容变了）
            cached_index_after = cache_manager.get_index_cache(updated_conditional_rules)
            assert cached_index_after is None  # 缓存应该失效
            
            cache_manager.cleanup()
    
    def test_cache_validity_check(self, temp_project_dir, rules_dir):
        """测试缓存有效性检查"""
        create_rule_file(rules_dir, "rule1.md", "测试规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 检查初始缓存状态
            validity = check_rules_cache_validity()
            assert validity['status'] == 'success'
            
            # 获取缓存统计信息
            stats = get_rules_cache_stats()
            assert stats['status'] in ['success', 'no_rules_directories']
    
    def test_manual_cache_invalidation(self, temp_project_dir, rules_dir, mock_llm):
        """测试手动缓存失效"""
        create_rule_file(rules_dir, "rule1.md", "测试规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取规则
            rules = get_parsed_rules()
            assert len(rules) == 1
            
            # 创建模拟摘要
            summary1 = AlwaysApplyRuleSummary(
                summary="测试摘要",
                rule_count=1,
                covered_areas=[]
            )
            
            # 保存缓存
            cache_manager.save_summary_cache(summary1, rules)
            
            # 验证缓存可以获取
            cached_summary = cache_manager.get_summary_cache(rules)
            assert cached_summary is not None
            assert cached_summary.summary == "测试摘要"
            
            # 手动失效缓存
            invalidate_rules_cache()
            
            # 验证缓存已被清理
            cached_summary_after = cache_manager.get_summary_cache(rules)
            assert cached_summary_after is None  # 缓存应该已被清理
            
            cache_manager.cleanup()


class TestMD5BasedCacheInvalidation:
    """测试基于 MD5 的缓存失效机制"""
    
    def test_md5_calculation_accuracy(self, temp_project_dir, rules_dir):
        """测试 MD5 计算的准确性"""
        cache_dir = os.path.join(rules_dir, ".cache")
        cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
        
        # 创建测试文件
        test_file = os.path.join(rules_dir, "test.md")
        content = "测试内容"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 计算 MD5
        md5_hash = cache_manager._calculate_file_md5(test_file)
        
        # 验证 MD5 计算正确性
        expected_md5 = hashlib.md5(content.encode('utf-8')).hexdigest()
        assert md5_hash == expected_md5
        
        cache_manager.cleanup()
    
    def test_directory_md5_tracking(self, temp_project_dir, rules_dir):
        """测试目录级别的 MD5 跟踪"""
        cache_dir = os.path.join(rules_dir, ".cache")
        cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
        
        # 创建多个规则文件
        create_rule_file(rules_dir, "rule1.md", "规则1内容")
        create_rule_file(rules_dir, "rule2.md", "规则2内容")
        
        # 计算目录 MD5 映射
        rules_directories = cache_manager._get_rules_directories()
        md5_map = cache_manager._calculate_directory_md5(rules_directories)
        
        # 验证所有 .md 文件都被跟踪
        md5_files = [path for path in md5_map.keys() if path.endswith('.md')]
        assert len(md5_files) == 2
        
        cache_manager.cleanup()
    
    def test_subtle_content_changes_detected(self, temp_project_dir, rules_dir, mock_llm):
        """测试微小内容变更能被检测到"""
        rule_file = create_rule_file(rules_dir, "rule1.md", "原始内容", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取初始规则
            rules = get_parsed_rules()
            assert len(rules) == 1
            assert rules[0].content == "原始内容"
            
            # 创建模拟摘要
            summary1 = AlwaysApplyRuleSummary(
                summary="原始摘要",
                rule_count=1,
                covered_areas=[]
            )
            
            # 保存缓存
            cache_manager.save_summary_cache(summary1, rules)
            
            # 验证缓存可以获取
            cached_summary = cache_manager.get_summary_cache(rules)
            assert cached_summary is not None
            assert cached_summary.summary == "原始摘要"
            
            # 进行微小的内容修改（仅添加一个字符）
            modify_rule_file(rule_file, "原始内容a")
            
            # 重新获取规则，内容应该已经变化
            reset_rules_manager()  # 重置管理器以重新加载文件
            updated_rules = get_parsed_rules()
            assert len(updated_rules) == 1
            assert updated_rules[0].content == "原始内容a"
            
            # 验证缓存应该失效（即使只是微小变化）
            cached_summary_after = cache_manager.get_summary_cache(updated_rules)
            assert cached_summary_after is None  # 缓存应该失效
            
            cache_manager.cleanup()
    
    def test_cache_metadata_structure(self, temp_project_dir, rules_dir, mock_llm):
        """测试缓存元数据结构"""
        create_rule_file(rules_dir, "rule1.md", "测试规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 获取规则
            rules = get_parsed_rules()
            assert len(rules) == 1
            
            # 创建模拟摘要
            summary = AlwaysApplyRuleSummary(
                summary="测试摘要",
                rule_count=1,
                covered_areas=[]
            )
            
            # 保存缓存以创建元数据
            cache_manager.save_summary_cache(summary, rules)
            
            # 检查缓存元数据结构
            metadata_file = os.path.join(cache_dir, "cache_metadata.json")
            
            assert os.path.exists(metadata_file)
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 验证元数据结构
            assert 'summary' in metadata
            summary_info = metadata['summary']
            assert 'rules_hash' in summary_info
            assert 'timestamp' in summary_info
            assert 'rule_count' in summary_info
            assert 'rule_files' in summary_info
            assert 'file_md5_map' in summary_info
            assert 'cache_version' in summary_info
            
            # 验证数据的正确性
            assert summary_info['rule_count'] == 1
            assert len(summary_info['rule_files']) == 1
            assert len(summary_info['file_md5_map']) == 1
            assert summary_info['cache_version'] == '1.1'
            
            cache_manager.cleanup()


class TestIntegrationScenarios:
    """集成测试场景"""
    
    def test_full_workflow_with_cache_invalidation(self, temp_project_dir, rules_dir, mock_llm):
        """测试完整的工作流程和缓存失效"""
        # 第一阶段：创建初始规则
        create_rule_file(rules_dir, "always.md", "必须应用规则", always_apply=True)
        create_rule_file(rules_dir, "conditional.md", "条件规则", always_apply=False)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
            
            # 第一阶段：获取初始规则
            rules = get_parsed_rules()
            always_apply_rules = [rule for rule in rules if rule.always_apply]
            conditional_rules = [rule for rule in rules if not rule.always_apply]
            
            assert len(always_apply_rules) == 1
            assert len(conditional_rules) == 1
            
            # 创建初始缓存
            summary1 = AlwaysApplyRuleSummary(
                summary="初始摘要",
                rule_count=1,
                covered_areas=[]
            )
            cache_manager.save_summary_cache(summary1, always_apply_rules)
            
            index1 = ConditionalRulesIndex(
                index_content="初始索引",
                rule_count=1,
                categories=[]
            )
            cache_manager.save_index_cache(index1, conditional_rules)
            
            # 验证缓存
            assert cache_manager.get_summary_cache(always_apply_rules) is not None
            assert cache_manager.get_index_cache(conditional_rules) is not None
            
            # 第二阶段：添加新规则
            create_rule_file(rules_dir, "always2.md", "第二个必须应用规则", always_apply=True)
            create_rule_file(rules_dir, "conditional2.md", "第二个条件规则", always_apply=False)
            
            # 重新获取规则
            reset_rules_manager()
            updated_rules = get_parsed_rules()
            updated_always_apply_rules = [rule for rule in updated_rules if rule.always_apply]
            updated_conditional_rules = [rule for rule in updated_rules if not rule.always_apply]
            
            assert len(updated_always_apply_rules) == 2
            assert len(updated_conditional_rules) == 2
            
            # 验证缓存失效
            assert cache_manager.get_summary_cache(updated_always_apply_rules) is None
            assert cache_manager.get_index_cache(updated_conditional_rules) is None
            
            cache_manager.cleanup()
    
    def test_concurrent_cache_access_safety(self, temp_project_dir, rules_dir, mock_llm):
        """测试并发缓存访问的安全性"""
        create_rule_file(rules_dir, "rule1.md", "测试规则", always_apply=True)
        
        with patch('os.getcwd', return_value=temp_project_dir):
            # 直接测试缓存管理器的功能
            cache_dir = os.path.join(rules_dir, ".cache")
            
            # 获取规则
            rules = get_parsed_rules()
            assert len(rules) == 1
            
            # 创建模拟摘要
            summary = AlwaysApplyRuleSummary(
                summary="并发测试摘要",
                rule_count=1,
                covered_areas=[]
            )
            
            # 模拟并发访问缓存管理器
            cache_managers = []
            for i in range(3):
                cache_manager = RuleCacheManager(cache_dir=cache_dir, project_root=temp_project_dir)
                cache_managers.append(cache_manager)
            
            # 所有缓存管理器都保存相同的摘要
            for cache_manager in cache_managers:
                cache_manager.save_summary_cache(summary, rules)
            
            # 验证所有缓存管理器都能正确获取缓存
            cached_summaries = []
            for cache_manager in cache_managers:
                cached_summary = cache_manager.get_summary_cache(rules)
                cached_summaries.append(cached_summary)
            
            # 验证结果一致性
            for cached_summary in cached_summaries:
                assert cached_summary is not None
                assert cached_summary.summary == "并发测试摘要"
                assert cached_summary.rule_count == 1
            
            # 清理所有缓存管理器
            for cache_manager in cache_managers:
                cache_manager.cleanup()
