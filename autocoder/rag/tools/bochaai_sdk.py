
"""
BochaAI SDK 封装

该模块提供了 BochaAI API 的 Python SDK 封装，支持网页搜索和内容爬取功能。
"""

import json
import time
import requests
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from loguru import logger
from urllib.parse import urlparse, urljoin


@dataclass
class BochaAIWebPage:
    """BochaAI 网页搜索结果数据类"""
    name: str
    url: str
    snippet: str
    display_url: Optional[str] = None
    summary: Optional[str] = None
    site_name: Optional[str] = None
    site_icon: Optional[str] = None
    date_published: Optional[str] = None
    date_last_crawled: Optional[str] = None
    cached_page_url: Optional[str] = None
    language: Optional[str] = None
    is_family_friendly: Optional[bool] = None
    is_navigational: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "name": self.name,
            "url": self.url,
            "snippet": self.snippet
        }
        
        # 添加可选字段
        optional_fields = [
            "display_url", "summary", "site_name", "site_icon",
            "date_published", "date_last_crawled", "cached_page_url",
            "language", "is_family_friendly", "is_navigational"
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
                
        return result


@dataclass
class BochaAIImage:
    """BochaAI 图片搜索结果数据类"""
    thumbnail_url: str
    content_url: str
    host_page_url: str
    width: int
    height: int
    name: Optional[str] = None
    web_search_url: Optional[str] = None
    date_published: Optional[str] = None
    content_size: Optional[str] = None
    encoding_format: Optional[str] = None
    host_page_display_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            k: v for k, v in self.__dict__.items() if v is not None
        }


@dataclass
class BochaAISearchResponse:
    """BochaAI 搜索响应数据类"""
    success: bool
    query: str
    total_matches: int = 0
    webpages: List[BochaAIWebPage] = field(default_factory=list)
    images: List[BochaAIImage] = field(default_factory=list)
    error: Optional[str] = None
    log_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "query": self.query,
            "total_matches": self.total_matches,
            "webpages": [page.to_dict() for page in self.webpages],
            "images": [img.to_dict() for img in self.images],
            "error": self.error,
            "log_id": self.log_id
        }


