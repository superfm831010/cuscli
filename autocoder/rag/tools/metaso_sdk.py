"""
Metaso SDK 封装

该模块提供了 Metaso API 的 Python SDK 封装，支持网页搜索和内容读取功能。
"""

import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import requests
from loguru import logger


@dataclass
class MetasoSearchResult:
    """Metaso 搜索结果数据类"""
    title: str
    link: str
    snippet: str
    score: str = "medium"
    position: int = 0
    date: Optional[str] = None
    authors: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "score": self.score,
            "position": self.position
        }
        if self.date:
            result["date"] = self.date
        if self.authors:
            result["authors"] = self.authors
        return result


@dataclass
class MetasoSearchResponse:
    """Metaso 搜索响应数据类"""
    credits: int
    search_parameters: Dict[str, Any]
    webpages: List[MetasoSearchResult]
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "credits": self.credits,
            "searchParameters": self.search_parameters,
            "webpages": [page.to_dict() for page in self.webpages],
            "success": self.success,
            "error": self.error
        }


class MetasoClient:
    """Metaso API 客户端"""
    
    BASE_URL = "https://metaso.cn/api/v1"
    DEFAULT_TIMEOUT = 30  # 默认超时时间（秒）
    
    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化 Metaso 客户端
        
        Args:
            api_key: Metaso API 密钥
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
    
    def search(
        self,
        query: str,
        scope: str = "webpage",
        size: Union[int, str] = 10,
        include_summary: bool = False,
        include_raw_content: bool = False,
        concise_snippet: bool = False,
        format: str = "chat_completions"
    ) -> MetasoSearchResponse:
        """
        执行网页搜索
        
        Args:
            query: 搜索查询字符串
            scope: 搜索范围，如 "webpage"、"news" 等
            size: 返回结果数量
            include_summary: 是否包含摘要
            include_raw_content: 是否包含原始内容
            concise_snippet: 是否使用简洁摘要
            format: 返回格式类型
            
        Returns:
            MetasoSearchResponse: 搜索响应对象
        """
        try:
            # 准备请求数据
            data = {
                "q": query,
                "scope": scope,
                "size": str(size),  # 确保是字符串
                "includeSummary": include_summary,
                "includeRawContent": include_raw_content,
                "conciseSnippet": concise_snippet
            }
            
            # 如果不是默认格式，添加format参数
            if format != "chat_completions":
                data["format"] = format
            
            logger.info(f"Metaso 搜索请求: query={query}, scope={scope}, size={size}")
            
            # 发送请求
            response = self.session.post(
                f"{self.BASE_URL}/search",
                json=data,
                timeout=self.timeout
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API 请求失败，状态码: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"{error_msg}, 错误信息: {error_data['error']}"
                except:
                    error_msg = f"{error_msg}, 响应内容: {response.text}"
                
                logger.error(error_msg)
                return MetasoSearchResponse(
                    credits=0,
                    search_parameters={},
                    webpages=[],
                    success=False,
                    error=error_msg
                )
            
            # 解析响应
            result = response.json()
            
            # 解析搜索结果
            webpages = []
            for idx, item in enumerate(result.get("webpages", [])):
                webpage = MetasoSearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    score=item.get("score", "medium"),
                    position=item.get("position", idx + 1),
                    date=item.get("date"),
                    authors=item.get("authors")
                )
                webpages.append(webpage)
            
            return MetasoSearchResponse(
                credits=result.get("credits", 0),
                search_parameters=result.get("searchParameters", {}),
                webpages=webpages,
                success=True
            )
            
        except requests.exceptions.Timeout:
            error_msg = f"搜索请求超时（{self.timeout}秒）"
            logger.error(error_msg)
            return MetasoSearchResponse(
                credits=0,
                search_parameters={},
                webpages=[],
                success=False,
                error=error_msg
            )
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return MetasoSearchResponse(
                credits=0,
                search_parameters={},
                webpages=[],
                success=False,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"搜索失败: {str(e)}"
            logger.error(error_msg)
            return MetasoSearchResponse(
                credits=0,
                search_parameters={},
                webpages=[],
                success=False,
                error=error_msg
            )
    
    def read(
        self,
        url: str,
        format: str = "text/plain"
    ) -> Union[str, Dict[str, Any]]:
        """
        读取网页内容
        
        Args:
            url: 要读取的网页 URL
            format: 返回格式，"text/plain" 或 "application/json"
            
        Returns:
            Union[str, Dict]: 网页内容，根据format参数返回文本或JSON
        """
        try:
            # 准备请求头
            headers = self.session.headers.copy()
            headers["Accept"] = format
            
            # 准备请求数据
            data = {
                "url": url
            }
            
            logger.info(f"Metaso 读取请求: url={url}, format={format}")
            
            # 发送请求
            response = self.session.post(
                f"{self.BASE_URL}/reader",
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API 请求失败，状态码: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"{error_msg}, 错误信息: {error_data['error']}"
                except:
                    error_msg = f"{error_msg}, 响应内容: {response.text}"
                
                logger.error(error_msg)
                if format == "application/json":
                    return {"success": False, "error": error_msg, "content": ""}
                else:
                    return f"Error: {error_msg}"
            
            # 根据格式返回结果
            if format == "application/json":
                return response.json()
            else:
                return response.text
            
        except requests.exceptions.Timeout:
            error_msg = f"读取请求超时（{self.timeout}秒）"
            logger.error(error_msg)
            if format == "application/json":
                return {"success": False, "error": error_msg, "content": ""}
            else:
                return f"Error: {error_msg}"
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            if format == "application/json":
                return {"success": False, "error": error_msg, "content": ""}
            else:
                return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"读取失败: {str(e)}"
            logger.error(error_msg)
            if format == "application/json":
                return {"success": False, "error": error_msg, "content": ""}
            else:
                return f"Error: {error_msg}"
    
    def crawl(
        self,
        url: str,
        limit: int = 10,
        max_depth: Optional[int] = None,
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        allow_subdomains: bool = False
    ) -> List[Dict[str, Any]]:
        """
        爬取网站内容（使用搜索和读取组合实现）
        
        Args:
            url: 起始 URL
            limit: 最大爬取页面数
            max_depth: 最大爬取深度
            exclude_paths: 排除的路径列表
            include_paths: 包含的路径列表
            allow_subdomains: 是否允许子域名
            
        Returns:
            List[Dict]: 爬取的页面内容列表
        """
        try:
            from urllib.parse import urlparse, urljoin
            
            # 解析起始 URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 首先搜索该域名下的相关页面
            search_query = f"site:{domain}"
            if parsed_url.path and parsed_url.path != "/":
                # 如果有特定路径，添加到搜索中
                search_query += f" {parsed_url.path}"
            
            logger.info(f"开始爬取: {url}, 限制: {limit} 页")
            
            # 执行搜索获取相关页面
            search_result = self.search(
                query=search_query,
                size=limit,
                include_raw_content=True
            )
            
            if not search_result.success:
                logger.error(f"爬取失败: {search_result.error}")
                return []
            
            crawled_pages = []
            urls_to_crawl = [url]  # 起始URL
            
            # 添加搜索结果中的URL
            for webpage in search_result.webpages:
                if webpage.link and webpage.link not in urls_to_crawl:
                    # 检查是否应该包含这个URL
                    should_include = True
                    
                    # 检查排除路径
                    if exclude_paths:
                        for exclude_path in exclude_paths:
                            if exclude_path in webpage.link:
                                should_include = False
                                break
                    
                    # 检查包含路径
                    if include_paths and should_include:
                        should_include = False
                        for include_path in include_paths:
                            if include_path in webpage.link:
                                should_include = True
                                break
                    
                    # 检查子域名
                    if not allow_subdomains and should_include:
                        webpage_domain = urlparse(webpage.link).netloc
                        if webpage_domain != domain:
                            should_include = False
                    
                    if should_include:
                        urls_to_crawl.append(webpage.link)
            
            # 限制爬取数量
            urls_to_crawl = urls_to_crawl[:limit]
            
            # 读取每个页面的内容
            for idx, page_url in enumerate(urls_to_crawl):
                logger.info(f"读取页面 {idx + 1}/{len(urls_to_crawl)}: {page_url}")
                
                content = self.read(page_url, format="text/plain")
                
                # 构建页面结果
                page_result = {
                    "url": page_url,
                    "title": "",  # 从内容中提取标题
                    "content": content if not content.startswith("Error:") else "",
                    "markdown": content if not content.startswith("Error:") else "",
                    "links": [],
                    "metadata": {
                        "position": idx + 1,
                        "source": "metaso"
                    }
                }
                
                # 尝试从搜索结果中获取标题
                for webpage in search_result.webpages:
                    if webpage.link == page_url:
                        page_result["title"] = webpage.title
                        page_result["metadata"]["date"] = webpage.date
                        page_result["metadata"]["authors"] = webpage.authors
                        break
                
                crawled_pages.append(page_result)
                
                # 添加小延迟避免请求过快
                if idx < len(urls_to_crawl) - 1:
                    time.sleep(0.5)
            
            return crawled_pages
            
        except Exception as e:
            logger.error(f"爬取失败: {str(e)}")
            return []
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，关闭会话"""
        self.session.close()
