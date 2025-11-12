"""
检查任务专属日志记录器

功能：
- 为每个检查任务创建独立的日志文件（保存在报告目录中）
- 自动管理日志处理器的生命周期
- 支持上下文管理器使用

作者: Claude AI
创建时间: 2025-10-13
"""

import os
from typing import Optional
from loguru import logger


class TaskLogger:
    """
    检查任务专属日志记录器

    使用示例:
        >>> with TaskLogger("codecheck/project_20250113_120000") as task_log:
        ...     logger.info("开始检查...")  # 会同时输出到全局日志和任务日志

    说明：
    - 任务日志文件路径：{report_dir}/check.log
    - 日志会同时输出到全局日志和任务日志
    - 使用 with 语句确保正确清理
    """

    def __init__(self, report_dir: str, log_filename: str = "check.log"):
        """
        初始化任务日志记录器

        Args:
            report_dir: 报告目录路径
            log_filename: 日志文件名，默认为 "check.log"
        """
        self.report_dir = report_dir
        self.log_filename = log_filename
        self.log_file_path = os.path.join(report_dir, log_filename)
        self.handler_id: Optional[int] = None

    def __enter__(self):
        """
        进入上下文管理器，创建日志处理器
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器，移除日志处理器
        """
        self.stop()
        return False

    def start(self) -> None:
        """
        开始记录任务日志

        创建日志文件并添加处理器到 loguru
        """
        # 确保报告目录存在
        os.makedirs(self.report_dir, exist_ok=True)

        # 添加日志处理器
        # rotation: 日志文件大小超过 50MB 时自动轮转
        # retention: 保留最近 3 个日志文件
        # compression: 压缩旧的日志文件
        # encoding: 使用 UTF-8 编码
        # format: 日志格式（时间、级别、模块、消息）
        self.handler_id = logger.add(
            self.log_file_path,
            rotation="50 MB",
            retention=3,
            compression="zip",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            enqueue=True,  # 异步写入，避免阻塞
        )

        logger.info(f"任务日志已启动，保存至: {self.log_file_path}")

    def stop(self) -> None:
        """
        停止记录任务日志

        移除日志处理器
        """
        if self.handler_id is not None:
            logger.info(f"任务日志已停止: {self.log_file_path}")
            logger.remove(self.handler_id)
            self.handler_id = None

    def get_log_path(self) -> str:
        """
        获取日志文件路径

        Returns:
            日志文件的完整路径
        """
        return self.log_file_path

    def log_summary(self, summary: str) -> None:
        """
        记录检查摘要信息（作为分隔符）

        Args:
            summary: 摘要信息
        """
        separator = "=" * 80
        logger.info(separator)
        logger.info(f"检查摘要: {summary}")
        logger.info(separator)
