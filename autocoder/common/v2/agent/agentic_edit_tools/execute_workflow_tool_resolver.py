from typing import Optional
import json
from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import (
    BaseToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import (
    ToolResult,
    ExecuteWorkflowTool,
)
from autocoder.common import AutoCoderArgs
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit
    from autocoder.workflow_agents.exceptions import (
        WorkflowValidationError,
        WorkflowFileNotFoundError,
        WorkflowParseError,
        WorkflowDependencyError,
        WorkflowAgentNotFoundError,
        WorkflowTemplateError,
    )


def _generate_error_feedback(error: Exception, workflow_name: str) -> str:
    """
    根据异常类型生成英文反馈指导

    Args:
        error: 捕获的异常
        workflow_name: workflow 名称

    Returns:
        英文反馈指导文本
    """
    # 运行时导入以避免循环依赖
    from autocoder.workflow_agents.exceptions import (
        WorkflowValidationError,
        WorkflowFileNotFoundError,
        WorkflowParseError,
        WorkflowDependencyError,
        WorkflowAgentNotFoundError,
        WorkflowTemplateError,
    )

    error_type = type(error).__name__

    if isinstance(error, WorkflowFileNotFoundError):
        return f"""
**Error Type**: Workflow File Not Found

**What happened**: The workflow '{workflow_name}' could not be located in the standard search directories.

**Quick Fix**:
1. Verify the workflow name is spelled correctly
2. Check if the workflow file exists in one of these directories:
   - `.autocoderworkflow/` (project-level, recommended)
   - `.auto-coder/.autocoderworkflow/` (project-level)
   - `~/.auto-coder/.autocoderworkflow/` (global-level)
3. Ensure the file has a `.yaml` or `.yml` extension

**Example**:
If your workflow is named 'my-workflow', create:
- `.autocoderworkflow/my-workflow.yaml` in your project root

**Use load_extra_document tool** to get the workflow YAML specification if you need to create a new workflow.
"""

    elif isinstance(error, WorkflowParseError):
        line_info = (
            f" at line {error.line_number}"
            if hasattr(error, "line_number") and error.line_number
            else ""
        )
        return f"""
**Error Type**: YAML Syntax Error{line_info}

**What happened**: The workflow YAML file contains syntax errors that prevent parsing.

**Common YAML Mistakes**:
1. **Indentation**: YAML requires consistent spaces (NOT tabs)
   - Wrong: `  agents:` (using tabs)
   - Right: `  agents:` (using 2 or 4 spaces consistently)

2. **Missing colons**: Every key must have a colon
   - Wrong: `name coder`
   - Right: `name: coder`

3. **Unquoted special characters**: Strings with `:`, `{{`, `}}`, `#` need quotes
   - Wrong: `query: Fix: the bug`
   - Right: `query: "Fix: the bug"`

4. **List syntax**: Lists must use `-` prefix
   - Wrong: `steps: [step1, step2]` (use this only for inline arrays)
   - Right:
     ```yaml
     steps:
       - id: step1
       - id: step2
     ```

**Quick Fix**:
- Copy your YAML content to an online YAML validator
- Use a YAML-aware editor (VS Code, etc.) with syntax highlighting
- Check the specific line mentioned in the error (if available)
"""

    elif isinstance(error, WorkflowValidationError):
        field = error.field_path if hasattr(error, "field_path") else "unknown field"
        expected = error.expected if hasattr(error, "expected") else "see documentation"
        return f"""
**Error Type**: Configuration Validation Error

**What happened**: The workflow configuration contains invalid or missing values.

**Problem Field**: `{field}`
**Expected**: {expected}

**Common Configuration Issues**:
1. **Missing required fields**: Ensure all required fields are present
   - Required in workflow: `apiVersion`, `kind`, `metadata.name`, `spec.agents`, `spec.steps`
   - Required in agents: `id`, `path`
   - Required in steps: `id`, `agent`

2. **Invalid enum values**:
   - `runner` must be: `sdk` or `terminal`
   - `conversation.action` must be: `new`, `resume`, or `continue`
   - `attempt.format` must be: `json` or `text`

3. **Type mismatches**:
   - `max_turns`, `retries`, `timeout_sec` must be positive integers
   - `include_rules` must be boolean (`true` or `false`)
   - `agents` and `steps` must be arrays (lists)

4. **Duplicate IDs**: All agent IDs and step IDs must be unique

**Quick Fix**:
- Review the specific field path mentioned above
- Check the workflow specification using `load_extra_document` tool with name 'workflow_subagents'
- Compare your configuration with working examples
"""

    elif isinstance(error, WorkflowDependencyError):
        return f"""
**Error Type**: Step Dependency Error

**What happened**: The workflow has dependency-related issues (circular dependencies or missing step references).

**Dependency Rules**:
1. **No circular dependencies**: Step A cannot depend on Step B if Step B depends on Step A
   - Wrong:
     ```yaml
     - id: step1
       needs: [step2]
     - id: step2
       needs: [step1]  # Circular!
     ```

2. **Referenced steps must exist**: Steps in `needs` field must be defined
   - Wrong: `needs: [nonexistent_step]`
   - Right: `needs: [gather_context]` (where gather_context is a valid step id)

3. **Execution order**: Steps are executed in topological order based on dependencies
   - Dependencies are executed first
   - Steps without dependencies can run in any order

**Quick Fix**:
1. Check the dependency chain shown in the error message
2. Verify all step IDs referenced in `needs` fields exist
3. Draw a dependency graph on paper to visualize the flow
4. Remove or fix circular dependencies

**Example of correct dependencies**:
```yaml
steps:
  - id: gather
    agent: context
    # No dependencies, runs first
  
  - id: implement
    needs: [gather]  # Depends on 'gather', runs after it
    agent: coder
```
"""

    elif isinstance(error, WorkflowAgentNotFoundError):
        agent_id = error.agent_id if hasattr(error, "agent_id") else "unknown"
        available = error.available_agents if hasattr(error, "available_agents") else []
        return f"""
**Error Type**: Agent Reference Error

**What happened**: A step references an agent '{agent_id}' that is not defined in `spec.agents`.

**Available Agents**: {', '.join(available) if available else 'none'}

**How to Fix**:
1. **Option A - Fix the typo**: If you meant to use an existing agent, correct the spelling
   - Check step's `agent` field matches an `id` in `spec.agents`

2. **Option B - Define the missing agent**: If '{agent_id}' is a new agent, add it to `spec.agents`
   ```yaml
   spec:
     agents:
       - id: {agent_id}
         path: {agent_id}.md  # Path to agent prompt file
         runner: sdk  # or terminal
   ```

3. **Verify agent files exist**:
   - Agent prompt files should be in `.autocoderagents/` directory
   - Use `ac_mod_list` tool to check available agent definitions

**Quick Fix**:
- Review your `spec.agents` section
- Ensure each step's `agent` field matches an agent `id`
- Create missing agent definition files if needed
"""

    elif isinstance(error, WorkflowTemplateError):
        expr = error.expression if hasattr(error, "expression") else "unknown"
        return f"""
**Error Type**: Template Rendering Error

**What happened**: Unable to resolve the template expression `${{{expr}}}` in the workflow configuration.

**Template Syntax**:
- `${{vars.key}}` - Access global variables from `spec.vars`
- `${{steps.stepId.outputs.key}}` - Access outputs from previous steps
- `${{attempt_result}}` - Access the raw result from the previous step
- `\\$` - Escape literal dollar sign

**Common Template Issues**:
1. **Referencing undefined variables**:
   - Ensure the variable is defined in `spec.vars`
   - Example: `${{vars.query}}` requires `vars: {{ query: "..." }}`

2. **Referencing outputs from steps not yet executed**:
   - Can only reference outputs from steps that have already run
   - Check step execution order (use `needs` to ensure dependencies)

3. **Typos in step IDs or output keys**:
   - Verify step ID spelling: `${{steps.gather_context.outputs.files}}`
   - Ensure the output key was defined in that step's `outputs` section

4. **Wrong template path structure**:
   - Must follow exact format: `steps.<step_id>.outputs.<output_key>`

**Quick Fix**:
1. Review the context keys available (shown in error message)
2. Verify the referenced step has executed before this step
3. Check the `outputs` section of the referenced step
4. Ensure proper nesting: `steps` → `step_id` → `outputs` → `key`

**Example of correct template usage**:
```yaml
steps:
  - id: gather
    outputs:
      files: "${{attempt_result}}"  # Save the result
  
  - id: implement
    needs: [gather]  # Ensure 'gather' runs first
    with:
      user_input: "Process these files: ${{steps.gather.outputs.files}}"
```
"""

    else:
        # 通用错误反馈
        return f"""
**Error Type**: {error_type}

**What happened**: An error occurred while executing the workflow '{workflow_name}'.

**Error Details**: {str(error)}

**General Troubleshooting Steps**:
1. **Review the error message** carefully for specific details
2. **Check the workflow YAML** configuration for common issues:
   - Syntax errors (indentation, missing colons, quotes)
   - Missing required fields
   - Invalid enum values
   - Type mismatches

3. **Validate step by step**:
   - Verify each agent is defined
   - Check all step dependencies are valid
   - Ensure template expressions are correct

4. **Use diagnostic tools**:
   - Use `load_extra_document` tool with name 'workflow_subagents' to see the specification
   - Review working workflow examples
   - Enable debug logging to see detailed execution flow

5. **Simplify and test**:
   - Start with a minimal workflow (1-2 steps)
   - Test each component individually
   - Gradually add complexity

**Need Help?**:
- Check the workflow documentation for examples
- Review error message structure for specific guidance
- Use load_extra_document tool to get the workflow YAML specification
"""


class ExecuteWorkflowToolResolver(BaseToolResolver):
    """执行 Workflow 工具解析器

    参考 terminal/command_processor.py 中 handle_workflow 的逻辑，
    调用 run_workflow_from_yaml 来执行指定名称的 workflow。
    """

    def __init__(
        self,
        agent: Optional["AgenticEdit"],
        tool: ExecuteWorkflowTool,
        args: AutoCoderArgs,
    ):
        super().__init__(agent, tool, args)
        self.tool: ExecuteWorkflowTool = tool

    def resolve(self) -> ToolResult:
        try:
            from autocoder.workflow_agents.runner import (
                run_workflow_from_yaml,
                print_workflow_result,
                list_available_workflows,
            )

            workflow_name = self.tool.name.strip()
            source_dir = self.args.source_dir or "."

            # 解析 vars_override
            vars_override = None
            if self.tool.vars_override:
                try:
                    vars_override = json.loads(self.tool.vars_override)
                    if not isinstance(vars_override, dict):
                        return ToolResult(
                            success=False,
                            message=f"vars_override must be a JSON object, got: {type(vars_override).__name__}",
                        )
                except json.JSONDecodeError as e:
                    return ToolResult(
                        success=False,
                        message=f"Invalid JSON in vars_override: {str(e)}",
                    )

            # 调用 run_workflow_from_yaml（参考 handle_workflow）
            logger.info(
                f"Executing workflow: {workflow_name} with vars_override={vars_override}"
            )

            result = run_workflow_from_yaml(
                yaml_path=workflow_name,
                source_dir=source_dir,
                vars_override=vars_override,
                cancel_token=None,  # 由外层 agent 管理 cancel
            )

            # 构建可读的结果消息
            if result.success:
                message_lines = [f"✅ Workflow '{workflow_name}' executed successfully"]
                message_lines.append(
                    f"Total steps: {len(result.step_results)}, Success: {sum(1 for s in result.step_results if s.status.value == 'success')}"
                )

                # 添加每个步骤的简要信息
                for step_result in result.step_results:
                    status_icon = (
                        "✅"
                        if step_result.status.value == "success"
                        else ("❌" if step_result.status.value == "failed" else "⏭️")
                    )
                    message_lines.append(
                        f"  {status_icon} {step_result.step_id}: {step_result.status.value}"
                    )
                    if step_result.error:
                        message_lines.append(f"     Error: {step_result.error}")

                message = "\n".join(message_lines)

                # content 包含详细的结构化结果
                content = {
                    "workflow_name": workflow_name,
                    "success": result.success,
                    "step_count": len(result.step_results),
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "status": s.status.value,
                            "error": s.error,
                            "attempt_result": s.attempt_result,
                            "outputs": s.outputs,
                        }
                        for s in result.step_results
                    ],
                    "context": result.context,
                }

                return ToolResult(success=True, message=message, content=content)
            else:
                # 失败情况
                error_msg = result.error or "Unknown error"
                message_lines = [f"❌ Workflow '{workflow_name}' failed: {error_msg}"]

                # 列出可用的 workflow（帮助用户找到正确的名称）
                if "未找到 workflow" in error_msg or "not found" in error_msg.lower():
                    message_lines.append("\nAvailable workflows:")
                    workflows = list_available_workflows(source_dir)
                    if workflows:
                        for name, path in workflows.items():
                            message_lines.append(f"  - {name}: {path}")
                    else:
                        message_lines.append("  (no workflows found)")

                message = "\n".join(message_lines)

                # 生成错误反馈指导（如果错误来自workflow异常）
                feedback = None
                try:
                    # 尝试从 result.error 中提取原始异常
                    # 注意：这里需要在 runner.py 中传递原始异常对象，或者根据错误消息判断类型
                    # 当前简化处理：根据错误消息关键词生成反馈
                    if (
                        "未找到 workflow" in error_msg
                        or "not found" in error_msg.lower()
                    ):
                        from autocoder.workflow_agents.exceptions import (
                            WorkflowFileNotFoundError,
                        )

                        dummy_error = WorkflowFileNotFoundError(workflow_name)
                        feedback = _generate_error_feedback(dummy_error, workflow_name)
                    elif (
                        "解析" in error_msg
                        or "parse" in error_msg.lower()
                        or "yaml" in error_msg.lower()
                    ):
                        from autocoder.workflow_agents.exceptions import (
                            WorkflowParseError,
                        )

                        dummy_error = WorkflowParseError(
                            workflow_name, Exception(error_msg)
                        )
                        feedback = _generate_error_feedback(dummy_error, workflow_name)
                    elif "循环依赖" in error_msg or "circular" in error_msg.lower():
                        from autocoder.workflow_agents.exceptions import (
                            WorkflowDependencyError,
                        )

                        dummy_error = WorkflowDependencyError(error_msg)
                        feedback = _generate_error_feedback(dummy_error, workflow_name)
                except Exception:
                    pass  # 忽略反馈生成错误

                return ToolResult(
                    success=False,
                    message=message,
                    content={
                        "workflow_name": workflow_name,
                        "error": error_msg,
                        "feedback": feedback,  # 添加反馈指导
                        "step_results": [
                            {
                                "step_id": s.step_id,
                                "status": s.status.value,
                                "error": s.error,
                            }
                            for s in result.step_results
                        ],
                    },
                )

        except Exception as e:
            logger.exception(f"ExecuteWorkflowTool failed: {e}")

            # 生成错误反馈指导
            feedback = _generate_error_feedback(e, self.tool.name)

            return ToolResult(
                success=False,
                message=f"Workflow execution error: {str(e)}",
                content={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "feedback": feedback,  # 添加反馈指导
                },
            )
