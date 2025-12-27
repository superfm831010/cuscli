"""
Workflow Agents - 子代理编排系统

提供基于 YAML 配置的多子代理编排功能，支持：
- DAG 拓扑顺序执行
- 条件判断（正则/JSONPath/文本）
- 输出映射与跨步骤数据传递
- 会话共享策略
- 基于 SdkRunner/TerminalRunner 的代理执行
"""

from autocoder.workflow_agents.types import (
    WorkflowSpec,
    GlobalsConfig,
    ConversationConfig,
    AttemptConfig,
    AgentSpec,
    StepSpec,
    WhenConfig,
    TextCondition,
    OutputConfig,
    StepResult,
    StepStatus,
    WorkflowResult,
)
from autocoder.workflow_agents.agent import WorkflowSubAgent
from autocoder.workflow_agents.executor import SubagentWorkflowExecutor
from autocoder.workflow_agents.loader import load_workflow_from_yaml
from autocoder.workflow_agents.runner import (
    run_workflow_from_yaml,
    print_workflow_result,
    list_available_workflows,
)
from autocoder.workflow_agents.workflow_manager import WorkflowManager
from autocoder.workflow_agents.exceptions import (
    WorkflowError,
    WorkflowValidationError,
    WorkflowFileNotFoundError,
    WorkflowParseError,
    WorkflowStepError,
    WorkflowDependencyError,
    WorkflowAgentNotFoundError,
    WorkflowTemplateError,
    WorkflowAgentDefinitionError,
    WorkflowConversationError,
    WorkflowConditionError,
    WorkflowOutputExtractionError,
    WorkflowAgentResolutionError,
    WorkflowModelValidationError,
)

__all__ = [
    # 类型定义
    "WorkflowSpec",
    "GlobalsConfig",
    "ConversationConfig",
    "AttemptConfig",
    "AgentSpec",
    "StepSpec",
    "WhenConfig",
    "TextCondition",
    "OutputConfig",
    "StepResult",
    "StepStatus",
    "WorkflowResult",
    # 核心类
    "WorkflowSubAgent",
    "SubagentWorkflowExecutor",
    "WorkflowManager",
    # 加载器和运行器
    "load_workflow_from_yaml",
    "run_workflow_from_yaml",
    "print_workflow_result",
    "list_available_workflows",
    # 异常类
    "WorkflowError",
    "WorkflowValidationError",
    "WorkflowFileNotFoundError",
    "WorkflowParseError",
    "WorkflowStepError",
    "WorkflowDependencyError",
    "WorkflowAgentNotFoundError",
    "WorkflowTemplateError",
    "WorkflowAgentDefinitionError",
    "WorkflowConversationError",
    "WorkflowConditionError",
    "WorkflowOutputExtractionError",
    "WorkflowAgentResolutionError",
    "WorkflowModelValidationError",
]
