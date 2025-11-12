
"""
WebSearchToolResolver Module

This module implements the WebSearchToolResolver class for providing 
web search functionality based on Firecrawl, Metaso, or BochaAI within 
the AgenticEdit framework. Supports concurrent search when multiple API 
keys are configured, using thread pools for concurrent processing.
"""

import os
import traceback
import json
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import WebSearchTool, ToolResult
from autocoder.common import AutoCoderArgs
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class WebSearchToolResolver(BaseToolResolver):
    """Web search tool resolver that implements concurrent search logic"""
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: WebSearchTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: WebSearchTool = tool
        self._results_lock = Lock()
        self._all_results = []
    
    def _get_available_providers(self) -> List[Dict[str, Any]]:
        """Get all available provider configurations"""
        providers = []
        
        # Check BochaAI keys
        bochaai_keys = []
        if hasattr(self.args, 'bochaai_api_key') and self.args.bochaai_api_key:
            if ',' in self.args.bochaai_api_key:
                bochaai_keys = [key.strip() for key in self.args.bochaai_api_key.split(',') if key.strip()]
            else:
                bochaai_keys = [self.args.bochaai_api_key]
        elif os.getenv('BOCHAAI_API_KEY'):
            env_keys = os.getenv('BOCHAAI_API_KEY')
            if ',' in env_keys:
                bochaai_keys = [key.strip() for key in env_keys.split(',') if key.strip()]
            else:
                bochaai_keys = [env_keys]
        
        for key in bochaai_keys:
            providers.append({
                'type': 'bochaai',
                'api_key': key,
                'priority': 1
            })
        
        # Check Metaso keys
        metaso_keys = []
        if hasattr(self.args, 'metaso_api_key') and self.args.metaso_api_key:
            if ',' in self.args.metaso_api_key:
                metaso_keys = [key.strip() for key in self.args.metaso_api_key.split(',') if key.strip()]
            else:
                metaso_keys = [self.args.metaso_api_key]
        elif os.getenv('METASO_API_KEY'):
            env_keys = os.getenv('METASO_API_KEY')
            if ',' in env_keys:
                metaso_keys = [key.strip() for key in env_keys.split(',') if key.strip()]
            else:
                metaso_keys = [env_keys]
        
        for key in metaso_keys:
            providers.append({
                'type': 'metaso',
                'api_key': key,
                'priority': 2
            })
        
        # Check Firecrawl keys
        firecrawl_keys = []
        if hasattr(self.args, 'firecrawl_api_key') and self.args.firecrawl_api_key:
            if ',' in self.args.firecrawl_api_key:
                firecrawl_keys = [key.strip() for key in self.args.firecrawl_api_key.split(',') if key.strip()]
            else:
                firecrawl_keys = [self.args.firecrawl_api_key]
        elif os.getenv('FIRECRAWL_API_KEY'):
            env_keys = os.getenv('FIRECRAWL_API_KEY')
            if ',' in env_keys:
                firecrawl_keys = [key.strip() for key in env_keys.split(',') if key.strip()]
            else:
                firecrawl_keys = [env_keys]
        
        for key in firecrawl_keys:
            providers.append({
                'type': 'firecrawl',
                'api_key': key,
                'priority': 3
            })
        
        # Sort by priority
        providers.sort(key=lambda x: x['priority'])
        return providers
        
    def _search_with_bochaai(self, api_key: str) -> ToolResult:
        """Search using BochaAI"""
        try:
            # Dynamic import to avoid dependency issues
            try:
                from autocoder.rag.tools.bochaai_sdk import BochaAIClient
            except ImportError:
                return ToolResult(
                    success=False,
                    message="BochaAI SDK not installed, please check dependencies",
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
                    "provider": "bochaai",
                    "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
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
                        "provider": "bochaai",
                        "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
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
                content=[]
            )
    
    def _search_with_metaso(self, api_key: str) -> ToolResult:
        """Search using Metaso"""
        try:
            # Dynamic import to avoid dependency issues
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
                    "provider": "metaso",
                    "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
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
                content=[]
            )
    
    def _search_with_firecrawl(self, api_key: str) -> ToolResult:
        """Search using Firecrawl"""
        try:
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
                        "position": position,
                        "provider": "firecrawl",
                        "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
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
            if isinstance(data, dict) and 'news' in data:
                for item in data['news']:
                    result_item = {
                        "type": "news",
                        "title": item.get('title', ''),
                        "url": item.get('url', ''),
                        "snippet": item.get('snippet', ''),
                        "date": item.get('date', ''),
                        "position": item.get('position', 0),
                        "provider": "firecrawl",
                        "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
                    }
                    search_results.append(result_item)
            
            # Process image results
            if isinstance(data, dict) and 'images' in data:
                for item in data['images']:
                    result_item = {
                        "type": "image",
                        "title": item.get('title', ''),
                        "imageUrl": item.get('imageUrl', ''),
                        "url": item.get('url', ''),
                        "imageWidth": item.get('imageWidth', 0),
                        "imageHeight": item.get('imageHeight', 0),
                        "position": item.get('position', 0),
                        "provider": "firecrawl",
                        "api_key_suffix": api_key[-4:] if len(api_key) > 4 else "****"
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
                content=[]
            )
    
    def _search_with_provider(self, provider: Dict[str, Any]) -> ToolResult:
        """Search using specified provider"""
        provider_type = provider['type']
        api_key = provider['api_key']
        
        if provider_type == 'bochaai':
            return self._search_with_bochaai(api_key)
        elif provider_type == 'metaso':
            return self._search_with_metaso(api_key)
        elif provider_type == 'firecrawl':
            return self._search_with_firecrawl(api_key)
        else:
            return ToolResult(
                success=False,
                message=f"Unsupported provider type: {provider_type}",
                content=[]
            )
    
    def _merge_results(self, results: List[ToolResult]) -> ToolResult:
        """Merge multiple search results"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        if not successful_results:
            # All requests failed
            error_messages = [r.message for r in failed_results]
            return ToolResult(
                success=False,
                message=f"All search requests failed: {'; '.join(error_messages)}",
                content=[]
            )
        
        # Merge successful results
        all_content = []
        total_results = 0
        providers_used = set()
        
        for result in successful_results:
            if result.content:
                all_content.extend(result.content)
                total_results += len(result.content)
                # 从结果中提取使用的提供商信息
                for item in result.content:
                    if 'provider' in item:
                        providers_used.add(item['provider'])
        
        # Remove duplicates (based on URL)
        seen_urls = set()
        unique_content = []
        for item in all_content:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_content.append(item)
            elif not url:  # If no URL, also keep
                unique_content.append(item)
        
        # Sort by position (if available)
        unique_content.sort(key=lambda x: x.get('position', 999))
        
        providers_str = ', '.join(sorted(providers_used)) if providers_used else 'unknown'        
        fail_count = len(failed_results)
        
        message = f"Successfully found {len(unique_content)} results (using {providers_str})"
        if fail_count > 0:
            message += f", {fail_count} API keys failed"
        
        return ToolResult(
            success=True,
            message=message,
            content=unique_content
        )
    
    def resolve(self) -> ToolResult:
        """Implement web search tool resolution logic with multi-key concurrency support"""
        try:
            # Get all available providers
            providers = self._get_available_providers()
            
            if not providers:                               
                return ToolResult(
                    success=False,
                    message=f"No web search API key configured (BochaAI, Metaso, Firecrawl).",
                    content={}
                )
            
            logger.info(f"Found {len(providers)} available API configurations, starting concurrent search")
            
            # If only one provider, call directly
            if len(providers) == 1:
                return self._search_with_provider(providers[0])
            
            # Use thread pool for concurrent execution when multiple providers
            results = []
            max_workers = min(len(providers), 5)  # Limit maximum concurrency
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_provider = {
                    executor.submit(self._search_with_provider, provider): provider 
                    for provider in providers
                }
                
                # Collect results
                for future in as_completed(future_to_provider):
                    provider = future_to_provider[future]
                    try:
                        result = future.result(timeout=60)  # 1 minute timeout
                        results.append(result)
                        logger.info(f"Provider {provider['type']} completed search")
                    except Exception as e:
                        logger.error(f"Provider {provider['type']} search exception: {str(e)}")
                        results.append(ToolResult(
                            success=False,
                            message=f"Provider {provider['type']} execution exception: {str(e)}",
                            content=[]
                        ))
            
            # Merge results
            return self._merge_results(results)
                
        except Exception as e:
            logger.error(f"Web search tool execution failed: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Web search tool execution failed: {str(e)}",
                content=traceback.format_exc()
            )

