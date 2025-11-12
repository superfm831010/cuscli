

"""
Auto-Coder SDK 常量定义

定义SDK中使用的各种常量，包括默认值、配置选项、错误码等。
"""

from enum import Enum, auto
from autocoder.common.international import get_message

# 版本信息
SDK_VERSION = "1.7.4"

# 默认配置
DEFAULT_MAX_TURNS = 10000
DEFAULT_OUTPUT_FORMAT = "text"
DEFAULT_PERMISSION_MODE = "manual"
DEFAULT_SESSION_TIMEOUT = 3600  # 1小时
DEFAULT_MODEL = "deepseek/v3"  # 默认使用的模型


class OutputFormat(Enum):
    """输出格式枚举"""
    TEXT = "text"
    JSON = "json"
    STREAM_JSON = "stream-json"
    
    @classmethod
    def values(cls):
        return [e.value for e in cls]


class InputFormat(Enum):
    """输入格式枚举"""
    TEXT = "text"
    JSON = "json"
    STREAM_JSON = "stream-json"
    
    @classmethod
    def values(cls):
        return [e.value for e in cls]


class PermissionMode(Enum):
    """权限模式枚举"""
    MANUAL = "manual"
    ACCEPT_EDITS = "acceptEdits"
    ACCEPT_ALL = "acceptAll"
    
    @classmethod
    def values(cls):
        return [e.value for e in cls]


class AllowedTool(Enum):
    """允许的工具枚举"""
    READ = "Read"
    WRITE = "Write" 
    BASH = "Bash"
    SEARCH = "Search"
    INDEX = "Index"
    CHAT = "Chat"
    DESIGN = "Design"
    
    @classmethod
    def values(cls):
        return [e.value for e in cls]


class EventType(Enum):
    """事件类型枚举"""
    START = "start"
    CONTENT = "content"
    END = "end"
    ERROR = "error"
    LLM_THINKING = "llm_thinking"
    LLM_OUTPUT = "llm_output"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    COMPLETION = "completion"
    TOKEN_USAGE = "token_usage"
    WINDOW_CHANGE = "window_change"
    CONVERSATION_ID = "conversation_id"
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    PLAN_MODE_RESPOND = "plan_mode_respond"
    
    @classmethod
    def values(cls):
        return [e.value for e in cls]


class ErrorCode(Enum):
    """错误码枚举"""
    SDK_ERROR = "SDK_ERROR"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    INVALID_OPTIONS = "INVALID_OPTIONS"
    BRIDGE_ERROR = "BRIDGE_ERROR"
    CLI_ERROR = "CLI_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    
    @classmethod
    def values(cls):
        return [e.value for e in cls]


# 支持的输出格式（向后兼容）
def _get_output_formats():
    """动态获取输出格式描述，支持国际化"""
    try:
        return {
            OutputFormat.TEXT.value: get_message("format_description_text"),
            OutputFormat.JSON.value: get_message("format_description_json"),
            OutputFormat.STREAM_JSON.value: get_message("format_description_stream_json")
        }
    except:
        # 回退到硬编码描述
        return {
            OutputFormat.TEXT.value: "Plain text format",
            OutputFormat.JSON.value: "JSON format",
            OutputFormat.STREAM_JSON.value: "Streaming JSON format"
        }

OUTPUT_FORMATS = _get_output_formats()

# 支持的输入格式（向后兼容）
INPUT_FORMATS = OUTPUT_FORMATS

# 权限模式（向后兼容）
def _get_permission_modes():
    """动态获取权限模式描述，支持国际化"""
    try:
        return {
            PermissionMode.MANUAL.value: get_message("permission_description_manual"),
            PermissionMode.ACCEPT_EDITS.value: get_message("permission_description_accept_edits"),
            PermissionMode.ACCEPT_ALL.value: get_message("permission_description_accept_all")
        }
    except:
        # 回退到硬编码描述
        return {
            PermissionMode.MANUAL.value: "Manually confirm each operation",
            PermissionMode.ACCEPT_EDITS.value: "Automatically accept file edits",
            PermissionMode.ACCEPT_ALL.value: "Automatically accept all operations"
        }

PERMISSION_MODES = _get_permission_modes()

# 支持的工具（向后兼容）
ALLOWED_TOOLS = [tool.value for tool in AllowedTool]

# 错误码（向后兼容）
ERROR_CODES = {code.value: code.name for code in ErrorCode}

# CLI相关常量
CLI_COMMAND_NAME = "auto-coder.run"
CLI_EXIT_SUCCESS = 0
CLI_EXIT_ERROR = 1
CLI_EXIT_INVALID_ARGS = 2

# 会话相关常量
SESSION_DIR_NAME = ".auto-coder/sdk/sessions"
SESSION_FILE_EXTENSION = ".json"
MAX_SESSIONS_TO_KEEP = 100

# 文件和目录
DEFAULT_PROJECT_ROOT = "."
CONFIG_FILE_NAME = ".auto-coder-sdk.json"

# 网络和超时
DEFAULT_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3

# 日志级别
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# 流式输出标记
STREAM_START_MARKER = "<<STREAM_START>>"
STREAM_END_MARKER = "<<STREAM_END>>"
STREAM_ERROR_MARKER = "<<STREAM_ERROR>>"

