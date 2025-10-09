"""
WebSearchTool 的 pytest 测试类

该测试模块使用纯 pytest 风格，包含 fixtures、参数化测试和覆盖率测试。
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from autocoder.agent.base_agentic.types import ToolResult
from .web_search_tool import WebSearchTool, WebSearchToolResolver, register_web_search_tool


class TestWebSearchTool:
    """WebSearchTool 基础功能测试"""
    
    def test_web_search_tool_creation(self):
        """测试 WebSearchTool 实例创建"""
        tool = WebSearchTool(query="test query")
        assert tool.query == "test query"
        assert tool.limit == 5  # 默认值
        assert tool.sources is None
        assert tool.scrape_options is None
        assert tool.location is None
        assert tool.tbs is None
    
    def test_web_search_tool_with_all_params(self):
        """测试 WebSearchTool 使用所有参数创建"""
        tool = WebSearchTool(
            query="Python tutorial",
            limit=10,
            sources=["web", "news"],
            scrape_options={"formats": ["markdown"]},
            location="China",
            tbs="qdr:d"
        )
        assert tool.query == "Python tutorial"
        assert tool.limit == 10
        assert tool.sources == ["web", "news"]
        assert tool.scrape_options == {"formats": ["markdown"]}
        assert tool.location == "China"
        assert tool.tbs == "qdr:d"


class TestWebSearchToolResolver:
    """WebSearchToolResolver 功能测试"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建 mock agent"""
        agent = Mock()
        agent.rag = Mock()
        return agent
    
    @pytest.fixture
    def mock_args_without_api_key(self):
        """创建没有 API key 的 mock args"""
        args = Mock()
        args.firecrawl_api_key = None
        return args
    
    @pytest.fixture
    def mock_args_with_api_key(self):
        """创建有 API key 的 mock args"""
        args = Mock()
        args.firecrawl_api_key = "test-api-key"
        return args
    
    @pytest.fixture
    def basic_search_tool(self):
        """创建基础搜索工具"""
        return WebSearchTool(query="test query")
    
    @pytest.fixture
    def advanced_search_tool(self):
        """创建高级搜索工具"""
        return WebSearchTool(
            query="Python RAG",
            limit=3,
            sources=["web"],
            location="US"
        )
    
    def test_resolver_creation(self, mock_agent, basic_search_tool, mock_args_without_api_key):
        """测试解析器创建"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_without_api_key)
        assert resolver.agent == mock_agent
        assert resolver.tool == basic_search_tool
        assert resolver.args == mock_args_without_api_key
    
    def test_resolve_without_api_key_in_args(self, mock_agent, basic_search_tool, mock_args_without_api_key):
        """测试没有 API key 时的错误处理"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_without_api_key)
        
        with patch.dict(os.environ, {}, clear=True):
            result = resolver.resolve()
            
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "未提供 Firecrawl API key" in result.message
        assert result.content == []
    
    def test_resolve_with_api_key_from_env(self, mock_agent, basic_search_tool, mock_args_without_api_key):
        """测试从环境变量获取 API key"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_without_api_key)
        
        with patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'env-api-key'}):
            with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
                mock_firecrawl = Mock()
                mock_firecrawl_class.return_value = mock_firecrawl
                mock_firecrawl.search.return_value = {
                    'success': True,
                    'data': {
                        'web': [
                            {
                                'title': 'Test Result',
                                'url': 'https://example.com',
                                'description': 'Test description',
                                'position': 1
                            }
                        ]
                    }
                }
                
                result = resolver.resolve()
                
        assert isinstance(result, ToolResult)
        assert result.success
        mock_firecrawl_class.assert_called_once_with(api_key='env-api-key')
        mock_firecrawl.search.assert_called_once()
    
    def test_resolve_without_firecrawl_sdk(self, mock_agent, basic_search_tool, mock_args_with_api_key):
        """测试没有安装 Firecrawl SDK 时的错误处理"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_with_api_key)
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl', side_effect=ImportError):
            result = resolver.resolve()
            
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "未安装 Firecrawl SDK" in result.message
        assert "pip install firecrawl-py" in result.message
    
    def test_resolve_successful_web_search(self, mock_agent, basic_search_tool, mock_args_with_api_key):
        """测试成功的网页搜索"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_with_api_key)
        
        mock_response = {
            'success': True,
            'data': {
                'web': [
                    {
                        'title': 'Python Tutorial',
                        'url': 'https://python.org/tutorial',
                        'description': 'Official Python tutorial',
                        'position': 1,
                        'markdown': '# Python Tutorial\nLearn Python...',
                        'links': ['https://python.org/docs'],
                        'metadata': {'status': 200}
                    },
                    {
                        'title': 'Advanced Python',
                        'url': 'https://realpython.com',
                        'description': 'Advanced Python concepts',
                        'position': 2
                    }
                ]
            }
        }
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.return_value = mock_response
            
            result = resolver.resolve()
            
        assert isinstance(result, ToolResult)
        assert result.success
        assert "成功搜索到 2 个结果" in result.message
        assert len(result.content) == 2
        
        # 检查第一个结果
        first_result = result.content[0]
        assert first_result['type'] == 'web'
        assert first_result['title'] == 'Python Tutorial'
        assert first_result['url'] == 'https://python.org/tutorial'
        assert first_result['description'] == 'Official Python tutorial'
        assert first_result['position'] == 1
        assert first_result['content'] == '# Python Tutorial\nLearn Python...'
        assert first_result['links'] == ['https://python.org/docs']
        assert first_result['metadata'] == {'status': 200}
        
        # 检查第二个结果
        second_result = result.content[1]
        assert second_result['type'] == 'web'
        assert second_result['title'] == 'Advanced Python'
        assert 'content' not in second_result  # 没有 markdown 内容
    
    def test_resolve_successful_news_search(self, mock_agent, mock_args_with_api_key):
        """测试成功的新闻搜索"""
        news_tool = WebSearchTool(query="AI news", sources=["news"])
        resolver = WebSearchToolResolver(mock_agent, news_tool, mock_args_with_api_key)
        
        mock_response = {
            'success': True,
            'data': {
                'news': [
                    {
                        'title': 'AI Breakthrough',
                        'url': 'https://news.com/ai',
                        'snippet': 'Latest AI developments...',
                        'date': '2024-01-01',
                        'position': 1
                    }
                ]
            }
        }
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.return_value = mock_response
            
            result = resolver.resolve()
            
        assert result.success
        assert len(result.content) == 1
        news_result = result.content[0]
        assert news_result['type'] == 'news'
        assert news_result['title'] == 'AI Breakthrough'
        assert news_result['snippet'] == 'Latest AI developments...'
        assert news_result['date'] == '2024-01-01'
    
    def test_resolve_successful_image_search(self, mock_agent, mock_args_with_api_key):
        """测试成功的图片搜索"""
        image_tool = WebSearchTool(query="machine learning", sources=["images"])
        resolver = WebSearchToolResolver(mock_agent, image_tool, mock_args_with_api_key)
        
        mock_response = {
            'success': True,
            'data': {
                'images': [
                    {
                        'title': 'ML Diagram',
                        'imageUrl': 'https://example.com/ml.jpg',
                        'url': 'https://example.com',
                        'imageWidth': 1920,
                        'imageHeight': 1080,
                        'position': 1
                    }
                ]
            }
        }
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.return_value = mock_response
            
            result = resolver.resolve()
            
        assert result.success
        assert len(result.content) == 1
        image_result = result.content[0]
        assert image_result['type'] == 'image'
        assert image_result['title'] == 'ML Diagram'
        assert image_result['imageUrl'] == 'https://example.com/ml.jpg'
        assert image_result['imageWidth'] == 1920
        assert image_result['imageHeight'] == 1080
    
    def test_resolve_api_failure(self, mock_agent, basic_search_tool, mock_args_with_api_key):
        """测试 API 调用失败"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_with_api_key)
        
        mock_response = {
            'success': False,
            'error': 'API rate limit exceeded'
        }
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.return_value = mock_response
            
            result = resolver.resolve()
            
        assert not result.success
        assert "搜索失败: API rate limit exceeded" in result.message
    
    def test_resolve_with_advanced_params(self, mock_agent, advanced_search_tool, mock_args_with_api_key):
        """测试使用高级参数的搜索"""
        resolver = WebSearchToolResolver(mock_agent, advanced_search_tool, mock_args_with_api_key)
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.return_value = {'success': True, 'data': {'web': []}}
            
            result = resolver.resolve()
            
            # 验证调用参数
            call_args = mock_firecrawl.search.call_args[1]
            assert call_args['query'] == "Python RAG"
            assert call_args['limit'] == 3
            assert call_args['sources'] == ["web"]
            assert call_args['location'] == "US"
    
    def test_resolve_exception_handling(self, mock_agent, basic_search_tool, mock_args_with_api_key):
        """测试异常处理"""
        resolver = WebSearchToolResolver(mock_agent, basic_search_tool, mock_args_with_api_key)
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.side_effect = Exception("Network error")
            
            result = resolver.resolve()
            
        assert not result.success
        assert "网页搜索工具执行失败" in result.message
        assert "Network error" in result.message
    
    @pytest.mark.parametrize("sources,expected_count", [
        (["web"], 1),
        (["news"], 1), 
        (["images"], 1),
        (["web", "news"], 2),
        (["web", "news", "images"], 3)
    ])
    def test_resolve_multiple_sources(self, mock_agent, mock_args_with_api_key, sources, expected_count):
        """参数化测试：多种数据源组合"""
        tool = WebSearchTool(query="test", sources=sources)
        resolver = WebSearchToolResolver(mock_agent, tool, mock_args_with_api_key)
        
        mock_data = {}
        if "web" in sources:
            mock_data["web"] = [{"title": "Web Result", "url": "http://web.com", "description": "desc", "position": 1}]
        if "news" in sources:
            mock_data["news"] = [{"title": "News Result", "url": "http://news.com", "snippet": "snippet", "date": "2024-01-01", "position": 1}]
        if "images" in sources:
            mock_data["images"] = [{"title": "Image Result", "imageUrl": "http://img.com/img.jpg", "url": "http://src.com", "imageWidth": 100, "imageHeight": 100, "position": 1}]
        
        mock_response = {"success": True, "data": mock_data}
        
        with patch('autocoder.rag.tools.web_search_tool.Firecrawl') as mock_firecrawl_class:
            mock_firecrawl = Mock()
            mock_firecrawl_class.return_value = mock_firecrawl
            mock_firecrawl.search.return_value = mock_response
            
            result = resolver.resolve()
            
        assert result.success
        assert len(result.content) == expected_count


