import byzerllm


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
    - model: optional, override the default model

    - spec.steps[]
    - id: step ID (unique)
    - agent: reference to `agents[].id`
    - needs: list of dependencies
    - replicas: optional, number of parallel replicas (default: 1)
        - When replicas > 1, the step runs multiple identical copies in parallel
        - Success policy: any replica succeeds → step succeeds
        - Console output: only the first replica uses TerminalRunner; others run silently with SdkRunner
        - Result merging:
          - JSON format: merges into a JSON array `[{...}, {...}]`
          - Text format: concatenates with `\n---\n` separator
        - Unset or 1: behaves as before (backward compatible)
        - Conversation management by action:
          - `action: new`: each replica creates an independent new conversation
          - `action: resume/continue`: first replica uses the linked conversation directly; other replicas copy the linked conversation (shared history, independent writes)
          - After completion: the first successful replica's conversation becomes the linked conversation for downstream steps
    - merge: optional, merge configuration for multi-replica steps
        - when: filter condition for replica results before merging
          - Only replica results that satisfy the condition participate in the merge
          - No `input` field needed; defaults to using the replica's `attempt_result`
          - Condition types: `jsonpath`, `text`, `regex` (reuses when syntax)
          - If all replicas fail the condition, the step fails
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
        - regex: `{ input, pattern, [flags] }`
        - jsonpath: `{ input, path, [exists], [equals], [contains] }`
        - text: `{ input, [contains], [not_contains], [starts_with], [ends_with], [equals], [not_equals], [is_empty], [matches], [ignore_case] }`
    - outputs: map AttemptCompletion result into structured outputs
        - When format=json, you can use `jsonpath`
        - When format=text, you can use `regex`
        - You can also directly pass through "${attempt_result}"
        - The system automatically injects `conversation_id` into each step's outputs, and it is a real conversation ID; even if you explicitly write `conversation_id`, it will be overwritten with the real value

    ---

    ## Template Syntax

    Templates are supported in fields such as `with.user_input`, `when.*.input`, `conversation.conversation_id`, etc.:

    - `${vars.key}`: reference a global variable
    - `${steps.stepId.outputs.key}`: reference a previous step's outputs
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
        action: new   # Isolated from a's conversation; start fresh
    ```

    4) Filtering replica results before merging (merge.when)
    ```yaml
    steps:
    - id: gather_context
        agent: context
        replicas: 3
        merge:
        when:
            jsonpath:
            path: "$.files"
            exists: true       # Only merge results that have a files field
        outputs:
        attempt_raw: "${attempt_result}"

    - id: analyze
        agent: analyzer
        replicas: 2
        merge:
        when:
            text:
            not_contains: "error"   # Exclude results containing "error"
    ```

    ---

    ## Practical Tips

    - You usually do not need to manually add `conversation_id` in `outputs`; the system injects it and guarantees it is the real value.
    - When you want to strictly continue from the previous step's conversation, prefer `action: resume`. If you need to explicitly bind to a specific conversation, set `conversation_id` in this step to `${steps.prev.outputs.conversation_id}`.
    - `action: new` resets the linked conversation (subsequent resume will refer to this newly created one).
    - Global `conversation.start=current` means it prefers the "current conversation"; when none exists the system will automatically create one and set it as current.

    ---

    ## Implementation Notes (Current Behavior)

    - The executor maintains a shared "linked conversation id" across steps.
      - `action: new` always creates a new conversation and sets it as both the current and linked conversation.
      - `action: resume` (and `action: continue`, currently equivalent) reuse the linked conversation if present; otherwise they try the current conversation, and if none exists, create a new one.
      - If `conversation_id` is explicitly provided with `resume/continue`, the executor attempts to use it as the linked conversation (creating one if the ID does not exist). With `new`, an explicit ID is ignored and a fresh conversation is created.
    - The system forcibly injects the real `conversation_id` into each step's outputs (overwriting any template literal), ensuring downstream steps can reliably reference it via `${steps.<id>.outputs.conversation_id}`.
    - Parallel replicas: each replica uses its own conversation when `action: new`. After the step, the executor's linked conversation reflects the last effective update; downstream `resume/continue` will reuse this linked conversation.
    - `conversation.start` is kept for backward compatibility and documentation clarity. The actual decision in the executor is governed by per-step `action` plus optional `conversation_id`, with `resume/continue` behavior naturally preferring the current conversation when no linked conversation exists.

    ---

    ## Agent Definition Format

    Each agent is defined as a markdown file in the `./.autocoderagents/` directory with the following structure:

    ### Agent File Format

    ```markdown
    ---
    name: agent_name                    # Agent identifier (must match the id in workflow)
    description: Brief description       # Agent purpose and capabilities
    tools: *                            # Available tools (* is ok)
    model: model_name                   # Model to use (e.g., v3_chat, openrouter/claude-sonnet-4-5)
    ---
    # Detailed Agent Instructions

    ## Role
    Define the agent's primary role and responsibilities

    ## Input
    Describe what input the agent will receive

    ## Output
    Specify the expected output format and content

    ## Core Responsibilities
    List the main tasks and responsibilities

    ## Tool Usage Guide
    Explain how to use available tools effectively

    ## Rules/Constraints
    Any specific rules or constraints the agent must follow
    ```

    ### Example Agent Definition

    Based on `.autocoderagents/contexer.md`:

    ```markdown
    ---
    name: contexer
    description: Project exploration and context discovery specialist. Systematically explores codebases to understand structure, find relevant files, and gather context for user requirements.
    tools: *
    model: v3_chat
    ---
    You are a context discovery assistant. Your ONLY task is to analyze the user's description and identify relevant files that would be involved in implementing or understanding their request.

    ## Core Responsibilities

    ### 1. Project Structure Understanding
    - Quickly analyze overall project architecture and organization
    - Identify the role of key directories and files
    - Understand project tech stack and dependencies

    ### 2. Requirement-Driven File Location
    - Analyze user requirements to understand what files would be involved
    - Locate existing code that implements similar or related functionality
    - Identify files that would need to be understood or potentially modified

    ## Output Format
    You must output a JSON string in the attempt_completion tool with this exact format:

    ```json
    {
    "files": [
        {"path": "/path/to/file1.py", "operation": "MODIFY"},
        {"path": "/path/to/file2.md", "operation": "REFERENCE"}
    ],
    "reasoning": "Detailed explanation of your analysis process..."
    }
    ```

    ## Tool Usage Guide

    ### Essential Tools
    - `ac_mod_list`: AC module discovery
    - `ac_mod_read`: View module information
    - `list_files`: Directory structure analysis
    - `search_files`: Content search
    - `execute_command` (grep): Precise pattern matching
    - `read_file`: Detailed code analysis
    ]]
    ```

    ### Agent File Requirements

    1. **Front Matter (YAML)**:
       - `name`: Agent identifier (required)
       - `description`: Brief description of agent's purpose (required)
       - `tools`: Tools available to agent (`*` for all tools, or specific tool names) (required)
       - `model`: Model to use for this agent (required)

    2. **Agent Instructions**:
       - Wrapped in `[[...]]` brackets
       - Contains detailed instructions for the agent
       - Should include role definition, input/output specifications, and usage guidelines
       - Can include examples and specific tool usage instructions

    3. **File Location**:
       - Must be placed in `./.autocoderagents/` directory
       - Filename must match the `path` specified in workflow agents section
       - File extension should be `.md`

    4. **Best Practices**:
       - Keep instructions clear and specific
       - Define expected output formats precisely
       - Include examples of tool usage
       - Specify any constraints or rules the agent must follow
       - Use structured sections with clear headings

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
            action: continue
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
