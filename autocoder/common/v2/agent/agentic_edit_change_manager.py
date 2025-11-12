"""
AgenticEdit 变更管理器模块

该模块负责处理文件变更的应用、检查点管理和回滚功能，从 AgenticEdit 主类中独立出来。
"""

import os
import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from loguru import logger

from autocoder.common import AutoCoderArgs, git_utils
from autocoder.common.printer import Printer
from autocoder.events.event_manager_singleton import get_event_manager
from autocoder.events.event_types import EventMetadata
from autocoder.events import event_content as EventContentCreator
from autocoder.common.action_yml_file_manager import ActionYmlFileManager
from autocoder.memory.active_context_manager import ActiveContextManager
from autocoder.common.auto_coder_lang import get_message, get_message_with_format
from autocoder.common.pull_requests import create_pull_request
from autocoder.common.v2.agent.agentic_edit_types import FileChangeEntry

if TYPE_CHECKING:
    from .agentic_edit import AgenticEdit


class AgenticEditChangeManager:
    """
    AgenticEdit 变更管理器
    
    负责处理文件变更的应用、检查点管理和回滚功能。
    """
    
    def __init__(self, agent: 'AgenticEdit'):
        """
        初始化变更管理器
        
        Args:
            agent: AgenticEdit 实例，用于访问必要的属性和方法
        """
        self.agent = agent
        self.args = agent.args
        self.printer = agent.printer
        self.llm = agent.llm
        self.checkpoint_manager = agent.checkpoint_manager
        self.conversation_config = agent.conversation_config
        
        # 文件变更跟踪信息
        # 格式: { file_path: FileChangeEntry(...) }
        self.file_changes: Dict[str, FileChangeEntry] = {}
    
    def record_file_change(self, file_path: str, change_type: str, diff: Optional[str] = None, content: Optional[str] = None):
        """
        记录单个文件的变更信息。

        Args:
            file_path: 相对路径
            change_type: 'added' 或 'modified'
            diff: 对于 replace_in_file，传入 diff 内容
            content: 最新文件内容（可选，通常用于 write_to_file）
        """
        entry = self.file_changes.get(file_path)
        if entry is None:
            entry = FileChangeEntry(
                type=change_type, diffs=[], content=content)
            self.file_changes[file_path] = entry
        else:
            # 文件已经存在，可能之前是 added，现在又被 modified，或者多次 modified
            # 简单起见，type 用 added 优先，否则为 modified
            if entry.type != "added":
                entry.type = change_type

            # content 以最新为准
            if content is not None:
                entry.content = content

        if diff:
            entry.diffs.append(diff)

    def get_all_file_changes(self) -> Dict[str, FileChangeEntry]:
        """
        获取当前记录的所有文件变更信息。

        Returns:
            字典，key 为文件路径，value 为变更详情
        """
        return self.file_changes
    
    def apply_pre_changes(self):
        """应用预处理变更，通常用于在主要变更前创建提交点"""
        # get the file name
        if not self.args.file:
            logger.warning("No self.args.file set, skip to apply pre changes")
            return
        file_name = os.path.basename(self.args.file)
        if not self.args.skip_commit:
            try:
                commit_result = git_utils.commit_changes(
                    self.args.source_dir, f"auto_coder_pre_{file_name}")
                get_event_manager(self.args.event_file).write_result(
                    EventContentCreator.create_result(
                        content={
                            "have_commit": commit_result.success,
                            "commit_hash": commit_result.commit_hash,
                            "diff_file_num": len(commit_result.changed_files),
                            "event_file": self.args.event_file
                        }), metadata=EventMetadata(
                        action_file=self.args.file,
                        is_streaming=False,
                        path="/agent/edit/apply_pre_changes",
                        stream_out_type="/agent/edit").to_dict())

            except Exception as e:
                self.printer.print_in_terminal("git_init_required",
                                               source_dir=self.args.source_dir, error=str(e))
                return

    def apply_changes(self):
        """
        Apply all tracked file changes to the original project directory.
        """
        if not self.args.file:
            logger.warning("No self.args.file set, skip to apply pre changes")
            return

        if not self.args.skip_commit:
            try:
                file_name = os.path.basename(self.args.file)
                commit_result = git_utils.commit_changes(
                    self.args.source_dir,
                    f"{self.args.query}\nauto_coder_{file_name}",
                )

                get_event_manager(self.args.event_file).write_result(
                    EventContentCreator.create_result(
                        content={
                            "have_commit": commit_result.success,
                            "commit_hash": commit_result.commit_hash,
                            "diff_file_num": len(commit_result.changed_files),
                            "event_file": self.args.event_file
                        }), metadata=EventMetadata(
                        action_file=self.args.file,
                        is_streaming=False,
                        path="/agent/edit/apply_changes",
                        stream_out_type="/agent/edit").to_dict())

                action_yml_file_manager = ActionYmlFileManager(
                    self.args.source_dir)
                action_file_name = os.path.basename(self.args.file)
                add_updated_urls = []
                commit_result.changed_files
                for file in commit_result.changed_files:
                    add_updated_urls.append(
                        os.path.join(self.args.source_dir, file))

                self.args.add_updated_urls = add_updated_urls
                update_yaml_success = action_yml_file_manager.update_yaml_field(
                    action_file_name, "add_updated_urls", add_updated_urls)
                if not update_yaml_success:
                    self.printer.print_in_terminal(
                        "yaml_save_error", style="red", yaml_file=action_file_name)

                if self.args.enable_active_context:
                    active_context_manager = ActiveContextManager(
                        self.llm, self.args.source_dir)
                    task_id = active_context_manager.process_changes(
                        self.args)
                    self.printer.print_in_terminal("active_context_background_task",
                                                   style="blue",
                                                   task_id=task_id)
                git_utils.print_commit_info(commit_result=commit_result)

                # 检查是否需要创建 Pull Request
                if self.conversation_config and self.conversation_config.pull_request:
                    self._create_pull_request(commit_result)

            except Exception as e:
                self.printer.print_str_in_terminal(
                    str(e),
                    style="red"
                )

    def get_available_checkpoints(self) -> List[Dict[str, Any]]:
        """
        获取可用的检查点列表

        Returns:
            List[Dict[str, Any]]: 检查点信息列表
        """
        if not self.checkpoint_manager:
            return []

        return self.checkpoint_manager.get_available_checkpoints()

    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """
        回滚到指定的检查点，恢复文件状态和对话状态

        Args:
            checkpoint_id: 检查点ID

        Returns:
            bool: 是否成功回滚
        """
        if not self.checkpoint_manager:
            logger.error("无法回滚：检查点管理器未初始化")
            return False

        try:
            # 回滚文件变更
            undo_result, checkpoint = self.checkpoint_manager.undo_change_group_with_conversation(
                checkpoint_id)
            if not undo_result.success:
                logger.error(f"回滚文件变更失败: {undo_result.errors}")
                return False

            # 恢复对话状态
            if checkpoint:
                self.agent.current_conversations = checkpoint.conversations
                logger.info(f"已恢复对话状态，包含 {len(checkpoint.conversations)} 条消息")
                return True
            else:
                logger.warning(f"未找到关联的对话检查点: {checkpoint_id}，只回滚了文件变更")
                return undo_result.success
        except Exception as e:
            logger.exception(f"回滚到检查点 {checkpoint_id} 失败: {str(e)}")
            return False

    def handle_rollback_command(self, command: str) -> str:
        """
        处理回滚相关的命令

        Args:
            command: 命令字符串，如 "rollback list", "rollback to <id>", "rollback info <id>"

        Returns:
            str: 命令执行结果
        """
        if command == "rollback list":
            # 列出可用的检查点
            checkpoints = self.get_available_checkpoints()
            if not checkpoints:
                return "没有可用的检查点。"

            result = "可用的检查点列表：\n"
            for i, cp in enumerate(checkpoints):
                time_str = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(cp["timestamp"]))
                result += f"{i+1}. ID: {cp['id'][:8]}... | 时间: {time_str} | 变更文件数: {cp['changes_count']}"
                result += f" | {'包含对话状态' if cp['has_conversation'] else '不包含对话状态'}\n"

            return result

        elif command.startswith("rollback info "):
            # 显示检查点详情
            cp_id = command[len("rollback info "):].strip()

            # 查找检查点
            checkpoints = self.get_available_checkpoints()
            target_cp = None

            # 支持通过序号或ID查询
            if cp_id.isdigit() and 1 <= int(cp_id) <= len(checkpoints):
                target_cp = checkpoints[int(cp_id) - 1]
            else:
                for cp in checkpoints:
                    if cp["id"].startswith(cp_id):
                        target_cp = cp
                        break

            if not target_cp:
                return f"未找到ID为 {cp_id} 的检查点。"

            # 获取检查点详细信息
            time_str = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(target_cp["timestamp"]))

            # 获取变更文件列表
            changes = self.checkpoint_manager.get_changes_by_group(
                target_cp["id"])
            changed_files = [change.file_path for change in changes]

            # 获取对话状态信息
            conversation_info = "无对话状态信息"
            if target_cp["has_conversation"] and hasattr(self.checkpoint_manager, 'conversation_store'):
                checkpoint = self.checkpoint_manager.conversation_store.get_checkpoint(
                    target_cp["id"])
                if checkpoint and checkpoint.conversations:
                    conversation_info = f"包含 {len(checkpoint.conversations)} 条对话消息"

            result = f"检查点详情：\n"
            result += f"ID: {target_cp['id']}\n"
            result += f"创建时间: {time_str}\n"
            result += f"变更文件数: {target_cp['changes_count']}\n"
            result += f"对话状态: {conversation_info}\n\n"

            if changed_files:
                result += "变更文件列表：\n"
                for i, file_path in enumerate(changed_files):
                    result += f"{i+1}. {file_path}\n"

            return result

        elif command.startswith("rollback to "):
            # 回滚到指定检查点
            cp_id = command[len("rollback to "):].strip()

            # 查找检查点
            checkpoints = self.get_available_checkpoints()
            target_cp = None

            # 支持通过序号或ID回滚
            if cp_id.isdigit() and 1 <= int(cp_id) <= len(checkpoints):
                target_cp = checkpoints[int(cp_id) - 1]
            else:
                for cp in checkpoints:
                    if cp["id"].startswith(cp_id):
                        target_cp = cp
                        break

            if not target_cp:
                return f"未找到ID为 {cp_id} 的检查点。"

            # 执行回滚
            success = self.rollback_to_checkpoint(target_cp["id"])

            if success:
                # 获取变更文件列表
                changes = self.checkpoint_manager.get_changes_by_group(
                    target_cp["id"])
                changed_files = [change.file_path for change in changes]

                result = f"成功回滚到检查点 {target_cp['id'][:8]}...\n"
                result += f"恢复了 {len(changed_files)} 个文件的状态"

                if target_cp["has_conversation"]:
                    result += f"\n同时恢复了对话状态"

                return result
            else:
                return f"回滚到检查点 {target_cp['id'][:8]}... 失败。"

        return "未知命令。可用命令：rollback list, rollback info <id>, rollback to <id>"

    def _create_pull_request(self, commit_result):
        """
        创建 Pull Request（如果配置启用）

        Args:
            commit_result: Git commit 结果对象
        """
        try:
            # 获取当前分支名
            current_branch = git_utils.get_current_branch(self.args.source_dir)
            if not current_branch:
                logger.warning(get_message(
                    "/agent/edit/pull_request/branch_name_failed"))
                return

            # 准备 PR 标题和描述
            query = self.args.query or get_message(
                "/agent/edit/pull_request/default_query")
            pr_title = get_message_with_format(
                "/agent/edit/pull_request/title", query=f"{query[0:40]}...")

            # 构建 PR 描述
            file_list = ""
            if commit_result.changed_files:
                for file_path in commit_result.changed_files:
                    file_list += f"- `{file_path}`\n"

            pr_description = get_message_with_format(
                "/agent/edit/pull_request/description",
                query=query,
                file_count=len(commit_result.changed_files or []),
                commit_hash=commit_result.commit_hash,
                file_list=file_list.strip(),
                source_branch=current_branch,
                target_branch="main",
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
            )

            # 创建 Pull Request
            logger.info(get_message_with_format(
                "/agent/edit/pull_request/creating", title=pr_title))

            result = create_pull_request(
                repo_path=self.args.source_dir,
                title=pr_title,
                description=pr_description,
            )

            if result.success:
                logger.info(get_message("/agent/edit/pull_request/success"))
                logger.info(f"PR URL: {result.pr_url}")
                logger.info(f"PR 编号: {result.pr_number}")

                # 打印成功信息到终端
                self.printer.print_str_in_terminal(
                    get_message("/agent/edit/pull_request/success"),
                    style="green"
                )
                self.printer.print_str_in_terminal(f"PR URL: {result.pr_url}")
                self.printer.print_str_in_terminal(
                    f"PR 编号: {result.pr_number}")

                # 写入事件日志
                get_event_manager(self.args.event_file).write_result(
                    EventContentCreator.create_result(
                        content={
                            "success": True,
                            "pr_url": result.pr_url,
                            "pr_number": result.pr_number,
                            "source_branch": current_branch,
                            "target_branch": "main",
                            "platform": result.platform.value if result.platform else "unknown"
                        }),
                    metadata=EventMetadata(
                        action_file=self.args.file,
                        is_streaming=False,
                        path="/agent/edit/pull_request_created",
                        stream_out_type="/agent/edit"
                    ).to_dict()
                )

            else:
                error_msg = get_message_with_format(
                    "/agent/edit/pull_request/failed", error=result.error_message)
                logger.error(error_msg)

                # 打印错误信息到终端
                self.printer.print_str_in_terminal(error_msg, style="red")

                # 写入错误事件日志
                get_event_manager(self.args.event_file).write_error(
                    EventContentCreator.create_error(
                        error_code="PR_CREATION_FAILED",
                        error_message=result.error_message,
                        details={
                            "source_branch": current_branch,
                            "target_branch": "main"
                        }
                    ).to_dict(),
                    metadata=EventMetadata(
                        action_file=self.args.file,
                        is_streaming=False,
                        path="/agent/edit/pull_request_error",
                        stream_out_type="/agent/edit"
                    ).to_dict()
                )

        except Exception as e:
            error_msg = get_message_with_format(
                "/agent/edit/pull_request/exception", error=str(e))
            logger.exception(error_msg)

            # 打印异常信息到终端
            self.printer.print_str_in_terminal(error_msg, style="red")

            # 写入异常事件日志
            get_event_manager(self.args.event_file).write_error(
                EventContentCreator.create_error(
                    error_code="PR_CREATION_EXCEPTION",
                    error_message=get_message_with_format(
                        "/agent/edit/pull_request/exception", error=str(e)),
                    details={"exception_type": type(e).__name__}
                ).to_dict(),
                metadata=EventMetadata(
                    action_file=self.args.file,
                    is_streaming=False,
                    path="/agent/edit/pull_request_exception",
                    stream_out_type="/agent/edit"
                ).to_dict()
            ) 