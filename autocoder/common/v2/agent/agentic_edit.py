import json
import os
import time
import byzerllm
from typing import List, Dict, Any, Union, Optional, Tuple, Type, Generator
from loguru import logger
from pathlib import Path
import re
import xml.sax.saxutils
from copy import deepcopy
from autocoder.common.printer import Printer

from autocoder.common import AutoCoderArgs, detect_env, shells
from autocoder.common.global_cancel import global_cancel, CancelRequestedException
from autocoder.common.mcp_tools.server import get_mcp_server, McpServerInfoRequest
from autocoder.common.utils_code_auto_generate import (
    stream_chat_with_continue,
)  # Added import
from autocoder.common.agents.agent_manager import AgentManager
from autocoder.common.conversations.get_conversation_manager import (
    get_conversation_manager,
)
from autocoder.common.conversations.llm_stats_models import (
    LLMCallMetadata,
    create_llm_metadata_from_token_usage_event,
)
from autocoder.common.pruner.agentic_conversation_pruner import (
    AgenticConversationPruner,
)

from autocoder.common.save_formatted_log import save_formatted_log
from autocoder.common.v2.agent.agentic_edit_types import FileChangeEntry
from autocoder.utils.llms import get_single_llm

from autocoder.common.agent_events import (
    create_event_system,
    EventEmitterConfig,
    EventContext,
    EventFactory,
)
from autocoder.common.agent_hooks import HookManager

from autocoder.common.file_checkpoint.manager import (
    FileChangeManager as CheckpointFileChangeManager,
)
from autocoder.linters.normal_linter import NormalLinter
from autocoder.compilers.normal_compiler import NormalCompiler

from autocoder.common.llm_friendly_package import LLMFriendlyPackageManager
from autocoder.common.tools_manager import ToolsManager
from autocoder.common.rulefiles import get_rules_for_conversation
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditRequest,
    ToolResult,
    BaseTool,
    AttemptCompletionTool,
    PlanModeRespondTool,
    TOOL_MODEL_MAP,
    # Event Types
    LLMOutputEvent,
    LLMThinkingEvent,
    ToolCallEvent,
    RetryEvent,
    ToolResultEvent,
    CompletionEvent,
    PlanModeRespondEvent,
    ErrorEvent,
    TokenUsageEvent,
    WindowLengthChangeEvent,
    ConversationIdEvent,
    AgenticEditConversationConfig,
    ConversationAction,
)
from autocoder.common.rag_manager import RAGManager
from .agentic_edit_change_manager import AgenticEditChangeManager
from .tool_caller import ToolCaller
from autocoder.common.tokens import count_string_tokens as count_tokens
from autocoder.common.wrap_llm_hint.utils import append_hint_to_text
from autocoder.common.shell_commands import get_background_process_notifier
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common.v2.agent.agentic_callbacks import (
    AgenticCallBacks,
    AgenticCallbackPoint,
    AgenticContext,
)


