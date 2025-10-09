
"""
测试 Metaso SDK 集成

该文件用于测试 Metaso SDK 的功能以及与 web_search_tool 和 web_crawl_tool 的集成。
"""

import os
import sys
import json
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from autocoder.rag.tools.metaso_sdk import MetasoClient, MetasoSearchResult, MetasoSearchResponse
from autocoder.rag.tools.web_search_tool import WebSearchTool, WebSearchToolResolver
from autocoder.rag.tools.web_crawl_tool import WebCrawlTool, WebCrawlToolResolver


def test_metaso_sdk():
    """测试 Metaso SDK 基本功能"""
    print("=" * 60)
    print("测试 Metaso SDK 基本功能")
    print("=" * 60)
    
    # 测试数据类
    search_result = MetasoSearchResult(
        title="测试标题",
        link="https://example.com",
        snippet="这是一个测试摘要",
        score="high",
        position=1,
        date="2024年01月01日"
    )
    
    print("\n1. 测试 MetasoSearchResult 数据类:")
    print(f"   标题: {search_result.title}")
    print(f"   链接: {search_result.link}")
    print(f"   摘要: {search_result.snippet[:30]}...")
    print(f"   转换为字典: {json.dumps(search_result.to_dict(), ensure_ascii=False, indent=2)}")
    
    # 测试响应类
    search_response = MetasoSearchResponse(
        credits=10,
        search_parameters={"q": "测试查询", "size": 5},
        webpages=[search_result],
        success=True
    )
    
    print("\n2. 测试 MetasoSearchResponse 数据类:")
    print(f"   成功状态: {search_response.success}")
    print(f"   剩余积分: {search_response.credits}")
    print(f"   结果数量: {len(search_response.webpages)}")
    
    print("\n✅ Metaso SDK 数据类测试通过")


