import byzerllm
import os
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from loguru import logger as global_logger

from autocoder.common.v2.agent.agentic_edit import AgenticEditRequest
from autocoder.run_context import get_run_context, RunMode
from autocoder.common.v2.agent.runner import (
    TerminalRunner,
    FileBasedEventRunner,
)


@byzerllm.prompt()
def merge_back_template(names: str, commits: str, query: str, home_dir: str):
    """
    ## Worktree Merge Task

    Merge the latest changes from the following worktrees back to the current project:
    {% for name in names.split(',') %}
    ### {{ name }}
    **Target Worktree Path:** `{{ home_dir }}/.auto-coder/async_agent/tasks/{{name}}`
    **Target Worktree Metadata:** `{{ home_dir }}/.auto-coder/async_agent/meta/{{name}}.json`

    The target worktree metadata contains the original user requirements, and the target worktree path contains the commits and uncommitted code changes generated for these requirements.
    {% endfor %}

    ### Operation Steps
    1. **Review Target Worktree Metadata**: Check the requirements for the new changes generated in the target worktree.
    2. **Commit History Check**: Review the git log from both sides to identify key changes.
    3. **Uncommitted Code Check**: Confirm if there are any uncommitted code changes in the worktree.
    4. **Merge Changes**: Understand the requirements, then safely merge the changes from the target worktree back to the current project.

    {% if commits and commits.strip() %}
    ### Key Commits to Focus on in the Worktree
    {% for commit in commits.split(',') %}
    - `{{ commit.strip() }}`
    {% endfor %}
    {% endif %}

    {% if query and query.strip() %}
    ### Additional Requirements
    {{ query }}
    {% endif %}
    """


class MergeCommandHandler:
    """处理 merge 指令相关的操作"""

    def __init__(self):
        self.console = Console()
        self._config = None

    def _create_config(self):
        """创建 merge 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .command("merge")
                .positional("names", required=True)
                .keyword("query", required=False)
                .keyword("commits", required=False)                
                .build()
            )
        return self._config

    def handle_merge_command(
        self, query: str, args, llm, conversation_config, cancel_token
    ) -> Optional[str]:
        """
        处理 merge 指令的主入口

        Args:
            query: 查询字符串，例如 "/merge branch_name --query some query"
            args: 配置参数
            llm: LLM实例
            conversation_config: 对话配置
            cancel_token: 取消令牌

        Returns:
            None: 表示处理了 merge 指令，应该返回而不继续执行
            其他值: 表示没有处理 merge 指令，应该继续执行
        """
        # 解析命令
        config = self._create_config()
        result = parse_typed_query(query, config)

        # 检查是否包含 merge 命令
        if not result.has_command("merge"):
            return "continue"  # 不是 merge 指令，继续执行

        # 获取参数 - 使用 CommandWrapper 的属性访问方式（更符合文档用法）
        merge_command = result.get_command("merge")
        if not merge_command or not merge_command.args:
            self.console.print(
                Panel(
                    "[red]Error:[/red] /merge requires a 'names' parameter.\n"
                    "Usage: /merge <names> [--query <query>]",
                    title="[red]Parameter Error[/red]",
                    border_style="red",
                )
            )
            return None

        # 通过属性访问位置参数（根据配置，位置参数名为 "names"）
        names = result.merge.names

        # 获取 query 参数：优先从键值对参数获取，其次从剩余参数获取
        query_value = ""
        try:
            # 键值对参数 query=xxx
            if result.merge.query:
                query_value = result.merge.query
        except AttributeError:
            pass

        if not query_value and result.query:
            # 全局剩余参数或命令级别的剩余参数
            query_value = result.query

        # 获取 commits 参数
        commits_value = ""
        try:
            if result.merge.commits:
                commits_value = result.merge.commits
        except AttributeError:
            pass

        # 执行 merge 操作
        return self._execute_merge(
            names=names,
            query=query_value,
            commits=commits_value,
            args=args,
            llm=llm,
            conversation_config=conversation_config,
            cancel_token=cancel_token,
        )

    def _execute_merge(
        self,
        names: str,
        query: str,
        commits: str,
        args,
        llm,
        conversation_config,
        cancel_token: Optional[str],
    ) -> None:
        """
        执行 merge 操作

        Args:
            names: 位置参数 names (逗号分隔的工作树名称)
            query: 命名参数 query (额外需求)
            commits: 命名参数 commits (需要重点关注的提交，逗号分隔)
            args: 配置参数
            llm: LLM实例
            conversation_config: 对话配置
            cancel_token: 取消令牌
        """
        try:
            # 获取用户 home 目录
            home_dir = os.path.expanduser("~")

            # 确保空字符串参数不会在模板中被误判为有值
            rendered_content = merge_back_template.prompt(
                names=names,
                commits=commits,
                query=query,
                home_dir=home_dir,
            )

            runner_class = {
                RunMode.WEB: FileBasedEventRunner,
                RunMode.TERMINAL: TerminalRunner,
            }.get(get_run_context().mode)

            if runner_class:
                runner = runner_class(
                    llm=llm,
                    args=args,
                    conversation_config=conversation_config,
                    cancel_token=cancel_token,
                )
                runner.run(AgenticEditRequest(user_input=rendered_content))

            self.console.print(
                Panel(
                    f"[green]Success:[/green] Merge command executed\n"
                    f"Names: {names}\n"
                    f"Query: {query if query else 'N/A'}\n"
                    f"Commits: {commits if commits else 'N/A'}",
                    title="[green]Merge Executed[/green]",
                    border_style="green",
                )
            )
            return None

        except Exception as e:
            self.console.print(
                Panel(
                    f"[red]Error:[/red] Failed to execute merge command: {str(e)}",
                    title="[red]Execution Error[/red]",
                    border_style="red",
                )
            )
            global_logger.error(f"Failed to execute merge command: {e}")
            return None
