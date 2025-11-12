from enum import Enum
import json
import os
import time
from pydantic import BaseModel, Field
import byzerllm
from typing import List, Dict, Any, Union, Callable, Optional
from autocoder.common.printer import Printer
from rich.console import Console
from rich.panel import Panel

from autocoder.common.result_manager import ResultManager
from autocoder.utils.auto_coder_utils.chat_stream_out import stream_out
from byzerllm.utils.str2model import to_model
from autocoder.common import git_utils
from autocoder.commands.tools import AutoCommandTools
from autocoder.common import AutoCoderArgs
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common import detect_env
from autocoder.common import shells
from loguru import logger
from autocoder.utils import llms as llms_utils
from autocoder.common.tokens import count_string_tokens as count_tokens
from autocoder.common.global_cancel import global_cancel
from autocoder.common.auto_configure import config_readme
from autocoder.utils.auto_project_type import ProjectTypeAnalyzer
from rich.text import Text
from autocoder.common.mcp_tools.server import get_mcp_server, McpServerInfoRequest
from autocoder.common.action_yml_file_manager import ActionYmlFileManager
from autocoder.events.event_manager_singleton import get_event_manager
from autocoder.events import event_content as EventContentCreator
from autocoder.run_context import get_run_context
from autocoder.common.stream_out_type import AgenticFilterStreamOutType
from autocoder.common.core_config import get_memory_manager


class AgenticFilterRequest(BaseModel):
    user_input: str


class FileOperation(BaseModel):
    path: str
    operation: str  # e.g., "MODIFY", "REFERENCE", "ADD", "REMOVE"


class AgenticFilterResponse(BaseModel):
    files: List[FileOperation]  # File list containing path and operation fields
    reasoning: str  # Decision process explanation


class CommandSuggestion(BaseModel):
    command: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str


class AutoCommandResponse(BaseModel):
    suggestions: List[CommandSuggestion]
    reasoning: Optional[str] = None


class AutoCommandRequest(BaseModel):
    user_input: str


