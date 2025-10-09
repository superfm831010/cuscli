"""
SdkRunner 提供生成器接口，适用于SDK环境下的代理运行。

这个模块提供了一个简单的生成器接口，允许外部代码迭代处理代理事件。
它是三种运行模式中最轻量级的一种，适合集成到其他应用程序中。
"""

from loguru import logger
from typing import Generator, Any, Optional
import os
import time

from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditRequest, AgentEvent, CompletionEvent, PullRequestEvent, 
    PullRequestResult, CommitEvent,PreCommitEvent
)
from autocoder.common import  git_utils
from autocoder.common.git_utils import CommitResult
from autocoder.common.pull_requests import create_pull_request

from .base_runner import BaseRunner

class SdkRunner(BaseRunner):
    """
    提供生成器接口的代理运行器，适用于SDK环境。
    
    这个运行器返回一个事件生成器，允许外部代码迭代处理代理事件。
    它是三种运行模式中最轻量级的一种，适合集成到其他应用程序中。
    """

    def apply_pre_changes(self)->Optional[CommitResult]:
        # get the file name
        file_name = os.path.basename(self.args.file)
        if not self.args.skip_commit:
            try:
                commit_result = git_utils.commit_changes(
                    self.args.source_dir, f"auto_coder_pre_{file_name}")                
                return commit_result

            except Exception as e:
                self.printer.print_in_terminal("git_init_required",
                                               source_dir=self.args.source_dir, error=str(e))
        return None

    def apply_changes(self) -> tuple[Optional[CommitResult], Optional[PullRequestResult]]:
        """
        应用变更并可选地创建 Pull Request
        
        Returns:
            tuple: (commit_result, pull_request_result)
        """
        if not self.args.skip_commit:
            try:
                file_name = os.path.basename(self.args.file)
                commit_result = git_utils.commit_changes(
                    self.args.source_dir,
                    f"{self.args.query}\nauto_coder_{file_name}",
                )
                
                pull_request_result = None
                # 检查是否需要创建 Pull Request
                if self.conversation_config and self.conversation_config.pull_request:
                    pr_result = self._create_pull_request(commit_result)
                    if pr_result:
                        # 将 PRResult 转换为 PullRequestResult
                        pull_request_result = PullRequestResult.from_pr_result(pr_result)

                return commit_result, pull_request_result    

            except Exception as e:
                self.printer.print_str_in_terminal(
                    str(e),
                    style="red"
                )  
        
        return None, None
    
    def _create_pull_request(self, commit_result):
        """
        创建 Pull Request 的内部方法
        
        Args:
            commit_result: Git commit 结果对象
            
        Returns:
            PRResult: Pull Request 创建结果
        """
        try:            
            
            # 获取当前分支名
            current_branch = git_utils.get_current_branch(self.args.source_dir)
            if not current_branch:
                logger.warning("无法获取当前分支名")
                return None

            # 准备 PR 标题和描述
            query = self.args.query or "Auto-coder generated changes"
            pr_title = f"Auto-coder: {query[:40]}..."

            # 构建 PR 描述
            file_list = ""
            if commit_result.changed_files:
                for file_path in commit_result.changed_files:
                    file_list += f"- `{file_path}`\n"

            pr_description = f"""## 自动生成的代码变更

**查询内容**: {query}

**变更文件数量**: {len(commit_result.changed_files or [])}

**Commit Hash**: {commit_result.commit_hash}

### 变更文件列表:
{file_list.strip()}

**源分支**: {current_branch}  
**目标分支**: main  
**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
---
此 Pull Request 由 Auto-coder 自动生成
"""

            # 创建 Pull Request
            logger.info(f"正在创建 Pull Request: {pr_title}")

            result = create_pull_request(
                repo_path=self.args.source_dir,
                title=pr_title,
                description=pr_description,
            )

            if result.success:
                logger.info("Pull Request 创建成功")
                logger.info(f"PR URL: {result.pr_url}")
                logger.info(f"PR 编号: {result.pr_number}")

            return result

        except Exception as e:
            logger.exception(f"创建 Pull Request 时发生异常: {str(e)}")
            # 返回一个失败的 PRResult
            try:
                from autocoder.common.pull_requests.models import PRResult
                return PRResult(
                    success=False,
                    error_message=f"创建 Pull Request 失败: {str(e)}"
                )
            except ImportError:
                return None
    
    def run(self, request: AgenticEditRequest) -> Generator[AgentEvent, None, None]:
        """
        Runs the agentic edit process and yields events for external processing.
        """
        try:
            if self.conversation_config and self.conversation_config.pre_commit:
                pre_commit_result = self.apply_pre_changes()
                yield PreCommitEvent(commit_result=pre_commit_result)

            event_stream = self.analyze(request)                                    
            for agent_event in event_stream:
                if isinstance(agent_event, CompletionEvent):
                    if self.conversation_config and self.conversation_config.post_commit:
                        commit_result, pull_request_result = self.apply_changes()                    
                        # 发射 commit 事件
                        if commit_result:
                            yield CommitEvent(commit_result=commit_result)
                        
                        # 发射 pull request 事件（如果有）                        
                        if pull_request_result:
                            yield PullRequestEvent(pull_request_result=pull_request_result)
                    
                    # 总是发射 completion 事件
                    yield agent_event
                else:
                    yield agent_event
                
        except Exception as e:
            logger.exception(
                "An unexpected error occurred during agent execution: {e}")           
            raise e
