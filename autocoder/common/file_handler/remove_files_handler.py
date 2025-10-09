import os
import fnmatch
from typing import List, Optional, Set
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.core_config import get_memory_manager
from autocoder.common.result_manager import ResultManager
from autocoder.common.printer import Printer


class RemoveFilesHandler:
    """处理文件删除相关的操作"""
    
    def __init__(self):
        self.console = Console()
        self.printer = Printer()
        self._config = None
    
    def _create_config(self):
        """创建 remove_files 命令的类型化配置"""
        if self._config is None:
            self._config = (create_config()
                .collect_remainder("patterns")  # 收集剩余参数作为文件模式
                .command("all")
                .max_args(0)  # 无参数命令
                .build()
            )
        return self._config
    
    def handle_remove_files_command(self, file_names: List[str]) -> Optional[None]:
        """
        处理文件删除命令的主入口
        
        Args:
            file_names: 文件名列表或模式列表
            
        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        if not file_names:
            return self._handle_no_args()
        
        # 检查是否包含 /all 命令
        if "/all" in file_names:
            return self._handle_remove_all()
        
        # 否则作为文件模式处理
        return self._handle_remove_patterns(file_names)
    
    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        result_manager = ResultManager()
        self.printer.print_in_terminal("remove_files_usage", style="yellow")
        result_manager.append(
            content="Please provide file names or patterns to remove.",
            meta={"action": "remove_files", "success": False, "input": {"file_names": []}}
        )
        return None
    
    def _handle_remove_all(self) -> None:
        """处理移除所有文件"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        
        memory_manager.clear_files()
        memory_manager.clear_current_groups()
        self.printer.print_in_terminal("remove_files_all", style="green")
        result_manager.append(
            content="All files removed.",
            meta={"action": "remove_files", "success": True, "input": {"file_names": ["/all"]}}
        )
        return None
    
    def _handle_remove_patterns(self, file_names: List[str]) -> None:
        """处理文件模式移除"""
        memory_manager = get_memory_manager()
        result_manager = ResultManager()
        project_root = os.getcwd()
        
        files_to_remove = set()
        current_files_abs = memory_manager.get_current_files()

        for pattern in file_names:
            pattern = pattern.strip()  # Remove leading/trailing whitespace
            if not pattern:
                continue

            matched_files = self._match_files_by_pattern(pattern, current_files_abs, project_root)
            files_to_remove.update(matched_files)

        removed_files_list = list(files_to_remove)
        if removed_files_list:
            # Use manager's remove_files method
            removed_files = memory_manager.remove_files(removed_files_list)

            table = Table(
                show_header=True,
                header_style="bold magenta"
            )
            table.add_column(self.printer.get_message_from_key(
                "file_column_title"), style="green")
            for f in removed_files:
                table.add_row(os.path.relpath(f, project_root))

            self.console.print(
                Panel(table, border_style="green",
                      title=self.printer.get_message_from_key("files_removed")))
            result_manager.append(
                content=f"Removed files: {', '.join(removed_files)}",
                meta={"action": "remove_files", "success": True, "input": {"file_names": file_names}}
            )
        else:
            self.printer.print_in_terminal("remove_files_none", style="yellow")
            result_manager.append(
                content=self.printer.get_message_from_key("remove_files_none"),
                meta={"action": "remove_files", "success": False, "input": {"file_names": file_names}}
            )
        return None
    
    def _match_files_by_pattern(self, pattern: str, current_files_abs: List[str], 
                               project_root: str) -> Set[str]:
        """
        根据模式匹配文件
        
        Args:
            pattern: 文件模式
            current_files_abs: 当前文件绝对路径列表
            project_root: 项目根目录
            
        Returns:
            匹配的文件路径集合
        """
        matched_files = set()
        is_wildcard = "*" in pattern or "?" in pattern

        for file_path_abs in current_files_abs:
            relative_path = os.path.relpath(file_path_abs, project_root)
            basename = os.path.basename(file_path_abs)

            matched = False
            if is_wildcard:
                # Match pattern against relative path or basename
                if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(basename, pattern):
                    matched = True
            else:
                # Normalize pattern for comparison
                normalized_pattern = pattern
                if pattern.startswith("./"):
                    normalized_pattern = pattern[2:]  # Remove "./" prefix

                # Also normalize relative_path for comparison
                normalized_relative_path = relative_path
                if relative_path.startswith("./"):
                    normalized_relative_path = relative_path[2:]

                # Exact match against relative path, absolute path, basename, and normalized forms
                if (relative_path == pattern or
                    file_path_abs == pattern or
                    basename == pattern or
                    normalized_relative_path == normalized_pattern or
                    relative_path == normalized_pattern or
                    normalized_relative_path == pattern):
                    matched = True

            if matched:
                matched_files.add(file_path_abs)
                
        return matched_files