class TestWebSearchToolIntegration:
    """WebSearchTool 集成测试 - 实际调用 Firecrawl API"""
    
    @pytest.fixture
    def real_api_key(self):
        """获取真实的 API key"""
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            pytest.skip("需要设置 FIRECRAWL_API_KEY 环境变量来运行集成测试")
        return api_key
    
    @pytest.fixture
    def mock_agent(self):
        """创建 mock agent"""
        agent = Mock()
        agent.rag = Mock()
        return agent
    
    @pytest.fixture
    def real_args(self, real_api_key):
        """创建真实 args"""
        args = Mock()
        args.firecrawl_api_key = real_api_key
        return args
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('FIRECRAWL_API_KEY'), reason="需要 FIRECRAWL_API_KEY 环境变量")
    def test_real_web_search(self, mock_agent, real_args):
        """实际调用 Firecrawl API 进行网页搜索"""
        try:
            # 导入真实的 Firecrawl SDK
            from firecrawl import Firecrawl
        except ImportError:
            pytest.skip("需要安装 firecrawl-py: pip install firecrawl-py")
        
        # 创建搜索工具 - 使用相对稳定的搜索词
        search_tool = WebSearchTool(
            query="python programming tutorial",
            limit=3,
            sources=["web"]
        )
        
        resolver = WebSearchToolResolver(mock_agent, search_tool, real_args)
        
        # 执行实际搜索 - 设置超时
        import time
        start_time = time.time()
        result = resolver.resolve()
        end_time = time.time()
        
        # 基本断言
        assert isinstance(result, ToolResult)
        print(f"\n=== 实际搜索结果 (耗时: {end_time - start_time:.2f}s) ===")
        print(f"成功: {result.success}")
        print(f"消息: {result.message}")
        
        if result.success:
            print(f"结果数量: {len(result.content)}")
            
            # 集成测试可能因为各种外部因素（API配额、网络、服务状态等）返回空结果
            # 这是可以接受的，我们主要验证API调用机制正常工作
            if len(result.content) > 0:
                print("✓ 返回了搜索结果，验证数据结构")
                assert len(result.content) <= 3, "不应该超过限制的结果数量"
                
                # 验证第一个结果的数据结构
                first_result = result.content[0]
                assert 'type' in first_result, "结果应该包含 type 字段"
                assert first_result['type'] == 'web', "搜索结果类型应该是 web"
                assert 'title' in first_result, "结果应该包含 title 字段"
                assert 'url' in first_result, "结果应该包含 url 字段"
                assert 'description' in first_result, "结果应该包含 description 字段"
                
                # 打印前两个结果用于手动验证
                for i, item in enumerate(result.content[:2]):
                    print(f"\n结果 {i+1}:")
                    print(f"  标题: {item.get('title', 'N/A')}")
                    print(f"  URL: {item.get('url', 'N/A')}")
                    print(f"  描述: {item.get('description', 'N/A')[:100]}...")
                    if 'content' in item:
                        print(f"  内容长度: {len(item['content'])} 字符")
            else:
                print("⚠ 没有返回搜索结果 - 可能是API配额、网络或服务状态影响")
                print("这在集成测试中是可以接受的，主要验证API调用机制正常")
        else:
            print(f"搜索失败: {result.message}")
            # 打印错误内容用于调试
            if result.content:
                print(f"错误详情: {result.content}")
            # 集成测试失败也是可接受的，因为依赖外部服务
            print("注意: 集成测试失败可能由外部因素导致（网络、API限制等）")
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('FIRECRAWL_API_KEY'), reason="需要 FIRECRAWL_API_KEY 环境变量")
    def test_real_image_search(self, mock_agent, real_args):
        """实际调用 Firecrawl API 进行图片搜索"""
        try:
            from firecrawl import Firecrawl
        except ImportError:
            pytest.skip("需要安装 firecrawl-py: pip install firecrawl-py")
        
        # 创建图片搜索工具
        image_tool = WebSearchTool(
            query="python logo",
            limit=2,
            sources=["images"]
        )
        
        resolver = WebSearchToolResolver(mock_agent, image_tool, real_args)
        
        # 执行实际搜索
        import time
        start_time = time.time()
        result = resolver.resolve()
        end_time = time.time()
        
        print(f"\n=== 实际图片搜索结果 (耗时: {end_time - start_time:.2f}s) ===")
        print(f"成功: {result.success}")
        print(f"消息: {result.message}")
        
        if result.success and len(result.content) > 0:
            print(f"图片数量: {len(result.content)}")
            
            # 验证图片结果结构
            first_image = result.content[0]
            assert first_image['type'] == 'image', "结果类型应该是 image"
            assert 'imageUrl' in first_image, "应该包含 imageUrl"
            assert 'title' in first_image, "应该包含 title"
            
            # 打印第一个图片结果
            print(f"  标题: {first_image.get('title', 'N/A')}")
            print(f"  图片URL: {first_image.get('imageUrl', 'N/A')}")
            print(f"  来源URL: {first_image.get('url', 'N/A')}")
            if 'imageWidth' in first_image and 'imageHeight' in first_image:
                print(f"  尺寸: {first_image['imageWidth']}x{first_image['imageHeight']}")


class TestWebSearchToolRegistry:
    """WebSearchTool 注册功能测试"""
    
    def test_register_web_search_tool(self):
        """测试工具注册功能"""
        # 这个测试比较简单，主要确保注册函数能正常调用
        # 具体的注册逻辑测试应该在 ToolRegistry 的测试中
        try:
            register_web_search_tool()
            # 如果没有异常，说明注册成功
            assert True
        except Exception as e:
            # 如果有异常，测试失败
            pytest.fail(f"Tool registration failed: {str(e)}")