class AgenticFilter:
    def __init__(
        self,
        llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM],
        conversation_history: List[Dict[str, Any]],
        args: AutoCoderArgs,
    ):
        self.llm = llm
        self.args = args
        self.printer = Printer()
        self.tools = AutoCommandTools(args=args, llm=self.llm)
        self.result_manager = ResultManager(source_dir=args.source_dir)
        # Use existing args for max iterations
        self.max_iterations = args.auto_command_max_iterations
        self.conversation_history = conversation_history
        self.project_type_analyzer = ProjectTypeAnalyzer(
            args=args, llm=self.llm)

        # Initialize AutoCoderArgs parser for flexible parameter parsing
        self.args_parser = AutoCoderArgsParser()
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
            self.mcp_server_info = ""
        self.memory_config = get_memory_manager()

    def _get_parsed_safe_zone_tokens(self) -> int:
        """
        Parse conversation_prune_safe_zone_tokens parameter, supports multiple formats

        Returns:
            Parsed token count
        """
        return self.args_parser.parse_conversation_prune_safe_zone_tokens(
            self.args.conversation_prune_safe_zone_tokens,
            self.args.code_model
        )

    @byzerllm.prompt()
    def _analyze(self, request: AgenticFilterRequest) -> str:
        """        
        ## Current User Environment Information:
        <os_info>
        Operating System: {{ env_info.os_name }} {{ env_info.os_version }}
        OS Distribution: {{ os_distribution }}
        Python Version: {{ env_info.python_version }}
        Terminal Type: {{ env_info.shell_type }}
        Terminal Encoding: {{ env_info.shell_encoding }}
        Current User: {{ current_user }}

        {%- if shell_type %}
        Script Type: {{ shell_type }}
        {%- endif %}

        {%- if env_info.conda_env %}
        Conda Environment: {{ env_info.conda_env }}
        {%- endif %}
        {%- if env_info.virtualenv %}
        Virtual Environment: {{ env_info.virtualenv }}
        {%- endif %}
        </os_info>

        Current Project Root Directory:
        {{ current_project }}

        {% if current_files %}
        ## Current User Manually Added File List:
        <current_files>
        {% for file in current_files %}
        - {{ file }}
        {% endfor %}
        </current_files>
        {% endif %}
        
        ## Available Function List:
        {{ available_commands }}  

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

        ## execute_shell_command

        When to use:
        - When you want to list all AC modules in the project
        - When you want to list all AC modules in a specific directory

        Example:

        execute_shell_command(command="find . -name '*.ac.mod.md' -type f | sed 's|/[^/]*$||' | sort | uniq")


        ## read_files

        When to use:
        - Use the this tool to retrieve comprehensive information about an AC module
        - The tool reads the `.ac.mod.md` file and provides structured information about the module        

        Example:

        read_files(paths="src/autocoder/agent/.ac.mod.md")        
               
       ====     
        
        {% if conversation_history %}
        ## Conversation History
        <conversation_history>
        {% for msg in conversation_history %}
        **{{ msg.role }}**: {{ msg.content }}
        {% endfor %}
        </conversation_history>
        {% endif %}
        
        ## Practical Guidance for Task Completion
        {{ command_combination_readme }}

        ## Your Task and Requirements
        You are a code analysis expert who needs to analyze project-related files based on user requirements. Your job is to determine:

        1. **Files to Modify** (marked as "MODIFY"): Files that need direct changes
        2. **Files to Reference** (marked as "REFERENCE"): Files needed for understanding requirements or implementing modifications
        3. **Files to Add** (marked as "ADD"): New files that may need to be created to fulfill requirements
        4. **Files to Remove** (marked as "REMOVE"): Files that may need to be deleted to fulfill requirements

        Please analyze through the following steps:
        1. Understand the core objectives of user requirements
        2. Use the provided tool functions to explore project structure
        3. Analyze the content and dependencies of relevant files
        4. Determine the list of files to modify, reference, add, or remove

        ## Return Format Requirements
        The return format must be strict JSON format:

        ```json
        {
            "suggestions": [
                {
                    "command": "function_name",
                    "parameters": {},
                    "confidence": 0.9,
                    "reasoning": "recommendation_reason"
                }
            ],
            "reasoning": "overall_reasoning_explanation"
        }
        ```

        Please return the first suggested function call. I will provide you with the execution results of each function, and then you can determine the next function to execute based on these results until the analysis is complete.
        """
        env_info = detect_env()
        shell_type = "bash"
        if shells.is_running_in_cmd():
            shell_type = "cmd"
        elif shells.is_running_in_powershell():
            shell_type = "powershell"
        return {
            "user_input": request.user_input,
            "current_files": self.memory_config.get_current_files(),
            "conversation_history": self.conversation_history,
            "available_commands": self._command_readme.prompt(),
            "current_conf": json.dumps(self.memory_config.get_all_config(), indent=2),
            "env_info": env_info,
            "shell_type": shell_type,
            "shell_encoding": shells.get_terminal_encoding(),
            "conversation_safe_zone_tokens": self._get_parsed_safe_zone_tokens(),
            "os_distribution": shells.get_os_distribution(),
            "current_user": shells.get_current_username(),
            "command_combination_readme": self._command_combination_readme.prompt(
                user_input=request.user_input
            ),
            "current_project": os.path.abspath(self.args.source_dir or "."),
        }  # type: ignore

    @byzerllm.prompt()
    def _command_combination_readme(self, user_input: str) -> str:
        """
        ## Recommended Operation Flow
        1.  **Understand Requirements**: Analyze user input `{{ user_input }}`.
        2.  **Explore Project**:
            *   List all current AC modules using `execute_shell_command` to enumerate them, then read `.ac.mod.md` files to understand the purpose of each AC module.
            *   Use `list_files` to progressively understand project structure and determine files that need attention.
            *   If user mentions file names, use `find_files_by_name`; if user mentions keywords, use `find_files_by_content` to locate potentially relevant files.            
        3.  **In-depth Analysis**:
            *   Use `read_files` to read key file contents for confirmation. If files are too large, use `line_ranges` parameter for segmented reading.
            *   If necessary, use `execute_shell_command` to execute code or commands for more complex analysis.
        4.  **Iterative Decision Making**: Based on tool return results, you may need to call different tools multiple times to gradually narrow down scope or obtain more information.        
        6.  **Final Response**: When you have determined all files that need to be referenced and modified, you **must** call the `output_result` tool and provide a JSON string that meets its format requirements as the `response` parameter.
            The required JSON format is:
            ```json
            {
                "files": [
                    {"path": "/path/to/file1.py", "operation": "MODIFY"},
                    {"path": "/path/to/file2.md", "operation": "REFERENCE"},
                    {"path": "/path/to/new_file.txt", "operation": "ADD"},
                    {"path": "/path/to/old_file.log", "operation": "REMOVE"}
                ],
                "reasoning": "Detailed explanation of how you analyzed and used tools to arrive at this file list."
            }
            ```

        ** Very Important Note **
        You should try to read the .ac.mod.md file for every directory to better understand the directory content. For example, directory description information for {{ project_path }}/src/abc/bbc would be located in {{ project_path }}/src/abc/bbc/.ac.mod.md file.
        You can use the read_files function to read these files, helping you better choose which files to read in detail.        
        """
        return {
            "project_path": os.path.abspath(self.args.source_dir or ".")
        }  # type: ignore

    @byzerllm.prompt()
    def _execute_command_result(self, result: str) -> str:
        """
        Based on function execution results, return the next function.

        Below is our previous function execution result:

        <function_result>
        {{ result }}
        </function_result>

        Please return the next function based on the command execution results and previous conversation.

        *** Very Important Notes ***
        1. If you think you have collected enough information to determine the final file list, you must call `output_result` with a JSON string in the required format as the `response` parameter. Maximum {{ max_iterations }} tool calls allowed.
            ```json
            {
                "files": [
                    {"path": "/path/to/file1.py", "operation": "MODIFY"},
                    {"path": "/path/to/file2.md", "operation": "REFERENCE"},
                    {"path": "/path/to/new_file.txt", "operation": "ADD"},
                    {"path": "/path/to/old_file.log", "operation": "REMOVE"}
                ],
                "reasoning": "Detailed explanation of how you analyzed and used tools to arrive at this file list."
            }
            ```
        2. You can try at most {{ auto_command_max_iterations }} times. If {{ auto_command_max_iterations }} attempts do not meet requirements, do not return any function and ensure suggestions is empty.
        """
        return {
            "auto_command_max_iterations": self.args.auto_command_max_iterations,
            "conversation_safe_zone_tokens": self._get_parsed_safe_zone_tokens(),
        }  # type: ignore

    @byzerllm.prompt()
    def _command_readme(self) -> str:
        """
        You have the following functions available:
        <commands>        
        <command>
        <name>execute_shell_command</name>
        <description>Execute specified shell scripts. Mainly used for compilation, running, testing, and other tasks.</description>
        <usage>
         This command accepts one parameter 'command', which is the shell script string to execute.


         Usage example:

         execute_shell_command(command="ls -l")

         Notes:
         - Scripts will be executed in the project root directory
         - Scripts containing rm commands are prohibited
         - Output results will be returned to the user
         - When executing this command, you need to ask the user through ask_user whether they agree to execute it. If the user refuses, do not execute the script.
        </usage>
        </command>                

        <command>
        <name>list_files</name>
        <description>list_files views all files in a specific directory</description>
        <usage>
         This command accepts one parameter 'path', which is the directory path to view.
         Usage example:
         list_files(path="path/to/dir")

        </usage>
        </command>

        <command>
        <name>read_files</name>
        <description>Read specified file content (supports line range specification), supports filename or absolute path.</description>
        <usage>
        This function is used to read specified file content.

        Parameter description:
        1. paths (str):
           - Comma-separated list of file paths
           - Supports two formats:
             a) Filename: If multiple files match this name, the first match will be selected
             b) Absolute path: Directly specify the complete file path
           - Example: "main.py,utils.py" or "/path/to/main.py,/path/to/utils.py"
           - Recommendation: Each call should read one file, maximum of 3 files.

        2. line_ranges (Optional[str]):
           - Optional parameter to specify the specific line ranges to read for each file
           - Format description:
             * Use commas to separate line ranges for different files
             * Each file can specify multiple line ranges, separated by /
             * Each line range uses - to connect start and end lines
           - Examples:
             * "1-100,2-50" (specify one line range for each of two files)
             * "1-100/200-300,50-100" (first file has two line ranges, second file has one line range)
           - Note: The number of files in line_ranges must match the number of files in paths, otherwise an error will be thrown

        Return value:
        - Returns str type, containing content of all requested files
        - Each file content will be annotated with file path and line range information (if line ranges are specified)

        Usage examples:

        read_files(paths="main.py,utils.py", line_ranges="1-100/200-300,50-100")

        read_files(paths="main.py,utils.py")

        You can use get_project_structure function to get project structure, then use get_project_map function to get a file's purpose, symbol list, and
        file size (token count), and finally use read_files function to read file content, helping you make better decisions. If the file to be read is too large,

        Special note: When using read_files, do not read more than 1 file at a time, only read 200 lines each time. If you find the read content is insufficient, continue reading the next 200 lines.

        </usage>
        </command>

        <command>
        <name>find_files_by_name</name>
        <description>Search files based on keywords in filename.</description>
        <usage>
         This command accepts one parameter 'keyword', which is the keyword string to search for.

         Usage example:

         find_files_by_name(keyword="test")

         Notes:
         - Search is case-insensitive
         - Returns all matching file paths, comma-separated
        </usage>
        </command>

        <command>
        <name>find_files_by_content</name>
        <description>Search files based on keywords in file content.</description>
        <usage>
         This command accepts one parameter 'keyword', which is the keyword string to search for.

         Usage example:

         find_files_by_content(keyword="TODO")

         Notes:
         - Search is case-insensitive
         - If too many results, only returns the first 10 matches
        </usage>
        </command>

        <command>
        <name>read_file_with_keyword_ranges</name>
        <description>Read lines containing specified keywords and their surrounding lines within specified range.</description>
        <usage>
         This function is used to read lines containing keywords and their surrounding lines within specified range.

         Parameter description:
         1. file_path (str): File path, can be relative or absolute path
         2. keyword (str): Keyword to search for
         3. before_size (int): Number of lines to read before keyword line, default 100
         4. after_size (int): Number of lines to read after keyword line, default 100

         Return value:
         - Returns str type, containing keyword lines and their surrounding lines within specified range
         - Format as follows:
           ```
           ##File: /path/to/file.py
           ##Line: 10-20

           Content
           ```

         Usage example:
         read_file_with_keyword_ranges(file_path="main.py", keyword="TODO", before_size=5, after_size=5)

         Notes:
         - If there are multiple matching keywords in the file, multiple content blocks will be returned
         - Search is case-insensitive
        </usage>
        </command>

        <command>
        <name>output_result</name>
        <description>Output the final required result</description>
        <usage>
         Only one parameter:
         response: String type, content to return to user. response must satisfy the following Json format:

         ```json
        {
            "files": [
                {"path": "/path/to/file1.py", "operation": "MODIFY"},
                {"path": "/path/to/file2.md", "operation": "REFERENCE"},
                {"path": "/path/to/new_file.txt", "operation": "ADD"},
                {"path": "/path/to/old_file.log", "operation": "REMOVE"}
            ],
            "reasoning": "Detailed explanation of how you analyzed and used tools to arrive at this file list."
        }
        ```

        Usage example:
        output_result(response='{"files": [{"path": "/path/to/file1.py", "operation": "MODIFY"}, {"path": "/path/to/file2.md", "operation": "REFERENCE"}, {"path": "/path/to/new_file.txt", "operation": "ADD"}, {"path": "/path/to/old_file.log", "operation": "REMOVE"}], "reasoning": "Detailed explanation of how you analyzed and used tools to arrive at this file list."}')
        </usage>
        </command>

        <command>
        <name>count_file_tokens</name>
        <description>Calculate the token count of specified file.</description>
        <usage>
         This function accepts one parameter file_path, which is the file path to calculate.

         Usage example:
         count_file_tokens(file_path="full")

         Notes:
         - Return value is int type, representing the token count of the file.

        </usage>
        </command>

        <command>
        <name>count_string_tokens</name>
        <description>Calculate the token count of specified string.</description>
        <usage>
         This function accepts one parameter text, which is the text to calculate.

         Usage example:
         count_string_tokens(text="Hello, World")

         Notes:
         - Return value is int type, representing the token count of the text.

        </usage>
        </command>

        <command>
        <n>find_symbol_definition</n>
        <description>Find the file path where the specified symbol is defined.</description>
        <usage>
         This function accepts one parameter symbol, which is the symbol name to search for.

         Usage examples:
         find_symbol_definition(symbol="MyClass")
         find_symbol_definition(symbol="process_data")

         Notes:
         - Return value is string, containing file path list where symbols are defined, comma-separated
         - Supports exact matching and fuzzy matching (case-insensitive)
         - If no matches found, returns prompt information

        </usage>
        </command>        
        <command>
        <n>execute_mcp_server</n>
        <description>Execute MCP server</description>
        <usage>
         This function accepts one parameter query, which is the MCP server query string to execute.

         You can decide whether to call this function based on the connected mcp server information below. Note that this function will automatically
         select the appropriate mcp server to execute based on your query. If you want a specific server to execute, you can specify which server you want in the query.

         <mcp_server_info>
         {{ mcp_server_info }}
         </mcp_server_info>

        </usage>
        </command>
        """
        return {
            "config_readme": config_readme.prompt(),
            "mcp_server_info": self.mcp_server_info,
        }

    def analyze(self, request: AgenticFilterRequest) -> Optional[AgenticFilterResponse]:
        # Get prompt content
        prompt = self._analyze.prompt(request)

        # Get the recent 8 history records of current project changes
        action_yml_file_manager = ActionYmlFileManager(self.args.source_dir)
        history_tasks = action_yml_file_manager.to_tasks_prompt(limit=8)
        new_messages = []
        if self.args.enable_task_history:
            new_messages.append({"role": "user", "content": history_tasks})
            new_messages.append(
                {
                    "role": "assistant",
                    "content": "Okay, I understand the recent project changes from tasks, and I will refer to these to better understand your requirements.",
                }
            )

        # Construct conversation context
        conversations = new_messages + [{"role": "user", "content": prompt}]

        # Use stream_out for output
        printer = Printer()
        title = printer.get_message_from_key("auto_command_analyzing")
        final_title = printer.get_message_from_key("auto_command_analyzed")

        def extract_command_response(content: str) -> str:
            # Extract JSON and convert to AutoCommandResponse
            try:
                response = to_model(content, AutoCommandResponse)
                if response.suggestions:
                    command = response.suggestions[0].command
                    parameters = response.suggestions[0].parameters
                    if parameters:
                        params_str = ", ".join(
                            [f"{k}={v}" for k, v in parameters.items()]
                        )
                    else:
                        params_str = ""
                    return f"{command}({params_str})"
                else:
                    return printer.get_message_from_key("satisfied_prompt")
            except Exception as e:
                logger.error(f"Error extracting command response: {str(e)}")
                return content

        result_manager = ResultManager()
        success_flag = False

        get_event_manager(self.args.event_file).write_result(
            EventContentCreator.create_result(
                content=printer.get_message_from_key("agenticFilterContext")),
            metadata={
                "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
            }
        )

        while True:
            global_cancel.check_and_raise(token=self.args.cancel_token)
            # print(json.dumps(conversations, ensure_ascii=False, indent=4))
            model_name = ",".join(llms_utils.get_llm_names(self.llm))
            start_time = time.monotonic()
            result, last_meta = stream_out(
                self.llm.stream_chat_oai(
                    conversations=conversations, delta_mode=True),
                model_name=model_name,
                title=title,
                final_title=final_title,
                display_func=extract_command_response,
                args=self.args,
                cancel_token=self.args.cancel_token,
                extra_meta={
                    "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
                },
            )

            if last_meta:
                elapsed_time = time.monotonic() - start_time
                speed = last_meta.generated_tokens_count / elapsed_time

                # Get model info for pricing
                from autocoder.utils import llms as llm_utils

                model_info = (
                    llm_utils.get_model_info(
                        model_name, self.args.product_mode) or {}
                )
                input_price = model_info.get(
                    "input_price", 0.0) if model_info else 0.0
                output_price = (
                    model_info.get("output_price", 0.0) if model_info else 0.0
                )

                # Calculate costs
                input_cost = (
                    last_meta.input_tokens_count * input_price
                ) / 1000000  # Convert to millions
                output_cost = (
                    last_meta.generated_tokens_count * output_price
                ) / 1000000  # Convert to millions

                temp_content = printer.get_message_from_key_with_format(
                    "stream_out_stats",
                    model_name=",".join(llms_utils.get_llm_names(self.llm)),
                    elapsed_time=elapsed_time,
                    first_token_time=last_meta.first_token_time,
                    input_tokens=last_meta.input_tokens_count,
                    output_tokens=last_meta.generated_tokens_count,
                    input_cost=round(input_cost, 4),
                    output_cost=round(output_cost, 4),
                    speed=round(speed, 2),
                )
                printer.print_str_in_terminal(temp_content)
                get_event_manager(self.args.event_file).write_result(
                    EventContentCreator.create_result(
                        content=EventContentCreator.ResultTokenStatContent(
                            model_name=model_name,
                            elapsed_time=elapsed_time,
                            first_token_time=last_meta.first_token_time,
                            input_tokens=last_meta.input_tokens_count,
                            output_tokens=last_meta.generated_tokens_count,
                            input_cost=round(input_cost, 4),
                            output_cost=round(output_cost, 4),
                            speed=round(speed, 2),
                        )
                    ).to_dict()
                )

            conversations.append({"role": "assistant", "content": result})
            # Extract JSON and convert to AutoCommandResponse
            try:
                response = to_model(result, AutoCommandResponse)
            except Exception as e:
                error_content = printer.get_message_from_key_with_format(
                    "invalid_output_format_error",
                    error=str(e)
                )
                # If this key doesn't exist, use default error message
                if not error_content or error_content.startswith("Message key"):
                                    error_content = f'''Invalid output format, error message: {str(e)}
Please output in the required JSON format:
```json
{{{{
    "files": [
        {{"path": "/path/to/file1.py", "operation": "MODIFY"}},
        {{"path": "/path/to/file2.md", "operation": "REFERENCE"}},
        {{"path": "/path/to/new_file.txt", "operation": "ADD"}},
        {{"path": "/path/to/old_file.log", "operation": "REMOVE"}}
    ],
                    "reasoning": "Detailed explanation of how you analyzed and used tools to arrive at this file list."
}}}}
```                    
'''
                conversations.append(
                    {"role": "user", "content": error_content})
                continue

            if not response or not response.suggestions:
                break

            # Execute command
            command = response.suggestions[0].command
            parameters = response.suggestions[0].parameters

                            # Print the command being executed
            temp_content = printer.get_message_from_key_with_format(
                "auto_command_executing", command=command
            )
            printer.print_str_in_terminal(temp_content, style="blue")

            get_event_manager(self.args.event_file).write_result(
                EventContentCreator.create_result(
                    content=EventContentCreator.ResultCommandPrepareStatContent(
                        command=command, parameters=parameters
                    ).to_dict()
                ), metadata={
                    "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
                }
            )
            try:
                self.execute_auto_command(command, parameters)
            except Exception as e:
                error_content = f"Command execution failed, error message: {e}"
                conversations.append(
                    {"role": "user", "content": error_content})
                continue

            content = ""
            last_result = result_manager.get_last()
            if last_result:
                action = last_result.meta["action"]
                if action == "coding":
                    # If the previous step was coding, need to include before and after changes as context
                    changes = git_utils.get_changes_by_commit_message(
                        "", last_result.meta["commit_message"]
                    )
                    if changes.success:
                        for file_path, change in changes.changes.items():
                            if change:
                                content += f"## File: {file_path}[Before Changes]\n{change.before or 'New File'}\n\nFile: {file_path}\n\n[After Changes]\n{change.after or 'Deleted File'}\n\n"
                    else:
                        content = printer.get_message_from_key(
                            "no_changes_made")
                else:
                    # For others, directly get execution results
                    content = last_result.content

                if action != command:
                    # If command and action don't match, consider command execution failed and exit
                    temp_content = printer.get_message_from_key_with_format(
                        "auto_command_action_break", command=command, action=action
                    )
                    printer.print_str_in_terminal(temp_content, style="yellow")
                    get_event_manager(self.args.event_file).write_result(
                        EventContentCreator.create_result(
                            content=temp_content),
                        metadata={
                            "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
                        }
                    )
                    break

                if command == "output_result":
                    success_flag = True
                    break

                get_event_manager(self.args.event_file).write_result(
                    EventContentCreator.create_result(
                        content=EventContentCreator.ResultCommandExecuteStatContent(
                            command=command, content=content
                        ).to_dict(),
                        metadata={
                            "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
                        }
                    )
                )

                # Print execution results
                console = Console()
                # Truncate content to 200 characters before and after
                truncated_content = (
                    content[:200] + "\n...\n" + content[-200:]
                    if len(content) > 400
                    else content
                )
                title = printer.get_message_from_key_with_format(
                    "command_execution_result", action=action
                )
                # Escape content to prevent Rich from interpreting [] in content as markup syntax
                text_content = Text(truncated_content)
                console.print(
                    Panel(
                        text_content, title=title, border_style="blue", padding=(1, 2)
                    )
                )

                # Add new conversation content
                new_content = self._execute_command_result.prompt(content)
                conversations.append({"role": "user", "content": new_content})

                # Count token numbers
                total_tokens = count_tokens(
                    json.dumps(conversations, ensure_ascii=False)
                )

                # If conversation is too long, use default strategy for pruning
                parsed_safe_zone_tokens = self._get_parsed_safe_zone_tokens()
                if total_tokens > parsed_safe_zone_tokens:
                    self.printer.print_in_terminal(
                        "conversation_pruning_start",
                        style="yellow",
                        total_tokens=total_tokens,
                        safe_zone=parsed_safe_zone_tokens,
                    )
                    from autocoder.common.pruner.conversation_pruner import ConversationPruner

                    pruner = ConversationPruner(self.args, self.llm)
                    conversations = pruner.prune_conversations(conversations)

            else:
                temp_content = printer.get_message_from_key_with_format(
                    "auto_command_break", command=command
                )
                printer.print_str_in_terminal(temp_content, style="yellow")
                get_event_manager(self.args.event_file).write_result(
                    EventContentCreator.create_result(content=temp_content),
                    metadata={
                        "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
                    }
                )
                break

        get_event_manager(self.args.event_file).write_result(
            EventContentCreator.create_result(
                content=printer.get_message_from_key("agenticFilterCommandResult")),
            metadata={
                "stream_out_type": AgenticFilterStreamOutType.AGENTIC_FILTER.value
            }
        )

        if success_flag:
            return to_model(content, AgenticFilterResponse)
            # return AgenticFilterResponse(**json.loads(content))
        else:
            return None

    def execute_auto_command(self, command: str, parameters: Dict[str, Any]) -> None:
        """
        Execute automatically generated commands
        """
        command_map = {
            "run_python": self.tools.run_python_code,
            "get_related_files_by_symbols": self.tools.get_related_files_by_symbols,
            "get_project_map": self.tools.get_project_map,
            "get_project_structure": self.tools.get_project_structure,
            "list_files": self.tools.list_files,
            "read_files": self.tools.read_files,
            "find_files_by_name": self.tools.find_files_by_name,
            "find_files_by_content": self.tools.find_files_by_content,
            "get_project_related_files": self.tools.get_project_related_files,
            "ask_user": self.tools.ask_user,
            "read_file_with_keyword_ranges": self.tools.read_file_with_keyword_ranges,
            "get_project_type": self.project_type_analyzer.analyze,
            "output_result": self.tools.output_result,
            "execute_mcp_server": self.tools.execute_mcp_server,
            "count_file_tokens": self.tools.count_file_tokens,
            "count_string_tokens": self.tools.count_string_tokens,
            "find_symbol_definition": self.tools.find_symbol_definition,
            "execute_shell_command": shells.execute_shell_command,
        }

        if command not in command_map:
            v = self.printer.get_message_from_key_with_format(
                "auto_command_not_found", style="red", command=command
            )
            raise Exception(v)
            return

        try:
            # Convert parameter dictionary to the format required by commands
            if parameters:
                command_map[command](**parameters)
            else:
                command_map[command]()

        except Exception as e:
            error_msg = str(e)
            v = self.printer.get_message_from_key_with_format(
                "auto_command_failed", style="red", command=command, error=error_msg
            )
            self.result_manager = ResultManager()
            result = f"command {command} with parameters {parameters} execution failed with error {error_msg}"
            self.result_manager.add_result(content=result, meta={
                "action": command,
                "input": parameters
            })
