"""
Workflow Agents 工具函数

提供模板渲染、条件评估、JSONPath 处理等辅助功能。
"""

import re
import json
from typing import Any, Dict, Optional
from loguru import logger

from autocoder.workflow_agents.types import (
    WhenConfig,
    RegexCondition,
    JsonPathCondition,
    TextCondition,
    OutputConfig,
)
from autocoder.workflow_agents.exceptions import (
    WorkflowTemplateError,
)

# 常量定义
TEMPLATE_PREFIX = "${"
TEMPLATE_SUFFIX = "}"
ATTEMPT_RESULT_VAR = "attempt_result"
FORMAT_JSON = "json"
FORMAT_TEXT = "text"


def render_template(template: Any, context: Dict[str, Any]) -> Any:
    """
    渲染模板字符串

    支持的模板语法：
    - ${vars.key} - 访问全局变量
    - ${steps.stepId.outputs.key} - 访问步骤输出
    - ${attempt_result} - 访问上一次的 attempt 结果
    - \\$ - 转义，输出字面的 $

    支持在字符串中嵌入多个变量，例如：
    "基于文件 ${steps.step1.outputs.files} 执行 ${vars.action}"

    Args:
        template: 模板（字符串或其他类型）
        context: 上下文数据，包含 vars、steps 等

    Returns:
        渲染后的值
    """
    if not isinstance(template, str):
        return template

    # 如果没有任何模板标记，直接返回
    if "${" not in template and "\\$" not in template:
        return template

    # 正则表达式：匹配非转义的 ${...}
    # (?<!\\) - 负向后查找，确保前面不是反斜杠
    # \$\{([^}]+)\} - 匹配 ${...}
    pattern = r"(?<!\\)\$\{([^}]+)\}"

    def replace_var(match):
        expr = match.group(1).strip()
        try:
            value = _resolve_expression(expr, context)
            # 如果值是 None，返回空字符串
            return str(value) if value is not None else ""
        except (KeyError, IndexError, TypeError) as e:
            # 提供更友好的错误信息
            context_keys = _get_context_keys(context)
            logger.warning(f"模板表达式无法解析: ${{{expr}}}, 可用键: {context_keys}")
            # 抛出友好的异常
            raise WorkflowTemplateError(
                template=template, expression=expr, context_keys=context_keys
            ) from e

    # 替换所有变量
    result = re.sub(pattern, replace_var, template)

    # 处理转义：将 \$ 替换为 $
    result = result.replace(r"\$", "$")

    return result


def _resolve_expression(expr: str, context: Dict[str, Any]) -> Any:
    """
    解析模板表达式

    Args:
        expr: 表达式内容（去除 ${ } 后的部分）
        context: 上下文数据

    Returns:
        解析后的值

    Raises:
        KeyError, IndexError, TypeError: 解析失败时抛出
    """
    parts = expr.split(".")

    # ${vars.key}
    if parts[0] == "vars" and len(parts) >= 2:
        vars_dict = context.get("vars", {})
        if parts[1] not in vars_dict:
            raise KeyError(f"Variable not found: vars.{parts[1]}")
        return vars_dict[parts[1]]

    # ${steps.stepId.outputs.key}
    if parts[0] == "steps" and len(parts) >= 4 and parts[2] == "outputs":
        step_id = parts[1]
        key = parts[3]
        steps_dict = context.get("steps", {})
        if step_id not in steps_dict:
            raise KeyError(f"Step not found: {step_id}")
        outputs_dict = steps_dict[step_id].get("outputs", {})
        if key not in outputs_dict:
            raise KeyError(f"Output not found: {step_id}.outputs.{key}")
        return outputs_dict[key]

    # ${attempt_result}
    if expr == ATTEMPT_RESULT_VAR:
        # attempt_result 可能为 None（初始状态），这是合法的
        return context.get("_last_attempt_result")

    # 不支持的表达式
    raise KeyError(f"不支持的表达式: {expr}")


def evaluate_condition(
    when_config: Optional[WhenConfig],
    attempt_result: Optional[str],
    context: Dict[str, Any],
) -> bool:
    """
    评估条件是否满足

    Args:
        when_config: 条件配置
        attempt_result: AttemptCompletion 结果字符串
        context: 上下文数据

    Returns:
        条件是否满足
    """
    if when_config is None:
        return True

    # 正则条件
    if when_config.regex is not None:
        return evaluate_regex_condition(when_config.regex, attempt_result, context)

    # JSONPath 条件
    if when_config.jsonpath is not None:
        return evaluate_jsonpath_condition(
            when_config.jsonpath, attempt_result, context
        )

    # 文本条件
    if when_config.text is not None:
        return evaluate_text_condition(when_config.text, attempt_result, context)

    return True


