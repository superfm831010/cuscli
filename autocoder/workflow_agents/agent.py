"""
Workflow Sub-Agent 实现

提供基于 SdkRunner 和 TerminalRunner 的子代理执行能力。
"""

from typing import Optional, Union, Any
from copy import deepcopy
from loguru import logger

from autocoder.common.v2.agent.agentic_edit import AgenticEditRequest
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditConversationConfig,
    CompletionEvent,
    AttemptCompletionTool,
)
from autocoder.common.v2.agent.runner import SdkRunner, TerminalRunner
from autocoder.common import AutoCoderArgs
from autocoder.inner.agentic import RunAgentic
from autocoder.common.global_cancel import CancelRequestedException


class WorkflowSubAgent:
    """
    Workflow 子代理

    每个子代理对应一个特定的 agent 配置，支持使用 SdkRunner 或 TerminalRunner 执行用户输入。
    """

    def __init__(
        self,
        agent_id: str,
        model: Optional[str],
        system_prompt: Optional[str],
        runner_type: str = "sdk",
        include_rules: bool = False,
    ) -> None:
        """
        初始化子代理

        Args:
            agent_id: 代理 ID
            model: 模型名称（可选，使用全局默认）
            system_prompt: 系统提示词
            runner_type: 运行器类型（sdk | terminal）
            include_rules: 是否包含规则上下文
        """
        self.agent_id = agent_id
        self.model = model
        self.system_prompt = system_prompt
        self.runner_type = runner_type
        self.include_rules = include_rules

    def run(
        self,
        user_input: str,
        conversation_config: Optional[AgenticEditConversationConfig],
        args: AutoCoderArgs,
        llm: Any,
        cancel_token: Optional[str] = None,
        runner_type: Optional[str] = None,
    ) -> Optional[AttemptCompletionTool]:
        """
        运行子代理

        Args:
            user_input: 用户输入
            conversation_config: 会话配置
            args: AutoCoderArgs 配置
            llm: LLM 实例
            cancel_token: 取消令牌，用于支持任务取消
            runner_type: 运行器类型覆盖（sdk | terminal），如果为 None 则使用实例默认值

        Returns:
            AttemptCompletionTool 对象（两种 Runner 返回统一接口）
            如果失败则返回 None
        """
        try:
            # 深拷贝 args 避免修改原始对象
            agent_args = deepcopy(args)

            # 配置模型
            if self.model:
                agent_args.code_model = self.model
                agent_args.model = self.model
                logger.debug(
                    f"代理 {self.agent_id} 覆盖 args.model: {self.model} (runner_type={self.runner_type})"
                )

            # 配置 include_rules
            if hasattr(agent_args, "skip_build_index"):
                # 如果 include_rules 为 True，需要确保不跳过索引构建
                if self.include_rules:
                    agent_args.skip_build_index = False
                    agent_args.skip_filter_index = False
                    logger.debug(
                        f"代理 {self.agent_id} 启用规则上下文，skip_build_index=False"
                    )
                else:
                    # 保持默认行为
                    pass

            # 根据 runner_type 选择不同的 runner
            # 优先使用传入的 runner_type，否则使用实例默认值
            effective_runner_type = (
                runner_type if runner_type is not None else self.runner_type
            )

            if effective_runner_type == "terminal":
                # 使用 TerminalRunner
                runner = TerminalRunner(
                    llm=llm,
                    args=agent_args,
                    conversation_config=conversation_config,
                    cancel_token=cancel_token,
                    system_prompt=self.system_prompt,
                )

                # TerminalRunner.run() 直接返回 attempt_result 字符串
                attempt_result = runner.run(AgenticEditRequest(user_input=user_input))

                # 为了统一接口，将字符串包装为 AttemptCompletionTool 对象
                return AttemptCompletionTool(result=attempt_result, command=None)

            else:
                # 使用 SdkRunner（默认，或静默模式下强制使用）
                runner = SdkRunner(
                    llm=llm,
                    args=agent_args,
                    conversation_config=conversation_config,
                    cancel_token=cancel_token,
                    system_prompt=self.system_prompt,
                )

                # 执行并监听事件
                attempt_completion = None
                events = runner.run(AgenticEditRequest(user_input=user_input))

                for event in events:
                    if isinstance(event, CompletionEvent):
                        attempt_completion = event.completion
                        break

                return attempt_completion

        except CancelRequestedException:
            # 取消请求需要向上抛出，让上层执行器能够标记步骤为 CANCELLED
            logger.info(f"WorkflowSubAgent {self.agent_id} 收到取消请求，向上抛出")
            raise
        except Exception as e:
            logger.error(f"WorkflowSubAgent {self.agent_id} 运行失败: {str(e)}")
            return None
