"""远程服务数据模型"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class ResourceType(str, Enum):
    """资源类型"""

    AGENTS = "agents"
    WORKFLOWS = "workflows"
    TOOLS = "tools"
    COMMANDS = "commands"


@dataclass
class RemoteResource:
    """远程资源信息"""

    name: str
    type: ResourceType
    size: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    content: Optional[str] = None
    content_bytes: Optional[bytes] = None  # 二进制内容，用于下载

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], resource_type: ResourceType
    ) -> "RemoteResource":
        """从字典创建 RemoteResource"""
        return cls(
            name=data.get("name", ""),
            type=resource_type,
            size=data.get("size", 0),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            description=data.get("description"),
            version=data.get("version"),
            author=data.get("author"),
            tags=data.get("tags", []),
            category=data.get("category"),
            content=data.get("content"),
        )


@dataclass
class ResourceListResponse:
    """资源列表响应"""

    resources: List[RemoteResource]
    total: int
    page: int
    limit: int
    has_more: bool

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], resource_type: ResourceType
    ) -> "ResourceListResponse":
        """从 API 响应创建 ResourceListResponse

        API 响应格式:
        {
            "success": true,
            "data": {
                "agents": [...] 或 "workflows": [...],
                "total": 11
            }
        }
        """
        inner_data = data.get("data", {})

        # 根据资源类型获取对应的列表
        type_key = resource_type.value  # "agents" 或 "workflows"
        items = inner_data.get(type_key, [])

        resources = [RemoteResource.from_dict(item, resource_type) for item in items]
        total = inner_data.get("total", len(resources))

        return cls(
            resources=resources,
            total=total,
            page=1,  # API 暂不支持分页参数返回
            limit=len(resources),
            has_more=False,
        )


@dataclass
class SyncResult:
    """同步结果"""

    success: bool
    synced_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    synced_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def add_synced(self, filename: str):
        """添加已同步文件"""
        self.synced_files.append(filename)
        self.synced_count += 1

    def add_skipped(self, filename: str):
        """添加跳过的文件"""
        self.skipped_files.append(filename)
        self.skipped_count += 1

    def add_failed(self, filename: str):
        """添加失败的文件"""
        self.failed_files.append(filename)
        self.failed_count += 1


@dataclass
class ResourceStats:
    """资源统计信息"""

    agents_count: int = 0
    workflows_count: int = 0
    tools_count: int = 0
    commands_count: int = 0
    total_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceStats":
        """从 API 响应创建 ResourceStats

        API 响应格式:
        {
            "success": true,
            "data": {
                "byType": {
                    "agents": { "count": 11, "totalSize": 26897 },
                    ...
                },
                "total": { "count": 14, "size": 28540 }
            }
        }
        """
        inner_data = data.get("data", {})
        by_type = inner_data.get("byType", {})
        total_info = inner_data.get("total", {})

        return cls(
            agents_count=by_type.get("agents", {}).get("count", 0),
            workflows_count=by_type.get("workflows", {}).get("count", 0),
            tools_count=by_type.get("tools", {}).get("count", 0),
            commands_count=by_type.get("commands", {}).get("count", 0),
            total_count=total_info.get("count", 0),
        )
