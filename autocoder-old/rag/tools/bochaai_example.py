

"""
BochaAI 集成使用示例

该文件展示如何使用集成了 BochaAI 的 web_search_tool 和 web_crawl_tool。
"""

import os
import sys
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from autocoder.rag.tools.bochaai_sdk import BochaAIClient
from autocoder.rag.tools.web_search_tool import WebSearchTool, WebSearchToolResolver
from autocoder.rag.tools.web_crawl_tool import WebCrawlTool, WebCrawlToolResolver
from unittest.mock import Mock


def example_direct_bochaai_sdk():
    """直接使用 BochaAI SDK 的示例"""
    print("=" * 60)
    print("示例 1: 直接使用 BochaAI SDK")
    print("=" * 60)
    
    # 从环境变量获取 API key
    api_key = os.getenv('BOCHAAI_API_KEY')
    if not api_key:
        print("\n⚠️  请先设置环境变量 BOCHAAI_API_KEY")
        print("   export BOCHAAI_API_KEY='your-api-key-here'")
        return
    
    # 创建客户端
    client = BochaAIClient(api_key=api_key)
    
    # 1. 搜索示例
    print("\n1. 搜索示例:")
    search_result = client.search(
        query="Python 编程最佳实践",
        count=5,
        summary=True,  # 显示文本摘要
        freshness="noLimit"  # 不限时间范围
    )
    
    if search_result.success:
        print(f"   找到 {len(search_result.webpages)} 个网页结果:")
        for idx, page in enumerate(search_result.webpages[:3], 1):
            print(f"\n   {idx}. {page.name}")
            print(f"      URL: {page.url}")
            print(f"      摘要: {page.snippet[:100]}...")
            if page.summary:
                print(f"      详细摘要: {page.summary[:100]}...")
            if page.date_published:
                print(f"      发布日期: {page.date_published}")
        
        if search_result.images:
            print(f"\n   找到 {len(search_result.images)} 个图片结果:")
            for idx, img in enumerate(search_result.images[:2], 1):
                print(f"   {idx}. {img.name or '未命名图片'}")
                print(f"      图片URL: {img.content_url}")
                print(f"      尺寸: {img.width}x{img.height}")
    else:
        print(f"   搜索失败: {search_result.error}")
    
    # 2. 爬取单个网页示例
    print("\n2. 爬取单个网页示例:")
    if search_result.success and search_result.webpages:
        first_url = search_result.webpages[0].url
        print(f"   爬取 URL: {first_url}")
        
        crawl_result = client.crawl_page(first_url)
        if crawl_result.get("success"):
            print(f"   成功爬取!")
            print(f"   页面标题: {crawl_result.get('title', 'N/A')}")
            print(f"   内容长度: {crawl_result.get('content_length', 0)} 字符")
            print(f"   内容预览:\n{crawl_result.get('content', '')[:300]}...")
        else:
            print(f"   爬取失败: {crawl_result.get('error', '未知错误')}")


def example_web_search_tool():
    """使用 WebSearchTool 的示例"""
    print("\n" + "=" * 60)
    print("示例 2: 使用 WebSearchTool (集成 BochaAI)")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    
    # 设置 API keys (可以同时设置，系统会自动选择)
    mock_args.bochaai_api_key = os.getenv('BOCHAAI_API_KEY')
    mock_args.metaso_api_key = os.getenv('METASO_API_KEY')
    mock_args.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not mock_args.bochaai_api_key:
        print("\n⚠️  请先设置环境变量 BOCHAAI_API_KEY")
        return
    
    # 创建搜索工具 - 明确指定使用 BochaAI
    tool = WebSearchTool(
        query="人工智能在医疗领域的应用",
        limit=10,
        provider="bochaai",  # 明确指定使用 BochaAI
        scrape_options='{"include_summary": true, "include_sites": "gov.cn|edu.cn", "exclude_sites": "ads.com"}'
    )
    
    # 创建解析器并执行
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"\n搜索成功: {result.message}")
        print(f"找到 {len(result.content)} 个结果:")
        
        for idx, item in enumerate(result.content[:5], 1):
            print(f"\n{idx}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   描述: {item['description'][:100]}...")
            print(f"   来源: {item.get('provider', 'unknown')}")
            if 'summary' in item:
                print(f"   摘要: {item['summary'][:100]}...")
            if 'date' in item:
                print(f"   日期: {item['date']}")
    else:
        print(f"\n搜索失败: {result.message}")


def example_web_crawl_tool():
    """使用 WebCrawlTool 的示例"""
    print("\n" + "=" * 60)
    print("示例 3: 使用 WebCrawlTool (集成 BochaAI)")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.bochaai_api_key = os.getenv('BOCHAAI_API_KEY')
    mock_args.metaso_api_key = os.getenv('METASO_API_KEY')
    mock_args.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not mock_args.bochaai_api_key:
        print("\n⚠️  请先设置环境变量 BOCHAAI_API_KEY")
        return
    
    # 示例 1: 单页爬取
    print("\n1. 单页爬取:")
    tool = WebCrawlTool(
        url="https://www.python.org",
        limit=1,
        provider="bochaai"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"   {result.message}")
        if result.content:
            page = result.content[0]
            print(f"   URL: {page['url']}")
            print(f"   标题: {page.get('title', 'N/A')}")
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
        exclude_paths="/api",
        provider="bochaai"
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
            metadata = page.get('metadata', {})
            if metadata.get('date_published'):
                print(f"     发布日期: {metadata['date_published']}")
    else:
        print(f"   失败: {result.message}")


