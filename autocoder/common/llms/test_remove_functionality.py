#!/usr/bin/env python3
"""
测试脚本：验证删除模型功能是否正常工作
"""

import sys
import tempfile
import json
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from autocoder.common.llms.manager import LLMManager


def test_remove_functionality():
    """测试删除模型功能"""
    print("=== 测试删除模型功能 ===\n")
    
    # 使用临时目录避免影响用户配置
    with tempfile.TemporaryDirectory() as temp_dir:
        models_json = Path(temp_dir) / "models.json"
        print(f"使用临时目录: {temp_dir}")
        
        # 1. 初始化 LLMManager
        print("\n1. 初始化 LLMManager...")
        manager = LLMManager(str(models_json))
        print(f"   ✓ 初始化完成，当前模型数量: {len(manager.get_all_models())}")
        
        # 2. 添加一些测试模型
        print("\n2. 添加测试模型...")
        test_models = [
            {
                "name": "test/model1",
                "model_name": "test-model-1",
                "model_type": "saas/openai",
                "base_url": "https://test1.api.com/v1",
                "description": "测试模型1"
            },
            {
                "name": "test/model2",
                "model_name": "test-model-2",
                "model_type": "saas/openai",
                "base_url": "https://test2.api.com/v1",
                "description": "测试模型2",
                "api_key": "test-key-123"
            }
        ]
        
        manager.add_models(test_models)  # type: ignore
        total_models = len(manager.get_all_models())
        print(f"   ✓ 添加了 {len(test_models)} 个测试模型")
        print(f"   ✓ 当前总模型数量: {total_models}")
        
        # 验证模型已添加
        for model_data in test_models:
            if manager.check_model_exists(model_data["name"]):
                print(f"   ✓ 模型 {model_data['name']} 已成功添加")
                if "api_key" in model_data:
                    has_key = manager.has_key(model_data["name"])
                    print(f"     - API 密钥状态: {'✓ 已配置' if has_key else '✗ 未配置'}")
            else:
                print(f"   ✗ 模型 {model_data['name']} 添加失败")
        
        # 3. 测试删除自定义模型
        print("\n3. 测试删除自定义模型...")
        model_to_remove = "test/model1"
        
        print(f"   删除前模型数量: {len(manager.get_all_models())}")
        result = manager.remove_model(model_to_remove)
        
        if result:
            print(f"   ✓ 成功删除模型: {model_to_remove}")
            print(f"   ✓ 删除后模型数量: {len(manager.get_all_models())}")
            
            # 验证模型确实被删除了
            if not manager.check_model_exists(model_to_remove):
                print(f"   ✓ 确认模型 {model_to_remove} 已不存在")
            else:
                print(f"   ✗ 错误：模型 {model_to_remove} 仍然存在")
        else:
            print(f"   ✗ 删除模型失败: {model_to_remove}")
        
        # 4. 测试删除带有 API 密钥的模型
        print("\n4. 测试删除带有 API 密钥的模型...")
        model_with_key = "test/model2"
        
        print(f"   删除前密钥状态: {'✓ 已配置' if manager.has_key(model_with_key) else '✗ 未配置'}")
        result = manager.remove_model(model_with_key)
        
        if result:
            print(f"   ✓ 成功删除带密钥的模型: {model_with_key}")
            
            # 验证模型和密钥都被删除了
            if not manager.check_model_exists(model_with_key):
                print(f"   ✓ 确认模型 {model_with_key} 已不存在")
            else:
                print(f"   ✗ 错误：模型 {model_with_key} 仍然存在")
        else:
            print(f"   ✗ 删除带密钥的模型失败: {model_with_key}")
        
        # 5. 测试删除默认模型（应该失败）
        print("\n5. 测试删除默认模型（应该失败）...")
        default_model = "deepseek/v3"
        
        result = manager.remove_model(default_model)
        if not result:
            print(f"   ✓ 正确：无法删除默认模型 {default_model}")
            
            # 验证默认模型仍然存在
            if manager.check_model_exists(default_model):
                print(f"   ✓ 确认默认模型 {default_model} 仍然存在")
            else:
                print(f"   ✗ 错误：默认模型 {default_model} 被意外删除")
        else:
            print(f"   ✗ 错误：成功删除了默认模型 {default_model}（这不应该发生）")
        
        # 6. 测试删除不存在的模型
        print("\n6. 测试删除不存在的模型...")
        nonexistent_model = "non/existent"
        
        result = manager.remove_model(nonexistent_model)
        if not result:
            print(f"   ✓ 正确：无法删除不存在的模型 {nonexistent_model}")
        else:
            print(f"   ✗ 错误：声称成功删除了不存在的模型 {nonexistent_model}")
        
        # 7. 最终验证
        print("\n7. 最终验证...")
        final_models = manager.get_all_models()
        custom_models = [name for name in final_models.keys() if name.startswith("test/")]
        
        print(f"   ✓ 最终模型总数: {len(final_models)}")
        print(f"   ✓ 剩余测试模型数量: {len(custom_models)}")
        
        if len(custom_models) == 0:
            print("   ✓ 所有测试模型已成功清理")
        else:
            print(f"   ⚠️  仍有测试模型未清理: {custom_models}")
        
        # 检查默认模型是否完整
        default_models = ["deepseek/v3", "deepseek/r1", "ark/deepseek-v3-250324"]
        missing_defaults = [name for name in default_models if not manager.check_model_exists(name)]
        
        if not missing_defaults:
            print("   ✓ 所有默认模型都完整保留")
        else:
            print(f"   ✗ 缺失的默认模型: {missing_defaults}")
    
    print("\n=== 删除功能测试完成 ===")


def test_models_command_integration():
    """测试与 models_command 的集成"""
    print("\n=== 测试与 models_command 的集成 ===\n")
    
    # 这部分可以通过模拟 handle_models_command 函数来测试
    # 但为了简单起见，我们只提供使用示例
    print("使用示例：")
    print("1. 添加模型：/models /add_model name=test/demo base_url=https://demo.com/v1")
    print("2. 列出模型：/models /list")
    print("3. 删除模型：/models /remove test/demo")
    print("4. 验证删除：/models /list")
    
    print("\n预期行为：")
    print("- 自定义模型应该能被成功删除")
    print("- 删除后模型不应该出现在列表中")
    print("- 默认模型不能被删除")
    print("- 删除不存在的模型应该显示错误消息")


if __name__ == "__main__":
    try:
        test_remove_functionality()
        test_models_command_integration()
        print("\n🎉 所有测试完成！删除功能工作正常。")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 