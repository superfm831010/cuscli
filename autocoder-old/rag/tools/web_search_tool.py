"""
WebSearchTool Module

This module implements the WebSearchTool and WebSearchToolResolver classes
for providing web search functionality based on Firecrawl, Metaso, or BochaAI
within the BaseAgent framework.
"""

import os
import traceback
import json
from typing import Dict, Any, List, Optional

import byzerllm
from loguru import logger
from numpy import log

from autocoder.agent.base_agentic.types import BaseTool, ToolResult
from autocoder.agent.base_agentic.tool_registry import ToolRegistry
from autocoder.agent.base_agentic.tools.base_tool_resolver import BaseToolResolver
from autocoder.agent.base_agentic.types import ToolDescription, ToolExample
from autocoder.rag.tools.metaso_sdk import MetasoClient
from autocoder.rag.tools.bochaai_sdk import BochaAIClient


class WebSearchTool(BaseTool):
    """Web search tool using Firecrawl, Metaso, or BochaAI for web search"""
    query: str  # Search query
    limit: Optional[int] = 5  # Return result count limit
    sources: Optional[str] = None  # Search source types, comma-separated: web,news,images
    scrape_options: Optional[str] = None  # Scraping options, JSON string format
    location: Optional[str] = None  # Search location
    tbs: Optional[str] = None  # Time filter parameters


