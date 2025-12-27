from typing import Optional
from pathlib import Path
from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import (
    BaseToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import (
    ToolResult,
    LoadExtraDocumentTool,
)
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_tools.extra_docs import (
    _skill,
    _workflow_subagents,
)
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class LoadExtraDocumentToolResolver(BaseToolResolver):
    """加载内置额外文档（以 prompt 字符串形式返回）

    当前支持的文档：
    - workflow_subagents: Subagent Workflow YAML 规范与指导
    - skill: Skill 规范，教 AI 如何完成特定任务的说明书
    """

    def __init__(
        self,
        agent: Optional["AgenticEdit"],
        tool: LoadExtraDocumentTool,
        args: AutoCoderArgs,
    ):
        super().__init__(agent, tool, args)
        self.tool: LoadExtraDocumentTool = tool

    def _read_text_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(f"Document not found: {path}")

    def resolve(self) -> ToolResult:
        try:
            name = self.tool.name.strip()
            # 按名称选择对应的 prompt 函数，并返回其 prompt 文本（非模型推理输出）
            if name == "workflow_subagents":
                prompt_text = _workflow_subagents.prompt()
            elif name == "skill":
                prompt_text = _skill.prompt()
            else:
                # 正常不会进入此分支，_get_doc_text_by_name 已抛错
                raise ValueError(f"Unsupported document name: {name}")

            return ToolResult(
                success=True,
                message=f"Loaded extra document: {name}",
                content=prompt_text,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"LoadExtraDocument failed: {str(e)}",
                content=None,
            )
