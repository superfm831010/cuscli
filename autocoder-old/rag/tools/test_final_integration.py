
"""
最终集成验证脚本

验证 Metaso 集成是否完全正常工作。
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


def test_imports():
    """测试所有导入是否正常"""
    print("=" * 60)
    print("测试导入")
    print("=" * 60)
    
    try:
        # 测试直接导入
        from autocoder.rag.tools.metaso_sdk import MetasoClient, MetasoSearchResult, MetasoSearchResponse
        print("✅ Metaso SDK 导入成功")
        
        from autocoder.rag.tools.web_search_tool import WebSearchTool, WebSearchToolResolver
        print("✅ WebSearchTool 导入成功")
        
        from autocoder.rag.tools.web_crawl_tool import WebCrawlTool, WebCrawlToolResolver
        print("✅ WebCrawlTool 导入成功")
        
        # 测试从 __init__ 导入
        from autocoder.rag.tools import MetasoClient as MC
        from autocoder.rag.tools import MetasoSearchResult as MSR
        from autocoder.rag.tools import MetasoSearchResponse as MSResp
        print("✅ 从 __init__.py 导入 Metaso 类成功")
        
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_metaso_integration():
    """测试 Metaso 集成功能"""
    print("\n" + "=" * 60)
    print("测试 Metaso 集成功能")
    print("=" * 60)
    
    from autocoder.rag.tools.web_search_tool import WebSearchTool
    from autocoder.rag.tools.web_crawl_tool import WebCrawlTool
    
    # 测试工具创建
    try:
        # 测试搜索工具
        search_tool = WebSearchTool(
            query="test query",
            limit=5,
            provider="metaso"
        )
        print(f"✅ WebSearchTool 创建成功")
        print(f"   - query: {search_tool.query}")
        print(f"   - limit: {search_tool.limit}")
        print(f"   - provider: {search_tool.provider}")
        
        # 测试爬取工具
        crawl_tool = WebCrawlTool(
            url="https://example.com",
            limit=10,
            provider="metaso"
        )
        print(f"✅ WebCrawlTool 创建成功")
        print(f"   - url: {crawl_tool.url}")
        print(f"   - limit: {crawl_tool.limit}")
        print(f"   - provider: {crawl_tool.provider}")
        
        return True
    except Exception as e:
        print(f"❌ 工具创建失败: {e}")
        return False


def test_provider_field():
    """测试 provider 字段是否正确添加"""
    print("\n" + "=" * 60)
    print("测试 Provider 字段")
    print("=" * 60)
    
    from autocoder.rag.tools.web_search_tool import WebSearchTool
    from autocoder.rag.tools.web_crawl_tool import WebCrawlTool
    
    # 检查字段是否存在
    search_fields = WebSearchTool.__annotations__
    crawl_fields = WebCrawlTool.__annotations__
    
    if 'provider' in search_fields:
        print(f"✅ WebSearchTool 包含 provider 字段")
        print(f"   类型: {search_fields['provider']}")
    else:
        print(f"❌ WebSearchTool 缺少 provider 字段")
        return False
    
    if 'provider' in crawl_fields:
        print(f"✅ WebCrawlTool 包含 provider 字段")
        print(f"   类型: {crawl_fields['provider']}")
    else:
        print(f"❌ WebCrawlTool 缺少 provider 字段")
        return False
    
    return True


def test_metaso_sdk():
    """测试 Metaso SDK 基本功能"""
    print("\n" + "=" * 60)
    print("测试 Metaso SDK")
    print("=" * 60)
    
    from autocoder.rag.tools.metaso_sdk import MetasoClient, MetasoSearchResult
    
    # 测试数据类创建
    try:
        result = MetasoSearchResult(
            title="Test Title",
            link="https://test.com",
            snippet="Test snippet"
        )
        print(f"✅ MetasoSearchResult 创建成功")
        print(f"   - title: {result.title}")
        print(f"   - link: {result.link}")
        
        # 测试转换为字典
        result_dict = result.to_dict()
        print(f"✅ to_dict() 方法正常")
        print(f"   字段数: {len(result_dict)}")
        
        return True
    except Exception as e:
        print(f"❌ SDK 测试失败: {e}")
        return False


def check_files():
    """检查所有必要文件是否存在"""
    print("\n" + "=" * 60)
    print("检查文件完整性")
    print("=" * 60)
    
    required_files = [
        "src/autocoder/rag/tools/metaso_sdk.py",
        "src/autocoder/rag/tools/web_search_tool.py",
        "src/autocoder/rag/tools/web_crawl_tool.py",
        "src/autocoder/rag/tools/test_metaso_integration.py",
        "src/autocoder/rag/tools/metaso_example.py",
        "src/autocoder/rag/tools/README_metaso.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join("/Users/williamzhu/projects/auto-coder", file_path)
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"✅ {os.path.basename(file_path)}: {file_size:,} bytes")
        else:
            print(f"❌ {os.path.basename(file_path)}: 不存在")
            all_exist = False
    
    return all_exist


def main():
    """运行所有验证测试"""
    print("\n" + "=" * 60)
    print("Metaso 集成最终验证")
    print("=" * 60)
    
    results = []
    
    # 运行各项测试
    print("\n开始验证...\n")
    
    results.append(("文件完整性", check_files()))
    results.append(("模块导入", test_imports()))
    results.append(("Provider 字段", test_provider_field()))
    results.append(("Metaso SDK", test_metaso_sdk()))
    results.append(("工具集成", test_metaso_integration()))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有验证通过！Metaso 集成完成！")
        print("\n下一步：")
        print("1. 设置环境变量: export METASO_API_KEY='your-api-key'")
        print("2. 运行示例: python src/autocoder/rag/tools/metaso_example.py")
        print("3. 在代码中使用: provider='metaso'")
    else:
        print("⚠️  部分验证失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
