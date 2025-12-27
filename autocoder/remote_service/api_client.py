"""远程 API 客户端 - 与 api.auto-coder.chat 交互"""

import requests
from typing import Optional, Dict, Any, List
from loguru import logger

from autocoder.remote_service.models import (
    ResourceType,
    RemoteResource,
    ResourceListResponse,
    ResourceStats,
)


class RemoteAPIClient:
    """远程 API 客户端"""

    DEFAULT_BASE_URL = "https://api.auto-coder.chat"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        初始化 API 客户端

        Args:
            base_url: API 基础 URL，默认为 https://api.auto-coder.chat
            timeout: 请求超时时间（秒）
        """
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "auto-coder-chat/1.0",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            **kwargs: 其他请求参数

        Returns:
            API 响应数据

        Raises:
            requests.RequestException: 请求失败时
        """
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"请求: {method} {url} params={params}")

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()

        # 检查是否是下载请求
        if params and params.get("download"):
            # 使用二进制方式获取内容，支持文本和二进制文件
            return {"content": response.content, "is_binary": True}

        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康检查响应
        """
        return self._request("GET", "/api/health")

    def get_resources_overview(self) -> Dict[str, Any]:
        """
        获取资源概览

        Returns:
            资源概览数据
        """
        return self._request("GET", "/api/v1/resources")

    def get_resources_stats(self) -> ResourceStats:
        """
        获取资源统计

        Returns:
            ResourceStats 对象
        """
        data = self._request("GET", "/api/v1/resources/stats")
        return ResourceStats.from_dict(data)

    def list_resources(
        self,
        resource_type: ResourceType,
        page: int = 1,
        limit: int = 100,
        sort_by: str = "updatedAt",
        sort_order: str = "desc",
    ) -> ResourceListResponse:
        """
        列出指定类型的资源

        Args:
            resource_type: 资源类型
            page: 页码
            limit: 每页数量
            sort_by: 排序字段
            sort_order: 排序方向

        Returns:
            ResourceListResponse 对象
        """
        params = {
            "page": page,
            "limit": limit,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        data = self._request("GET", f"/api/v1/{resource_type.value}", params=params)
        return ResourceListResponse.from_dict(data, resource_type)

    def get_resource(
        self,
        resource_type: ResourceType,
        filename: str,
        download: bool = False,
    ) -> RemoteResource:
        """
        获取指定资源

        Args:
            resource_type: 资源类型
            filename: 文件名（不含扩展名）
            download: 是否获取文件内容

        Returns:
            RemoteResource 对象
        """
        params = {"download": "true"} if download else None
        data = self._request(
            "GET", f"/api/v1/{resource_type.value}/{filename}", params=params
        )

        if download:
            # 下载模式返回的是二进制内容
            return RemoteResource(
                name=filename,
                type=resource_type,
                content_bytes=data.get("content"),
            )

        # 详情模式返回完整信息
        resource_data = data.get("data", data)
        resource = RemoteResource.from_dict(resource_data, resource_type)
        resource.content = resource_data.get("content")
        return resource

    def download_resource(
        self,
        resource_type: ResourceType,
        filename: str,
    ) -> bytes:
        """
        下载资源内容

        Args:
            resource_type: 资源类型
            filename: 文件名

        Returns:
            资源文件内容（二进制）
        """
        resource = self.get_resource(resource_type, filename, download=True)
        return resource.content_bytes or b""

    def search_resources(
        self,
        query: str,
        resource_type: Optional[ResourceType] = None,
        search_content: bool = False,
    ) -> List[RemoteResource]:
        """
        搜索资源

        Args:
            query: 搜索关键词
            resource_type: 限定资源类型
            search_content: 是否搜索内容

        Returns:
            匹配的资源列表
        """
        params: Dict[str, Any] = {"q": query}
        if resource_type:
            params["type"] = resource_type.value
        if search_content:
            params["content"] = "true"

        data = self._request("GET", "/api/v1/resources/search", params=params)
        results = data.get("data", [])

        resources = []
        for item in results:
            item_type = ResourceType(item.get("type", "agents"))
            resources.append(RemoteResource.from_dict(item, item_type))
        return resources

    def get_all_resources(
        self,
        resource_type: Optional[ResourceType] = None,
    ) -> List[RemoteResource]:
        """
        获取所有资源（分页获取）

        Args:
            resource_type: 限定资源类型，None 表示所有类型

        Returns:
            所有资源列表
        """
        all_resources: List[RemoteResource] = []

        types_to_fetch = (
            [resource_type]
            if resource_type
            else [
                ResourceType.AGENTS,
                ResourceType.WORKFLOWS,
                ResourceType.TOOLS,
                ResourceType.COMMANDS,
            ]
        )

        for res_type in types_to_fetch:
            page = 1
            while True:
                response = self.list_resources(res_type, page=page, limit=100)
                all_resources.extend(response.resources)
                if not response.has_more:
                    break
                page += 1

        return all_resources

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
