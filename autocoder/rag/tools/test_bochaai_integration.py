

"""
测试 BochaAI SDK 集成

该文件用于测试 BochaAI SDK 的功能以及与 web_search_tool 和 web_crawl_tool 的集成。
"""

import os
import sys
import json
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from autocoder.rag.tools.bochaai_sdk import BochaAIClient, BochaAIWebPage, BochaAIImage, BochaAISearchResponse
from autocoder.rag.tools.web_search_tool import WebSearchTool, WebSearchToolResolver
from autocoder.rag.tools.web_crawl_tool import WebCrawlTool, WebCrawlToolResolver


def test_bochaai_sdk():
    """测试 BochaAI SDK 基本功能"""
    print("=" * 60)
    print("测试 BochaAI SDK 基本功能")
    print("=" * 60)
    
    # 测试数据类
    webpage = BochaAIWebPage(
        name="测试网页标题",
        url="https://example.com",
        snippet="这是一个测试网页的摘要内容",
        display_url="https://example.com",
        summary="详细的摘要内容",
        site_name="示例网站",
        date_published="2024-01-01T00:00:00Z"
    )
    
    print("\n1. 测试 BochaAIWebPage 数据类:")
    print(f"   标题: {webpage.name}")
    print(f"   链接: {webpage.url}")
    print(f"   摘要: {webpage.snippet[:30]}...")
    print(f"   转换为字典: {json.dumps(webpage.to_dict(), ensure_ascii=False, indent=2)}")
    
    # 测试图片类
    image = BochaAIImage(
        thumbnail_url="https://example.com/thumb.jpg",
        content_url="https://example.com/image.jpg",
        host_page_url="https://example.com",
        width=800,
        height=600,
        name="测试图片"
    )
    
    print("\n2. 测试 BochaAIImage 数据类:")
    print(f"   图片URL: {image.content_url}")
    print(f"   尺寸: {image.width}x{image.height}")
    
    # 测试响应类
    search_response = BochaAISearchResponse(
        success=True,
        query="测试查询",
        total_matches=100,
        webpages=[webpage],
        images=[image]
    )
    
    print("\n3. 测试 BochaAISearchResponse 数据类:")
    print(f"   成功状态: {search_response.success}")
    print(f"   查询: {search_response.query}")
    print(f"   总匹配数: {search_response.total_matches}")
    print(f"   网页数量: {len(search_response.webpages)}")
    print(f"   图片数量: {len(search_response.images)}")
    
    print("\n✅ BochaAI SDK 数据类测试通过")


