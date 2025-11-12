#!/usr/bin/env python3
"""
Project Tracker Demo

演示如何使用 LLM 模块和 Project Tracker 模块来分析项目并生成 AUTO-CODER.md 文件。
使用指定的模型 idea/k2 进行项目探索和文档生成。
"""

import sys
import os
from pathlib import Path
from loguru import logger

from autocoder.common import AutoCoderArgs
from autocoder.common.llms.manager import LLMManager
from autocoder.common.project_tracker.api import ProjectTrackerAPI
from autocoder.common.project_tracker.types import ExplorationMode
from autocoder.auto_coder_runner import load_tokenizer

# 配置日志级别为 INFO
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

project_root = "/Users/williamzhu/projects/auto-coder"
load_tokenizer()

def setup_autocoder_args(source_dir: str, model_name: str = "v3_chat") -> AutoCoderArgs:
    """
    设置 AutoCoder 参数配置
    
    Args:
        source_dir: 项目源代码目录
        model_name: 使用的模型名称
        
    Returns:
        配置好的 AutoCoderArgs 实例
    """
    args = AutoCoderArgs()
    args.source_dir = source_dir
    args.model = model_name
    args.code_model = model_name
    args.product_mode = "lite"  # 使用 lite 模式
    args.project_type = "python"
    
    return args


def verify_model_availability(model_name: str) -> bool:
    """
    验证指定模型是否可用
    
    Args:
        model_name: 模型名称
        
    Returns:
        模型是否可用
    """
    try:
        manager = LLMManager()
        model = manager.get_model(model_name)
        
        if model:
            print(f"✓ 找到模型: {model.name}")
            print(f"  描述: {model.description}")
            print(f"  类型: {model.model_type}")
            print(f"  基础URL: {model.base_url}")
            print(f"  是否配置密钥: {'是' if manager.has_key(model_name) else '否'}")
            
            if not manager.has_key(model_name):
                print(f"⚠ 警告: 模型 {model_name} 未配置 API 密钥")
                print(f"请在 ~/.auto-coder/keys/{model_name.replace('/', '_')}.key 中配置密钥")
                return False
                
            return True
        else:
            print(f"✗ 未找到模型: {model_name}")
            print("请确保在 ~/.auto-coder/keys/models.json 中配置了该模型")
            return False
            
    except Exception as e:
        print(f"✗ 验证模型时出错: {e}")
        return False


