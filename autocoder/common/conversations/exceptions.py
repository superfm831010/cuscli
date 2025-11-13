"""
PersistConversationManager 异常类定义
"""


class ConversationManagerError(Exception):
    """对话管理器基础异常类"""
    
    def __init__(self, message="对话管理器发生错误", error_code="GENERAL_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class ConversationNotFoundError(ConversationManagerError):
    """对话不存在异常"""
    
    def __init__(self, conversation_id):
        # 检查是否是类似ID的字符串（不包含中文等）
        if (isinstance(conversation_id, str) and len(conversation_id) > 0 and 
            not any(ord(c) > 127 or c.isspace() for c in conversation_id)):
            message = f"对话未找到: {conversation_id}"
        else:
            message = conversation_id  # 自定义消息
        super().__init__(message, error_code="CONVERSATION_NOT_FOUND")


class MessageNotFoundError(ConversationManagerError):
    """消息不存在异常"""
    
    def __init__(self, message_id):
        # 检查是否是类似ID的字符串（不包含中文等）
        if (isinstance(message_id, str) and len(message_id) > 0 and 
            not any(ord(c) > 127 or c.isspace() for c in message_id)):
            message = f"消息未找到: {message_id}"
        else:
            message = message_id  # 自定义消息
        super().__init__(message, error_code="MESSAGE_NOT_FOUND")


class ConcurrencyError(ConversationManagerError):
    """并发访问异常"""
    
    def __init__(self, message="并发访问冲突"):
        super().__init__(message, error_code="CONCURRENCY_ERROR")


class DataIntegrityError(ConversationManagerError):
    """数据完整性异常"""
    
    def __init__(self, message="数据完整性检查失败"):
        super().__init__(message, error_code="DATA_INTEGRITY_ERROR")


class LockTimeoutError(ConversationManagerError):
    """锁超时异常"""
    
    def __init__(self, message="锁获取超时"):
        super().__init__(message, error_code="LOCK_TIMEOUT_ERROR")


class BackupError(ConversationManagerError):
    """备份操作异常"""
    
    def __init__(self, message="备份操作失败"):
        super().__init__(message, error_code="BACKUP_ERROR")


class RestoreError(ConversationManagerError):
    """恢复操作异常"""

    def __init__(self, message="恢复操作失败"):
        super().__init__(message, error_code="RESTORE_ERROR")


class EmptyMessageError(ConversationManagerError):
    """空消息内容异常"""

    def __init__(
        self,
        conversation_id: str = None,
        role: str = None,
        content_preview: str = None,
        call_location: str = None,
        additional_context: dict = None
    ):
        # 构建详细的错误消息
        details = ["尝试添加空消息到对话历史"]

        if conversation_id:
            details.append(f"对话ID: {conversation_id}")

        if role:
            details.append(f"消息角色: {role}")

        if content_preview:
            details.append(f"内容预览: {content_preview}")

        if call_location:
            details.append(f"调用位置: {call_location}")

        if additional_context:
            for key, value in additional_context.items():
                details.append(f"{key}: {value}")

        message = "\n  ".join(details)
        super().__init__(message, error_code="EMPTY_MESSAGE_ERROR")

        # 保存详细信息供调试使用
        self.conversation_id = conversation_id
        self.role = role
        self.content_preview = content_preview
        self.call_location = call_location
        self.additional_context = additional_context or {}