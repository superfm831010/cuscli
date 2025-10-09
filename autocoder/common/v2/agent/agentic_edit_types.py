from pydantic import BaseModel
from typing import List, Dict, Any, Callable, Optional, Type, Union
from pydantic import SkipValidation
from enum import Enum

# Import for Pull Request support and Git operations
try:
    from autocoder.common.pull_requests.models import PRResult, PlatformType
except ImportError:
    # Fallback if pull_requests module is not available
    PRResult = None
    PlatformType = None

try:
    from autocoder.common.git_utils import CommitResult
except ImportError:
    # Fallback if git_utils is not available
    CommitResult = None

class ConversationAction(str, Enum):
    """Enumeration for conversation actions"""
    RESUME = "resume"
    NEW = "new"
    CONTINUE = "continue"
    LIST = "list"
    COMMAND = "command"

# Result class used by Tool Resolvers
class ToolResult(BaseModel):
    success: bool
    message: str
    content: Any = None # Can store file content, command output, etc.

# Pydantic Models for Tools
class BaseTool(BaseModel):
    pass

class ExecuteCommandTool(BaseTool):
    command: str    
    requires_approval: bool
    timeout: Optional[int] = 60  # 超时时间（秒），默认60秒
    background: Optional[bool] = False  # 是否后台运行，默认为False

class ReadFileTool(BaseTool):
    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    query: Optional[str] = None

class WriteToFileTool(BaseTool):
    path: str
    content: str
    mode: str = "write" # write or append


class CountTokensTool(BaseTool):
    """Token统计工具类型"""
    path: str  # 文件或目录路径
    recursive: Optional[bool] = True  # 是否递归统计目录
    include_summary: Optional[bool] = True  # 是否包含分类汇总

class ExtractToTextTool(BaseTool):
    """提取各种格式文件（包括URL）的文本内容到目标文件"""
    source_path: str  # 源路径，可以是本地文件路径或URL
    target_path: str  # 目标文本文件路径

class SessionStartTool(BaseTool):
    """启动交互式会话工具"""
    command: str                          # 要执行的命令，如 "python -i"
    timeout: Optional[int] = 60           # 启动超时时间（秒）
    cwd: Optional[str] = None             # 工作目录
    env: Optional[Dict[str, str]] = None  # 环境变量

class SessionInteractiveTool(BaseTool):
    """与交互式会话交互的工具"""
    session_id: str                       # 会话ID
    input: str                            # 发送到stdin的内容
    read_timeout: Optional[int] = 5       # 等待读取输出的时间（秒）
    max_bytes: Optional[int] = 40960       # 每次读取的最大字节数
    expect_prompt: Optional[bool] = False # 是否等待提示符出现再返回
    prompt_regex: Optional[str] = None  # 提示符的正则表达式

class SessionStopTool(BaseTool):
    """停止交互式会话工具"""
    session_id: str                       # 会话ID
    force: Optional[bool] = False         # True=强制杀死，False=优雅终止

class ReplaceInFileTool(BaseTool):
    path: str
    diff: str
    fence_0: Optional[str] = "```"
    fence_1: Optional[str] = "```"

class SearchFilesTool(BaseTool):
    path: str
    regex: str
    file_pattern: Optional[str] = None

class ListFilesTool(BaseTool):
    path: str
    recursive: Optional[bool] = False

class ListCodeDefinitionNamesTool(BaseTool):
    path: str

class AskFollowupQuestionTool(BaseTool):
    question: str
    options: Optional[List[str]] = None

class AttemptCompletionTool(BaseTool):
    result: str
    command: Optional[str] = None

class PlanModeRespondTool(BaseTool):
    response: str
    options: Optional[List[str]] = None

class UseMcpTool(BaseTool):
    server_name: str
    tool_name: str
    query:str

class UseRAGTool(BaseTool):
    server_name: str
    query: str