class WebSearchToolResolver(BaseToolResolver):
    """Web search tool resolver that implements search logic"""

    def __init__(self, agent, tool, args):
        super().__init__(agent, tool, args)
        self.tool: WebSearchTool = tool

    def _search_with_bochaai(self) -> ToolResult:
        """Search using BochaAI"""
        try:
            # Check if BochaAI API key is provided
            api_key = getattr(self.args, 'bochaai_api_key', None) or os.getenv('BOCHAAI_API_KEY')
            if not api_key:
                return ToolResult(
                    success=False,
                    message="BochaAI API key not provided, please set --bochaai_api_key parameter or BOCHAAI_API_KEY environment variable",
                    content=[]
                )

            # Initialize BochaAI client
            client = BochaAIClient(api_key=api_key)

            # Prepare search parameters
            freshness = "noLimit"  # Default no time limit
            if self.tool.tbs:
                # Map time filter parameters
                tbs_mapping = {
                    "d": "oneDay",
                    "w": "oneWeek",
                    "m": "oneMonth",
                    "y": "oneYear"
                }
                freshness = tbs_mapping.get(self.tool.tbs, "noLimit")

            # Parse scrape_options to get additional parameters
            include_summary = False
            include_sites = None
            exclude_sites = None
            if self.tool.scrape_options:
                try:
                    scrape_opts = json.loads(self.tool.scrape_options)
                    include_summary = scrape_opts.get('include_summary', False) or scrape_opts.get('summary', False)
                    include_sites = scrape_opts.get('include_sites')
                    exclude_sites = scrape_opts.get('exclude_sites')
                except json.JSONDecodeError:
                    pass

            # Execute search
            logger.info(f"Performing web search using BochaAI, query: {self.tool.query}")
            result = client.search(
                query=self.tool.query,
                count=self.tool.limit,
                freshness=freshness,
                summary=include_summary,
                include=include_sites,
                exclude=exclude_sites
            )

            if not result.success:
                return ToolResult(
                    success=False,
                    message=f"BochaAI search failed: {result.error}",
                    content=[]
                )

            # Format search results
            search_results = []

            # Process web results
            for webpage in result.webpages:
                result_item = {
                    "type": "web",
                    "title": webpage.name,
                    "url": webpage.url,
                    "description": webpage.snippet,
                    "provider": "bochaai"
                }

                if webpage.summary:
                    result_item["summary"] = webpage.summary
                if webpage.date_published:
                    result_item["date"] = webpage.date_published
                if webpage.site_name:
                    result_item["site_name"] = webpage.site_name
                if webpage.site_icon:
                    result_item["site_icon"] = webpage.site_icon

                search_results.append(result_item)

            # Process image results (if needed)
            if self.tool.sources and "images" in self.tool.sources:
                for image in result.images:
                    image_item = {
                        "type": "image",
                        "url": image.content_url,
                        "thumbnail_url": image.thumbnail_url,
                        "host_page_url": image.host_page_url,
                        "width": image.width,
                        "height": image.height,
                        "provider": "bochaai"
                    }
                    if image.name:
                        image_item["title"] = image.name
                    search_results.append(image_item)

            return ToolResult(
                success=True,
                message=f"Successfully found {len(search_results)} results (using BochaAI)",
                content=search_results
            )

        except Exception as e:
            logger.error(f"BochaAI search failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"BochaAI search failed: {str(e)}",
                content=traceback.format_exc()
            )

    def _search_with_metaso(self) -> ToolResult:
        """Search using Metaso"""
        try:
            # Check if Metaso API key is provided
            api_key = getattr(self.args, 'metaso_api_key', None) or os.getenv('METASO_API_KEY')
            if not api_key:
                return ToolResult(
                    success=False,
                    message="Metaso API key not provided, please set --metaso_api_key parameter or METASO_API_KEY environment variable",
                    content=[]
                )

            # Initialize Metaso client
            client = MetasoClient(api_key=api_key)

            # Prepare search parameters
            scope = "webpage"  # Default search web pages
            if self.tool.sources:
                # Map sources to Metaso's scope
                sources_list = [s.strip().lower() for s in self.tool.sources.split(',')]
                if "news" in sources_list:
                    scope = "news"
                # Metaso does not support images search yet, keep default webpage

            # Parse scrape_options to get additional parameters
            include_summary = False
            include_raw_content = False
            if self.tool.scrape_options:
                try:
                    scrape_opts = json.loads(self.tool.scrape_options)
                    include_summary = scrape_opts.get('include_summary', False)
                    include_raw_content = scrape_opts.get('include_raw_content', False)
                except json.JSONDecodeError:
                    pass

            # Execute search
            logger.info(f"Performing web search using Metaso, query: {self.tool.query}")
            result = client.search(
                query=self.tool.query,
                scope=scope,
                size=self.tool.limit,
                include_summary=include_summary,
                include_raw_content=include_raw_content
            )

            if not result.success:
                return ToolResult(
                    success=False,
                    message=f"Metaso search failed: {result.error}",
                    content=[]
                )

            # Format search results
            search_results = []
            for webpage in result.webpages:
                result_item = {
                    "type": "web",
                    "title": webpage.title,
                    "url": webpage.link,
                    "description": webpage.snippet,
                    "position": webpage.position,
                    "score": webpage.score,
                    "provider": "metaso"
                }

                if webpage.date:
                    result_item["date"] = webpage.date
                if webpage.authors:
                    result_item["authors"] = webpage.authors

                search_results.append(result_item)

            return ToolResult(
                success=True,
                message=f"Successfully found {len(search_results)} results (using Metaso)",
                content=search_results
            )

        except Exception as e:
            logger.error(f"Metaso search failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Metaso search failed: {str(e)}",
                content=traceback.format_exc()
            )

    def _search_with_firecrawl(self) -> ToolResult:
        """Search using Firecrawl"""
        try:
            # Check if Firecrawl API key is provided
            api_key = getattr(self.args, 'firecrawl_api_key', None) or os.getenv('FIRECRAWL_API_KEY')
            if not api_key:
                return ToolResult(
                    success=False,
                    message="Firecrawl API key not provided, please set --firecrawl_api_key parameter or FIRECRAWL_API_KEY environment variable",
                    content=[]
                )

            # Import Firecrawl SDK
            try:
                from firecrawl import Firecrawl
            except ImportError:
                return ToolResult(
                    success=False,
                    message="Firecrawl SDK not installed, please run: pip install firecrawl-py",
                    content=[]
                )

            # Initialize Firecrawl client
            firecrawl = Firecrawl(api_key=api_key)

            # Prepare search parameters
            search_params = {
                "query": self.tool.query,
                "limit": self.tool.limit
            }

            # Add optional parameters
            if self.tool.sources:
                # Parse comma-separated sources string
                sources_list = [s.strip() for s in self.tool.sources.split(',') if s.strip()]
                search_params["sources"] = sources_list
            if self.tool.scrape_options:
                # Parse JSON format scrape_options string
                try:
                    scrape_options_dict = json.loads(self.tool.scrape_options)
                    search_params["scrape_options"] = scrape_options_dict
                except json.JSONDecodeError as e:
                    logger.warning(f"scrape_options JSON parsing failed: {e}, ignoring this parameter")
            if self.tool.location:
                search_params["location"] = self.tool.location
            if self.tool.tbs:
                search_params["tbs"] = self.tool.tbs

            # Execute search
            logger.info(f"Starting web search, query: {self.tool.query}")
            results = firecrawl.search(**search_params)

            # Check result type and success status
            if not results:
                return ToolResult(
                    success=False,
                    message="No results returned",
                    content=[]
                )

            # New version firecrawl returns SearchData object with different structure
            if hasattr(results, 'success') and not results.success:
                error_msg = getattr(results, 'error', 'Unknown error')
                return ToolResult(
                    success=False,
                    message=f"Search failed: {error_msg}",
                    content=[]
                )

            # Format search results
            search_results = []
            # New version firecrawl returned data might be attribute instead of dict key
            if hasattr(results, 'data'):
                data = results.data
            else:
                data = results.get('data', {}) if hasattr(results, 'get') else {}

            # If data is empty, log information for debugging
            if not data or (isinstance(data, dict) and not data):
                logger.info("Search returned empty data, possibly due to API quota limit or service status issues")

            # Process web results - new version might be directly in data, not in data.web
            web_results = []
            if hasattr(data, 'web'):
                web_results = data.web
            elif isinstance(data, dict) and 'web' in data:
                web_results = data['web']
            elif isinstance(data, list):
                # Might directly return result list
                web_results = data

            if web_results:
                for item in web_results:
                    # Handle possible object or dictionary format
                    title = getattr(item, 'title', None) or (item.get('title', '') if hasattr(item, 'get') else '')
                    url = getattr(item, 'url', None) or (item.get('url', '') if hasattr(item, 'get') else '')
                    description = getattr(item, 'description', None) or (item.get('description', '') if hasattr(item, 'get') else '')
                    position = getattr(item, 'position', None) or (item.get('position', 0) if hasattr(item, 'get') else 0)

                    result_item = {
                        "type": "web",
                        "title": title,
                        "url": url,
                        "description": description,
                        "position": position
                    }

                    # If there is scraped content, add to results
                    markdown = getattr(item, 'markdown', None) or (item.get('markdown') if hasattr(item, 'get') else None)
                    if markdown:
                        result_item['content'] = markdown

                    links = getattr(item, 'links', None) or (item.get('links') if hasattr(item, 'get') else None)
                    if links:
                        result_item['links'] = links

                    metadata = getattr(item, 'metadata', None) or (item.get('metadata') if hasattr(item, 'get') else None)
                    if metadata:
                        result_item['metadata'] = metadata

                    search_results.append(result_item)

            # Process news results
            if 'news' in data:
                for item in data['news']:
                    result_item = {
                        "type": "news",
                        "title": item.get('title', ''),
                        "url": item.get('url', ''),
                        "snippet": item.get('snippet', ''),
                        "date": item.get('date', ''),
                        "position": item.get('position', 0)
                    }
                    search_results.append(result_item)

            # Process image results
            if 'images' in data:
                for item in data['images']:
                    result_item = {
                        "type": "image",
                        "title": item.get('title', ''),
                        "imageUrl": item.get('imageUrl', ''),
                        "url": item.get('url', ''),
                        "imageWidth": item.get('imageWidth', 0),
                        "imageHeight": item.get('imageHeight', 0),
                        "position": item.get('position', 0)
                    }
                    search_results.append(result_item)

            return ToolResult(
                success=True,
                message=f"Successfully found {len(search_results)} results (using Firecrawl)",
                content=search_results
            )

        except Exception as e:
            logger.error(f"Firecrawl search failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Firecrawl search failed: {str(e)}",
                content=traceback.format_exc()
            )

    def resolve(self) -> ToolResult:
        """Implement web search tool resolution logic"""
        try:
            # Determine which provider to use
            arg_bochaai_key = self.args.bochaai_api_key
            bochaai_key = arg_bochaai_key

            arg_metaso_key = self.args.metaso_api_key
            metaso_key = arg_metaso_key

            arg_firecrawl_key = self.args.firecrawl_api_key
            firecrawl_key = arg_firecrawl_key

            # Check if any API key is configured
            if not any([bochaai_key, metaso_key, firecrawl_key]):
                # No API key configured, guide to use search engines and curl
                search_query = self.tool.query.replace(' ', '+')

                # Build search suggestions
                search_suggestions = []
                search_suggestions.append(f"# Use search engines for web search")
                search_suggestions.append(f"# 1. Google Search:")
                search_suggestions.append(f"#    Visit: https://www.google.com/search?q={search_query}")
                search_suggestions.append(f"")
                search_suggestions.append(f"# 2. DuckDuckGo Search:")
                search_suggestions.append(f"#    Visit: https://duckduckgo.com/?q={search_query}")
                search_suggestions.append(f"")
                search_suggestions.append(f"# 3. Use curl to get search result pages (need to handle anti-crawling mechanisms):")
                search_suggestions.append(f"curl -s -L -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' 'https://www.google.com/search?q={search_query}'")
                search_suggestions.append(f"")
                search_suggestions.append(f"# 4. If you know specific websites, search them directly:")
                search_suggestions.append(f"curl -s -L 'https://example.com/search?q={search_query}'")

                if self.tool.sources:
                    search_suggestions.append(f"")
                    search_suggestions.append(f"# Specified search type: {self.tool.sources}")
                    if "news" in self.tool.sources:
                        search_suggestions.append(f"# For news search, visit: https://news.google.com/search?q={search_query}")
                    if "images" in self.tool.sources:
                        search_suggestions.append(f"# For image search, visit: https://www.google.com/search?tbm=isch&q={search_query}")

                if self.tool.location:
                    search_suggestions.append(f"")
                    search_suggestions.append(f"# Geographic location restriction: {self.tool.location}")
                    search_suggestions.append(f"# You can add location keywords to search")

                if self.tool.tbs:
                    search_suggestions.append(f"")
                    search_suggestions.append(f"# Time filter: {self.tool.tbs}")
                    search_suggestions.append(f"# Google search can use time filter options in the tools menu")

                suggestion_text = "\n".join(search_suggestions)

                return ToolResult(
                    success=False,
                    message=f"No web search API key configured (BochaAI, Metaso, Firecrawl).",
                    content={}
                )

            # Determine provider priority: BochaAI > Metaso > Firecrawl
            provider = None
            selected_key_name = None
            selected_key_value = None
            if bochaai_key:
                provider = "bochaai"
                selected_key_name = "bochaai_api_key" if arg_bochaai_key else "BOCHAAI_API_KEY"
                selected_key_value = bochaai_key
            elif metaso_key:
                provider = "metaso"
                selected_key_name = "metaso_api_key" if arg_metaso_key else "METASO_API_KEY"
                selected_key_value = metaso_key
            elif firecrawl_key:
                provider = "firecrawl"
                selected_key_name = "firecrawl_api_key" if arg_firecrawl_key else "FIRECRAWL_API_KEY"
                selected_key_value = firecrawl_key

            key_prefix = (selected_key_value[:10] if selected_key_value else "")
            logger.info(f"Using search provider: {provider}, key_name: {selected_key_name}, key_prefix: {key_prefix}")

            if provider == "bochaai":
                return self._search_with_bochaai()
            elif provider == "metaso":
                return self._search_with_metaso()
            elif provider == "firecrawl":
                return self._search_with_firecrawl()

            # This situation should not happen theoretically
            return ToolResult(
                success=False,
                message="Internal error: Unable to determine search provider",
                content=[]
            )

        except Exception as e:
            logger.error(f"Web search tool execution failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Web search tool execution failed: {str(e)}",
                content=traceback.format_exc()
            )


