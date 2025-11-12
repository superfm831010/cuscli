#!/usr/bin/env python3
"""
Web 工具使用示例

这个文件展示了如何使用 WebSearchTool 和 WebCrawlTool 进行网页搜索和爬取。
注意：需要设置 FIRECRAWL_API_KEY 环境变量或在启动服务时使用 --firecrawl_api_key 参数。
"""

def web_search_example():
    """
    网页搜索工具使用示例
    
    在 Agent 对话中可以这样使用：
    """
    example_xml = """
    <web_search>
    <query>Python RAG系统实现最佳实践</query>
    <limit>5</limit>
    <sources>["web"]</sources>
    </web_search>
    """
    
    print("Web Search Tool 使用示例:")
    print(example_xml)
    print()
    
    # 搜索新闻的示例
    news_example = """
    <web_search>
    <query>人工智能最新发展</query>
    <limit>3</limit>
    <sources>["news"]</sources>
    <location>China</location>
    <tbs>qdr:d</tbs>
    </web_search>
    """
    
    print("搜索新闻示例:")
    print(news_example)
    print()
    
    # 搜索图片的示例
    image_example = """
    <web_search>
    <query>机器学习架构图 imagesize:1920x1080</query>
    <limit>5</limit>
    <sources>["images"]</sources>
    </web_search>
    """
    
    print("搜索图片示例:")
    print(image_example)
    print()


def web_crawl_example():
    """
    网页爬取工具使用示例
    
    在 Agent 对话中可以这样使用：
    """
    example_xml = """
    <web_crawl>
    <url>https://docs.python.org/3/tutorial/</url>
    <limit>10</limit>
    <scrape_options>{"formats": ["markdown", "links"]}</scrape_options>
    <max_depth>2</max_depth>
    </web_crawl>
    """
    
    print("Web Crawl Tool 使用示例:")
    print(example_xml)
    print()
    
    # 爬取特定路径的示例
    specific_paths_example = """
    <web_crawl>
    <url>https://example.com</url>
    <limit>5</limit>
    <include_paths>["/docs/", "/api/"]</include_paths>
    <exclude_paths>["/admin/", "/private/"]</exclude_paths>
    </web_crawl>
    """
    
    print("爬取特定路径示例:")
    print(specific_paths_example)
    print()


def setup_instructions():
    """
    设置说明
    """
    print("=== Firecrawl Web 工具设置说明 ===")
    print()
    print("1. 安装 Firecrawl SDK:")
    print("   pip install firecrawl-py")
    print()
    print("2. 获取 Firecrawl API Key:")
    print("   - 访问 https://firecrawl.dev/ 注册账号")
    print("   - 获取 API Key")
    print()
    print("3. 配置 API Key:")
    print("   方式 1: 设置环境变量")
    print("   export FIRECRAWL_API_KEY=your_api_key_here")
    print()
    print("   方式 2: 启动服务时指定参数")
    print("   auto-coder.rag serve --firecrawl_api_key your_api_key_here")
    print()
    print("4. 工具功能说明:")
    print("   - WebSearchTool: 搜索网页、新闻、图片")
    print("   - WebCrawlTool: 深度爬取网站内容")
    print()


if __name__ == "__main__":
    setup_instructions()
    web_search_example()
    web_crawl_example()