class RunNamedSubagentsTool(BaseTool):
    """
    Tool for running a named subagent with a specific query.
    Gets agent details from the agents module and executes via auto-coder.run.
    """
    subagents: str
    background: Optional[bool] = False  # 是否后台运行，默认为False

class ACModReadTool(BaseTool):
    path: str  # 源码包目录，相对路径或绝对路径

class ACModWriteTool(BaseTool):
    """
    Tool for creating or updating an AC Module's .ac.mod.md file.
    """
    path: str  # AC Module directory path, relative or absolute path
    diff: str  # diff content to edit the .ac.mod.md file

class ACModListTool(BaseTool):
    """
    Tool for listing all directories containing .ac.mod.md files (AC Modules).
    """
    path: Optional[str] = None  # Optional root path to search, defaults to source_dir

class TodoReadTool(BaseTool):
    """
    Tool for reading the current todo list.
    Takes no parameters.
    """
    pass  # No parameters needed

class TodoWriteTool(BaseTool):
    """
    Tool for creating and managing a structured task list.
    """
    action: str  # 'create', 'update', 'mark_progress', 'mark_completed', 'add_task'
    task_id: Optional[str] = None  # Task ID for update/mark operations
    content: Optional[str] = None  # Task content for create/add operations
    priority: Optional[str] = None  # 'high', 'medium', 'low'
    status: Optional[str] = None  # 'pending', 'in_progress', 'completed'
    notes: Optional[str] = None  # Additional notes for the task

class ConversationMessageIdsWriteTool(BaseTool):
    """
    Tool for writing conversation message IDs for pruning.
    Manages message IDs that should be DELETED during conversation pruning.
    """
    message_ids: str  # Message IDs specification like "9226b3a4,204e1cd8"
    action: str  # Action to perform: "create", "append", or "delete"

class ConversationMessageIdsReadTool(BaseTool):
    """
    Tool for reading existing conversation message IDs configuration.
    Returns the current message IDs configuration for the active conversation.
    """
    pass  # No parameters needed, uses current conversation ID

class BackgroundTaskTool(BaseTool):
    """后台任务管理工具
    
    支持对后台运行的命令和子代理任务进行统一管理，包括：
    - list: 列出当前会话的后台任务
    - monitor: 监控任务输出内容
    - cleanup: 清理已完成的任务记录
    - kill: 终止正在运行的任务
    
    任务标识支持 task_id、pid 和 process_uniq_id 三种方式。
    """
    action: str  # 操作类型: "list", "monitor", "cleanup", "kill"
    
    # list 操作参数
    show_completed: Optional[bool] = False  # 是否显示已完成的任务
    task_type: Optional[str] = None         # 过滤任务类型: "command", "subagent", None(全部)
    
    # monitor 操作参数
    task_id: Optional[str] = None           # 任务ID（UUID格式）
    pid: Optional[int] = None               # 进程ID（系统PID）
    process_uniq_id: Optional[str] = None   # 进程唯一ID（显示友好的短ID）
    lines: Optional[int] = 100              # 显示的行数，默认100行
    output_type: Optional[str] = "both"     # "stdout", "stderr", "both"
    
    # cleanup 操作参数
    status_filter: Optional[str] = None     # "completed", "failed", None(全部已结束的)
    older_than_minutes: Optional[int] = None  # 清理多少分钟前完成的任务
    task_ids: Optional[List[str]] = None    # 指定要清理的任务ID列表
    
    # kill 操作参数
    pids: Optional[List[int]] = None        # 批量终止多个进程（系统PID）
    force: Optional[bool] = False           # 是否强制终止（SIGKILL vs SIGTERM）
    kill_children: Optional[bool] = True    # 是否同时终止子进程