def _get_input_string(
    input_template: str, context: Dict[str, Any], fallback: Optional[str]
) -> str:
    """
    获取输入字符串（公共逻辑）

    Args:
        input_template: 输入模板
        context: 上下文数据
        fallback: 回退值（通常是 attempt_result）

    Returns:
        解析后的输入字符串
    """
    if input_template:
        return str(render_template(input_template, context))
    return fallback or ""


def evaluate_regex_condition(
    regex_config: RegexCondition, attempt_result: Optional[str], context: Dict[str, Any]
) -> bool:
    """
    评估正则条件

    Args:
        regex_config: 正则条件配置
        attempt_result: AttemptCompletion 结果字符串
        context: 上下文数据

    Returns:
        条件是否满足
    """
    input_str = _get_input_string(regex_config.input, context, attempt_result)
    pattern = regex_config.pattern

    flags = 0
    if regex_config.flags and regex_config.flags.lower() == "i":
        flags |= re.IGNORECASE

    match = re.search(pattern, input_str, flags)
    return match is not None


def evaluate_jsonpath_condition(
    jsonpath_config: JsonPathCondition,
    attempt_result: Optional[str],
    context: Dict[str, Any],
) -> bool:
    """
    评估 JSONPath 条件

    Args:
        jsonpath_config: JSONPath 条件配置
        attempt_result: AttemptCompletion 结果字符串
        context: 上下文数据

    Returns:
        条件是否满足
    """
    input_str = _get_input_string(jsonpath_config.input, context, attempt_result)

    try:
        data = json.loads(input_str)
    except Exception:
        return False

    path = jsonpath_config.path
    value = extract_jsonpath_value(data, path)

    # exists 检查
    if jsonpath_config.exists is not None:
        return (value is not None) == jsonpath_config.exists

    # equals 检查
    if jsonpath_config.equals is not None:
        return value == jsonpath_config.equals

    # contains 检查
    if jsonpath_config.contains is not None and isinstance(value, str):
        return jsonpath_config.contains in value

    # 默认：检查值是否存在且非空
    return bool(value)


def evaluate_text_condition(
    text_config: TextCondition,
    attempt_result: Optional[str],
    context: Dict[str, Any],
) -> bool:
    """
    评估文本条件

    支持多种文本匹配方式：
    - contains: 包含指定字符串
    - not_contains: 不包含指定字符串
    - starts_with: 以指定字符串开头
    - ends_with: 以指定字符串结尾
    - equals: 完全相等
    - not_equals: 不相等
    - is_empty: 是否为空
    - matches: 正则表达式匹配
    - ignore_case: 是否忽略大小写

    Args:
        text_config: 文本条件配置
        attempt_result: AttemptCompletion 结果字符串
        context: 上下文数据

    Returns:
        条件是否满足
    """
    input_str = _get_input_string(text_config.input, context, attempt_result)
    ignore_case = text_config.ignore_case

    # 辅助函数：根据 ignore_case 进行字符串比较
    def normalize(s: str) -> str:
        return s.lower() if ignore_case else s

    # is_empty 检查（优先级最高）
    if text_config.is_empty is not None:
        is_empty = input_str is None or input_str.strip() == ""
        return is_empty == text_config.is_empty

    # 如果 input_str 为 None，后续检查都返回 False
    if input_str is None:
        return False

    normalized_input = normalize(input_str)

    # contains 检查
    if text_config.contains is not None:
        target = normalize(text_config.contains)
        if target not in normalized_input:
            return False

    # not_contains 检查
    if text_config.not_contains is not None:
        target = normalize(text_config.not_contains)
        if target in normalized_input:
            return False

    # starts_with 检查
    if text_config.starts_with is not None:
        target = normalize(text_config.starts_with)
        if not normalized_input.startswith(target):
            return False

    # ends_with 检查
    if text_config.ends_with is not None:
        target = normalize(text_config.ends_with)
        if not normalized_input.endswith(target):
            return False

    # equals 检查
    if text_config.equals is not None:
        target = normalize(text_config.equals)
        if normalized_input != target:
            return False

    # not_equals 检查
    if text_config.not_equals is not None:
        target = normalize(text_config.not_equals)
        if normalized_input == target:
            return False

    # matches 正则检查（不受 ignore_case 影响，使用正则自身的 flags）
    if text_config.matches is not None:
        flags = re.IGNORECASE if ignore_case else 0
        if not re.search(text_config.matches, input_str, flags):
            return False

    return True


