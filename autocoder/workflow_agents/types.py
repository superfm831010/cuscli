"""
Workflow Agents 类型定义

定义 Subagent Workflow 系统中使用的数据类型和结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


@dataclass
class GlobalsConfig:
    """全局配置"""

    model: str = "v3_chat"
    product_mode: str = "lite"


@dataclass
class ConversationConfig:
    """会话共享策略配置"""

    default_action: str = "resume"  # resume | new | continue


@dataclass
class AttemptConfig:
    """AttemptCompletion 返回契约配置"""

    format: str = "json"  # json | text
    jsonpaths: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentSpec:
    """代理规格配置"""

    id: str
    path: str
    runner: str = "sdk"  # sdk | terminal
    model: Optional[str] = None


@dataclass
class RegexCondition:
    """正则条件配置"""

    input: str
    pattern: str
    flags: Optional[str] = None


@dataclass
class JsonPathCondition:
    """JSONPath 条件配置"""

    input: str
    path: str
    exists: Optional[bool] = None
    equals: Optional[Any] = None
    contains: Optional[str] = None


@dataclass
class TextCondition:
    """
    文本条件配置

    支持多种文本匹配方式：
    - contains: 包含指定字符串
    - not_contains: 不包含指定字符串
    - starts_with: 以指定字符串开头
    - ends_with: 以指定字符串结尾
    - equals: 完全相等
    - not_equals: 不相等
    - is_empty: 是否为空
    - matches: 正则表达式匹配
    - ignore_case: 是否忽略大小写（适用于 contains/starts_with/ends_with/equals）
    """

    input: str  # 输入模板，支持 ${...} 语法
    contains: Optional[str] = None
    not_contains: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    equals: Optional[str] = None
    not_equals: Optional[str] = None
    is_empty: Optional[bool] = None  # True: 检查为空, False: 检查非空
    matches: Optional[str] = None  # 正则表达式
    ignore_case: bool = False  # 是否忽略大小写


@dataclass
class WhenConfig:
    """条件判断配置"""

    regex: Optional[RegexCondition] = None
    jsonpath: Optional[JsonPathCondition] = None
    text: Optional[TextCondition] = None


@dataclass
class OutputConfig:
    """输出映射配置"""

    jsonpath: Optional[str] = None
    regex: Optional[str] = None
    regex_group: Optional[int] = None
    template: Optional[str] = None  # 模板字符串，如 "${attempt_result}"


@dataclass
class StepConversationConfig:
    """步骤级会话配置"""

    action: str = "resume"
    conversation_id: Optional[str] = None


@dataclass
class MergeConfig:
    """
    合并配置

    用于配置多副本执行时的结果合并行为。

    Attributes:
        when: 参与合并的条件（复用 WhenConfig）。
              只有满足条件的副本结果才会参与最终合并。
              条件中不需要指定 input，默认使用当前副本的 attempt_result。
    """

    when: Optional["WhenConfig"] = None


@dataclass
class StepSpec:
    """步骤规格配置"""

    id: str
    agent: str
    needs: List[str] = field(default_factory=list)
    with_args: Dict[str, Any] = field(default_factory=dict)
    when: Optional[WhenConfig] = None
    outputs: Dict[str, OutputConfig] = field(default_factory=dict)
    conversation: Optional[StepConversationConfig] = None
    replicas: int = 1  # 并行副本数，默认为1（不并行）
    merge: Optional[MergeConfig] = None  # 合并配置（用于多副本场景）


@dataclass
class MetadataConfig:
    """元数据配置"""

    name: str
    description: str = ""


@dataclass
class WorkflowSpec:
    """Workflow 总规格"""

    apiVersion: str
    kind: str
    metadata: MetadataConfig
    spec: "SpecConfig"


@dataclass
class SpecConfig:
    """Spec 配置"""

    globals: GlobalsConfig
    vars: Dict[str, Any] = field(default_factory=dict)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    attempt: AttemptConfig = field(default_factory=AttemptConfig)
    agents: List[AgentSpec] = field(default_factory=list)
    steps: List[StepSpec] = field(default_factory=list)


# 执行结果相关类型


class StepStatus(str, Enum):
    """步骤执行状态"""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class StepResult:
    """步骤执行结果"""

    step_id: str
    status: StepStatus
    attempt_result: Optional[str] = None
    error: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """工作流执行结果"""

    success: bool
    context: Dict[str, Any]
    step_results: List[StepResult]
    error: Optional[str] = None