class WebCrawlTool(BaseTool):
    """网页爬取工具，使用 Firecrawl、Metaso 或 BochaAI 进行网页爬取
    
    支持多个API key配置时的并发爬取，结果会合并返回。
    使用线程池进行并发处理以提高效率。
    """
    url: str  # 要爬取的URL
    limit: Optional[int] = 10  # 爬取页面数量限制
    scrape_options: Optional[str] = None  # 抓取选项，JSON字符串格式
    exclude_paths: Optional[str] = None  # 排除的路径，逗号分割
    include_paths: Optional[str] = None  # 包含的路径，逗号分割
    max_depth: Optional[int] = None  # 最大爬取深度
    allow_subdomains: Optional[str] = "false"  # 是否允许子域名，true/false
    crawl_entire_domain: Optional[str] = "false"  # 是否爬取整个域名，true/false


class WebSearchTool(BaseTool):
    """网页搜索工具，使用 Firecrawl、Metaso 或 BochaAI 进行网页搜索
    
    支持多个API key配置时的并发搜索，结果会合并返回。
    使用线程池进行并发处理以提高效率。
    """
    query: str  # 搜索查询
    limit: Optional[int] = 5  # 返回结果数量限制
    sources: Optional[str] = None  # 搜索源类型，逗号分割：web,news,images
    scrape_options: Optional[str] = None  # 抓取选项，JSON字符串格式
    location: Optional[str] = None  # 搜索位置
    tbs: Optional[str] = None  # 时间过滤参数

# Event Types for Rich Output Streaming
class LLMOutputEvent(BaseModel):
    """Represents plain text output from the LLM."""
    text: str

class LLMThinkingEvent(BaseModel):
    """Represents text within <thinking> tags from the LLM."""
    text: str

class ToolCallEvent(BaseModel):
    """Represents the LLM deciding to call a tool."""
    tool: SkipValidation[BaseTool] # Use SkipValidation as BaseTool itself is complex
    tool_xml: str

class ToolResultEvent(BaseModel):
    """Represents the result of executing a tool."""
    tool_name: str
    result: ToolResult

class TokenUsageEvent(BaseModel):
    """Represents the result of executing a tool."""
    usage: Any


class ConversationIdEvent(BaseModel):
    """Represents the conversation id."""
    conversation_id: str

class PlanModeRespondEvent(BaseModel):
    """Represents the LLM attempting to complete the task."""
    completion: SkipValidation[PlanModeRespondTool] # Skip validation
    completion_xml: str

class CompletionEvent(BaseModel):
    """Represents the LLM attempting to complete the task."""
    completion: SkipValidation[AttemptCompletionTool] # Skip validation
    completion_xml: str

class PreCommitEvent(BaseModel):
    """Represents the LLM attempting to complete the task."""
    commit_result: CommitResult
    tpe: str = "pre_commit"

class CommitEvent(BaseModel):
    """Represents the LLM attempting to complete the task."""
    commit_result: CommitResult
    tpe: str = "commit"


class ErrorEvent(BaseModel):
    """Represents an error during the process."""
    message: str

class RetryEvent(BaseModel):
    """Represents a retry event."""
    message: str    

class WindowLengthChangeEvent(BaseModel):
    """Represents the token usage in the conversation window."""
    tokens_used: int
    pruned_tokens_used: int
    conversation_round: int

# Base event class for all agent events
class AgentEvent(BaseModel):
    """Base class for all agent events."""
    pass

# Metadata for token usage tracking
class AgentSingleOutputMeta(BaseModel):
    """Metadata for tracking token usage for a single LLM output."""
    model_name: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float

# Pull Request Result type - compatible with PRResult from pull_requests module
class PullRequestResult(BaseModel):
    """Pull Request operation result for agentic edit events"""
    success: bool
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    platform: Optional[str] = None  # Using str instead of PlatformType for flexibility
    raw_response: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None
    
    @classmethod
    def from_pr_result(cls, pr_result) -> "PullRequestResult":
        """Create PullRequestResult from PRResult instance"""
        if pr_result is None:
            return cls(success=False, error_message="No PR result provided")
        
        return cls(
            success=pr_result.success,
            pr_number=pr_result.pr_number,
            pr_url=pr_result.pr_url,
            pr_id=pr_result.pr_id,
            error_message=pr_result.error_message,
            error_code=pr_result.error_code,
            platform=str(pr_result.platform) if pr_result.platform else None,
            raw_response=pr_result.raw_response,
            retry_after=pr_result.retry_after
        )

