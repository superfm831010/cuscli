import os
import tempfile
import threading
import subprocess
from pathlib import Path
from typing import Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from loguru import logger as global_logger


class AsyncCommandHandler:
    """处理 async 指令相关的操作"""

    def __init__(self):
        self.async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
        self.console = Console()
        self._config = None

    def _create_config(self):
        """创建 async 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .collect_remainder("query")
                .command("async")
                .max_args(0)
                .command("model")
                .positional("value", required=True)
                .max_args(1)
                .command("loop")
                .positional("value", type=int)
                .max_args(1)
                .command("effect")
                .positional("value", type=int)
                .max_args(1)
                .command("name")
                .positional("value", required=True)
                .max_args(1)
                .command("prefix")
                .positional("value", required=True)
                .max_args(1)
                .command("list")
                .max_args(0)
                .command("kill")
                .positional("task_id", required=True)
                .max_args(1)
                .command("task")
                .positional("task_id", required=False)
                .max_args(1)
                .command("libs")
                .positional("value", required=True)
                .max_args(1)
                .build()
            )
        return self._config

    def handle_async_command(self, query: str, args) -> Optional[Union[str, None]]:
        """
        处理 async 指令的主入口

        Args:
            query: 查询字符串，例如 "/async /model gpt-4 /loop 3 analysis task"
            args: 配置参数

        Returns:
            None: 表示处理了 async 指令，应该返回而不继续执行
            其他值: 表示没有处理 async 指令，应该继续执行
        """
        # 解析命令
        config = self._create_config()
        result = parse_typed_query(query, config)

        # 检查是否包含 async 命令
        if not result.has_command("async"):
            return "continue"  # 不是 async 指令，继续执行

        # 检查各种子命令
        if result.has_command("list"):
            return self._handle_list_command()

        if result.has_command("kill"):
            return self._handle_kill_command(result)

        if result.has_command("task"):
            return self._handle_task_command(result)

        # 处理异步任务执行
        return self._handle_async_execution(result, args)

    def _handle_list_command(self) -> None:
        """处理 list 子命令 - 显示任务列表"""
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 获取所有任务（已按创建时间排序，最新的在前）
            tasks = metadata_manager.list_tasks()[0:20]

            if not tasks:
                self.console.print(
                    Panel(
                        get_message("async_task_list_no_tasks"),
                        title=get_message("async_task_list_title"),
                        border_style="yellow",
                    )
                )
                return None

            # 创建表格
            table = Table(title=get_message("async_task_list_title"))
            table.add_column(
                get_message("async_task_table_id"), style="cyan", no_wrap=True
            )
            table.add_column(get_message("async_task_table_status"), style="green")
            table.add_column(get_message("async_task_table_model"), style="yellow")
            table.add_column(get_message("async_task_table_created"), style="blue")
            table.add_column(get_message("async_task_table_query"), style="white")
            table.add_column(get_message("async_task_table_log"), style="dim")

            # 添加任务行
            for task in tasks:
                # 状态颜色
                status_color = {
                    "running": get_message("async_task_status_running"),
                    "completed": get_message("async_task_status_completed"),
                    "failed": get_message("async_task_status_failed"),
                }.get(task.status, f"[white]{task.status}[/white]")

                # 格式化时间
                created_time = task.created_at.strftime("%Y-%m-%d %H:%M:%S")

                # 截取查询内容
                query_preview = (
                    task.user_query[:50] + "..."
                    if len(task.user_query) > 50
                    else task.user_query
                )

                # 日志文件路径
                log_file = task.log_file if task.log_file else "-"
                if log_file != "-" and len(log_file) > 30:
                    log_file = "..." + log_file[-27:]

                table.add_row(
                    task.task_id,
                    status_color,
                    task.model or "-",
                    created_time,
                    query_preview,
                    log_file,
                )

            self.console.print(table)

            # 显示汇总信息
            summary = metadata_manager.get_task_summary()
            self.console.print(
                Panel(
                    get_message_with_format(
                        "async_task_list_summary",
                        total=summary["total"],
                        completed=summary["completed"],
                        running=summary["running"],
                        failed=summary["failed"],
                    ),
                    title="📊 Summary",
                    border_style="blue",
                )
            )

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("async_task_list_error", error=str(e)),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_kill_command(self, result) -> None:
        """处理 kill 子命令 - 终止任务"""
        kill_command = result.get_command("kill")
        if not kill_command or not kill_command.args:
            self.console.print(
                Panel(
                    get_message("async_provide_task_id"),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )
            return None

        task_id = kill_command.args[0]
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 获取任务详情
            task = metadata_manager.load_task_metadata(task_id)

            if not task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_not_found", task_id=task_id
                        ),
                        title=get_message("async_task_not_exist"),
                        border_style="red",
                    )
                )
                return None

            # 检查任务状态
            if task.status != "running":
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_cannot_terminate",
                            task_id=task_id,
                            status=task.status,
                        ),
                        title=get_message("async_task_status_error"),
                        border_style="yellow",
                    )
                )
                return None

            # 新的终止逻辑：先杀子进程，再杀主进程
            try:
                import psutil

                killed_processes = []

                # 1. 先终止子进程 (auto-coder.run)
                if task.sub_pid > 0:
                    if psutil.pid_exists(task.sub_pid):
                        try:
                            sub_process = psutil.Process(task.sub_pid)
                            self._terminate_process_tree(sub_process)
                            killed_processes.append(f"子进程 {task.sub_pid} (auto-coder.run)")
                        except psutil.NoSuchProcess:
                            pass
                    else:
                        print(f"[DEBUG] 子进程 {task.sub_pid} 不存在")

                # 2. 再终止主进程 (main.py)
                if task.pid > 0:
                    if psutil.pid_exists(task.pid):
                        try:
                            main_process = psutil.Process(task.pid)
                            self._terminate_process_tree(main_process)
                            killed_processes.append(f"主进程 {task.pid} (main.py)")
                        except psutil.NoSuchProcess:
                            pass
                    else:
                        print(f"[DEBUG] 主进程 {task.pid} 不存在")

                # 更新任务状态
                task.update_status("failed", "Task manually terminated by user")
                metadata_manager.save_task_metadata(task)

                if killed_processes:
                    self.console.print(
                        Panel(
                            get_message_with_format(
                                "async_task_terminated_success",
                                task_id=task_id,
                                pid=f"已终止进程:\n" + "\n".join(f"  - {p}" for p in killed_processes),
                            ),
                            title=get_message("async_terminate_success"),
                            border_style="green",
                        )
                    )
                else:
                    self.console.print(
                        Panel(
                            get_message_with_format("async_no_valid_pid", task_id=task_id),
                            title=get_message("async_terminate_warning"),
                            border_style="yellow",
                        )
                    )

            except ImportError:
                self.console.print(
                    Panel(
                        get_message("async_missing_psutil"),
                        title=get_message("async_dependency_missing"),
                        border_style="red",
                    )
                )
                return None

            except Exception as e:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_terminate_process_error", error=str(e)
                        ),
                        title=get_message("async_terminate_failed"),
                        border_style="red",
                    )
                )
                return None

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format("async_kill_command_error", error=str(e)),
                    title=get_message("async_processing_error"),
                    border_style="red",
                )
            )

        return None

    def _handle_task_command(self, result) -> None:
        """处理 task 子命令 - 显示特定任务详情"""
        task_command = result.get_command("task")
        meta_dir = os.path.join(self.async_agent_dir, "meta")

        try:
            # 导入并初始化任务元数据管理器
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            metadata_manager = TaskMetadataManager(meta_dir)

            # 如果没有提供任务ID，自动获取最新的任务
            if not task_command or not task_command.args:
                tasks = metadata_manager.list_tasks()
                if not tasks:
                    self.console.print(
                        Panel(
                            get_message("async_task_list_no_tasks"),
                            title=get_message("async_task_param_error"),
                            border_style="red",
                        )
                    )
                    return None
                # 获取最新的任务（list_tasks已按创建时间排序，最新的在前）
                task_id = tasks[0].task_id
            else:
                task_id = task_command.args[0]

            # 获取任务详情
            task = metadata_manager.load_task_metadata(task_id)

            if not task:
                self.console.print(
                    Panel(
                        get_message_with_format(
                            "async_task_detail_not_found", task_id=task_id
                        ),
                        title=get_message("async_task_param_error"),
                        border_style="red",
                    )
                )
                return None

            self._display_task_details(task)

        except Exception as e:
            self.console.print(
                Panel(
                    get_message_with_format(
                        "async_task_detail_load_error", error=str(e)
                    ),
                    title=get_message("async_task_param_error"),
                    border_style="red",
                )
            )

        return None

    def _terminate_process_tree(self, process):
        """终止进程及其所有子进程"""
        try:
            import psutil

            # 获取所有子进程
            children = process.children(recursive=True)

            # 先终止所有子进程
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # 终止主进程
            process.terminate()

            # 等待进程结束
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # 强制杀死
                process.kill()
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass

        except psutil.NoSuchProcess:
            # 进程已经不存在
            pass

    def _display_task_details(self, task):
        """显示任务详细信息"""
        # 状态颜色映射
        status_colors = {
            "running": get_message("async_task_status_running"),
            "completed": get_message("async_task_status_completed"),
            "failed": get_message("async_task_status_failed"),
        }
        status_display = status_colors.get(task.status, f"[white]{task.status}[/white]")

        # 创建任务基本信息面板
        yes_text = get_message("async_task_value_yes")
        no_text = get_message("async_task_value_no")

        basic_info = [
            f"[bold]{get_message('async_task_field_id')}:[/bold] [cyan]{task.task_id}[/cyan]",
            f"[bold]{get_message('async_task_field_status')}:[/bold] {status_display}",
            f"[bold]{get_message('async_task_field_model')}:[/bold] [yellow]{task.model or '-'}[/yellow]",
            f"[bold]{get_message('async_task_field_split_mode')}:[/bold] [blue]{task.split_mode or '-'}[/blue]",
            f"[bold]{get_message('async_task_field_bg_mode')}:[/bold] {yes_text if task.background_mode else no_text}",
            f"[bold]{get_message('async_task_field_pr_mode')}:[/bold] {yes_text if task.pull_request else no_text}",
            f"[bold]{get_message('async_task_field_created')}:[/bold] [blue]{task.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/blue]",
        ]

        if task.completed_at:
            basic_info.append(
                f"[bold]{get_message('async_task_field_completed')}:[/bold] [blue]{task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}[/blue]"
            )

            # 计算耗时
            duration = task.completed_at - task.created_at
            total_seconds = int(duration.total_seconds())

            basic_info.append(
                f"[bold]{get_message('async_task_field_duration')}:[/bold] [cyan]{get_message_with_format('async_task_duration_format', duration=total_seconds)}[/cyan]"
            )

        self.console.print(
            Panel(
                "\n".join(basic_info),
                title=get_message("async_task_detail_title"),
                border_style="blue",
            )
        )

        # 显示用户查询内容
        self.console.print(
            Panel(
                f"[white]{task.user_query}[/white]",
                title=get_message("async_task_panel_query"),
                border_style="green",
            )
        )

        # 显示路径信息
        path_info = [
            f"[bold]{get_message('async_task_field_worktree_path')}:[/bold] [dim]{task.worktree_path}[/dim]",
            f"[bold]{get_message('async_task_field_original_path')}:[/bold] [dim]{task.original_project_path}[/dim]",
        ]

        if task.log_file:
            path_info.append(
                f"[bold]{get_message('async_task_field_log_file')}:[/bold] [dim]{task.log_file}[/dim]"
            )

        self.console.print(
            Panel(
                "\n".join(path_info),
                title=get_message("async_task_panel_paths"),
                border_style="cyan",
            )
        )

        # 显示错误信息（如果有）
        if task.error_message:
            self.console.print(
                Panel(
                    f"[red]{task.error_message}[/red]",
                    title=get_message("async_task_panel_error"),
                    border_style="red",
                )
            )

        # 显示执行结果（如果有）
        if task.execution_result:
            self._display_execution_result(task.execution_result)

        # 显示操作提示
        self._display_operation_hints(task)

    def _display_execution_result(self, result):
        """显示执行结果"""
        result_info = []

        if "success" in result:
            success_status = (
                get_message("async_task_value_yes")
                if result["success"]
                else get_message("async_task_value_no")
            )
            result_info.append(
                f"[bold]{get_message('async_task_field_success')}:[/bold] {success_status}"
            )

        if result.get("output"):
            output_preview = result["output"]
            result_info.append(
                f"[bold]{get_message('async_task_field_output_preview')}:[/bold]\n[dim]{output_preview}[/dim]"
            )

        if result.get("error"):
            error_preview = result["error"]
            result_info.append(
                f"[bold]{get_message('async_task_field_error_preview')}:[/bold]\n[red]{error_preview}[/red]"
            )

        if result_info:
            self.console.print(
                Panel(
                    "\n\n".join(result_info),
                    title=get_message("async_task_panel_execution"),
                    border_style="yellow",
                )
            )

    def _display_operation_hints(self, task):
        """显示操作提示"""
        actions = []
        if task.log_file and os.path.exists(task.log_file):
            actions.append(
                get_message_with_format(
                    "async_task_hint_view_log", log_file=task.log_file
                )
            )

        if task.worktree_path and os.path.exists(task.worktree_path):
            actions.append(
                get_message_with_format(
                    "async_task_hint_enter_worktree", worktree_path=task.worktree_path
                )
            )

        actions.append(get_message("async_task_hint_back_to_list"))

        self.console.print(
            Panel(
                "\n".join(actions),
                title=get_message("async_task_operation_hints"),
                border_style="dim",
            )
        )

    def _handle_async_execution(self, result, args) -> None:
        """处理异步任务执行"""
        # 解析参数
        async_query = result.query or ""
        model = args.code_model or args.model

        # 从解析结果中获取参数
        if result.has_command("model"):
            model = result.model

        task_prefix = ""
        if result.has_command("prefix"):
            task_prefix = result.prefix

        worktree_name = ""
        if result.has_command("name"):
            worktree_name = result.name

        loop_count = 1
        if result.has_command("loop"):
            loop_count = result.loop
        elif result.has_command("effect"):
            loop_count = result.effect

        include_libs = ""
        if result.has_command("libs"):
            include_libs = result.libs

        # 执行异步任务
        self._execute_async_task(
            async_query, model, task_prefix, worktree_name, loop_count, include_libs
        )
        return None

    def _execute_async_task(
        self,
        async_query: str,
        model: str,
        task_prefix: str,
        worktree_name: str,
        loop_count: int,
        include_libs: str = "",
    ):
        """执行异步任务"""
        # 创建临时文件并写入查询内容
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(async_query)
            tmp_file_path = tmp_file.name

        # 如果是多轮，则需要改善下提示词
        loop_query = f"{async_query}\n\nAdditional instruction: use git log to get the code changes generated by previous tasks and try to focus on iterative improvements and refinements and make sure to use git commit command to make a commit after every single file edit."
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_file_loop:
            tmp_file_loop.write(loop_query)
            tmp_file_loop_path = tmp_file_loop.name

        def run_async_command():
            """在后台线程中执行异步命令"""

            def execute(index: int):
                target_file = tmp_file_path
                if index > 0:
                    target_file = tmp_file_loop_path
                cmd = f"cat {target_file} | auto-coder.run --async --include-rules --model {model} --verbose --is-sub-agent --worktree-name {worktree_name}"
                if task_prefix:
                    cmd += f" --task-prefix {task_prefix}"
                if include_libs:
                    cmd += f" --include-libs {include_libs}"

                # 执行命令
                if index == 0:
                    global_logger.info(
                        f"Executing async command {index}: {cmd}  async_query: {async_query}"
                    )
                else:
                    global_logger.info(
                        f"Executing async command {index}: {cmd}  async_query: {loop_query}"
                    )

                v = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                global_logger.info(f"Async command result: {v.stdout}")

            try:
                for i in range(loop_count):
                    execute(i)
            except Exception as e:
                global_logger.error(f"Error executing async command: {e}")
            finally:
                # 删除临时文件
                try:
                    os.remove(tmp_file_path)
                    os.remove(tmp_file_loop_path)
                except:
                    pass

        # 在新线程中启动异步任务
        thread = threading.Thread(target=run_async_command, daemon=True)
        thread.start()

        # 打印任务信息
        query_preview = async_query[:100] + ("..." if len(async_query) > 100 else "")

        # 根据是否有 name 参数选择不同的消息格式
        if worktree_name:
            message_content = get_message_with_format(
                "async_task_started_message_with_name",
                model=model,
                query=query_preview,
                name=worktree_name,
                agent_dir=self.async_agent_dir,
            )
        else:
            message_content = get_message_with_format(
                "async_task_started_message",
                model=model,
                query=query_preview,
                agent_dir=self.async_agent_dir,
            )

        self.console.print(
            Panel(
                message_content,
                title=get_message("async_task_title"),
                border_style="green",
            )
        )
