

"""
Test cases for ConversationNormalizer

This module contains comprehensive tests for the conversation normalization functionality,
including merge and delete strategies, edge cases, and validation.
"""

import pytest
from typing import List, Dict, Any
from autocoder.common.pruner.conversation_normalizer import (
    ConversationNormalizer,
    NormalizationStrategy,
    NormalizationResult
)


class TestConversationNormalizer:
    """测试会话规整化器的核心功能"""
    
    def setup_method(self):
        """测试前的设置"""
        self.normalizer = ConversationNormalizer()
    
    def test_merge_strategy_basic(self):
        """测试基本的合并策略"""
        # 测试目标：验证连续的相同角色消息能够正确合并
        conversations = [
            {"role": "user", "content": "第一个用户消息"},
            {"role": "user", "content": "第二个用户消息"},
            {"role": "assistant", "content": "助手回复"}
        ]
        
        result = self.normalizer.normalize_conversations(
            conversations, 
            strategy=NormalizationStrategy.MERGE
        )
        
        # 验证结果
        assert result.original_count == 3
        assert result.normalized_count == 2
        assert len(result.changes_made) == 1
        assert result.strategy_used == "merge"
        
        # 验证合并后的内容
        normalized = result.normalized_conversations
        assert len(normalized) == 2
        assert normalized[0]["role"] == "user"
        assert "[消息 1]" in normalized[0]["content"]
        assert "[消息 2]" in normalized[0]["content"]
        assert "第一个用户消息" in normalized[0]["content"]
        assert "第二个用户消息" in normalized[0]["content"]
        assert normalized[1]["role"] == "assistant"
        assert normalized[1]["content"] == "助手回复"
    
    def test_delete_strategy_basic(self):
        """测试基本的删除策略"""
        # 测试目标：验证连续的相同角色消息只保留第一个
        conversations = [
            {"role": "user", "content": "第一个用户消息"},
            {"role": "user", "content": "第二个用户消息"},
            {"role": "assistant", "content": "助手回复"}
        ]
        
        result = self.normalizer.normalize_conversations(
            conversations, 
            strategy=NormalizationStrategy.DELETE
        )
        
        # 验证结果
        assert result.original_count == 3
        assert result.normalized_count == 2
        assert len(result.changes_made) == 1
        assert result.strategy_used == "delete"
        
        # 验证删除后的内容
        normalized = result.normalized_conversations
        assert len(normalized) == 2
        assert normalized[0]["role"] == "user"
        assert normalized[0]["content"] == "第一个用户消息"  # 只保留第一个
        assert normalized[1]["role"] == "assistant"
        assert normalized[1]["content"] == "助手回复"
        
        # 验证变更记录
        change = result.changes_made[0]
        assert change["action"] == "delete"
        assert change["deleted_count"] == 1
        assert change["kept_message"]["content"] == "第一个用户消息"
    
    def test_complex_conversation_merge(self):
        """测试复杂会话的合并策略"""
        # 测试目标：验证多个连续组的正确处理
        conversations = [
            {"role": "user", "content": "用户消息1"},
            {"role": "user", "content": "用户消息2"},
            {"role": "user", "content": "用户消息3"},
            {"role": "assistant", "content": "助手消息1"},
            {"role": "assistant", "content": "助手消息2"},
            {"role": "user", "content": "用户消息4"},
            {"role": "assistant", "content": "助手消息3"}
        ]
        
        result = self.normalizer.normalize_conversations(
            conversations, 
            strategy=NormalizationStrategy.MERGE
        )
        
        # 验证结果
        assert result.original_count == 7
        assert result.normalized_count == 4
        assert len(result.changes_made) == 2  # 两个合并操作
        
        normalized = result.normalized_conversations
        assert len(normalized) == 4
        
        # 验证第一个合并（3个user消息）
        assert normalized[0]["role"] == "user"
        assert "[消息 1]" in normalized[0]["content"]
        assert "[消息 2]" in normalized[0]["content"]
        assert "[消息 3]" in normalized[0]["content"]
        
        # 验证第二个合并（2个assistant消息）
        assert normalized[1]["role"] == "assistant"
        assert "[消息 1]" in normalized[1]["content"]
        assert "[消息 2]" in normalized[1]["content"]
        
        # 验证未合并的消息
        assert normalized[2]["role"] == "user"
        assert normalized[2]["content"] == "用户消息4"
        assert normalized[3]["role"] == "assistant"
        assert normalized[3]["content"] == "助手消息3"
    
    def test_no_normalization_needed(self):
        """测试不需要规整化的正常会话"""
        # 测试目标：验证正常的交替会话不会被修改
        conversations = [
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手回复"},
            {"role": "user", "content": "用户追问"},
            {"role": "assistant", "content": "助手再回复"}
        ]
        
        result = self.normalizer.normalize_conversations(conversations)
        
        # 验证结果
        assert result.original_count == 4
        assert result.normalized_count == 4
        assert len(result.changes_made) == 0
        assert result.normalized_conversations == conversations
    
    def test_empty_conversations(self):
        """测试空会话列表"""
        # 测试目标：验证空输入的正确处理
        result = self.normalizer.normalize_conversations([])
        
        assert result.original_count == 0
        assert result.normalized_count == 0
        assert len(result.changes_made) == 0
        assert result.normalized_conversations == []
    
    def test_single_message(self):
        """测试单条消息"""
        # 测试目标：验证单条消息不会被修改
        conversations = [{"role": "user", "content": "单条消息"}]
        
        result = self.normalizer.normalize_conversations(conversations)
        
        assert result.original_count == 1
        assert result.normalized_count == 1
        assert len(result.changes_made) == 0
        assert result.normalized_conversations == conversations
    
    def test_preserve_additional_fields(self):
        """测试保留消息的额外字段"""
        # 测试目标：验证合并时保留除role和content外的其他字段
        conversations = [
            {"role": "user", "content": "消息1", "timestamp": "2024-01-01", "id": "msg1"},
            {"role": "user", "content": "消息2", "timestamp": "2024-01-02", "id": "msg2"},
            {"role": "assistant", "content": "回复"}
        ]
        
        result = self.normalizer.normalize_conversations(
            conversations, 
            strategy=NormalizationStrategy.MERGE
        )
        
        normalized = result.normalized_conversations
        merged_msg = normalized[0]
        
        # 验证额外字段被保留（来自第一条消息）
        assert "timestamp" in merged_msg
        assert "id" in merged_msg
        assert merged_msg["timestamp"] == "2024-01-01"
        assert merged_msg["id"] == "msg1"


