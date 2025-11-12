#!/usr/bin/env python3
"""
简单演示：如何通过 LLMManager 获取 v3_chat 模型
"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from autocoder.common.llms.manager import LLMManager


def simple_demo():
    """简单演示获取 v3_chat 模型"""
    
    # 1. 初始化管理器
    manager = LLMManager()
    
    # 2. 获取 v3_chat 模型配置
    model = manager.get_model("v3_chat")
    
    if model:
        print(f"✓ 找到模型: {model.name}")
        print(f"  描述: {model.description}")
        print(f"  类型: {model.model_type}")
        print(f"  基础URL: {model.base_url}")
        print(f"  是否配置密钥: {'是' if manager.has_key('v3_chat') else '否'}")
        
        # 3. 获取 LLM 实例
        llm = manager.get_single_llm("v3_chat", "lite")
        if llm:
            print(f"✓ 成功创建 LLM 实例: {type(llm).__name__}")
        else:
            print("✗ 无法创建 LLM 实例")
            
    else:
        print("✗ 未找到 v3_chat 模型")
        print("请确保在 ~/.auto-coder/keys/models.json 中配置了 v3_chat 模型")


if __name__ == "__main__":
    simple_demo() 