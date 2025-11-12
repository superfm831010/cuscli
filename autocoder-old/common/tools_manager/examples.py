


"""
Tools Manager Usage Examples

工具管理器的使用示例和演示代码。
"""

import os
import tempfile
from pathlib import Path
from autocoder.common.tools_manager import ToolsManager


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建工具管理器实例
    manager = ToolsManager()
    
    # 加载工具
    result = manager.load_tools()
    
    print(f"加载结果: {'成功' if result.success else '失败'}")
    print(f"工具总数: {result.total_count}")
    print(f"失败数量: {result.failed_count}")
    
    if result.success:
        print("\n工具列表:")
        for tool in result.tools:
            print(f"- {tool.name}: {tool.path}")
    
    print()


def example_get_tools_prompt():
    """获取工具prompt示例"""
    print("=== 获取工具Prompt示例 ===")
    
    manager = ToolsManager()
    
    # 获取工具prompt
    prompt = manager.get_tools_prompt.prompt()
    print("生成的Prompt:")
    print(prompt)
    print()


def example_find_specific_tool():
    """查找特定工具示例"""
    print("=== 查找特定工具示例 ===")
    
    manager = ToolsManager()
    
    # 获取所有工具名称
    tool_names = manager.list_tool_names()
    print(f"所有工具名称: {tool_names}")
    
    # 查找特定工具
    if tool_names:
        first_tool_name = tool_names[0]
        tool = manager.get_tool_by_name(first_tool_name)
        if tool:
            print(f"\n找到工具 '{first_tool_name}':")
            print(f"  路径: {tool.path}")
            print(f"  可执行: {tool.is_executable}")
            print(f"  帮助信息: {tool.help_text[:100]}...")
    
    print()


def example_create_test_tools():
    """创建测试工具示例"""
    print("=== 创建测试工具示例 ===")
    
    # 创建临时目录作为工具目录
    with tempfile.TemporaryDirectory() as temp_dir:
        tools_dir = Path(temp_dir) / ".autocodertools"
        tools_dir.mkdir(parents=True)
        
        # 创建一个Python工具
        python_tool = tools_dir / "test_tool.py"
        python_tool.write_text("""#!/usr/bin/env python3
# 描述: 这是一个测试工具
# 用法: test_tool.py [选项]

import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['help', '-h', '--help']:
        print("测试工具使用说明:")
        print("  test_tool.py help    - 显示此帮助信息")
        print("  test_tool.py run     - 运行测试")
        return
    
    print("测试工具正在运行...")

if __name__ == "__main__":
    main()
""")
        
        # 设置执行权限
        python_tool.chmod(0o755)
        
        # 创建一个Shell工具
        shell_tool = tools_dir / "deploy.sh"
        shell_tool.write_text("""#!/bin/bash
# 描述: 部署脚本
# 用法: deploy.sh [环境]

if [ "$1" = "help" ] || [ "$1" = "-h" ]; then
    echo "部署脚本使用说明:"
    echo "  deploy.sh help       - 显示此帮助信息"
    echo "  deploy.sh dev        - 部署到开发环境"
    echo "  deploy.sh prod       - 部署到生产环境"
    exit 0
fi

echo "开始部署到环境: ${1:-dev}"
""")
        
        shell_tool.chmod(0o755)
        
        # 使用自定义目录创建工具管理器
        manager = ToolsManager(tools_dirs=[str(tools_dir)])
        
        # 加载工具
        result = manager.load_tools(force_reload=True)
        
        print(f"测试工具加载结果: {'成功' if result.success else '失败'}")
        print(f"找到工具数量: {len(result.tools)}")
        
        for tool in result.tools:
            print(f"\n工具: {tool.name}")
            print(f"  路径: {tool.path}")
            print(f"  扩展名: {tool.file_extension}")
            print(f"  可执行: {tool.is_executable}")
            print(f"  帮助信息:\n{tool.help_text}")
    
    print()


def main():
    """运行所有示例"""
    print("工具管理器使用示例")
    print("=" * 50)
    
    example_basic_usage()
    example_get_tools_prompt()
    example_find_specific_tool()
    example_create_test_tools()
    
    print("示例运行完成!")


if __name__ == "__main__":
    main()



