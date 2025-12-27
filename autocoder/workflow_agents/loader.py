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
    TextCondition,
    OutputConfig,
    StepConversationConfig,
    MergeConfig,
)
from autocoder.common.agents import AgentManager
from autocoder.common.international import get_message, get_message_with_format
from autocoder.workflow_agents.exceptions import (
    WorkflowFileNotFoundError,
    WorkflowParseError,
    WorkflowValidationError,
    WorkflowAgentResolutionError,
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
            message=get_message("workflow.yaml_empty"),
            suggestion=get_message("workflow.yaml_empty_suggestion"),
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
            message=get_message("workflow.unsupported_api_version"),
            field_path="apiVersion",
            expected="autocoder/v1",
            actual=api_version,
            suggestion=get_message("workflow.api_version_suggestion"),
        )

    kind = data["kind"]
    if kind != "SubagentWorkflow":
        raise WorkflowValidationError(
            message=get_message("workflow.unsupported_kind"),
            field_path="kind",
            expected="SubagentWorkflow",
            actual=kind,
            suggestion=get_message("workflow.kind_suggestion"),
        )

    # 解析 metadata
    metadata_data = data.get("metadata", {})

    # 验证 metadata.name
    workflow_name = metadata_data.get("name")
    if not workflow_name or not workflow_name.strip():
        raise WorkflowValidationError(
            message=get_message("workflow.metadata_name_empty"),
            field_path="metadata.name",
            expected=get_message("workflow.non_empty_string"),
            actual=str(workflow_name),
            suggestion=get_message("workflow.metadata_name_suggestion"),
        )

    metadata = MetadataConfig(
        name=workflow_name,
        description=metadata_data.get("description", ""),
    )

    # 解析 spec
    spec_data = data.get("spec", {})
    if not isinstance(spec_data, dict):
        raise WorkflowValidationError(
            message=get_message("workflow.spec_must_be_dict"),
            field_path="spec",
            expected=get_message("workflow.dict_object"),
            actual=str(type(spec_data).__name__),
            suggestion=get_message("workflow.spec_dict_suggestion"),
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
            message=get_message("workflow.vars_must_be_dict"),
            field_path="spec.vars",
            expected=get_message("workflow.dict_object"),
            actual=str(type(vars_data).__name__),
            suggestion=get_message("workflow.vars_dict_suggestion"),
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
            message=get_message("workflow.agents_must_be_list"),
            field_path="spec.agents",
            expected=get_message("workflow.list_array"),
            actual=str(type(agents_data).__name__),
            suggestion=get_message("workflow.agents_list_suggestion"),
        )

    if not agents_data:
        raise WorkflowValidationError(
            message=get_message("workflow.agents_empty"),
            field_path="spec.agents",
            expected=get_message("workflow.at_least_one_agent"),
            actual=get_message("workflow.empty_list"),
            suggestion=get_message("workflow.agents_empty_suggestion"),
        )

    agents = [
        parse_agent_spec(agent_data, i) for i, agent_data in enumerate(agents_data)
    ]

    # 验证 agent ID 唯一性
    agent_ids = [a.id for a in agents]
    duplicates = [aid for aid in agent_ids if agent_ids.count(aid) > 1]
    if duplicates:
        raise WorkflowValidationError(
            message=get_message_with_format(
                "workflow.duplicate_agent_ids", ids=", ".join(set(duplicates))
            ),
            field_path="spec.agents",
            suggestion=get_message("workflow.duplicate_agent_ids_suggestion"),
        )

    # 验证 agent 文件存在性（新增✨）
    _validate_agents_existence(agents, yaml_path)

    # 解析 steps
    steps_data = data.get("steps", [])
    if not isinstance(steps_data, list):
        raise WorkflowValidationError(
            message=get_message("workflow.steps_must_be_list"),
            field_path="spec.steps",
            expected=get_message("workflow.list_array"),
            actual=str(type(steps_data).__name__),
            suggestion=get_message("workflow.steps_list_suggestion"),
        )

    if not steps_data:
        raise WorkflowValidationError(
            message=get_message("workflow.steps_empty"),
            field_path="spec.steps",
            expected=get_message("workflow.at_least_one_step"),
            actual=get_message("workflow.empty_list"),
            suggestion=get_message("workflow.steps_empty_suggestion"),
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
            message=get_message_with_format(
                "workflow.duplicate_step_ids", ids=", ".join(set(duplicates))
            ),
            field_path="spec.steps",
            suggestion=get_message("workflow.duplicate_step_ids_suggestion"),
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
            message=get_message("workflow.invalid_runner_type"),
            field_path=f"{context}.runner",
            expected="'sdk' or 'terminal'",
            actual=f"'{runner}'",
            suggestion=get_message("workflow.runner_type_suggestion"),
        )

    return AgentSpec(
        id=data["id"],
        path=data["path"],
        runner=runner,
        model=data.get("model"),
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
            message=get_message_with_format(
                "workflow.step_agent_not_found", agent_id=agent_id
            ),
            field_path=f"{context}.agent",
            expected=f"one of: {', '.join(available_agent_ids)}",
            actual=f"'{agent_id}'",
            suggestion=get_message_with_format(
                "workflow.step_agent_suggestion", agent_id=agent_id
            ),
        )

    # 验证 needs 字段
    needs = data.get("needs", [])
    if not isinstance(needs, list):
        raise WorkflowValidationError(
            message=get_message("workflow.needs_must_be_list"),
            field_path=f"{context}.needs",
            expected=get_message("workflow.list_array"),
            actual=str(type(needs).__name__),
            suggestion=get_message("workflow.needs_list_suggestion"),
        )

    # 解析 when
    when_data = data.get("when")
    when_config = parse_when_config(when_data, f"{context}.when") if when_data else None

    # 解析 outputs
    outputs_data = data.get("outputs", {})
    if not isinstance(outputs_data, dict):
        raise WorkflowValidationError(
            message=get_message("workflow.outputs_must_be_dict"),
            field_path=f"{context}.outputs",
            expected=get_message("workflow.dict_object"),
            actual=str(type(outputs_data).__name__),
            suggestion=get_message("workflow.outputs_dict_suggestion"),
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
            message=get_message("workflow.replicas_must_be_positive"),
            field_path=f"{context}.replicas",
            expected=get_message("workflow.positive_integer"),
            actual=str(replicas),
            suggestion=get_message("workflow.replicas_suggestion"),
        )

    # 解析 merge
    merge_data = data.get("merge")
    merge_config = (
        parse_merge_config(merge_data, f"{context}.merge") if merge_data else None
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
        merge=merge_config,
    )


