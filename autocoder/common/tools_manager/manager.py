"""
Tools Manager Core Implementation

工具管理器的核心实现，负责动态加载和管理 .autocodertools 目录中的工具命令。
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger
import byzerllm

from .models import ToolCommand, ToolsLoadResult
from .utils import is_tool_command_file, extract_tool_help, get_project_name
from ..priority_directory_finder import (
    PriorityDirectoryFinder,
    FinderConfig,
    SearchStrategy,
    ValidationMode
)


class ToolsManager:
    """
    工具管理器

    负责从多个优先级目录中加载和管理工具命令文件。
    支持的目录优先级（从高到低）：
    1. 当前项目/.autocodertools
    2. .auto-coder/.autocodertools
    3. ~/.auto-coder/.autocodertools
    4. ~/.auto-coder/.autocodertools/repos/<项目名>
    """

    def __init__(self, tools_dirs: Optional[List[str]] = None):
        """
        初始化工具管理器

        Args:
            tools_dirs: 自定义工具目录列表，如果为None则使用默认查找策略
        """
        self.tools_dirs = tools_dirs or self._find_tools_directories()
        self._result_cache: Optional[ToolsLoadResult] = None

    def _find_tools_directories(self) -> List[str]:
        """
        查找所有有效的工具目录

        Returns:
            List[str]: 有效的工具目录路径列表
        """

        config = FinderConfig(strategy=SearchStrategy.MERGE_ALL)

        # 添加标准目录路径
        current_dir = Path.cwd()
        project_name = get_project_name()

        # 1. 当前项目/.autocodertools (最高优先级)
        config.add_directory(
            str(current_dir / ".autocodertools"),
            priority=1,
            validation_mode=ValidationMode.HAS_FILES
        )

        # 2. .auto-coder/.autocodertools
        config.add_directory(
            str(current_dir / ".auto-coder" / ".autocodertools"),
            priority=2,
            validation_mode=ValidationMode.HAS_FILES
        )

        # 3. ~/.auto-coder/.autocodertools
        home_dir = Path.home()
        config.add_directory(
            str(home_dir / ".auto-coder" / ".autocodertools"),
            priority=3,
            validation_mode=ValidationMode.HAS_FILES
        )

        # 4. ~/.auto-coder/.autocodertools/repos/<项目名> (最低优先级)
        config.add_directory(
            str(home_dir / ".auto-coder" / ".autocodertools" / "repos" / project_name),
            priority=4,
            validation_mode=ValidationMode.HAS_FILES
        )

        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()

        if result.success:
            logger.info(f"找到工具目录: {result.all_valid_directories}")
            return result.all_valid_directories
        else:
            logger.warning("未找到任何工具目录")
            return []


    def load_tools(self, force_reload: bool = False) -> ToolsLoadResult:
        """
        加载所有工具命令

        Args:
            force_reload: 是否强制重新加载

        Returns:
            ToolsLoadResult: 加载结果
        """
        if not force_reload and self._result_cache is not None:
            return self._result_cache

        all_tools = []
        failed_count = 0

        for tools_dir in self.tools_dirs:
            if not os.path.exists(tools_dir):
                continue

            logger.debug(f"扫描工具目录: {tools_dir}")

            try:
                for item in os.listdir(tools_dir):
                    item_path = os.path.join(tools_dir, item)

                    if os.path.isfile(item_path) and is_tool_command_file(item_path):
                        try:
                            tool = self._create_tool_command(item_path, tools_dir)
                            if tool:
                                all_tools.append(tool)
                                logger.debug(f"加载工具: {tool.name}")
                            else:
                                failed_count += 1
                        except Exception as e:
                            logger.warning(f"加载工具文件失败 {item_path}: {e}")
                            failed_count += 1

            except OSError as e:
                logger.warning(f"读取工具目录失败 {tools_dir}: {e}")
                continue

        # 去重：如果多个目录中有同名工具，优先使用高优先级目录中的
        unique_tools = self._deduplicate_tools(all_tools)

        result = ToolsLoadResult(
            success=True,
            tools=unique_tools,
            failed_count=failed_count
        )
        self._result_cache = result

        return result

    def _create_tool_command(self, file_path: str, source_dir: str) -> Optional[ToolCommand]:
        """
        创建工具命令对象

        Args:
            file_path: 工具文件路径
            source_dir: 来源目录

        Returns:
            Optional[ToolCommand]: 工具命令对象
        """
        path = Path(file_path)

        # 提取帮助信息
        help_text = extract_tool_help(file_path)

        # 检查是否可执行
        is_executable = os.access(file_path, os.X_OK)

        return ToolCommand(
            name=path.name,
            path=file_path,
            help_text=help_text,
            is_executable=is_executable,
            file_extension=path.suffix,
            source_directory=source_dir
        )

    def _deduplicate_tools(self, tools: List[ToolCommand]) -> List[ToolCommand]:
        """
        去重工具列表，保留高优先级目录中的工具

        Args:
            tools: 工具列表

        Returns:
            List[ToolCommand]: 去重后的工具列表
        """
        # 创建目录优先级映射
        dir_priority = {dir_path: idx for idx, dir_path in enumerate(self.tools_dirs)}

        # 按工具名称分组
        tools_by_name: Dict[str, List[ToolCommand]] = {}
        for tool in tools:
            if tool.name not in tools_by_name:
                tools_by_name[tool.name] = []
            tools_by_name[tool.name].append(tool)

        # 对每个工具名称，选择优先级最高的工具
        unique_tools = []
        for name, tool_list in tools_by_name.items():
            if len(tool_list) == 1:
                unique_tools.append(tool_list[0])
            else:
                # 选择优先级最高的工具
                best_tool = min(
                    tool_list,
                    key=lambda t: dir_priority.get(t.source_directory, 999)
                )
                unique_tools.append(best_tool)

                # 记录被覆盖的工具
                for tool in tool_list:
                    if tool != best_tool:
                        logger.debug(f"工具 {name} 在 {tool.source_directory} 被 {best_tool.source_directory} 中的版本覆盖")

        return unique_tools

    def get_tool_by_name(self, name: str) -> Optional[ToolCommand]:
        """
        根据名称获取工具命令

        Args:
            name: 工具名称

        Returns:
            Optional[ToolCommand]: 工具命令对象
        """
        result = self.load_tools()
        if not result.success:
            return None

        for tool in result.tools:
            if tool.name == name:
                return tool
        return None

    def list_tool_names(self) -> List[str]:
        """
        获取所有工具名称列表

        Returns:
            List[str]: 工具名称列表
        """
        result = self.load_tools()
        if not result.success:
            return []
        return [tool.name for tool in result.tools]

    @byzerllm.prompt()
    def get_tools_prompt(self) -> str:
        """
        # Available External Tool Commands

        Project Name: {{ project_name }}
        Current Project Path: {{ project_path }}
        Total Tools: {{ tools_count }}
        {% if failed_count > 0 %}
        Failed to Load: {{ failed_count }} tools
        {% endif %}

        ## Tool Directories
        {% for dir in tools_directories %}
        - {{ dir }}
        {% endfor %}

        ## Tool List

        {% if tools_count == 0 %}
        No available tool commands found.
        {% else %}
        {% for tool in tools_info %}
        ### {{ tool.name }}{{ tool.file_extension }}

        **Source Directory**: {{ tool.source_directory }}
        **Executable**: {% if tool.is_executable %}Yes{% else %}No{% endif %}

        **Usage Instructions**:
        ```
        {{ tool.help_text }}
        ```

        ---
        {% endfor %}
        {% endif %}

        ## How to Create External Tools

        ### Directory Structure (Priority Order)
        Tools are loaded from these directories in priority order (highest to lowest):
        1. **Project-specific**: `./.autocodertools/` (highest priority)
        2. **Project config**: `./.auto-coder/.autocodertools/` (**recommended**)
        3. **Global user**: `~/.auto-coder/.autocodertools/`
        4. **Project-specific global**: `~/.auto-coder/.autocodertools/repos/{{ project_name }}/` (lowest priority)

        > **Note**: Tools with identical names in higher priority directories will override those in lower priority directories.

        ### Supported File Types
        - **Executable binaries** (compiled tools, **recommended**)
        - **Script files** (`.sh`, `.py`, `.js`, `.rb`, etc.)

        ### Tool Development Guidelines

        Please use SubAgent to create new tools. New tools should follow
        the same guidelines as existing tools.

        #### 1. Help Information (Required)
        Your tool must provide help information using one of these methods:

        **Method 1: Command-line help (Recommended)**
        ```bash
        your_tool help
        your_tool -h
        your_tool --help
        ```

        **Method 2: File header comments**
        ```python
        #!/usr/bin/env python3
        # Description: Brief description of your tool
        # Usage: tool_name [options] [arguments]
        #
        # Options:
        #   -h, --help     Show this help message
        #   -v, --verbose  Enable verbose output
        ```

        #### 2. File Permissions
        - **Binary files** (no extension): Must be executable (`chmod +x`)
        - **Script files** (`.py`, `.sh`, etc.): Must be readable (`chmod +r`)

        #### 3. Tool Execution
        Use the built-in `execute_command` tool to run your custom tools.

        #### 4. **Tool is now available** - the AI assistant will discover and use it freely

        ## Important Rules
        1. If you use python, try to use uv to create project {{ autocoder_home }}/.auto-coder/tool_repos and run the tool. (we not recommend using python to build tools, please try to use Go first)
        1. **MANDATORY**: All tools MUST support `help` or `-h` parameter for detailed usage information
        2. **REQUIRED**: Always use a custom sub agent to create tools and set a proper timeout for sub agent task, e.g. 1800s. - never create tools directly
        3. **STRONGLY RECOMMENDED**: Prefer Go for building tools， here is the steps:
           - Create a tool project in {{ autocoder_home }}/.auto-coder/tool_repos
           - Ask the subagent to develop and build the binary in the tool directory (with proper timeout). The command should like this: cd <tool directory> && echo '<prompt>' | auto-coder.run --model <model_name> --is-sub-agent
           - Copy the final binary to `./.auto-coder/.autocodertools/` after completion
           - If no binary is found in the directory, request the subagent to rebuild the tool
        """

        # 加载所有工具
        result = self.load_tools()

        if not result.success:
            return {
                "project_name": get_project_name(),
                "project_path": os.getcwd(),
                "autocoder_home": os.path.expanduser("~"),
                "tools_count": 0,
                "tools_info": [],
                "failed_count": 0,
                "tools_directories": self.tools_dirs,
                "error_message": result.error_message or "未找到任何工具"
            } # type: ignore[return]

        tools_info = []
        for tool in result.tools:
            tools_info.append({
                "name": tool.name,
                "help_text": tool.help_text,
                "is_executable": tool.is_executable,
                "file_extension": tool.file_extension,
                "source_directory": tool.source_directory
            })

        project_name = get_project_name()

        return {
            "project_name": project_name,
            "project_path": os.getcwd(),
            "autocoder_home": os.path.expanduser("~"),
            "tools_count": len(result.tools),
            "tools_info": tools_info,
            "failed_count": result.failed_count,
            "tools_directories": self.tools_dirs
        } # type: ignore[return]
