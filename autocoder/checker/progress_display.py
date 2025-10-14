"""
进度显示管理器（优化版）

提供简洁清晰的多层级进度显示，用于代码检查任务。

优化：
- 只有主进度显示完整进度条
- Chunk和LLM信息用紧凑文本显示
- 减少视觉干扰，提高信息密度

作者: Claude AI
创建时间: 2025-10-13
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text
from rich.panel import Panel


class ProgressDisplay:
    """
    进度显示管理器（优化版）

    使用更简洁的布局，减少冗余信息。
    """

    def __init__(self, console: Optional[Console] = None):
        """
        初始化进度显示管理器

        Args:
            console: Rich Console实例，如果为None则创建新实例
        """
        self.console = console or Console()

        # 进度条实例（只用于主进度）
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=self.console,
            expand=False
        )

        # 状态追踪
        self.current_state: Dict[str, Any] = {
            # 文件级统计
            "total_files": 0,
            "completed_files": 0,
            "current_file": "",
            "files_start_time": None,

            # Chunk级统计
            "total_chunks": 0,
            "completed_chunks": 0,
            "current_chunk": 0,
            "chunk_info": {},

            # LLM调用统计
            "llm_current_attempt": 0,
            "llm_total_attempts": 0,
            "llm_call_start_time": None,
            "llm_total_calls": 0,
            "llm_total_duration": 0.0,
            "llm_last_duration": 0.0,
            "llm_last_issues_found": 0,

            # LLM配置参数
            "llm_repeat": 1,
            "llm_consensus": 1.0,

            # 速度统计
            "files_per_minute": 0.0,
            "chunks_per_minute": 0.0,
            "avg_llm_response_time": 0.0,
        }

        # 任务ID
        self.main_task_id = None

        # Live display
        self.live = None

    def _create_status_text(self) -> Text:
        """创建状态文本（Chunk和LLM信息）"""
        lines = []

        # Chunk信息
        if self.current_state["total_chunks"] > 0:
            chunk_idx = self.current_state["current_chunk"] + 1
            total_chunks = self.current_state["total_chunks"]
            chunk_info = self.current_state.get("chunk_info", {})

            chunk_text = f"📦 Chunk {chunk_idx}/{total_chunks}"

            start_line = chunk_info.get("start_line")
            end_line = chunk_info.get("end_line")
            tokens = chunk_info.get("tokens")

            if start_line and end_line:
                chunk_text += f" (行 {start_line}-{end_line}"
                if tokens:
                    chunk_text += f", ~{tokens} tokens"
                chunk_text += ")"

            lines.append(chunk_text)

        # LLM信息
        if self.current_state["llm_total_attempts"] > 0:
            llm_text = f"🤖 LLM调用 {self.current_state['llm_current_attempt']}/{self.current_state['llm_total_attempts']}"

            if self.current_state["llm_last_duration"] > 0:
                llm_text += f" | ⏱ {self.current_state['llm_last_duration']:.1f}s"

            if self.current_state["avg_llm_response_time"] > 0:
                llm_text += f" | 平均: {self.current_state['avg_llm_response_time']:.1f}s/次"

            if self.current_state["llm_last_issues_found"] >= 0:
                llm_text += f" | 📋 发现 {self.current_state['llm_last_issues_found']} 个问题"

            lines.append(llm_text)

        # 参数说明（移到条件块外，检查进行中时始终显示）
        if self.current_state["total_files"] > 0:
            repeat = self.current_state["llm_repeat"]
            consensus = self.current_state["llm_consensus"]
            param_text = f"⚙️  repeat={repeat} (↑值=↑准确↓速度), consensus={consensus:.2f} (↑值=↓误报↑漏报) | 修改: /check /config"
            lines.append(param_text)

        # 组合文本
        if lines:
            text = Text("\n".join(lines))
        else:
            text = Text("")

        return text

    def _create_display_group(self) -> Group:
        """创建显示组（进度条+状态文本）"""
        components = [self.progress]

        status_text = self._create_status_text()
        if status_text.plain:
            components.append(status_text)

        return Group(*components)

    @contextmanager
    def display_progress(self):
        """
        上下文管理器，用于显示进度

        使用方式：
            with progress_display.display_progress():
                # 执行任务
                pass
        """
        self.live = Live(
            self._create_display_group(),
            console=self.console,
            refresh_per_second=4,
            transient=False
        )

        with self.live:
            yield self

    def _update_display(self):
        """更新显示内容"""
        if self.live:
            self.live.update(self._create_display_group())

    def update_file_progress(
        self,
        total_files: Optional[int] = None,
        completed_files: Optional[int] = None,
        current_file: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        更新文件级进度

        Args:
            total_files: 总文件数
            completed_files: 已完成文件数
            current_file: 当前文件名
            description: 自定义描述
        """
        if total_files is not None:
            self.current_state["total_files"] = total_files
            if self.current_state["files_start_time"] is None:
                self.current_state["files_start_time"] = time.time()

        if completed_files is not None:
            self.current_state["completed_files"] = completed_files

            # 计算文件处理速度
            if self.current_state["files_start_time"]:
                elapsed = time.time() - self.current_state["files_start_time"]
                if elapsed > 0 and completed_files > 0:
                    self.current_state["files_per_minute"] = (completed_files / elapsed) * 60

        if current_file is not None:
            self.current_state["current_file"] = current_file

        # 构造描述
        if description is None:
            if self.current_state["total_files"] > 1:
                # 文件夹检查模式
                speed_text = ""
                if self.current_state["files_per_minute"] > 0:
                    speed_text = f" | 🚀 {self.current_state['files_per_minute']:.1f} files/min"

                description = (
                    f"📂 检查进度: {self.current_state['completed_files']}/{self.current_state['total_files']}"
                    f"{speed_text}"
                )
            else:
                # 单文件检查模式
                file_name = self.current_state["current_file"]
                if len(file_name) > 40:
                    file_name = "..." + file_name[-37:]
                description = f"📄 检查文件: {file_name}"

        # 更新或创建任务
        if self.main_task_id is None:
            self.main_task_id = self.progress.add_task(
                description,
                total=self.current_state["total_files"] or None
            )
        else:
            self.progress.update(
                self.main_task_id,
                completed=self.current_state["completed_files"],
                total=self.current_state["total_files"] or None,
                description=description
            )

        self._update_display()

    def update_chunk_progress(
        self,
        total_chunks: Optional[int] = None,
        completed_chunks: Optional[int] = None,
        current_chunk: Optional[int] = None,
        chunk_info: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ):
        """
        更新chunk级进度

        Args:
            total_chunks: 总chunk数
            completed_chunks: 已完成chunk数
            current_chunk: 当前chunk索引（0-based）
            chunk_info: chunk信息（start_line, end_line, tokens等）
            description: 自定义描述（忽略，用于兼容）
        """
        if total_chunks is not None:
            self.current_state["total_chunks"] = total_chunks

        if completed_chunks is not None:
            self.current_state["completed_chunks"] = completed_chunks

        if current_chunk is not None:
            self.current_state["current_chunk"] = current_chunk

        if chunk_info:
            self.current_state["chunk_info"] = chunk_info

        self._update_display()

    def update_llm_progress(
        self,
        event: str,
        attempt: Optional[int] = None,
        total_attempts: Optional[int] = None,
        duration: Optional[float] = None,
        issues_found: Optional[int] = None,
        description: Optional[str] = None
    ):
        """
        更新LLM调用进度

        Args:
            event: 事件类型 ('start', 'end', 'aggregate')
            attempt: 当前尝试次数（1-based）
            total_attempts: 总尝试次数
            duration: 本次调用耗时（秒）
            issues_found: 本次发现的问题数
            description: 自定义描述（忽略，用于兼容）
        """
        if event == "start":
            if attempt is not None:
                self.current_state["llm_current_attempt"] = attempt
            if total_attempts is not None:
                self.current_state["llm_total_attempts"] = total_attempts
            self.current_state["llm_call_start_time"] = time.time()

        elif event == "end":
            # 记录本次调用
            self.current_state["llm_total_calls"] += 1

            if duration is not None:
                self.current_state["llm_last_duration"] = duration
                self.current_state["llm_total_duration"] += duration

                # 计算平均响应时间
                if self.current_state["llm_total_calls"] > 0:
                    self.current_state["avg_llm_response_time"] = (
                        self.current_state["llm_total_duration"] /
                        self.current_state["llm_total_calls"]
                    )

            if issues_found is not None:
                self.current_state["llm_last_issues_found"] = issues_found

        elif event == "aggregate":
            # 聚合完成，清空LLM显示
            pass

        self._update_display()

    def update_llm_config(self, repeat: int, consensus: float):
        """
        更新LLM配置参数

        Args:
            repeat: LLM重复调用次数
            consensus: 共识阈值
        """
        self.current_state["llm_repeat"] = repeat
        self.current_state["llm_consensus"] = consensus
        self._update_display()

    def remove_llm_task(self):
        """清除LLM显示（兼容接口）"""
        self.current_state["llm_total_attempts"] = 0
        self.current_state["llm_current_attempt"] = 0
        self._update_display()

    def remove_chunk_task(self):
        """清除chunk显示（兼容接口）"""
        self.current_state["total_chunks"] = 0
        self.current_state["current_chunk"] = 0
        self.current_state["chunk_info"] = {}
        self._update_display()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "files_completed": self.current_state["completed_files"],
            "files_total": self.current_state["total_files"],
            "files_per_minute": self.current_state["files_per_minute"],
            "chunks_completed": self.current_state["completed_chunks"],
            "chunks_total": self.current_state["total_chunks"],
            "llm_total_calls": self.current_state["llm_total_calls"],
            "llm_total_duration": self.current_state["llm_total_duration"],
            "llm_avg_response_time": self.current_state["avg_llm_response_time"],
        }


