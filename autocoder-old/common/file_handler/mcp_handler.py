import os
import time
import uuid
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.core_config import get_memory_manager
from autocoder.common.printer import Printer
from autocoder.auto_coder_runner import get_mcp_server, convert_config_value, convert_yaml_config_to_str, convert_yaml_to_config
from autocoder.common.mcp_tools import (
    McpRemoveRequest, McpListRunningRequest, McpListRequest, 
    McpRefreshRequest, McpInstallRequest, McpServerInfoRequest, McpRequest
)


class McpHandler:
    """处理MCP服务器相关的操作"""
    
    def __init__(self):
        self.console = Console()
        self.printer = Printer()
        self._config = None
    
    def _create_config(self):
        """创建 mcp 命令的类型化配置"""
        if self._config is None:
            self._config = (create_config()
                .collect_remainder("query")  # 收集剩余参数作为查询内容
                .command("remove")
                .positional("server_name", required=True)
                .max_args(1)
                .command("list_running")
                .max_args(0)
                .command("list")
                .max_args(0)
                .command("refresh")
                .positional("server_name")  # 可选的服务器名
                .max_args(1)
                .command("add")
                .positional("server_config", required=True)
                .max_args(1)
                .command("info")
                .max_args(0)
                .build()
            )
        return self._config
    
    def handle_mcp_command(self, query: str) -> Optional[None]:
        """
        处理MCP命令的主入口
        
        Args:
            query: 查询字符串
            
        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        query = query.strip()
        if not query:
            return self._handle_no_args()
        
        # 解析命令
        config = self._create_config()
        result = parse_typed_query(query, config)
        
        # 检查各种子命令
        if result.has_command("remove"):
            return self._handle_remove(result)
        
        if result.has_command("list_running"):
            return self._handle_list_running()
        
        if result.has_command("list"):
            return self._handle_list()
        
        if result.has_command("refresh"):
            return self._handle_refresh(result)
        
        if result.has_command("add"):
            return self._handle_add(result)
        
        if result.has_command("info"):
            return self._handle_info()
        
        # 默认查询处理
        return self._handle_default_query(result.query if hasattr(result, 'query') else query)
    
    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        self.printer.print_in_terminal("mcp_usage", style="yellow")
        return None
    
    def _handle_remove(self, result) -> None:
        """处理移除服务器命令"""
        mcp_server = get_mcp_server()
        remove_cmd = result.get_command("remove")
        server_name = remove_cmd.args[0] if remove_cmd.args else ""
        
        response = mcp_server.send_request(
            McpRemoveRequest(server_name=server_name))
        
        if response.error:
            self.printer.print_in_terminal(
                "mcp_remove_error", style="red", error=response.error)
        else:
            self.printer.print_in_terminal(
                "mcp_remove_success", style="green", result=response.result)
        return None
    
    def _handle_list_running(self) -> None:
        """处理列出运行中的服务器"""
        mcp_server = get_mcp_server()
        response = mcp_server.send_request(McpListRunningRequest())
        
        if response.error:
            self.printer.print_in_terminal(
                "mcp_list_running_error", style="red", error=response.error)
        else:
            self.printer.print_in_terminal("mcp_list_running_title")
            self.printer.print_str_in_terminal(response.result)
        return None
    
    def _handle_list(self) -> None:
        """处理列出内置服务器"""
        mcp_server = get_mcp_server()
        response = mcp_server.send_request(McpListRequest())
        
        if response.error:
            self.printer.print_in_terminal(
                "mcp_list_builtin_error", style="red", error=response.error)
        else:
            self.printer.print_in_terminal("mcp_list_builtin_title")
            self.printer.print_str_in_terminal(response.result)
        return None
    
    def _handle_refresh(self, result) -> None:
        """处理刷新服务器"""
        mcp_server = get_mcp_server()
        refresh_cmd = result.get_command("refresh")
        server_name = refresh_cmd.args[0] if refresh_cmd.args else None
        
        response = mcp_server.send_request(
            McpRefreshRequest(name=server_name))
        
        if response.error:
            self.printer.print_in_terminal(
                "mcp_refresh_error", style="red", error=response.error)
        else:
            self.printer.print_in_terminal("mcp_refresh_success", style="green")
        return None
    
    def _handle_add(self, result) -> None:
        """处理添加服务器"""
        mcp_server = get_mcp_server()
        add_cmd = result.get_command("add")
        server_config = add_cmd.args[0] if add_cmd.args else ""
        
        request = McpInstallRequest(server_name_or_config=server_config)
        response = mcp_server.send_request(request)

        if response.error:
            self.printer.print_in_terminal(
                "mcp_install_error", style="red", error=response.error)
        else:
            self.printer.print_in_terminal(
                "mcp_install_success", style="green", result=response.result)
        return None
    
    def _handle_info(self) -> None:
        """处理服务器信息查询"""
        # 准备配置
        memory_manager = get_memory_manager()
        conf = memory_manager.get_all_config()
        args = self._prepare_config(conf)
        
        mcp_server = get_mcp_server()
        response = mcp_server.send_request(McpServerInfoRequest(
            model=args.inference_model or args.model,
            product_mode=args.product_mode
        ))
        
        if response.error:
            self.printer.print_in_terminal(
                "mcp_server_info_error", style="red", error=response.error)
        else:
            self.printer.print_in_terminal("mcp_server_info_title")
            self.printer.print_str_in_terminal(response.result)
        return None
    
    def _handle_default_query(self, query: str) -> None:
        """处理默认查询"""
        # 准备配置
        memory_manager = get_memory_manager()
        conf = memory_manager.get_all_config()
        args = self._prepare_config(conf)
        
        mcp_server = get_mcp_server()
        response = mcp_server.send_request(
            McpRequest(
                query=query,
                model=args.inference_model or args.model,
                product_mode=args.product_mode
            )
        )

        if response.error:
            self.printer.print_panel(
                f"Error from MCP server: {response.error}",
                text_options={"justify": "left"},
                panel_options={
                    "title": self.printer.get_message_from_key("mcp_error_title"),
                    "border_style": "red"
                }
            )
        else:
            # Save conversation
            mcp_dir = os.path.join(".auto-coder", "mcp", "conversations")
            os.makedirs(mcp_dir, exist_ok=True)
            timestamp = str(int(time.time()))
            file_path = os.path.join(mcp_dir, f"{timestamp}.md")

            # Format response as markdown
            markdown_content = response.result

            # Save to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            self.console.print(
                Panel(
                    Markdown(markdown_content, justify="left"),
                    title=self.printer.get_message_from_key('mcp_response_title'),
                    border_style="green"
                )
            )
        return None
    
    def _prepare_config(self, conf: dict):
        """准备配置参数"""
        yaml_config = {
            "include_file": ["./base/base.yml"],
            "auto_merge": conf.get("auto_merge", "editblock"),
            "human_as_model": conf.get("human_as_model", "false") == "true",
            "skip_build_index": conf.get("skip_build_index", "true") == "true",
            "skip_confirm": conf.get("skip_confirm", "true") == "true",
            "silence": conf.get("silence", "true") == "true",
            "include_project_structure": conf.get("include_project_structure", "false") == "true",
            "exclude_files": get_memory_manager().get_exclude_files(),
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
            return args
        finally:
            if os.path.exists(temp_yaml):
                os.remove(temp_yaml)