def extract_jsonpath_value(data: Any, path: str) -> Any:
    """
    从 JSON 数据中提取 JSONPath 路径的值

    简化实现，仅支持顶层访问：$.key

    Args:
        data: JSON 数据
        path: JSONPath 路径

    Returns:
        提取的值，如果路径不存在则返回 None
    """
    if not isinstance(data, dict):
        return None

    if path.startswith("$."):
        key = path[2:]
        return data.get(key)

    return None


def extract_outputs(
    outputs_map: Dict[str, Any],
    attempt_result: str,
    attempt_format: str,
    default_jsonpaths: Dict[str, str],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    从 AttemptCompletion 结果中提取输出

    Args:
        outputs_map: 输出映射配置
        attempt_result: AttemptCompletion 结果字符串
        attempt_format: 格式（json | text）
        default_jsonpaths: 默认 JSONPath 映射
        context: 上下文数据

    Returns:
        提取的输出字典
    """
    if not outputs_map:
        return {"attempt_raw": attempt_result}

    # 如果格式是 JSON，尝试解析
    parsed_json = _try_parse_json(attempt_result, attempt_format)

    # 提取每个输出
    extracted: Dict[str, Any] = {}
    for key, spec in outputs_map.items():
        value = _extract_single_output(
            key, spec, attempt_result, parsed_json, default_jsonpaths
        )
        extracted[key] = value

    # 确保总是有 attempt_raw
    extracted.setdefault("attempt_raw", attempt_result)
    return extracted


def _try_parse_json(
    attempt_result: str, attempt_format: str
) -> Optional[Dict[str, Any]]:
    """
    尝试将 attempt_result 解析为 JSON

    Args:
        attempt_result: AttemptCompletion 结果字符串
        attempt_format: 格式（json | text）

    Returns:
        解析后的 JSON 字典，如果失败或格式不是 json 则返回 None
    """
    if attempt_format != FORMAT_JSON:
        return None

    try:
        return json.loads(attempt_result)
    except Exception:
        return None


def _extract_single_output(
    key: str,
    spec: Any,
    attempt_result: str,
    parsed_json: Optional[Dict[str, Any]],
    default_jsonpaths: Dict[str, str],
) -> Any:
    """
    提取单个输出值

    Args:
        key: 输出键名
        spec: 输出配置（可能是字符串或 OutputConfig）
        attempt_result: 原始结果字符串
        parsed_json: 解析后的 JSON（如果有）
        default_jsonpaths: 默认 JSONPath 映射

    Returns:
        提取的值
    """
    # 直接透传 attempt_result（兼容旧代码）
    template_value = f"{TEMPLATE_PREFIX}{ATTEMPT_RESULT_VAR}{TEMPLATE_SUFFIX}"
    if isinstance(spec, str) and spec == template_value:
        return attempt_result

    # 不是 OutputConfig 对象，返回 None
    if not isinstance(spec, OutputConfig):
        return None

    # 模板字符串提取（新增支持）
    if spec.template is not None:
        # 如果是 ${attempt_result}，直接返回
        if spec.template == template_value:
            return attempt_result
        # 否则作为普通值返回（可能是其他模板）
        return spec.template

    # JSONPath 提取
    if spec.jsonpath is not None and parsed_json is not None:
        path = spec.jsonpath if spec.jsonpath else default_jsonpaths.get(key, "")
        return extract_jsonpath_value(parsed_json, path)

    # 正则提取
    if spec.regex is not None:
        return _extract_by_regex(spec.regex, spec.regex_group, attempt_result)

    return None


def _extract_by_regex(pattern: str, group: Optional[int], text: str) -> Optional[str]:
    """
    使用正则表达式提取文本

    Args:
        pattern: 正则表达式模式
        group: 捕获组索引（None 表示整个匹配）
        text: 待提取的文本

    Returns:
        提取的文本，如果未匹配则返回 None
    """
    match = re.search(pattern, text)
    if not match:
        return None

    if group is None:
        return match.group(0)
    return match.group(group)


def _get_context_keys(context: Dict[str, Any]) -> list:
    """
    获取上下文中所有可用的键（用于错误提示）

    Args:
        context: 上下文数据

    Returns:
        可用键的列表
    """
    keys = []

    # vars.*
    if "vars" in context and isinstance(context["vars"], dict):
        for var_key in context["vars"].keys():
            keys.append(f"vars.{var_key}")

    # steps.*.outputs.*
    if "steps" in context and isinstance(context["steps"], dict):
        for step_id, step_data in context["steps"].items():
            if isinstance(step_data, dict) and "outputs" in step_data:
                outputs = step_data["outputs"]
                if isinstance(outputs, dict):
                    for output_key in outputs.keys():
                        keys.append(f"steps.{step_id}.outputs.{output_key}")

    # attempt_result
    if "_last_attempt_result" in context:
        keys.append("attempt_result")

    return keys
