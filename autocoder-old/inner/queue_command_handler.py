import re
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.common.agent_query_queue.queue_manager import (
    QueueManager,
    QueueTaskStatus,
)
from autocoder.common.agent_query_queue.queue_executor import (
    get_global_queue_executor,
    start_global_queue_executor,
)


class QueueCommandHandler:
    """处理 queue 指令相关的操作"""

    def __init__(self):
        self.queue_manager = QueueManager()
        self.console = Console()
        self._config = None

    def _create_config(self):
        """创建 queue 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .collect_remainder("query")
                .command("queue")
                .collect_remainder("query")
                .command("list")
                .positional("status_filter", required=False)
                .max_args(1)
                .command("remove")
                .positional("task_id", required=True)
                .max_args(1)
                .command("clear")
                .max_args(0)
                .command("stats")
                .max_args(0)
                .command("start")
                .max_args(0)
                .command("stop")
                .max_args(0)
                .command("status")
                .max_args(0)
                .command("name")
                .positional("worktree_name", required=True)
                .collect_remainder("query")
                .build()
            )
        return self._config

    def handle_queue_command(self, query: str, args) -> Optional[None]:
        """
        处理 queue 指令的主入口

        Args:
            query: 查询字符串，例如 "/queue /list pending" 或 "/queue some task"
            args: 配置参数

        Returns:
            None: 表示处理了 queue 指令，应该返回而不继续执行
            其他值: 表示没有处理 queue 指令，应该继续执行
        """
        # 解析命令
        config = self._create_config()
        result = parse_typed_query(query, config)

        # 检查是否包含 queue 命令
        if not result.has_command("queue"):
            return "continue"  # 不是 queue 指令，继续执行

        # 检查各种子命令
        if result.has_command("list"):
            return self._handle_list_command(result)

        if result.has_command("remove"):
            return self._handle_remove_command(result)

        # 处理清理已完成任务
        if result.has_command("clear"):
            return self._handle_clear_command()

        # 处理统计信息
        if result.has_command("stats"):
            return self._handle_stats_command()

        # 处理启动执行器
        if result.has_command("start"):
            return self._handle_start_command()

        # 处理停止执行器
        if result.has_command("stop"):
            return self._handle_stop_command()

        # 处理执行器状态
        if result.has_command("status"):
            return self._handle_status_command()

        # 处理自定义 worktree 名称
        if result.has_command("name"):
            return self._handle_name_command(result, args)

        # 如果有剩余查询，则作为用户需求添加到队列
        user_query = result.query
        # 如果 result.query 为空，尝试从 queue 命令的 remainder 获取
        if not user_query:
            queue_command = result.get_command("queue")
            if queue_command and queue_command.remainder:
                user_query = queue_command.remainder

        if user_query:
            return self._handle_add_query_command(user_query, args)

        # 默认显示帮助信息
        return self._handle_help_command()

    def _handle_list_command(self, result) -> None:
        """处理 list 子命令 - 显示任务列表"""
        try:
            # 检查是否有状态过滤参数
            status_filter = None
            list_command = result.get_command("list")

            if list_command and list_command.args:
                status_arg = list_command.args[0].lower()
                try:
                    status_filter = QueueTaskStatus(status_arg)
                except ValueError:
                    self.console.print(
                        Panel(
                            get_message_with_format(
                                "queue_invalid_status_filter", status=status_arg
                            ),
                            title=get_message("queue_param_error"),
                            border_style="red",
                        )
                    )
                    return None

            # 获取任务列表
            tasks = self.queue_manager.list_tasks(status_filter)

            if not tasks:
                filter_text = (
                    get_message_with_format(
                        "queue_status_filter", status=status_filter.value
                    )
                    if status_filter
                    else ""
                )
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "queue_no_tasks_found", filter=filter_text
                        ),
                        title=get_message("queue_task_list"),
                        border_style="yellow",
                    )
                )
                return None

            # 创建表格
            table = Table(title=get_message("queue_task_list"))
            table.add_column(get_message("queue_task_id"), style="cyan", no_wrap=True)
            table.add_column(get_message("queue_status"), style="green")
            table.add_column(get_message("queue_priority"), style="yellow")
            table.add_column("Worktree", style="magenta")
            table.add_column(get_message("queue_created_time"), style="blue")
            table.add_column(get_message("queue_started_time"), style="blue")
            table.add_column(get_message("queue_completed_time"), style="blue")
            table.add_column(get_message("queue_query"), style="white")
            table.add_column(get_message("queue_result_error"), style="dim")

            # 添加任务行
            for task in tasks:
                # 状态颜色

                status_color = {
                    QueueTaskStatus.PENDING: get_message("queue_status_pending"),
                    QueueTaskStatus.RUNNING: get_message("queue_status_running"),
                    QueueTaskStatus.COMPLETED: get_message("queue_status_completed"),
                    QueueTaskStatus.FAILED: get_message("queue_status_failed"),
                    QueueTaskStatus.CANCELLED: get_message("queue_status_cancelled"),
                }.get(task.status, f"[white]{task.status.value}[/white]")

                # 格式化时间
                created_time = (
                    task.created_at.strftime("%m-%d %H:%M:%S")
                    if task.created_at
                    else "-"
                )
                started_time = (
                    task.started_at.strftime("%m-%d %H:%M:%S")
                    if task.started_at
                    else "-"
                )
                completed_time = (
                    task.completed_at.strftime("%m-%d %H:%M:%S")
                    if task.completed_at
                    else "-"
                )

                # 截取需求内容
                query_preview = (
                    task.user_query[:40] + "..."
                    if len(task.user_query) > 40
                    else task.user_query
                )

                # Worktree 名称显示
                worktree_display = task.worktree_name or "-"

                # 结果或错误信息
                result_info = ""
                if task.error_message:
                    error_text = (
                        task.error_message[:30] + "..."
                        if len(task.error_message) > 30
                        else task.error_message
                    )
                    result_info = get_message_with_format(
                        "queue_error_prefix", error=error_text
                    )
                elif task.result:
                    result_info = (
                        f"{task.result[:30]}..."
                        if len(task.result) > 30
                        else task.result
                    )
                else:
                    result_info = "-"

                table.add_row(
                    task.task_id,
                    status_color,
                    str(task.priority),
                    worktree_display,
                    created_time,
                    started_time,
                    completed_time,
                    query_preview,
                    result_info,
                )

            self.console.print(table)

            # 显示统计信息
            stats = self.queue_manager.get_queue_statistics()
            self.console.print(
                Panel(
                    get_message_with_format("queue_stats_total", **stats),
                    title=get_message("queue_statistics"),
                    border_style="blue",
                )
            )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_get_tasks_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_remove_command(self, result) -> None:
        """处理 remove 子命令 - 移除任务"""
        remove_command = result.get_command("remove")

        if not remove_command or not remove_command.args:
            self.console.print(
                Panel(
                    get_message("queue_provide_task_id"),
                    title=get_message("queue_param_error"),
                    border_style="red",
                )
            )
            return None

        task_id = remove_command.args[0]

        try:
            # 检查任务是否存在
            task = self.queue_manager.get_task(task_id)
            if not task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "queue_task_not_found", task_id=task_id
                        ),
                        title=get_message("queue_task_not_exist"),
                        border_style="red",
                    )
                )
                return None

            if task.status == QueueTaskStatus.RUNNING:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "queue_task_running_cannot_remove", task_id=task_id
                        ),
                        title=get_message("queue_task_status_error"),
                        border_style="yellow",
                    )
                )
                return None

            # 移除任务
            if self.queue_manager.remove_task(task_id):
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "queue_task_removed_success", task_id=task_id
                        ),
                        title=get_message("queue_remove_success"),
                        border_style="green",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        get_message_with_format("queue_remove_failed", task_id=task_id),
                        title=get_message("queue_remove_failed_title"),
                        border_style="red",
                    )
                )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_remove_task_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_add_query_command(
        self, user_query: str, args, worktree_name: str = None
    ) -> None:
        """处理添加用户需求到队列"""
        try:
            # 获取模型配置
            model = args.code_model or args.model or "auto"

            # 添加任务到队列
            task_id = self.queue_manager.add_task(
                user_query=user_query,
                model=model,
                priority=0,
                worktree_name=worktree_name,
            )

            query_preview = user_query[:100] + ("..." if len(user_query) > 100 else "")
            success_message = get_message_with_format(
                "queue_task_added_success",
                task_id=task_id,
                query=query_preview,
                model=model,
            )

            if worktree_name:
                success_message += f"\n{get_message_with_format('queue_custom_worktree_info', worktree_name=worktree_name)}"

            self.console.print(
                Panel(
                    success_message,
                    title=get_message("queue_add_success"),
                    border_style="green",
                )
            )

            # 自动启动执行器（如果还没启动）
            from autocoder.common.agent_query_queue.queue_executor import (
                get_global_queue_executor,
                start_global_queue_executor,
            )

            executor = get_global_queue_executor()
            if not executor.is_running():
                start_global_queue_executor()
                self.console.print(
                    Panel(
                        get_message("queue_executor_auto_started"),
                        title=get_message("queue_executor_status"),
                        border_style="blue",
                    )
                )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_add_task_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_name_command(self, result, args) -> None:
        """处理 name 子命令 - 使用自定义 worktree 名称添加任务"""
        name_command = result.get_command("name")

        if not name_command or not name_command.args:
            self.console.print(
                Panel(
                    get_message("queue_name_command_usage"),
                    title=get_message("queue_param_error"),
                    border_style="red",
                )
            )
            return None

        # 第一个参数是 worktree 名称，查询来自 remainder
        worktree_name = name_command.args[0]
        user_query = result.query

        if not user_query:
            self.console.print(
                Panel(
                    get_message("queue_name_command_usage"),
                    title=get_message("queue_param_error"),
                    border_style="red",
                )
            )
            return None

        # 验证 worktree 名称
        if not self._validate_worktree_name(worktree_name):
            self.console.print(
                Panel(
                    get_message_with_format(
                        "queue_invalid_worktree_name", name=worktree_name
                    ),
                    title=get_message("queue_param_error"),
                    border_style="red",
                )
            )
            return None

        # 调用添加任务的方法，传入自定义 worktree 名称
        return self._handle_add_query_command(user_query, args, worktree_name)

    def _validate_worktree_name(self, name: str) -> bool:
        """验证 worktree 名称是否合法"""
        # 基本验证：不为空，不包含特殊字符
        if not name or len(name.strip()) == 0:
            return False

        # 检查是否包含不合法字符（git worktree 名称限制）
        # 允许字母、数字、下划线、连字符
        if not re.match(r"^[a-zA-Z0-9_-]+$", name.strip()):
            return False

        return True

    def _handle_clear_command(self) -> None:
        """处理 clear 子命令 - 清理已完成的任务"""
        try:
            removed_count = self.queue_manager.clear_completed_tasks()

            if removed_count > 0:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "queue_cleared_count", count=removed_count
                        ),
                        title=get_message("queue_clear_success"),
                        border_style="green",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        get_message("queue_no_completed_tasks"),
                        title=get_message("queue_clear_completed"),
                        border_style="yellow",
                    )
                )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_clear_tasks_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_stats_command(self) -> None:
        """处理 stats 子命令 - 显示统计信息"""
        try:
            stats = self.queue_manager.get_queue_statistics()

            # 创建统计表格
            table = Table(title=get_message("queue_stats_info"))
            table.add_column(get_message("queue_stats_status_column"), style="cyan")
            table.add_column(
                get_message("queue_stats_count_column"), style="green", justify="right"
            )
            table.add_column(
                get_message("queue_stats_percentage_column"),
                style="yellow",
                justify="right",
            )

            total = stats["total"]
            if total > 0:
                for status, count in stats.items():
                    if status != "total":
                        percentage = (count / total) * 100
                        status_display = {
                            "pending": get_message("queue_stats_pending_display"),
                            "running": get_message("queue_stats_running_display"),
                            "completed": get_message("queue_stats_completed_display"),
                            "failed": get_message("queue_stats_failed_display"),
                            "cancelled": get_message("queue_stats_cancelled_display"),
                        }.get(status, status)

                        table.add_row(status_display, str(count), f"{percentage:.1f}%")

                table.add_section()
                table.add_row(
                    get_message("queue_stats_total_bold"),
                    f"[bold]{total}[/bold]",
                    "[bold]100.0%[/bold]",
                )
            else:
                table.add_row(get_message("queue_stats_no_tasks"), "0", "0%")

            self.console.print(table)

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_get_stats_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_start_command(self) -> None:
        """处理 start 子命令 - 启动队列执行器"""
        try:

            executor = get_global_queue_executor()
            if executor.is_running():
                self.console.print(
                    Panel(
                        get_message("queue_executor_already_running"),
                        title=get_message("queue_status_info"),
                        border_style="yellow",
                    )
                )
            else:
                start_global_queue_executor()
                self.console.print(
                    Panel(
                        get_message("queue_executor_started"),
                        title=get_message("queue_start_success"),
                        border_style="green",
                    )
                )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_start_executor_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_stop_command(self) -> None:
        """处理 stop 子命令 - 停止队列执行器"""
        try:
            from autocoder.common.agent_query_queue.queue_executor import (
                get_global_queue_executor,
                stop_global_queue_executor,
            )

            executor = get_global_queue_executor()
            if not executor.is_running():
                self.console.print(
                    Panel(
                        get_message("queue_executor_not_running"),
                        title=get_message("queue_status_info"),
                        border_style="yellow",
                    )
                )
            else:
                stop_global_queue_executor()
                self.console.print(
                    Panel(
                        get_message("queue_executor_stopped"),
                        title=get_message("queue_stop_success"),
                        border_style="green",
                    )
                )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_stop_executor_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_status_command(self) -> None:
        """处理 status 子命令 - 显示执行器状态"""
        try:
            from autocoder.common.agent_query_queue.queue_executor import (
                get_global_queue_executor,
            )

            executor = get_global_queue_executor()
            is_running = executor.is_running()
            running_tasks_count = executor.get_running_tasks_count()

            # 获取队列统计
            stats = self.queue_manager.get_queue_statistics()

            status_icon = (
                get_message("queue_status_running_icon")
                if is_running
                else get_message("queue_status_stopped_icon")
            )
            status_text = get_message_with_format(
                "queue_executor_status_text",
                status=status_icon,
                running_count=running_tasks_count,
                pending_count=stats["pending"],
                **stats,
            )

            self.console.print(
                Panel(
                    status_text,
                    title=get_message("queue_status_title"),
                    border_style="blue",
                )
            )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("queue_get_status_error", error=str(e)),
                    title=get_message("queue_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_help_command(self) -> None:
        """显示帮助信息"""
        self.console.print(
            Panel(
                get_message("queue_help_content_with_name"),
                title=get_message("queue_help_title"),
                border_style="blue",
            )
        )

        return None
