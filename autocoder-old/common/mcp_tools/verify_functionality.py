#!/usr/bin/env python3
"""
功能验证脚本 - 验证MCP工具模块的核心功能
"""

import sys
import traceback
from pathlib import Path
import tempfile
import json

def test_basic_imports():
    """测试基本导入功能"""
    print("1. 测试基本导入...")
    try:
        from autocoder.common.mcp_tools import (
            McpHub, McpExecutor, McpServerInstaller, McpServer,
            get_mcp_server, McpRequest, McpResponse, MarketplaceMCPServerItem
        )
        print("   ✓ 所有主要类都可以正常导入")
        return True
    except Exception as e:
        print(f"   ✗ 导入失败: {e}")
        traceback.print_exc()
        return False

def test_type_creation():
    """测试类型创建功能"""
    print("2. 测试类型创建...")
    try:
        from autocoder.common.mcp_tools.types import (
            McpRequest, McpInstallRequest, MarketplaceMCPServerItem,
            McpToolCall, McpResourceAccess
        )
        
        # 测试McpRequest
        request = McpRequest(query="test query")
        assert request.query == "test query"
        
        # 测试MarketplaceMCPServerItem
        item = MarketplaceMCPServerItem(
            name="test-server",
            description="Test server",
            command="python"
        )
        assert item.name == "test-server"
        
        # 测试McpToolCall
        tool_call = McpToolCall(
            server_name="test-server",
            tool_name="test-tool",
            arguments={"param1": "value1"}
        )
        assert tool_call.server_name == "test-server"
        
        print("   ✓ 所有类型可以正常创建")
        return True
    except Exception as e:
        print(f"   ✗ 类型创建失败: {e}")
        traceback.print_exc()
        return False

def test_hub_functionality():
    """测试Hub功能"""
    print("3. 测试Hub功能...")
    try:
        from autocoder.common.mcp_tools import McpHub
        
        # 测试文件创建
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "test_settings.json"
            marketplace_path = Path(tmp_dir) / "test_marketplace.json"
            
            hub = McpHub(
                settings_path=str(settings_path),
                marketplace_path=str(marketplace_path)
            )
            
            # 验证文件创建
            assert settings_path.exists(), "Settings file not created"
            assert marketplace_path.exists(), "Marketplace file not created"
            
            # 验证文件内容
            with open(settings_path) as f:
                settings_data = json.load(f)
                assert "mcpServers" in settings_data
            
            with open(marketplace_path) as f:
                marketplace_data = json.load(f)
                assert "mcpServers" in marketplace_data
            
            print("   ✓ Hub功能正常工作")
            return True
    except Exception as e:
        print(f"   ✗ Hub功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_server_templates():
    """测试服务器模板功能"""
    print("4. 测试服务器模板...")
    try:
        from autocoder.common.mcp_tools import McpHub
        
        templates = McpHub.get_server_templates()
        assert isinstance(templates, dict)
        
        print(f"   ✓ 服务器模板获取成功，共有 {len(templates)} 个模板")
        return True
    except Exception as e:
        print(f"   ✗ 服务器模板测试失败: {e}")
        traceback.print_exc()
        return False

def test_server_singleton():
    """测试服务器单例模式"""
    print("5. 测试服务器单例...")
    try:
        from autocoder.common.mcp_tools import get_mcp_server
        
        server1 = get_mcp_server()
        server2 = get_mcp_server()
        
        assert server1 is server2, "服务器不是单例"
        
        print("   ✓ 服务器单例模式正常工作")
        return True
    except Exception as e:
        print(f"   ✗ 服务器单例测试失败: {e}")
        traceback.print_exc()
        return False

def test_installer_functionality():
    """测试安装器功能"""
    print("6. 测试安装器功能...")
    try:
        from autocoder.common.mcp_tools import McpServerInstaller
        
        installer = McpServerInstaller()
        
        # 测试字典合并
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        result = installer.deep_merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        assert result == expected, f"字典合并失败: {result} != {expected}"
        
        # 测试命令行参数解析
        args = "--name test-server --command python --args -m test"
        name, config = installer.parse_command_line_args(args)
        assert name == "test-server"
        assert config["command"] == "python"
        assert config["args"] == ["-m", "test"]
        
        print("   ✓ 安装器功能正常工作")
        return True
    except Exception as e:
        print(f"   ✗ 安装器功能测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=== MCP工具模块功能验证 ===\n")
    
    tests = [
        test_basic_imports,
        test_type_creation,
        test_hub_functionality,
        test_server_templates,
        test_server_singleton,
        test_installer_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ✗ 测试执行失败: {e}")
            failed += 1
        print()
    
    print(f"=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有功能测试通过！MCP工具模块迁移成功！")
        return 0
    else:
        print(f"\n❌ {failed} 个测试失败，需要进一步调试")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 