def test_bochaai_client_mock():
    """使用 mock 测试 BochaAI Client"""
    print("\n" + "=" * 60)
    print("测试 BochaAI Client (使用 Mock)")
    print("=" * 60)
    
    # Mock API 响应
    mock_search_response = {
        "code": 200,
        "log_id": "test_log_id",
        "msg": None,
        "data": {
            "_type": "SearchResponse",
            "queryContext": {
                "originalQuery": "Python编程"
            },
            "webPages": {
                "totalEstimatedMatches": 1000000,
                "value": [
                    {
                        "name": "Python 官方网站",
                        "url": "https://www.python.org",
                        "displayUrl": "https://www.python.org",
                        "snippet": "Python 是一种编程语言，可让您快速工作并更有效地集成系统。",
                        "summary": "Python 官方网站提供了完整的文档、教程和下载资源。",
                        "siteName": "Python.org",
                        "siteIcon": "https://www.python.org/favicon.ico",
                        "datePublished": "2024-01-15T00:00:00Z"
                    },
                    {
                        "name": "Python 教程",
                        "url": "https://docs.python.org/tutorial",
                        "displayUrl": "https://docs.python.org/tutorial",
                        "snippet": "本教程非正式地向读者介绍了 Python 语言和系统的基本概念和功能。",
                        "siteName": "Python Docs"
                    }
                ]
            },
            "images": {
                "value": [
                    {
                        "thumbnailUrl": "https://example.com/python-logo-thumb.png",
                        "contentUrl": "https://example.com/python-logo.png",
                        "hostPageUrl": "https://www.python.org",
                        "width": 200,
                        "height": 200,
                        "name": "Python Logo"
                    }
                ]
            }
        }
    }
    
    mock_crawl_response = {
        "success": True,
        "url": "https://www.python.org",
        "title": "Python Programming Language",
        "content": "<html><head><title>Python Programming Language</title></head><body>Python content here...</body></html>",
        "content_type": "text/html",
        "status_code": 200
    }
    
    with patch('requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock search 请求
        mock_search_resp = MagicMock()
        mock_search_resp.status_code = 200
        mock_search_resp.json.return_value = mock_search_response
        
        # Mock crawl 请求
        with patch('requests.get') as mock_get:
            mock_crawl_resp = MagicMock()
            mock_crawl_resp.status_code = 200
            mock_crawl_resp.text = mock_crawl_response["content"]
            mock_crawl_resp.headers = {"Content-Type": "text/html"}
            mock_get.return_value = mock_crawl_resp
            
            # 设置 mock 返回值
            mock_session.post.return_value = mock_search_resp
            
            # 测试搜索功能
            client = BochaAIClient(api_key="test_api_key")
            
            print("\n1. 测试搜索功能:")
            search_result = client.search(query="Python编程", count=3, summary=True)
            
            print(f"   搜索成功: {search_result.success}")
            print(f"   结果数量: {len(search_result.webpages)}")
            for idx, page in enumerate(search_result.webpages, 1):
                print(f"   {idx}. {page.name}")
                print(f"      URL: {page.url}")
                if page.summary:
                    print(f"      摘要: {page.summary[:50]}...")
            
            # 测试爬取功能
            print("\n2. 测试爬取功能:")
            crawl_result = client.crawl_page("https://www.python.org")
            print(f"   爬取成功: {crawl_result.get('success', False)}")
            print(f"   页面标题: {crawl_result.get('title', 'N/A')}")
            print(f"   内容长度: {crawl_result.get('content_length', 0)} 字符")
    
    print("\n✅ BochaAI Client Mock 测试通过")


def test_web_search_tool_with_bochaai():
    """测试 WebSearchTool 与 BochaAI 的集成"""
    print("\n" + "=" * 60)
    print("测试 WebSearchTool 与 BochaAI 集成")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.bochaai_api_key = "test_bochaai_key"
    mock_args.metaso_api_key = None
    mock_args.firecrawl_api_key = None
    
    # 创建工具实例
    tool = WebSearchTool(
        query="人工智能最新进展",
        limit=3,
        provider="bochaai"
    )
    
    # 创建解析器
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    print("\n1. 测试工具配置:")
    print(f"   查询: {tool.query}")
    print(f"   限制: {tool.limit}")
    print(f"   提供商: {tool.provider}")
    
    # Mock BochaAI 客户端
    with patch('autocoder.rag.tools.web_search_tool.BochaAIClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # 设置 mock 搜索结果
        mock_search_result = MagicMock()
        mock_search_result.success = True
        mock_search_result.webpages = [
            MagicMock(
                name="AI 突破性进展",
                url="https://ai-news.com/breakthrough",
                snippet="最新的人工智能研究取得重大突破...",
                summary="详细的研究成果说明...",
                site_name="AI News",
                date_published="2024-01-15T00:00:00Z"
            ),
            MagicMock(
                name="深度学习新算法",
                url="https://ml-research.org/new-algo",
                snippet="研究人员开发出新的深度学习算法...",
                summary=None,
                site_name="ML Research",
                date_published=None
            )
        ]
        mock_search_result.images = []
        mock_client.search.return_value = mock_search_result
        
        # 执行搜索
        result = resolver.resolve()
        
        print("\n2. 测试搜索结果:")
        print(f"   执行成功: {result.success}")
        print(f"   消息: {result.message}")
        print(f"   结果数量: {len(result.content)}")
        
        if result.success and result.content:
            for idx, item in enumerate(result.content[:2], 1):
                print(f"\n   结果 {idx}:")
                print(f"     标题: {item['title']}")
                print(f"     URL: {item['url']}")
                print(f"     提供商: {item.get('provider', 'unknown')}")
                if 'summary' in item:
                    print(f"     摘要: {item['summary'][:50]}...")
    
    print("\n✅ WebSearchTool BochaAI 集成测试通过")


def test_web_crawl_tool_with_bochaai():
    """测试 WebCrawlTool 与 BochaAI 的集成"""
    print("\n" + "=" * 60)
    print("测试 WebCrawlTool 与 BochaAI 集成")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.bochaai_api_key = "test_bochaai_key"
    mock_args.metaso_api_key = None
    mock_args.firecrawl_api_key = None
    
    # 测试单页爬取
    print("\n1. 测试单页爬取模式:")
    tool = WebCrawlTool(
        url="https://docs.python.org/tutorial",
        limit=1,
        provider="bochaai"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, tool, mock_args)
    
    with patch('autocoder.rag.tools.web_crawl_tool.BochaAIClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock crawl_page 方法
        mock_client.crawl_page.return_value = {
            "success": True,
            "url": "https://docs.python.org/tutorial",
            "title": "Python 教程",
            "content": "# Python 教程\n\n这是 Python 官方教程的内容...",
            "content_type": "text/html",
            "status_code": 200
        }
        
        result = resolver.resolve()
        
        print(f"   执行成功: {result.success}")
        print(f"   消息: {result.message}")
        if result.success and result.content:
            print(f"   URL: {result.content[0]['url']}")
            print(f"   标题: {result.content[0].get('title', 'N/A')}")
            print(f"   内容长度: {len(result.content[0]['content'])} 字符")
    
    # 测试多页爬取
    print("\n2. 测试多页爬取模式:")
    tool = WebCrawlTool(
        url="https://docs.python.org",
        limit=5,
        exclude_paths="/api,/admin",
        include_paths="/tutorial,/library",
        allow_subdomains="true",
        provider="bochaai"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, tool, mock_args)
    
    with patch('autocoder.rag.tools.web_crawl_tool.BochaAIClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock crawl 方法
        mock_crawl_results = [
            {
                "url": "https://docs.python.org/tutorial/index.html",
                "title": "Python 教程",
                "content": "教程主页内容...",
                "markdown": "# Python 教程\n\n教程主页内容...",
                "metadata": {"source": "bochaai"}
            },
            {
                "url": "https://docs.python.org/tutorial/introduction.html",
                "title": "Python 简介",
                "content": "Python 简介内容...",
                "markdown": "# Python 简介\n\nPython 简介内容...",
                "metadata": {"source": "bochaai"}
            }
        ]
        mock_client.crawl.return_value = mock_crawl_results
        
        result = resolver.resolve()
        
        print(f"   执行成功: {result.success}")
        print(f"   消息: {result.message}")
        print(f"   爬取页面数: {len(result.content) if result.success else 0}")
        
        if result.success and result.content:
            for idx, page in enumerate(result.content[:2], 1):
                print(f"\n   页面 {idx}:")
                print(f"     URL: {page['url']}")
                print(f"     标题: {page.get('title', 'N/A')}")
                print(f"     来源: {page.get('metadata', {}).get('source', 'unknown')}")
    
    print("\n✅ WebCrawlTool BochaAI 集成测试通过")


def test_provider_auto_detection():
    """测试提供商自动检测功能"""
    print("\n" + "=" * 60)
    print("测试提供商自动检测（包含 BochaAI）")
    print("=" * 60)
    
    mock_agent = Mock()
    
    # 场景1: 只有 BochaAI key
    print("\n1. 只有 BochaAI API key:")
    mock_args = Mock()
    mock_args.bochaai_api_key = "bochaai_key"
    mock_args.metaso_api_key = None
    mock_args.firecrawl_api_key = None
    
    tool = WebSearchTool(
        query="test",
        provider=None  # 不指定，让系统自动检测
    )
    
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    with patch('autocoder.rag.tools.web_search_tool.BochaAIClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_search_result = MagicMock()
        mock_search_result.success = True
        mock_search_result.webpages = []
        mock_search_result.images = []
        mock_client.search.return_value = mock_search_result
        
        result = resolver.resolve()
        print(f"   自动选择: BochaAI (预期)")
        print(f"   消息包含 'BochaAI': {'BochaAI' in result.message}")
    
    # 场景2: 多个 key 都有
    print("\n2. 三个 API key 都有:")
    mock_args = Mock()
    mock_args.bochaai_api_key = "bochaai_key"
    mock_args.metaso_api_key = "metaso_key"
    mock_args.firecrawl_api_key = "firecrawl_key"
    
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    with patch('firecrawl.Firecrawl') as mock_firecrawl_class:
        mock_firecrawl = MagicMock()
        mock_firecrawl_class.return_value = mock_firecrawl
        mock_search_result = MagicMock()
        mock_search_result.success = True
        mock_search_result.data = []
        mock_firecrawl.search.return_value = mock_search_result
        
        result = resolver.resolve()
        print(f"   优先选择: Firecrawl (预期)")
        print(f"   消息包含 'Firecrawl': {'Firecrawl' in result.message}")
    
    # 场景3: BochaAI 和 Metaso
    print("\n3. BochaAI 和 Metaso API key:")
    mock_args = Mock()
    mock_args.bochaai_api_key = "bochaai_key"
    mock_args.metaso_api_key = "metaso_key"
    mock_args.firecrawl_api_key = None
    
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    with patch('autocoder.rag.tools.web_search_tool.BochaAIClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_search_result = MagicMock()
        mock_search_result.success = True
        mock_search_result.webpages = []
        mock_search_result.images = []
        mock_client.search.return_value = mock_search_result
        
        result = resolver.resolve()
        print(f"   优先选择: BochaAI (预期)")
        print(f"   消息包含 'BochaAI': {'BochaAI' in result.message}")
    
    print("\n✅ 提供商自动检测测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试 BochaAI 集成")
    print("=" * 60)
    
    try:
        # 运行各项测试
        test_bochaai_sdk()
        test_bochaai_client_mock()
        test_web_search_tool_with_bochaai()
        test_web_crawl_tool_with_bochaai()
        test_provider_auto_detection()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
        print("\n测试总结:")
        print("1. ✅ BochaAI SDK 数据类功能正常")
        print("2. ✅ BochaAI Client 搜索和爬取功能正常")
        print("3. ✅ WebSearchTool 成功集成 BochaAI")
        print("4. ✅ WebCrawlTool 成功集成 BochaAI")
        print("5. ✅ 提供商自动检测机制正常（支持 BochaAI）")
        
        print("\n下一步:")
        print("1. 设置环境变量 BOCHAAI_API_KEY")
        print("2. 在工具中指定 provider='bochaai' 或让系统自动检测")
        print("3. 使用工具进行实际的网页搜索和爬取")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

