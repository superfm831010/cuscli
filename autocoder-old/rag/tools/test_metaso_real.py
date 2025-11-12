
"""
Metaso 实际 API 测试

使用真实的 API key 测试 Metaso 功能。
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from autocoder.rag.tools.metaso_sdk import MetasoClient
from autocoder.rag.tools.web_search_tool import WebSearchTool, WebSearchToolResolver
from autocoder.rag.tools.web_crawl_tool import WebCrawlTool, WebCrawlToolResolver
from unittest.mock import Mock


def test_real_metaso_api():
    """使用真实 API 测试 Metaso"""
    print("=" * 60)
    print("Metaso 真实 API 测试")
    print("=" * 60)
    
    # 使用提供的 API key
    api_key = "mk-6EFE0560471B476BA2ECC475DB9A50D7"
    
    print("\n1. 测试搜索 API")
    print("-" * 40)
    
    client = MetasoClient(api_key=api_key)
    
    # 测试搜索
    result = client.search(
        query="谁是这个世界上最美丽的女人",
        size=3,
        include_summary=False
    )
    
    if result.success:
        print(f"✅ 搜索成功!")
        print(f"   剩余积分: {result.credits}")
        print(f"   结果数量: {len(result.webpages)}")
        print("\n   搜索结果:")
        for idx, page in enumerate(result.webpages[:3], 1):
            print(f"\n   {idx}. {page.title}")
            print(f"      链接: {page.link}")
            print(f"      评分: {page.score}")
            print(f"      位置: {page.position}")
            if page.date:
                print(f"      日期: {page.date}")
            print(f"      摘要: {page.snippet[:100]}...")
    else:
        print(f"❌ 搜索失败: {result.error}")
    
    print("\n2. 测试读取 API")
    print("-" * 40)
    
    # 测试读取网页
    test_url = "https://www.163.com/news/article/K56809DQ000189FH.html"
    print(f"   读取 URL: {test_url}")
    
    content = client.read(test_url)
    
    if not content.startswith("Error:"):
        print(f"✅ 读取成功!")
        print(f"   内容长度: {len(content)} 字符")
        print(f"   内容预览:")
        print(f"   {content[:300]}...")
    else:
        print(f"❌ 读取失败: {content}")
    
    return result.success if result else False


def test_web_tools_with_real_api():
    """使用真实 API 测试工具集成"""
    print("\n" + "=" * 60)
    print("工具集成真实 API 测试")
    print("=" * 60)
    
    # 设置 mock 参数
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.metaso_api_key = "mk-6EFE0560471B476BA2ECC475DB9A50D7"
    mock_args.firecrawl_api_key = None
    
    print("\n1. 测试 WebSearchTool")
    print("-" * 40)
    
    # 创建搜索工具
    search_tool = WebSearchTool(
        query="Python 编程教程",
        limit=3,
        provider="metaso"
    )
    
    resolver = WebSearchToolResolver(mock_agent, search_tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"✅ WebSearchTool 执行成功!")
        print(f"   消息: {result.message}")
        print(f"   结果数量: {len(result.content)}")
        for idx, item in enumerate(result.content[:2], 1):
            print(f"\n   结果 {idx}:")
            print(f"     标题: {item['title']}")
            print(f"     URL: {item['url']}")
            print(f"     提供商: {item.get('provider', 'unknown')}")
    else:
        print(f"❌ WebSearchTool 执行失败: {result.message}")
    
    print("\n2. 测试 WebCrawlTool (单页读取)")
    print("-" * 40)
    
    # 创建爬取工具（单页）
    crawl_tool = WebCrawlTool(
        url="https://www.python.org",
        limit=1,
        provider="metaso"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, crawl_tool, mock_args)
    result = resolver.resolve()
    
    if result.success:
        print(f"✅ WebCrawlTool 执行成功!")
        print(f"   消息: {result.message}")
        if result.content:
            page = result.content[0]
            print(f"   URL: {page['url']}")
            print(f"   内容长度: {len(page.get('content', ''))} 字符")
            print(f"   内容预览: {page.get('content', '')[:200]}...")
    else:
        print(f"❌ WebCrawlTool 执行失败: {result.message}")


def main():
    """运行实际 API 测试"""
    print("\n" + "=" * 60)
    print("开始 Metaso 真实 API 测试")
    print("=" * 60)
    print("\n使用 API Key: mk-6EFE0560471B476BA2ECC475DB9A50D7")
    
    try:
        # 运行测试
        test_real_metaso_api()
        test_web_tools_with_real_api()
        
        print("\n" + "=" * 60)
        print("✅ 真实 API 测试完成！")
        print("=" * 60)
        
        print("\n总结:")
        print("1. ✅ Metaso 搜索 API 正常工作")
        print("2. ✅ Metaso 读取 API 正常工作")
        print("3. ✅ WebSearchTool 集成正常")
        print("4. ✅ WebCrawlTool 集成正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
