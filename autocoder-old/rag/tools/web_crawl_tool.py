"""
WebCrawlTool Module

This module implements WebCrawlTool and WebCrawlToolResolver classes for providing
web crawling functionality based on Firecrawl, Metaso in the BaseAgent framework.
Supports concurrent crawling with multiple API keys using thread pools.
"""

import os
import traceback
import time
import json
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import byzerllm
from loguru import logger

from autocoder.agent.base_agentic.types import BaseTool, ToolResult
from autocoder.agent.base_agentic.tool_registry import ToolRegistry
from autocoder.agent.base_agentic.tools.base_tool_resolver import BaseToolResolver
from autocoder.agent.base_agentic.types import ToolDescription, ToolExample


class WebCrawlTool(BaseTool):
    """Web crawling tool using Firecrawl, Metaso for web crawling"""
    url: str  # URL to crawl
    limit: Optional[int] = 10  # Page crawling limit
    scrape_options: Optional[str] = None  # Scraping options in JSON string format
    exclude_paths: Optional[str] = None  # Excluded paths, comma-separated
    include_paths: Optional[str] = None  # Included paths, comma-separated
    max_depth: Optional[int] = None  # Maximum crawling depth
    allow_subdomains: Optional[str] = "false"  # Whether to allow subdomains, true/false
    crawl_entire_domain: Optional[str] = "false"  # Whether to crawl entire domain, true/false    


