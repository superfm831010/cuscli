"""
Subagent Workflow 执行器

负责加载 workflow 配置、执行拓扑排序、运行各个步骤。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import threading
from loguru import logger

from autocoder.common import AutoCoderArgs
from autocoder.common.agents import AgentManager, AgentParser
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditConversationConfig,
    ConversationAction,
)
from autocoder.common.conversations.get_conversation_manager import (
    get_conversation_manager,
    copy_conversation,
)
from autocoder.utils.llms import get_single_llm
from autocoder.workflow_agents.types import (
    WorkflowSpec,
    StepSpec,
    AgentSpec,
    StepResult,
    StepStatus,
    WorkflowResult,
)
from autocoder.workflow_agents.agent import WorkflowSubAgent
from autocoder.workflow_agents.utils import (
    render_template,
    evaluate_condition,
    extract_outputs,
)
from autocoder.common.llms import LLMManager
from autocoder.common.international import get_message, get_message_with_format
from autocoder.workflow_agents.exceptions import (
    WorkflowDependencyError,
    WorkflowAgentNotFoundError,
    WorkflowModelValidationError,
)
from autocoder.common.global_cancel import (
    global_cancel,
    CancelRequestedException,
)


class SubagentWorkflowExecutor:
    """
    Subagent Workflow 执行器

    负责编排和执行多个子代理，支持 DAG 拓扑排序、条件判断、输出映射等。
    """

    def __init__(
        self,
        workflow_spec: WorkflowSpec,
        args: AutoCoderArgs,
        llm: Any,
        cancel_token: Optional[str] = None,
    ) -> None:
        """
        初始化执行器

        Args:
            workflow_spec: Workflow 规格配置
            args: AutoCoderArgs 配置
            llm: LLM 实例
            cancel_token: 取消令牌，用于支持任务取消
        """
        self.workflow_spec = workflow_spec
        self.args = args
        self.llm = llm
        self.cancel_token = cancel_token

        # 解析配置
        self.spec = workflow_spec.spec
        self.agents: Dict[str, WorkflowSubAgent] = self._build_agents()
        self.steps: List[StepSpec] = self.spec.steps

        # 执行上下文
        self.context: Dict[str, Any] = {
            "vars": self.spec.vars,
            "steps": {},
            "_last_attempt_result": None,
        }

        # 会话管理（共享链路会话ID）
        self._conversation_id: Optional[str] = None

        # 执行结果
        self.step_results: List[StepResult] = []

        # LLM 缓存机制：按模型名缓存 LLM 实例
        # 初始化时将全局 LLM 放入缓存
        self._llm_cache: Dict[str, Any] = {args.model: llm}
        self._llm_cache_lock = threading.RLock()

        # LLM 管理器：用于验证模型存在性和密钥配置
        self._llm_manager = LLMManager()

    def _build_agents(self) -> Dict[str, WorkflowSubAgent]:
        """
        构建代理字典

        使用 AgentManager 加载 agent 定义，获取 system prompt、model、include_rules 等信息

        Returns:
            代理字典，key 为 agent_id
        """
        agents: Dict[str, WorkflowSubAgent] = {}
        agent_manager = AgentManager(project_root=str(self.args.source_dir))

        for agent_spec in self.spec.agents:
            agent_definition = self._load_agent_definition(agent_spec, agent_manager)
            agents[agent_spec.id] = self._create_sub_agent(agent_spec, agent_definition)

        return agents

    def _load_agent_definition(
        self, agent_spec: AgentSpec, agent_manager: AgentManager
    ) -> Tuple[str, Optional[str], bool]:
        """
        加载 agent 定义

        Args:
            agent_spec: agent 规格
            agent_manager: agent 管理器

        Returns:
            (system_prompt, model, include_rules)
        """
        agent_id = agent_spec.id
        base_dir = Path(".autocoderagents")
        prompt_path = base_dir / agent_spec.path

        # 首先尝试从 AgentManager 获取
        agent_definition = agent_manager.get_agent(agent_id)

        if agent_definition:
            logger.debug(
                f"从 AgentManager 加载代理 {agent_id}: model={agent_definition.model}, include_rules={agent_definition.include_rules}"
            )
            return (
                agent_definition.content,
                agent_spec.model or agent_definition.model,
                agent_definition.include_rules,
            )

        # 尝试直接解析文件
        if prompt_path.exists():
            try:
                agent_definition = AgentParser.parse_agent_file(prompt_path)
                logger.debug(f"从文件解析代理 {agent_id}: {prompt_path}")
                return (
                    agent_definition.content,
                    agent_spec.model or agent_definition.model,
                    agent_definition.include_rules,
                )
            except Exception as e:
                logger.warning(f"解析代理文件 {prompt_path} 失败: {e}，使用纯文本内容")
                return (
                    prompt_path.read_text(encoding="utf-8"),
                    agent_spec.model,
                    False,
                )

        # 文件不存在
        logger.warning(f"代理 {agent_id} 的提示词文件不存在: {prompt_path}")
        return ("", agent_spec.model, False)

    def _create_sub_agent(
        self, agent_spec: AgentSpec, agent_definition: Tuple[str, Optional[str], bool]
    ) -> WorkflowSubAgent:
        """
        创建子代理

        Args:
            agent_spec: agent 规格
            agent_definition: (system_prompt, model, include_rules)

        Returns:
            WorkflowSubAgent 实例
        """
        system_prompt, model, include_rules = agent_definition

        return WorkflowSubAgent(
            agent_id=agent_spec.id,
            model=model,
            system_prompt=system_prompt,
            runner_type=agent_spec.runner,
            include_rules=include_rules,
        )

    def _get_llm_for_model(
        self, model_name: Optional[str], step_id: str = None, agent_id: str = None
    ) -> Any:
        """
        根据模型名称获取 LLM 实例，支持缓存和验证

        Args:
            model_name: 模型名称，如果为 None 或与全局模型相同，返回全局 LLM
            step_id: 步骤 ID（用于错误提示）
            agent_id: 代理 ID（用于错误提示）

        Returns:
            LLM 实例

        Raises:
            WorkflowModelValidationError: 如果模型不存在或密钥未配置
            Exception: 如果模型初始化失败
        """
        # 未指定模型或与全局模型相同，使用全局 LLM
        if not model_name or model_name == self.args.model:
            logger.debug(f"使用全局 LLM: {self.args.model}")
            return self.llm

        # 验证模型存在性（新增✨）
        if not self._llm_manager.check_model_exists(model_name):
            logger.error(f"模型不存在: {model_name}")
            raise WorkflowModelValidationError.for_model_not_found(
                step_id=step_id or "unknown",
                agent_id=agent_id or "unknown",
                model=model_name,
            )

        # 验证模型密钥配置（新增✨）
        if not self._llm_manager.has_key(model_name):
            logger.error(f"模型未配置 API 密钥: {model_name}")
            raise WorkflowModelValidationError.for_key_missing(
                step_id=step_id or "unknown",
                agent_id=agent_id or "unknown",
                model=model_name,
            )

        # 检查缓存
        with self._llm_cache_lock:
            cached_llm = self._llm_cache.get(model_name)
            if cached_llm:
                logger.debug(f"使用缓存的 LLM: {model_name}")
                return cached_llm

            # 首次使用该模型，创建新的 LLM 实例
            logger.info(
                f"初始化新的 LLM 实例: model={model_name}, product_mode={self.args.product_mode}"
            )
            try:
                new_llm = get_single_llm(
                    model_names=model_name, product_mode=self.args.product_mode
                )
                self._llm_cache[model_name] = new_llm
                logger.debug(
                    f"LLM 缓存已更新，当前缓存模型: {list(self._llm_cache.keys())}"
                )
                return new_llm
            except Exception as e:
                logger.error(f"初始化 LLM 失败: model={model_name}, error={str(e)}")
                raise

    def _toposort(self) -> List[StepSpec]:
        """
        拓扑排序步骤

        Returns:
            排序后的步骤列表

        Raises:
            WorkflowDependencyError: 如果检测到循环依赖或依赖不存在
        """
        result: List[StepSpec] = []
        visited: Set[str] = set()
        visiting: Set[str] = set()
        id2step = {step.id: step for step in self.steps}

        # 用于追踪依赖链
        dependency_chain: List[str] = []

        def dfs(step_id: str) -> None:
            nonlocal dependency_chain

            if step_id in visited:
                return

            if step_id in visiting:
                # 循环依赖，构建依赖链
                cycle_start = dependency_chain.index(step_id)
                cycle = dependency_chain[cycle_start:] + [step_id]
                raise WorkflowDependencyError(
                    message=f"检测到循环依赖", step_id=step_id, dependency_chain=cycle
                )

            visiting.add(step_id)
            dependency_chain.append(step_id)

            step = id2step[step_id]
            for dep in step.needs:
                if dep not in id2step:
                    all_step_ids = list(id2step.keys())
                    raise WorkflowDependencyError(
                        message=f"步骤 '{step_id}' 依赖不存在的步骤: '{dep}'",
                        step_id=step_id,
                        dependency_chain=[step_id, f"{dep} (不存在)"],
                    )
                dfs(dep)

            dependency_chain.pop()
            visiting.remove(step_id)
            visited.add(step_id)
            result.append(step)

        try:
            for step in self.steps:
                dependency_chain = []  # 重置依赖链
                dfs(step.id)
        except WorkflowDependencyError:
            raise  # 重新抛出我们自己的异常

        return result

    def _get_conversation_config(
        self, step: StepSpec, set_current: bool = True
    ) -> Optional[AgenticEditConversationConfig]:
        """按新语义仅基于 action 与可选 conversation_id 构造配置

        Args:
            step: 步骤配置
            set_current: 是否设置为当前会话（并行执行时只有第一个副本需要设置）
        """
        action = self._get_action(step)
        conversation_id = self._resolve_conversation_id(
            step, action, set_current=set_current
        )

        return AgenticEditConversationConfig(
            action=ConversationAction(action),
            conversation_id=conversation_id,
        )

    def _get_action(self, step: StepSpec) -> str:
        """读取动作，默认来源于全局 default_action"""
        action = self.spec.conversation.default_action
        if step.conversation is not None and step.conversation.action:
            action = step.conversation.action
        return action

    def _resolve_conversation_id(
        self, step: StepSpec, action: str, set_current: bool = True
    ) -> Optional[str]:
        """基于 action 与可选 conversation_id（支持模板渲染）获取会话ID

        Args:
            step: 步骤配置
            action: 会话动作（new | resume | continue）
            set_current: 是否设置为当前会话并更新实例状态
                - True: 修改 self._conversation_id 并设置为全局 current（正常路径/首副本）
                - False: 并行副本模式，resume/continue 时拷贝当前会话获得独立副本

        Returns:
            会话 ID
        """
        conversation_manager = get_conversation_manager()

        # 1) 若步骤显式指定 conversation_id（需渲染），优先使用
        explicit_id = None
        if step.conversation is not None and step.conversation.conversation_id:
            try:
                explicit_id = str(
                    render_template(step.conversation.conversation_id, self.context)
                )
            except Exception:
                explicit_id = step.conversation.conversation_id

        if explicit_id:
            # resume/continue/new 都可使用外部传入ID；new时若需要强制新建则忽略此ID
            if action == "new":
                # new 强制新建新会话
                conv_id = conversation_manager.create_conversation(
                    name=self.workflow_spec.metadata.name,
                    description=self.workflow_spec.metadata.description,
                )
                if set_current:
                    self._conversation_id = conv_id
                    conversation_manager.set_current_conversation(conv_id)
                return conv_id
            else:
                # resume/continue 使用该ID
                if set_current:
                    # 首副本：直接使用该 ID
                    conv_id = explicit_id
                    self._conversation_id = conv_id
                    try:
                        conversation_manager.set_current_conversation(conv_id)
                    except Exception:
                        # 若不存在，则按 resume 兜底：创建并设置
                        conv_id = conversation_manager.create_conversation(
                            name=self.workflow_spec.metadata.name,
                            description=self.workflow_spec.metadata.description,
                        )
                        self._conversation_id = conv_id
                        conversation_manager.set_current_conversation(conv_id)
                    return conv_id
                else:
                    # 非首副本：拷贝该会话，获得独立副本
                    try:
                        conv_id = copy_conversation(
                            source_conversation_id=explicit_id,
                            new_name=f"{self.workflow_spec.metadata.name} (replica)",
                            copy_messages=True,
                            copy_metadata=True,
                        )
                        logger.debug(f"非首副本拷贝会话 {explicit_id} -> {conv_id}")
                        return conv_id
                    except Exception as e:
                        # 拷贝失败，创建新会话
                        logger.warning(f"拷贝会话失败: {e}，创建新会话")
                        return conversation_manager.create_conversation(
                            name=self.workflow_spec.metadata.name,
                            description=self.workflow_spec.metadata.description,
                        )

        # 2) 未显式指定ID，依据 action 与共享链路状态处理
        if action == "new":
            # 总是新建
            conv_id = conversation_manager.create_conversation(
                name=self.workflow_spec.metadata.name,
                description=self.workflow_spec.metadata.description,
            )
            if set_current:
                self._conversation_id = conv_id
                conversation_manager.set_current_conversation(conv_id)
            return conv_id

        # resume / continue：若已有共享ID则复用；否则从 current 获取，没有就新建
        # 首先确定基准会话 ID
        base_conv_id = self._conversation_id
        if not base_conv_id:
            base_conv_id = conversation_manager.get_current_conversation_id()

        if base_conv_id:
            if set_current:
                # 首副本：直接使用
                self._conversation_id = base_conv_id
                return base_conv_id
            else:
                # 非首副本：拷贝会话，获得独立副本
                try:
                    conv_id = copy_conversation(
                        source_conversation_id=base_conv_id,
                        new_name=f"{self.workflow_spec.metadata.name} (replica)",
                        copy_messages=True,
                        copy_metadata=True,
                    )
                    logger.debug(f"非首副本拷贝会话 {base_conv_id} -> {conv_id}")
                    return conv_id
                except Exception as e:
                    # 拷贝失败，创建新会话
                    logger.warning(f"拷贝会话失败: {e}，创建新会话")
                    return conversation_manager.create_conversation(
                        name=self.workflow_spec.metadata.name,
                        description=self.workflow_spec.metadata.description,
                    )

        # 无当前会话则新建
        conv_id = conversation_manager.create_conversation(
            name=self.workflow_spec.metadata.name,
            description=self.workflow_spec.metadata.description,
        )
        if set_current:
            self._conversation_id = conv_id
            conversation_manager.set_current_conversation(conv_id)
        return conv_id

    def run(self) -> WorkflowResult:
        """
        执行 workflow

        Returns:
            WorkflowResult 对象，包含执行状态和所有步骤的结果
        """
        try:
            sorted_steps = self._toposort()
        except WorkflowDependencyError as e:
            error_msg = str(e)
            logger.error(error_msg)
            return WorkflowResult(
                success=False, context=self.context, step_results=[], error=error_msg
            )
        except Exception as e:
            error_msg = get_message_with_format(
                "workflow.exec_toposort_failed", error=str(e)
            )
            logger.error(error_msg, exc_info=True)
            return WorkflowResult(
                success=False, context=self.context, step_results=[], error=error_msg
            )

        logger.info(f"开始执行 workflow: {self.workflow_spec.metadata.name}")

        for step in sorted_steps:
            # 在执行每个步骤之前检查取消状态
            if self.cancel_token and global_cancel.is_requested(self.cancel_token):
                logger.info(f"检测到取消请求，中止 workflow 执行")
                # 将剩余步骤标记为取消
                remaining_steps = sorted_steps[sorted_steps.index(step) :]
                for remaining_step in remaining_steps:
                    self.step_results.append(
                        StepResult(
                            step_id=remaining_step.id,
                            status=StepStatus.CANCELLED,
                            error="Workflow execution was cancelled by user",
                        )
                    )
                return WorkflowResult(
                    success=False,
                    context=self.context,
                    step_results=self.step_results,
                    error="Workflow execution was cancelled by user",
                )

            step_result = self._execute_step(step)
            self.step_results.append(step_result)

            # 如果步骤被取消，停止执行后续步骤
            if step_result.status == StepStatus.CANCELLED:
                logger.info(f"步骤 {step.id} 被取消，中止后续步骤执行")
                # 将剩余步骤标记为取消
                current_idx = sorted_steps.index(step)
                for remaining_step in sorted_steps[current_idx + 1 :]:
                    self.step_results.append(
                        StepResult(
                            step_id=remaining_step.id,
                            status=StepStatus.CANCELLED,
                            error="Skipped due to workflow cancellation",
                        )
                    )
                return WorkflowResult(
                    success=False,
                    context=self.context,
                    step_results=self.step_results,
                    error="Workflow execution was cancelled by user",
                )

            # 如果步骤失败，可以选择是否继续（目前继续执行）
            if step_result.status == StepStatus.FAILED:
                logger.warning(f"步骤 {step.id} 失败，但继续执行后续步骤")

        # 判断整体是否成功
        failed_steps = [r for r in self.step_results if r.status == StepStatus.FAILED]
        success = len(failed_steps) == 0

        logger.info(
            f"Workflow 执行完成: 总步骤={len(self.step_results)}, "
            f"成功={len([r for r in self.step_results if r.status == StepStatus.SUCCESS])}, "
            f"失败={len(failed_steps)}, "
            f"跳过={len([r for r in self.step_results if r.status == StepStatus.SKIPPED])}"
        )

        return WorkflowResult(
            success=success,
            context=self.context,
            step_results=self.step_results,
            error=(
                None
                if success
                else get_message_with_format(
                    "workflow.exec_failed_steps_count", n=len(failed_steps)
                )
            ),
        )

    def _execute_step(self, step: StepSpec) -> StepResult:
        """
        执行单个步骤

        Args:
            step: 步骤规格

        Returns:
            StepResult 对象
        """
        logger.info(f"执行步骤: {step.id}")

        # 在执行步骤之前检查取消状态
        if self.cancel_token and global_cancel.is_requested(self.cancel_token):
            logger.info(f"步骤 {step.id} 执行前检测到取消请求")
            return StepResult(
                step_id=step.id,
                status=StepStatus.CANCELLED,
                error="Step cancelled before execution",
            )

        # 评估条件
        attempt_prev = self.context.get("_last_attempt_result")
        if not evaluate_condition(step.when, attempt_prev, self.context):
            logger.info(f"步骤 {step.id} 的条件不满足，跳过")
            return StepResult(step_id=step.id, status=StepStatus.SKIPPED)

        # 检查代理是否存在
        agent_id = step.agent
        if agent_id not in self.agents:
            available_agents = list(self.agents.keys())
            error = WorkflowAgentNotFoundError(
                agent_id=agent_id, step_id=step.id, available_agents=available_agents
            )
            error_msg = str(error)
            logger.error(error_msg)
            return StepResult(
                step_id=step.id, status=StepStatus.FAILED, error=error_msg
            )

        # 检查是否需要并行执行
        if step.replicas > 1:
            return self._execute_step_parallel(step)
        else:
            return self._execute_step_single(step)

    def _execute_step_single(self, step: StepSpec) -> StepResult:
        """
        执行单个步骤（非并行）

        Args:
            step: 步骤规格

        Returns:
            StepResult 对象
        """
        try:
            # 渲染用户输入
            user_input = render_template(
                step.with_args.get("user_input", ""), self.context
            )
            if not isinstance(user_input, str):
                user_input = str(user_input)

            # 获取会话配置
            conversation_config = self._get_conversation_config(step)

            # 获取该 agent 专属的 LLM（如果 agent 指定了模型）
            agent = self.agents[step.agent]
            agent_llm = self._get_llm_for_model(
                agent.model, step_id=step.id, agent_id=step.agent
            )

            # 记录使用的模型
            if agent.model and agent.model != self.args.model:
                logger.info(
                    f"步骤 {step.id} (agent={step.agent}) 使用 agent 专属模型: {agent.model}"
                )

            # 运行代理
            completion = agent.run(
                user_input=user_input,
                conversation_config=conversation_config,
                args=self.args,
                llm=agent_llm,
                cancel_token=self.cancel_token,
            )

            # 处理结果
            if completion is None:
                error_msg = get_message("workflow.exec_agent_no_result")
                logger.warning(f"步骤 {step.id} {error_msg}")
                return StepResult(
                    step_id=step.id, status=StepStatus.FAILED, error=error_msg
                )

            attempt_result = completion.result
            logger.debug(f"步骤 {step.id} 完成，结果长度: {len(attempt_result)}")

            self.context["_last_attempt_result"] = attempt_result

            # 提取输出
            outputs = extract_outputs(
                outputs_map=step.outputs,
                attempt_result=attempt_result,
                attempt_format=self.spec.attempt.format,
                default_jsonpaths=self.spec.attempt.jsonpaths,
                context=self.context,
            )

            # 注入内置变量：conversation_id（强制覆盖以避免模板字面量泄漏）
            outputs["conversation_id"] = self._conversation_id

            # 保存到上下文
            if step.id not in self.context["steps"]:
                self.context["steps"][step.id] = {"outputs": {}}

            self.context["steps"][step.id]["outputs"].update(outputs)
            logger.debug(f"步骤 {step.id} 输出: {list(outputs.keys())}")

            return StepResult(
                step_id=step.id,
                status=StepStatus.SUCCESS,
                attempt_result=attempt_result,
                outputs=outputs,
            )

        except CancelRequestedException:
            logger.info(f"步骤 {step.id} 执行过程中被取消")
            return StepResult(
                step_id=step.id,
                status=StepStatus.CANCELLED,
                error="Step cancelled during execution",
            )
        except Exception as e:
            error_msg = get_message_with_format("workflow.exec_exception", error=str(e))
            logger.error(f"步骤 {step.id} {error_msg}", exc_info=True)
            return StepResult(
                step_id=step.id, status=StepStatus.FAILED, error=error_msg
            )

    def _execute_step_parallel(self, step: StepSpec) -> StepResult:
        """
        并行执行单个步骤的多个副本

        Args:
            step: 步骤规格

        Returns:
            StepResult 对象，包含合并后的结果
        """
        logger.info(f"步骤 {step.id} 将并行执行 {step.replicas} 个副本")

        # 在执行之前检查取消状态
        if self.cancel_token and global_cancel.is_requested(self.cancel_token):
            logger.info(f"步骤 {step.id} 并行执行前检测到取消请求")
            return StepResult(
                step_id=step.id,
                status=StepStatus.CANCELLED,
                error="Step cancelled before parallel execution",
            )

        # 渲染用户输入（所有副本使用相同输入）
        try:
            user_input = render_template(
                step.with_args.get("user_input", ""), self.context
            )
            if not isinstance(user_input, str):
                user_input = str(user_input)
        except Exception as e:
            error_msg = get_message_with_format(
                "workflow.exec_render_input_failed", error=str(e)
            )
            logger.error(f"步骤 {step.id} {error_msg}", exc_info=True)
            return StepResult(
                step_id=step.id, status=StepStatus.FAILED, error=error_msg
            )

        # 并行执行所有副本
        agent = self.agents[step.agent]
        # 获取该 agent 专属的 LLM（如果 agent 指定了模型）
        agent_llm = self._get_llm_for_model(
            agent.model, step_id=step.id, agent_id=step.agent
        )

        # 记录使用的模型
        if agent.model and agent.model != self.args.model:
            logger.info(
                f"步骤 {step.id} (agent={step.agent}) 使用 agent 专属模型: {agent.model}"
            )

        results = []
        errors = []

        # 用于存储每个副本的会话 ID
        replica_conversation_ids: Dict[int, Optional[str]] = {}
        # 用于保护 conversation_id 的锁
        conv_lock = threading.Lock()

        def run_replica(replica_idx: int):
            """运行单个副本"""
            try:
                logger.info(
                    f"步骤 {step.id} 副本 {replica_idx + 1}/{step.replicas} 开始执行"
                )

                # 只有第一个副本设置 current 会话，避免并发时 current 抖动
                is_first_replica = replica_idx == 0

                # 获取会话配置
                # 注意：每个副本需要独立获取会话配置，避免竞态条件
                with conv_lock:
                    conversation_config = self._get_conversation_config(
                        step, set_current=is_first_replica
                    )
                    # 记录当前副本使用的会话 ID（从 conversation_config 获取，而非实例状态）
                    replica_conv_id = conversation_config.conversation_id
                    replica_conversation_ids[replica_idx] = replica_conv_id

                # 决定 runner_type：只有第一个副本（replica_idx=0）使用原配置的 runner
                # 其他副本强制使用 SdkRunner，避免控制台输出交错
                override_runner_type = None  # 使用 agent 默认配置
                if not is_first_replica:
                    override_runner_type = "sdk"
                    logger.debug(
                        f"步骤 {step.id} 副本 {replica_idx + 1} 使用 SdkRunner（避免输出交错）"
                    )

                # 运行代理（使用 agent 专属的 LLM）
                completion = agent.run(
                    user_input=user_input,
                    conversation_config=conversation_config,
                    args=self.args,
                    llm=agent_llm,
                    cancel_token=self.cancel_token,
                    runner_type=override_runner_type,
                )

                if completion is None:
                    return (
                        replica_idx,
                        None,
                        get_message("workflow.exec_agent_no_result"),
                    )

                logger.info(
                    f"步骤 {step.id} 副本 {replica_idx + 1}/{step.replicas} 执行完成"
                )
                return (replica_idx, completion.result, None)

            except CancelRequestedException:
                logger.info(
                    f"步骤 {step.id} 副本 {replica_idx + 1}/{step.replicas} 被取消"
                )
                return (replica_idx, None, "cancelled")

            except Exception as e:
                error_msg = get_message_with_format(
                    "workflow.exec_replica_exception",
                    idx=replica_idx + 1,
                    error=str(e),
                )
                logger.error(f"步骤 {step.id} {error_msg}", exc_info=True)
                return (replica_idx, None, error_msg)

        # 用于追踪是否有取消请求
        cancelled = False

        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=step.replicas) as executor:
            futures = [executor.submit(run_replica, i) for i in range(step.replicas)]

            for future in as_completed(futures):
                replica_idx, result, error = future.result()
                if error:
                    if error == "cancelled":
                        cancelled = True
                    errors.append(f"副本 {replica_idx + 1}: {error}")
                else:
                    results.append((replica_idx, result))

        # 如果检测到取消请求，返回取消状态
        if cancelled and not results:
            logger.info(f"步骤 {step.id} 所有副本都被取消")
            return StepResult(
                step_id=step.id,
                status=StepStatus.CANCELLED,
                error="All replicas were cancelled",
            )

        # 判断成功：任意一个成功即可（any-success 策略）
        if not results:
            # 全部失败
            error_msg = get_message_with_format(
                "workflow.exec_all_replicas_failed",
                n=step.replicas,
                errors="; ".join(errors),
            )
            logger.error(f"步骤 {step.id} {error_msg}")
            return StepResult(
                step_id=step.id, status=StepStatus.FAILED, error=error_msg
            )

        # 至少有一个成功
        logger.info(f"步骤 {step.id} 成功执行了 {len(results)}/{step.replicas} 个副本")

        # 使用第一个成功副本的会话作为链路会话
        # 按副本索引排序，取第一个成功副本的会话 ID
        sorted_results = sorted(results, key=lambda x: x[0])
        first_success_replica_idx = sorted_results[0][0]
        first_success_conv_id = replica_conversation_ids.get(first_success_replica_idx)

        if first_success_conv_id:
            self._conversation_id = first_success_conv_id
            conversation_manager = get_conversation_manager()
            conversation_manager.set_current_conversation(first_success_conv_id)
            logger.info(
                f"步骤 {step.id} 使用副本 {first_success_replica_idx + 1} 的会话作为链路会话: {first_success_conv_id}"
            )

        # 过滤结果（根据 merge.when 条件）
        filtered_results = self._filter_replica_results(results, step)

        if not filtered_results:
            # 所有结果都被过滤掉了
            error_msg = get_message_with_format(
                "workflow.exec_all_filtered", n=len(results)
            )
            logger.error(f"步骤 {step.id} {error_msg}")
            return StepResult(
                step_id=step.id, status=StepStatus.FAILED, error=error_msg
            )

        if len(filtered_results) < len(results):
            logger.info(
                f"步骤 {step.id} 有 {len(filtered_results)}/{len(results)} 个副本通过合并条件"
            )

        # 合并结果
        merged_result = self._merge_replica_results(filtered_results, step)

        # 更新上下文
        self.context["_last_attempt_result"] = merged_result

        # 提取输出（从合并后的结果中提取）
        try:
            outputs = extract_outputs(
                outputs_map=step.outputs,
                attempt_result=merged_result,
                attempt_format=self.spec.attempt.format,
                default_jsonpaths=self.spec.attempt.jsonpaths,
                context=self.context,
            )
        except Exception as e:
            logger.warning(f"步骤 {step.id} 提取输出失败: {e}，使用空输出")
            outputs = {}

        # 注入内置变量：conversation_id
        outputs["conversation_id"] = self._conversation_id

        # 保存到上下文
        if step.id not in self.context["steps"]:
            self.context["steps"][step.id] = {"outputs": {}}

        self.context["steps"][step.id]["outputs"].update(outputs)
        logger.debug(f"步骤 {step.id} 输出: {list(outputs.keys())}")

        return StepResult(
            step_id=step.id,
            status=StepStatus.SUCCESS,
            attempt_result=merged_result,
            outputs=outputs,
        )

    def _filter_replica_results(
        self, results: List[Tuple[int, str]], step: StepSpec
    ) -> List[Tuple[int, str]]:
        """
        根据 merge.when 条件过滤副本结果

        只有满足条件的副本结果才会参与最终合并。

        Args:
            results: [(replica_idx, attempt_result), ...]
            step: 步骤规格

        Returns:
            过滤后的结果列表
        """
        # 如果没有配置 merge.when，返回所有结果
        if not step.merge or not step.merge.when:
            return results

        filtered = []
        for replica_idx, result in results:
            # 评估条件：input 为空时，evaluate_condition 会使用 attempt_result 作为输入
            if evaluate_condition(step.merge.when, result, self.context):
                filtered.append((replica_idx, result))
                logger.debug(f"步骤 {step.id} 副本 {replica_idx + 1} 通过合并条件")
            else:
                logger.info(
                    f"步骤 {step.id} 副本 {replica_idx + 1} 未通过合并条件，不参与合并"
                )

        return filtered

    def _merge_replica_results(
        self, results: List[Tuple[int, str]], step: StepSpec
    ) -> str:
        """
        合并多个副本的结果

        Args:
            results: [(replica_idx, attempt_result), ...]
            step: 步骤规格

        Returns:
            合并后的结果字符串
        """
        # 按副本索引排序
        sorted_results = sorted(results, key=lambda x: x[0])
        attempt_results = [result for _, result in sorted_results]

        # 根据 attempt.format 决定合并方式
        if self.spec.attempt.format == "json":
            # JSON 格式：尝试将多个结果打包成 JSON 数组
            json_objects = []
            for result in attempt_results:
                try:
                    obj = json.loads(result)
                    json_objects.append(obj)
                except json.JSONDecodeError:
                    # 如果解析失败，保留原始字符串
                    json_objects.append({"raw": result})

            # 返回 JSON 数组字符串
            return json.dumps(json_objects, ensure_ascii=False, indent=2)
        else:
            # Text 格式：用分隔符拼接
            separator = "\n---\n"
            return separator.join(attempt_results)