class AgenticEdit:
    def __init__(
        self,
        llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM],
        args: AutoCoderArgs,
        custom_system_prompt: Optional[str] = None,
        conversation_config: Optional[AgenticEditConversationConfig] = None,
        cancel_token: Optional[str] = None,
    ):
        self.callbacks = AgenticCallBacks()
        self.llm = llm
        self.context_prune_llm = get_single_llm(
            args.context_prune_model or args.model, product_mode=args.product_mode
        )
        self.args = args
        self.custom_system_prompt = custom_system_prompt
        self.printer = Printer()

        # Initialize AutoCoderArgs parser for flexible parameter parsing
        self.args_parser = AutoCoderArgsParser()
        # Removed self.tools and self.result_manager
        # Removed self.max_iterations
        # Note: This might need updating based on the new flow

        self.current_conversations = []
        self.cancel_token = cancel_token

        taget_source_dir = args.source_dir or os.getcwd()

        self.base_persist_dir = os.path.join(
            taget_source_dir, ".auto-coder", "plugins", "chat-auto-coder"
        )

        self.checkpoint_manager = CheckpointFileChangeManager(
            project_dir=taget_source_dir,
            backup_dir=os.path.join(taget_source_dir, ".auto-coder", "checkpoint"),
            store_dir=os.path.join(taget_source_dir, ".auto-coder", "checkpoint_store"),
            max_history=50,
        )
        self.linter = NormalLinter(taget_source_dir, verbose=False)
        self.compiler = NormalCompiler(taget_source_dir, verbose=False)

        # Initialize agent events and hooks system
        self._init_event_system()

        self.mcp_server_info = ""
        try:
            self.mcp_server = get_mcp_server()
            mcp_server_info_response = self.mcp_server.send_request(
                McpServerInfoRequest(
                    model=args.inference_model or args.model,
                    product_mode=args.product_mode,
                )
            )
            self.mcp_server_info = mcp_server_info_response.result
        except Exception as e:
            logger.error(f"Error getting MCP server info: {str(e)}")

        # 初始化 RAG 管理器并获取服务器信息
        self.rag_server_info = ""
        try:
            self.rag_manager = RAGManager(args)
            if self.rag_manager.has_configs():
                self.rag_server_info = self.rag_manager.get_config_info()
                logger.info(
                    f"RAG manager initialized with {len(self.rag_manager.get_all_configs())} configurations"
                )
            else:
                self.rag_server_info = "No available RAG server configurations found"
                logger.info("No RAG configurations found")
        except Exception as e:
            logger.error(f"Error initializing RAG manager: {str(e)}")
            self.rag_manager = None

        # 对话管理器
        self.conversation_config = conversation_config

        if self.conversation_config is None:
            raise ValueError("conversation_config is required")

        self.conversation_manager = get_conversation_manager()

        # Agentic 对话修剪器
        self.agentic_pruner = AgenticConversationPruner(
            args=args,
            llm=self.context_prune_llm,
            conversation_id=self.conversation_config.conversation_id,
        )

        # 初始化变更管理器
        self.change_manager = AgenticEditChangeManager(self)

        # 初始化工具调用器，集成插件系统
        self.tool_caller = ToolCaller(agent=self, args=self.args, enable_plugins=True)
        logger.info("Tool caller initialized with plugin system")

    def _get_parsed_safe_zone_tokens(self) -> int:
        """
        解析 conversation_prune_safe_zone_tokens 参数，支持多种格式

        Returns:
            解析后的 token 数量
        """
        return self.args_parser.parse_conversation_prune_safe_zone_tokens(
            self.args.conversation_prune_safe_zone_tokens, self.args.code_model
        )

    @byzerllm.prompt()
    def generate_library_docs_prompt(
        self, libraries_with_paths: List[Dict[str, str]], docs_content: str
    ) -> Dict[str, Any]:
        """
        ====

        THIRD-PARTY LIBRARY DOCUMENTATION

        The following documentation is for third-party libraries that are available in this project. Use this information to understand the capabilities and APIs of these libraries when they are relevant to the user's task.

        Libraries included: {{ libraries_list }}

        <library_documentation>
        {{ combined_docs }}
        </library_documentation>

        You should reference this documentation when:
        1. The user asks about functionality that might be provided by these libraries
        2. You need to implement features that could leverage these library capabilities
        3. You want to suggest using library functions instead of implementing from scratch
        4. You need to understand the API or usage patterns of these libraries
        ====
        """
        # 格式化库列表，包含名称和路径
        libraries_list = []
        for lib_info in libraries_with_paths:
            name = lib_info.get("name", "")
            path = lib_info.get("path", "Path not found")
            libraries_list.append(f"{name} (路径: {path})")

        return {
            "libraries_list": ", ".join(libraries_list),
            "combined_docs": docs_content,
        }

    def record_file_change(
        self,
        file_path: str,
        change_type: str,
        diff: Optional[str] = None,
        content: Optional[str] = None,
    ):
        """记录单个文件的变更信息，委托给变更管理器处理"""
        return self.change_manager.record_file_change(
            file_path, change_type, diff, content
        )

    def get_all_file_changes(self) -> Dict[str, FileChangeEntry]:
        """获取当前记录的所有文件变更信息，委托给变更管理器处理"""
        return self.change_manager.get_all_file_changes()

    # Tool Caller Plugin Management Methods
    def register_tool_plugin(self, plugin) -> bool:
        """注册工具调用插件"""
        return self.tool_caller.register_plugin(plugin)

    def unregister_tool_plugin(self, plugin_name: str) -> bool:
        """注销工具调用插件"""
        return self.tool_caller.unregister_plugin(plugin_name)

    def enable_tool_plugin(self, plugin_name: str) -> bool:
        """启用工具调用插件"""
        return self.tool_caller.enable_plugin(plugin_name)

    def disable_tool_plugin(self, plugin_name: str) -> bool:
        """禁用工具调用插件"""
        return self.tool_caller.disable_plugin(plugin_name)

    def set_tool_plugins_enabled(self, enabled: bool) -> None:
        """设置工具插件系统启用状态"""
        self.tool_caller.set_plugins_enabled(enabled)

    def get_tool_caller_stats(self) -> Dict[str, Any]:
        """获取工具调用器统计信息"""
        return self.tool_caller.get_stats()

    def get_tool_plugin_status(self) -> Dict[str, Any]:
        """获取工具插件状态"""
        return self.tool_caller.get_plugin_status()

    @byzerllm.prompt()
    def _analyze(self, request: AgenticEditRequest) -> str:
        """
         {{system_prompt}}

         ====

         TOOL USE

         You have access to a set of tools that are executed upon the user's approval. You can use one tool per message, and will receive the result of that tool use in the user's response. You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.

         # Tool Use Formatting

         Tool use is formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. Here's the structure:

         <tool_name>
         <parameter1_name>value1</parameter1_name>
         <parameter2_name>value2</parameter2_name>
         ...
         </tool_name>

         For example:

         <read_file>
         <path>src/main.js</path>
         </read_file>

         Always adhere to this format for the tool use to ensure proper parsing and execution.


         # Tools

         ## execute_command
         Description: Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does.

         **Batch Command Execution**: This tool also supports executing multiple commands in a single call using JSON, YAML, or newline-separated formats. By default, multiple commands run in parallel for better performance. Use serial execution when commands depend on each other.
         **Background Command Execution**: This tool also supports running commands in the background. Set the background parameter to 'true' for long-running processes (e.g., 'npm run dev') to keep the session responsive while the process continues running.
         **Sub Agent Execution**: You can also delegate tasks to sub-agents using pipe syntax like `echo 'task description' | auto-coder.run --model {{ current_model }} --is-sub-agent` or `cat task_file.txt | auto-coder.run --model {{ current_model }} --is-sub-agent`. The --is-sub-agent flag indicates this agent is called by another agent rather than directly by a human.

         For command chaining, use the appropriate chaining syntax for the user's shell. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Commands will be executed in the current working directory: {{current_project}}

         Parameters:
         - command: (required) The CLI command to execute. This can be:
           - A single command string
           - A JSON array of commands: ["cmd1", "cmd2", "cmd3"] or A JSON object with mode specification: {"mode": "serial", "cmds": ["cmd1", "cmd2", "cmd3"]}
           - A YAML format with mode specification:
             mode: serial  # or parallel
             cmds:
               - cmd1
               - cmd2
           - Multiple commands separated by newlines
           - Commands with a mode comment: # serial or # parallel as the first line
         - requires_approval: (required) A boolean indicating whether this command requires explicit user approval before execution in case the user has auto-approve mode enabled. Set to 'true' for potentially impactful operations like installing/uninstalling packages, deleting/overwriting files, system configuration changes, network operations, or any commands that could have unintended side effects. Set to 'false' for safe operations like reading files/directories, running development servers, building projects, and other non-destructive operations.
         - timeout: (optional) Timeout for the command execution in seconds. Default is 60 seconds. For batch commands, this is the overall timeout when using parallel mode, or distributed per-command in serial mode.
         - background: (optional) Whether to run the command in the background. Default is false. Set to 'true' for long-running processes (e.g., 'npm run dev') to keep the session responsive while the process continues running.

         Usage:
         <execute_command>
         <command>Your command here</command>
         <requires_approval>true or false</requires_approval>
         <timeout>60</timeout>
         <background>false</background>
         </execute_command>


         ## ac_mod_read
         Description: Request to retrieve information about an AC Module - a directory marked with a .ac.mod.md file that represents an independent functional system with token count under model window size and language-agnostic design. The .ac.mod.md file contains usage examples, core components, component dependencies, references to other AC modules, and testing information. Use this instead of read_file for clearer AC module operations.
         Parameters:
         - path: (required) The AC Module directory path (directory containing .ac.mod.md file).
         Usage:
         <ac_mod_read>
         <path>relative/or/absolute/ac/module/path</path>
         </ac_mod_read>

         ## ac_mod_list
         Description: Request to list all directories containing .ac.mod.md files (AC Modules) in the project. This tool helps you discover available AC Modules before using ac_mod_read to examine specific modules. It recursively searches for AC modules and provides information about each module including its title, file count, and size.
         Parameters:
         - path: (optional) The root directory path to search for AC modules. If not provided, searches from the project root directory.
         Usage:
         <ac_mod_list>
         </ac_mod_list>

         or with specific path:

         <ac_mod_list>
         <path>src/some/directory</path>
         </ac_mod_list>

         ## ac_mod_write
         Description: Request to create or update an AC Module's .ac.mod.md file. This tool allows you to define a new AC Module or modify an existing one by writing to its .ac.mod.md file. The file contains usage examples, core components, component dependencies, references to other AC modules, and testing information.
         Parameters:
         - path: (required) The AC Module directory path (directory where .ac.mod.md file should be created or updated).
         - diff: (required) One or more SEARCH/REPLACE blocks following this exact format:

         <<<<<<< SEARCH
         [exact content to find]
         =======
         [new content to replace with]
         >>>>>>> REPLACE

         This tool have the same usage as the replace_in_file tool, but it is used to update the AC Module's .ac.mod.md file.

         Usage:

         <ac_mod_write>
         <path>relative/or/absolute/ac/module/path</path>
         <diff>
         Search and replace blocks here
         </diff>
         </ac_mod_write>

         ## read_file
         Description: Request to read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file you do not know the contents of, for example to analyze code, review text files, or extract information from configuration files. Automatically extracts raw text from PDF and DOCX files. May not be suitable for other types of binary files, as it returns the raw content as a string.

         **IMPORTANT AC Module Check**: Before reading any file, first check if the file is located within an AC Module directory (a directory containing a .ac.mod.md file). If it is, you MUST read the module's .ac.mod.md file first using the ac_mod_read tool to understand the module's purpose, structure, and dependencies before deciding whether to read the specific file. This ensures you understand the full context and can determine if the file reading is necessary.

         Parameters:
         - path: (required) The path of the file to read (relative to the current working directory {{ current_project }})
         - start_line: (optional) Starting line number (1-based) to read from. If specified, only reads from this line onwards.
         - end_line: (optional) Ending line number (1-based, inclusive) to read until. If specified, only reads up to this line.
         - query: (optional) Try your best to describe what you want from the file. This will help the tool extract the most relevant content to reduce the number of tokens used.
         Usage:
         <read_file>
         <path>File path here</path>
         <start_line>1</start_line>
         <end_line>100</end_line>
         <query>Query here</query>
         </read_file>

         ## write_to_file
         Description: Request to write content to a file at the specified path. Supports two modes:
         - write (default): Overwrite the entire file with the provided content. If the file doesn't exist, it will be created.
         - append: Append the provided content to the end of the file. If the file doesn't exist, it will be created and the content written.
         This tool will automatically create any directories needed to write the file.
         Parameters:
         - path: (required) The path of the file to write to (relative to the current working directory {{ current_project }})
         - content: (required) The content to write.
         - mode: (optional) "write" or "append". Defaults to "write".
         Guidance:
         - In write mode: ALWAYS provide the COMPLETE intended content of the file, without any truncation or omissions.
         - In append mode: Provide ONLY the content to append; do not repeat existing content.
         Usage:
         <write_to_file>
         <path>File path here</path>
         <mode>append</mode>
         <content>
         Your file content here
         </content>
         </write_to_file>

         ## replace_in_file
         Description: Modify existing files using SEARCH/REPLACE blocks. Supports single file or multiple files in one operation.

         Parameters:
         - path: (required) File path relative to {{ current_project }}, or "*" for multiple files
         - diff: (required) SEARCH/REPLACE content blocks
         - fence_0: (optional) Opening fence marker, defaults to "```"
         - fence_1: (optional) Closing fence marker, defaults to "```"

         **SEARCH/REPLACE Block Format:**
         <<<<<<< SEARCH
         [exact content to find]
         =======
         [new content to replace with]
         >>>>>>> REPLACE

         **Multiple Files Format (when path="*"):**
         ```
         ##File: path/to/file.ext
         <<<<<<< SEARCH
         [exact content to find]
         =======
         [new content to replace with]
         >>>>>>> REPLACE
         ```

         ```
         ##File: path/to/file2.ext
         <<<<<<< SEARCH
         [exact content to find]
         =======
         [new content to replace with]
         >>>>>>> REPLACE
         ```

         **Important Rules:**
         - No extra '=======' after REPLACE
         - Max 1 newline before SEARCH or after REPLACE
         - Use </diff> not </div> to close XML tags
         - Use ``` to open and close the code block with file name when in multiple files mode


         Usage:
         **Single File Mode**:
         <replace_in_file>
         <path>File path here</path>
         <diff>
         Search and replace blocks here
         </diff>
         </replace_in_file>

         **Multiple Files Mode**:
         <replace_in_file>
         <path>*</path>
         <fence_0>```</fence_0>
         <fence_1>```</fence_1>
         <diff>
         Editblock format with multiple files here
         </diff>
         </replace_in_file>

         ## search_files
         Description: Request to perform a regex search across files in a specified directory, providing context-rich results. This tool searches for patterns or specific content across multiple files, displaying each match with encapsulating context.
         Parameters:
         - path: (required) The path of the directory to search in (relative to the current working directory {{ current_project }}). This directory will be recursively searched.
         - regex: (required) The target regular expression pattern used for full-text matching across all files in the specified directory. Uses Regex syntax.
         - file_pattern: (optional) Glob pattern to filter files (e.g., '*.ts' for TypeScript files). If not provided, it will search all files (*). We encourage you to use this parameter to filter files so that you can narrow down the search results.
         Usage:
         <search_files>
         <path>Directory path here</path>
         <regex>Your regex pattern for full-text matching across all files in the specified directory</regex>
         <file_pattern>file pattern here (optional)</file_pattern>
         </search_files>

         ## list_files
         Description: Request to list files and directories within the specified directory. If recursive is true, it will list all files and directories recursively. If recursive is false or not provided, it will only list the top-level contents. Do not use this tool to confirm the existence of files you may have created, as the user will let you know if the files were created successfully or not.
         Parameters:
         - path: (required) The path of the directory to list contents for (relative to the current working directory {{ current_project }})
         - recursive: (optional) Whether to list files recursively. Use true for recursive listing, false or omit for top-level only.
         Usage:
         <list_files>
         <path>Directory path here</path>
         <recursive>true or false (optional)</recursive>
         </list_files>

         ## list_code_definition_names
         Description: Request to list definition names (classes, functions, methods, etc.) used in source code files at the top level of the specified directory. This tool provides insights into the codebase structure and important constructs, encapsulating high-level concepts and relationships that are crucial for understanding the overall architecture.
         Parameters:
         - path: (required) The path of the directory (relative to the current working directory {{ current_project }}) to list top level source code definitions for.
         Usage:
         <list_code_definition_names>
         <path>Directory path here</path>
         </list_code_definition_names>

         ## ask_followup_question
         Description: Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.
         Parameters:
         - question: (required) The question to ask the user. This should be a clear, specific question that addresses the information you need.
         - options: (optional) An array of 2-5 options for the user to choose from. Each option should be a string describing a possible answer. You may not always need to provide options, but it may be helpful in many cases where it can save the user from having to type out a response manually. IMPORTANT: NEVER include an option to toggle to Act mode, as this would be something you need to direct the user to do manually themselves if needed.
         Usage:
         <ask_followup_question>
         <question>Your question here</question>
         <options>
         Array of options here (optional), e.g. ["Option 1", "Option 2", "Option 3"]
         </options>
         </ask_followup_question>

         ## todo_read
         Description: Request to read the current todo list for the session. This tool helps you track progress, organize complex tasks, and understand the current status of ongoing work. Use this tool proactively to stay aware of task progress and demonstrate thoroughness.
         Parameters:
         - No parameters required
         Usage:
         <todo_read>
         </todo_read>

         ## todo_write
         Description: Request to create and manage a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user. It also helps the user understand the progress of the task and overall progress of their request. Use this tool proactively for complex multi-step tasks, when explicitly requested by the user, or when you need to organize multiple operations.
         Parameters:
         - action: (required) The action to perform: 'create' (create new todo list), 'add_task' (add single task), 'update' (update existing task), 'mark_progress' (mark task as in progress), 'mark_completed' (mark task as completed)
         - task_id: (optional) The ID of the task to update (required for update, mark_progress, mark_completed actions)
         - content: (optional) The task content or description (required for create, add_task actions)
         - priority: (optional) Task priority level: 'high', 'medium', 'low' (default: 'medium')
         - status: (optional) Task status: 'pending', 'in_progress', 'completed' (default: 'pending')
         - notes: (optional) Additional notes or details about the task
         Usage:
         <todo_write>
         <action>create</action>
         <content>
         <task>Read the configuration file</task>
         <task>Update the database settings</task>
         <task>Test the connection</task>
         <task>Deploy the changes</task>
         </content>
         <priority>high</priority>
         </todo_write>

         ## attempt_completion
         Description: After each tool use, the user will respond with the result of that tool use, i.e. if it succeeded or failed, along with any reasons for failure. Once you've received the results of tool uses and can confirm that the task is complete, use this tool to present the result of your work to the user. Optionally you may provide a CLI command to showcase the result of your work. The user may respond with feedback if they are not satisfied with the result, which you can use to make improvements and try again.
         IMPORTANT NOTE: This tool CANNOT be used until you've confirmed from the user that any previous tool uses were successful. Failure to do so will result in code corruption and system failure. Before using this tool, you must ask yourself in <thinking></thinking> tags if you've confirmed from the user that any previous tool uses were successful. If not, then DO NOT use this tool.
         Parameters:
         - result: (required) The result of the task. Formulate this result in a way that is final and does not require further input from the user. Don't end your result with questions or offers for further assistance.
         - command: (optional) A CLI command to execute to show a live demo of the result to the user. For example, use `open index.html` to display a created html website, or `open localhost:3000` to display a locally running development server. But DO NOT use commands like `echo` or `cat` that merely print text. This command should be valid for the current operating system. Ensure the command is properly formatted and does not contain any harmful instructions.
         Usage:
         <attempt_completion>
         <result>
         Your final result description here
         </result>
         <command>Command to demonstrate result (optional)</command>
         </attempt_completion>

         ## count_tokens
         Description: Request to count tokens in files or directories. This tool analyzes the token count for individual files or entire directories, providing detailed statistics about file sizes, token distribution, and summary information. It's useful for understanding the scope of code changes, analyzing codebase size, and tracking token usage across different file types.
         Parameters:
         - path: (required) The path of the file or directory to analyze (relative to the current working directory {{ current_project }})
         - recursive: (optional) Whether to recursively count tokens in subdirectories. Default is true.
         - include_summary: (optional) Whether to include a detailed summary with statistics by file type and top files by token count. Default is true.
         Usage:
         <count_tokens>
         <path>File or directory path here</path>
         <recursive>true or false (optional)</recursive>
         <include_summary>true or false (optional)</include_summary>
         </count_tokens>

         ## extract_to_text
         Description: Extract text content from various file formats (PDF, DOCX, PPTX, plain text) or URLs and save it as a plain text file. This tool is particularly useful for preparing large documents for line range processing by AI models, enabling efficient text translation, analysis, or other operations on big files. It supports downloading files from URLs and handles multiple document formats.
         Parameters:
         - source_path: (required) The source file path or URL to extract text from. Can be a local file path (PDF, DOCX, PPTX, TXT) or a web URL pointing to a document.
         - target_path: (required) The target file path where the extracted text will be saved. The directory will be created automatically if it doesn't exist.
         Usage:
         <extract_to_text>
         <source_path>path/to/document.pdf or https://example.com/document.pdf</source_path>
         <target_path>path/to/extracted_text.txt</target_path>
         </extract_to_text>

         ## session_start
         Description: Request to start an interactive command session. This tool creates a persistent interactive session that can be used to run commands that require real-time input/output, such as interactive Python shells, database CLIs, or other command-line tools that maintain state between commands. Use this for commands that expect user interaction or maintain REPL state. Determine interactivity based on your knowledge, web search, or MCP/RAG tools - for example, `python -i` is interactive while `python script.py` typically is not (unless the script contains input() calls).
         Parameters:
         - command: (required) The command to execute interactively (e.g., "python -i", "mysql -u root", "node")
         - timeout: (optional) Session timeout in seconds. Default is 60 seconds.
         - cwd: (optional) Working directory for the session. Uses current directory if not specified.
         - env: (optional) Environment variables as a JSON object (e.g., {"PATH": "/usr/bin", "DEBUG": "true"})
         Usage:
         <session_start>
         <command>python -i</command>
         <timeout>300</timeout>
         <cwd>./my_project</cwd>
         </session_start>

         ## session_interactive
         Description: Request to send input to an active interactive session and read its output. Use this to interact with a session that was previously started with session_start.
         Parameters:
         - session_id: (required) The session ID returned from session_start
         - input: (required) The input to send to the session (usually ending with \n for commands)
         - read_timeout: (optional) Time to wait for output in seconds. Default is 2 seconds.
         - max_bytes: (optional) Maximum bytes to read from output. Default is 40960 bytes.
         - expect_prompt: (optional) Whether to wait for a prompt pattern before returning. Default is false. Set to true for interactive shells/interpreters.
         - prompt_regex: (optional) Regular expression to match prompt. For example Python is '>>> ?$' and shell prompt might be '\\$ ?$'.
         Usage:
         <session_interactive>
         <session_id>your-session-id-here</session_id>
         <input>print("Hello World")\n</input>
         <read_timeout>3</read_timeout>
         <expect_prompt>true</expect_prompt>
         <prompt_regex>>>> ?$</prompt_regex>
         </session_interactive>

         ## session_stop
         Description: Request to stop an active interactive session. This will terminate the session and clean up resources.
         Parameters:
         - session_id: (required) The session ID to stop
         - force: (optional) Whether to force termination. Default is false (graceful termination).
         Usage:
         <session_stop>
         <session_id>your-session-id-here</session_id>
         <force>false</force>
         </session_stop>

         ## conversation_message_ids_write
         Description: Request to write conversation message IDs configuration for pruning. This tool allows you to manage which message IDs should be DELETED during conversation pruning. Message IDs are specified as comma-separated 8-character hexadecimal strings like "9226b3a4,204e1cd8". The action parameter determines how to handle the IDs: create (replace existing), append (add to existing), or delete (remove from existing).
         Parameters:
         - message_ids: (required) Message IDs specification string for messages to DELETE. Format: "9226b3a4,204e1cd8,1f3a5b7c" (comma-separated 8-character hex strings)
         - action: (required) Action to perform: "create" (replace existing configuration), "append" (add to existing), or "delete" (remove from existing)
         Usage:
         <conversation_message_ids_write>
         <message_ids>9226b3a4,204e1cd8</message_ids>
         <action>create</action>
         </conversation_message_ids_write>

         ## conversation_message_ids_read
         Description: Request to read existing conversation message IDs configuration for the current conversation. This tool shows you what message IDs are currently configured for DELETION during pruning, if any. It provides detailed information about the configured message IDs, statistics, and settings.
         Parameters: None (uses current conversation ID automatically)
         Usage:
         <conversation_message_ids_read>
         </conversation_message_ids_read>

         ## background_task
         Description: Request to manage background tasks (background commands and background sub agents). This unified tool supports listing, monitoring, cleaning up, and terminating background tasks through different actions.
         Parameters:
         - action: (required) The operation to perform: "list", "monitor", "cleanup", "kill"

         For "list" action:
         - show_completed: (optional) Whether to show completed tasks. Default is false.
         - task_type: (optional) Filter by task type: "command", "subagent", or None for all types.

         For "monitor" action:
         - process_uniq_id: (required) Process unique ID to monitor. Alternative to task_id and pid.
         - task_id: (optional) Task ID to monitor. Alternative to pid.
         - pid: (optional) Process ID to monitor. Alternative to task_id.
         Note: Use whichever identifier was returned by the previous task execution.
         - lines: (optional) Number of output lines to show. Default is 100.
         - output_type: (optional) Type of output to show: "stdout", "stderr", or "both". Default is "both".

         For "cleanup" action:
         - status_filter: (optional) Filter by status: "completed", "failed", or None for all ended tasks.
         - older_than_minutes: (optional) Only clean up tasks completed more than this many minutes ago.
         - task_ids: (optional) List of specific task IDs to clean up.

         For "kill" action:
         - task_id: (optional) Task ID to terminate. Alternative to pid or pids.
         - pid: (optional) Process ID to terminate. Alternative to task_id.
         - pids: (optional) List of process IDs to terminate in batch.
         - force: (optional) Whether to force kill (SIGKILL) vs graceful termination (SIGTERM). Default is false.
         - kill_children: (optional) Whether to also kill child processes. Default is true.

         Usage:
         <background_task>
         <action>list</action>
         <show_completed>true</show_completed>
         <task_type>command</task_type>
         </background_task>

         <background_task>
         <action>monitor</action>
         <task_id>task_12345</task_id>
         <lines>50</lines>
         <output_type>both</output_type>
         </background_task>

         <background_task>
         <action>cleanup</action>
         <status_filter>completed</status_filter>
         <older_than_minutes>30</older_than_minutes>
         </background_task>

         <background_task>
         <action>kill</action>
         <task_id>task_12345</task_id>
         <force>false</force>
         <kill_children>true</kill_children>
         </background_task>

         ## run_named_subagents
         Description: Request to run a named subagent with a specific task. This tool allows you to run a named subagent with a specific query.
         Parameters:
         - subagents: (required) The subagents to run.
           - A JSON Array of subagents, each with a name and task: [{"name": "xxx", "task": "task here"}]
           - A YAML format with mode specification
             mode: parallel or serial
             subagents:
                 - name: xxx
                   task: task here
                 - name: xxx
                   task: task here
         - background: (optional) Whether to run the subagents in the background. Default is false. Set to 'true' for long-running processes.
         Usage:
         <run_named_subagents>
         <subagents>
         mode: parallel or serial
         subagents:
             - name: xxx
               task: task here
             - name: xxx
               task: task here
         </subagents>
         <background>false</background>
         </run_named_subagents>

         ## web_search
         Description: Request to search the web using multiple API providers (Firecrawl, Metaso, BochaAI) with concurrent processing. When multiple API keys are configured, the tool will use all available providers concurrently to improve search coverage and reliability. Results are automatically merged, deduplicated, and sorted by relevance.
         Parameters:
         - query: (required) The search query
         - limit: (optional) Number of search results to return. Default is 5.
         - sources: (optional) Comma-separated search source types, e.g., "web,news,images"
         - scrape_options: (optional) JSON string with scrape options, e.g., '{"include_summary": true, "include_sites": "github.com"}'
         - location: (optional) Search location for geo-specific results
         - tbs: (optional) Time filter parameter, e.g., "m" for recent month

         Usage:
         <web_search>
         <query>Python RAG system implementation</query>
         <limit>5</limit>
         <sources>web,news</sources>
         <tbs>m</tbs>
         </web_search>

         ## web_crawl
         Description: Advanced web crawling tool supporting multiple API providers (Firecrawl, Metaso) with intelligent concurrent processing. Features automatic failover, quality comparison, and comprehensive content extraction.
         Parameters:
         - url: (required) The starting URL to crawl
         - limit: (optional) Maximum number of pages to crawl. Default is 10. Use 1 for single-page scraping.
         - scrape_options: (optional) JSON string with advanced scraping options. Examples:
           * Basic: '{"formats": ["markdown", "links"]}'
           * Advanced: '{"formats": ["markdown", "links"], "only_main_content": true, "remove_base64_images": true}'
           * Custom: '{"formats": ["markdown", "html"], "include_tags": ["article", "main"], "exclude_tags": ["nav", "footer"]}'
         - exclude_paths: (optional) Comma-separated path patterns to exclude, e.g., "/api,/admin,/login"
         - include_paths: (optional) Comma-separated path patterns to include, e.g., "/docs,/help,/guide"
         - max_depth: (optional) Maximum crawling depth from the starting URL. Default varies by provider.
         - allow_subdomains: (optional) Whether to allow crawling subdomains, "true" or "false". Default is "false".
         - crawl_entire_domain: (optional) Whether to crawl the entire domain, "true" or "false". Default is "false". (Firecrawl only)

         Usage Examples:

         # Basic single-page scraping with quality content
         <web_crawl>
         <url>https://example.com/article</url>
         <limit>1</limit>
         <scrape_options>{"formats": ["markdown", "links"], "only_main_content": true}</scrape_options>
         </web_crawl>

         # Multi-page documentation crawling
         <web_crawl>
         <url>https://docs.example.com</url>
         <limit>20</limit>
         <scrape_options>{"formats": ["markdown", "links"], "remove_base64_images": true}</scrape_options>
         <include_paths>/docs,/api-reference,/guides</include_paths>
         <exclude_paths>/admin,/login,/dashboard</exclude_paths>
         <max_depth>3</max_depth>
         <allow_subdomains>false</allow_subdomains>
         </web_crawl>

         ## mcp_tool
         Description: Request to execute a tool via the Model Context Protocol (MCP) server. Use this when you need to execute a tool that is not natively supported by the agentic edit tools.
         Parameters:
         - server_name: (optional) The name of the MCP server to use. If not provided, the tool will automatically choose the best server based on the query.
         - tool_name: (optional) The name of the tool to execute. If not provided, the tool will automatically choose the best tool in the selected server based on the query.
         - query: (required) The query to pass to the tool.
         Usage:
         <use_mcp_tool>
         <server_name>xxx</server_name>
         <tool_name>xxxx</tool_name>
         <query>
         Your query here
         </query>
         </use_mcp_tool>

         {%if mcp_server_info %}
         ### MCP_SERVER_LIST
         {{mcp_server_info}}
         {%endif%}

         ## rag_tool
         Description: Request to query the RAG server for information. Use this when you need to query the RAG server for information.
         Parameters:
         - server_name: (required) The url of the RAG server to use.
         - query: (required) The query to pass to the tool.
         Usage:
         <use_rag_tool>
         <server_name>xxx</server_name>
         <query>Your query here</query>
         </use_rag_tool>

         {%if rag_server_info %}
         ### RAG_SERVER_LIST
         {{rag_server_info}}
         {%endif%}

         # Tool Use Examples

         ## Example 1: Requesting to execute a command (run dev server in background)

         <execute_command>
         <command>npm run dev</command>
         <requires_approval>false</requires_approval>
         <background>true</background>
         </execute_command>

         ## Example 1a: Requesting to execute multiple commands in batch

         Parallel execution (default) for independent tasks:
         <execute_command>
         <command>["curl -s https://api.github.com/status", "curl -s https://api.npm.com/ping", "df -h", "free -m"]</command>
         <requires_approval>false</requires_approval>
         <timeout>30</timeout>
         </execute_command>

         <execute_command>
         <command>{"mode":"parallel","cmds":["curl -s https://api.github.com/status", "curl -s https://api.npm.com/ping", "df -h", "free -m"]}</command>
         <requires_approval>false</requires_approval>
         <timeout>30</timeout>
         </execute_command>

         Serial execution for dependent commands:
         <execute_command>
         <command>
         mode: serial
         cmds:
         - npm install
         - npm run lint
         - npm run test
         - npm run build
         </command>
         <requires_approval>false</requires_approval>
         <timeout>300</timeout>
         </execute_command>


         For quick commands with custom timeout:
         <execute_command>
         <command>ls -la</command>
         <requires_approval>false</requires_approval>
         <timeout>10</timeout>
         </execute_command>

         For serial batch execution (YAML format):
         <execute_command>
         <command>
         mode: serial
         cmds:
         - git add .
         - git commit -m "Update feature"
         - git push origin main
         </command>
         <requires_approval>true</requires_approval>
         <timeout>120</timeout>
         </execute_command>

         For simple multi-command (newline-separated - parallel by default):
         <execute_command>
         <command>
         echo "Task 1"
         echo "Task 2"
         echo "Task 3"
         </command>
         <requires_approval>false</requires_approval>
         </execute_command>

         ## Example 2: Requesting to create a new file

         <write_to_file>
         <path>src/frontend-config.json</path>
         <content>
         {
         "apiEndpoint": "https://api.example.com",
         "theme": {
             "primaryColor": "#007bff",
             "secondaryColor": "#6c757d",
             "fontFamily": "Arial, sans-serif"
         },
         "features": {
             "darkMode": true,
             "notifications": true,
             "analytics": false
         },
         "version": "1.0.0"
         }
         </content>
         </write_to_file>

         ## Example 3: Requesting to make targeted edits to a file

         <replace_in_file>
         <path>src/components/App.tsx</path>
         <diff>
         <<<<<<< SEARCH
         import React from 'react';
         =======
         import React, { useState } from 'react';
         >>>>>>> REPLACE

         <<<<<<< SEARCH
         function handleSubmit() {
         saveData();
         setLoading(false);
         }

         =======
         >>>>>>> REPLACE

         <<<<<<< SEARCH
         return (
         <div>
         =======
         function handleSubmit() {
         saveData();
         setLoading(false);
         }

         return (
         <div>
         >>>>>>> REPLACE
         </diff>
         </replace_in_file>

         ## Example 4: Another example of using an MCP tool (where the server name is a unique identifier listed in MCP_SERVER_LIST)

         <use_mcp_tool>
         <server_name>github</server_name>
         <tool_name>create_issue</tool_name>
         <query>ower is octocat, repo is hello-world, title is Found a bug, body is I'm having a problem with this. labels is "bug" and "help wanted",assignees is "octocat"</query>
         </use_mcp_tool>

         ## Example 5: Reading the current todo list

         <todo_read>
         </todo_read>

         ## Example 6: Creating a new todo list for a complex task

         <todo_write>
         <action>create</action>
         <content>
         <task>Analyze the existing codebase structure</task>
         <task>Design the new feature architecture</task>
         <task>Implement the core functionality</task>
         <task>Add comprehensive tests</task>
         <task>Update documentation</task>
         <task>Review and refactor code</task>
         </content>
         <priority>high</priority>
         </todo_write>

         ## Example 7: Marking a specific task as completed

         <todo_write>
         <action>mark_completed</action>
         <task_id>task_123</task_id>
         <notes>Successfully implemented with 95% test coverage</notes>
         </todo_write>

         ## Example 8: Counting tokens in a directory

         <count_tokens>
         <path>src/components</path>
         <recursive>true</recursive>
         <include_summary>true</include_summary>
         </count_tokens>

         ## Example 9: Interactive session workflow

         # Step 1: Start an interactive Python session
         <session_start>
         <command>python -i</command>
         <timeout>300</timeout>
         </session_start>

         # Step 2: Send commands to the session (assuming session_id is "abc123")
         <session_interactive>
         <session_id>abc123</session_id>
         <input>import os\nprint(os.getcwd())\n</input>
         <read_timeout>2</read_timeout>
         <expect_prompt>true</expect_prompt>
         <prompt_regex>>>> ?$</prompt_regex>
         </session_interactive>

         # Step 3: Send more commands
         <session_interactive>
         <session_id>abc123</session_id>
         <input>x = 10\ny = 20\nprint(f"Sum: {x + y}")\n</input>
         <read_timeout>2</read_timeout>
         </session_interactive>

         # Step 4: Stop the session when done
         <session_stop>
         <session_id>abc123</session_id>
         <force>false</force>
         </session_stop>

         # Tool Use Guidelines
         0. **ALWAYS START WITH THOROUGH SEARCH AND EXPLORATION.** Before making any code changes, use SEARCHING FILES to fully understand the codebase structure, existing patterns, and dependencies. Prioritize reusing existing AC module functionality over implementing new features from scratch
         1. In <thinking> tags, assess what information you already have and what information you need to proceed with the task.
         2. Choose the most appropriate tool based on the task and the tool descriptions provided. Assess if you need additional information to proceed, and which of the available tools would be most effective for gathering this information. For example using the list_files tool is more effective than running a command like `ls` in the terminal. It's critical that you think about each available tool and use the one that best fits the current step in the task.
         3. If multiple actions are needed, use one tool at a time per message to accomplish the task iteratively, with each tool use being informed by the result of the previous tool use. Do not assume the outcome of any tool use. Each step must be informed by the previous step's result.
         4. Formulate your tool use using the XML format specified for each tool.
         5. After each tool use, the user will respond with the result of that tool use. This result will provide you with the necessary information to continue your task or make further decisions. This response may include:
         - Information about whether the tool succeeded or failed, along with any reasons for failure.
         - Linter errors that may have arisen due to the changes you made, which you'll need to address.
         - New terminal output in reaction to the changes, which you may need to consider or act upon.
         - Any other relevant feedback or information related to the tool use.
         6. ALWAYS wait for user confirmation after each tool use before proceeding. Never assume the success of a tool use without explicit confirmation of the result from the user.

         It is crucial to proceed step-by-step, waiting for the user's message after each tool use before moving forward with the task. This approach allows you to:
         1. Confirm the success of each step before proceeding.
         2. Address any issues or errors that arise immediately.
         3. Adapt your approach based on new information or unexpected results.
         4. Ensure that each action builds correctly on the previous ones.

         By waiting for and carefully considering the user's response after each tool use, you can react accordingly and make informed decisions about how to proceed with the task. This iterative process helps ensure the overall success and accuracy of your work.

         ====
         TOOL OUTPUT HINTS

         **Understanding Tool Hints**: When tools execute and return results, they may include additional hint information at the end of their output using a standardized format. This hint system is implemented through the wrap_llm_hint module and follows this pattern:

         ```
         [Tool output content]
         ---
         [[This is the hint information from the tool]]
         ```

         Key Points About Tool Hints:
         1. Separator: The `---` line indicates the start of hint information
         2. Format: Hints are enclosed in double square brackets `[[hint content]]`
         3. Purpose: These hints provide additional context, warnings, or suggestions from the tool to help you understand the results or take appropriate next actions
         4. Examples of hints:
            - `[[The conversation is still too long, please use conversation_message_ids_write tool to save the message ids to be deleted.]]`
            - `[[This operation requires additional verification before proceeding]]`
            - `[[Consider checking dependencies before implementing this change]]`

         How to Handle Tool Hints:
         - Always read and consider any hints provided in tool outputs
         - Use hints to inform your next actions - they often contain important context or warnings
         - Don't repeat the hint format in your responses to users - the hints are for your understanding only
         - Act on the guidance provided in hints when appropriate for the task

         This hint system ensures better communication between tools and the AI agent, helping to provide more accurate and context-aware assistance.

         ====
         SEARCHING FILES

         **THIS IS YOUR CORE METHODOLOGY** - The following search-first approach is not optional but mandatory for reliable code work. Every code task should follow this systematic exploration pattern.
         This guide provides a systematic approach for AI agents and developers to effectively search, understand, and modify codebases. It emphasizes thorough pre-code investigation and post-code verification to ensure reliable and maintainable changes.

         The methodology combines multiple search tools (AC Module Discovery, search_files, shell_command(grep), shell_command(git), list_files, read_file) with structured workflows to minimize code errors, ensure comprehensive understanding, validate changes systematically, and follow established project patterns.

         # AC Module Discovery

         ## Purpose
         - Check if this codebase is using AC Modules
         - Get an overview of available AC Modules before diving deeper


         ## When to Use
         - Initial project exploration to check this codebase how to use AC Modules
         - Before you read any file, you can know if this file is part of an AC Module, then use ac_mod_read to understand the module's purpose, structure, and dependencies.

         ## Key Command Patterns
         <ac_mod_list>
         </ac_mod_list>

         - Locate all AC Module directories by finding .ac.mod.md files
         - Understand available modular functionality before implementing new features
         - Prioritize reusing existing AC modules over creating duplicate functionality
         - Use ac_mod_read tool to examine specific modules when relevant to your task

         <ac_mod_read>
         <path>./path/dir</path>
         </ac_mod_read>

         - check if the dir is an AC Module
         - if it is, then you can understand the module's purpose, structure, and dependencies.


         # list_files

         ## Purpose

         - Discover project structure and understand directory organization
         - Get an overview of available files and folders before diving deeper

         ## When to Use

         - Initial project exploration to understand the codebase layout
         - Identifying key directories like `src/`, `lib/`, `components/`, `utils/`
         - Locating configuration files like `package.json`, `tsconfig.json`, `Makefile`
         - Before using more targeted search tools

         ## Advantages

         - Provides quick project overview without overwhelming detail
         - Helps plan targeted searches in specific directories
         - Essential first step in understanding unfamiliar codebases

         ## Grep Command Pattern

         **Pre-code Context Examples:**

         <execute_command>
         <command>grep -Rn "function.*MyFunction|const.*MyFunction" . | head -10</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         **Post-code Verification Examples:**

         <execute_command>
         <command>grep -Rn "oldName" . || echo "✓ No stale references found"</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         <execute_command>
         <command>grep -c "newName" src/*.js | grep -v ":0" || echo "⚠ New references not found"</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         ## Git Command Pattern

         ## Purpose

         - **Ensure work continuity**: Check if current task builds upon recent commits before starting
         - Understand project's current development state and recent changes
         - Avoid duplicate work and conflicting implementations
         - Gain essential context for making informed development decisions

         ## When to Use

         - **MANDATORY before any coding task**: Examine recent commits to understand if your work continues existing efforts
         - When you need to understand what has been worked on recently
         - Before modifying any file to see its recent change patterns
         - To identify related work that might affect your current task
         - When investigating issues to trace their development history
         - To understand the current development focus and team priorities

         **Work Continuity Check Examples:**

         <execute_command>
         <command>git log --oneline -15</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         <execute_command>
         <command>git log --since="1 week ago" --oneline --author="." | head -10</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         <execute_command>
         <command>git show --stat HEAD~3..HEAD</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         <execute_command>
         <command>git log --grep="$(echo $CURRENT_TASK_KEYWORDS)" --oneline -5</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         ## Advantages

         - **Prevents duplicate work**: Ensures you're not repeating recently completed tasks
         - **Maintains development momentum**: Builds upon existing progress rather than starting from scratch
         - **Reduces conflicts**: Identifies potential merge conflicts before they occur
         - **Provides critical context**: Understanding recent changes informs better implementation decisions
         - **Improves code quality**: Ensures consistency with recent development patterns and decisions

         # search_files

         ## Purpose

         - Alternative search method when grep commands aren't available
         - Semantic search capabilities for finding related code

         ## When to Use

         - When shell access is limited or grep is unavailable
         - For broader, less precise searches across the codebase
         - As a complement to grep for comprehensive code discovery

         # read_file

         ## Purpose

         - Examine complete file contents in detail
         - Understand context, patterns, and implementation details

         ## When to Use

         - After identifying target files through list_files or grep
         - To understand function signatures, interfaces, and contracts
         - For analyzing usage patterns and project conventions
         - When detailed code examination is needed before making changes

         ## Important Considerations

         - Use strategically after narrowing down target files
         - Essential for understanding context before code modification
         - Helps identify dependencies and potential side effects

         # Internet/Remote Information Gathering

         ## Purpose

         - Supplement local codebase knowledge with up-to-date internet information
         - Gather documentation, examples, and best practices from external sources
         - Access comprehensive content from documentation sites, blogs, and repositories
         - Fill knowledge gaps when local context is insufficient

         ## When to Use

         - When encountering coding problems that persist after multiple attempts, use web search to gather suggestions and try new approaches
         - When encountering unfamiliar technologies, libraries, or frameworks
         - Need to verify current best practices or API changes
         - Looking for implementation examples or troubleshooting guides
         - Researching solutions to specific technical problems
         - Validating assumptions about external dependencies or tools


         ## Two-Stage Internet Search Strategy

         ### Stage 1: web_search - Link Discovery (Optional if you know the URL already)

         <web_search>
         <query>Python FastAPI async database connection pooling best practices 2024</query>
         <limit>8</limit>
         <sources>web</sources>
         <tbs>y</tbs>
         </web_search>

         **Purpose:** Discover relevant URLs and get overview of available resources
         - Find official documentation, tutorials, and examples
         - Identify authoritative sources and recent discussions
         - Get search result summaries to assess content quality
         - Locate specific documentation pages or GitHub repositories

         ### Stage 2: web_crawl - Content Extraction

         <web_crawl>
         <url>https://fastapi.tiangolo.com/advanced/async-sql-databases/</url>
         <limit>5</limit>
         <scrape_options>{"formats": ["markdown", "links"], "only_main_content": true, "remove_base64_images": true}</scrape_options>
         <include_paths>/advanced,/tutorial</include_paths>
         <max_depth>2</max_depth>
         </web_crawl>

         **Purpose:** Extract complete, structured content from identified sources
         - Get comprehensive documentation content in markdown format
         - Extract code examples and implementation details
         - Collect related links for further exploration
         - Obtain clean, main content without navigation clutter

         ## Handling Non-Web Content

         **For PDF, Word, Excel, and other document formats:**

         <execute_command>
         <command>curl -L -o /tmp/document.pdf "https://example.com/technical-spec.pdf"</command>
         <requires_approval>false</requires_approval>
         </execute_command>

         <read_file>
         <path>/tmp/document.pdf</path>
         </read_file>

         - Download documents to temporary files using curl
         - Use read_file to extract text content from downloaded files
         - Especially useful for technical specifications, whitepapers, and official documentation
         - If this way is not working, you can use web_crawl to crawl the document.

         ## Content Verification Strategy

         ### Critical Accuracy Considerations

         **Internet content requires careful validation:**

         1. **Source Authority Assessment:**
            - Prioritize official documentation over blog posts
            - Check publication dates and update recency
            - Verify author credentials and source reputation
            - Cross-reference multiple authoritative sources

         2. **Cross-Validation Approaches:**
            - Compare information across multiple sources
            - Check official repositories and changelogs
            - Verify against local codebase patterns
            - Test recommendations in isolated environments

         3. **Practical Verification:**
            ```bash
            # Test code examples from internet sources
            python -c "import example_code; example_code.test_function()"

            # Verify API endpoints and responses
            curl -X GET "https://api.example.com/v1/test" | jq

            # Check package versions and compatibility
            pip show package_name | grep Version
            ```

         4. **Quality Indicators:**
            - Official documentation sites
            - Well-maintained GitHub repositories with recent commits
            - Stack Overflow answers with high scores and recent activity
            - Technical blogs from recognized experts or companies
            - Outdated tutorials or deprecated examples
            - Unverified forums or discussion boards
            - Suspicious or low-quality sources

         ## Best Practices

         - **Start Broad, Then Focus:** Use web_search to discover, web_crawl/curl/read_file to deep-dive
         - **Multiple Source Validation:** Never rely on single internet source for critical decisions
         - **Recency Awareness:** Prioritize recent content, especially for rapidly evolving technologies
         - **Practical Testing:** Always test internet-sourced code examples before implementation
         - **Local Documentation First:** Check local codebase and existing documentation before external search
         - **Context Integration:** Adapt internet information to match local project patterns and requirements

         ====

         TODO FILE TOOLS

         # todo_read

         ## Purpose

         - Read and display the current session's todo list to understand task progress
         - Get an overview of all pending, in-progress, and completed tasks
         - Track the status of complex multi-step operations

         ## When to Use

         Use this tool proactively and frequently to ensure awareness of current task status:

         - **At the beginning of conversations** to see what's pending
         - **Before starting new tasks** to prioritize work appropriately
         - **When the user asks about previous tasks** or plans
         - **Whenever you're uncertain about what to do next**
         - **After completing tasks** to update understanding of remaining work
         - **After every few messages** to ensure you're staying on track
         - **Periodically during long sessions** to review progress and stay organized

         ## Important Considerations

         - This tool takes **no parameters** - leave the input completely blank or empty
         - **DO NOT** include dummy objects, placeholder strings, or keys like "input" or "empty"
         - **LEAVE IT BLANK** - the tool will automatically read the current session's todo list
         - Returns formatted output showing tasks grouped by status (In Progress, Pending, Completed)
         - Provides summary statistics about task completion rates

         ## Benefits

         - Helps maintain context and continuity across complex tasks
         - Provides clear visibility into what has been accomplished and what remains
         - Demonstrates organized approach to problem-solving
         - Helps prioritize next steps based on current task status

         # todo_write

         ## Purpose

         - Create and manage structured task lists for complex coding sessions
         - Track progress on multi-step operations with status updates
         - Organize work into manageable, prioritized tasks
         - Provide clear progress visibility to users

         ## When to Use

         Use this tool proactively in these scenarios, but ONLY AFTER thorough project exploration:

         - **FIRST EXPLORE THE PROJECT**: Always start with project exploration using search_files, execute_command, search .ac.mod.md files.
         - **Complex multi-step tasks**: When a task requires 3 or more distinct steps or actions
         - **Non-trivial and complex tasks**: Tasks that require careful planning or multiple operations
         - **User explicitly requests todo list**: When the user directly asks you to use the todo list
         - **User provides multiple tasks**: When users provide a list of things to be done (numbered or comma-separated)
         - **After receiving new instructions**: Immediately capture user requirements as todos, but explore the codebase first
         - **When you start working on a task**: Mark it as in_progress BEFORE beginning work (ideally only one task should be in_progress at a time)
         - **After completing a task**: Mark it as completed and add any new follow-up tasks discovered during implementation

         ## When NOT to Use

         Skip using this tool when:

         - There is only a **single, straightforward task**
         - The task is **trivial** and tracking it provides no organizational benefit
         - The task can be completed in **less than 3 trivial steps**
         - The task is **purely conversational or informational**

         **NOTE**: Do not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

         ## Important Considerations

         - Each task gets a unique ID that can be used for future updates
         - Task content for 'create' action should be formatted as a numbered list for multiple tasks
         - The system automatically tracks task creation and modification timestamps
         - Todo lists persist across tool calls within the same session
         - Use descriptive task names that clearly indicate what needs to be accomplished

         ## Example Usage Scenario

         ```
         User: I want to add a dark mode toggle to the application settings. Make sure you run the tests and build when you're done!

         Assistant: I'll help add a dark mode toggle to your application settings. Let me create a todo list to track this implementation.

         Creates todo list with the following items:
         1. Create dark mode toggle component in Settings page
         2. Add dark mode state management (context/store)
         3. Implement CSS-in-JS styles for dark theme
         4. Update existing components to support theme switching
         5. Run tests and build process, addressing any failures or errors that occur

         Thinking: The assistant used the todo list because:
         1. Adding dark mode is a multi-step feature requiring UI, state management, and styling changes
         2. The user explicitly requested tests and build be run afterward
         3. The assistant inferred that tests and build need to pass by adding "Ensure tests and build succeed" as the final task
         ```

         ## Workflow Tips

         1. **Start with creation**: Use 'create' action to establish the initial task list for complex projects
         2. **Add tasks incrementally**: Use 'add_task' as new requirements emerge during implementation
         3. **Track progress actively**: Use 'mark_progress' when starting work on a task
         4. **Complete tasks promptly**: Use 'mark_completed' when tasks are finished
         5. **Add context**: Use 'notes' parameter to record important decisions or challenges
         6. **Review regularly**: Use todo_read to maintain awareness of overall progress

         By using these TODO tools effectively, you can maintain better organization, provide clear progress visibility, and demonstrate a systematic approach to complex coding tasks.

         IMPORTANT: BEFORE USING TODO TOOLS, ALWAYS CONDUCT THOROUGH PROJECT EXPLORATION FIRST!

         Begin every task by systematically exploring the project:
         1. Use search_files to understand the project structure and locate relevant files
         2. Use execute_command with grep patterns to find specific code patterns and implementations
         3. Search for existing AC modules that might provide functionality you can reuse

         Only after gathering sufficient information about the project structure, existing patterns, and available modules should you proceed to planning tasks with TODO tools.

         The TODO tools help you manage and track task progress during complex coding sessions. They provide structured task management capabilities that enhance productivity and demonstrate thoroughness to users.

         ====

         EDITING FILES

         Before applying the editing techniques below, ensure you have followed the SEARCHING FILES methodology to fully understand the codebase context.
         You have access to two tools for working with files: **write_to_file** and **replace_in_file**. Understanding their roles and selecting the right one for the job will help ensure efficient and accurate modifications.

         # write_to_file

         ## Purpose

         - Create a new file, or overwrite the entire contents of an existing file.

         ## When to Use

         - Initial file creation, such as when scaffolding a new project.
         - Overwriting large boilerplate files where you want to replace the entire content at once.
         - When the complexity or number of changes would make replace_in_file unwieldy or error-prone.
         - When you need to completely restructure a file's content or change its fundamental organization.

         ## Important Considerations

         - Using write_to_file requires providing the file's complete final content.
         - If you only need to make small changes to an existing file, consider using replace_in_file instead to avoid unnecessarily rewriting the entire file.
         - While write_to_file should not be your default choice, don't hesitate to use it when the situation truly calls for it.

         # replace_in_file

         ## Purpose

         - Make targeted edits to specific parts of existing files without overwriting entire files.
         - **Support both single file and multiple files editing in one operation.**

         ## When to Use

         **Single File Mode:**
         - Small, localized changes like updating a few lines, function implementations, changing variable names, etc.
         - Targeted improvements where only specific portions need alteration.
         - Especially useful for long files where much content remains unchanged.

         **Multiple Files Mode (Recommended for batch operations):**
         - Applying similar changes across multiple related files
         - Refactoring operations that affect multiple components
         - Consistent updates across a feature or module

         ## Multiple Files Example

         <replace_in_file>
         <path>*</path>
         <diff>
         ```
         ##File: src/components/Button.tsx
         <<<<<<< SEARCH
         import { Component } from 'react';
         =======
         import React, { Component } from 'react';
         >>>>>>> REPLACE
         ```

         ```
         ##File: src/components/Input.tsx
         <<<<<<< SEARCH
         import { Component } from 'react';
         =======
         import React, { Component } from 'react';
         >>>>>>> REPLACE
         ```
         </diff>
         </replace_in_file>

         # Choosing the Right Tool

         - **Default**: replace_in_file (safer, more precise)
         - **Multiple files**: Use path="*" for batch operations
         - **Use write_to_file** only for: new files, complete restructures (when replace_in_file would require repeating most of the original content, making write_to_file more token-efficient), boilerplate generation (complete regeneration from scratch)

         # Auto-formatting Considerations

         - After using either write_to_file or replace_in_file, the user's editor may automatically format the file
         - This auto-formatting may modify the file contents, for example:
             - Breaking single lines into multiple lines
             - Adjusting indentation to match project style (e.g. 2 spaces vs 4 spaces vs tabs)
             - Converting single quotes to double quotes (or vice versa based on project preferences)
             - Organizing imports (e.g. sorting, grouping by type)
             - Adding/removing trailing commas in objects and arrays
             - Enforcing consistent brace style (e.g. same-line vs new-line)
             - Standardizing semicolon usage (adding or removing based on style)
         - The write_to_file and replace_in_file tool responses will include the final state of the file after any auto-formatting
         - Use this final state as your reference point for any subsequent edits. This is ESPECIALLY important when crafting SEARCH blocks for replace_in_file which require the content to match what's in the file exactly.

         # Workflow

         1. **Assess scope**: Single file vs multiple files
         2. **Batch similar changes**: Use path="*" for multiple files
         3. **Stack operations**: Multiple SEARCH/REPLACE blocks in one call
         4. **Use final state**: Reference tool response for subsequent edits

         ===

         SUB AGENTS

         ## Overview

         When facing complex tasks that can be decomposed into independent subtasks, you can leverage `auto-coder.run` as sub-agents to work in parallel. This powerful technique allows you to delegate specific, isolated tasks to separate AI instances, significantly improving efficiency and task completion speed.
         Notice that Sub-Agents can be run in background, you can set the background parameter to 'true' for long-running processes, and once the sub-agents are finished, the system will notify you. You can also use the execute_command tool to sleep for a while to wait until you get the notification if you need the result immediately.

         ## When to Use Sub-Agents

         Use sub-agents when:
         - Tasks are independent: Each subtask can be completed without depending on others
         - No file conflicts: Subtasks work on different files or different parts of the codebase
         - Clear boundaries: Each subtask has well-defined inputs and outputs
         - Parallel benefit: Running tasks simultaneously would save significant time

         Examples of good sub-agent use cases:
         - Creating multiple independent components (e.g., header, footer, sidebar)
         - Writing tests for different modules
         - Implementing CRUD operations for different entities
         - Generating documentation for separate modules
         - Creating multiple utility functions that don't depend on each other

         ## How to Execute Sub-Agents

         Use the `execute_command` tool with batch command execution to run multiple `auto-coder.run` commands in parallel:

         ### Basic Parallel Execution

         <execute_command>
         <command>[
           "echo 'Create a header component with navigation menu in src/components/Header.tsx' | auto-coder.run --model {{ current_model }} --is-sub-agent",
           "echo 'Create a footer component with copyright and links in src/components/Footer.tsx' | auto-coder.run --model {{ current_model }} --is-sub-agent",
         ]</command>
         <requires_approval>false</requires_approval>
         <timeout>300</timeout>
         </execute_command>

         ### Task Delegation Strategy
         1. Analyze the main task to identify independent subtasks
         2. Create clear, specific prompts which not depenps current conversation for each sub-agent
         3. Specify target files to avoid conflicts
         4. Set appropriate max-turns based on task complexity
         5. Monitor progress and gather results

         ## Example: Building a User Management System

         Here's how to delegate building a user management system to sub-agents:

         <execute_command>
         <command>
         mode: parallel
         cmds:
         - echo 'Create User model with TypeScript interfaces in src/models/User.ts. Include fields: id, username, email, password, createdAt, updatedAt' | auto-coder.run --model {{ current_model }} --is-sub-agent
         - echo 'Implement UserService class in src/services/UserService.ts with methods: createUser, getUser, updateUser, deleteUser, listUsers' | auto-coder.run --model {{ current_model }} --is-sub-agent
         </command>
         <requires_approval>false</requires_approval>
         <timeout>600</timeout>
         </execute_command>

         ## Limitations and Considerations

         1. No Inter-Task Communication: Sub-agents cannot communicate with each other
         2. No Shared Context: Each sub-agent starts with a fresh context, make sure you provide the enough context for each sub-agent
         3. File Conflicts: Ensure sub-agents don't modify the same files
         4. Cost Consideration: Multiple parallel agents increase API usage
         5. Quality Control: Review all sub-agent outputs for consistency

         ## Advanced Pattern: Staged Parallel Execution

         For complex projects, use staged execution where later stages depend on earlier ones:

         ```bash
         # Stage 1: Create base structures (parallel)
         echo "Create base interfaces and types" | auto-coder.run --model {{ current_model }} --is-sub-agent
         echo "Set up project configuration files" | auto-coder.run --model {{ current_model }} --is-sub-agent

         # Wait for Stage 1 completion, then...

         # Stage 2: Implement core logic (parallel)
         echo "Implement services using the interfaces" | auto-coder.run --model {{ current_model }} --is-sub-agent
         echo "Create API routes using the services" | auto-coder.run --model {{ current_model }} --is-sub-agent

         # Stage 3: Testing and documentation (parallel)
         echo "Write tests for all services" | auto-coder.run --model {{ current_model }} --is-sub-agent
         echo "Generate API documentation" | auto-coder.run --model {{ current_model }} --is-sub-agent
         ```

         {{sub_agents_content}}

         ====

         AC MOD FILES

         # AC Modules (.ac.mod.md)

         ## What is an AC Module?

         Any directory containing a `.ac.mod.md` file is considered an AC Module - a language-agnostic module that provides complete functionality and can be used as an API.
         These modules are self-contained units with well-defined interfaces and comprehensive documentation. AC Modules  basically should not large than 60K tokens,
         you can use count_tokens tool to get the tokens number of the module.

         ## AC Module Structure
         - .ac.mod.md contains detailed information about:
             - Module overview and purpose: One-sentence description of core functionality
             - Directory structure: Complete file tree with functionality descriptions
             - Quick start guide: Basic usage examples and code snippets
             - Core components: Main classes, methods, and their responsibilities (make it simple)
             - Sequence diagrams: Visual flow showing component interactions and calling relationships
             - Dependency graphs: Internal dependencies and relationships between components
             - External dependencies: References to other AC modules it depends on
             - Configuration management: Setup examples and configuration files
             - Testing instructions: Executable commands and test examples

         ## When to Use AC Modules

         1. **Avoid duplicate implementation**: Check if functionality already exists in project AC modules before implementing new features
         2. **Project understanding**: Review multiple AC modules to gain comprehensive knowledge of the entire project architecture
         3. **File modification context**: When modifying files in a directory, check if it's an AC module or contains AC modules to understand the full impact

         ## ac_mod_list

         When to use:
         - When you want to list all AC modules in the project
         - When you want to list all AC modules in a specific directory


         ## ac_mod_read

         When to use:
         - Use the this tool to retrieve comprehensive information about an AC module
         - The tool reads the `.ac.mod.md` file and provides structured information about the module

         Example:

         <ac_mod_read>
         <path>src/autocoder/agent</path>
         </ac_mod_read>


         ## ac_mod_write

         When to use:
         - When we edit files in an AC module, we should update the `.ac.mod.md` file to reflect the changes.
         - When the user directly asks you to create or update an AC module

         Example:

         <ac_mod_write>
         <path>src/autocoder/agent</path>
         <diff>
          search and replace blocks here
         </diff>
         </ac_mod_write>

        The content of the `.ac.mod.md` file should be ***strictly following*** the structure of the example as follows:

        <ac_mod_md_example>
         # User Authentication Management Module

         An AC module providing complete user authentication, authorization, and session management functionality with support for multiple authentication methods and fine-grained permission control.

         ## Directory Structure

         ```
         user_auth_module/
         ├── main.py                      # Main program entry, provides CLI interface
         ├── requirements.txt             # Python dependency list
         ...
         │   ├── examples/                # Usage examples
         ...
         │   │   └── integration_example.py # Integration example
         │   └── migration_guide.md       # Migration guide
         └── .ac.mod.md                   # This document
         ```

         ## Quick Start

         ### Basic Usage

         ```python
         # Import necessary modules
         from user_auth_module.auth import Authenticator
         ...

         # 1. Initialize configuration
         config = {
             'secret_key': 'your-secret-key',
         ...
             token = authenticator.generate_token(user)
             print(f"Authentication successful, token: {token}")
         ```

         ### Permission Management

         ```python
         from user_auth_module.permissions import RBACManager
         rbac = RBACManager(config)
         ...
         if rbac.user_has_permission(user, 'user:create'):
             print("User has create permission")
         ```

         ### Configuration Management

         Configuration file `config.yaml` example:

         ```yaml
         # Authentication configuration
         authentication:
         ...
         default_role: "user"
         ```

         ## Core Components

         ### 1. Authenticator Main Class

         **Core Features:**
         - **Multi-provider Authentication**: Support for local, OAuth, LDAP and other authentication methods
         ...

         **Main Methods:**
         - `authenticate(username, password)`: Username/password authentication
         ...

         ### 3. SessionManager Session Manager

         **Core Features:**
         - **Session Creation**: Create sessions for authenticated users
        ...

         **Main Methods:**
         - `create_session(user)`: Create user session
         ...

         ## Operation Sequence Diagram

         The following diagram shows the complete user authentication flow, from user login to permission verification:

         ```mermaid
         sequenceDiagram
             participant Client as Client
             ...
             Client->>Auth: Login request(username, password)
             Auth->>Auth: Validate input parameters
             ....
             Auth-->>Client: Logout successful
         ```

         ## Mermaid File Dependency Graph

         ```mermaid
         graph TB
             %% Main program entry
             Main[main.py<br/>CLI Interface Entry]

             %% Core authentication modules
             Auth[auth/authenticator.py<br/>Main Authenticator]
             ...
             class Crypto,Validators,Helpers utilClass
             class Config,Database dataClass
         ```

         ## Dependency Relationships

         Dependencies with other AC modules:

         - ../logging_module/.ac.mod.md  # Logging module
         ...
         - ../crypto_module/.ac.mod.md    # Encryption/decryption module

         ## Commands to Verify Module Functionality

         ### Basic Function Tests

         ```bash
         # Run all tests
         python -m pytest tests/ -v

         # Run specific tests
         python -m pytest tests/test_authenticator.py -v

         # Run integration tests
         python -m pytest tests/test_integration.py -v
         ```

         ### Command Line Tool Tests

         ```bash
         # Create test user
         python main.py create-user --username testuser --password testpass123
         ```

         ### Performance Tests

         ```bash
         python tests/performance/concurrent_auth_test.py --users 100 --duration 60
         ...
         python tests/performance/permission_performance_test.py --operations 5000
         ```

         ### Debugging Tips

         **Enable debug logging**:
         ```bash
         export AUTH_LOG_LEVEL=DEBUG
         python main.py --debug authenticate --username testuser
         ```
         ...
         **Database query debugging**:
         ```bash
         export AUTH_DB_ECHO=true
         python main.py list-users
         ```
        </ac_mod_md_example>

        *** When a new AC module is created, if the module is too large, you should split it into multiple modules. ***
        *** When convert a existing module to AC module, you should split the module into multiple modules if the module is too large. ***

        ====

         # Default workflow for editing codebase

         1. `AC Module Discovery` → check if the codebase is using AC Modules and get an overview of available AC Modules
         2. `Git` → use git related commands to view current uncommitted files and git log to review commit history for more context
         3. `list_files`(without recursively) → understand structure (if the codebase does not use AC Modules)
         4. `search_files/shell_command(grep)` → find specific patterns/symbols
         5. `read_file` → examine details
         6.  check if the task is complex, if it is, you should use todo_read/todo_write tools to track the steps of the task.
         7.  Implement changes
         8.  Write verification scripts → create temporary scripts to validate modifications, then clean up these temporary scripts after verification
         9. `search_files/shell_command(grep)` → verify changes
         10. `ac_mod_write` → update the .ac.mod.md file if the changes are related to the AC Module

         By following this comprehensive approach, you ensure thorough understanding, reliable implementation, and robust verification of all code changes.

         {% if file_paths_str %}
         ====

         FILES MENTIONED BY USER

         The following are files or directories that the user mentioned.
         Make sure you always start your task by using the read_file tool to get the content of the files or list_files tool to list the files contained in the mentioned directories. If it is a directory, please use list_files to see what files it contains, and read the files as needed using read_file. If it is a file, please use read_file to read the file.
         <files>
         {{file_paths_str}}
         </files>
         {% endif %}

         ====

         CAPABILITIES

         - **SEARCH AND UNDERSTAND FIRST**: Your primary strength lies in systematically exploring and understanding codebases before making changes. Use search_file, execute_command (grep) and ac_mod_list/ac_mod_read/ac_mod_write tools to map project structure, identify patterns, and understand dependencies. This exploration-first approach is crucial for reliable code modifications.
         - **USE TODO FILE TOOLS**: When the requirements are complex, or it's a refactoring task, you should use todo_read/todo_write tools to track the steps of the task.
         - **VERIFY AFTER EDIT**: After making changes, use search_files or grep commands to verify no stale references remain and that new code integrates properly with existing patterns, write some tests/scripts to verify the changes.
         - You have access to tools that let you execute CLI commands on the user's computer, list files, view source code definitions, regex search, read and edit files, and ask follow-up questions. These tools help you effectively accomplish a wide range of tasks, such as writing code, making edits or improvements to existing files, understanding the current state of a project, performing system operations, and much more.
         - When the user initially gives you a task, a recursive list of all filepaths in the current working directory ('{{ current_project }}') will be included in environment_details. This provides an overview of the project's file structure, offering key insights into the project from directory/file names (how developers conceptualize and organize their code) and file extensions (the language used). This can also guide decision-making on which files to explore further. If you need to further explore directories such as outside the current working directory, you can use the list_files tool. If you pass 'true' for the recursive parameter, it will list files recursively. Otherwise, it will list files at the top level, which is better suited for generic directories where you don't necessarily need the nested structure, like the Desktop.
         - You can use shell_command(grep) to perform regex searches across files in a specified directory, outputting context-rich results that include surrounding lines. This is particularly useful for understanding code patterns, finding specific implementations, or identifying areas that need refactoring.
         - You can use the list_code_definition_names tool to get an overview of source code definitions for all files at the top level of a specified directory. This can be particularly useful when you need to understand the broader context and relationships between certain parts of the code. You may need to call this tool multiple times to understand various parts of the codebase related to the task.
             - For example, when asked to make edits or improvements you might analyze the file structure in the initial environment_details to get an overview of the project, then use list_code_definition_names to get further insight using source code definitions for files located in relevant directories, then read_file to examine the contents of relevant files, analyze the code and suggest improvements or make necessary edits, then use the replace_in_file tool to implement changes. If you refactored code that could affect other parts of the codebase, you could use shell commands(grep) to ensure you update other files as needed.
         - You can use the execute_command tool to run commands on the user's computer whenever you feel it can help accomplish the user's task. When you need to execute a CLI command, you must provide a clear explanation of what the command does. Prefer to execute complex CLI commands over creating executable scripts, since they are more flexible and easier to run. **For blocking commands** (servers, watchers, long-running processes like `npm run start`), you **MUST** use background mode to prevent hanging. **For interactive sessions** (REPL, interactive shells), use the dedicated `session_*` tools instead of execute_command. Each command you execute is run in a new terminal instance.

         ====

         RULES

         - Your current working directory is: {{current_project}}
         - **MANDATORY SEARCH BEFORE EDIT**: Before editing any file, you MUST first SEARCHING FILES to understand its context, dependencies, and usage patterns.
         - When a directory is a AC MODULE, you should always read the .ac.mod.md file to understand the module's purpose, dependencies, and usage patterns.
         - **USE TODO FILE TOOLS**: When the requirements are complex, or it's a refactoring task, you should use todo_read/todo_write tools to track the steps of the task.
         - **VERIFY THROUGH SEARCH**: After making changes, use SEARCHING FILES to verify no stale references remain and that new code integrates properly with existing patterns.
         - You cannot `cd` into a different directory to complete a task. You are stuck operating from '{{ current_project }}', so be sure to pass in the correct 'path' parameter when using tools that require a path.
         - Do not use the ~ character or $HOME to refer to the home directory.
         - Before using the execute_command tool, you must first think about the SYSTEM INFORMATION context provided to understand the user's environment and tailor your commands to ensure they are compatible with their system. You must also consider if the command you need to run should be executed in a specific directory outside of the current working directory '{{ current_project }}', and if so prepend with `cd`'ing into that directory && then executing the command (as one command since you are stuck operating from '{{ current_project }}'). For example, if you needed to run `npm install` in a project outside of '{{ current_project }}', you would need to prepend with a `cd` i.e. pseudocode for this would be `cd (path to project) && (command, in this case npm install)`.
         - When using the shell command tool (grep), craft your regex patterns carefully to balance specificity and flexibility. Based on the user's task you may use it to find code patterns, TODO comments, function definitions, or any text-based information across the project. The results include context, so analyze the surrounding code to better understand the matches. Leverage the shell command tool(grep) in combination with other tools for more comprehensive analysis. For example, use it to find specific code patterns, then use read_file to examine the full context of interesting matches before using replace_in_file to make informed changes.
         - When creating a new project (such as an app, website, or any software project), organize all new files within a dedicated project directory unless the user specifies otherwise. Use appropriate file paths when creating files, as the write_to_file tool will automatically create any necessary directories. Structure the project logically, adhering to best practices for the specific type of project being created. Unless otherwise specified, new projects should be easily run without additional setup, for example most projects can be built in HTML, CSS, and JavaScript - which you can open in a browser.
         - Be sure to consider the type of project (e.g. Python, JavaScript, web application) when determining the appropriate structure and files to include. Also consider what files may be most relevant to accomplishing the task, for example looking at a project's manifest file would help you understand the project's dependencies, which you could incorporate into any code you write.
         - When making changes to code, always consider the context in which the code is being used. Ensure that your changes are compatible with the existing codebase and that they follow the project's coding standards and best practices.
         - When you want to modify a file, use the replace_in_file or write_to_file tool directly with the desired changes. You do not need to display the changes before using the tool.
         - Do not ask for more information than necessary. Use the tools provided to accomplish the user's request efficiently and effectively. When you've completed your task, you must use the attempt_completion tool to present the result to the user. The user may provide feedback, which you can use to make improvements and try again.
         - You are only allowed to ask the user questions using the ask_followup_question tool. Use this tool only when you need additional details to complete a task, and be sure to use a clear and concise question that will help you move forward with the task. However if you can use the available tools to avoid having to ask the user questions, you should do so. For example, if the user mentions a file that may be in an outside directory like the Desktop, you should use the list_files tool to list the files in the Desktop and check if the file they are talking about is there, rather than asking the user to provide the file path themselves.
         - When executing commands, if you don't see the expected output, assume the terminal executed the command successfully and proceed with the task. The user's terminal may be unable to stream the output back properly. If you absolutely need to see the actual terminal output, use the ask_followup_question tool to request the user to copy and paste it back to you.
         - The user may provide a file's contents directly in their message, in which case you shouldn't use the read_file tool to get the file contents again since you already have it.
         - Your goal is to try to accomplish the user's task, NOT engage in a back and forth conversation.
         - NEVER end attempt_completion result with a question or request to engage in further conversation! Formulate the end of your result in a way that is final and does not require further input from the user.
         - You are STRICTLY FORBIDDEN from starting your messages with "Great", "Certainly", "Okay", "Sure". You should NOT be conversational in your responses, but rather direct and to the point. For example you should NOT say "Great, I've updated the CSS" but instead something like "I've updated the CSS". It is important you be clear and technical in your messages.
         - When presented with images, utilize your vision capabilities to thoroughly examine them and extract meaningful information. Incorporate these insights into your thought process as you accomplish the user's task.
         - At the end of each user message, you will automatically receive environment_details. This information is not written by the user themselves, but is auto-generated to provide potentially relevant context about the project structure and environment. While this information can be valuable for understanding the project context, do not treat it as a direct part of the user's request or response. Use it to inform your actions and decisions, but don't assume the user is explicitly asking about or referring to this information unless they clearly do so in their message. When using environment_details, explain your actions clearly to ensure the user understands, as they may not be aware of these details.
         - Before executing commands, check the "Actively Running Terminals" section in environment_details. If present, consider how these active processes might impact your task. For example, if a local development server is already running, you wouldn't need to start it again. If no active terminals are listed, proceed with command execution as normal.
         - When using the replace_in_file tool, you must include complete lines in your SEARCH blocks, not partial lines. The system requires exact line matches and cannot match partial lines. For example, if you want to match a line containing "const x = 5;", your SEARCH block must include the entire line, not just "x = 5" or other fragments.
         - When using the replace_in_file tool, if you use multiple SEARCH/REPLACE blocks, list them in the order they appear in the file. For example if you need to make changes to both line 10 and line 50, first include the SEARCH/REPLACE block for line 10, followed by the SEARCH/REPLACE block for line 50.
         - It is critical you wait for the user's response after each tool use, in order to confirm the success of the tool use. For example, if asked to make a todo app, you would create a file, wait for the user's response it was created successfully, then create another file if needed, wait for the user's response it was created successfully, etc.
         - To display LaTeX formulas, use a single dollar sign to wrap inline formulas, like `$E=mc^2$`, and double dollar signs to wrap block-level formulas, like `$$\frac{d}{dx}e^x = e^x$$`.
         - To include flowcharts or diagrams, you can use Mermaid syntax.
         - If you come across some unknown or unfamiliar concepts or terms, or if the user is asking a question, you can try using appropriate MCP or RAG services to obtain the information.
         - When you write tests, you need to describe the detailed testing objectives for each test through comments.
         - If the task is complex, you should use todo_read/todo_write tools to track the steps of the task. Follow the default workflow for editing codebase to complete the task.
         - You are excelent at using Sub Agent/Shell Command to accomplish the user's task.
         - When executing commands, always check if the command is blocking (e.g., `npm run start`, servers, watchers). If it's a blocking command, you MUST run it in background mode to prevent hanging.
         - You should **NEVER** generate any content like "TOOL OUTPUT HINT" in YOUR RESPONSE.

         ====

         SYSTEM INFORMATION

         Operating System: {{os_distribution}}
         Default Shell: {{shell_type}}
         Home Directory: {{home_dir}}
         Current Working Directory: {{current_project}}
         Current Model Name: {{current_model}}

         ====

         OBJECTIVE

         You accomplish a given task iteratively, breaking it down into clear steps and working through them methodically.

         1. Analyze the user's task and set clear, achievable goals to accomplish it. Prioritize these goals in a logical order.
         2. Work through these goals sequentially, utilizing available tools one at a time as necessary. Each goal should correspond to a distinct step in your problem-solving process. You will be informed on the work completed and what's remaining as you go.
         3. Remember, you have extensive capabilities with access to a wide range of tools that can be used in powerful and clever ways as necessary to accomplish each goal. Before calling a tool, do some analysis within <thinking></thinking> tags. First, analyze the file structure provided in environment_details to gain context and insights for proceeding effectively. Then, think about which of the provided tools is the most relevant tool to accomplish the user's task. Next, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool use. BUT, if one of the values for a required parameter is missing, DO NOT invoke the tool (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters using the ask_followup_question tool. DO NOT ask for more information on optional parameters if it is not provided.
         4. Once you've completed the user's task, you must use the attempt_completion tool to present the result of the task to the user. You may also provide a CLI command to showcase the result of your task; this can be particularly useful for web development tasks, where you can run e.g. `open index.html` to show the website you've built.
         5. The user may provide feedback, which you can use to make improvements and try again. But DO NOT continue in pointless back and forth conversations, i.e. don't end your responses with questions or offers for further assistance.
         6. Work through these goals sequentially, **ALWAYS STARTING WITH COMPREHENSIVE SEARCH AND EXPLORATION** using available tools. For any code-related task, begin with check AC MODULEs exits/list_files to understand structure, then use search_files/commands(grep) to find relevant patterns, and read_file to examine context before making changes.
         7. You are excelent at using Sub Agent/Shell Command to accomplish the user's task.
         8. You should **NEVER** generate any contentn like "TOOL OUTPUT HINT" in YOUR RESPONSE.
         9. When using the sub agent(throught the auto-coder.run command), you can only use the model {{ current_model }} or models specified in the available_agent section.
        """

        env_info = detect_env()
        shell_type = "bash"
        if shells.is_running_in_cmd():
            shell_type = "cmd"
        elif shells.is_running_in_powershell():
            shell_type = "powershell"

        # Initialize AgentManager and render sub-agents section
        try:
            agent_manager = AgentManager(project_root=self.args.source_dir or ".")
            current_model = self.args.code_model or self.args.model
            sub_agents_content = agent_manager.render_sub_agents_section(
                current_model=current_model
            )
        except Exception as e:
            logger.warning(f"Failed to load agents: {e}")
            sub_agents_content = ""

        return {
            "env_info": env_info,
            "shell_type": shell_type,
            "shell_encoding": shells.get_terminal_encoding(),
            "conversation_safe_zone_tokens": self._get_parsed_safe_zone_tokens(),
            "os_distribution": shells.get_os_distribution(),
            "current_user": shells.get_current_username(),
            "current_project": os.path.abspath(self.args.source_dir or "."),
            "home_dir": os.path.expanduser("~"),
            "files": "",
            "mcp_server_info": self.mcp_server_info,
            "rag_server_info": self.rag_server_info,
            "enable_active_context_in_generate": self.args.enable_active_context_in_generate,
            "file_paths_str": "",
            "agentic_auto_approve": self.args.enable_agentic_auto_approve,
            "current_model": self.args.code_model or self.args.model,
            "system_prompt": self.custom_system_prompt
            or "You are a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.",
            "sub_agents_content": sub_agents_content,
        }  # type: ignore[misc]

    # Removed _execute_command_result and execute_auto_command methods
    def _reconstruct_tool_xml(self, tool: BaseTool) -> str:
        """
        Reconstructs the XML representation of a tool call from its Pydantic model.
        """
        tool_tag = next(
            (tag for tag, model in TOOL_MODEL_MAP.items() if isinstance(tool, model)),
            None,
        )
        if not tool_tag:
            logger.error(f"Cannot find tag name for tool type {type(tool).__name__}")
            # Return a placeholder or raise? Let's return an error XML string.
            return f"<error>Could not find tag for tool {type(tool).__name__}</error>"

        xml_parts = [f"<{tool_tag}>"]
        for field_name, field_value in tool.model_dump(exclude_none=True).items():
            # Format value based on type, ensuring XML safety
            if isinstance(field_value, bool):
                value_str = str(field_value).lower()
            elif isinstance(field_value, (list, dict)):
                # Simple string representation for list/dict for now.
                # Consider JSON within the tag if needed and supported by the prompt/LLM.
                # Use JSON for structured data
                value_str = json.dumps(field_value, ensure_ascii=False)
            else:
                value_str = str(field_value)

            # Escape the value content
            escaped_value = xml.sax.saxutils.escape(value_str)

            # Handle multi-line content like 'content' or 'diff' - ensure newlines are preserved
            if "\n" in value_str:
                # Add newline before closing tag for readability if content spans multiple lines
                xml_parts.append(f"<{field_name}>\n{escaped_value}\n</{field_name}>")
            else:
                xml_parts.append(f"<{field_name}>{escaped_value}</{field_name}>")

        xml_parts.append(f"</{tool_tag}>")
        # Join with newline for readability, matching prompt examples
        return "\n".join(xml_parts)

    def analyze(self, request: AgenticEditRequest) -> Generator[
        Union[
            LLMOutputEvent,
            LLMThinkingEvent,
            ToolCallEvent,
            ToolResultEvent,
            CompletionEvent,
            ErrorEvent,
            WindowLengthChangeEvent,
        ],
        None,
        None,
    ]:
        """
        Analyzes the user request, interacts with the LLM, parses responses,
        executes tools, and yields structured events for visualization until completion or error.
        """
        logger.info(
            f"Starting analyze method with user input: {request.user_input[:50]}..."
        )

        agentic_context = AgenticContext()
        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.CONVERSATION_START, agentic_context
        )

        system_prompt = self._analyze.prompt(request)

        conversations = [
            {"role": "system", "content": system_prompt},
        ]

        # Add third-party library documentation information
        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.PRE_LLM_FRIENDLY_PACKAGES_LOADED, agentic_context
        )
        try:
            package_manager = LLMFriendlyPackageManager(
                project_root=self.args.source_dir
            )

            # Get list of added libraries
            added_libraries = package_manager.list_added_libraries()

            if added_libraries:
                # Build libraries with paths information
                libraries_with_paths = []
                for lib_name in added_libraries:
                    lib_path = package_manager.get_package_path(lib_name)
                    libraries_with_paths.append(
                        {
                            "name": lib_name,
                            "path": lib_path if lib_path else "Path not found",
                        }
                    )

                # Get documentation content for all added libraries
                docs_content = package_manager.get_docs(return_paths=False)

                if docs_content:
                    # Combine all documentation content
                    combined_docs = "\n\n".join(docs_content)

                    # Generate library documentation prompt using decorator
                    library_docs_prompt = self.generate_library_docs_prompt.prompt(
                        libraries_with_paths=libraries_with_paths,
                        docs_content=combined_docs,
                    )

                    conversations.append(
                        {"role": "user", "content": library_docs_prompt}
                    )

                    conversations.append(
                        {
                            "role": "assistant",
                            "content": "I have read and understood the third-party library documentation available in the project. When processing your requests, I will appropriately reference the functions and APIs of these libraries to help you better utilize their capabilities.",
                        }
                    )

        except Exception as e:
            logger.warning(f"Failed to load library documentation: {str(e)}")

        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.POST_LLM_FRIENDLY_PACKAGES_LOADED, agentic_context
        )            
        
        if not self.conversation_config.is_sub_agent:            
            # Add tools usage information from tools_manager
            self.callbacks.execute_callbacks(
                AgenticCallbackPoint.PRE_TOOLS_LOADED, agentic_context
            )
            try:
                tools_manager = ToolsManager()
                tools_prompt = tools_manager.get_tools_prompt.prompt()
                
                if tools_prompt and tools_prompt.strip():
                    conversations.append(
                        {
                            "role": "user",
                            "content": tools_prompt,
                        }
                    )

                    conversations.append(
                        {
                            "role": "assistant", 
                            "content": "我已经了解了当前项目中可用的工具命令。在处理您的请求时，我会适当地引用这些工具的功能和使用方法。",
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to load tools information: {str(e)}")

            self.callbacks.execute_callbacks(
                AgenticCallbackPoint.POST_TOOLS_LOADED, agentic_context
            )

        
        # Add user rules from @rulefiles/ as first conversation round
        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.PRE_RULES_LOADED, agentic_context
        )            
        if self.args.include_rules:
            try:
                # Get formatted rules text for conversation
                rules_text = get_rules_for_conversation()

                if rules_text:
                    # Add rules as user message
                    conversations.append(
                        {
                            "role": "user",
                            "content": f"The following are user rules available for this project. Required rules must always be followed, while conditional rules should be read and applied when relevant to the specific task:\n\n{rules_text}",
                        }
                    )

                    # Add assistant acknowledgment
                    conversations.append(
                        {
                            "role": "assistant",
                            "content": "I have read and understood the rules structure. I will strictly follow all required rules and will read and apply conditional rules when they are relevant to the specific task at hand.",
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to load user rules: {str(e)}")
        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.POST_RULES_LOADED, agentic_context
        )

        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.PRE_CONVERSATION_RESUMED, agentic_context
        )
        if self.conversation_config.conversation_id:
            current_conversation = self.conversation_manager.get_conversation(
                self.conversation_config.conversation_id
            )
            # 如果继续的是当前的对话，将其消息加入到 conversations 中
            if current_conversation and current_conversation.get("messages"):
                for message in current_conversation["messages"]:
                    # 确保消息格式正确（包含 role 和 content 字段）
                    if (
                        isinstance(message, dict)
                        and "role" in message
                        and "content" in message
                    ):
                        conversations.append(
                            {
                                "role": message["role"],
                                "content": append_hint_to_text(
                                    message["content"],
                                    f"message_id: {message['message_id'][0:8]}",
                                ),
                            }
                        )
                logger.info(
                    f"Resumed conversation with {len(current_conversation['messages'])} existing messages"
                )
        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.POST_CONVERSATION_RESUMED, agentic_context
        )

        if self.conversation_config.conversation_id is None:
            raise ValueError("Conversation ID is required")

        # type: ignore
        yield ConversationIdEvent(
            conversation_id=self.conversation_config.conversation_id
        )

        # Set up event context for this analyze session
        event_context, contextual_event_factory = self._create_event_context(
            self.conversation_config.conversation_id
        )

        # 检查最后一条消息是否是用户消息，如果是则删除它
        if conversations and conversations[-1]["role"] == "user":
            logger.info("Removing last user message before adding new user input")
            conversations.pop()

        conversations.append({"role": "user", "content": request.user_input})

        self.conversation_manager.append_message(
            conversation_id=self.conversation_config.conversation_id,
            role="user",
            content=request.user_input,
            metadata={},
        )

        self.current_conversations = conversations

        iteration_count = 0
        tool_executed = False
        should_yield_completion_event = False
        completion_event = None
        current_llm_metadata = None  # 跟踪当前轮次的 LLM 元数据
        pending_assistant_message_id = None  # 缓存待更新llm_metadata的assistant消息ID

        while True:
            iteration_count += 1
            tool_executed = False
            current_llm_metadata = None  # 重置当前轮次的 LLM 元数据
            pending_assistant_message_id = None  # 重置待更新的消息ID
            global_cancel.check_and_raise(token=self.cancel_token)
            last_message = conversations[-1]
            if last_message["role"] == "assistant":
                logger.info(
                    f"Last message is assistant, skipping LLM interaction cycle"
                )
                if should_yield_completion_event:
                    if completion_event is None:
                        yield CompletionEvent(
                            completion=AttemptCompletionTool(
                                result=last_message["content"], command=""
                            ),
                            completion_xml="",
                        )
                    else:
                        yield completion_event
                break

            assistant_buffer = ""

            pruned_conversations = self.agentic_pruner.prune_conversations(
                deepcopy(conversations)
            )
            pruned_conversations_tokens = count_tokens(
                json.dumps(pruned_conversations, ensure_ascii=False)
            )
            conversations_tokens = count_tokens(
                json.dumps(conversations, ensure_ascii=False)
            )

            yield WindowLengthChangeEvent(
                tokens_used=conversations_tokens,
                pruned_tokens_used=pruned_conversations_tokens,
                conversation_round=len(conversations) - 1,
            )

            if iteration_count > self.args.agentic_max_rounds:
                logger.info(
                    f"Agentic max rounds reached: {self.args.agentic_max_rounds}"
                )
                yield CompletionEvent(
                    completion=AttemptCompletionTool(
                        result="Agentic max rounds reached, please try again later",
                        command="",
                    ),
                    completion_xml="",
                )
                break

            # ## 实际请求大模型,并且我们会裁剪对话窗口长度
            self.callbacks.execute_callbacks(
                AgenticCallbackPoint.API_REQUEST_START, agentic_context
            )
            llm_response_gen = stream_chat_with_continue(
                llm=self.llm,
                conversations=pruned_conversations,
                llm_config={},  # Placeholder for future LLM configs
                args=self.args,
            )

            # llm_response_gen = self.llm.stream_chat_oai(
            #     conversations=conversations,
            #     delta_mode=True
            # )

            parsed_events = self.stream_and_parse_llm_response(
                llm_response_gen, agentic_context
            )

            event_count = 0
            mark_event_should_finish = False
            tool_start_time = time.time()
            for event in parsed_events:
                global_cancel.check_and_raise(token=self.cancel_token)
                event_count += 1

                if mark_event_should_finish:
                    if isinstance(event, TokenUsageEvent):
                        # 保存当前轮次的 LLM 元数据
                        current_llm_metadata = (
                            create_llm_metadata_from_token_usage_event(
                                event, conversation_round=len(conversations) - 1
                            )
                        )

                        # 如果有待更新的assistant消息，回写llm_metadata
                        if pending_assistant_message_id and current_llm_metadata:
                            try:
                                self.conversation_manager.update_message(
                                    conversation_id=self.conversation_config.conversation_id,
                                    message_id=pending_assistant_message_id,
                                    llm_metadata=current_llm_metadata,
                                )
                                logger.debug(
                                    f"Updated llm_metadata for message {pending_assistant_message_id[:8]}"
                                )
                                pending_assistant_message_id = (
                                    None  # 清除已处理的消息ID
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to update llm_metadata for message {pending_assistant_message_id[:8]}: {e}"
                                )

                        yield event
                    continue

                if isinstance(event, (LLMOutputEvent, LLMThinkingEvent)):
                    assistant_buffer += event.text
                    yield event  # Yield text/thinking immediately for display

                elif isinstance(event, ToolCallEvent):

                    ## 在这里检查异步消息，比如后台sub agent 是否执行完成，或者execute command后台任务是否完成
                    ## 如果是的话，额外添加一个 user 消息，提醒大模处理完（会丢弃掉这次）的事件然后直接返回

                    # Check async completion messages for this conversation and inject summary
                    try:
                        notifier = get_background_process_notifier()
                        conv_id = self.conversation_config.conversation_id
                        if conv_id and notifier.has_messages(conv_id):
                            msgs = notifier.poll_messages(conv_id, max_items=64)
                            if msgs:

                                def _indent_tail(text: str) -> str:
                                    # Indent helper for multi-line tails
                                    return "\n".join(
                                        ["    " + line for line in text.splitlines()]
                                    )

                                lines = [
                                    f"Background task completion notifications ({len(msgs)} items):"
                                ]
                                for m in msgs:
                                    meta = []
                                    if m.exit_code is not None:
                                        meta.append(f"exit_code={m.exit_code}")
                                    if m.duration_sec is not None:
                                        meta.append(f"duration={m.duration_sec:.2f}s")
                                    meta_str = ", ".join(meta)
                                    lines.append(
                                        f"- [{m.tool_name}] pid={m.pid} status={m.status} {('('+meta_str+')') if meta_str else ''}"
                                    )
                                    if m.agent_name or m.task:
                                        detail = []
                                        if m.agent_name:
                                            detail.append(f"agent={m.agent_name}")
                                        if m.task:
                                            detail.append(f"task={m.task}")
                                        lines.append("  " + ", ".join(detail))
                                    if m.output_tail:
                                        lines.append(
                                            "  output_tail:\n"
                                            + _indent_tail(m.output_tail)
                                        )
                                    if m.error_tail:
                                        lines.append(
                                            "  error_tail:\n"
                                            + _indent_tail(m.error_tail)
                                        )

                                summary_text = "\n".join(lines)
                                message_id = self.conversation_manager.append_message(
                                    conversation_id=conv_id,
                                    role="user",
                                    content=summary_text,
                                    metadata={},
                                )
                                conversations.append(
                                    {
                                        "role": "user",
                                        "content": append_hint_to_text(
                                            summary_text,
                                            f"message_id: {message_id[0:8]}",
                                        ),
                                    }
                                )
                                # After injecting summary, finish current LLM cycle and let next round consume it
                                break
                    except Exception as e:
                        logger.warning(f"Error checking async background messages: {e}")

                    tool_executed = True
                    tool_obj = event.tool
                    tool_name = type(tool_obj).__name__

                    tool_xml = event.tool_xml  # Already reconstructed by parser

                    self.callbacks.execute_callbacks(
                        AgenticCallbackPoint.PRE_TOOL_CALL, agentic_context
                    )
                    # Emit PreToolUse event using synchronous method
                    self._emit_pre_tool_use_event(
                        tool_name=tool_name,
                        tool_input=(
                            tool_obj.model_dump()
                            if hasattr(tool_obj, "model_dump")
                            else {}
                        ),
                        event_context=event_context,
                        contextual_event_factory=contextual_event_factory,
                    )

                    message_id = self.conversation_manager.append_message(
                        conversation_id=self.conversation_config.conversation_id,
                        role="assistant",
                        content=assistant_buffer + tool_xml,
                        metadata={},
                        llm_metadata=current_llm_metadata,
                    )

                    # 缓存message_id，等待TokenUsageEvent到达后回写llm_metadata
                    if current_llm_metadata is None:
                        pending_assistant_message_id = message_id
                    # 记录当前对话的token数量
                    conversations.append(
                        {
                            "role": "assistant",
                            "content": append_hint_to_text(
                                assistant_buffer + tool_xml,
                                f"message_id: {message_id[0:8]}",
                            ),
                        }
                    )

                    assistant_buffer = ""  # Reset buffer after tool call

                    yield event  # Yield the ToolCallEvent for display

                    # Handle AttemptCompletion separately as it ends the loop
                    if isinstance(tool_obj, AttemptCompletionTool):
                        completion_event = CompletionEvent(
                            completion=tool_obj, completion_xml=tool_xml
                        )
                        save_formatted_log(
                            self.args.source_dir,
                            json.dumps(conversations, ensure_ascii=False),
                            "agentic_conversation",
                            conversation_id=self.conversation_config.conversation_id,
                        )
                        mark_event_should_finish = True
                        should_yield_completion_event = True
                        continue

                    if isinstance(tool_obj, PlanModeRespondTool):
                        yield PlanModeRespondEvent(
                            completion=tool_obj, completion_xml=tool_xml
                        )
                        save_formatted_log(
                            self.args.source_dir,
                            json.dumps(conversations, ensure_ascii=False),
                            "agentic_conversation",
                            conversation_id=self.conversation_config.conversation_id,
                        )
                        mark_event_should_finish = True
                        continue

                    # Use the integrated tool caller with plugin support
                    try:

                        tool_result: ToolResult = self.tool_caller.call_tool(
                            tool_obj,
                            context={
                                "conversation_id": self.conversation_config.conversation_id,
                                "tool_name": tool_name,
                            },
                        )

                        result_event = ToolResultEvent(
                            tool_name=type(tool_obj).__name__, result=tool_result
                        )

                        escaped_message = xml.sax.saxutils.escape(tool_result.message)
                        content_str = (
                            str(tool_result.content)
                            if tool_result.content is not None
                            else ""
                        )
                        escaped_content = xml.sax.saxutils.escape(content_str)
                        tool_executed_xml = (
                            f"<tool_result tool_name='{type(tool_obj).__name__}' success='{str(tool_result.success).lower()}'>"
                            f"<message>{escaped_message}</message>"
                            f"<content>{escaped_content}</content>"
                            f"</tool_result>"
                        )
                    except Exception as e:
                        logger.exception(
                            f"Error in tool caller for {type(tool_obj).__name__}: {e}"
                        )
                        error_message = f"Critical Error during tool execution: {e}"
                        tool_result = ToolResult(
                            success=False, message=error_message, content=None
                        )
                        result_event = ToolResultEvent(
                            tool_name=type(tool_obj).__name__, result=tool_result
                        )
                        escaped_error = xml.sax.saxutils.escape(error_message)
                        tool_executed_xml = f"<tool_result tool_name='{type(tool_obj).__name__}' success='false'><message>{escaped_error}</message><content></content></tool_result>"

                    yield result_event  # Yield the ToolResultEvent for display

                    # Emit PostToolUse event using synchronous method
                    execution_time_ms = None

                    self.callbacks.execute_callbacks(
                        AgenticCallbackPoint.POST_TOOL_CALL, agentic_context
                    )

                    self._emit_post_tool_use_event(
                        tool_name=tool_name,
                        tool_input=(
                            tool_obj.model_dump()
                            if hasattr(tool_obj, "model_dump")
                            else {}
                        ),
                        tool_result=tool_result,
                        execution_time_ms=execution_time_ms,
                        event_context=event_context,
                        contextual_event_factory=contextual_event_factory,
                    )

                    message_id = self.conversation_manager.append_message(
                        conversation_id=self.conversation_config.conversation_id,
                        role="user",
                        content=tool_executed_xml,
                        metadata={},
                    )
                    # 添加工具结果到对话历史
                    conversations.append(
                        {
                            "role": "user",  # Simulating the user providing the tool result
                            "content": append_hint_to_text(
                                tool_executed_xml, f"message_id: {message_id[0:8]}"
                            ),
                        }
                    )

                    # 一次交互只能有一次工具，剩下的其实就没有用了，但是如果不让流式处理完，我们就无法获取服务端
                    # 返回的token消耗和计费，所以通过此标记来完成进入空转，直到流式走完，获取到最后的token消耗和计费
                    mark_event_should_finish = True

                elif isinstance(event, RetryEvent):
                    logger.info(f"Retry event occurred: {event.message}")
                    yield event

                elif isinstance(event, ErrorEvent):
                    logger.error(f"Error event occurred: {event.message}")
                    yield event  # Pass through errors
                    # Optionally stop the process on parsing errors
                    # logger.error("Stopping analyze loop due to parsing error.")
                    # return
                elif isinstance(event, TokenUsageEvent):
                    # 保存当前轮次的 LLM 元数据
                    current_llm_metadata = create_llm_metadata_from_token_usage_event(
                        event, conversation_round=len(conversations) - 1
                    )

                    # 如果有待更新的assistant消息，回写llm_metadata
                    if pending_assistant_message_id and current_llm_metadata:
                        try:
                            self.conversation_manager.update_message(
                                conversation_id=self.conversation_config.conversation_id,
                                message_id=pending_assistant_message_id,
                                llm_metadata=current_llm_metadata,
                            )
                            logger.debug(
                                f"Updated llm_metadata for message {pending_assistant_message_id[:8]}"
                            )
                            pending_assistant_message_id = None  # 清除已处理的消息ID
                        except Exception as e:
                            logger.warning(
                                f"Failed to update llm_metadata for message {pending_assistant_message_id[:8]}: {e}"
                            )

                    yield event

            if not tool_executed:
                # No tool executed in this LLM response cycle
                logger.info("LLM response finished without executing a tool.")
                # Append any remaining assistant buffer to history if it wasn't followed by a tool
                if assistant_buffer:

                    last_message = conversations[-1]
                    if last_message["role"] != "assistant":
                        logger.info("Adding new assistant message")
                        message_id = self.conversation_manager.append_message(
                            conversation_id=self.conversation_config.conversation_id,
                            role="assistant",
                            content=assistant_buffer,
                            metadata={},
                            llm_metadata=current_llm_metadata,
                        )
                        conversations.append(
                            {
                                "role": "assistant",
                                "content": append_hint_to_text(
                                    assistant_buffer, f"message_id: {message_id[0:8]}"
                                ),
                            }
                        )

                    elif last_message["role"] == "assistant":
                        logger.info("Appending to existing assistant message")
                        last_message["content"] += assistant_buffer

                # 添加系统提示，要求LLM必须使用工具或明确结束，而不是直接退出
                logger.info("Adding system reminder to use tools or attempt completion")

                conversations.append(
                    {
                        "role": "user",
                        "content": "NOTE: You must use an appropriate tool (such as read_file, write_to_file, execute_command, etc.) or explicitly complete the task (using attempt_completion). Do not provide text responses without taking concrete actions. Please select a suitable tool to continue based on the user's task.",
                    }
                )

                self.conversation_manager.append_message(
                    conversation_id=self.conversation_config.conversation_id,
                    role="user",
                    content="NOTE: You must use an appropriate tool (such as read_file, write_to_file, execute_command, etc.) or explicitly complete the task (using attempt_completion). Do not provide text responses without taking concrete actions. Please select a suitable tool to continue based on the user's task.",
                    metadata={},
                )

                continue

        logger.info(
            f"AgenticEdit analyze loop finished after {iteration_count} iterations."
        )
        self.callbacks.execute_callbacks(
            AgenticCallbackPoint.CONVERSATION_END, agentic_context
        )
        save_formatted_log(
            self.args.source_dir,
            json.dumps(conversations, ensure_ascii=False),
            "agentic_conversation",
            conversation_id=self.conversation_config.conversation_id,
        )

    def stream_and_parse_llm_response(
        self,
        generator: Generator[Tuple[str, Any], None, None],
        agentic_context: AgenticContext,
    ) -> Generator[
        Union[LLMOutputEvent, LLMThinkingEvent, ToolCallEvent, ErrorEvent], None, None
    ]:
        """
        Streamingly parses the LLM response generator, distinguishing between
        plain text, thinking blocks, and tool usage blocks, yielding corresponding Event models.

        Args:
            generator: An iterator yielding (content, metadata) tuples from the LLM stream.

        Yields:
            Union[LLMOutputEvent, LLMThinkingEvent, ToolCallEvent, ErrorEvent]: Events representing
            different parts of the LLM's response.
        """
        buffer = ""
        in_tool_block = False
        in_thinking_block = False
        current_tool_tag = None
        tool_start_pattern = re.compile(r"<([a-zA-Z0-9_]+)>")  # Matches tool tags
        thinking_start_tag = "<thinking>"
        thinking_end_tag = "</thinking>"

        def parse_tool_xml(tool_xml: str, tool_tag: str) -> Optional[BaseTool]:
            """Minimal parser for tool XML string."""
            params = {}
            try:
                # Find content between <tool_tag> and </tool_tag>
                inner_xml_match = re.search(
                    rf"<{tool_tag}>(.*?)</{tool_tag}>", tool_xml, re.DOTALL
                )
                if not inner_xml_match:
                    logger.error(
                        f"Could not find content within <{tool_tag}>...</{tool_tag}>"
                    )
                    return None
                inner_xml = inner_xml_match.group(1).strip()

                # Find <param>value</param> pairs within the inner content
                pattern = re.compile(r"<([a-zA-Z0-9_]+)>(.*?)</\1>", re.DOTALL)
                for m in pattern.finditer(inner_xml):
                    key = m.group(1)
                    # Basic unescaping (might need more robust unescaping if complex values are used)
                    val = xml.sax.saxutils.unescape(m.group(2))
                    params[key] = val

                tool_cls = TOOL_MODEL_MAP.get(tool_tag)
                if tool_cls:
                    # Attempt to handle boolean conversion specifically for requires_approval
                    if "requires_approval" in params:
                        params["requires_approval"] = (
                            params["requires_approval"].lower() == "true"
                        )
                    # Attempt to handle JSON parsing for ask_followup_question_tool
                    if tool_tag == "ask_followup_question" and "options" in params:
                        try:
                            params["options"] = json.loads(params["options"])
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Could not decode JSON options for ask_followup_question_tool: {params['options']}"
                            )
                            # Keep as string or handle error? Let's keep as string for now.
                            pass
                    if tool_tag == "plan_mode_respond" and "options" in params:
                        try:
                            params["options"] = json.loads(params["options"])
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Could not decode JSON options for plan_mode_respond_tool: {params['options']}"
                            )
                    # Handle recursive for list_files
                    if tool_tag == "list_files" and "recursive" in params:
                        params["recursive"] = params["recursive"].lower() == "true"
                    return tool_cls(**params)
                else:
                    logger.error(f"Tool class not found for tag: {tool_tag}")
                    return None
            except Exception as e:
                logger.exception(
                    f"Failed to parse tool XML for <{tool_tag}>: {e}\nXML:\n{tool_xml}"
                )
                return None

        last_metadata = None
        retry_count = 0
        max_retries = self.args.agentic_connection_retries

        while True:
            try:
                for content_chunk, metadata in generator:
                    global_cancel.check_and_raise(token=self.cancel_token)
                    if not content_chunk:
                        last_metadata = metadata
                        continue

                    last_metadata = metadata
                    buffer += content_chunk

                    while True:
                        # Check for transitions: thinking -> text, tool -> text, text -> thinking, text -> tool
                        next_event_pos = len(buffer)
                        found_event = False

                        # 1. Check for </thinking> if inside thinking block
                        if in_thinking_block:
                            end_think_pos = buffer.find(thinking_end_tag)
                            if end_think_pos != -1:
                                thinking_content = buffer[:end_think_pos]
                                yield LLMThinkingEvent(text=thinking_content)
                                buffer = buffer[end_think_pos + len(thinking_end_tag) :]
                                in_thinking_block = False
                                found_event = True
                                continue  # Restart loop with updated buffer/state
                            else:
                                # Need more data to close thinking block
                                break

                        # 2. Check for </tool_tag> if inside tool block
                        elif in_tool_block:
                            end_tag = f"</{current_tool_tag}>"
                            end_tool_pos = buffer.find(end_tag)
                            if end_tool_pos != -1:
                                tool_block_end_index = end_tool_pos + len(end_tag)
                                tool_xml = buffer[:tool_block_end_index]
                                tool_obj = parse_tool_xml(tool_xml, current_tool_tag)

                                if tool_obj:
                                    # Reconstruct the XML accurately here AFTER successful parsing
                                    # This ensures the XML yielded matches what was parsed.
                                    reconstructed_xml = self._reconstruct_tool_xml(
                                        tool_obj
                                    )
                                    if reconstructed_xml.startswith("<error>"):
                                        yield ErrorEvent(
                                            message=f"Failed to reconstruct XML for tool {current_tool_tag}"
                                        )
                                    else:
                                        yield ToolCallEvent(
                                            tool=tool_obj, tool_xml=reconstructed_xml
                                        )
                                else:
                                    # yield ErrorEvent(message=f"Failed to parse tool: <{current_tool_tag}>")
                                    # Optionally yield the raw XML as plain text?
                                    yield LLMOutputEvent(
                                        text=f"Failed to parse tool: <{current_tool_tag}> {tool_xml}"
                                    )

                                buffer = buffer[tool_block_end_index:]
                                in_tool_block = False
                                current_tool_tag = None
                                found_event = True
                                continue  # Restart loop
                            else:
                                # Need more data to close tool block
                                break

                        # 3. Check for <thinking> or <tool_tag> if in plain text state
                        else:
                            start_think_pos = buffer.find(thinking_start_tag)
                            tool_match = tool_start_pattern.search(buffer)
                            start_tool_pos = tool_match.start() if tool_match else -1
                            tool_name = tool_match.group(1) if tool_match else None

                            # Determine which tag comes first (if any)
                            first_tag_pos = -1
                            is_thinking = False
                            is_tool = False

                            if start_think_pos != -1 and (
                                start_tool_pos == -1 or start_think_pos < start_tool_pos
                            ):
                                first_tag_pos = start_think_pos
                                is_thinking = True
                            elif start_tool_pos != -1 and (
                                start_think_pos == -1
                                or start_tool_pos < start_think_pos
                            ):
                                # Check if it's a known tool
                                if tool_name in TOOL_MODEL_MAP:
                                    first_tag_pos = start_tool_pos
                                    is_tool = True
                                else:
                                    # Unknown tag, treat as text for now, let buffer grow
                                    pass

                            if (
                                first_tag_pos != -1
                            ):  # Found either <thinking> or a known <tool>
                                # Yield preceding text if any
                                preceding_text = buffer[:first_tag_pos]
                                if preceding_text:
                                    yield LLMOutputEvent(text=preceding_text)

                                # Transition state
                                if is_thinking:
                                    buffer = buffer[
                                        first_tag_pos + len(thinking_start_tag) :
                                    ]
                                    in_thinking_block = True
                                elif is_tool:
                                    # Keep the starting tag
                                    buffer = buffer[first_tag_pos:]
                                    in_tool_block = True
                                    current_tool_tag = tool_name

                                found_event = True
                                continue  # Restart loop

                            else:
                                # No tags found, or only unknown tags found. Need more data or end of stream.
                                # Yield text chunk but keep some buffer for potential tag start
                                # Keep last 100 chars
                                split_point = max(0, len(buffer) - 100)
                                text_to_yield = buffer[:split_point]
                                if text_to_yield:
                                    yield LLMOutputEvent(text=text_to_yield)
                                    buffer = buffer[split_point:]
                                break  # Need more data

                        # If no event was processed in this iteration, break inner loop
                        if not found_event:
                            break
                # 如果成功执行完毕，跳出重试循环
                break

            except Exception as e:

                if isinstance(e, CancelRequestedException):
                    raise e

                retry_count += 1

                # 获取完整的堆栈信息并截取最后200个字符
                import traceback

                full_traceback = traceback.format_exc()
                error_detail = (
                    full_traceback[-300:]
                    if len(full_traceback) > 300
                    else full_traceback
                )

                # 检查是否需要重试
                if max_retries == -1 or retry_count <= max_retries:
                    retry_info = f"Connection error, retrying attempt {retry_count}"
                    if max_retries != -1:
                        retry_info += f" (max {max_retries} retries)"
                    else:
                        retry_info += " (infinite retry mode)"

                    logger.warning(
                        f"LLM connection failed: {error_detail}, {retry_info}"
                    )
                    yield LLMOutputEvent(
                        text=f"\n⚠️ {retry_info}, waiting 10 seconds before continuing...\nError: {error_detail}\n"
                    )

                    # 等待10秒
                    time.sleep(10)

                    # 重置状态以便重试
                    buffer = ""
                    in_tool_block = False
                    in_thinking_block = False
                    current_tool_tag = None

                    continue  # 继续重试循环
                else:
                    # 超过最大重试次数，抛出异常
                    logger.error(
                        f"LLM connection failed after {max_retries} retries, error: {error_detail}"
                    )
                    yield ErrorEvent(
                        message=f"Connection failed after {max_retries} retries, please try again later. Error: {error_detail}"
                    )
                    break

        # After generator exhausted, yield any remaining content
        if in_thinking_block:
            # Unterminated thinking block
            yield RetryEvent(message="Stream ended with unterminated <thinking> block.")
            if buffer:
                # Yield remaining as thinking
                yield LLMThinkingEvent(text=buffer)
        elif in_tool_block:
            # Unterminated tool block
            yield RetryEvent(
                message=f"Stream ended with unterminated <{current_tool_tag}> block."
            )
            if buffer:
                yield LLMOutputEvent(text=buffer)  # Yield remaining as text
        elif buffer:
            # Yield remaining plain text
            yield LLMOutputEvent(text=buffer)

        # 这个要放在最后，防止其他关联的多个事件的信息中断
        yield TokenUsageEvent(usage=last_metadata)

    def apply_pre_changes(self):
        return self.change_manager.apply_pre_changes()

    def handle_rollback_command(self, command: str) -> str:
        return self.change_manager.handle_rollback_command(command)

    def apply_changes(self):
        return self.change_manager.apply_changes()

    def _create_event_context(
        self, conversation_id: Optional[str]
    ) -> Tuple[EventContext, EventFactory]:
        """Create event context and contextual event factory for the current analyze session."""
        event_context = EventContext(
            agent_id=f"agentic_edit_{int(time.time())}",
            conversation_id=conversation_id,
            metadata={
                "source_dir": self.args.source_dir,
                "model": self.args.model,
                "timestamp": time.time(),
            },
        )

        contextual_event_factory = self.event_factory.create_with_context(event_context)

        return event_context, contextual_event_factory

    def _emit_pre_tool_use_event(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        event_context: EventContext,
        contextual_event_factory: EventFactory,
    ) -> None:
        """Emit PreToolUse event using synchronous method with automatic async/sync conversion."""
        try:
            pre_tool_event = contextual_event_factory.create_pre_tool_use_event(
                tool_name=tool_name, tool_input=tool_input, context=event_context
            )
            # Use sync emit method (auto-generated by AsyncSyncMixin)
            self.event_emitter.emit_sync(pre_tool_event)
            logger.debug(f"Emitted PreToolUse event for {tool_name}")
        except Exception as e:
            logger.warning(f"Failed to emit PreToolUse event: {e}")

    def _emit_post_tool_use_event(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: Any,
        execution_time_ms: Optional[float],
        event_context: EventContext,
        contextual_event_factory: EventFactory,
    ) -> None:
        """Emit PostToolUse event using synchronous method with automatic async/sync conversion."""
        try:
            post_tool_event = contextual_event_factory.create_post_tool_use_event(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=(
                    tool_result.model_dump()
                    if hasattr(tool_result, "model_dump")
                    else str(tool_result)
                ),
                success=tool_result.success,
                execution_time_ms=execution_time_ms,
                context=event_context,
            )
            # Use sync emit method (auto-generated by AsyncSyncMixin)
            self.event_emitter.emit_sync(post_tool_event)
            logger.debug(
                f"Emitted PostToolUse event for {tool_name} (success={tool_result.success})"
            )
        except Exception as e:
            logger.warning(f"Failed to emit PostToolUse event: {e}")

    def _init_event_system(self):
        """Initialize the agent events and hooks system with automatic async/sync support."""
        try:
            # Set up hook manager with AsyncSyncMixin support
            self.hook_manager = HookManager(
                cwd=self.args.source_dir, command_timeout=30000  # 30 second timeout
            )

            # Set up event system with hook integration
            event_config = EventEmitterConfig(
                enable_logging=False, max_listeners=100, hook_manager=self.hook_manager
            )
            self.event_emitter, self.event_factory = create_event_system(event_config)

            logger.info(
                "Agent events and hooks system initialized successfully with async/sync support"
            )

        except Exception as e:
            logger.warning(f"Failed to initialize event system: {e}")
            # Create minimal fallback system without hook integration
            self.hook_manager = None
            self.event_emitter, self.event_factory = create_event_system()

    def get_conversation_message_range(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取当前对话的第一个和最后一个消息ID

        Returns:
            Tuple[Optional[str], Optional[str]]: (first_message_id, last_message_id)
        """
        try:
            if (
                not self.conversation_config
                or not self.conversation_config.conversation_id
            ):
                return None, None

            conversation_id = self.conversation_config.conversation_id
            messages = self.conversation_manager.get_messages(conversation_id)

            if not messages:
                return None, None

            first_message_id = messages[0].get("message_id") if messages else None
            last_message_id = messages[-1].get("message_id") if messages else None

            return first_message_id, last_message_id
        except Exception as e:
            logger.error(f"Failed to get conversation message range: {e}")
            return None, None
