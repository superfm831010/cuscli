
"""
Metaso 集成使用示例

该文件展示如何使用集成了 Metaso 的 web_search_tool 和 web_crawl_tool。
"""

import os
import sys
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from autocoder.rag.tools.metaso_sdk import MetasoClient
from autocoder.rag.tools.web_search_tool import WebSearchTool, WebSearchToolResolver
from autocoder.rag.tools.web_crawl_tool import WebCrawlTool, WebCrawlToolResolver
from unittest.mock import Mock


def example_direct_metaso_sdk():
    """直接使用 Metaso SDK 的示例"""
    print("=" * 60)
    print("示例 1: 直接使用 Metaso SDK")
    print("=" * 60)
    
    # 从环境变量获取 API key
    api_key = os.getenv('METASO_API_KEY')
    if not api_key:
        print("\n⚠️  请先设置环境变量 METASO_API_KEY")
        print("   export METASO_API_KEY='your-api-key-here'")
        return
    
    # 创建客户端
    client = MetasoClient(api_key=api_key)
    
    # 1. 搜索示例
    print("\n1. 搜索示例:")
    search_result = client.search(
        query="Python 编程最佳实践",
        size=3,
        include_summary=False
    )
    
    if search_result.success:
        print(f"   找到 {len(search_result.webpages)} 个结果:")
        for idx, page in enumerate(search_result.webpages, 1):
            print(f"\n   {idx}. {page.title}")
            print(f"      URL: {page.link}")
            print(f"      摘要: {page.snippet[:100]}...")
            if page.date:
                print(f"      日期: {page.date}")
    else:
        print(f"   搜索失败: {search_result.error}")
    
    # 2. 读取网页示例
    print("\n2. 读取网页示例:")
    if search_result.success and search_result.webpages:
        first_url = search_result.webpages[0].link
        print(f"   读取 URL: {first_url}")
        
        content = client.read(first_url)
        if not content.startswith("Error:"):
            print(f"   成功读取，内容长度: {len(content)} 字符")
            print(f"   内容预览:\n{content[:500]}...")
        else:
            print(f"   读取失败: {content}")


def example_web_search_tool():
    """使用 WebSearchTool 的示例"""
    print("\n" + "=" * 60)
    print("示例 2: 使用 WebSearchTool (集成 Metaso)")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    
    # 设置 API keys (可以同时设置，系统会自动选择)
    mock_args.metaso_api_key = os.getenv('METASO_API_KEY')
    mock_args.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not mock_args.metaso_api_key:
        print("\n⚠️  请先设置环境变量 METASO_API_KEY")
        return
    
    # 创建搜索工具 - 明确指定使用 Metaso
    tool = WebSearchTool(
        query="人工智能在医疗领域的应用",
        limit=5,
        provider="metaso",  # 明确指定使用 Metaso
        scrape_options='{"include_summary": true}'
    )
    
    # 创建解析器并执行
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"\n搜索成功: {result.message}")
        print(f"找到 {len(result.content)} 个结果:")
        
        for idx, item in enumerate(result.content, 1):
            print(f"\n{idx}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   描述: {item['description'][:100]}...")
            print(f"   来源: {item.get('provider', 'unknown')}")
            if 'date' in item:
                print(f"   日期: {item['date']}")
    else:
        print(f"\n搜索失败: {result.message}")


def example_web_crawl_tool():
    """使用 WebCrawlTool 的示例"""
    print("\n" + "=" * 60)
    print("示例 3: 使用 WebCrawlTool (集成 Metaso)")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.metaso_api_key = os.getenv('METASO_API_KEY')
    mock_args.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not mock_args.metaso_api_key:
        print("\n⚠️  请先设置环境变量 METASO_API_KEY")
        return
    
    # 示例 1: 单页读取
    print("\n1. 单页读取:")
    tool = WebCrawlTool(
        url="https://www.python.org",
        limit=1,
        provider="metaso"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"   {result.message}")
        if result.content:
            page = result.content[0]
            print(f"   URL: {page['url']}")
            print(f"   内容长度: {len(page['content'])} 字符")
            print(f"   内容预览: {page['content'][:200]}...")
    else:
        print(f"   失败: {result.message}")
    
    # 示例 2: 多页爬取
    print("\n2. 多页爬取:")
    tool = WebCrawlTool(
        url="https://docs.python.org",
        limit=3,
        include_paths="/tutorial",
        provider="metaso"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"   {result.message}")
        for idx, page in enumerate(result.content, 1):
            print(f"\n   页面 {idx}:")
            print(f"     URL: {page['url']}")
            print(f"     标题: {page.get('title', 'N/A')}")
            print(f"     内容长度: {len(page.get('content', ''))} 字符")
    else:
        print(f"   失败: {result.message}")


def example_auto_provider_selection():
    """演示提供商自动选择"""
    print("\n" + "=" * 60)
    print("示例 4: 提供商自动选择")
    print("=" * 60)
    
    mock_agent = Mock()
    mock_args = Mock()
    
    # 设置环境变量中的 API keys
    mock_args.metaso_api_key = os.getenv('METASO_API_KEY')
    mock_args.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    print("\n环境配置:")
    print(f"  Metaso API Key: {'已设置' if mock_args.metaso_api_key else '未设置'}")
    print(f"  Firecrawl API Key: {'已设置' if mock_args.firecrawl_api_key else '未设置'}")
    
    if not (mock_args.metaso_api_key or mock_args.firecrawl_api_key):
        print("\n⚠️  请至少设置一个 API key")
        return
    
    # 不指定 provider，让系统自动选择
    tool = WebSearchTool(
        query="自动选择测试",
        limit=2
        # 注意：没有指定 provider 参数
    )
    
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    # 系统会根据可用的 API keys 自动选择：
    # 1. 如果只有 Metaso key -> 使用 Metaso
    # 2. 如果只有 Firecrawl key -> 使用 Firecrawl  
    # 3. 如果两个都有 -> 默认使用 Firecrawl
    
    result = resolver.resolve()
    
    if result.success:
        print(f"\n自动选择结果: {result.message}")
        if "Metaso" in result.message:
            print("  ✓ 系统选择了 Metaso")
        elif "Firecrawl" in result.message:
            print("  ✓ 系统选择了 Firecrawl")
    else:
        print(f"\n执行失败: {result.message}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("Metaso 集成使用示例")
    print("=" * 60)
    
    print("\n使用说明:")
    print("1. 设置 API Key:")
    print("   export METASO_API_KEY='your-metaso-api-key'")
    print("   export FIRECRAWL_API_KEY='your-firecrawl-api-key' (可选)")
    print("\n2. 在工具中指定 provider 参数:")
    print("   provider='metaso' - 使用 Metaso")
    print("   provider='firecrawl' - 使用 Firecrawl")
    print("   provider=None - 自动选择")
    
    # 检查环境变量
    has_metaso = bool(os.getenv('METASO_API_KEY'))
    has_firecrawl = bool(os.getenv('FIRECRAWL_API_KEY'))
    
    print("\n当前环境:")
    print(f"  Metaso API Key: {'✓ 已设置' if has_metaso else '✗ 未设置'}")
    print(f"  Firecrawl API Key: {'✓ 已设置' if has_firecrawl else '✗ 未设置'}")
    
    if not has_metaso:
        print("\n⚠️  请先设置 METASO_API_KEY 环境变量来运行示例")
        print("   export METASO_API_KEY='mk-YOUR_API_KEY_HERE'")
        return
    
    try:
        # 运行示例
        example_direct_metaso_sdk()
        example_web_search_tool()
        example_web_crawl_tool()
        example_auto_provider_selection()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