class WebSearchToolDescGenerator:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    @byzerllm.prompt()
    def web_search_description(self) -> Dict:
        """
        Description: Request to perform web search using Firecrawl, Metaso or BochaAI API. Use this when you need to search for current web content, news, or images to gather information for completing your task. This tool supports multiple search sources and can optionally scrape the full content of search result pages. You can use web_crawl to fetch the url of the search result pages.
        Parameters:
        - query: (required) The search query string to search for
        - limit: (optional) Maximum number of results to return (default: 5)
        - sources: (optional) Comma-separated search source types, e.g., "web", "news", "images", "web,news"
        - scrape_options: (optional) Additional scraping options as JSON string, e.g., '{"formats": ["markdown"], "include_summary": true, "include_sites": "example.com", "exclude_sites": "bad.com"}'
        - location: (optional) Geographic location to focus the search (Firecrawl only)
        - tbs: (optional) Time-based search parameters for filtering results (Firecrawl/BochaAI)
        Usage:
        <web_search>
        <query>Your search query here</query>
        <limit>5</limit>
        <sources>web</sources>
        </web_search>
        """
        return self.params


def register_web_search_tool():
    """Register web search tool"""
    desc_gen = WebSearchToolDescGenerator({})

    # 准备工具描述
    description = ToolDescription(
        description=desc_gen.web_search_description.prompt()
    )

    # 准备工具示例
    example = ToolExample(
        title="Web search tool usage example",
        body="""<web_search>
<query>Python RAG system implementation</query>
<limit>3</limit>
<sources>web</sources>
</web_search>"""
    )

    # 注册工具
    ToolRegistry.register_tool(
        tool_tag="web_search",  # XML标签名
        tool_cls=WebSearchTool,  # 工具类
        resolver_cls=WebSearchToolResolver,  # 解析器类
        description=description,  # 工具描述
        example=example,  # 工具示例
        use_guideline="Use this tool to search for web content across different sources (web pages, news, images). It can optionally scrape complete content from search results. Ideal for gathering current information from the internet to help complete tasks that require up-to-date data."  # 使用指南
    )