def example_time_based_search():
    """演示时间范围搜索"""
    print("\n" + "=" * 60)
    print("示例 4: 时间范围搜索")
    print("=" * 60)
    
    api_key = os.getenv('BOCHAAI_API_KEY')
    if not api_key:
        print("\n⚠️  请先设置环境变量 BOCHAAI_API_KEY")
        return
    
    client = BochaAIClient(api_key=api_key)
    
    # 不同时间范围的搜索示例
    time_ranges = [
        ("oneDay", "一天内"),
        ("oneWeek", "一周内"),
        ("oneMonth", "一个月内"),
        ("oneYear", "一年内"),
        ("2024-01-01..2024-12-31", "2024年全年")
    ]
    
    for freshness, desc in time_ranges[:2]:  # 只演示前两个避免过多请求
        print(f"\n搜索 {desc} 的内容:")
        result = client.search(
            query="科技新闻",
            count=3,
            freshness=freshness,
            summary=False
        )
        
        if result.success:
            print(f"   找到 {len(result.webpages)} 个结果")
            for page in result.webpages[:2]:
                print(f"   - {page.name}")
                if page.date_published:
                    print(f"     发布时间: {page.date_published}")
        else:
            print(f"   搜索失败: {result.error}")


def example_auto_provider_selection():
    """演示提供商自动选择"""
    print("\n" + "=" * 60)
    print("示例 5: 提供商自动选择")
    print("=" * 60)
    
    mock_agent = Mock()
    mock_args = Mock()
    
    # 设置环境变量中的 API keys
    mock_args.bochaai_api_key = os.getenv('BOCHAAI_API_KEY')
    mock_args.metaso_api_key = os.getenv('METASO_API_KEY')
    mock_args.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    
    print("\n环境配置:")
    print(f"  BochaAI API Key: {'已设置' if mock_args.bochaai_api_key else '未设置'}")
    print(f"  Metaso API Key: {'已设置' if mock_args.metaso_api_key else '未设置'}")
    print(f"  Firecrawl API Key: {'已设置' if mock_args.firecrawl_api_key else '未设置'}")
    
    if not any([mock_args.bochaai_api_key, mock_args.metaso_api_key, mock_args.firecrawl_api_key]):
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
    # 1. 如果只有 BochaAI key -> 使用 BochaAI
    # 2. 如果只有 Metaso key -> 使用 Metaso
    # 3. 如果只有 Firecrawl key -> 使用 Firecrawl  
    # 4. 如果多个都有 -> 优先级: Firecrawl > BochaAI > Metaso
    
    result = resolver.resolve()
    
    if result.success:
        print(f"\n自动选择结果: {result.message}")
        if "BochaAI" in result.message:
            print("  ✓ 系统选择了 BochaAI")
        elif "Metaso" in result.message:
            print("  ✓ 系统选择了 Metaso")
        elif "Firecrawl" in result.message:
            print("  ✓ 系统选择了 Firecrawl")
    else:
        print(f"\n执行失败: {result.message}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("BochaAI 集成使用示例")
    print("=" * 60)
    
    print("\n使用说明:")
    print("1. 设置 API Key:")
    print("   export BOCHAAI_API_KEY='your-bochaai-api-key'")
    print("   export METASO_API_KEY='your-metaso-api-key' (可选)")
    print("   export FIRECRAWL_API_KEY='your-firecrawl-api-key' (可选)")
    print("\n2. 在工具中指定 provider 参数:")
    print("   provider='bochaai' - 使用 BochaAI")
    print("   provider='metaso' - 使用 Metaso")
    print("   provider='firecrawl' - 使用 Firecrawl")
    print("   provider=None - 自动选择")
    
    # 检查环境变量
    has_bochaai = bool(os.getenv('BOCHAAI_API_KEY'))
    has_metaso = bool(os.getenv('METASO_API_KEY'))
    has_firecrawl = bool(os.getenv('FIRECRAWL_API_KEY'))
    
    print("\n当前环境:")
    print(f"  BochaAI API Key: {'✓ 已设置' if has_bochaai else '✗ 未设置'}")
    print(f"  Metaso API Key: {'✓ 已设置' if has_metaso else '✗ 未设置'}")
    print(f"  Firecrawl API Key: {'✓ 已设置' if has_firecrawl else '✗ 未设置'}")
    
    if not has_bochaai:
        print("\n⚠️  请先设置 BOCHAAI_API_KEY 环境变量来运行示例")
        print("   export BOCHAAI_API_KEY='sk-YOUR_API_KEY_HERE'")
        print("\n   获取 API Key: https://open.bochaai.com")
        return
    
    try:
        # 运行示例
        example_direct_bochaai_sdk()
        example_web_search_tool()
        example_web_crawl_tool()
        example_time_based_search()
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