class WebCrawlToolResolver(BaseToolResolver):
    """Web crawling tool resolver implementing concurrent crawling logic"""
    
    def __init__(self, agent, tool, args):
        super().__init__(agent, tool, args)
        self.tool: WebCrawlTool = tool
        self._results_lock = Lock()
        self._all_results = []
    
    def _get_available_providers(self) -> List[Dict[str, Any]]:
        """Get all available provider configurations"""
        providers = []                
        # Check Metaso keys
        metaso_keys = []
        if self.args.metaso_api_key:
            if ',' in self.args.metaso_api_key:
                metaso_keys = [key.strip() for key in self.args.metaso_api_key.split(',') if key.strip()]
            else:
                metaso_keys = [self.args.metaso_api_key]
        
        for key in metaso_keys:
            providers.append({
                'type': 'metaso',
                'api_key': key,
                'priority': 2
            })
        
        # Check Firecrawl keys
        firecrawl_keys = []
        if self.args.firecrawl_api_key:
            if ',' in self.args.firecrawl_api_key:
                firecrawl_keys = [key.strip() for key in self.args.firecrawl_api_key.split(',') if key.strip()]
            else:
                firecrawl_keys = [self.args.firecrawl_api_key]
        
        for key in firecrawl_keys:
            providers.append({
                'type': 'firecrawl',
                'api_key': key,
                'priority': 3
            })
        
        # Sort by priority
        providers.sort(key=lambda x: x['priority'])
        return providers        
    
    def _crawl_with_metaso(self, api_key: str) -> ToolResult:
        """Use Metaso for crawling (single page reading or multi-page crawling)"""
        logger.info(f"🔍 Starting Metaso crawl (key: ...{api_key[-4:]}): {self.tool.url}")
        try:
            # Dynamically import to avoid dependency issues
            try:
                from autocoder.rag.tools.metaso_sdk import MetasoClient
            except ImportError:
                return ToolResult(
                    success=False,
                    message="Metaso SDK not installed, please check dependencies",
                    content=[]
                )
            
            # Initialize Metaso client
            client = MetasoClient(api_key=api_key)
            
            # Prepare crawling parameters
            exclude_paths_list = None
            if self.tool.exclude_paths:
                exclude_paths_list = [p.strip() for p in self.tool.exclude_paths.split(',') if p.strip()]
            
            include_paths_list = None
            if self.tool.include_paths:
                include_paths_list = [p.strip() for p in self.tool.include_paths.split(',') if p.strip()]
            
            allow_subdomains = self.tool.allow_subdomains.lower() == "true"
            
            # If only crawling one page (limit=1), use read method directly
            if self.tool.limit == 1:
                logger.info(f"Using Metaso to read single page: {self.tool.url}")
                content = client.read(self.tool.url, format="text/plain")
                
                if content.startswith("Error:"):
                    return ToolResult(
                        success=False,
                        message=f"Metaso reading failed: {content}",
                        content=[]
                    )
                
                result_item = {
                    "url": self.tool.url,
                    "title": "",
                    "content": content,
                    "markdown": content,
                    "links": [],
                    "metadata": {
                        "source": "metaso",
                        "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
                    }
                }
                
                return ToolResult(
                    success=True,
                    message=f"Successfully read 1 page (using Metaso)",
                    content=[result_item]
                )
            
            # Multi-page crawling
            logger.info(f"Using Metaso to start web crawling, URL: {self.tool.url}")
            crawl_results = client.crawl(
                url=self.tool.url,
                limit=self.tool.limit,
                max_depth=self.tool.max_depth,
                exclude_paths=exclude_paths_list,
                include_paths=include_paths_list,
                allow_subdomains=allow_subdomains
            )
            
            if not crawl_results:
                return ToolResult(
                    success=False,
                    message="Metaso crawling returned no results",
                    content=[]
                )
            
            # Add API key identifier to each result
            for result in crawl_results:
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['api_key_suffix'] = api_key[-4:] if len(api_key) > 4 else "****"
            
            return ToolResult(
                success=True,
                message=f"Successfully crawled {len(crawl_results)} pages (using Metaso)",
                content=crawl_results
            )
            
        except Exception as e:
            logger.error(f"❌ Metaso crawling failed (key: ...{api_key[-4:]}): {str(e)}")
            return ToolResult(
                success=False,
                message=f"Metaso crawling failed (key: ...{api_key[-4:]}): {str(e)}",
                content=[]
            )
    
    def _crawl_with_firecrawl(self, api_key: str) -> ToolResult:
        """Use Firecrawl for crawling with simplified API"""
        logger.info(f"🔥 Starting Firecrawl crawl (key: ...{api_key[-4:]}): {self.tool.url}")
        try:
            # Import Firecrawl SDK - try multiple import options
            try:
                from firecrawl import FirecrawlApp
                use_app_class = True
            except ImportError:
                try:
                    from firecrawl import Firecrawl
                    use_app_class = False
                except ImportError:
                    return ToolResult(
                        success=False,
                        message="Firecrawl SDK not installed, please run: pip install firecrawl-py",
                        content=[]
                    )
            
            # Initialize Firecrawl client using the available class
            if use_app_class:
                firecrawl = FirecrawlApp(api_key=api_key)
                logger.info("Using FirecrawlApp class")
            else:
                firecrawl = Firecrawl(api_key=api_key)
                logger.info("Using Firecrawl class")
            
            # For single page (limit=1), use simple scrape method
            if self.tool.limit == 1:
                logger.info("Using simple scrape for single page")
                
                # Both FirecrawlApp and Firecrawl use the same 'scrape' method
                scrape_result = firecrawl.scrape(self.tool.url, formats=['markdown'])
                
                # Process single page result
                if not scrape_result:
                    return ToolResult(
                        success=False,
                        message="Firecrawl scrape returned empty result",
                        content=[]
                    )
                
                # Convert to consistent format - scrape_result is a Document object
                title = ''
                if scrape_result.metadata and hasattr(scrape_result.metadata, 'title'):
                    title = scrape_result.metadata.title or ''
                
                result_item = {
                    "url": self.tool.url,
                    "title": title,
                    "content": scrape_result.markdown or '',
                    "markdown": scrape_result.markdown or '',
                    "links": scrape_result.links or [],
                    "metadata": {
                        "source": "firecrawl",
                        "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
                    }
                }
                
                # Add original metadata if available
                if scrape_result.metadata:
                    if hasattr(scrape_result.metadata, 'dict'):
                        result_item['metadata'].update(scrape_result.metadata.dict())
                    elif hasattr(scrape_result.metadata, '__dict__'):
                        result_item['metadata'].update(scrape_result.metadata.__dict__)
                
                return ToolResult(
                    success=True,
                    message=f"Successfully scraped 1 page using Firecrawl (key: ...{api_key[-4:]})",
                    content=[result_item]
                )
            
            # Multi-page crawling using the unified 'crawl' method
            logger.info(f"Using multi-page crawling for {self.tool.limit} pages")
            
            try:
                # Prepare crawl parameters
                crawl_options = {}
                
                if self.tool.max_depth is not None:
                    crawl_options['max_discovery_depth'] = self.tool.max_depth
                if self.tool.limit is not None:
                    crawl_options['limit'] = self.tool.limit
                if self.tool.exclude_paths:
                    crawl_options['exclude_paths'] = [p.strip() for p in self.tool.exclude_paths.split(',') if p.strip()]
                if self.tool.include_paths:
                    crawl_options['include_paths'] = [p.strip() for p in self.tool.include_paths.split(',') if p.strip()]
                if self.tool.allow_subdomains is not None:
                    crawl_options['allow_subdomains'] = self.tool.allow_subdomains.lower() == "true"
                if self.tool.crawl_entire_domain is not None:
                    crawl_options['crawl_entire_domain'] = self.tool.crawl_entire_domain.lower() == "true"
                
                logger.info(f"Starting crawl with options: {crawl_options}")
                
                # Both FirecrawlApp and Firecrawl use the same 'crawl' method
                crawl_result = firecrawl.crawl(self.tool.url, **crawl_options)
                
                # Process crawl results - crawl_result is a CrawlJob object
                crawl_results = []
                
                # CrawlJob.data contains List[Document]
                data = crawl_result.data or []
                logger.info(f"Processing {len(data)} crawled documents")
                
                for doc in data:
                    # doc is a Document object
                    url = ''
                    title = ''
                    if doc.metadata:
                        if hasattr(doc.metadata, 'source_url'):
                            url = doc.metadata.source_url or ''
                        if hasattr(doc.metadata, 'title'):
                            title = doc.metadata.title or ''
                    
                    result_item = {
                        "url": url,
                        "title": title,
                        "content": doc.markdown or '',
                        "markdown": doc.markdown or '',
                        "links": doc.links or [],
                        "metadata": {
                            "source": "firecrawl",
                            "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
                        }
                    }
                    
                    # Add original metadata if available
                    if doc.metadata:
                        try:
                            if hasattr(doc.metadata, 'dict'):
                                result_item['metadata'].update(doc.metadata.dict())
                            elif hasattr(doc.metadata, '__dict__'):
                                result_item['metadata'].update(doc.metadata.__dict__)
                        except Exception as e:
                            logger.warning(f"Failed to extract metadata: {e}")
                    
                    crawl_results.append(result_item)
                
                return ToolResult(
                    success=True,
                    message=f"Successfully crawled {len(crawl_results)} pages using Firecrawl (key: ...{api_key[-4:]})",
                    content=crawl_results
                )
                
            except Exception as crawl_error:
                logger.error(f"Multi-page crawling failed: {crawl_error}")
                # Fallback to single page scrape
                logger.info("Attempting fallback to single page scrape")
                try:
                    scrape_result = firecrawl.scrape(self.tool.url, formats=['markdown'])
                    
                    title = ''
                    if scrape_result.metadata and hasattr(scrape_result.metadata, 'title'):
                        title = scrape_result.metadata.title or ''
                    
                    result_item = {
                        "url": self.tool.url,
                        "title": title,
                        "content": scrape_result.markdown or '',
                        "markdown": scrape_result.markdown or '',
                        "links": scrape_result.links or [],
                        "metadata": {
                            "source": "firecrawl",
                            "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
                        }
                    }
                    
                    # Add original metadata if available
                    if scrape_result.metadata:
                        if hasattr(scrape_result.metadata, 'dict'):
                            result_item['metadata'].update(scrape_result.metadata.dict())
                        elif hasattr(scrape_result.metadata, '__dict__'):
                            result_item['metadata'].update(scrape_result.metadata.__dict__)
                    
                    return ToolResult(
                        success=True,
                        message=f"Fallback successful: scraped 1 page using Firecrawl (key: ...{api_key[-4:]}) - multi-page failed: {str(crawl_error)}",
                        content=[result_item]
                    )
                except Exception as fallback_error:
                    return ToolResult(
                        success=False,
                        message=f"Both crawling and fallback failed. Crawl error: {str(crawl_error)}, Fallback error: {str(fallback_error)}",
                        content=[]
                    )
            
        except Exception as e:
            logger.error(f"❌ Firecrawl crawling failed (key: ...{api_key[-4:]}): {str(e)}")
            return ToolResult(
                success=False,
                message=f"Firecrawl crawling failed (key: ...{api_key[-4:]}): {str(e)}",
                content=[]
            )
    
    def _crawl_with_provider(self, provider: Dict[str, Any]) -> ToolResult:
        """Use specified provider for crawling"""
        provider_type = provider['type']
        api_key = provider['api_key']
                
        if provider_type == 'metaso':
            return self._crawl_with_metaso(api_key)
        elif provider_type == 'firecrawl':
            return self._crawl_with_firecrawl(api_key)
        else:
            return ToolResult(
                success=False,
                message=f"Unsupported provider type: {provider_type}",
                content=[]
            )
    
    def _merge_results(self, results: List[ToolResult]) -> ToolResult:
        """Merge multiple crawling results"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        logger.info(f"📄 Merging results: {len(successful_results)} successful, {len(failed_results)} failed")
        
        if not successful_results:
            # All requests failed
            error_messages = [r.message for r in failed_results]
            return ToolResult(
                success=False,
                message=f"All crawling requests failed: {'; '.join(error_messages)}",
                content=[]
            )
        
        # Merge successful results
        all_content = []
        total_pages = 0
        providers_used = set()
        
        for result in successful_results:
            if result.content:
                all_content.extend(result.content)
                total_pages += len(result.content)
                # Extract provider information from results
                for item in result.content:
                    if 'metadata' in item and 'source' in item['metadata']:
                        providers_used.add(item['metadata']['source'])
                    elif 'metadata' in item and 'api_key_suffix' in item['metadata']:
                        # Infer provider from API key suffix                        
                        if 'metaso' in result.message.lower():
                            providers_used.add('metaso')
                        elif 'firecrawl' in result.message.lower():
                            providers_used.add('firecrawl')
        
        # Deduplicate (based on URL + source combination)
        # Keep results from different sources even if they have the same URL
        seen_url_source_pairs = set()
        unique_content = []
        for item in all_content:
            url = item.get('url', '')
            source = item.get('metadata', {}).get('source', 'unknown')
            url_source_key = (url, source)
            
            if url and url_source_key not in seen_url_source_pairs:
                seen_url_source_pairs.add(url_source_key)
                unique_content.append(item)
            elif not url:  # If no URL, also keep it
                unique_content.append(item)
        
        # If we have multiple results for the same URL from different sources, log it
        url_count = {}
        for item in unique_content:
            url = item.get('url', '')
            if url:
                url_count[url] = url_count.get(url, 0) + 1
        
        multi_source_urls = [url for url, count in url_count.items() if count > 1]
        if multi_source_urls:
            logger.info(f"📊 Found {len(multi_source_urls)} URLs crawled by multiple sources: {multi_source_urls[:3]}{'...' if len(multi_source_urls) > 3 else ''}")
        
        providers_str = ', '.join(sorted(providers_used)) if providers_used else 'unknown'
        success_count = len(successful_results)
        fail_count = len(failed_results)
        
        message = f"Successfully crawled {len(unique_content)} pages (using {providers_str})"
        if fail_count > 0:
            # 收集失败原因的详细信息
            failed_details = []
            for failed_result in failed_results:
                # 尝试从错误消息中提取 provider 信息
                if 'metaso' in failed_result.message.lower():
                    failed_details.append(f"Metaso: {failed_result.message}")
                elif 'firecrawl' in failed_result.message.lower():
                    failed_details.append(f"Firecrawl: {failed_result.message}")
                else:
                    failed_details.append(f"Unknown: {failed_result.message}")
            
            message += f", {fail_count} API keys failed"
            if failed_details:
                logger.warning(f"❌ 失败的 API 详情: {'; '.join(failed_details)}")
                # 在消息中也包含失败详情（但保持简洁）
                if len(failed_details) == 1:
                    message += f" ({failed_details[0]})"
        
        return ToolResult(
            success=True,
            message=message,
            content=unique_content
        )

    def resolve(self) -> ToolResult:
        """Implement web crawling tool resolution logic, supporting multi-key concurrency"""
        try:
            # Get all available providers
            providers = self._get_available_providers()
            
            if not providers:
                # No API key configured, guide to use curl
                curl_command = f"curl -s -L '{self.tool.url}'"
                
                # Add more curl options based on parameters
                curl_suggestions = []
                curl_suggestions.append(f"curl -s -L '{self.tool.url}'  # Basic web content retrieval")
                curl_suggestions.append(f"curl -s -L -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' '{self.tool.url}'  # Add user agent")
                curl_suggestions.append(f"curl -s -L --max-time 30 '{self.tool.url}'  # Set timeout")
                curl_suggestions.append(f"curl -s -L -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' '{self.tool.url}'  # Set Accept header")
                
                if self.tool.limit and self.tool.limit == 1:
                    curl_suggestions.append(f"# For single page scraping, you can use curl directly")
                else:
                    curl_suggestions.append(f"# For multi-page crawling, recommend using wget recursive download:")
                    max_depth = self.tool.max_depth or 2
                    wget_cmd = f"wget --recursive --level={max_depth} --no-parent --reject='*.css,*.js,*.png,*.jpg,*.gif,*.pdf' --user-agent='Mozilla/5.0' '{self.tool.url}'"
                    curl_suggestions.append(wget_cmd)
                
                if self.tool.exclude_paths:
                    curl_suggestions.append(f"# Exclude paths: {self.tool.exclude_paths}")
                    curl_suggestions.append(f"# Can use wget's --exclude-directories option")
                
                if self.tool.include_paths:
                    curl_suggestions.append(f"# Include paths: {self.tool.include_paths}")
                    curl_suggestions.append(f"# Can use wget's --include-directories option")
                
                suggestion_text = "\n".join(curl_suggestions)
                
                return ToolResult(
                    success=False,
                    message=f"No web crawling API key configured (Metaso, Firecrawl). Recommend using curl or wget commands to get web content:\n\n{suggestion_text}\n\nConfiguration instructions:\n- Metaso: Set --metaso_api_key parameter\n- Firecrawl: Set --firecrawl_api_key parameter",
                    content={
                        "suggested_commands": curl_suggestions,
                        "target_url": self.tool.url,
                        "curl_basic": curl_command,
                        "wget_recursive": f"wget --recursive --level={self.tool.max_depth or 2} --no-parent --reject='*.css,*.js,*.png,*.jpg,*.gif,*.pdf' --user-agent='Mozilla/5.0' '{self.tool.url}'"                        
                    }
                )
            
            logger.info(f"🚀 Found {len(providers)} available API configurations, starting concurrent crawling")
            for i, provider in enumerate(providers, 1):
                logger.info(f"  {i}. {provider['type'].upper()} API (key: ...{provider['api_key'][-4:]})")
            
            # If only one provider, call directly
            if len(providers) == 1:
                logger.info(f"📝 Using single provider: {providers[0]['type'].upper()}")
                return self._crawl_with_provider(providers[0])
            
            # Use thread pool for concurrent execution with multiple providers
            logger.info(f"🏁 Starting concurrent execution with {len(providers)} providers")
            results = []
            max_workers = min(len(providers), 5)  # Limit maximum concurrency
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_provider = {
                    executor.submit(self._crawl_with_provider, provider): provider 
                    for provider in providers
                }
                
                # Collect results
                for future in as_completed(future_to_provider):
                    provider = future_to_provider[future]
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout
                        results.append(result)
                        if result.success:
                            logger.info(f"✅ Provider {provider['type']} (key: ...{provider['api_key'][-4:]}) completed successfully")
                        else:
                            logger.warning(f"❌ Provider {provider['type']} (key: ...{provider['api_key'][-4:]}) failed: {result.message}")
                    except Exception as e:
                        logger.error(f"❌ Provider {provider['type']} (key: ...{provider['api_key'][-4:]}) execution exception: {str(e)}")
                        results.append(ToolResult(
                            success=False,
                            message=f"Provider {provider['type']} execution exception: {str(e)}",
                            content=[]
                        ))
            
            # Merge results
            return self._merge_results(results)
                
        except Exception as e:
            logger.error(f"Web crawling tool execution failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Web crawling tool execution failed: {str(e)}",
                content=traceback.format_exc()
            )


class WebCrawlToolDescGenerator:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    @byzerllm.prompt()
    def web_crawl_description(self) -> Dict:
        """
        Description: Request to perform deep web crawling using Firecrawl, Metaso API to recursively crawl website sub-pages. Use this when you need to extract comprehensive content from multiple related pages on a website, such as documentation sites or knowledge bases.
        Parameters:
        - url: (required) The URL to start crawling from
        - limit: (optional) Maximum number of pages to crawl (default: 10)
        - scrape_options: (optional) Additional scraping options as JSON string, e.g., '{"formats": ["markdown", "links"]}'
        - exclude_paths: (optional) Comma-separated path patterns to exclude from crawling, e.g., "/api,/admin"
        - include_paths: (optional) Comma-separated path patterns to include in crawling, e.g., "/docs,/help"
        - max_depth: (optional) Maximum crawling depth from the starting URL
        - allow_subdomains: (optional) Whether to allow crawling subdomains, "true" or "false" (default: "false")
        - crawl_entire_domain: (optional) Whether to crawl the entire domain, "true" or "false" (default: "false") (Firecrawl only)        
        Usage:
        <web_crawl>
        <url>https://example.com</url>
        <limit>10</limit>
        <scrape_options>{"formats": ["markdown", "links"]}</scrape_options>        
        </web_crawl>
        """
        return self.params


def register_web_crawl_tool():
    """Register web crawl tool"""
    desc_gen = WebCrawlToolDescGenerator({})
    
    # Prepare tool description
    description = ToolDescription(
        description=desc_gen.web_crawl_description.prompt()
    )
    
    # Prepare tool example
    example = ToolExample(
        title="Web crawl tool usage example",
        body="""<web_crawl>
<url>https://docs.firecrawl.dev</url>
<limit>5</limit>
<scrape_options>{"formats": ["markdown", "links"]}</scrape_options>
<exclude_paths>/api,/admin</exclude_paths>
</web_crawl>"""
    )
    
    # Register tool
    ToolRegistry.register_tool(
        tool_tag="web_crawl",  # XML tag name
        tool_cls=WebCrawlTool,  # Tool class
        resolver_cls=WebCrawlToolResolver,  # Resolver class
        description=description,  # Tool description
        example=example,  # Tool example
        use_guideline="Use this tool for deep crawling of website content, recursively retrieving multiple pages from a site. Supports setting crawl depth, excluding paths, and other advanced options. Ideal for gathering comprehensive content from documentation sites, knowledge bases, or other structured websites."  # Usage guideline
    )
