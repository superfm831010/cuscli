"""
CLI 选项定义模块

定义命令行接口的选项数据结构。
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..constants import DEFAULT_MODEL
from ..models.responses import CLIResult  # 从 models.responses 导入，避免重复定义
from autocoder.common.international import get_message_with_format, get_message


def get_default_async_workdir() -> str:
    """获取默认的异步运行器工作目录，支持多平台"""
    home_dir = Path.home()
    return str(home_dir / ".auto-coder" / "async_agent")


@dataclass
class CLIOptions:
    """CLI选项数据类，用于配置命令行工具的行为。"""

    # 命令选项
    command: Optional[str] = None  # 子命令名称，如 'config'
    config_args: list = field(default_factory=list)  # config 命令的参数列表

    # 会话选项
    continue_session: bool = False  # 继续最近的对话
    resume_session: Optional[str] = None  # 恢复特定会话的ID

    # 输入选项
    prompt: Optional[str] = None  # 提示内容，如果为None则从stdin读取
    input_format: str = "text"  # 输入格式，可选值: text, json, stream-json

    # 输出选项
    output_format: str = "text"  # 输出格式，可选值: text, json, stream-json
    verbose: bool = False  # 是否输出详细信息

    # 高级选项
    max_turns: int = 10000  # 最大对话轮数
    system_prompt: Optional[str] = None  # 系统提示
    system_prompt_path: Optional[str] = None  # 系统提示文件路径
    allowed_tools: list = field(default_factory=list)  # 允许使用的工具列表
    permission_mode: str = "manual"  # 权限模式，可选值: manual, acceptEdits
    model: Optional[str] = None  # 模型名称，如 gpt-4, gpt-3.5-turbo 等
    include_rules: bool = False  # 是否包含规则文件
    pr: bool = False  # 是否创建 PR
    is_sub_agent: bool = False  # 是否为子代理模式，避免conversation冲突
    loop: int = 1  # 循环执行次数，默认为1
    loop_keep_conversation: bool = False  # 循环时是否保持对话连续性
    loop_additional_prompt: Optional[str] = None  # 循环时的额外提示，可自定义
    include_libs: list = field(
        default_factory=list
    )  # 要包含的LLM friendly packages列表

    # Workflow 选项
    workflow: Optional[str] = None  # workflow 名称或文件路径（仅非 async 模式支持）

    # Async Agent Runner 选项
    async_mode: bool = False  # 是否启用异步代理运行器模式
    split_mode: str = "h1"  # 分割模式: h1, h2, h3, any, delimiter
    delimiter: str = "==="  # 自定义分隔符（当 split_mode=delimiter 时使用）
    min_level: int = 1  # 最小标题级别（当 split_mode=any 时使用）
    max_level: int = 3  # 最大标题级别（当 split_mode=any 时使用）
    workdir: str = field(default_factory=get_default_async_workdir)  # 工作目录
    from_branch: str = ""  # 基础分支（为空时自动检测）
    bg_mode: bool = False  # 后台运行模式
    task_prefix: str = ""  # 任务名称前缀（异步模式下使用）
    worktree_name: Optional[str] = None  # 指定的 worktree 名称（为空时自动生成）

    def validate(self) -> None:
        """验证选项的有效性。"""
        # 验证输出格式
        valid_formats = ["text", "json", "stream-json"]
        if self.output_format not in valid_formats:
            raise ValueError(
                get_message_with_format(
                    "invalid_output_format",
                    format=self.output_format,
                    valid_formats=", ".join(valid_formats),
                )
            )

        # stream-json 格式建议开启verbose以获得实时输出
        # 但不强制要求，JSON格式可以在非verbose模式下正常工作

        # 验证输入格式
        if self.input_format not in valid_formats:
            raise ValueError(
                get_message_with_format(
                    "invalid_input_format",
                    format=self.input_format,
                    valid_formats=", ".join(valid_formats),
                )
            )

        # 验证权限模式
        valid_permission_modes = ["manual", "acceptEdits"]
        if self.permission_mode not in valid_permission_modes:
            raise ValueError(
                get_message_with_format(
                    "invalid_permission_mode",
                    mode=self.permission_mode,
                    valid_modes=", ".join(valid_permission_modes),
                )
            )

        # 验证会话选项的互斥性
        if self.continue_session and self.resume_session:
            raise ValueError(get_message_with_format("session_options_conflict"))

        # 验证 system_prompt 和 system_prompt_path 的互斥性
        if self.system_prompt and self.system_prompt_path:
            raise ValueError(
                "只能配置 --system-prompt 或 --system-prompt-path 中的一个，不能同时配置两个"
            )

        # 验证异步模式相关参数
        if self.async_mode:
            # 验证分割模式
            valid_split_modes = ["h1", "h2", "h3", "any", "delimiter"]
            if self.split_mode not in valid_split_modes:
                raise ValueError(
                    get_message_with_format(
                        "invalid_split_mode",
                        mode=self.split_mode,
                        valid_modes=", ".join(valid_split_modes),
                    )
                )

            # 验证标题级别范围
            if self.split_mode == "any":
                if self.min_level < 1 or self.max_level < 1:
                    raise ValueError(get_message("heading_level_must_be_positive"))
                if self.min_level > self.max_level:
                    raise ValueError(get_message("min_level_cannot_exceed_max"))

            # 验证分隔符
            if self.split_mode == "delimiter" and not self.delimiter.strip():
                raise ValueError(get_message("delimiter_required_for_delimiter_mode"))

        # 验证 workflow 选项
        if self.workflow:
            # workflow 仅支持 text 输出格式
            if self.output_format != "text":
                raise ValueError("--workflow 仅支持 --output-format text")

        # 自动选择模型或验证指定的模型（config 命令时跳过）
        # 在 workflow 模式下跳过模型自动选择与校验，允许使用 YAML 中的模型配置
        if self.command != "config" and not self.workflow:
            if not self.model or not self.model.strip():
                self.model = self._auto_select_model()
                if not self.model:
                    raise ValueError(
                        get_message_with_format("model_auto_select_failed")
                    )

    def _auto_select_model(self) -> Optional[str]:
        """自动选择第一个设置了API key的模型"""
        try:
            from autocoder.common.llms import LLMManager

            manager = LLMManager()
            all_models = manager.get_all_models()

            # 遍历所有模型，找到第一个有API key的模型
            for model_name, model in all_models.items():
                if manager.has_key(model_name):
                    return model_name

            return None
        except Exception:
            # 如果导入或初始化失败，返回 None
            return None
