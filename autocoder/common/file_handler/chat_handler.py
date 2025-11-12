import os
import uuid
from typing import Optional

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.ac_style_command_parser.parser import parse_query
from autocoder.auto_coder_runner import (
    get_current_memory,
    get_current_files,
    convert_config_value,
    convert_yaml_config_to_str,
    get_llm_friendly_package_docs,
    get_global_memory_file_paths,
    auto_coder_main,
)
from byzerllm.utils.nontext import Image


class ChatHandler:
    """处理聊天相关的操作"""

    def __init__(self):
        self._config = None

    def _create_config(self):
        """创建 chat 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .collect_remainder("query")  # 收集剩余参数作为聊天查询
                .command("new")
                .max_args(0)  # 开启新会话
                .command("learn")
                .max_args(0)  # 学习模式
                .command("review")
                .max_args(0)  # 审查模式
                .command("no_context")
                .max_args(0)  # 无上下文模式
                .command("copy")
                .max_args(0)  # 复制结果
                .command("save")
                .max_args(0)  # 保存到全局记忆
                .command("mcp")
                .max_args(0)  # MCP 模式
                .command("rag")
                .max_args(0)  # RAG 模式
                .build()
            )
        return self._config

    def handle_chat_command(self, query: str) -> Optional[None]:
        """
        处理聊天命令的主入口

        Args:
            query: 查询字符串

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

        # 执行聊天逻辑
        return self._handle_chat(query)

    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(
            Panel(
                "Please provide a chat query or command.",
                title="Chat Command",
                border_style="yellow",
            )
        )
        return None

    def _handle_help_command(self) -> None:
        """处理 /help 命令"""
        help_text = get_message("chat_help_text")
        print(help_text)

    def _handle_chat(self, query: str) -> None:
        """处理聊天逻辑"""
        memory = get_current_memory()
        conf = memory.get("conf", {})

        yaml_config = {
            "include_file": ["./base/base.yml"],
            "include_project_structure": conf.get("include_project_structure", "false")
            in ["true", "True"],
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "exclude_files": memory.get("exclude_files", []),
        }

        current_files = get_current_files() + get_llm_friendly_package_docs(
            return_paths=True
        )

        if conf.get("enable_global_memory", "false") in ["true", "True", True]:
            current_files += get_global_memory_file_paths()

        yaml_config["urls"] = current_files

        if "emb_model" in conf:
            yaml_config["emb_model"] = conf["emb_model"]

        # 解析命令
        commands_infos = parse_query(query)
        if len(commands_infos) > 0:
            if "query" in commands_infos:
                query = " ".join(commands_infos["query"]["args"])
            else:
                temp_query = ""
                for command, command_info in commands_infos.items():
                    if command_info["args"]:
                        temp_query = " ".join(command_info["args"])
                query = temp_query

        is_new = "new" in commands_infos

        # 特殊处理某些命令
        if "learn" in commands_infos:
            commands_infos["no_context"] = {}

        if "review" in commands_infos:
            commands_infos["no_context"] = {}

        # 转换 OrderedDict 为普通字典以便YAML序列化
        yaml_serializable_commands = {}
        for command, command_info in commands_infos.items():
            if isinstance(command_info, dict):
                yaml_serializable_commands[command] = dict(command_info)
            else:
                yaml_serializable_commands[command] = command_info

        yaml_config["action"] = yaml_serializable_commands

        for key, value in conf.items():
            converted_value = convert_config_value(key, value)
            if converted_value is not None:
                yaml_config[key] = converted_value

        # 处理图片转换
        query = Image.convert_image_paths_from(query)
        yaml_config["query"] = query

        # 保存和执行
        yaml_content = convert_yaml_config_to_str(yaml_config=yaml_config)
        execute_file = os.path.join("actions", f"{uuid.uuid4()}.yml")

        with open(os.path.join(execute_file), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        def execute_ask():
            cmd = ["agent", "chat", "--file", execute_file]
            if is_new:
                cmd.append("--new_session")
            auto_coder_main(cmd)

        try:
            execute_ask()
        finally:
            os.remove(execute_file)

        return None