class TestConversationStructureAnalysis:
    """测试会话结构分析功能"""
    
    def setup_method(self):
        """测试前的设置"""
        self.normalizer = ConversationNormalizer()
    
    def test_analyze_normal_structure(self):
        """测试分析正常的会话结构"""
        # 测试目标：验证正常会话结构的分析结果
        conversations = [
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手回复"},
            {"role": "user", "content": "用户追问"},
            {"role": "assistant", "content": "助手再回复"}
        ]
        
        analysis = self.normalizer.analyze_conversation_structure(conversations)
        
        assert analysis["total_messages"] == 4
        assert analysis["role_distribution"] == {"user": 2, "assistant": 2}
        assert analysis["consecutive_groups"] == []
        assert analysis["needs_normalization"] == False
        assert len(analysis["issues"]) == 0
    
    def test_analyze_problematic_structure(self):
        """测试分析有问题的会话结构"""
        # 测试目标：验证问题会话结构的正确识别
        conversations = [
            {"role": "user", "content": "消息1"},
            {"role": "user", "content": "消息2"},
            {"role": "user", "content": "消息3"},
            {"role": "assistant", "content": "回复1"},
            {"role": "assistant", "content": "回复2"}
        ]
        
        analysis = self.normalizer.analyze_conversation_structure(conversations)
        
        assert analysis["total_messages"] == 5
        assert analysis["role_distribution"] == {"user": 3, "assistant": 2}
        assert len(analysis["consecutive_groups"]) == 2
        assert analysis["needs_normalization"] == True
        assert len(analysis["issues"]) >= 2
        
        # 验证连续组信息
        user_group = analysis["consecutive_groups"][0]
        assert user_group["role"] == "user"
        assert user_group["count"] == 3
        assert user_group["start_index"] == 0
        
        assistant_group = analysis["consecutive_groups"][1]
        assert assistant_group["role"] == "assistant"
        assert assistant_group["count"] == 2
        assert assistant_group["start_index"] == 3
    
    def test_analyze_empty_conversations(self):
        """测试分析空会话"""
        # 测试目标：验证空会话的分析结果
        analysis = self.normalizer.analyze_conversation_structure([])
        
        assert analysis["total_messages"] == 0
        assert analysis["role_distribution"] == {}
        assert analysis["consecutive_groups"] == []
        assert analysis["needs_normalization"] == False
        assert analysis["issues"] == []