def run_project_exploration(source_dir: str, model_name: str = "v3_chat"):
    """
    运行项目探索并生成 AUTO-CODER.md 文件
    
    Args:
        source_dir: 项目源代码目录
        model_name: 使用的模型名称
    """
    print(f"🚀 开始项目探索...")
    print(f"📁 项目目录: {source_dir}")
    print(f"🤖 使用模型: {model_name}")
    print("=" * 60)
    
    # 1. 验证模型可用性
    print("1. 验证模型可用性...")
    if not verify_model_availability(model_name):
        print("❌ 模型验证失败，无法继续")
        return False
    
    # 2. 设置配置
    print("\n2. 设置项目配置...")
    try:
        args = setup_autocoder_args(source_dir, model_name)
        print(f"✓ 配置完成: {args.source_dir}")
    except Exception as e:
        print(f"✗ 配置失败: {e}")
        return False
    
    # 3. 初始化 Project Tracker API
    print("\n3. 初始化 Project Tracker...")
    try:
        api = ProjectTrackerAPI(args=args)
        print("✓ Project Tracker 初始化成功")
    except Exception as e:
        print(f"✗ Project Tracker 初始化失败: {e}")
        return False
    
    # 4. 获取项目概览
    print("\n4. 获取项目基本信息...")
    try:
        overview = api.get_project_overview()
        print(f"✓ 发现 {overview.get('ac_modules_found', 0)} 个 AC 模块")
        if overview.get('ac_module_paths'):
            print("  AC 模块列表:")
            for module_path in overview['ac_module_paths'][:5]:  # 显示前5个
                print(f"    - {module_path}")
            if len(overview['ac_module_paths']) > 5:
                print(f"    ... 还有 {len(overview['ac_module_paths']) - 5} 个模块")
    except Exception as e:
        print(f"✗ 获取项目概览失败: {e}")
        return False
    
    # 5. 执行全面项目探索
    print("\n5. 执行项目探索分析...")
    print("   这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 使用自定义提示来确保生成 AUTO-CODER.md 文件
        custom_prompt = """
请特别关注以下任务：

1. 全面分析项目中的所有 AC 模块
2. 理解项目的整体架构和设计模式
3. 识别关键组件和它们之间的依赖关系
4. 提供开发建议和最佳实践

**重要**: 完成分析后，必须使用 write_to_file 工具创建 .auto-coder/projects/AUTO-CODER.md 文件，
包含完整的项目文档，帮助开发者快速理解和使用这个项目。

文档应该包括：
- 项目概述和目标
- 架构总结
- AC 模块详细说明
- 开发工作流程
- 新手入门指南
- 最佳实践建议
"""
        
        response = api.full_exploration(custom_prompt=custom_prompt)
        
        if response.success:
            print("✓ 项目探索完成!")
            
            # 显示探索结果摘要
            if response.exploration_result:
                result = response.exploration_result
                print(f"  - 分析模式: {result.mode}")
                print(f"  - 发现模块: {len(result.modules_found)} 个")
                print(f"  - 关键洞察: {len(result.key_insights)} 条")
                print(f"  - 建议事项: {len(result.recommendations)} 条")
                print(f"  - 执行时间: {result.exploration_time:.2f} 秒")
                
                # 显示部分关键洞察
                if result.key_insights:
                    print("\n  关键洞察:")
                    for i, insight in enumerate(result.key_insights[:3], 1):
                        print(f"    {i}. {insight}")
                
                # 显示部分建议
                if result.recommendations:
                    print("\n  建议事项:")
                    for i, rec in enumerate(result.recommendations[:3], 1):
                        print(f"    {i}. {rec}")
            
            print(f"\n✓ 对话ID: {response.conversation_id}")
            
        else:
            print(f"✗ 项目探索失败: {response.error_message}")
            return False
            
    except Exception as e:
        print(f"✗ 项目探索过程中出错: {e}")
        return False
    
    # 6. 验证生成的文档
    print("\n6. 验证生成的文档...")
    auto_coder_md_path = os.path.join(source_dir, ".auto-coder", "projects", "AUTO-CODER.md")
    
    if os.path.exists(auto_coder_md_path):
        print(f"✓ AUTO-CODER.md 文件已生成: {auto_coder_md_path}")
        
        # 显示文件大小
        file_size = os.path.getsize(auto_coder_md_path)
        print(f"  文件大小: {file_size} 字节")
        
        # 显示文件开头内容
        try:
            with open(auto_coder_md_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # 读取前500个字符
                print("\n  文件内容预览:")
                print("  " + "─" * 50)
                for line in content.split('\n')[:10]:  # 显示前10行
                    print(f"  {line}")
                print("  " + "─" * 50)
        except Exception as e:
            print(f"  ⚠ 无法读取文件内容: {e}")
    else:
        print(f"⚠ AUTO-CODER.md 文件未找到: {auto_coder_md_path}")
        print("  可能需要手动检查探索过程中的输出")
    
    print("\n" + "=" * 60)
    print("🎉 项目探索演示完成!")
    return True


def main():
    """主函数"""
    print("AutoCoder Project Tracker Demo")
    print("使用 LLM 模块和 Project Tracker 模块生成项目文档")
    print("=" * 60)
    
    # 使用当前项目作为演示目标
    current_project_dir = str(project_root)
    model_name = "v3_chat"
    
    print(f"目标项目: {current_project_dir}")
    print(f"指定模型: {model_name}")
    print()
    
    # 确认是否继续
    try:
        user_input = input("是否继续执行项目探索? (y/N): ").strip().lower()
        if user_input not in ['y', 'yes', '是']:
            print("取消执行")
            return
    except KeyboardInterrupt:
        print("\n取消执行")
        return
    
    # 执行项目探索
    success = run_project_exploration(current_project_dir, model_name)
    
    if success:
        print("\n✅ 演示成功完成!")
        print("\n下一步建议:")
        print("1. 查看生成的 .auto-coder/projects/AUTO-CODER.md 文件")
        print("2. 根据文档内容了解项目结构")
        print("3. 使用文档中的建议进行开发")
    else:
        print("\n❌ 演示执行失败")
        print("\n故障排除建议:")
        print("1. 检查模型配置和 API 密钥")
        print("2. 确认网络连接正常")
        print("3. 查看错误日志获取详细信息")


if __name__ == "__main__":
    main()