class SimpleProgressCallback:
    """
    简单的进度回调适配器

    将core.py的回调事件转换为ProgressDisplay的更新调用。
    适用于单文件检查场景。
    """

    def __init__(
        self,
        progress_display: ProgressDisplay,
        file_path: str,
        repeat: int = 1,
        consensus: float = 1.0
    ):
        """
        初始化回调适配器

        Args:
            progress_display: 进度显示管理器
            file_path: 文件路径
            repeat: LLM重复调用次数
            consensus: 共识阈值
        """
        self.display = progress_display
        self.file_path = file_path
        self.total_chunks = 0
        self.completed_chunks = 0

        # 更新LLM配置参数到显示器
        self.display.update_llm_config(repeat, consensus)

    def __call__(self, step: str, **kwargs):
        """
        处理进度回调事件

        Args:
            step: 事件类型
            **kwargs: 事件参数
        """
        if step == "start":
            # 开始检查
            self.display.update_file_progress(
                total_files=1,
                completed_files=0,
                current_file=self.file_path
            )

        elif step == "rules_loaded":
            # 规则加载完成
            pass  # 不需要显示

        elif step == "chunked":
            # 文件分块完成
            self.total_chunks = kwargs.get("total_chunks", 0)
            self.display.update_chunk_progress(
                total_chunks=self.total_chunks,
                completed_chunks=0
            )

        elif step == "chunk_start":
            # 开始检查某个chunk
            chunk_index = kwargs.get("chunk_index", 0)

            chunk_info = {
                "start_line": kwargs.get("start_line"),
                "end_line": kwargs.get("end_line"),
                "tokens": kwargs.get("tokens"),
            }

            self.display.update_chunk_progress(
                current_chunk=chunk_index,
                chunk_info=chunk_info
            )

        elif step == "chunk_done":
            # 某个chunk检查完成
            chunk_index = kwargs.get("chunk_index", 0)
            self.completed_chunks = chunk_index + 1

            self.display.update_chunk_progress(
                completed_chunks=self.completed_chunks
            )

        elif step == "llm_call_start":
            # LLM调用开始
            attempt = kwargs.get("attempt", 1)
            total_attempts = kwargs.get("total_attempts", 1)

            self.display.update_llm_progress(
                event="start",
                attempt=attempt,
                total_attempts=total_attempts
            )

        elif step == "llm_call_end":
            # LLM调用结束
            attempt = kwargs.get("attempt", 1)
            duration = kwargs.get("duration", 0.0)
            issues_found = kwargs.get("issues_found", 0)

            self.display.update_llm_progress(
                event="end",
                attempt=attempt,
                duration=duration,
                issues_found=issues_found
            )

        elif step == "llm_aggregate":
            # 聚合结果
            self.display.update_llm_progress(
                event="aggregate"
            )

        elif step == "merge_done":
            # 结果合并完成
            self.display.remove_llm_task()
            self.display.remove_chunk_task()
            self.display.update_file_progress(
                completed_files=1
            )