class TestConversationValidation:
    """测试会话验证功能"""
    
    def setup_method(self):
        """测试前的设置"""
        self.normalizer = ConversationNormalizer()
    
    def test_validate_perfect_conversation(self):
        """测试验证完美的会话"""
        # 测试目标：验证理想的user-assistant交替模式
        conversations = [
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手回复"},
            {"role": "user", "content": "用户追问"},
            {"role": "assistant", "content": "助手再回复"}
        ]
        
        validation = self.normalizer.validate_normalized_conversation(conversations)
        
        assert validation["is_valid"] == True
        assert len(validation["errors"]) == 0
        assert len(validation["warnings"]) == 0
        assert validation["structure_info"]["follows_user_assistant_pattern"] == True
        assert validation["structure_info"]["starts_with_user"] == True
        assert validation["structure_info"]["ends_with_assistant"] == True
    
    def test_validate_consecutive_roles(self):
        """测试验证连续相同角色的问题"""
        # 测试目标：验证连续相同角色被正确识别为错误
        conversations = [
            {"role": "user", "content": "用户消息1"},
            {"role": "user", "content": "用户消息2"},
            {"role": "assistant", "content": "助手回复"}
        ]
        
        validation = self.normalizer.validate_normalized_conversation(conversations)
        
        assert validation["is_valid"] == False
        assert len(validation["errors"]) == 1
        assert "连续的 'user' 角色" in validation["errors"][0]
    
    def test_validate_wrong_pattern(self):
        """测试验证错误的角色模式"""
        # 测试目标：验证不符合user-assistant交替模式的会话
        conversations = [
            {"role": "assistant", "content": "助手先开始"},
            {"role": "user", "content": "用户回应"},
            {"role": "user", "content": "用户继续"}
        ]
        
        validation = self.normalizer.validate_normalized_conversation(conversations)
        
        assert validation["structure_info"]["follows_user_assistant_pattern"] == False
        assert validation["structure_info"]["starts_with_user"] == False
        assert validation["structure_info"]["ends_with_assistant"] == False
        assert len(validation["warnings"]) >= 2  # 至少有模式不匹配的警告


class TestEdgeCases:
    """测试边缘情况"""
    
    def setup_method(self):
        """测试前的设置"""
        self.normalizer = ConversationNormalizer()
    
    def test_empty_content_messages(self):
        """测试空内容消息的处理"""
        # 测试目标：验证空内容消息的正确处理
        conversations = [
            {"role": "user", "content": ""},
            {"role": "user", "content": "有内容的消息"},
            {"role": "assistant", "content": "回复"}
        ]
        
        result = self.normalizer.normalize_conversations(
            conversations, 
            strategy=NormalizationStrategy.MERGE
        )
        
        # 验证空内容也被正确合并
        assert result.normalized_count == 2
        normalized = result.normalized_conversations
        assert "[消息 2]" in normalized[0]["content"]
        assert "有内容的消息" in normalized[0]["content"]
    
    def test_missing_role_field(self):
        """测试缺少role字段的消息"""
        # 测试目标：验证缺少role字段时的处理
        conversations = [
            {"content": "没有role字段"},
            {"content": "也没有role字段"},
            {"role": "assistant", "content": "有role字段"}
        ]
        
        result = self.normalizer.normalize_conversations(conversations)
        
        # 验证缺少role字段的消息被当作相同角色处理
        assert result.normalized_count == 2
        assert len(result.changes_made) == 1
    
    def test_unknown_role(self):
        """测试未知角色的处理"""
        # 测试目标：验证未知角色的正确处理
        conversations = [
            {"role": "system", "content": "系统消息1"},
            {"role": "system", "content": "系统消息2"},
            {"role": "user", "content": "用户消息"},
            {"role": "assistant", "content": "助手回复"}
        ]
        
        result = self.normalizer.normalize_conversations(
            conversations,
            strategy=NormalizationStrategy.MERGE
        )
        
        # 验证系统消息被正确合并
        assert result.normalized_count == 3
        normalized = result.normalized_conversations
        assert normalized[0]["role"] == "system"
        assert "[消息 1]" in normalized[0]["content"]
        assert "[消息 2]" in normalized[0]["content"]
    
    def test_all_same_role(self):
        """测试全部相同角色的会话"""
        # 测试目标：验证全部相同角色时的处理
        conversations = [
            {"role": "user", "content": "消息1"},
            {"role": "user", "content": "消息2"},
            {"role": "user", "content": "消息3"},
            {"role": "user", "content": "消息4"}
        ]
        
        # 测试合并策略
        merge_result = self.normalizer.normalize_conversations(
            conversations,
            strategy=NormalizationStrategy.MERGE
        )
        assert merge_result.normalized_count == 1
        assert len(merge_result.changes_made) == 1
        
        # 测试删除策略
        delete_result = self.normalizer.normalize_conversations(
            conversations,
            strategy=NormalizationStrategy.DELETE
        )
        assert delete_result.normalized_count == 1
        assert len(delete_result.changes_made) == 1
        assert delete_result.changes_made[0]["deleted_count"] == 3


