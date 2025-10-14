"""
滚动窗口显示器 - 用于显示 Agent 思考过程的实时进度

这个模块提供了一个滚动窗口显示器，可以捕获并格式化输出，
以5行滚动的方式展示最近的内容，让用户实时看到 Agent 的工作进度。
"""

import sys
import io
import time
import threading
from collections import deque
from contextlib import contextmanager
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from loguru import logger


class RollingDisplay:
    """
    滚动窗口显示器，用于实时显示最近的5行输出

    特性：
    - 维护5行滚动缓冲区
    - 使用 Rich 提供美观的格式化输出
    - 线程安全
    - 支持 Windows 和 Linux
    - 自动处理长行和换行
    """

    def __init__(self, max_lines: int = 5, title: str = "🤖 Agent 思考中..."):
        """
        初始化滚动显示器

        Args:
            max_lines: 显示的最大行数（默认5行）
            title: 面板标题
        """
        self.max_lines = max_lines
        self.title = title
        self.buffer = deque(maxlen=max_lines)
        self.console = Console()
        self.lock = threading.Lock()
        self.live: Optional[Live] = None
        self.original_stdout = None
        self.original_stderr = None
        self.capture_stream = None
        self.capture_thread = None
        self.running = False

    def _create_display(self) -> Panel:
        """创建当前显示面板"""
        with self.lock:
            if not self.buffer:
                content = Text("等待 Agent 响应...", style="dim")
            else:
                # 将缓冲区的行组合成一个 Text 对象
                content = Text()
                for i, line in enumerate(self.buffer):
                    if i > 0:
                        content.append("\n")
                    # 限制每行的最大长度，避免显示问题
                    display_line = line[:200] + "..." if len(line) > 200 else line
                    content.append(display_line)

            return Panel(
                content,
                title=self.title,
                border_style="cyan",
                padding=(0, 1)
            )

    def _process_line(self, line: str):
        """处理并添加一行到缓冲区"""
        if not line.strip():
            return

        with self.lock:
            # 清理 ANSI 转义序列（如果有）
            clean_line = line.strip()

            # 添加到缓冲区（自动移除最老的行如果超过 max_lines）
            self.buffer.append(clean_line)

            # 更新显示
            if self.live:
                try:
                    self.live.update(self._create_display())
                except Exception as e:
                    # 静默处理更新错误
                    logger.debug(f"Failed to update live display: {e}")

    def _capture_output(self):
        """后台线程：捕获并处理输出流"""
        try:
            while self.running:
                line = self.capture_stream.readline()
                if line:
                    # 同时写入原始输出流（保留日志记录）
                    if self.original_stdout:
                        try:
                            self.original_stdout.write(line)
                            self.original_stdout.flush()
                        except:
                            pass

                    # 处理行
                    self._process_line(line)
                else:
                    # 短暂休眠，避免过度消耗 CPU
                    time.sleep(0.05)
        except Exception as e:
            logger.debug(f"Capture thread error: {e}")

    def start(self):
        """启动滚动显示"""
        if self.running:
            return

        self.running = True

        # 保存原始的 stdout 和 stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # 创建捕获流
        self.capture_stream = io.StringIO()

        # 重定向 stdout 到捕获流
        # 创建一个 Tee 类来同时写入捕获流和原始流
        class TeeStream:
            def __init__(self, original, capture):
                self.original = original
                self.capture = capture

            def write(self, data):
                # 写入捕获流
                try:
                    self.capture.write(data)
                except:
                    pass
                # 也写入原始流（用于日志）
                try:
                    self.original.write(data)
                except:
                    pass
                return len(data)

            def flush(self):
                try:
                    self.capture.flush()
                except:
                    pass
                try:
                    self.original.flush()
                except:
                    pass

            def isatty(self):
                return False

        # 使用包装流
        tee = TeeStream(self.original_stdout, self.capture_stream)
        sys.stdout = tee
        sys.stderr = tee

        # 启动捕获线程
        self.capture_thread = threading.Thread(target=self._capture_output, daemon=True)
        self.capture_thread.start()

        # 启动 Rich Live 显示
        try:
            self.live = Live(
                self._create_display(),
                console=self.console,
                refresh_per_second=4,  # 每秒刷新4次
                transient=True  # 完成后不保留显示
            )
            self.live.start()
        except Exception as e:
            logger.warning(f"Failed to start live display: {e}")
            # 如果 Live 启动失败，降级为简单输出
            self.live = None

    def stop(self):
        """停止滚动显示并恢复原始输出"""
        if not self.running:
            return

        self.running = False

        # 停止 Live 显示
        if self.live:
            try:
                self.live.stop()
            except:
                pass
            self.live = None

        # 恢复原始输出流
        if self.original_stdout:
            sys.stdout = self.original_stdout
        if self.original_stderr:
            sys.stderr = self.original_stderr

        # 等待捕获线程结束
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)

    def get_buffer_content(self) -> List[str]:
        """获取当前缓冲区的所有内容"""
        with self.lock:
            return list(self.buffer)

    def __enter__(self):
        """支持上下文管理器"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动停止"""
        self.stop()
        return False


@contextmanager
def rolling_progress(max_lines: int = 5, title: str = "🤖 Agent 思考中..."):
    """
    上下文管理器：方便地使用滚动显示

    用法:
        with rolling_progress():
            # 执行需要显示进度的代码
            agent.chat(...)

    Args:
        max_lines: 显示的最大行数
        title: 面板标题
    """
    display = RollingDisplay(max_lines=max_lines, title=title)
    display.start()
    try:
        yield display
    finally:
        display.stop()


def demo():
    """演示滚动显示器的用法"""
    import time

    print("开始演示滚动显示器...")
    time.sleep(1)

    with rolling_progress(title="🔧 处理任务中..."):
        for i in range(20):
            print(f"步骤 {i + 1}: 正在处理数据...")
            time.sleep(0.5)

            if i % 3 == 0:
                print(f"  -> 子任务: 分析文件...")
            if i % 5 == 0:
                print(f"  -> 子任务: 验证结果...")

    print("\n演示完成！")


if __name__ == "__main__":
    demo()
