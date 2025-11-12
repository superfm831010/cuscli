"""
Workflow YAML 加载器

负责从 YAML 文件加载 workflow 配置并转换为 Python 数据结构。
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger

from autocoder.workflow_agents.types import (
    WorkflowSpec,
    MetadataConfig,
    SpecConfig,
    GlobalsConfig,
    ConversationConfig,
    AttemptConfig,
    AgentSpec,
    StepSpec,
    WhenConfig,
    RegexCondition,
    JsonPathCondition,
    OutputConfig,
    StepConversationConfig,
)
from autocoder.workflow_agents.exceptions import (
    WorkflowFileNotFoundError,
    WorkflowParseError,
    WorkflowValidationError,
)


def load_workflow_from_yaml(yaml_path: str) -> WorkflowSpec:
    """
    从 YAML 文件加载 workflow 配置

    Args:
        yaml_path: YAML 文件路径

    Returns:
        WorkflowSpec 对象

    Raises:
        WorkflowFileNotFoundError: 如果文件不存在
        WorkflowParseError: 如果 YAML 解析失败
        WorkflowValidationError: 如果配置格式不正确
    """
    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        raise WorkflowFileNotFoundError(
            workflow_name=yaml_path, searched_paths=[str(yaml_file.absolute())]
        )

    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        # 尝试提取行号
        line_number = None
        if hasattr(e, "problem_mark") and e.problem_mark:
            line_number = e.problem_mark.line + 1  # YAML 行号从0开始

        raise WorkflowParseError(
            yaml_path=str(yaml_file), parse_error=e, line_number=line_number
        )
    except Exception as e:
        raise WorkflowParseError(yaml_path=str(yaml_file), parse_error=e)

    if data is None:
        raise WorkflowValidationError(
            message="YAML 文件为空或仅包含注释",
            suggestion="请确保 YAML 文件包含有效的 workflow 配置",
        )

    return parse_workflow_spec(data, yaml_path=str(yaml_file))


def parse_workflow_spec(data: Dict[str, Any], yaml_path: str = None) -> WorkflowSpec:
    """
    解析 YAML 数据为 WorkflowSpec

    Args:
        data: YAML 解析后的字典
        yaml_path: YAML 文件路径（可选，用于错误提示）

    Returns:
        WorkflowSpec 对象

    Raises:
        WorkflowValidationError: 如果配置格式不正确
    """
    # 验证顶层必需字段
    _validate_required_field(data, "apiVersion", "workflow 配置", yaml_path)
    _validate_required_field(data, "kind", "workflow 配置", yaml_path)
    _validate_required_field(data, "spec", "workflow 配置", yaml_path)

    # 验证顶层字段值
    api_version = data["apiVersion"]
    if api_version != "autocoder/v1":
        raise WorkflowValidationError(
            message=f"不支持的 apiVersion",
            field_path="apiVersion",
            expected="autocoder/v1",
            actual=api_version,
            suggestion="请将 apiVersion 修改为 'autocoder/v1'",
        )

    kind = data["kind"]
    if kind != "SubagentWorkflow":
        raise WorkflowValidationError(
            message=f"不支持的 kind",
            field_path="kind",
            expected="SubagentWorkflow",
            actual=kind,
            suggestion="请将 kind 修改为 'SubagentWorkflow'",
        )

    # 解析 metadata
    metadata_data = data.get("metadata", {})

    # 验证 metadata.name
    workflow_name = metadata_data.get("name")
    if not workflow_name or not workflow_name.strip():
        raise WorkflowValidationError(
            message="metadata.name 不能为空",
            field_path="metadata.name",
            expected="非空字符串",
            actual=str(workflow_name),
            suggestion="请设置一个有意义的 workflow 名称，如 'my-workflow'",
        )

    metadata = MetadataConfig(
        name=workflow_name,
        description=metadata_data.get("description", ""),
    )

    # 解析 spec
    spec_data = data.get("spec", {})
    if not isinstance(spec_data, dict):
        raise WorkflowValidationError(
            message="spec 必须是一个字典对象",
            field_path="spec",
            expected="字典对象",
            actual=str(type(spec_data).__name__),
            suggestion="请确保 spec: 后面跟的是字典格式的配置",
        )

    spec = parse_spec_config(spec_data, yaml_path=yaml_path)

    return WorkflowSpec(
        apiVersion=data["apiVersion"],
        kind=data["kind"],
        metadata=metadata,
        spec=spec,
    )


def parse_spec_config(data: Dict[str, Any], yaml_path: str = None) -> SpecConfig:
    """
    解析 spec 配置

    Args:
        data: spec 字典
        yaml_path: YAML 文件路径（可选，用于错误提示）

    Returns:
        SpecConfig 对象

    Raises:
        WorkflowValidationError: 如果配置格式不正确
    """
    # 解析 globals
    globals_data = data.get("globals", {})
    globals_config = _parse_globals_config(globals_data)

    # 解析 vars
    vars_data = data.get("vars", {})
    if not isinstance(vars_data, dict):
        raise WorkflowValidationError(
            message="spec.vars 必须是字典对象",
            field_path="spec.vars",
            expected="字典对象",
            actual=str(type(vars_data).__name__),
            suggestion="将 vars 定义为键值对，如: vars:\\n  project_type: '*'",
        )

    # 解析 conversation
    conv_data = data.get("conversation", {})
    conversation_config = _parse_conversation_config(conv_data)

    # 解析 attempt
    attempt_data = data.get("attempt", {})
    attempt_config = _parse_attempt_config(attempt_data)

    # 解析 agents
    agents_data = data.get("agents", [])
    if not isinstance(agents_data, list):
        raise WorkflowValidationError(
            message="spec.agents 必须是列表",
            field_path="spec.agents",
            expected="列表（数组）",
            actual=str(type(agents_data).__name__),
            suggestion="确保 agents: 后面跟的是列表格式，每项以 - 开头",
        )

    if not agents_data:
        raise WorkflowValidationError(
            message="spec.agents 不能为空",
            field_path="spec.agents",
            expected="至少一个 agent 定义",
            actual="空列表",
            suggestion="请定义至少一个 agent，例如:\\n  - id: context\\n    path: context.md",
        )

    agents = [
        parse_agent_spec(agent_data, i) for i, agent_data in enumerate(agents_data)
    ]

    # 验证 agent ID 唯一性
    agent_ids = [a.id for a in agents]
    duplicates = [aid for aid in agent_ids if agent_ids.count(aid) > 1]
    if duplicates:
        raise WorkflowValidationError(
            message=f"发现重复的 agent ID: {', '.join(set(duplicates))}",
            field_path="spec.agents",
            suggestion="每个 agent 的 id 必须唯一，请修改重复的 ID",
        )

    # 解析 steps
    steps_data = data.get("steps", [])
    if not isinstance(steps_data, list):
        raise WorkflowValidationError(
            message="spec.steps 必须是列表",
            field_path="spec.steps",
            expected="列表（数组）",
            actual=str(type(steps_data).__name__),
            suggestion="确保 steps: 后面跟的是列表格式，每项以 - 开头",
        )

    if not steps_data:
        raise WorkflowValidationError(
            message="spec.steps 不能为空",
            field_path="spec.steps",
            expected="至少一个 step 定义",
            actual="空列表",
            suggestion="请定义至少一个 step，例如:\\n  - id: step1\\n    agent: context",
        )

    steps = [
        parse_step_spec(step_data, i, agent_ids)
        for i, step_data in enumerate(steps_data)
    ]

    # 验证 step ID 唯一性
    step_ids = [s.id for s in steps]
    duplicates = [sid for sid in step_ids if step_ids.count(sid) > 1]
    if duplicates:
        raise WorkflowValidationError(
            message=f"发现重复的 step ID: {', '.join(set(duplicates))}",
            field_path="spec.steps",
            suggestion="每个 step 的 id 必须唯一，请修改重复的 ID",
        )

    return SpecConfig(
        globals=globals_config,
        vars=vars_data,
        conversation=conversation_config,
        attempt=attempt_config,
        agents=agents,
        steps=steps,
    )


def parse_agent_spec(data: Dict[str, Any], index: int = None) -> AgentSpec:
    """
    解析 agent 配置

    Args:
        data: agent 字典
        index: agent 在列表中的索引（用于错误提示）

    Returns:
        AgentSpec 对象

    Raises:
        WorkflowValidationError: 如果缺少必需字段或格式不正确
    """
    context = f"spec.agents[{index}]" if index is not None else "agent 配置"

    _validate_required_field(data, "id", context)
    _validate_required_field(data, "path", context)

    # 验证 runner 类型
    runner = data.get("runner", "sdk")
    if runner not in ["sdk", "terminal"]:
        raise WorkflowValidationError(
            message=f"agent runner 类型无效",
            field_path=f"{context}.runner",
            expected="'sdk' 或 'terminal'",
            actual=f"'{runner}'",
            suggestion=f"请将 agent '{data['id']}' 的 runner 修改为 'sdk' 或 'terminal'",
        )

    return AgentSpec(
        id=data["id"],
        path=data["path"],
        runner=runner,
        model=data.get("model"),
        retry=data.get("retry"),
        timeout_sec=data.get("timeout_sec"),
    )


def parse_step_spec(
    data: Dict[str, Any], index: int = None, available_agent_ids: list = None
) -> StepSpec:
    """
    解析 step 配置

    Args:
        data: step 字典
        index: step 在列表中的索引（用于错误提示）
        available_agent_ids: 可用的 agent ID 列表（用于验证）

    Returns:
        StepSpec 对象

    Raises:
        WorkflowValidationError: 如果缺少必需字段或格式不正确
    """
    context = f"spec.steps[{index}]" if index is not None else "step 配置"

    _validate_required_field(data, "id", context)
    _validate_required_field(data, "agent", context)

    step_id = data["id"]
    agent_id = data["agent"]

    # 验证 agent 引用是否存在
    if available_agent_ids and agent_id not in available_agent_ids:
        raise WorkflowValidationError(
            message=f"步骤引用的 agent 不存在: '{agent_id}'",
            field_path=f"{context}.agent",
            expected=f"以下之一: {', '.join(available_agent_ids)}",
            actual=f"'{agent_id}'",
            suggestion=f"请将 agent 修改为已定义的 agent ID，或在 spec.agents 中添加 '{agent_id}' 的定义",
        )

    # 验证 needs 字段
    needs = data.get("needs", [])
    if not isinstance(needs, list):
        raise WorkflowValidationError(
            message="needs 必须是列表",
            field_path=f"{context}.needs",
            expected="列表（数组）",
            actual=str(type(needs).__name__),
            suggestion="将 needs 定义为列表，如: needs: [step1, step2]",
        )

    # 解析 when
    when_data = data.get("when")
    when_config = parse_when_config(when_data, f"{context}.when") if when_data else None

    # 解析 outputs
    outputs_data = data.get("outputs", {})
    if not isinstance(outputs_data, dict):
        raise WorkflowValidationError(
            message="outputs 必须是字典对象",
            field_path=f"{context}.outputs",
            expected="字典对象",
            actual=str(type(outputs_data).__name__),
            suggestion="将 outputs 定义为键值对",
        )
    outputs = {
        key: parse_output_config(value, f"{context}.outputs.{key}")
        for key, value in outputs_data.items()
    }

    # 解析 conversation
    conv_data = data.get("conversation")
    conversation = (
        parse_step_conversation_config(conv_data, context) if conv_data else None
    )

    # 解析 replicas
    replicas = data.get("replicas", 1)
    if not isinstance(replicas, int) or replicas < 1:
        raise WorkflowValidationError(
            message="replicas 必须是正整数",
            field_path=f"{context}.replicas",
            expected="正整数（>= 1）",
            actual=str(replicas),
            suggestion="将 replicas 设置为正整数，如 2（表示并行运行2个副本）",
        )

    return StepSpec(
        id=step_id,
        agent=agent_id,
        needs=needs,
        with_args=data.get("with", {}),
        when=when_config,
        outputs=outputs,
        conversation=conversation,
        replicas=replicas,
    )


def parse_when_config(data: Dict[str, Any], context: str = "when 配置") -> WhenConfig:
    """
    解析 when 条件配置

    Args:
        data: when 字典
        context: 上下文描述（用于错误提示）

    Returns:
        WhenConfig 对象

    Raises:
        WorkflowValidationError: 如果条件配置格式不正确
    """
    regex_config = None
    jsonpath_config = None

    if "regex" in data:
        regex_data = data["regex"]
        if not isinstance(regex_data, dict):
            raise WorkflowValidationError(
                message="regex 条件必须是字典对象",
                field_path=f"{context}.regex",
                expected="字典对象",
                actual=str(type(regex_data).__name__),
                suggestion="请使用字典格式定义 regex 条件",
            )

        # 验证必需字段
        if "pattern" not in regex_data or not regex_data["pattern"]:
            raise WorkflowValidationError(
                message="regex 条件缺少 pattern 字段",
                field_path=f"{context}.regex.pattern",
                expected="非空正则表达式",
                actual=str(regex_data.get("pattern")),
                suggestion="请提供有效的正则表达式 pattern",
            )

        regex_config = RegexCondition(
            input=regex_data.get("input", ""),
            pattern=regex_data["pattern"],
            flags=regex_data.get("flags"),
            group=regex_data.get("group"),
        )

    if "jsonpath" in data:
        jsonpath_data = data["jsonpath"]
        if not isinstance(jsonpath_data, dict):
            raise WorkflowValidationError(
                message="jsonpath 条件必须是字典对象",
                field_path=f"{context}.jsonpath",
                expected="字典对象",
                actual=str(type(jsonpath_data).__name__),
                suggestion="请使用字典格式定义 jsonpath 条件",
            )

        # 验证必需字段
        if "path" not in jsonpath_data or not jsonpath_data["path"]:
            raise WorkflowValidationError(
                message="jsonpath 条件缺少 path 字段",
                field_path=f"{context}.jsonpath.path",
                expected="非空 JSONPath 表达式",
                actual=str(jsonpath_data.get("path")),
                suggestion="请提供有效的 JSONPath 表达式，如 '$.files'",
            )

        jsonpath_config = JsonPathCondition(
            input=jsonpath_data.get("input", ""),
            path=jsonpath_data["path"],
            exists=jsonpath_data.get("exists"),
            equals=jsonpath_data.get("equals"),
            contains=jsonpath_data.get("contains"),
        )

    return WhenConfig(regex=regex_config, jsonpath=jsonpath_config)


def parse_output_config(value: Any, context: str = "output 配置") -> OutputConfig:
    """
    解析 output 配置

    Args:
        value: output 值（可能是字符串或字典）
        context: 上下文描述（用于错误提示）

    Returns:
        OutputConfig 对象

    Raises:
        WorkflowValidationError: 如果配置格式不正确
    """
    if isinstance(value, str):
        # 直接字符串，如 "${attempt_result}"
        # 保存到 template 字段，以便后续渲染
        return OutputConfig(template=value)

    if isinstance(value, dict):
        # 验证至少有一种提取方法
        has_jsonpath = "jsonpath" in value and value["jsonpath"]
        has_regex = "regex" in value and value["regex"]
        has_template = "template" in value and value["template"]

        if not (has_jsonpath or has_regex or has_template):
            raise WorkflowValidationError(
                message="output 配置必须指定至少一种提取方法",
                field_path=context,
                expected="jsonpath, regex 或 template 之一",
                actual="无有效提取方法",
                suggestion="请添加 jsonpath, regex 或直接使用字符串模板",
            )

        return OutputConfig(
            jsonpath=value.get("jsonpath"),
            regex=value.get("regex"),
            regex_group=value.get("group"),
            template=value.get("template"),
        )

    raise WorkflowValidationError(
        message="output 配置格式不正确",
        field_path=context,
        expected="字符串或字典对象",
        actual=str(type(value).__name__),
        suggestion="使用字符串（如 '${attempt_result}'）或字典（如 {jsonpath: '$.files'}）",
    )


def parse_step_conversation_config(
    data: Dict[str, Any], context: str = "conversation 配置"
) -> StepConversationConfig:
    """
    解析 step 级别的 conversation 配置

    Args:
        data: conversation 字典
        context: 上下文描述（用于错误提示）

    Returns:
        StepConversationConfig 对象

    Raises:
        WorkflowValidationError: 如果配置格式不正确
    """
    action = data.get("action", "resume")

    # 验证 action 值
    valid_actions = ["new", "resume", "continue"]
    if action not in valid_actions:
        raise WorkflowValidationError(
            message=f"无效的 conversation action",
            field_path=f"{context}.conversation.action",
            expected=f"以下之一: {', '.join(valid_actions)}",
            actual=f"'{action}'",
            suggestion=f"请将 action 修改为 {', '.join(valid_actions)} 之一",
        )

    return StepConversationConfig(
        action=action,
        conversation_id=data.get("conversation_id"),
    )


def _validate_required_field(
    data: Dict[str, Any], field: str, context: str, yaml_path: str = None
) -> None:
    """
    验证必需字段是否存在

    Args:
        data: 数据字典
        field: 字段名
        context: 上下文描述（用于错误消息）
        yaml_path: YAML 文件路径（可选，用于错误提示）

    Raises:
        WorkflowValidationError: 如果字段缺失或为空
    """
    if field not in data:
        raise WorkflowValidationError(
            message=f"缺少必需字段: '{field}'",
            field_path=f"{context}.{field}",
            expected=f"必需字段 '{field}'",
            actual="字段不存在",
            suggestion=f"请在 {context} 中添加 '{field}' 字段",
        )

    value = data[field]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise WorkflowValidationError(
            message=f"字段 '{field}' 不能为空",
            field_path=f"{context}.{field}",
            expected="非空值",
            actual=str(value),
            suggestion=f"请为 '{field}' 提供有效的值",
        )


def _parse_globals_config(data: Dict[str, Any]) -> GlobalsConfig:
    """
    解析 globals 配置并进行类型验证

    Args:
        data: globals 字典

    Returns:
        GlobalsConfig 对象

    Raises:
        WorkflowValidationError: 如果配置类型不正确
    """
    # 验证数值类型字段
    max_turns = data.get("max_turns", 6)
    if not isinstance(max_turns, int) or max_turns < 1:
        raise WorkflowValidationError(
            message="globals.max_turns 必须是正整数",
            field_path="spec.globals.max_turns",
            expected="正整数（>= 1）",
            actual=str(max_turns),
            suggestion="将 max_turns 设置为正整数，如 6",
        )

    retries = data.get("retries", 2)
    if not isinstance(retries, int) or retries < 0:
        raise WorkflowValidationError(
            message="globals.retries 必须是非负整数",
            field_path="spec.globals.retries",
            expected="非负整数（>= 0）",
            actual=str(retries),
            suggestion="将 retries 设置为非负整数，如 2",
        )

    timeout_sec = data.get("timeout_sec", 300)
    if not isinstance(timeout_sec, int) or timeout_sec < 1:
        raise WorkflowValidationError(
            message="globals.timeout_sec 必须是正整数",
            field_path="spec.globals.timeout_sec",
            expected="正整数（>= 1）",
            actual=str(timeout_sec),
            suggestion="将 timeout_sec 设置为正整数（秒），如 300",
        )

    # 验证布尔类型字段
    include_rules = data.get("include_rules", False)
    if not isinstance(include_rules, bool):
        raise WorkflowValidationError(
            message="globals.include_rules 必须是布尔值",
            field_path="spec.globals.include_rules",
            expected="true 或 false",
            actual=str(include_rules),
            suggestion="将 include_rules 设置为 true 或 false",
        )

    return GlobalsConfig(
        model=data.get("model", "v3_chat"),
        product_mode=data.get("product_mode", "lite"),
        max_turns=max_turns,
        retries=retries,
        timeout_sec=timeout_sec,
        include_rules=include_rules,
    )


def _parse_conversation_config(data: Dict[str, Any]) -> ConversationConfig:
    """
    解析 conversation 配置并进行值验证

    Args:
        data: conversation 字典

    Returns:
        ConversationConfig 对象

    Raises:
        WorkflowValidationError: 如果配置值不正确
    """
    start = data.get("start", "current")
    valid_start_values = ["current", "new"]
    if start not in valid_start_values:
        raise WorkflowValidationError(
            message="conversation.start 值无效",
            field_path="spec.conversation.start",
            expected=f"以下之一: {', '.join(valid_start_values)}",
            actual=f"'{start}'",
            suggestion=f"请将 start 修改为 {' 或 '.join(valid_start_values)}",
        )

    default_action = data.get("default_action", "resume")
    valid_actions = ["resume", "new", "continue"]
    if default_action not in valid_actions:
        raise WorkflowValidationError(
            message="conversation.default_action 值无效",
            field_path="spec.conversation.default_action",
            expected=f"以下之一: {', '.join(valid_actions)}",
            actual=f"'{default_action}'",
            suggestion=f"请将 default_action 修改为 {', '.join(valid_actions)} 之一",
        )

    return ConversationConfig(
        start=start,
        default_action=default_action,
    )


def _parse_attempt_config(data: Dict[str, Any]) -> AttemptConfig:
    """
    解析 attempt 配置并进行值验证

    Args:
        data: attempt 字典

    Returns:
        AttemptConfig 对象

    Raises:
        WorkflowValidationError: 如果配置值不正确
    """
    format_type = data.get("format", "json")
    valid_formats = ["json", "text"]
    if format_type not in valid_formats:
        raise WorkflowValidationError(
            message="attempt.format 值无效",
            field_path="spec.attempt.format",
            expected=f"以下之一: {', '.join(valid_formats)}",
            actual=f"'{format_type}'",
            suggestion=f"请将 format 修改为 {' 或 '.join(valid_formats)}",
        )

    jsonpaths = data.get("jsonpaths", {})
    if not isinstance(jsonpaths, dict):
        raise WorkflowValidationError(
            message="attempt.jsonpaths 必须是字典对象",
            field_path="spec.attempt.jsonpaths",
            expected="字典对象",
            actual=str(type(jsonpaths).__name__),
            suggestion="将 jsonpaths 定义为键值对",
        )

    return AttemptConfig(
        format=format_type,
        jsonpaths=jsonpaths,
    )