class TestIntegrationScenarios:
    """测试集成场景"""
    
    def setup_method(self):
        """测试前的设置"""
        self.normalizer = ConversationNormalizer()
    
    def test_real_world_scenario_1(self):
        """测试真实场景1：用户多次提问后得到回复"""
        # 测试目标：模拟用户连续提问的真实场景
        conversations = [
            {"role": "user", "content": "我想了解Python"},
            {"role": "user", "content": "特别是关于数据结构的部分"},
            {"role": "user", "content": "你能详细介绍一下列表吗？"},
            {"role": "assistant", "content": "好的，我来详细介绍Python中的列表..."},
            {"role": "user", "content": "那字典呢？"},
            {"role": "assistant", "content": "字典是另一种重要的数据结构..."}
        ]
        
        # 分析原始结构
        analysis = self.normalizer.analyze_conversation_structure(conversations)
        assert analysis["needs_normalization"] == True
        assert len(analysis["consecutive_groups"]) == 1
        
        # 应用合并策略
        result = self.normalizer.normalize_conversations(
            conversations,
            strategy=NormalizationStrategy.MERGE
        )
        
        assert result.normalized_count == 4
        normalized = result.normalized_conversations
        
        # 验证用户的三个问题被合并
        assert normalized[0]["role"] == "user"
        assert "Python" in normalized[0]["content"]
        assert "数据结构" in normalized[0]["content"]
        assert "列表" in normalized[0]["content"]
        
        # 验证后续对话保持不变
        assert normalized[1]["content"] == "好的，我来详细介绍Python中的列表..."
        assert normalized[2]["content"] == "那字典呢？"
        assert normalized[3]["content"] == "字典是另一种重要的数据结构..."
        
        # 验证规整化后的会话
        validation = self.normalizer.validate_normalized_conversation(normalized)
        assert validation["is_valid"] == True
    
    def test_real_world_scenario_2(self):
        """测试真实场景2：助手多次回复后用户提问"""
        # 测试目标：模拟助手连续回复的真实场景
        conversations = [
            {"role": "user", "content": "请解释机器学习"},
            {"role": "assistant", "content": "机器学习是人工智能的一个分支..."},
            {"role": "assistant", "content": "它主要包括监督学习、无监督学习..."},
            {"role": "assistant", "content": "常见的算法有线性回归、决策树..."},
            {"role": "user", "content": "能举个具体例子吗？"},
            {"role": "assistant", "content": "当然，比如预测房价..."}
        ]
        
        # 应用删除策略
        result = self.normalizer.normalize_conversations(
            conversations,
            strategy=NormalizationStrategy.DELETE
        )
        
        assert result.normalized_count == 4
        normalized = result.normalized_conversations
        
        # 验证只保留第一个助手回复
        assert normalized[1]["role"] == "assistant"
        assert normalized[1]["content"] == "机器学习是人工智能的一个分支..."
        
        # 验证变更记录
        change = result.changes_made[0]
        assert change["action"] == "delete"
        assert change["deleted_count"] == 2
        
        # 验证规整化后的会话
        validation = self.normalizer.validate_normalized_conversation(normalized)
        assert validation["is_valid"] == True


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "-s"])


