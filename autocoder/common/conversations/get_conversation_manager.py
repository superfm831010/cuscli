import os
import threading
from typing import Optional, List, Dict
from .manager import PersistConversationManager
from .config import ConversationManagerConfig


class ConversationManagerSingleton:
    """对话管理器的单例类，确保全局只有一个实例"""

    _instance: Optional[PersistConversationManager] = None
    _lock = threading.Lock()
    _config: Optional[ConversationManagerConfig] = None

    @classmethod
    def get_instance(
        cls, config: Optional[ConversationManagerConfig] = None
    ) -> PersistConversationManager:
        """
        获取对话管理器实例

        Args:
            config: 配置对象，如果为None则使用默认配置

        Returns:
            PersistConversationManager实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if config is None:
                        config = cls._get_default_config()
                    cls._config = config
                    cls._instance = PersistConversationManager(config)
        return cls._instance

    @classmethod
    def reset_instance(cls, config: Optional[ConversationManagerConfig] = None):
        """
        重置实例，用于测试或配置更改时

        Args:
            config: 新的配置对象
        """
        with cls._lock:
            cls._instance = None
            cls._config = None
            if config is not None:
                cls._instance = PersistConversationManager(config)
                cls._config = config

    @classmethod
    def _get_default_config(cls) -> ConversationManagerConfig:
        """获取默认配置"""
        # 默认存储路径为当前工作目录下的 .auto-coder/conversations
        default_storage_path = os.path.join(os.getcwd(), ".auto-coder", "conversations")

        return ConversationManagerConfig(
            storage_path=default_storage_path,
            max_cache_size=100,
            cache_ttl=300.0,
            lock_timeout=10.0,
            backup_enabled=True,
            backup_interval=3600.0,
            max_backups=10,
        )

    @classmethod
    def get_config(cls) -> Optional[ConversationManagerConfig]:
        """获取当前使用的配置"""
        return cls._config


def get_conversation_manager(
    config: Optional[ConversationManagerConfig] = None,
) -> PersistConversationManager:
    """
    获取全局对话管理器实例

    这是一个便捷函数，内部使用单例模式确保全局只有一个实例。
    首次调用时会创建实例，后续调用会返回同一个实例。

    Args:
        config: 可选的配置对象。如果为None，将使用默认配置。
               注意：只有在首次调用时，config参数才会生效。

    Returns:
        PersistConversationManager: 对话管理器实例

    Example:
        ```python
        # 使用默认配置
        manager = get_conversation_manager()

        # 使用自定义配置（仅在首次调用时生效）
        config = ConversationManagerConfig(
            storage_path="./my_conversations",
            max_cache_size=200,
            default_namespace="my_project"
        )
        manager = get_conversation_manager(config)

        # 创建对话
        conv_id = manager.create_conversation(
            name="测试对话",
            description="这是一个测试对话"
        )

        # 使用命名空间管理当前对话
        manager.set_current_conversation(conv_id, "my_project")
        current_id = manager.get_current_conversation_id("my_project")
        ```
    """
    return ConversationManagerSingleton.get_instance(config)


def reset_conversation_manager(config: Optional[ConversationManagerConfig] = None):
    """
    重置全局对话管理器实例

    用于测试或需要更改配置时重置实例。

    Args:
        config: 新的配置对象，如果为None则在下次调用get_conversation_manager时使用默认配置

    Example:
        ```python
        # 重置为默认配置
        reset_conversation_manager()

        # 重置为新配置
        new_config = ConversationManagerConfig(storage_path="./new_path")
        reset_conversation_manager(new_config)
        ```
    """
    ConversationManagerSingleton.reset_instance(config)


def get_conversation_manager_config() -> Optional[ConversationManagerConfig]:
    """
    获取当前对话管理器使用的配置

    Returns:
        当前配置对象，如果还未初始化则返回None
    """
    return ConversationManagerSingleton.get_config()


def get_current_conversation_id_with_namespace(
    namespace: Optional[str] = None,
) -> Optional[str]:
    """
    获取指定命名空间的当前对话ID

    Args:
        namespace: 命名空间，None表示使用默认命名空间

    Returns:
        当前对话ID，如果未设置返回None

    Example:
        ```python
        # 获取默认命名空间的当前对话ID
        current_id = get_current_conversation_id_with_namespace()

        # 获取特定命名空间的当前对话ID
        project_id = get_current_conversation_id_with_namespace("my_project")
        ```
    """
    manager = get_conversation_manager()
    return manager.get_current_conversation_id(namespace)


def set_current_conversation_with_namespace(
    conversation_id: str, namespace: Optional[str] = None
) -> bool:
    """
    设置指定命名空间的当前对话

    Args:
        conversation_id: 对话ID
        namespace: 命名空间，None表示使用默认命名空间

    Returns:
        True if setting was successful

    Example:
        ```python
        # 设置默认命名空间的当前对话
        set_current_conversation_with_namespace("conv-123")

        # 设置特定命名空间的当前对话
        set_current_conversation_with_namespace("conv-456", "my_project")
        ```
    """
    manager = get_conversation_manager()
    return manager.set_current_conversation(conversation_id, namespace)


def list_conversation_namespaces() -> List[Optional[str]]:
    """
    列出所有已使用的命名空间

    Returns:
        命名空间列表，None 表示默认命名空间

    Example:
        ```python
        namespaces = list_conversation_namespaces()
        for ns in namespaces:
            if ns is None:
                print("默认命名空间")
            else:
                print(f"命名空间: {ns}")
        ```
    """
    manager = get_conversation_manager()
    return manager.list_namespaces()


def get_all_current_conversations_by_namespace() -> Dict[Optional[str], str]:
    """
    获取所有命名空间的当前对话ID

    Returns:
        命名空间到对话ID的映射

    Example:
        ```python
        all_current = get_all_current_conversations_by_namespace()
        for namespace, conv_id in all_current.items():
            ns_name = "默认" if namespace is None else namespace
            print(f"命名空间 '{ns_name}' 的当前对话: {conv_id}")
        ```
    """
    manager = get_conversation_manager()
    return manager.get_all_current_conversations()


def copy_conversation(
    source_conversation_id: str,
    new_name: Optional[str] = None,
    new_description: Optional[str] = None,
    new_conversation_id: Optional[str] = None,
    copy_messages: bool = True,
    copy_metadata: bool = True,
) -> str:
    """
    复制一个会话，生成新的会话ID

    Args:
        source_conversation_id: 源会话ID
        new_name: 新会话名称，如果为None则使用 "源会话名称 (副本)"
        new_description: 新会话描述，如果为None则复制源会话描述
        new_conversation_id: 可选的新会话ID，如果为None则自动生成
        copy_messages: 是否复制消息，默认True
        copy_metadata: 是否复制元数据，默认True

    Returns:
        新会话的ID

    Example:
        ```python
        # 复制会话，自动生成新ID
        new_id = copy_conversation("source-conv-123")

        # 复制会话，指定新名称和ID
        new_id = copy_conversation(
            "source-conv-123",
            new_name="我的会话副本",
            new_conversation_id="my-copy-001"
        )

        # 只复制会话元信息，不复制消息
        new_id = copy_conversation(
            "source-conv-123",
            copy_messages=False
        )
        ```
    """
    manager = get_conversation_manager()
    return manager.copy_conversation(
        source_conversation_id=source_conversation_id,
        new_name=new_name,
        new_description=new_description,
        new_conversation_id=new_conversation_id,
        copy_messages=copy_messages,
        copy_metadata=copy_metadata,
    )


# 便捷别名
get_manager = get_conversation_manager
reset_manager = reset_conversation_manager
get_manager_config = get_conversation_manager_config

# 命名空间相关的便捷别名
get_current_conv_id = get_current_conversation_id_with_namespace
set_current_conv = set_current_conversation_with_namespace
list_namespaces = list_conversation_namespaces
get_all_current_convs = get_all_current_conversations_by_namespace

# 会话操作便捷别名
copy_conv = copy_conversation
