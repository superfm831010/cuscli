from typing import Optional
from pathlib import Path
import byzerllm
from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import (
    BaseToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import (
    ToolResult,
    LoadExtraDocumentTool,
)
from autocoder.common import AutoCoderArgs
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


@byzerllm.prompt()
def _workflow_subagents() -> str:
    """
    ### Subagent Workflow YAML Specification (Action-based Conversation Semantics)

    This document defines the YAML specification for Auto-Coder Subagent Workflows (SubagentWorkflow) and provides authoring guidelines and examples.

    ---

    ## Top-level Structure

    ```yaml
    apiVersion: autocoder/v1       # fixed
    kind: SubagentWorkflow         # fixed
    metadata:
    name: coder                  # Workflow name; must match the filename
    description: "Description"
    spec:
    globals:                     # Global default configuration
        model: v3_chat             # Default model
        product_mode: lite         # Product mode (e.g., lite)
        timeout_sec: 300           # Default timeout (seconds)
        include_rules: false       # Whether the runner includes rule context

    vars:                        # Optional, global template variables
        project_type: "*"

    conversation:                # Global conversation policy (simplified)
        start: current             # current | new; when current and none exists, auto-create
        default_action: resume     # resume | new | continue; used when a step doesn't specify

    attempt:                     # AttemptCompletion return contract
        format: text               # json | text
        # jsonpaths:               # When format=json, default extraction paths (optional)
        #   files: "$.files"
        #   reasoning: "$.reasoning"

    agents:                      # Agent definitions
        - id: context
        path: contexer.md        # From ./.autocoderagents/
        runner: terminal         # sdk | terminal
        # model/retry/timeout_sec optional

        - id: code
        path: code.md
        runner: terminal

    steps:                       # DAG steps, executed in topological order
        - id: step1
        agent: context
        conversation:
            action: new            # Start a new conversation and set it as the linked conversation
        with:
            user_input: "${vars.query}"
        outputs:                 # The system always injects conversation_id; no manual config needed
            attempt_raw: "${attempt_result}"

        - id: step2
        needs: [step1]
        agent: code
        conversation:
            action: resume         # Reuse the linked conversation (created by step1)
            # Optional: explicitly set conversation ID (templating supported)
            # conversation_id: "${steps.step1.outputs.conversation_id}"
        with:
            user_input: |
            Edit code based on these files: ${steps.step1.outputs.attempt_raw}
            Original request: ${vars.query}
        outputs:
            attempt_raw: "${attempt_result}"
    ```

    ---

    ## Field Descriptions

    - metadata
    - name: workflow name
    - description: description

    - spec.globals (defaults; can be overridden per agent)
    - model: default model (e.g., v3_chat)
    - product_mode: product mode (e.g., lite)
    - timeout_sec, include_rules: runtime parameters

    - spec.vars: dictionary of template variables, referenced via `${vars.key}`

    - spec.conversation (global)
    - start: current | new; when current and there is no "current conversation", a new one is auto-created
    - default_action: resume | new | continue; used as the default step-level action

    - spec.attempt
    - format: text | json; when json, `jsonpaths` can configure default extraction

    - spec.agents[]
    - id: agent identifier
    - path: prompt path relative to `./.autocoderagents/`
    - runner: sdk | terminal
    - model/retry/timeout_sec: optional

    - spec.steps[]
    - id: step ID (unique)
    - agent: reference to `agents[].id`
    - needs: list of dependencies
    - replicas: optional, number of parallel replicas (default: 1)
        - When replicas > 1, the step runs multiple identical copies in parallel
        - Success policy: any replica succeeds → step succeeds
        - Result merging:
          - JSON format: merges into a JSON array `[{...}, {...}]`
          - Text format: concatenates with `\n---\n` separator
        - Unset or 1: behaves as before (backward compatible)
    - conversation: step-level conversation control
        - action: new | resume | continue
        - new: always starts a new conversation and sets it as the "linked conversation" (subsequent resume will reuse it)
        - resume: reuse the "current linked conversation"; if none, try reusing the "current conversation", otherwise start a new one
        - continue: currently equivalent to resume (reserved for lightweight history strategy)
        - conversation_id: optional, supports templating
        - If set and action is resume/continue: use this ID as the linked conversation; if the ID does not exist, a new conversation will be created
        - If action=new: this field is ignored and a new conversation is forced
    - with
        - user_input: input passed to the Runner (string; supports templating)
    - when: optional condition
        - regex: `{ input, pattern, [flags], [group] }`
        - jsonpath: `{ input, path, [exists], [equals], [contains] }`
    - outputs: map AttemptCompletion result into structured outputs
        - When format=json, you can use `jsonpath`
        - When format=text, you can use `regex`
        - You can also directly pass through "${attempt_result}"
        - The system automatically injects `conversation_id` into each step's outputs, and it is a real conversation ID; even if you explicitly write `conversation_id`, it will be overwritten with the real value

    ---

    ## Template Syntax

    Templates are supported in fields such as `with.user_input`, `when.*.input`, `conversation.conversation_id`, etc.:

    - `${vars.key}`: reference a global variable
    - `${steps.stepId.outputs.key}`: reference a previous step’s outputs
    - `${attempt_result}`: reference the raw string result of the last AttemptCompletion
    - Escape `$`: use `\\$`

    Note: If you need to pass a conversation ID, use `${steps.prev.outputs.conversation_id}` (the real ID injected by the system from the previous step). Do not use a bare `${conversation_id}`.

    ---

    ## Common Authoring Patterns

    1) Two-step chain sharing the same conversation
    ```yaml
    steps:
    - id: s1
        agent: context
        conversation:
        action: new
        with:
        user_input: "${vars.query}"

    - id: s2
        needs: [s1]
        agent: code
        conversation:
        action: resume   # Automatically reuse the linked conversation created by s1
        with:
        user_input: "Based on these files: ${steps.s1.outputs.attempt_raw}"
    ```

    2) Explicitly passing the conversation ID (cross-branch/cross-step references)
    ```yaml
    steps:
    - id: gather
        agent: context
        conversation:
        action: new

    - id: write
        needs: [gather]
        agent: code
        conversation:
        action: resume
        conversation_id: "${steps.gather.outputs.conversation_id}"
    ```

    3) Resetting the conversation mid-way (isolating context)
    ```yaml
    steps:
    - id: a
        agent: context
        conversation:
        action: new

    - id: b
        needs: [a]
        agent: code
        conversation:
        action: new   # Isolated from a’s conversation; start fresh
    ```

    ---

    ## Practical Tips

    - You usually do not need to manually add `conversation_id` in `outputs`; the system injects it and guarantees it is the real value.
    - When you want to strictly continue from the previous step’s conversation, prefer `action: resume`. If you need to explicitly bind to a specific conversation, set `conversation_id` in this step to `${steps.prev.outputs.conversation_id}`.
    - `action: new` resets the linked conversation (subsequent resume will refer to this newly created one).
    - Global `conversation.start=current` means it prefers the "current conversation"; when none exists the system will automatically create one and set it as current.

    ---

    ## Typical Working Example

    ```yaml
    apiVersion: autocoder/v1
    kind: SubagentWorkflow
    metadata:
    name: coder
    description: "Two agents—context discovery and code writing—cooperate to turn a coding request into file paths and editing operations"
    spec:
    globals:
        model: v3_chat            # Default model; can be overridden per agent
        product_mode: lite        # Default product mode
        include_rules: false      # Whether to include rules context in SdkRunner

    vars:                       # Optional: global variables for templating
        project_type: "*"

    conversation:               # Conversation sharing policy (global)
        start: current            # current: inherit current conversation; new: create new (if none, fallback to create)
        default_action: resume    # resume | new | continue

    attempt:                    # AttemptCompletion return contract (global)
        format: text              # json | text

    agents:                     # Agents: each agent is a runner configuration (SdkRunner in this design)
        - id: context
        path: contexer.md       # Full path is ./.autocoderagents/context.md
        runner: terminal        # sdk/terminal

        - id: code
        path: code.md           # Full path is ./.autocoderagents/code.md
        runner: terminal        # sdk/terminal

    steps:                      # DAG, executed in topological order
        - id: gather_context
        agent: context
        replicas: 2             # Run 2 parallel replicas to improve context discovery coverage
        conversation:           # Keep only action; conversation_id also supports templating
            action: new
        with:                   # Input for TerminalRunner; becomes AgenticEditRequest.user_input
            user_input: |
            ${vars.query}
            ---
            [[REMINDER: You are in context discovery mode. Analyze the request above to identify relevant files, but DO NOT implement the request. Focus on thorough file discovery and understanding the codebase context.

            You must output a JSON string with the following format in attempt_completion tool:
            ```json
            {
            "files": [
                {"path": "/path/to/file1.py", "operation": "MODIFY"},
                {"path": "/path/to/file2.md", "operation": "REFERENCE"},
                {"path": "/path/to/new_file.txt", "operation": "ADD"},
                {"path": "/path/to/old_file.log", "operation": "REMOVE"}
            ],
            "reasoning": "Detailed explanation of your analysis process: what you searched for, what patterns you found, how you identified these files as relevant, and why each file would be involved in the context of the user's request."
            }
            ```
            Never stop unless you think you have found the enough files to satisfy the user's request.
            ]]
        outputs:                # Map AttemptCompletion to structured outputs for later steps
            attempt_raw: "${attempt_result}"
            conversation_id: "${conversation_id}"

        - id: write_code
        needs: [gather_context]
        agent: code
        conversation:
            action: new
            # conversation_id: "${steps.gather_context.outputs.conversation_id}"
        with:
            user_input: |
            Edit code based on these files: ${steps.gather_context.outputs.attempt_raw}
            Here is the user's original request:

            ${vars.query}

        outputs:
            attempt_raw: "${attempt_result}"
            conversation_id: "${conversation_id}"
    ```



    """


class LoadExtraDocumentToolResolver(BaseToolResolver):
    """加载内置额外文档（以 prompt 字符串形式返回）

    当前支持的文档：
    - workflow_subagents: Subagent Workflow YAML 规范与指导
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
