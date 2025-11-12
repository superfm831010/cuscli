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
    max_turns: int = 6
    retries: int = 2
    timeout_sec: int = 300
    include_rules: bool = False


@dataclass
class ConversationConfig:
    """会话共享策略配置"""

    # start 和 default_action 保留向后兼容
    start: str = "current"  # current | new（向后兼容，当前实现中不强制使用）
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
    retry: Optional[int] = None
    timeout_sec: Optional[int] = None


@dataclass
class RegexCondition:
    """正则条件配置"""

    input: str
    pattern: str
    flags: Optional[str] = None
    group: Optional[int] = None


@dataclass
class JsonPathCondition:
    """JSONPath 条件配置"""

    input: str
    path: str
    exists: Optional[bool] = None
    equals: Optional[Any] = None
    contains: Optional[str] = None


@dataclass
class WhenConfig:
    """条件判断配置"""

    regex: Optional[RegexCondition] = None
    jsonpath: Optional[JsonPathCondition] = None


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
