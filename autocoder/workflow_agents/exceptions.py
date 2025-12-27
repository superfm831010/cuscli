"""
Workflow Agents 异常定义

提供清晰、结构化的异常类型，帮助用户快速定位和修复 workflow YAML 配置问题。
所有错误消息支持国际化。
"""

from autocoder.common.international import get_message


class WorkflowError(Exception):
    """Workflow 基础异常类"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class WorkflowValidationError(WorkflowError):
    """Workflow 验证错误

    用于 YAML 配置格式验证、必需字段检查等场景。
    """

    def __init__(
        self,
        message: str,
        field_path: str = None,
        expected: str = None,
        actual: str = None,
        suggestion: str = None,
    ):
        """
        Args:
            message: 错误消息
            field_path: 字段路径，如 "spec.agents[0].id"
            expected: 期望的值或格式
            actual: 实际的值
            suggestion: 修复建议
        """
        details = {
            "field_path": field_path,
            "expected": expected,
            "actual": actual,
            "suggestion": suggestion,
        }
        # 过滤掉 None 值
        details = {k: v for k, v in details.items() if v is not None}

        super().__init__(message, details)
        self.field_path = field_path
        self.expected = expected
        self.actual = actual
        self.suggestion = suggestion

    def __str__(self):
        title = get_message("workflow.validation_error_title")
        lines = [f"{title}: {self.message}"]

        if self.field_path:
            field_label = get_message("workflow.field_path")
            lines.append(f"   {field_label}: {self.field_path}")

        if self.expected:
            expected_label = get_message("workflow.expected_value")
            lines.append(f"   {expected_label}: {self.expected}")

        if self.actual:
            actual_label = get_message("workflow.actual_value")
            lines.append(f"   {actual_label}: {self.actual}")

        if self.suggestion:
            suggestion_label = get_message("workflow.fix_suggestion")
            lines.append(f"   {suggestion_label}: {self.suggestion}")

        return "\n".join(lines)


class WorkflowFileNotFoundError(WorkflowError):
    """Workflow 文件未找到错误"""

    def __init__(self, workflow_name: str, searched_paths: list = None):
        self.workflow_name = workflow_name
        self.searched_paths = searched_paths or []

        message = f"未找到 workflow: '{workflow_name}'"
        details = {"workflow_name": workflow_name, "searched_paths": searched_paths}

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.file_not_found_title")
        lines = [f"{title}: {self.workflow_name}"]

        if self.searched_paths:
            searched_label = get_message("workflow.searched_paths")
            lines.append(f"   {searched_label}:")
            for path in self.searched_paths:
                lines.append(f"     - {path}")

        lines.append("")
        please_check = get_message("workflow.please_check")
        lines.append(f"   {please_check}:")
        check_name = get_message("workflow.check_name_correct")
        lines.append(f"     {check_name}")
        check_file = get_message("workflow.check_file_exists")
        lines.append(f"     {check_file}:")
        lines.append("        - .autocoderworkflow/")
        lines.append("        - .auto-coder/.autocoderworkflow/")
        lines.append("        - ~/.auto-coder/.autocoderworkflow/")

        return "\n".join(lines)


class WorkflowParseError(WorkflowError):
    """Workflow YAML 解析错误"""

    def __init__(self, yaml_path: str, parse_error: Exception, line_number: int = None):
        self.yaml_path = yaml_path
        self.parse_error = parse_error
        self.line_number = line_number

        message = f"解析 workflow YAML 文件失败: {yaml_path}"
        details = {
            "yaml_path": yaml_path,
            "error_type": type(parse_error).__name__,
            "error_message": str(parse_error),
            "line_number": line_number,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.parse_error_title")
        lines = [title]

        file_label = get_message("workflow.file")
        lines.append(f"   {file_label}: {self.yaml_path}")

        if self.line_number:
            line_label = get_message("workflow.line_number")
            lines.append(f"   {line_label}: {self.line_number}")

        error_type_label = get_message("workflow.error_type")
        lines.append(f"   {error_type_label}: {self.details['error_type']}")

        error_details_label = get_message("workflow.error_details")
        lines.append(f"   {error_details_label}: {self.details['error_message']}")

        lines.append("")
        common_issues = get_message("workflow.common_issues")
        lines.append(f"   {common_issues}:")

        check_syntax = get_message("workflow.check_yaml_syntax")
        lines.append(f"     {check_syntax}")

        no_tabs = get_message("workflow.no_tab_characters")
        lines.append(f"     {no_tabs}")

        check_chars = get_message("workflow.check_special_chars")
        lines.append(f"     {check_chars}")

        return "\n".join(lines)


class WorkflowStepError(WorkflowError):
    """Workflow 步骤执行错误"""

    def __init__(
        self,
        step_id: str,
        agent_id: str = None,
        error_message: str = None,
        cause: Exception = None,
    ):
        self.step_id = step_id
        self.agent_id = agent_id
        self.cause = cause

        message = f"步骤 '{step_id}' 执行失败"
        if error_message:
            message = f"{message}: {error_message}"

        details = {
            "step_id": step_id,
            "agent_id": agent_id,
            "error_message": error_message,
            "cause_type": type(cause).__name__ if cause else None,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.step_error_title")
        lines = [title]

        step_label = get_message("workflow.step_id")
        lines.append(f"   {step_label}: {self.step_id}")

        if self.agent_id:
            agent_label = get_message("workflow.agent_id")
            lines.append(f"   {agent_label}: {self.agent_id}")

        if self.details.get("error_message"):
            error_label = get_message("workflow.error")
            lines.append(f"   {error_label}: {self.details['error_message']}")

        if self.cause:
            cause_type_label = get_message("workflow.cause_type")
            lines.append(f"   {cause_type_label}: {self.details['cause_type']}")

            cause_details_label = get_message("workflow.cause_details")
            lines.append(f"   {cause_details_label}: {str(self.cause)}")

        return "\n".join(lines)


class WorkflowDependencyError(WorkflowError):
    """Workflow 依赖错误（循环依赖、缺失依赖等）"""

    def __init__(
        self, message: str, step_id: str = None, dependency_chain: list = None
    ):
        self.step_id = step_id
        self.dependency_chain = dependency_chain or []

        details = {"step_id": step_id, "dependency_chain": dependency_chain}

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.dependency_error_title")
        lines = [f"{title}: {self.message}"]

        if self.step_id:
            involved_label = get_message("workflow.involved_step")
            lines.append(f"   {involved_label}: {self.step_id}")

        if self.dependency_chain:
            chain_label = get_message("workflow.dependency_chain")
            lines.append(f"   {chain_label}:")
            for i, step in enumerate(self.dependency_chain):
                lines.append(f"     {i + 1}. {step}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        check_needs = get_message("workflow.check_needs_field")
        lines.append(f"     {check_needs}")

        no_circular = get_message("workflow.no_circular_dependency")
        lines.append(f"     {no_circular}")

        check_spelling = get_message("workflow.check_step_id_spelling")
        lines.append(f"     {check_spelling}")

        return "\n".join(lines)


class WorkflowAgentNotFoundError(WorkflowError):
    """Workflow 中引用的 agent 不存在"""

    def __init__(
        self, agent_id: str, step_id: str = None, available_agents: list = None
    ):
        self.agent_id = agent_id
        self.step_id = step_id
        self.available_agents = available_agents or []

        message = f"步骤引用的代理不存在: '{agent_id}'"
        if step_id:
            message = f"步骤 '{step_id}' {message}"

        details = {
            "agent_id": agent_id,
            "step_id": step_id,
            "available_agents": available_agents,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.agent_not_found_title")
        lines = [title]

        referenced_label = get_message("workflow.referenced_agent")
        lines.append(f"   {referenced_label}: {self.agent_id}")

        if self.step_id:
            step_label = get_message("workflow.in_step")
            lines.append(f"   {step_label}: {self.step_id}")

        available_label = get_message("workflow.available_agents")
        if self.available_agents:
            lines.append(f"   {available_label}:")
            for agent in self.available_agents:
                lines.append(f"     - {agent}")
        else:
            no_agents = get_message("workflow.no_agents")
            lines.append(f"   {available_label}: {no_agents}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        check_spelling = get_message("workflow.check_agent_spelling")
        lines.append(f"     {check_spelling}")

        ensure_defined = get_message("workflow.ensure_agent_defined")
        lines.append(f"     {ensure_defined}")

        return "\n".join(lines)


class WorkflowTemplateError(WorkflowError):
    """Workflow 模板渲染错误"""

    def __init__(self, template: str, expression: str, context_keys: list = None):
        self.template = template
        self.expression = expression
        self.context_keys = context_keys or []

        message = f"模板渲染失败: 无法解析表达式 '${{{expression}}}'"

        details = {
            "template": template,
            "expression": expression,
            "context_keys": context_keys,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.template_error_title")
        lines = [title]

        expr_label = get_message("workflow.expression")
        lines.append(f"   {expr_label}: ${{{self.expression}}}")

        # 显示模板片段（最多100字符）
        template_preview = self.template[:100]
        if len(self.template) > 100:
            template_preview += "..."
        snippet_label = get_message("workflow.template_snippet")
        lines.append(f"   {snippet_label}: {template_preview}")

        if self.context_keys:
            keys_label = get_message("workflow.available_context_keys")
            lines.append(f"   {keys_label}:")
            for key in self.context_keys[:10]:  # 最多显示10个
                lines.append(f"     - {key}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        check_syntax = get_message("workflow.check_expression_syntax")
        lines.append(f"     {check_syntax}")

        ensure_defined = get_message("workflow.ensure_variable_defined")
        lines.append(f"     {ensure_defined}")

        check_order = get_message("workflow.check_execution_order")
        lines.append(f"     {check_order}")

        return "\n".join(lines)


class WorkflowAgentDefinitionError(WorkflowError):
    """Workflow agent 定义错误（文件不存在、内容无效等）"""

    def __init__(
        self, agent_id: str, agent_path: str, error_type: str, error_details: str = None
    ):
        self.agent_id = agent_id
        self.agent_path = agent_path
        self.error_type = error_type

        message = f"代理 '{agent_id}' 定义错误: {error_type}"

        details = {
            "agent_id": agent_id,
            "agent_path": agent_path,
            "error_type": error_type,
            "error_details": error_details,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.agent_definition_error_title")
        lines = [title]

        agent_id_label = get_message("workflow.agent_id")
        lines.append(f"   {agent_id_label}: {self.agent_id}")

        agent_path_label = get_message("workflow.agent_path")
        lines.append(f"   {agent_path_label}: {self.agent_path}")

        error_type_label = get_message("workflow.error_type")
        lines.append(f"   {error_type_label}: {self.error_type}")

        if self.details.get("error_details"):
            error_details_label = get_message("workflow.error_details")
            lines.append(f"   {error_details_label}: {self.details['error_details']}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        check_file = get_message("workflow.check_agent_file_exists")
        lines.append(f"     {check_file}")

        ensure_content = get_message("workflow.ensure_agent_content_valid")
        lines.append(f"     {ensure_content}")

        check_spelling = get_message("workflow.check_path_spelling")
        lines.append(f"     {check_spelling}")

        return "\n".join(lines)


class WorkflowConversationError(WorkflowError):
    """Workflow 会话管理错误"""

    def __init__(
        self,
        message: str,
        conversation_id: str = None,
        action: str = None,
        step_id: str = None,
    ):
        self.conversation_id = conversation_id
        self.action = action
        self.step_id = step_id

        details = {
            "conversation_id": conversation_id,
            "action": action,
            "step_id": step_id,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.conversation_error_title")
        lines = [f"{title}: {self.message}"]

        if self.step_id:
            step_label = get_message("workflow.step_id")
            lines.append(f"   {step_label}: {self.step_id}")

        if self.action:
            action_label = get_message("workflow.conversation_action")
            lines.append(f"   {action_label}: {self.action}")

        if self.conversation_id:
            conv_id_label = get_message("workflow.conversation_id")
            lines.append(f"   {conv_id_label}: {self.conversation_id}")

        return "\n".join(lines)


class WorkflowConditionError(WorkflowError):
    """Workflow 条件评估错误"""

    def __init__(
        self,
        message: str,
        step_id: str = None,
        condition_type: str = None,
        condition_details: dict = None,
    ):
        self.step_id = step_id
        self.condition_type = condition_type
        self.condition_details = condition_details or {}

        details = {
            "step_id": step_id,
            "condition_type": condition_type,
            **condition_details,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.condition_error_title")
        lines = [f"{title}: {self.message}"]

        if self.step_id:
            step_label = get_message("workflow.step_id")
            lines.append(f"   {step_label}: {self.step_id}")

        if self.condition_type:
            type_label = get_message("workflow.condition_type")
            lines.append(f"   {type_label}: {self.condition_type}")

        if self.condition_details:
            details_label = get_message("workflow.condition_details")
            lines.append(f"   {details_label}:")
            for key, value in self.condition_details.items():
                lines.append(f"     {key}: {value}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        check_when = get_message("workflow.check_when_syntax")
        lines.append(f"     {check_when}")

        verify_regex = get_message("workflow.verify_regex_pattern")
        lines.append(f"     {verify_regex}")

        ensure_jsonpath = get_message("workflow.ensure_jsonpath_correct")
        lines.append(f"     {ensure_jsonpath}")

        return "\n".join(lines)


class WorkflowOutputExtractionError(WorkflowError):
    """Workflow 输出提取错误"""

    def __init__(
        self,
        message: str,
        step_id: str = None,
        output_key: str = None,
        extraction_method: str = None,
    ):
        self.step_id = step_id
        self.output_key = output_key
        self.extraction_method = extraction_method

        details = {
            "step_id": step_id,
            "output_key": output_key,
            "extraction_method": extraction_method,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.output_extraction_error_title")
        lines = [f"{title}: {self.message}"]

        if self.step_id:
            step_label = get_message("workflow.step_id")
            lines.append(f"   {step_label}: {self.step_id}")

        if self.output_key:
            key_label = get_message("workflow.output_key")
            lines.append(f"   {key_label}: {self.output_key}")

        if self.extraction_method:
            method_label = get_message("workflow.extraction_method")
            lines.append(f"   {method_label}: {self.extraction_method}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        check_jsonpath = get_message("workflow.check_jsonpath_expression")
        lines.append(f"     {check_jsonpath}")

        verify_regex = get_message("workflow.verify_regex_and_group")
        lines.append(f"     {verify_regex}")

        ensure_format = get_message("workflow.ensure_format_matches")
        lines.append(f"     {ensure_format}")

        return "\n".join(lines)


class WorkflowAgentResolutionError(WorkflowError):
    """Workflow 代理解析错误（代理文件无法解析）"""

    def __init__(
        self,
        agent_id: str,
        path: str,
        searched_paths: list = None,
        field_path: str = None,
        suggestion: str = None,
    ):
        """
        Args:
            agent_id: 代理 ID
            path: 代理路径
            searched_paths: 已搜索的路径列表
            field_path: 字段路径，如 "spec.agents[0].path"
            suggestion: 修复建议
        """
        self.agent_id = agent_id
        self.path = path
        self.searched_paths = searched_paths or []
        self.field_path = field_path
        self.suggestion = suggestion

        message = get_message("workflow.agent_resolution_failed")

        details = {
            "agent_id": agent_id,
            "path": path,
            "searched_paths": searched_paths,
            "field_path": field_path,
            "suggestion": suggestion,
        }

        super().__init__(message, details)

    def __str__(self):
        title = get_message("workflow.agent_resolution_error_title")
        lines = [title]

        agent_id_label = get_message("workflow.agent_id")
        lines.append(f"   {agent_id_label}: {self.agent_id}")

        path_label = get_message("workflow.agent_path")
        lines.append(f"   {path_label}: {self.path}")

        if self.field_path:
            field_label = get_message("workflow.field_path")
            lines.append(f"   {field_label}: {self.field_path}")

        if self.searched_paths:
            searched_label = get_message("workflow.searched_agent_paths")
            lines.append(f"   {searched_label}:")
            for search_path in self.searched_paths:
                lines.append(f"     - {search_path}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        if self.suggestion:
            lines.append(f"     {self.suggestion}")
        else:
            check_exists = get_message("workflow.check_agent_path_exists")
            lines.append(f"     {check_exists}")

            verify_path = get_message("workflow.verify_agent_path_correct")
            lines.append(f"     {verify_path}")

        return "\n".join(lines)


class WorkflowModelValidationError(WorkflowError):
    """Workflow 模型验证错误（模型不存在或密钥未配置）"""

    def __init__(
        self,
        message: str,
        step_id: str = None,
        agent_id: str = None,
        model: str = None,
        suggestion: str = None,
    ):
        """
        Args:
            message: 错误消息
            step_id: 步骤 ID
            agent_id: 代理 ID
            model: 模型名称
            suggestion: 修复建议
        """
        self.step_id = step_id
        self.agent_id = agent_id
        self.model = model
        self.suggestion = suggestion

        details = {
            "step_id": step_id,
            "agent_id": agent_id,
            "model": model,
            "suggestion": suggestion,
        }

        super().__init__(message, details)

    @classmethod
    def for_model_not_found(
        cls, step_id: str, agent_id: str, model: str
    ) -> "WorkflowModelValidationError":
        """创建模型不存在错误"""
        message = get_message("workflow.model_not_found")
        suggestion = get_message("workflow.check_model_registered")
        return cls(
            message=f"{message}: {model}",
            step_id=step_id,
            agent_id=agent_id,
            model=model,
            suggestion=suggestion,
        )

    @classmethod
    def for_key_missing(
        cls, step_id: str, agent_id: str, model: str
    ) -> "WorkflowModelValidationError":
        """创建密钥未配置错误"""
        message = get_message("workflow.model_key_missing")
        suggestion = get_message("workflow.check_api_key_configured")
        return cls(
            message=f"{message}: {model}",
            step_id=step_id,
            agent_id=agent_id,
            model=model,
            suggestion=suggestion,
        )

    def __str__(self):
        title = get_message("workflow.model_validation_error_title")
        lines = [f"{title}: {self.message}"]

        if self.step_id:
            step_label = get_message("workflow.step_id")
            lines.append(f"   {step_label}: {self.step_id}")

        if self.agent_id:
            agent_label = get_message("workflow.agent_id")
            lines.append(f"   {agent_label}: {self.agent_id}")

        if self.model:
            model_label = get_message("workflow.model_name")
            lines.append(f"   {model_label}: {self.model}")

        lines.append("")
        suggestion_label = get_message("workflow.fix_suggestion")
        lines.append(f"   {suggestion_label}:")

        if self.suggestion:
            lines.append(f"     {self.suggestion}")
        else:
            check_registered = get_message("workflow.check_model_registered")
            lines.append(f"     {check_registered}")

            check_key = get_message("workflow.check_api_key_configured")
            lines.append(f"     {check_key}")

            check_spelling = get_message("workflow.check_model_name_spelling")
            lines.append(f"     {check_spelling}")

        return "\n".join(lines)
