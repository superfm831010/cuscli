
"""
Auto-Coder SDK 异常定义

定义所有自定义异常类，提供错误码和异常的映射关系，统一异常处理策略。
"""

from autocoder.common.international import get_message_with_format

class AutoCoderSDKError(Exception):
    """SDK基础异常类"""
    
    def __init__(self, message: str, error_code: str = "SDK_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
    
    def __str__(self):
        return get_message_with_format("sdk_error_with_code", error_code=self.error_code, message=self.message)


class SessionNotFoundError(AutoCoderSDKError):
    """会话未找到异常"""
    
    def __init__(self, session_id: str):
        super().__init__(
            get_message_with_format("session_not_found", session_id=session_id),
            error_code="SESSION_NOT_FOUND"
        )
        self.session_id = session_id


class InvalidOptionsError(AutoCoderSDKError):
    """无效选项异常"""
    
    def __init__(self, message: str):
        super().__init__(
            get_message_with_format("invalid_options", message=message),
            error_code="INVALID_OPTIONS"
        )


class BridgeError(AutoCoderSDKError):
    """桥接层异常"""
    
    def __init__(self, message: str, original_error: Exception | None = None):
        if original_error:
            formatted_message = get_message_with_format("bridge_error_with_original", 
                                                       message=message, 
                                                       original_error=str(original_error))
        else:
            formatted_message = get_message_with_format("bridge_error", message=message)
        
        super().__init__(formatted_message, error_code="BRIDGE_ERROR")
        self.original_error = original_error


class CLIError(AutoCoderSDKError):
    """CLI异常"""
    
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(
            get_message_with_format("cli_error", message=message),
            error_code="CLI_ERROR"
        )
        self.exit_code = exit_code


class ValidationError(AutoCoderSDKError):
    """验证错误异常"""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            get_message_with_format("validation_error_field", field=field, message=message),
            error_code="VALIDATION_ERROR"
        )
        self.field = field

