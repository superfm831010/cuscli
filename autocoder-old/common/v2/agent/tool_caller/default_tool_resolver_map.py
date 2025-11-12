"""
Default Tool Resolver Map

定义默认的工具解析器映射，集中管理所有工具类型和解析器类的对应关系。
"""

from typing import Dict, Type
from autocoder.common.v2.agent.agentic_edit_types import (
    BaseTool,
    ExecuteCommandTool, ReadFileTool, WriteToFileTool, ReplaceInFileTool,
    SearchFilesTool, ListFilesTool, ListCodeDefinitionNamesTool,
    AskFollowupQuestionTool, AttemptCompletionTool, PlanModeRespondTool,
    UseMcpTool, UseRAGTool, RunNamedSubagentsTool, ACModReadTool, ACModWriteTool, ACModListTool,
    TodoReadTool, TodoWriteTool, CountTokensTool, ExtractToTextTool, SessionStartTool,
    SessionInteractiveTool, SessionStopTool, ConversationMessageIdsWriteTool,
    ConversationMessageIdsReadTool, BackgroundTaskTool, WebCrawlTool, WebSearchTool
)
from autocoder.common.v2.agent.agentic_edit_tools import (
    BaseToolResolver,
    ExecuteCommandToolResolver, ReadFileToolResolver, WriteToFileToolResolver,
    ReplaceInFileToolResolver, SearchFilesToolResolver, ListFilesToolResolver,
    ListCodeDefinitionNamesToolResolver, AskFollowupQuestionToolResolver,
    AttemptCompletionToolResolver, PlanModeRespondToolResolver, UseMcpToolResolver,
    UseRAGToolResolver, ACModReadToolResolver, ACModWriteToolResolver, 
    ACModListToolResolver, TodoReadToolResolver, TodoWriteToolResolver, 
    CountTokensToolResolver, ExtractToTextToolResolver, SessionStartToolResolver, SessionInteractiveToolResolver, 
    SessionStopToolResolver, BackgroundTaskToolResolver
)
from autocoder.common.v2.agent.agentic_edit_tools.run_named_subagents_tool_resolver import RunNamedSubagentsToolResolver
from autocoder.common.v2.agent.agentic_edit_tools.conversation_message_ids_write_tool_resolver import ConversationMessageIdsWriteToolResolver
from autocoder.common.v2.agent.agentic_edit_tools.conversation_message_ids_read_tool_resolver import ConversationMessageIdsReadToolResolver
from autocoder.common.v2.agent.agentic_edit_tools.web_crawl_tool_resolver import WebCrawlToolResolver
from autocoder.common.v2.agent.agentic_edit_tools.web_search_tool_resolver import WebSearchToolResolver
from autocoder.common.v2.agent.agentic_edit_tools.extract_to_text_tool_resolver import ExtractToTextToolResolver


def get_default_tool_resolver_map() -> Dict[Type[BaseTool], Type[BaseToolResolver]]:
    """
    获取默认的工具解析器映射
    
    Returns:
        Dict[Type[BaseTool], Type[BaseToolResolver]]: 工具类型到解析器类的映射
    """
    return {
        ExecuteCommandTool: ExecuteCommandToolResolver,
        ReadFileTool: ReadFileToolResolver,
        WriteToFileTool: WriteToFileToolResolver,
        ReplaceInFileTool: ReplaceInFileToolResolver,
        SearchFilesTool: SearchFilesToolResolver,
        ListFilesTool: ListFilesToolResolver,
        ListCodeDefinitionNamesTool: ListCodeDefinitionNamesToolResolver,
        ACModReadTool: ACModReadToolResolver,
        ACModWriteTool: ACModWriteToolResolver,
        ACModListTool: ACModListToolResolver,
        AskFollowupQuestionTool: AskFollowupQuestionToolResolver,
        AttemptCompletionTool: AttemptCompletionToolResolver,  # Will stop the loop anyway
        PlanModeRespondTool: PlanModeRespondToolResolver,
        UseMcpTool: UseMcpToolResolver,
        UseRAGTool: UseRAGToolResolver,
        RunNamedSubagentsTool: RunNamedSubagentsToolResolver,
        TodoReadTool: TodoReadToolResolver,
        TodoWriteTool: TodoWriteToolResolver,
        CountTokensTool: CountTokensToolResolver,
        ExtractToTextTool: ExtractToTextToolResolver,
        SessionStartTool: SessionStartToolResolver,
        SessionInteractiveTool: SessionInteractiveToolResolver,
        SessionStopTool: SessionStopToolResolver,
        ConversationMessageIdsWriteTool: ConversationMessageIdsWriteToolResolver,
        ConversationMessageIdsReadTool: ConversationMessageIdsReadToolResolver,
        BackgroundTaskTool: BackgroundTaskToolResolver,
        WebCrawlTool: WebCrawlToolResolver,
        WebSearchTool: WebSearchToolResolver
    }


# 导出默认映射，供模块级别直接使用
DEFAULT_TOOL_RESOLVER_MAP = get_default_tool_resolver_map() 