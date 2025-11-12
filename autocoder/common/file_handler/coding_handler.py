import os
import json
import uuid
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.conversations.get_conversation_manager import (
    get_conversation_manager,
)
from autocoder.common.core_config import get_memory_manager
from autocoder.common.result_manager import ResultManager
from autocoder.auto_coder_runner import (
    get_current_files,
    get_last_yaml_file,
    convert_config_value,
    convert_yaml_config_to_str,
    get_llm_friendly_package_docs,
    get_global_memory_file_paths,
    auto_coder_main,
    completer,
    get_current_memory,
    convert_yaml_to_config,
)
from autocoder.utils.llms import get_single_llm
from autocoder.agent.auto_guess_query import AutoGuessQuery
from byzerllm.utils.nontext import Image


class CodingHandler:
    """处理代码生成相关的操作"""

    def __init__(self):
        self.console = Console()
        self._config = None
        self.namespace = self._generate_namespace()

    def _generate_namespace(self) -> Optional[str]:
        """
        生成命名空间，用于会话隔离
        
        Returns:
            str: 基于项目路径的命名空间
        """
        return None

    def _create_config(self):
        """创建 coding 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .collect_remainder("query")  # 收集剩余参数作为代码生成查询
                .command("apply")
                .max_args(0)  # 应用历史对话上下文
                .command("next")
                .max_args(0)  # 生成下一步任务预测
                .build()
            )
        return self._config

    def handle_coding_command(self, query: str, cancel_token=None) -> Optional[None]:
        """
        处理代码生成命令的主入口

        Args:
            query: 查询字符串
            cancel_token: 可选的取消令牌

        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        if not query or not query.strip():
            return self._handle_no_args()

        # 检查是否是 /help 命令
        query_stripped = query.strip()
        if query_stripped == "/help":
            self._handle_help_command()
            return None

        # 保存原始查询字符串，用于处理没有命令的情况
        self._original_query = query.strip()

        # 解析命令
        config = self._create_config()
        result = parse_typed_query(query, config)

        # 检查子命令
        is_apply = result.has_command("apply")
        is_next = result.has_command("next")

        if is_next:
            return self._handle_next_command(result)

        # 执行代码生成
        return self._handle_coding_generation(result, is_apply, cancel_token)

    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        self.console.print(
            Panel(
                "Please provide a coding request or query.",
                title="Coding Command",
                border_style="yellow",
            )
        )
        return None

    def _handle_help_command(self) -> None:
        """处理 /help 命令"""
        help_text = get_message("coding_help_text")
        print(help_text)

    def _handle_next_command(self, result) -> None:
        """处理 /next 子命令"""
        # 修复：当没有解析到命令时，使用原始查询字符串
        if hasattr(result, "query") and result.query:
            query = result.query
        elif hasattr(result, "_query") and result._query:
            query = result._query
        else:
            # 如果解析结果中没有 query，说明输入的内容没有被识别为命令
            # 这时应该将原始输入作为 query 使用
            query = self._original_query if hasattr(self, "_original_query") else ""

        self.code_next(query)
        return None

    def code_next(self, query: str):
        """预测下一步任务的方法，从 auto_coder_runner.py 复制而来"""
        memory = get_current_memory()
        conf = memory.get("conf", {})
        yaml_config = {
            "include_file": ["./base/base.yml"],
            "auto_merge": conf.get("auto_merge", "editblock"),
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "include_project_structure": conf.get("include_project_structure", "false")
            == "true",
            "exclude_files": memory.get("exclude_files", []),
        }
        for key, value in conf.items():
            converted_value = convert_config_value(key, value)
            if converted_value is not None:
                yaml_config[key] = converted_value

        temp_yaml = os.path.join("actions", f"{uuid.uuid4()}.yml")
        try:
            with open(temp_yaml, "w", encoding="utf-8") as f:
                f.write(convert_yaml_config_to_str(yaml_config=yaml_config))
            args = convert_yaml_to_config(temp_yaml)
        finally:
            if os.path.exists(temp_yaml):
                os.remove(temp_yaml)

        product_mode = conf.get("product_mode", "lite")
        llm = get_single_llm(args.chat_model or args.model, product_mode=product_mode)

        auto_guesser = AutoGuessQuery(llm=llm, project_dir=os.getcwd(), skip_diff=True)

        predicted_tasks = auto_guesser.predict_next_tasks(
            5, is_human_as_model=args.human_as_model
        )

        if not predicted_tasks:
            console = Console()
            console.print(Panel("No task predictions available", style="yellow"))
            return

        console = Console()

        # Create main panel for all predicted tasks
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Priority", style="cyan", width=8)
        table.add_column("Task Description", style="green", width=40, overflow="fold")
        table.add_column("Files", style="yellow", width=30, overflow="fold")
        table.add_column("Reason", style="blue", width=30, overflow="fold")
        table.add_column("Dependencies", style="magenta", width=30, overflow="fold")

        for task in predicted_tasks:
            # Format file paths to be more readable
            file_list = "\n".join([os.path.relpath(f, os.getcwd()) for f in task.urls])

            # Format dependencies to be more readable
            dependencies = (
                "\n".join(task.dependency_queries)
                if task.dependency_queries
                else "None"
            )

            table.add_row(
                str(task.priority), task.query, file_list, task.reason, dependencies
            )

        console.print(
            Panel(
                table,
                title="[bold]Predicted Next Tasks[/bold]",
                border_style="blue",
                padding=(1, 2),  # Add more horizontal padding
            )
        )

    def _handle_coding_generation(
        self, result, is_apply: bool, cancel_token=None
    ) -> None:
        """处理代码生成逻辑"""
        # 修复：当没有解析到命令时，使用原始查询字符串
        if hasattr(result, "query") and result.query:
            query = result.query
        elif hasattr(result, "_query") and result._query:
            query = result._query
        else:
            # 如果解析结果中没有 query，说明输入的内容没有被识别为命令
            # 这时应该将原始输入作为 query 使用
            query = self._original_query if hasattr(self, "_original_query") else ""

        # 获取配置和状态
        memory_manager = get_memory_manager()
        conf = memory_manager.get_all_config()

        current_files = get_current_files()
        current_groups = memory_manager.get_current_groups()
        groups = memory_manager.get_file_groups()
        groups_info = memory_manager.get_groups_info()

        def prepare_chat_yaml():
            auto_coder_main(["next", "chat_action"])

        prepare_chat_yaml()

        latest_yaml_file = get_last_yaml_file("actions")

        if latest_yaml_file:
            # 构建 YAML 配置
            yaml_config = self._build_yaml_config(
                conf, memory_manager, current_files, is_apply, cancel_token
            )

            # 处理图片转换
            v = Image.convert_image_paths_from(query)
            yaml_config["query"] = v

            # 添加组上下文
            if current_groups:
                yaml_config["context"] = self._build_groups_context(
                    current_groups, groups, groups_info, yaml_config.get("context", "")
                )

            # 处理 /apply 逻辑
            if is_apply:
                yaml_config["context"] = self._apply_chat_history(
                    yaml_config.get("context", "")
                )

            # 保存和执行
            print(yaml_config)
            self._save_and_execute_yaml(yaml_config, latest_yaml_file, query)
        else:
            print("Failed to create new YAML file.")

        completer.refresh_files()
        return None

    def _build_yaml_config(
        self,
        conf: dict,
        memory_manager,
        current_files: list,
        is_apply: bool,
        cancel_token,
    ) -> dict:
        """构建 YAML 配置"""
        yaml_config = {
            "include_file": ["./base/base.yml"],
            "auto_merge": conf.get("auto_merge", "editblock"),
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "include_project_structure": conf.get("include_project_structure", "false")
            == "true",
            "exclude_files": memory_manager.get_exclude_files(),
        }

        yaml_config["context"] = ""
        yaml_config["in_code_apply"] = is_apply
        yaml_config["cancel_token"] = cancel_token

        for key, value in conf.items():
            converted_value = convert_config_value(key, value)
            if converted_value is not None:
                yaml_config[key] = converted_value

        yaml_config["urls"] = current_files + get_llm_friendly_package_docs(
            return_paths=True
        )

        if conf.get("enable_global_memory", "false") in ["true", "True", True]:
            yaml_config["urls"] += get_global_memory_file_paths()

        return yaml_config

    def _build_groups_context(
        self,
        current_groups: list,
        groups: dict,
        groups_info: dict,
        existing_context: str,
    ) -> str:
        """构建组上下文信息"""
        active_groups_context = "下面是对上面文件按分组给到的一些描述，当用户的需求正好匹配描述的时候，参考描述来做修改：\n"

        for group in current_groups:
            group_files = groups.get(group, [])
            query_prefix = groups_info.get(group, {}).get("query_prefix", "")
            active_groups_context += f"组名: {group}\n"
            active_groups_context += f"文件列表:\n"
            for file in group_files:
                active_groups_context += f"- {file}\n"
            active_groups_context += f"组描述: {query_prefix}\n\n"

        return existing_context + active_groups_context + "\n"

    def _apply_chat_history(self, existing_context: str) -> str:
        """应用聊天历史上下文"""

        def error_message():
            self.console.print(
                Panel(
                    "No chat history found to apply.",
                    title="Chat History",
                    expand=False,
                    border_style="yellow",
                )
            )

        try:            
            conversation_manager = get_conversation_manager()
            
            current_conversation_id = conversation_manager.get_current_conversation_id(
                self.namespace
            )

            conversations = []
            if current_conversation_id:
                # 获取当前会话的消息列表
                messages = conversation_manager.get_messages(current_conversation_id)
                # 转换为原有格式
                conversations = [
                    {"role": msg["role"], "content": msg["content"]} for msg in messages
                ]

            if not conversations:
                error_message()
                return existing_context

            context = existing_context
            context += f"下面是我们的历史对话，参考我们的历史对话从而更好的理解需求和修改代码: \n\n<history>\n"
            for conv in conversations:
                if conv["role"] == "user":
                    context += f"用户: {conv['content']}\n"
                elif conv["role"] == "assistant":
                    context += f"你: {conv['content']}\n"
            context += "</history>\n"
            
            return context

        except Exception as e:
            # 如果出现任何错误，显示错误信息并返回原有上下文
            self.console.print(
                Panel(
                    f"Failed to load chat history: {str(e)}",
                    title="Chat History Error",
                    expand=False,
                    border_style="red",
                )
            )
            return existing_context

    def _save_and_execute_yaml(
        self, yaml_config: dict, latest_yaml_file: str, query: str
    ):
        """保存并执行 YAML 配置"""
        yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)

        execute_file = os.path.join("actions", latest_yaml_file)
        with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        def execute_coding():
            cmd = ["--file", execute_file]
            auto_coder_main(cmd)
            result_manager = ResultManager()
            result_manager.append(
                content="",
                meta={
                    "commit_message": f"auto_coder_{latest_yaml_file}",
                    "action": "coding",
                    "input": {"query": query},
                },
            )

        execute_coding()