class BatchProgressCallback:
    """
    批量检查进度回调适配器（简化版）

    适用于文件夹检查场景，显示多文件进度。
    不再为每个文件显示详细的chunk/LLM信息。
    """

    def __init__(self, progress_display: ProgressDisplay, total_files: int):
        """
        初始化回调适配器

        Args:
            progress_display: 进度显示管理器
            total_files: 总文件数
        """
        self.display = progress_display
        self.total_files = total_files
        self.completed_files = 0
        self.current_file = ""

        # 初始化文件级进度
        self.display.update_file_progress(
            total_files=total_files,
            completed_files=0
        )

    def on_file_start(self, file_path: str):
        """
        文件开始检查

        Args:
            file_path: 文件路径
        """
        self.current_file = file_path
        self.display.update_file_progress(
            current_file=file_path
        )

    def on_file_complete(self, file_path: str):
        """
        文件检查完成

        Args:
            file_path: 文件路径
        """
        self.completed_files += 1
        self.display.update_file_progress(
            completed_files=self.completed_files
        )

    def create_file_callback(self, file_path: str) -> SimpleProgressCallback:
        """
        为单个文件创建回调（批量检查时不使用）

        Args:
            file_path: 文件路径

        Returns:
            None（批量检查时不显示文件内部进度）
        """
        # 批量检查时不显示每个文件的详细进度
        return None
