#!/usr/bin/env python3
"""
集成测试运行脚本

这个脚本演示如何运行 Web 工具的集成测试。
它会检查环境配置，并提供运行不同类型测试的示例。

使用方法:
    python run_integration_tests.py --help
    python run_integration_tests.py --check-env
    python run_integration_tests.py --run-search
    python run_integration_tests.py --run-crawl
    python run_integration_tests.py --run-all
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_environment():
    """检查运行集成测试所需的环境"""
    print("=== 环境检查 ===")
    
    # 检查 API key
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if api_key:
        print(f"✓ FIRECRAWL_API_KEY: 已设置 (长度: {len(api_key)} 字符)")
    else:
        print("✗ FIRECRAWL_API_KEY: 未设置")
        print("  请设置环境变量: export FIRECRAWL_API_KEY=your_api_key")
        return False
    
    # 检查 firecrawl-py 依赖
    try:
        import firecrawl
        print(f"✓ firecrawl-py: 已安装 (版本: {getattr(firecrawl, '__version__', '未知')})")
    except ImportError:
        print("✗ firecrawl-py: 未安装")
        print("  请安装依赖: pip install firecrawl-py")
        return False
    
    # 检查 pytest
    try:
        import pytest
        print(f"✓ pytest: 已安装 (版本: {pytest.__version__})")
    except ImportError:
        print("✗ pytest: 未安装")
        print("  请安装依赖: pip install pytest")
        return False
    
    # 检查测试文件
    current_dir = Path(__file__).parent
    search_test_file = current_dir / "test_web_search_tool.py"
    crawl_test_file = current_dir / "test_web_crawl_tool.py"
    
    if search_test_file.exists():
        print(f"✓ WebSearch 测试文件: {search_test_file}")
    else:
        print(f"✗ WebSearch 测试文件不存在: {search_test_file}")
        return False
        
    if crawl_test_file.exists():
        print(f"✓ WebCrawl 测试文件: {crawl_test_file}")
    else:
        print(f"✗ WebCrawl 测试文件不存在: {crawl_test_file}")
        return False
    
    print("\n✓ 环境检查通过！可以运行集成测试")
    return True


def run_pytest_command(cmd, description):
    """运行 pytest 命令"""
    print(f"\n=== {description} ===")
    print(f"执行命令: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            print(f"\n✓ {description} - 完成")
        else:
            print(f"\n⚠ {description} - 部分测试失败 (退出码: {result.returncode})")
        return result.returncode
    except KeyboardInterrupt:
        print(f"\n⏸ {description} - 用户中断")
        return 130
    except Exception as e:
        print(f"\n✗ {description} - 执行错误: {e}")
        return 1


def run_search_integration_tests():
    """运行网页搜索集成测试"""
    current_dir = Path(__file__).parent
    test_file = current_dir / "test_web_search_tool.py"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file) + "::TestWebSearchToolIntegration",
        "-v", "-s",
        "--tb=short"
    ]
    
    return run_pytest_command(cmd, "WebSearch 集成测试")


def run_crawl_integration_tests(include_slow=False):
    """运行网页爬取集成测试"""
    current_dir = Path(__file__).parent
    test_file = current_dir / "test_web_crawl_tool.py"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file) + "::TestWebCrawlToolIntegration",
        "-v", "-s",
        "--tb=short"
    ]
    
    if not include_slow:
        cmd.extend(["-m", "not slow"])
        print("注意: 跳过慢速测试（异步作业测试）")
    
    return run_pytest_command(cmd, "WebCrawl 集成测试")


def run_all_integration_tests(include_slow=False):
    """运行所有集成测试"""
    current_dir = Path(__file__).parent
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(current_dir / "test_web_search_tool.py") + "::TestWebSearchToolIntegration",
        str(current_dir / "test_web_crawl_tool.py") + "::TestWebCrawlToolIntegration",
        "-v", "-s",
        "--tb=short"
    ]
    
    if not include_slow:
        cmd.extend(["-m", "not slow"])
        print("注意: 跳过慢速测试（异步作业测试）")
    
    return run_pytest_command(cmd, "所有 Web 工具集成测试")


def main():
    parser = argparse.ArgumentParser(
        description="Web 工具集成测试运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
    python run_integration_tests.py --check-env           # 检查环境配置
    python run_integration_tests.py --run-search          # 运行搜索集成测试
    python run_integration_tests.py --run-crawl           # 运行爬取集成测试
    python run_integration_tests.py --run-all             # 运行所有集成测试
    python run_integration_tests.py --run-all --slow      # 包含慢速测试

环境要求:
    export FIRECRAWL_API_KEY=your_actual_api_key
    pip install firecrawl-py pytest
        """
    )
    
    parser.add_argument('--check-env', action='store_true', help='检查环境配置')
    parser.add_argument('--run-search', action='store_true', help='运行网页搜索集成测试')
    parser.add_argument('--run-crawl', action='store_true', help='运行网页爬取集成测试')
    parser.add_argument('--run-all', action='store_true', help='运行所有集成测试')
    parser.add_argument('--slow', action='store_true', help='包含慢速测试（需要更长时间）')
    
    args = parser.parse_args()
    
    if not any([args.check_env, args.run_search, args.run_crawl, args.run_all]):
        parser.print_help()
        return 0
    
    if args.check_env:
        if not check_environment():
            return 1
        return 0
    
    # 运行测试前先检查环境
    if not check_environment():
        print("\n环境检查失败，无法运行集成测试")
        return 1
    
    return_code = 0
    
    if args.run_search:
        return_code = max(return_code, run_search_integration_tests())
    
    if args.run_crawl:
        return_code = max(return_code, run_crawl_integration_tests(args.slow))
    
    if args.run_all:
        return_code = max(return_code, run_all_integration_tests(args.slow))
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