class PullRequestEvent(BaseModel):
    """Represents a Pull Request creation event."""
    pull_request_result: PullRequestResult

# Deprecated: Will be replaced by specific Event types
# class PlainTextOutput(BaseModel):
#     text: str


# Mapping from tool tag names to Pydantic models
TOOL_MODEL_MAP: Dict[str, Type[BaseTool]] = {
    "execute_command": ExecuteCommandTool,
    "read_file": ReadFileTool,
    "write_to_file": WriteToFileTool,
    "replace_in_file": ReplaceInFileTool,
    "search_files": SearchFilesTool,
    "list_files": ListFilesTool,
    "list_code_definition_names": ListCodeDefinitionNamesTool,
    "ask_followup_question": AskFollowupQuestionTool,
    "attempt_completion": AttemptCompletionTool,
    "plan_mode_respond": PlanModeRespondTool,
    "use_mcp_tool": UseMcpTool,
    "use_rag_tool": UseRAGTool,
    "run_named_subagents": RunNamedSubagentsTool,
    "todo_read": TodoReadTool,
    "todo_write": TodoWriteTool,
    "ac_mod_read": ACModReadTool,
    "ac_mod_write": ACModWriteTool,
    "ac_mod_list": ACModListTool,
    "count_tokens": CountTokensTool,
    "extract_to_text": ExtractToTextTool,
    "session_start": SessionStartTool,
    "session_interactive": SessionInteractiveTool,
    "session_stop": SessionStopTool,
    "conversation_message_ids_write": ConversationMessageIdsWriteTool,
    "conversation_message_ids_read": ConversationMessageIdsReadTool,
    "background_task": BackgroundTaskTool,
    "web_crawl": WebCrawlTool,
    "web_search": WebSearchTool,
}

class FileChangeEntry(BaseModel):
    type: str  # 'added' or 'modified'
    diffs: List[str] = []
    content: Optional[str] = None


class AgenticEditRequest(BaseModel):
    user_input: str


class FileOperation(BaseModel):
    path: str
    operation: str  # e.g., "MODIFY", "REFERENCE", "ADD", "REMOVE"
class MemoryConfig(BaseModel):
    """
    A model to encapsulate memory configuration and operations.
    """

    memory: Dict[str, Any]
    save_memory_func: SkipValidation[Callable]

    class Config:
        arbitrary_types_allowed = True


class CommandConfig(BaseModel):
    coding: SkipValidation[Callable]
    chat: SkipValidation[Callable]
    add_files: SkipValidation[Callable]
    remove_files: SkipValidation[Callable]
    index_build: SkipValidation[Callable]
    index_query: SkipValidation[Callable]
    list_files: SkipValidation[Callable]
    ask: SkipValidation[Callable]
    revert: SkipValidation[Callable]
    commit: SkipValidation[Callable]
    help: SkipValidation[Callable]
    exclude_dirs: SkipValidation[Callable]
    summon: SkipValidation[Callable]
    design: SkipValidation[Callable]
    mcp: SkipValidation[Callable]
    models: SkipValidation[Callable]
    lib: SkipValidation[Callable]
    execute_shell_command: SkipValidation[Callable]
    generate_shell_command: SkipValidation[Callable]
    conf_export: SkipValidation[Callable]
    conf_import: SkipValidation[Callable]
    index_export: SkipValidation[Callable]
    index_import: SkipValidation[Callable]
    exclude_files: SkipValidation[Callable]

class AgenticEditConversationConfig(BaseModel):     
    conversation_name: Optional[str] = "current"
    conversation_id: Optional[str] = None 
    action: Optional[str] = None
    query: Optional[str] = None
    pull_request: bool = False
    pre_commit: bool = False
    post_commit: bool = False
    is_sub_agent: bool = False