def parse_merge_config(
    data: Dict[str, Any], context: str = "merge 配置"
) -> MergeConfig:
    """
    解析 merge 配置

    用于多副本执行时的结果合并配置。

    Args:
        data: merge 字典
        context: 上下文描述（用于错误提示）

    Returns:
        MergeConfig 对象

    Raises:
        WorkflowValidationError: 如果配置格式不正确
    """
    if not isinstance(data, dict):
        raise WorkflowValidationError(
            message=get_message("workflow.merge_must_be_dict"),
            field_path=context,
            expected=get_message("workflow.dict_object"),
            actual=str(type(data).__name__),
            suggestion=get_message("workflow.merge_dict_suggestion"),
        )

    when_config = None

    if "when" in data:
        when_data = data["when"]
        if not isinstance(when_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.merge_when_must_be_dict"),
                field_path=f"{context}.when",
                expected=get_message("workflow.dict_object"),
                actual=str(type(when_data).__name__),
                suggestion=get_message("workflow.merge_when_dict_suggestion"),
            )
        # 使用宽松模式解析，input 字段可选（默认使用 attempt_result）
        when_config = parse_when_config_for_merge(when_data, context=f"{context}.when")

    return MergeConfig(when=when_config)


def parse_when_config_for_merge(
    data: Dict[str, Any], context: str = "merge.when 配置"
) -> WhenConfig:
    """
    为 merge.when 解析条件配置（宽松模式）

    与 parse_when_config 的区别：
    - text 条件不要求 input 字段（默认使用 attempt_result）
    - regex 条件不要求 input 字段（默认使用 attempt_result）
    - jsonpath 条件不要求 input 字段（默认使用 attempt_result）

    Args:
        data: when 字典
        context: 上下文描述

    Returns:
        WhenConfig 对象

    Raises:
        WorkflowValidationError: 如果条件配置格式不正确
    """
    regex_config = None
    jsonpath_config = None
    text_config = None

    if "regex" in data:
        regex_data = data["regex"]
        if not isinstance(regex_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.regex_must_be_dict"),
                field_path=f"{context}.regex",
                expected=get_message("workflow.dict_object"),
                actual=str(type(regex_data).__name__),
                suggestion=get_message("workflow.regex_dict_suggestion"),
            )

        # 验证必需字段 pattern
        if "pattern" not in regex_data or not regex_data["pattern"]:
            raise WorkflowValidationError(
                message=get_message("workflow.regex_missing_pattern"),
                field_path=f"{context}.regex.pattern",
                expected=get_message("workflow.non_empty_regex"),
                actual=str(regex_data.get("pattern")),
                suggestion=get_message("workflow.regex_pattern_suggestion"),
            )

        # input 可选，默认为空（评估时使用 attempt_result）
        regex_config = RegexCondition(
            input=regex_data.get("input", ""),
            pattern=regex_data["pattern"],
            flags=regex_data.get("flags"),
        )

    if "jsonpath" in data:
        jsonpath_data = data["jsonpath"]
        if not isinstance(jsonpath_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.jsonpath_must_be_dict"),
                field_path=f"{context}.jsonpath",
                expected=get_message("workflow.dict_object"),
                actual=str(type(jsonpath_data).__name__),
                suggestion=get_message("workflow.jsonpath_dict_suggestion"),
            )

        # 验证必需字段 path
        if "path" not in jsonpath_data or not jsonpath_data["path"]:
            raise WorkflowValidationError(
                message=get_message("workflow.jsonpath_missing_path"),
                field_path=f"{context}.jsonpath.path",
                expected=get_message("workflow.non_empty_jsonpath"),
                actual=str(jsonpath_data.get("path")),
                suggestion=get_message("workflow.jsonpath_path_suggestion"),
            )

        # input 可选，默认为空（评估时使用 attempt_result）
        jsonpath_config = JsonPathCondition(
            input=jsonpath_data.get("input", ""),
            path=jsonpath_data["path"],
            exists=jsonpath_data.get("exists"),
            equals=jsonpath_data.get("equals"),
            contains=jsonpath_data.get("contains"),
        )

    if "text" in data:
        text_data = data["text"]
        if not isinstance(text_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.text_must_be_dict"),
                field_path=f"{context}.text",
                expected=get_message("workflow.dict_object"),
                actual=str(type(text_data).__name__),
                suggestion=get_message("workflow.text_dict_suggestion"),
            )

        # input 可选（与 parse_when_config 的区别）

        # 至少需要一个匹配条件
        match_fields = [
            "contains",
            "not_contains",
            "starts_with",
            "ends_with",
            "equals",
            "not_equals",
            "is_empty",
            "matches",
        ]
        has_match_condition = any(field in text_data for field in match_fields)
        if not has_match_condition:
            raise WorkflowValidationError(
                message=get_message("workflow.text_missing_match_condition"),
                field_path=f"{context}.text",
                expected=f"at least one of: {', '.join(match_fields)}",
                actual=str(list(text_data.keys())),
                suggestion=get_message("workflow.text_match_suggestion"),
            )

        # input 可选，默认为空（评估时使用 attempt_result）
        text_config = TextCondition(
            input=text_data.get("input", ""),
            contains=text_data.get("contains"),
            not_contains=text_data.get("not_contains"),
            starts_with=text_data.get("starts_with"),
            ends_with=text_data.get("ends_with"),
            equals=text_data.get("equals"),
            not_equals=text_data.get("not_equals"),
            is_empty=text_data.get("is_empty"),
            matches=text_data.get("matches"),
            ignore_case=text_data.get("ignore_case", False),
        )

    return WhenConfig(regex=regex_config, jsonpath=jsonpath_config, text=text_config)


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
    text_config = None

    if "regex" in data:
        regex_data = data["regex"]
        if not isinstance(regex_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.regex_must_be_dict"),
                field_path=f"{context}.regex",
                expected=get_message("workflow.dict_object"),
                actual=str(type(regex_data).__name__),
                suggestion=get_message("workflow.regex_dict_suggestion"),
            )

        # 验证必需字段
        if "pattern" not in regex_data or not regex_data["pattern"]:
            raise WorkflowValidationError(
                message=get_message("workflow.regex_missing_pattern"),
                field_path=f"{context}.regex.pattern",
                expected=get_message("workflow.non_empty_regex"),
                actual=str(regex_data.get("pattern")),
                suggestion=get_message("workflow.regex_pattern_suggestion"),
            )

        regex_config = RegexCondition(
            input=regex_data.get("input", ""),
            pattern=regex_data["pattern"],
            flags=regex_data.get("flags"),
        )

    if "jsonpath" in data:
        jsonpath_data = data["jsonpath"]
        if not isinstance(jsonpath_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.jsonpath_must_be_dict"),
                field_path=f"{context}.jsonpath",
                expected=get_message("workflow.dict_object"),
                actual=str(type(jsonpath_data).__name__),
                suggestion=get_message("workflow.jsonpath_dict_suggestion"),
            )

        # 验证必需字段
        if "path" not in jsonpath_data or not jsonpath_data["path"]:
            raise WorkflowValidationError(
                message=get_message("workflow.jsonpath_missing_path"),
                field_path=f"{context}.jsonpath.path",
                expected=get_message("workflow.non_empty_jsonpath"),
                actual=str(jsonpath_data.get("path")),
                suggestion=get_message("workflow.jsonpath_path_suggestion"),
            )

        jsonpath_config = JsonPathCondition(
            input=jsonpath_data.get("input", ""),
            path=jsonpath_data["path"],
            exists=jsonpath_data.get("exists"),
            equals=jsonpath_data.get("equals"),
            contains=jsonpath_data.get("contains"),
        )

    if "text" in data:
        text_data = data["text"]
        if not isinstance(text_data, dict):
            raise WorkflowValidationError(
                message=get_message("workflow.text_must_be_dict"),
                field_path=f"{context}.text",
                expected=get_message("workflow.dict_object"),
                actual=str(type(text_data).__name__),
                suggestion=get_message("workflow.text_dict_suggestion"),
            )

        # 验证必需字段 input
        if "input" not in text_data:
            raise WorkflowValidationError(
                message=get_message("workflow.text_missing_input"),
                field_path=f"{context}.text.input",
                expected=get_message("workflow.input_template"),
                actual="None",
                suggestion=get_message("workflow.text_input_suggestion"),
            )

        # 至少需要一个匹配条件
        match_fields = [
            "contains",
            "not_contains",
            "starts_with",
            "ends_with",
            "equals",
            "not_equals",
            "is_empty",
            "matches",
        ]
        has_match_condition = any(field in text_data for field in match_fields)
        if not has_match_condition:
            raise WorkflowValidationError(
                message=get_message("workflow.text_missing_match_condition"),
                field_path=f"{context}.text",
                expected=f"at least one of: {', '.join(match_fields)}",
                actual=str(list(text_data.keys())),
                suggestion=get_message("workflow.text_match_suggestion"),
            )

        text_config = TextCondition(
            input=text_data.get("input", ""),
            contains=text_data.get("contains"),
            not_contains=text_data.get("not_contains"),
            starts_with=text_data.get("starts_with"),
            ends_with=text_data.get("ends_with"),
            equals=text_data.get("equals"),
            not_equals=text_data.get("not_equals"),
            is_empty=text_data.get("is_empty"),
            matches=text_data.get("matches"),
            ignore_case=text_data.get("ignore_case", False),
        )

    return WhenConfig(regex=regex_config, jsonpath=jsonpath_config, text=text_config)


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
                message=get_message("workflow.output_missing_method"),
                field_path=context,
                expected="jsonpath, regex or template",
                actual="no valid extraction method",
                suggestion=get_message("workflow.output_method_suggestion"),
            )

        return OutputConfig(
            jsonpath=value.get("jsonpath"),
            regex=value.get("regex"),
            regex_group=value.get("group"),
            template=value.get("template"),
        )

    raise WorkflowValidationError(
        message=get_message("workflow.output_invalid_format"),
        field_path=context,
        expected="string or dictionary object",
        actual=str(type(value).__name__),
        suggestion=get_message("workflow.output_format_suggestion"),
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
            message=get_message("workflow.invalid_conversation_action"),
            field_path=f"{context}.conversation.action",
            expected=f"one of: {', '.join(valid_actions)}",
            actual=f"'{action}'",
            suggestion=get_message("workflow.conversation_action_suggestion"),
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
            message=get_message_with_format(
                "workflow.missing_required_field", field=field
            ),
            field_path=f"{context}.{field}",
            expected=f"required field '{field}'",
            actual="field does not exist",
            suggestion=f"Please add '{field}' field in {context}",
        )

    value = data[field]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise WorkflowValidationError(
            message=get_message_with_format(
                "workflow.field_cannot_be_empty", field=field
            ),
            field_path=f"{context}.{field}",
            expected=get_message("workflow.non_empty_string"),
            actual=str(value),
            suggestion=f"Please provide a valid value for '{field}'",
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
    return GlobalsConfig(
        model=data.get("model", "v3_chat"),
        product_mode=data.get("product_mode", "lite"),
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
    default_action = data.get("default_action", "resume")
    valid_actions = ["resume", "new", "continue"]
    if default_action not in valid_actions:
        raise WorkflowValidationError(
            message=get_message("workflow.invalid_default_action"),
            field_path="spec.conversation.default_action",
            expected=f"one of: {', '.join(valid_actions)}",
            actual=f"'{default_action}'",
            suggestion=get_message("workflow.default_action_suggestion"),
        )

    return ConversationConfig(
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
            message=get_message("workflow.invalid_attempt_format"),
            field_path="spec.attempt.format",
            expected=f"one of: {', '.join(valid_formats)}",
            actual=f"'{format_type}'",
            suggestion=get_message("workflow.attempt_format_suggestion"),
        )

    jsonpaths = data.get("jsonpaths", {})
    if not isinstance(jsonpaths, dict):
        raise WorkflowValidationError(
            message=get_message("workflow.jsonpaths_must_be_dict"),
            field_path="spec.attempt.jsonpaths",
            expected=get_message("workflow.dict_object"),
            actual=str(type(jsonpaths).__name__),
            suggestion=get_message("workflow.jsonpaths_dict_suggestion"),
        )

    return AttemptConfig(
        format=format_type,
        jsonpaths=jsonpaths,
    )


def _validate_agents_existence(agents: List[AgentSpec], yaml_path: str = None) -> None:
    """
    验证所有 agent 定义文件是否存在

    使用 AgentManager 的优先级目录搜索机制来验证 agent 是否可以被解析。

    Args:
        agents: agent 规格列表
        yaml_path: YAML 文件路径（用于推断 project_root）

    Raises:
        WorkflowAgentResolutionError: 如果任何 agent 无法被解析
    """
    # 推断 project_root
    if yaml_path:
        yaml_file = Path(yaml_path)
        # 尝试从 YAML 文件路径推断 project_root
        # 假设 YAML 在 .autocoderworkflow/ 或 .auto-coder/.autocoderworkflow/ 下
        if ".autocoderworkflow" in yaml_file.parts:
            # 找到 .autocoderworkflow 的父目录
            for i, part in enumerate(yaml_file.parts):
                if part == ".autocoderworkflow":
                    project_root = Path(*yaml_file.parts[:i])
                    break
                elif (
                    part == ".auto-coder"
                    and i + 1 < len(yaml_file.parts)
                    and yaml_file.parts[i + 1] == ".autocoderworkflow"
                ):
                    project_root = Path(*yaml_file.parts[:i])
                    break
            else:
                project_root = yaml_file.parent
        else:
            project_root = yaml_file.parent if yaml_file.is_file() else yaml_file
    else:
        project_root = Path.cwd()

    # 创建 AgentManager 实例
    agent_manager = AgentManager(project_root=str(project_root))

    # 获取所有搜索目录用于错误提示
    search_directories = agent_manager.get_all_agents_directories()

    # 如果没有搜索目录，使用默认目录列表
    if not search_directories:
        search_directories = [
            str(project_root / ".autocoderagents"),
            str(project_root / ".auto-coder" / ".autocoderagents"),
            str(Path.home() / ".auto-coder" / ".autocoderagents"),
        ]

    # 验证每个 agent
    for i, agent_spec in enumerate(agents):
        agent_id = agent_spec.id
        agent_path = agent_spec.path

        # 方法1：尝试通过 ID 获取（假设 agent ID 与 agent name 一致）
        agent_definition = agent_manager.get_agent(agent_id)

        if agent_definition:
            # 找到了 agent 定义，验证通过
            logger.debug(
                f"验证通过: agent '{agent_id}' 存在于 {agent_definition.file_path}"
            )
            continue

        # 方法2：如果通过 ID 找不到，尝试直接检查文件路径
        # 按优先级在各个目录中查找
        found = False
        for search_dir in search_directories:
            potential_path = Path(search_dir) / agent_path
            if potential_path.exists() and potential_path.is_file():
                logger.debug(f"验证通过: agent 文件存在于 {potential_path}")
                found = True
                break

        if found:
            continue

        # 未找到 agent 定义文件，抛出错误
        field_path = f"spec.agents[{i}].path"

        # 构建搜索路径列表用于错误提示
        searched_paths = [str(Path(d) / agent_path) for d in search_directories]

        raise WorkflowAgentResolutionError(
            agent_id=agent_id,
            path=agent_path,
            searched_paths=searched_paths,
            field_path=field_path,
            suggestion=f"请确保代理定义文件 '{agent_path}' 存在于以下目录之一：{', '.join(search_directories)}",
        )
