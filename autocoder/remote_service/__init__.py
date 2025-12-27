"""远程服务模块 - 与 api.auto-coder.chat 交互"""

from autocoder.remote_service.manager import RemoteServiceManager
from autocoder.remote_service.api_client import RemoteAPIClient
from autocoder.remote_service.models import (
    ResourceType,
    RemoteResource,
    ResourceListResponse,
    SyncResult,
)

__all__ = [
    "RemoteServiceManager",
    "RemoteAPIClient",
    "ResourceType",
    "RemoteResource",
    "ResourceListResponse",
    "SyncResult",
]