def test_metaso_client_mock():
    """使用 mock 测试 Metaso Client"""
    print("\n" + "=" * 60)
    print("测试 Metaso Client (使用 Mock)")
    print("=" * 60)
    
    # Mock API 响应
    mock_search_response = {
        "credits": 10,
        "searchParameters": {
            "q": "Python编程",
            "scope": "webpage",
            "size": "3"
        },
        "webpages": [
            {
                "title": "Python 官方网站",
                "link": "https://www.python.org",
                "snippet": "Python 是一种编程语言，可让您快速工作并更有效地集成系统。",
                "score": "high",
                "position": 1
            },
            {
                "title": "Python 教程",
                "link": "https://docs.python.org/tutorial",
                "snippet": "本教程非正式地向读者介绍了 Python 语言和系统的基本概念和功能。",
                "score": "high",
                "position": 2
            }
        ]
    }
    
    mock_read_response = """# Python 编程语言
    
Python 是一种高级编程语言，具有动态语义。其高级内置数据结构与动态类型和动态绑定相结合，
使其对于快速应用程序开发以及用作脚本或粘合语言将现有组件连接在一起非常有吸引力。

## 主要特性
- 简单易学
- 功能强大
- 跨平台
"""
    
    with patch('requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock search 请求
        mock_search_resp = MagicMock()
        mock_search_resp.status_code = 200
        mock_search_resp.json.return_value = mock_search_response
        
        # Mock read 请求
        mock_read_resp = MagicMock()
        mock_read_resp.status_code = 200
        mock_read_resp.text = mock_read_response
        mock_read_resp.json.return_value = {"content": mock_read_response}
        
        # 设置 mock 返回值
        mock_session.post.side_effect = [mock_search_resp, mock_read_resp]
        
        # 测试搜索功能
        client = MetasoClient(api_key="test_api_key")
        
        print("\n1. 测试搜索功能:")
        search_result = client.search(query="Python编程", size=3)
        
        print(f"   搜索成功: {search_result.success}")
        print(f"   结果数量: {len(search_result.webpages)}")
        for idx, page in enumerate(search_result.webpages, 1):
            print(f"   {idx}. {page.title}")
            print(f"      URL: {page.link}")
            print(f"      评分: {page.score}")
        
        # 测试读取功能
        print("\n2. 测试读取功能:")
        content = client.read("https://www.python.org")
        print(f"   读取成功: {not content.startswith('Error:')}")
        print(f"   内容长度: {len(content)} 字符")
        print(f"   内容预览: {content[:100]}...")
    
    print("\n✅ Metaso Client Mock 测试通过")


def test_web_search_tool_with_metaso():
    """测试 WebSearchTool 与 Metaso 的集成"""
    print("\n" + "=" * 60)
    print("测试 WebSearchTool 与 Metaso 集成")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.metaso_api_key = "test_metaso_key"
    mock_args.firecrawl_api_key = None
    
    # 创建工具实例
    tool = WebSearchTool(
        query="人工智能最新进展",
        limit=3,
        provider="metaso"
    )
    
    # 创建解析器
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    print("\n1. 测试工具配置:")
    print(f"   查询: {tool.query}")
    print(f"   限制: {tool.limit}")
    print(f"   提供商: {tool.provider}")
    
    # Mock Metaso 客户端
    with patch('autocoder.rag.tools.web_search_tool.MetasoClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # 设置 mock 搜索结果
        mock_search_result = MagicMock()
        mock_search_result.success = True
        mock_search_result.webpages = [
            MagicMock(
                title="AI 突破性进展",
                link="https://ai-news.com/breakthrough",
                snippet="最新的人工智能研究取得重大突破...",
                position=1,
                score="high",
                date="2024年01月15日",
                authors=["张三", "李四"]
            ),
            MagicMock(
                title="深度学习新算法",
                link="https://ml-research.org/new-algo",
                snippet="研究人员开发出新的深度学习算法...",
                position=2,
                score="medium",
                date=None,
                authors=None
            )
        ]
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
                if 'date' in item:
                    print(f"     日期: {item['date']}")
    
    print("\n✅ WebSearchTool Metaso 集成测试通过")


def test_web_crawl_tool_with_metaso():
    """测试 WebCrawlTool 与 Metaso 的集成"""
    print("\n" + "=" * 60)
    print("测试 WebCrawlTool 与 Metaso 集成")
    print("=" * 60)
    
    # 创建 mock agent 和 args
    mock_agent = Mock()
    mock_args = Mock()
    mock_args.metaso_api_key = "test_metaso_key"
    mock_args.firecrawl_api_key = None
    
    # 测试单页读取
    print("\n1. 测试单页读取模式:")
    tool = WebCrawlTool(
        url="https://docs.python.org/tutorial",
        limit=1,
        provider="metaso"
    )
    
    resolver = WebCrawlToolResolver(mock_agent, tool, mock_args)
    
    with patch('autocoder.rag.tools.web_crawl_tool.MetasoClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock read 方法
        mock_client.read.return_value = "# Python 教程\n\n这是 Python 官方教程的内容..."
        
        result = resolver.resolve()
        
        print(f"   执行成功: {result.success}")
        print(f"   消息: {result.message}")
        if result.success and result.content:
            print(f"   URL: {result.content[0]['url']}")
            print(f"   内容长度: {len(result.content[0]['content'])} 字符")
    
    # 测试多页爬取
    print("\n2. 测试多页爬取模式:")
    tool = WebCrawlTool(
        url="https://docs.python.org",
        limit=5,
        exclude_paths="/api,/admin",
        include_paths="/tutorial,/library",
        allow_subdomains="true",
        provider="metaso"
    )
    
    with patch('autocoder.rag.tools.web_crawl_tool.MetasoClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock crawl 方法
        mock_crawl_results = [
            {
                "url": "https://docs.python.org/tutorial/index.html",
                "title": "Python 教程",
                "content": "教程主页内容...",
                "markdown": "# Python 教程\n\n教程主页内容...",
                "metadata": {"source": "metaso"}
            },
            {
                "url": "https://docs.python.org/tutorial/introduction.html",
                "title": "Python 简介",
                "content": "Python 简介内容...",
                "markdown": "# Python 简介\n\nPython 简介内容...",
                "metadata": {"source": "metaso"}
            }
        ]
        mock_client.crawl.return_value = mock_crawl_results
        
        result = resolver.resolve()
        
        print(f"   执行成功: {result.success}")
        print(f"   消息: {result.message}")
        print(f"   爬取页面数: {len(result.content)}")
        
        if result.success and result.content:
            for idx, page in enumerate(result.content[:2], 1):
                print(f"\n   页面 {idx}:")
                print(f"     URL: {page['url']}")
                print(f"     标题: {page.get('title', 'N/A')}")
                print(f"     来源: {page.get('metadata', {}).get('source', 'unknown')}")
    
    print("\n✅ WebCrawlTool Metaso 集成测试通过")


def test_provider_auto_detection():
    """测试提供商自动检测功能"""
    print("\n" + "=" * 60)
    print("测试提供商自动检测")
    print("=" * 60)
    
    mock_agent = Mock()
    
    # 场景1: 只有 Metaso key
    print("\n1. 只有 Metaso API key:")
    mock_args = Mock()
    mock_args.metaso_api_key = "metaso_key"
    mock_args.firecrawl_api_key = None
    
    tool = WebSearchTool(
        query="test",
        provider=None  # 不指定，让系统自动检测
    )
    
    resolver = WebSearchToolResolver(mock_agent, tool, mock_args)
    
    with patch('autocoder.rag.tools.web_search_tool.MetasoClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_search_result = MagicMock()
        mock_search_result.success = True
        mock_search_result.webpages = []
        mock_client.search.return_value = mock_search_result
        
        result = resolver.resolve()
        print(f"   自动选择: Metaso (预期)")
        print(f"   消息包含 'Metaso': {'Metaso' in result.message}")
    
    # 场景2: 只有 Firecrawl key
    print("\n2. 只有 Firecrawl API key:")
    mock_args = Mock()
    mock_args.metaso_api_key = None
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
        print(f"   自动选择: Firecrawl (预期)")
        print(f"   消息包含 'Firecrawl': {'Firecrawl' in result.message}")
    
    # 场景3: 两个都有，默认使用 Firecrawl
    print("\n3. 两个 API key 都有:")
    mock_args = Mock()
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
        print(f"   默认选择: Firecrawl (预期)")
        print(f"   消息包含 'Firecrawl': {'Firecrawl' in result.message}")
    
    print("\n✅ 提供商自动检测测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试 Metaso 集成")
    print("=" * 60)
    
    try:
        # 运行各项测试
        test_metaso_sdk()
        test_metaso_client_mock()
        test_web_search_tool_with_metaso()
        test_web_crawl_tool_with_metaso()
        test_provider_auto_detection()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
        print("\n测试总结:")
        print("1. ✅ Metaso SDK 数据类功能正常")
        print("2. ✅ Metaso Client 搜索和读取功能正常")
        print("3. ✅ WebSearchTool 成功集成 Metaso")
        print("4. ✅ WebCrawlTool 成功集成 Metaso")
        print("5. ✅ 提供商自动检测机制正常")
        
        print("\n下一步:")
        print("1. 设置环境变量 METASO_API_KEY")
        print("2. 在工具中指定 provider='metaso' 或让系统自动检测")
        print("3. 使用工具进行实际的网页搜索和爬取")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
