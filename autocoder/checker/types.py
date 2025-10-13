"""
代码检查模块的核心数据模型定义

使用 pydantic 进行数据验证和序列化。
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class Severity(str, Enum):
    """
    问题严重程度枚举

    - ERROR: 必须修复的严重问题，可能导致系统崩溃、安全漏洞或数据丢失
    - WARNING: 强烈建议修复的问题，影响代码质量、性能或可维护性
    - INFO: 建议改进的问题，主要是命名规范、注释建议等
    """
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Rule(BaseModel):
    """
    代码检查规则定义

    Attributes:
        id: 规则唯一标识符，如 "backend_001", "frontend_001"
        category: 规则所属类别，如 "代码结构", "安全性", "性能优化"
        title: 规则简短标题
        description: 规则详细描述
        severity: 违反此规则的严重程度
        enabled: 规则是否启用
        examples: 示例代码（包含错误示例和正确示例）
    """
    id: str = Field(..., description="规则唯一标识符")
    category: str = Field(..., description="规则类别")
    title: str = Field(..., description="规则标题")
    description: str = Field(..., description="规则详细描述")
    severity: Severity = Field(..., description="严重程度")
    enabled: bool = Field(default=True, description="是否启用此规则")
    examples: Optional[str] = Field(default=None, description="示例代码")

    class Config:
        use_enum_values = True


class Issue(BaseModel):
    """
    代码检查发现的问题

    Attributes:
        rule_id: 违反的规则ID
        severity: 问题严重程度
        line_start: 问题代码起始行号（从1开始）
        line_end: 问题代码结束行号
        description: 问题的详细描述
        suggestion: 修复建议
        code_snippet: 问题代码片段
    """
    rule_id: str = Field(..., description="违反的规则ID")
    severity: Severity = Field(..., description="问题严重程度")
    line_start: int = Field(..., ge=1, description="问题起始行号")
    line_end: int = Field(..., ge=1, description="问题结束行号")
    description: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="修复建议")
    code_snippet: Optional[str] = Field(default=None, description="问题代码片段")

    class Config:
        use_enum_values = True


class FileCheckResult(BaseModel):
    """
    单个文件的检查结果

    Attributes:
        file_path: 被检查的文件路径
        check_time: 检查时间（ISO 8601格式）
        issues: 发现的问题列表
        error_count: 错误数量
        warning_count: 警告数量
        info_count: 提示数量
        status: 检查状态（success/failed/skipped）
        error_message: 如果检查失败，记录错误信息
    """
    file_path: str = Field(..., description="文件路径")
    check_time: str = Field(..., description="检查时间")
    issues: List[Issue] = Field(default_factory=list, description="问题列表")
    error_count: int = Field(default=0, ge=0, description="错误数量")
    warning_count: int = Field(default=0, ge=0, description="警告数量")
    info_count: int = Field(default=0, ge=0, description="提示数量")
    status: str = Field(..., description="检查状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")

    def get_total_issues(self) -> int:
        """获取问题总数"""
        return len(self.issues)

    def has_errors(self) -> bool:
        """是否有错误"""
        return self.error_count > 0


class BatchCheckResult(BaseModel):
    """
    批量检查结果

    Attributes:
        check_id: 检查任务唯一标识符
        start_time: 检查开始时间
        end_time: 检查结束时间
        total_files: 总文件数
        checked_files: 已检查文件数
        total_issues: 总问题数
        total_errors: 总错误数
        total_warnings: 总警告数
        total_infos: 总提示数
        file_results: 各文件的检查结果
    """
    check_id: str = Field(..., description="检查任务ID")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    total_files: int = Field(..., ge=0, description="总文件数")
    checked_files: int = Field(..., ge=0, description="已检查文件数")
    total_issues: int = Field(default=0, ge=0, description="总问题数")
    total_errors: int = Field(default=0, ge=0, description="总错误数")
    total_warnings: int = Field(default=0, ge=0, description="总警告数")
    total_infos: int = Field(default=0, ge=0, description="总提示数")
    file_results: List[FileCheckResult] = Field(
        default_factory=list, description="文件检查结果列表"
    )

    def get_duration_seconds(self) -> float:
        """计算检查耗时（秒）"""
        try:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        except Exception:
            return 0.0

    def get_completion_rate(self) -> float:
        """获取完成率（百分比）"""
        if self.total_files == 0:
            return 0.0
        return (self.checked_files / self.total_files) * 100


class CheckState(BaseModel):
    """
    检查状态（用于持久化和中断恢复）

    Attributes:
        check_id: 检查任务ID
        start_time: 开始时间
        config: 检查配置（如过滤条件、并发数等）
        total_files: 所有待检查文件列表
        completed_files: 已完成检查的文件列表
        remaining_files: 剩余待检查文件列表
        status: 检查状态（running/completed/interrupted/failed）
        report_dir: 报告目录路径
        file_results_dir: 文件结果保存目录（用于持久化检查结果）
    """
    check_id: str = Field(..., description="检查任务ID")
    start_time: str = Field(..., description="开始时间")
    config: Dict[str, Any] = Field(default_factory=dict, description="检查配置")
    total_files: List[str] = Field(default_factory=list, description="总文件列表")
    completed_files: List[str] = Field(default_factory=list, description="已完成文件")
    remaining_files: List[str] = Field(default_factory=list, description="剩余文件")
    status: str = Field(default="running", description="检查状态")
    report_dir: Optional[str] = Field(default=None, description="报告目录路径")
    file_results_dir: Optional[str] = Field(default=None, description="文件结果保存目录")

    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        total = len(self.total_files)
        if total == 0:
            return 0.0
        completed = len(self.completed_files)
        return (completed / total) * 100


class CodeChunk(BaseModel):
    """
    代码分块（用于处理大文件）

    Attributes:
        content: 代码内容（带行号）
        start_line: 起始行号
        end_line: 结束行号
        chunk_index: 分块索引（从0开始）
        file_path: 所属文件路径
    """
    content: str = Field(..., description="代码内容")
    start_line: int = Field(..., ge=1, description="起始行号")
    end_line: int = Field(..., ge=1, description="结束行号")
    chunk_index: int = Field(..., ge=0, description="分块索引")
    file_path: Optional[str] = Field(default=None, description="文件路径")

    def get_line_count(self) -> int:
        """获取代码行数"""
        return self.end_line - self.start_line + 1


class FileFilters(BaseModel):
    """
    文件过滤条件

    Attributes:
        extensions: 文件扩展名列表（如 [".py", ".js"]）
        ignored: 忽略的文件或目录模式（支持glob模式）
        include_patterns: 包含的文件模式
        exclude_patterns: 排除的文件模式
    """
    extensions: Optional[List[str]] = Field(
        default=None, description="文件扩展名列表"
    )
    ignored: Optional[List[str]] = Field(
        default=None, description="忽略的文件/目录模式"
    )
    include_patterns: Optional[List[str]] = Field(
        default=None, description="包含的文件模式"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None, description="排除的文件模式"
    )

    def should_ignore(self, path: str) -> bool:
        """判断路径是否应该被忽略"""
        if not self.ignored:
            return False

        import fnmatch
        for pattern in self.ignored:
            if fnmatch.fnmatch(path, pattern) or pattern in path:
                return True
        return False

    def matches_extension(self, path: str) -> bool:
        """判断文件扩展名是否匹配"""
        if not self.extensions:
            return True

        import os
        _, ext = os.path.splitext(path)
        return ext in self.extensions
