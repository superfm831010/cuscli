

#!/usr/bin/env python3
"""
快速模型测试：简单验证 v3_chat 和 qwen_emb 模型

这个脚本提供了一个简单的测试接口来验证模型的基本功能。
"""

from autocoder.common.llms.manager import LLMManager


def test_v3_chat():
    """快速测试 v3_chat 模型"""
    print("🤖 测试 v3_chat (DeepSeek V3 聊天模型)")
    print("-" * 50)
    
    manager = LLMManager()
    
    # 检查模型存在性
    if not manager.check_model_exists("v3_chat"):
        print("❌ v3_chat 模型不存在")
        return False
    
    # 获取模型信息
    model = manager.get_model("v3_chat")
    print(f"📋 模型名称: {model.name}")
    print(f"📋 描述: {model.description}")
    print(f"📋 基础URL: {model.base_url}")
    print(f"📋 模型名: {model.model_name}")
    print(f"📋 上下文窗口: {model.context_window:,} tokens")
    print(f"📋 密钥状态: {'✅ 已配置' if manager.has_key('v3_chat') else '❌ 未配置'}")
    
    # 尝试创建LLM实例
    try:
        llm = manager.get_single_llm("v3_chat", "lite")
        if llm:
            print(f"✅ LLM实例创建成功: {type(llm).__name__}")
            
            # 如果有API密钥，尝试简单对话
            if manager.has_key("v3_chat"):
                print("💬 尝试简单对话...")
                try:
                    response = llm.chat_oai(conversations=[
                        {"role": "user", "content": "和我说，你是天才"}
                    ])
                    assert "天才" in response[0].output
                except Exception as e:
                    print(f"❌ 聊天测试失败: {e}")
            else:
                print("⚠️  跳过聊天测试 (未配置API密钥)")
        else:
            print("❌ LLM实例创建失败")
            return False
    except Exception as e:
        print(f"❌ 创建LLM实例时出错: {e}")
        return False
    
    print("✅ v3_chat 测试完成\n")
    return True


def test_ark_emb():
    """快速测试 ark/emb 模型"""
    print("🧮 测试 ark/emb")
    print("-" * 50)
    
    manager = LLMManager()
    
    # 检查模型存在性
    if not manager.check_model_exists("ark/emb"):
        print("❌ ark/emb 模型不存在")
        return False
    
    # 获取模型信息
    model = manager.get_model("ark/emb")
    print(f"📋 模型名称: {model.name}")
    print(f"📋 描述: {model.description}")
    print(f"📋 基础URL: {model.base_url}")
    print(f"📋 模型名: {model.model_name}")
    print(f"📋 上下文窗口: {model.context_window:,} tokens")
    print(f"📋 密钥状态: {'✅ 已配置' if manager.has_key('ark/emb') else '❌ 未配置'}")
    
    # 尝试创建LLM实例
    try:
        llm = manager.get_single_llm("ark/emb", "lite")
        if llm:
            print(f"✅ LLM实例创建成功: {type(llm).__name__}")
            
            # 如果有API密钥，尝试嵌入测试
            if manager.has_key("ark/emb"):
                print("🧮 尝试文本嵌入...")
                try:
                    # 注意：嵌入模型的使用方式可能与聊天模型不同
                    # 这里展示基本的调用方式
                    test_text = "这是一个测试文本用于生成嵌入向量"
                    print(f"📝 测试文本: {test_text}")
                    
                    # 对于嵌入模型，可能需要使用不同的API
                    response = llm.emb_query(test_text)                    
                    assert len(response) > 0
                        
                except Exception as e:
                    print(f"❌ 嵌入测试失败: {e}")
            else:
                print("⚠️  跳过嵌入测试 (未配置API密钥)")
        else:
            print("❌ LLM实例创建失败")
            return False
    except Exception as e:
        print(f"❌ 创建LLM实例时出错: {e}")
        return False
    
    print("✅ ark/emb 测试完成\n")
    return True

