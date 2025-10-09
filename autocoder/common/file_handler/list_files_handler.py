import os
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.auto_coder_runner import get_current_files


class ListFilesHandler:
    """处理文件列表显示相关的操作"""
    
    def __init__(self):
        self.console = Console()
        self._config = None
    
    def _create_config(self):
        """创建 list_files 命令的类型化配置"""
        if self._config is None:
            self._config = (create_config()
                .collect_remainder("query")  # 收集剩余参数（虽然当前不使用）
                .command("tokens")
                .max_args(0)  # 显示Token统计
                .command("simple")
                .max_args(0)  # 简单列表模式
                .build()
            )
        return self._config
    
    def handle_list_files_command(self) -> Optional[None]:
        """
        处理文件列表命令的主入口
        
        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        # 获取当前文件列表
        project_root = os.getcwd()
        current_files = get_current_files()
        
        if current_files:
            self._display_files_with_tokens(current_files, project_root)
        else:
            self._display_no_files()
        
        return None
    
    def _display_files_with_tokens(self, current_files: list, project_root: str) -> None:
        """显示文件列表和Token统计"""
        # Import token counting functions
        from autocoder.common.tokens import count_file_tokens, count_directory_tokens

        table = Table(
            title="Current Files", show_header=True, header_style="bold magenta"
        )
        table.add_column("File", style="green")
        table.add_column("Tokens", style="cyan", justify="right")

        total_tokens = 0

        for file_path in current_files:
            relative_path = os.path.relpath(file_path, project_root)

            # Calculate tokens based on whether it's a file or directory
            try:
                if os.path.isfile(file_path):
                    # Handle single file
                    result = count_file_tokens(file_path)
                    if result.success:
                        tokens = result.token_count
                        total_tokens += tokens
                        table.add_row(relative_path, f"{tokens:,}")
                    else:
                        table.add_row(relative_path, "[red]Error[/red]")
                elif os.path.isdir(file_path):
                    # Handle directory recursively
                    result = count_directory_tokens(
                        file_path,
                        recursive=True
                    )
                    tokens = result.total_tokens
                    total_tokens += tokens
                    table.add_row(f"{relative_path}/", f"{tokens:,}")
                else:
                    # Handle non-existent files
                    table.add_row(relative_path, "[yellow]Not found[/yellow]")
            except Exception as e:
                # Handle any errors during token counting
                table.add_row(
                    relative_path, f"[red]Error: {str(e)[:30]}[/red]")

        # Add total row
        if total_tokens > 0:
            table.add_section()
            table.add_row("[bold]Total[/bold]",
                          f"[bold cyan]{total_tokens:,}[/bold cyan]")

        self.console.print(Panel(table, border_style="blue"))
    
    def _display_no_files(self) -> None:
        """显示无文件提示"""
        self.console.print(
            Panel(
                "No files in the current session.",
                title="Current Files",
                border_style="yellow",
            )
        )
