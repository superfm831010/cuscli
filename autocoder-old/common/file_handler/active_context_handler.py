import os
from typing import Optional

from rich.console import Console
from rich.table import Table

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.ac_style_command_parser.parser import parse_query
from autocoder.auto_coder_runner import (
    get_final_config, get_single_llm
)
from autocoder.common.action_yml_file_manager import ActionYmlFileManager
from autocoder.common.printer import Printer
from autocoder.memory.active_context_manager import ActiveContextManager


class ActiveContextHandler:
    """处理活动上下文相关的操作"""
    
    def __init__(self):
        self.console = Console()
        self.printer = Printer()
        self._config = None
    
    def _create_config(self):
        """创建 active_context 命令的类型化配置"""
        if self._config is None:
            self._config = (create_config()
                .collect_remainder("query")  # 收集剩余参数作为查询内容
                .command("list")
                .max_args(0)  # 列出所有任务
                .command("run")
                .positional("file_name", required=True)
                .max_args(1)  # 运行指定文件
                .build()
            )
        return self._config
    
    def handle_active_context_command(self, query: str) -> Optional[None]:
        """
        处理活动上下文命令的主入口
        
        Args:
            query: 查询字符串
            
        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        query = query.strip()
        if not query:
            query = "list"  # 默认列出所有任务
        
        # 解析命令 - 需要处理OrderedDict问题
        commands_infos = parse_query(query)
        command = "list"  # 默认命令是列出所有任务

        if len(commands_infos) > 0:
            if "list" in commands_infos:
                command = "list"
            if "run" in commands_infos:
                command = "run"

        args = get_final_config()
        
        # 获取LLM实例
        llm = get_single_llm(args.model, product_mode=args.product_mode)
        action_file_manager = ActionYmlFileManager(args.source_dir)

        # 获取配置和参数
        active_context_manager = ActiveContextManager(llm, args.source_dir)
        
        if command == "run":
            file_name = commands_infos["run"]["args"][-1]
            args.file = action_file_manager.get_full_path_by_file_name(file_name)
            # 因为更新了args.file
            active_context_manager = ActiveContextManager(llm, args.source_dir)
            task_id = active_context_manager.process_changes(args)
            self.printer.print_in_terminal("active_context_background_task",
                                      style="blue",
                                      task_id=task_id)

        # 处理不同的命令
        if command == "list":
            self._handle_list_command(active_context_manager)
        
        return None
    
    def _handle_list_command(self, active_context_manager: ActiveContextManager) -> None:
        """处理列表命令"""
        # 获取所有任务
        all_tasks = active_context_manager.get_all_tasks()

        if not all_tasks:
            self.console.print("[yellow]没有找到任何活动上下文任务[/yellow]")
            return

        # 创建表格
        table = Table(title="活动上下文任务列表", show_lines=True, expand=True)
        table.add_column("任务ID", style="cyan", no_wrap=False)
        table.add_column("状态", style="green", no_wrap=False)
        table.add_column("开始时间", style="yellow", no_wrap=False)
        table.add_column("完成时间", style="yellow", no_wrap=False)
        table.add_column("文件", style="blue", no_wrap=False)
        table.add_column("Token统计", style="magenta", no_wrap=False)
        table.add_column("费用", style="red", no_wrap=False)

        # 添加任务数据
        for task in all_tasks:
            status = task.get("status", "未知")
            status_display = status

            # 根据状态设置不同的显示样式
            if status == "completed":
                status_display = "[green]已完成[/green]"
            elif status == "running":
                status_display = "[blue]运行中[/blue]"
            elif status == "queued":
                position = task.get("queue_position", 0)
                status_display = f"[yellow]排队中 (位置: {position})[/yellow]"
            elif status == "failed":
                status_display = "[red]失败[/red]"

            # 格式化时间
            start_time = task.get("start_time", "")
            start_time_str = start_time.strftime(
                "%Y-%m-%d %H:%M:%S") if start_time else "未知"

            completion_time = task.get("completion_time", "")
            completion_time_str = completion_time.strftime(
                "%Y-%m-%d %H:%M:%S") if completion_time else "-"

            # 获取文件名
            file_name = task.get("file_name", "未知")

            # 获取token信息
            total_tokens = task.get("total_tokens", 0)
            input_tokens = task.get("input_tokens", 0)
            output_tokens = task.get("output_tokens", 0)
            token_info = f"总计: {total_tokens:,}\n输入: {input_tokens:,}\n输出: {output_tokens:,}"

            # 获取费用信息
            cost = task.get("cost", 0.0)
            cost_info = f"${cost:.6f}"

            # 添加到表格
            table.add_row(
                task.get("task_id", "未知"),
                status_display,
                start_time_str,
                completion_time_str,
                file_name,
                token_info,
                cost_info
            )

        # 显示表格
        console = Console(width=120)  # 设置更宽的显示宽度
        console.print(table)
