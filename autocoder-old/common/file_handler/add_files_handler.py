import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.core_config import get_memory_manager
from autocoder.auto_coder_runner import find_files_in_project
from autocoder.common.result_manager import ResultManager
from autocoder.common.printer import Printer


class AddFilesHandler:
    """处理文件添加相关的操作"""
    
    def __init__(self):
        self.console = Console()
        self.printer = Printer()
        self._config = None
    
    def _create_config(self):
        """创建 add_files 命令的类型化配置"""
        if self._config is None:
            self._config = (create_config()
                .collect_remainder("files")  # 收集剩余参数作为文件路径
                .command("refresh")
                .max_args(0)  # 无参数命令
                .command("group")
                .positional("action", choices=["list", "reset", "add", "drop", "set"], default="list")
                .positional("group_name")  # 组名，某些操作需要
                .max_args(2)  # 最多2个位置参数：action 和 group_name
                .build()
            )
        return self._config
    
    def handle_add_files_command(self, args: List[str]) -> Optional[None]:
        """
        处理文件添加命令的主入口
        
        Args:
            args: 参数列表
            
        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        if not args:
            return self._handle_no_args()
            
        # 将 args 转换为查询字符串
        query = " ".join(args)
        
        # 特殊处理：如果第一个参数是 /refresh，转换为命令格式
        if args[0] == "/refresh":
            return self._handle_refresh()
        
        # 特殊处理：如果第一个参数是 /group，转换为命令格式
        if args[0] == "/group":
            return self._handle_group_command(args[1:])
        
        # 否则作为普通文件添加处理
        return self._handle_regular_files(args)
    
    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        result_manager = ResultManager()
        self.printer.print_in_terminal("add_files_no_args", style="red")
        result_manager.append(
            content=self.printer.get_message_from_key("add_files_no_args"),
            meta={"action": "add_files", "success": False, "input": {"args": []}}
        )
        return None
    
    def _handle_refresh(self) -> None:
        """处理刷新文件列表"""
        # 与原实现保持一致，从 auto_coder_runner 引入 completer
        from autocoder.auto_coder_runner import completer
        result_manager = ResultManager()
        
        completer.refresh_files()
        self.console.print(
            Panel("Refreshed file list.",
                  title="Files Refreshed", border_style="green")
        )
        result_manager.append(
            content="Files refreshed.",
            meta={"action": "add_files", "success": True, "input": {"args": ["/refresh"]}}
        )
        return None
    
    def _handle_group_command(self, sub_args: List[str]) -> None:
        """处理组相关命令"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        groups = memory_manager.get_file_groups()
        current_groups = memory_manager.get_current_groups()
        
        if not sub_args or sub_args[0] == "list":
            return self._handle_group_list(groups, current_groups)
        
        if sub_args[0] == "/reset":
            return self._handle_group_reset()
        
        if sub_args[0] == "/add" and len(sub_args) >= 2:
            return self._handle_group_add(sub_args[1])
        
        if sub_args[0] == "/drop" and len(sub_args) >= 2:
            return self._handle_group_drop(sub_args[1])
        
        if sub_args[0] == "/set" and len(sub_args) >= 2:
            return self._handle_group_set(sub_args[1])
        
        # 否则作为组名处理，支持多个组的合并
        return self._handle_group_merge(sub_args)
    
    def _handle_group_list(self, groups, current_groups) -> None:
        """处理组列表显示"""
        result_manager = ResultManager()
        
        if not groups:
            self.console.print(
                Panel("No groups defined.", title="Groups",
                      border_style="yellow")
            )
            result_manager.append(
                content="No groups defined.",
                meta={"action": "add_files", "success": False, "input": {"args": ["/group", "list"]}}
            )
        else:
            project_root = os.getcwd()  # 使用当前工作目录作为项目根目录
            table = Table(
                title="Defined Groups",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("Group Name", style="cyan", no_wrap=True)
            table.add_column("Files", style="green")
            table.add_column("Query Prefix", style="yellow")
            table.add_column("Active", style="magenta")

            memory_manager = get_memory_manager()
            for i, (group_name, files) in enumerate(groups.items()):
                query_prefix = memory_manager.get_group_query_prefix(group_name)
                is_active = "✓" if group_name in current_groups else ""
                table.add_row(
                    group_name,
                    "\n".join([os.path.relpath(f, project_root) for f in files]),
                    query_prefix,
                    is_active,
                    end_section=(i == len(groups) - 1),
                )
            self.console.print(Panel(table, border_style="blue"))
            result_manager.append(
                content="Defined groups.",
                meta={"action": "add_files", "success": True, "input": {"args": ["/group", "list"]}}
            )
        return None
    
    def _handle_group_reset(self) -> None:
        """处理组重置"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        memory_manager.clear_current_groups()
        self.console.print(
            Panel(
                "Active group names have been reset. If you want to clear the active files, you should use the command /remove_files /all.",
                title="Groups Reset",
                border_style="green",
            )
        )
        result_manager.append(
            content="Active group names have been reset. If you want to clear the active files, you should use the command /remove_files /all.",
            meta={"action": "add_files", "success": True, "input": {"args": ["/group", "/reset"]}}
        )
        return None
    
    def _handle_group_add(self, group_name: str) -> None:
        """处理添加组"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        current_files = memory_manager.get_current_files()
        memory_manager.set_file_group(group_name, current_files.copy())
        self.console.print(
            Panel(
                f"Added group '{group_name}' with current files.",
                title="Group Added",
                border_style="green",
            )
        )
        result_manager.append(
            content=f"Added group '{group_name}' with current files.",
            meta={"action": "add_files", "success": True, "input": {"args": ["/group", "/add", group_name]}}
        )
        return None
    
    def _handle_group_drop(self, group_name: str) -> None:
        """处理删除组"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        if memory_manager.has_file_group(group_name):
            memory_manager.delete_file_group(group_name)
            self.console.print(
                Panel(
                    f"Dropped group '{group_name}'.",
                    title="Group Dropped",
                    border_style="green",
                )
            )
            result_manager.append(
                content=f"Dropped group '{group_name}'.",
                meta={"action": "add_files", "success": True, "input": {"args": ["/group", "/drop", group_name]}}
            )
        else:
            self.console.print(
                Panel(
                    f"Group '{group_name}' not found.",
                    title="Error",
                    border_style="red",
                )
            )
            result_manager.append(
                content=f"Group '{group_name}' not found.",
                meta={"action": "add_files", "success": False, "input": {"args": ["/group", "/drop", group_name]}}
            )
        return None
    
    def _handle_group_set(self, group_name: str) -> None:
        """处理设置组描述"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        query_prefix = self._multiline_edit()
        if memory_manager.has_file_group(group_name):
            memory_manager.set_group_query_prefix(group_name, query_prefix)
            self.console.print(
                Panel(
                    f"Set Atom Group Desc for group '{group_name}'.",
                    title="Group Info Updated",
                    border_style="green",
                )
            )
            result_manager.append(
                content=f"Set Atom Group Desc for group '{group_name}'.",
                meta={"action": "add_files", "success": True, "input": {"args": ["/group", "/set", group_name]}}
            )
        else:
            self.console.print(
                Panel(
                    f"Group '{group_name}' not found.",
                    title="Error",
                    border_style="red",
                )
            )
            result_manager.append(
                content=f"Group '{group_name}' not found.",
                meta={"action": "add_files", "success": False, "input": {"args": ["/group", "/set", group_name]}}
            )
        return None
    
    def _handle_group_merge(self, group_names: List[str]) -> None:
        """处理组合并"""
        project_root = os.getcwd()  # 使用当前工作目录作为项目根目录
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        # 支持多个组的合并，允许组名之间使用逗号或空格分隔
        group_names_str = " ".join(group_names).replace(",", " ")
        group_names_list = group_names_str.split()
        
        missing_groups = memory_manager.merge_groups_to_current_files(group_names_list)

        if missing_groups:
            self.console.print(
                Panel(
                    f"Group(s) not found: {', '.join(missing_groups)}",
                    title="Error",
                    border_style="red",
                )
            )
            result_manager.append(
                content=f"Group(s) not found: {', '.join(missing_groups)}",
                meta={"action": "add_files", "success": False, "input": {"args": ["/group"] + group_names}}
            )

        # Check if any files were merged
        current_files = memory_manager.get_current_files()
        if current_files:
            successful_groups = [g for g in group_names_list if g not in missing_groups]
            self.console.print(
                Panel(
                    f"Merged files from groups: {', '.join(successful_groups)}",
                    title="Files Merged",
                    border_style="green",
                )
            )
            table = Table(
                title="Current Files",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("File", style="green")
            for i, f in enumerate(current_files):
                table.add_row(
                    os.path.relpath(f, project_root),
                    end_section=(i == len(current_files) - 1),
                )
            self.console.print(Panel(table, border_style="blue"))

            current_groups = memory_manager.get_current_groups()
            self.console.print(
                Panel(
                    f"Active groups: {', '.join(current_groups)}",
                    title="Active Groups",
                    border_style="green",
                )
            )
            result_manager.append(
                content=f"Active groups: {', '.join(current_groups)}",
                meta={"action": "add_files", "success": True, "input": {"args": ["/group"] + group_names}}
            )
        elif not missing_groups:
            self.console.print(
                Panel(
                    "No files in the specified groups.",
                    title="No Files Added",
                    border_style="yellow",
                )
            )
            result_manager.append(
                content="No files in the specified groups.",
                meta={"action": "add_files", "success": False, "input": {"args": ["/group"] + group_names}}
            )
        return None
    
    def _handle_regular_files(self, args: List[str]) -> None:
        """处理常规文件添加"""
        project_root = os.getcwd()  # 使用当前工作目录作为项目根目录
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        matched_files = find_files_in_project(args)
        files_to_add = memory_manager.add_files(matched_files)

        if files_to_add:
            table = Table(
                title=get_message("add_files_added_files"),
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("File", style="green")
            for i, f in enumerate(files_to_add):
                table.add_row(
                    os.path.relpath(f, project_root),
                    end_section=(i == len(files_to_add) - 1),
                )
            self.console.print(Panel(table, border_style="green"))
            result_manager.append(
                content=f"Added files: {', '.join(files_to_add)}",
                meta={"action": "add_files", "success": True, "input": {"args": args}}
            )
        else:
            self.printer.print_in_terminal("add_files_matched", style="yellow")
            result_manager.append(
                content="No files matched.",
                meta={"action": "add_files", "success": False, "input": {"args": args}}
            )
        return None
    
    def _multiline_edit(self) -> str:
        """多行编辑功能"""
        from prompt_toolkit.lexers import PygmentsLexer
        from pygments.lexers.markup import MarkdownLexer
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.shortcuts import print_formatted_text
        from prompt_toolkit.styles import Style

        style = Style.from_dict({
            "dialog": "bg:#88ff88",
            "dialog frame.label": "bg:#ffffff #000000",
            "dialog.body": "bg:#000000 #00ff00",
            "dialog shadow": "bg:#00aa00",
        })

        print_formatted_text(
            HTML(
                "<b>Type Atom Group Desc (Press [Esc] + [Enter] to finish.)</b><br/>"
            )
        )
        text = prompt(
            HTML("<ansicyan>║</ansicyan> "),
            multiline=True,
            lexer=PygmentsLexer(MarkdownLexer),
            style=style,
            wrap_lines=True,
            prompt_continuation=HTML("<ansicyan>║</ansicyan> "),
            rprompt=HTML("<ansicyan>║</ansicyan>"),
        )
        return text