class BochaAIClient:
    """BochaAI API 客户端"""
    
    BASE_URL = "https://api.bochaai.com/v1"
    DEFAULT_TIMEOUT = 30  # 默认超时时间（秒）
    
    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化 BochaAI 客户端
        
        Args:
            api_key: BochaAI API 密钥
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def search(
        self,
        query: str,
        count: int = 10,
        freshness: str = "noLimit",
        summary: bool = False,
        include: Optional[str] = None,
        exclude: Optional[str] = None
    ) -> BochaAISearchResponse:
        """
        执行网页搜索
        
        Args:
            query: 搜索查询字符串
            count: 返回结果数量 (1-50)
            freshness: 时间范围过滤 (noLimit, oneDay, oneWeek, oneMonth, oneYear)
            summary: 是否包含文本摘要
            include: 指定搜索的网站范围，多个域名用|或,分隔
            exclude: 排除搜索的网站范围，多个域名用|或,分隔
            
        Returns:
            BochaAISearchResponse: 搜索响应对象
        """
        try:
            # 准备请求数据
            data = {
                "query": query,
                "count": min(max(count, 1), 50),  # 限制在 1-50 范围内
                "freshness": freshness,
                "summary": summary
            }
            
            # 添加可选参数
            if include:
                data["include"] = include
            if exclude:
                data["exclude"] = exclude
            
            logger.info(f"BochaAI 搜索请求: query={query}, count={count}, summary={summary}")
            
            # 发送请求
            response = self.session.post(
                f"{self.BASE_URL}/web-search",
                json=data,
                timeout=self.timeout
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API 请求失败，状态码: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = f"{error_msg}, 错误信息: {error_data['message']}"
                    log_id = error_data.get("log_id", "")
                except:
                    error_msg = f"{error_msg}, 响应内容: {response.text}"
                    log_id = ""
                
                logger.error(error_msg)
                return BochaAISearchResponse(
                    success=False,
                    query=query,
                    error=error_msg,
                    log_id=log_id
                )
            
            # 解析响应
            result = response.json()
            
            # 检查响应格式
            if result.get("code") != 200:
                error_msg = result.get("msg", "未知错误")
                return BochaAISearchResponse(
                    success=False,
                    query=query,
                    error=error_msg,
                    log_id=result.get("log_id")
                )
            
            data = result.get("data", {})
            
            # 解析网页搜索结果
            webpages = []
            web_pages_data = data.get("webPages", {})
            for item in web_pages_data.get("value", []):
                webpage = BochaAIWebPage(
                    name=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    display_url=item.get("displayUrl"),
                    summary=item.get("summary"),
                    site_name=item.get("siteName"),
                    site_icon=item.get("siteIcon"),
                    date_published=item.get("datePublished"),
                    date_last_crawled=item.get("dateLastCrawled"),
                    cached_page_url=item.get("cachedPageUrl"),
                    language=item.get("language"),
                    is_family_friendly=item.get("isFamilyFriendly"),
                    is_navigational=item.get("isNavigational")
                )
                webpages.append(webpage)
            
            # 解析图片搜索结果
            images = []
            images_data = data.get("images", {})
            for item in images_data.get("value", []):
                image = BochaAIImage(
                    thumbnail_url=item.get("thumbnailUrl", ""),
                    content_url=item.get("contentUrl", ""),
                    host_page_url=item.get("hostPageUrl", ""),
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                    name=item.get("name"),
                    web_search_url=item.get("webSearchUrl"),
                    date_published=item.get("datePublished"),
                    content_size=item.get("contentSize"),
                    encoding_format=item.get("encodingFormat"),
                    host_page_display_url=item.get("hostPageDisplayUrl")
                )
                images.append(image)
            
            total_matches = web_pages_data.get("totalEstimatedMatches", 0)
            
            return BochaAISearchResponse(
                success=True,
                query=query,
                total_matches=total_matches,
                webpages=webpages,
                images=images,
                log_id=result.get("log_id")
            )
            
        except requests.exceptions.Timeout:
            error_msg = f"搜索请求超时（{self.timeout}秒）"
            logger.error(error_msg)
            return BochaAISearchResponse(
                success=False,
                query=query,
                error=error_msg
            )
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return BochaAISearchResponse(
                success=False,
                query=query,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"搜索失败: {str(e)}"
            logger.error(error_msg)
            return BochaAISearchResponse(
                success=False,
                query=query,
                error=error_msg
            )
    
    def crawl_page(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        爬取单个网页内容（使用 requests）
        
        Args:
            url: 要爬取的网页 URL
            headers: 自定义请求头
            
        Returns:
            Dict: 包含网页内容的字典
        """
        try:
            logger.info(f"BochaAI 爬取页面: {url}")
            
            # 设置默认请求头
            default_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            if headers:
                default_headers.update(headers)
            
            # 发送请求
            response = requests.get(
                url,
                headers=default_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"页面请求失败，状态码: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "url": url,
                    "error": error_msg,
                    "status_code": response.status_code
                }
            
            # 获取内容
            content = response.text
            
            # 尝试提取标题
            title = ""
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": content,
                "content_type": response.headers.get("Content-Type", ""),
                "content_length": len(content),
                "status_code": response.status_code
            }
            
        except requests.exceptions.Timeout:
            error_msg = f"页面请求超时（{self.timeout}秒）"
            logger.error(error_msg)
            return {
                "success": False,
                "url": url,
                "error": error_msg
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "url": url,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"爬取失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "url": url,
                "error": error_msg
            }
    
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
        爬取网站内容（使用搜索和爬取组合实现）
        
        Args:
            url: 起始 URL
            limit: 最大爬取页面数
            max_depth: 最大爬取深度（暂未实现）
            exclude_paths: 排除的路径列表
            include_paths: 包含的路径列表
            allow_subdomains: 是否允许子域名
            
        Returns:
            List[Dict]: 爬取的页面内容列表
        """
        try:
            # 解析起始 URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 如果只爬取一个页面
            if limit == 1:
                result = self.crawl_page(url)
                if result.get("success"):
                    return [{
                        "url": url,
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "markdown": result.get("content", ""),  # 简单处理，实际应该转换为 markdown
                        "links": [],
                        "metadata": {
                            "source": "bochaai",
                            "content_type": result.get("content_type", ""),
                            "status_code": result.get("status_code", 200)
                        }
                    }]
                else:
                    return []
            
            # 多页爬取：先搜索该域名下的相关页面
            search_query = f"site:{domain}"
            if parsed_url.path and parsed_url.path != "/":
                # 如果有特定路径，添加到搜索中
                path_keywords = parsed_url.path.strip("/").replace("/", " ")
                search_query += f" {path_keywords}"
            
            logger.info(f"开始爬取: {url}, 限制: {limit} 页")
            
            # 执行搜索获取相关页面
            search_result = self.search(
                query=search_query,
                count=min(limit * 2, 50),  # 搜索更多结果以便筛选
                summary=False
            )
            
            if not search_result.success:
                logger.error(f"爬取失败: {search_result.error}")
                # 至少尝试爬取起始页面
                result = self.crawl_page(url)
                if result.get("success"):
                    return [{
                        "url": url,
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "markdown": result.get("content", ""),
                        "links": [],
                        "metadata": {"source": "bochaai"}
                    }]
                return []
            
            crawled_pages = []
            urls_to_crawl = [url]  # 起始URL
            
            # 添加搜索结果中的URL
            for webpage in search_result.webpages:
                if webpage.url and webpage.url not in urls_to_crawl:
                    # 检查是否应该包含这个URL
                    should_include = True
                    
                    # 检查排除路径
                    if exclude_paths:
                        for exclude_path in exclude_paths:
                            if exclude_path in webpage.url:
                                should_include = False
                                break
                    
                    # 检查包含路径
                    if include_paths and should_include:
                        should_include = False
                        for include_path in include_paths:
                            if include_path in webpage.url:
                                should_include = True
                                break
                    
                    # 检查子域名
                    if not allow_subdomains and should_include:
                        webpage_domain = urlparse(webpage.url).netloc
                        if webpage_domain != domain:
                            should_include = False
                    
                    if should_include:
                        urls_to_crawl.append(webpage.url)
            
            # 限制爬取数量
            urls_to_crawl = urls_to_crawl[:limit]
            
            # 爬取每个页面的内容
            for idx, page_url in enumerate(urls_to_crawl):
                logger.info(f"爬取页面 {idx + 1}/{len(urls_to_crawl)}: {page_url}")
                
                result = self.crawl_page(page_url)
                
                if result.get("success"):
                    # 从搜索结果中查找对应的信息
                    page_info = None
                    for webpage in search_result.webpages:
                        if webpage.url == page_url:
                            page_info = webpage
                            break
                    
                    page_result = {
                        "url": page_url,
                        "title": page_info.name if page_info else result.get("title", ""),
                        "content": result.get("content", ""),
                        "markdown": result.get("content", ""),  # 简单处理
                        "links": [],
                        "metadata": {
                            "position": idx + 1,
                            "source": "bochaai",
                            "content_type": result.get("content_type", ""),
                            "status_code": result.get("status_code", 200)
                        }
                    }
                    
                    # 添加额外的元数据
                    if page_info:
                        if page_info.date_published:
                            page_result["metadata"]["date_published"] = page_info.date_published
                        if page_info.site_name:
                            page_result["metadata"]["site_name"] = page_info.site_name
                    
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

