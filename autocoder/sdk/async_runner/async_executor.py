"""
异步执行器模块

提供并行执行 auto-coder.run 命令的功能，支持前台和后台运行模式。
"""

import os
import platform
import subprocess
import asyncio
import concurrent.futures
import uuid
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .markdown_processor import Document
from .worktree_manager import WorktreeManager, WorktreeInfo
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.llm_friendly_package import get_package_manager


def _get_command_path(command: str) -> str:
    """
    获取命令的完整路径

    在 Windows 上，使用 shutil.which() 来查找可执行文件的完整路径，
    以解决 subprocess 在不使用 shell=True 时无法找到命令的问题。

    Args:
        command: 命令名称

    Returns:
        命令的完整路径
    """
    # 如果已经是完整路径，直接返回
    if os.path.isabs(command):
        return command

    # 使用 shutil.which() 查找命令
    full_path = shutil.which(command)
    if full_path:
        return full_path

    # 在 Windows 上，尝试添加 .exe 后缀
    if platform.system() == "Windows":
        full_path = shutil.which(f"{command}.exe")
        if full_path:
            return full_path

    # 如果找不到，返回原始命令（让后续错误处理来报告问题）
    return command


def _build_env() -> Dict[str, str]:
    """
    构建子进程环境变量

    在 Windows 上自动配置 UTF-8 相关环境变量，确保子进程使用 UTF-8 编码。

    Returns:
        合并后的环境变量字典
    """
    # 复制系统环境变量
    env = os.environ.copy()

    # Windows UTF-8 自动配置
    if platform.system() == "Windows":
        env.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "LANG": "zh_CN.UTF-8",
                "LC_ALL": "zh_CN.UTF-8",
            }
        )

    return env


@dataclass
class ExecutionResult:
    """执行结果"""

    success: bool
    output: str = ""
    error: str = ""
    log_file: str = ""


class AutoCoderExecutor:
    """Auto-coder 执行器，用于执行 auto-coder.run 命令"""

    def __init__(
        self,
        model: str,
        pull_request: bool = False,
        background_mode: bool = False,
        verbose: bool = False,
        metadata_manager=None,
        task_id=None,
    ):
        """
        初始化执行器

        Args:
            model: 模型名称
            pull_request: 是否创建 PR
            background_mode: 是否后台运行
            verbose: 是否启用详细输出
            metadata_manager: 元数据管理器
            task_id: 任务ID
        """
        self.model = model
        self.pull_request = pull_request
        self.background_mode = background_mode
        self.verbose = verbose
        self.metadata_manager = metadata_manager
        self.task_id = task_id

    def execute_autocoder(
        self, work_dir: str, temp_file_path: str
    ) -> "ExecutionResult":
        """
        执行 auto-coder.run 命令

        Args:
            work_dir: 工作目录
            temp_file_path: 临时文件的完整路径

        Returns:
            ExecutionResult: 执行结果
        """
        # 构建 auto-coder.run 命令参数 (不包含 --pr，我们单独处理)
        # 使用 _get_command_path 获取完整路径，确保 Windows 兼容性
        args = [_get_command_path("auto-coder.run"), "--model", self.model]

        # # 如果启用了 verbose，添加 --verbose 参数
        # if self.verbose:
        #     args.append("--verbose")

        # 准备输入文件路径
        temp_file_path = Path(temp_file_path)

        try:
            # 先执行代码生成
            if self.background_mode:
                result = self._execute_background(work_dir, temp_file_path, args)
            else:
                result = self._execute_foreground(work_dir, temp_file_path, args)

            # 如果代码生成成功且需要创建 PR，则继续处理 PR
            if result.success and self.pull_request:
                pr_result = self._create_pull_request_after_execution(
                    work_dir, temp_file_path.name
                )
                if pr_result:
                    # 更新结果输出，包含 PR 信息
                    result.output += f"\n\n{pr_result}"

            return result

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=get_message_with_format("execution_failed", error=str(e)),
            )

    def execute_autocoder_workflow(
        self, work_dir: str, temp_file_path: str, workflow: str
    ) -> "ExecutionResult":
        """
        执行 auto-coder.run --workflow 命令

        Args:
            work_dir: 工作目录
            temp_file_path: 临时文件的完整路径
            workflow: workflow 名称或文件路径

        Returns:
            ExecutionResult: 执行结果
        """
        # 构建 auto-coder.run --workflow 命令参数
        # 使用 _get_command_path 获取完整路径，确保 Windows 兼容性
        args = [_get_command_path("auto-coder.run"), "--workflow", workflow]

        # 如果指定了模型，添加 --model 参数（可选，允许使用 YAML 中的模型）
        if self.model and self.model.strip():
            args.extend(["--model", self.model])

        # 准备输入文件路径
        temp_file_path = Path(temp_file_path)

        try:
            # 执行 workflow
            if self.background_mode:
                result = self._execute_background(work_dir, temp_file_path, args)
            else:
                result = self._execute_foreground(work_dir, temp_file_path, args)

            # 如果 workflow 执行成功且需要创建 PR，则继续处理 PR
            if result.success and self.pull_request:
                pr_result = self._create_pull_request_after_execution(
                    work_dir, temp_file_path.name
                )
                if pr_result:
                    # 更新结果输出，包含 PR 信息
                    result.output += f"\n\n{pr_result}"

            return result

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=get_message_with_format("execution_failed", error=str(e)),
            )

    def _execute_background(
        self, work_dir: str, temp_file_path: Path, args: List[str]
    ) -> ExecutionResult:
        """后台执行模式"""
        # 创建日志文件
        log_filename = f"autocoder_{temp_file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path = Path(work_dir) / log_filename

        try:
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                # 写入日志头部信息
                log_file.write("=== Auto-coder.run 执行日志 ===\n")
                log_file.write(
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                log_file.write(f"工作目录: {work_dir}\n")
                log_file.write(f"任务文件: {temp_file_path.name}\n")
                log_file.write(f"使用模型: {self.model}\n")
                log_file.write(f"创建PR: {self.pull_request}\n")
                log_file.write("================================\n\n")
                log_file.flush()

                # 读取输入文件内容并通过管道传递给 auto-coder.run
                with open(temp_file_path, "r", encoding="utf-8") as input_file:
                    content = input_file.read()

                # 使用 Popen 获取进程PID
                # 显式指定 encoding、errors 和 env，确保 Windows 兼容性
                process = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=work_dir,
                    env=_build_env(),
                )

                # 立即保存子进程PID到元数据
                if self.metadata_manager and self.task_id:
                    self.metadata_manager.update_sub_pid(self.task_id, process.pid)
                    if self.verbose:
                        print(
                            f"[DEBUG] 保存子进程PID: {process.pid} for task: {self.task_id}"
                        )

                # 发送输入并等待完成
                try:
                    stdout, stderr = process.communicate(
                        input=content, timeout=3600 * 12
                    )
                    returncode = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    return ExecutionResult(
                        success=False,
                        error=get_message("execution_timeout"),
                        log_file=str(log_file_path),
                    )

                print(
                    get_message_with_format(
                        "background_task_running", log_file=str(log_file_path)
                    )
                )

                if returncode == 0:
                    print(get_message("background_task_completed"))
                    return ExecutionResult(
                        success=True,
                        output=get_message("background_task_completed"),
                        log_file=str(log_file_path),
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        error=get_message_with_format(
                            "autocoder_run_failed_with_code", code=returncode
                        ),
                        log_file=str(log_file_path),
                    )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error=get_message("execution_timeout"),
                log_file=str(log_file_path) if log_file_path.exists() else "",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=get_message_with_format(
                    "background_execution_failed", error=str(e)
                ),
                log_file=str(log_file_path) if log_file_path.exists() else "",
            )

    def _execute_foreground(
        self, work_dir: str, temp_file_path: Path, args: List[str]
    ) -> ExecutionResult:
        """前台执行模式"""
        try:
            print(get_message("foreground_task_running"))
            print("================================")

            # 读取输入文件内容
            with open(temp_file_path, "r", encoding="utf-8") as input_file:
                content = input_file.read()

            # 使用 Popen 获取PID
            # 显式指定 encoding、errors 和 env，确保 Windows 兼容性
            process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=work_dir,
                env=_build_env(),
            )

            # 保存子进程PID
            if self.metadata_manager and self.task_id:
                self.metadata_manager.update_sub_pid(self.task_id, process.pid)
                if self.verbose:
                    print(
                        f"[DEBUG] 保存子进程PID: {process.pid} for task: {self.task_id}"
                    )

            # 等待完成
            try:
                stdout, stderr = process.communicate(input=content, timeout=3600)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                return ExecutionResult(
                    success=False, error=get_message("execution_timeout")
                )

            # 输出结果
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)

            print("================================")
            print(get_message("foreground_task_completed"))

            if returncode == 0:
                return ExecutionResult(success=True, output=stdout)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"{get_message_with_format('autocoder_run_failed_with_code', code=returncode)}\n{stderr}",
                )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False, error=get_message("execution_timeout")
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=get_message_with_format(
                    "foreground_execution_failed", error=str(e)
                ),
            )

    def check_autocoder_available(self) -> bool:
        """
        检查 auto-coder.run 是否可用

        Returns:
            是否可用
        """
        # 使用 shutil.which() 替代 Unix 的 which 命令，确保跨平台兼容
        return shutil.which("auto-coder.run") is not None

    def validate_model(self) -> None:
        """
        验证模型参数

        Raises:
            ValueError: 模型参数无效时抛出异常
        """
        if not self.model or not self.model.strip():
            raise ValueError("模型参数不能为空")

    def log_execution(
        self, work_dir: str, temp_file_path: str, meta_file_path: str = ""
    ) -> None:
        """记录执行信息"""
        mode_str = (
            get_message("background_mode")
            if self.background_mode
            else get_message("foreground_mode")
        )
        print(get_message_with_format("async_mode_task_info", mode=mode_str))
        print(get_message_with_format("execution_directory", dir=work_dir))
        print(get_message_with_format("temp_file", file=Path(temp_file_path).name))
        print(get_message_with_format("using_model", model=self.model))
        print(get_message_with_format("create_pr", pr=self.pull_request))
        print(get_message_with_format("run_mode", mode=mode_str))
        print(get_message_with_format("full_path", path=temp_file_path))
        if meta_file_path:
            print(get_message_with_format("meta_file_path", path=meta_file_path))

    def _create_pull_request_after_execution(
        self, work_dir: str, temp_filename: str
    ) -> Optional[str]:
        """
        在代码生成完成后创建 Pull Request

        Args:
            work_dir: 工作目录
            temp_filename: 临时文件名

        Returns:
            PR 创建结果信息
        """
        try:
            from autocoder.common.pull_requests import create_pull_request
            from autocoder.common.pull_requests.utils import (
                get_current_branch,
                has_uncommitted_changes,
                auto_commit_changes,
            )

            # 检查是否有未提交的更改
            if has_uncommitted_changes(work_dir):
                if not auto_commit_changes(
                    work_dir, f"Auto-generated code from {temp_filename}"
                ):
                    return get_message("auto_commit_failed")

            # 获取当前分支
            current_branch = get_current_branch(work_dir)
            if not current_branch:
                return get_message("cannot_get_current_branch")

            # 生成 PR 标题
            pr_title = f"Auto-generated code from async agent runner"
            if temp_filename != "stdin.md":
                pr_title += f" ({temp_filename})"

            print(get_message_with_format("creating_pull_request", title=pr_title))

            # 创建 PR
            result = create_pull_request(
                repo_path=work_dir,
                title=pr_title,
                description=f"This PR was automatically generated by the async agent runner.\n\nSource: {temp_filename}",
                draft=False,
            )

            if result.success:
                pr_info = get_message("pull_request_created_successfully") + "\n"
                if hasattr(result, "pr_info") and result.pr_info:
                    pr_info += f"   URL: {result.pr_info.html_url}\n"
                    pr_info += (
                        f"   分支: {current_branch} → {result.pr_info.base_branch}"
                    )
                return pr_info
            else:
                return get_message_with_format(
                    "pull_request_creation_failed", error=result.error_message
                )

        except Exception as e:
            print(get_message_with_format("pull_request_creation_error", error=str(e)))
            return get_message_with_format("pull_request_creation_error", error=str(e))


class AsyncExecutor:
    """异步执行器，管理多个并行任务"""

    def __init__(
        self,
        model: str,
        pull_request: bool = False,
        background_mode: bool = False,
        max_workers: int = 4,
        verbose: bool = False,
        task_prefix: str = "",
        worktree_name: Optional[str] = None,
        include_libs: List[str] = None,
        workflow: Optional[str] = None,
    ):
        """
        初始化异步执行器

        Args:
            model: 模型名称
            pull_request: 是否创建 PR
            background_mode: 是否后台运行
            max_workers: 最大并行工作线程数
            verbose: 是否启用详细输出
            task_prefix: 任务名称前缀
            worktree_name: 指定的 worktree 名称，为空时自动生成
            include_libs: 要包含的LLM friendly packages列表
            workflow: workflow 名称或文件路径（可选）
        """
        self.model = model
        self.pull_request = pull_request
        self.background_mode = background_mode
        self.max_workers = max_workers
        self.verbose = verbose
        self.task_prefix = task_prefix
        self.worktree_name = worktree_name
        self.include_libs = include_libs or []
        self.workflow = workflow
        self.worktree_manager: Optional[WorktreeManager] = None

    def set_worktree_manager(self, manager: WorktreeManager) -> None:
        """设置 worktree 管理器"""
        self.worktree_manager = manager

    def _sanitize_worktree_name(self, name: str) -> str:
        """清理并标准化用户指定的 worktree 名称，避免路径与文件名问题"""
        safe = re.sub(r'[<>:"/\\|?*\s]+', "_", name)
        safe = re.sub(r"_+", "_", safe).strip("_")
        if len(safe) > 100:
            safe = safe[:100]
        return safe or "task"

    def _add_libraries_to_worktree(self, worktree_path: str) -> None:
        """在指定的 worktree 目录中添加 LLM friendly packages"""
        try:
            if self.verbose:
                print(
                    f"Adding LLM friendly packages to worktree {worktree_path}: {', '.join(self.include_libs)}"
                )

            manager = get_package_manager(worktree_path)

            for lib_name in self.include_libs:
                if lib_name.strip():  # 确保库名不为空
                    success = manager.add_library(lib_name.strip())
                    if self.verbose:
                        if success:
                            print(f"Successfully added library {lib_name} to worktree")
                        else:
                            print(
                                f"Library {lib_name} was already added or failed to add to worktree"
                            )

        except Exception as e:
            if self.verbose:
                print(
                    f"Warning: Failed to add libraries to worktree {worktree_path}: {str(e)}"
                )
            # 不抛出异常，只是警告，因为这不应该阻止主要功能

    def _copy_workflow_dirs_to_worktree(self, worktree_path: str) -> None:
        """拷贝 workflow 相关目录到 worktree"""

        try:
            # 获取原始项目路径
            if self.worktree_manager and self.worktree_manager.original_project_path:
                original_project = Path(self.worktree_manager.original_project_path)
            else:
                original_project = Path.cwd()

            worktree_path = Path(worktree_path)

            # 需要拷贝的目录列表
            dirs_to_copy = [".autocoderagents", ".autocoderworkflow"]

            for dir_name in dirs_to_copy:
                src_dir = original_project / dir_name
                dst_dir = worktree_path / dir_name

                if src_dir.exists() and src_dir.is_dir():
                    if dst_dir.exists():
                        # 如果目标已存在，先删除
                        shutil.rmtree(dst_dir)

                    # 拷贝目录
                    shutil.copytree(src_dir, dst_dir)

                    if self.verbose:
                        print(f"Copied {dir_name} to worktree: {dst_dir}")
                elif self.verbose:
                    print(f"Source directory {src_dir} does not exist, skipping")

        except Exception as e:
            if self.verbose:
                print(
                    f"Warning: Failed to copy workflow dirs to worktree {worktree_path}: {str(e)}"
                )
            # 不抛出异常，只是警告

    async def process_documents_async(
        self, documents: List[Document]
    ) -> List[ExecutionResult]:
        """
        异步处理多个文档

        Args:
            documents: 文档列表

        Returns:
            执行结果列表
        """
        if not self.worktree_manager:
            raise ValueError("必须先设置 worktree 管理器")

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # 创建执行器
        autocoder_exec = AutoCoderExecutor(
            self.model, self.pull_request, self.background_mode, self.verbose
        )

        # 检查 auto-coder.run 是否可用
        if not autocoder_exec.check_autocoder_available():
            raise Exception("auto-coder.run 未找到，请确保已正确安装")

        # 验证模型参数（workflow 模式下跳过，允许使用 YAML 中的模型）
        if not self.workflow:
            autocoder_exec.validate_model()

        # 使用线程池执行器来处理文档（因为涉及文件I/O和子进程）
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 创建任务列表
            tasks = []
            for doc in documents:
                task = loop.run_in_executor(
                    executor,
                    self._process_document_sync,
                    doc,
                    timestamp,
                    autocoder_exec,
                )
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果，将异常转换为失败的 ExecutionResult
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        ExecutionResult(
                            success=False, error=f"处理文档 {i+1} 失败: {str(result)}"
                        )
                    )
                else:
                    processed_results.append(result)

            return processed_results

    def process_documents_sync(
        self, documents: List[Document]
    ) -> List[ExecutionResult]:
        """
        同步处理多个文档

        Args:
            documents: 文档列表

        Returns:
            执行结果列表
        """
        return asyncio.run(self.process_documents_async(documents))

    def _process_document_sync(
        self, doc: Document, timestamp: str, autocoder_exec: AutoCoderExecutor
    ) -> ExecutionResult:
        """
        同步处理单个文档（在线程池中执行）

        Args:
            doc: 文档
            timestamp: 时间戳
            autocoder_exec: auto-coder 执行器

        Returns:
            执行结果
        """
        wt_info = None
        try:
            # 生成工作目录名
            workdir_name = self._generate_worktree_name(doc, timestamp)

            print(
                get_message_with_format(
                    "processing_document", info=self._get_document_info(doc)
                )
            )
            print(get_message_with_format("creating_git_worktree", name=workdir_name))

            # 创建 worktree 并记录元数据
            try:
                wt_info = self.worktree_manager.create_worktree(
                    name=workdir_name,
                    user_query=doc.content,  # 使用文档内容作为查询
                    model=self.model,
                    split_mode=f"doc_{doc.index}",  # 文档分割信息
                )
                print(
                    get_message_with_format(
                        "git_worktree_created_successfully", path=wt_info.path
                    )
                )

                # 自动添加指定的 LLM friendly packages
                if self.include_libs:
                    self._add_libraries_to_worktree(wt_info.path)

                # 如果是 workflow 模式，拷贝必要的目录到 worktree
                if self.workflow:
                    self._copy_workflow_dirs_to_worktree(wt_info.path)

            except Exception as e:
                error_msg = get_message_with_format(
                    "create_git_worktree_failed", error=str(e)
                )
                print(
                    get_message_with_format(
                        "git_worktree_creation_failed", error=str(e)
                    )
                )
                return ExecutionResult(success=False, error=error_msg)

            try:
                # 写入内容到 meta_dir 中的临时文件
                temp_file_path = self.worktree_manager.meta_dir / doc.temp_filename
                print(
                    get_message_with_format(
                        "writing_content_to_file", filename=doc.temp_filename
                    )
                )

                # 确保 meta_dir 存在
                self.worktree_manager.meta_dir.mkdir(parents=True, exist_ok=True)

                # 写入文件内容
                with open(temp_file_path, "w", encoding="utf-8") as f:
                    f.write(doc.content)
                print(get_message("file_write_successful"))

                # 传递元数据管理器和任务ID给执行器
                autocoder_exec.metadata_manager = self.worktree_manager.metadata_manager
                autocoder_exec.task_id = workdir_name

                # 记录执行信息（包含meta文件路径）
                meta_file_path = str(
                    self.worktree_manager.meta_dir / f"{workdir_name}.json"
                )
                autocoder_exec.log_execution(
                    wt_info.path, str(temp_file_path), meta_file_path
                )

                # 执行 auto-coder.run（根据是否有 workflow 选择不同的执行路径）
                print(get_message("running_autocoder"))
                if self.workflow:
                    # workflow 模式
                    result = autocoder_exec.execute_autocoder_workflow(
                        wt_info.path, str(temp_file_path), self.workflow
                    )
                else:
                    # 常规模式
                    result = autocoder_exec.execute_autocoder(
                        wt_info.path, str(temp_file_path)
                    )

                # 更新任务状态
                execution_result_dict = {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "log_file": result.log_file,
                }

                if result.success:
                    print(
                        get_message_with_format(
                            "processing_completed", name=workdir_name
                        )
                    )
                    self.worktree_manager.update_task_status(
                        task_id=workdir_name,
                        status="completed",
                        log_file=result.log_file,
                        execution_result=execution_result_dict,
                    )
                else:
                    print(
                        get_message_with_format(
                            "autocoder_run_execution_failed", error=result.error
                        )
                    )
                    self.worktree_manager.update_task_status(
                        task_id=workdir_name,
                        status="failed",
                        error_message=result.error,
                        log_file=result.log_file,
                        execution_result=execution_result_dict,
                    )

                return result

            except Exception as e:
                error_msg = get_message_with_format(
                    "document_processing_failed", error=str(e)
                )
                print(error_msg)

                # 更新任务状态为失败
                if wt_info:
                    execution_result_dict = {
                        "success": False,
                        "output": "",
                        "error": error_msg,
                        "log_file": "",
                    }
                    self.worktree_manager.update_task_status(
                        task_id=wt_info.name,
                        status="failed",
                        error_message=error_msg,
                        execution_result=execution_result_dict,
                    )

                # 清理失败的 worktree
                if wt_info:
                    try:
                        print(
                            get_message_with_format(
                                "cleaning_failed_worktree", name=wt_info.name
                            )
                        )
                        self.worktree_manager.cleanup_worktree(wt_info)
                    except Exception as cleanup_error:
                        print(
                            get_message_with_format(
                                "cleanup_worktree_warning", error=str(cleanup_error)
                            )
                        )

                return ExecutionResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = get_message_with_format(
                "document_processing_unexpected_error", error=str(e)
            )
            print(error_msg)

            # 尝试清理 worktree（如果已创建）
            if wt_info:
                try:
                    print(
                        get_message_with_format("cleaning_worktree", name=wt_info.name)
                    )
                    self.worktree_manager.cleanup_worktree(wt_info)
                except Exception as cleanup_error:
                    print(
                        get_message_with_format(
                            "cleanup_worktree_warning", error=str(cleanup_error)
                        )
                    )

            return ExecutionResult(success=False, error=error_msg)

    def _generate_worktree_name(self, doc: Document, timestamp: str) -> str:
        """生成 worktree 名称，格式：[task_prefix_]<base_name>_<时间>_<uuid>"""
        # 如果用户指定了 worktree 名称，则使用指定的名称
        if self.worktree_name:
            base = self._sanitize_worktree_name(self.worktree_name)
            # 如果是第一个文档（或者只有一个文档），直接使用指定名称
            if doc.index == 0:
                return base
            else:
                # 如果有多个文档，为后续文档添加序号后缀
                return f"{base}_{doc.index+1:02d}"

        # 原有的自动生成逻辑
        base_name = "stdin"
        if doc.original_file and doc.original_file != "stdin":
            base_name = Path(doc.original_file).stem

        # 生成短UUID（8位）
        short_uuid = str(uuid.uuid4()).replace("-", "")[:8]

        # 构建名称部分
        name_parts = []
        if self.task_prefix:
            name_parts.append(self.task_prefix)

        if doc.index == 0:
            name_parts.extend([base_name, timestamp, short_uuid])
        else:
            name_parts.extend([f"{base_name}_{doc.index+1:02d}", timestamp, short_uuid])

        return "_".join(name_parts)

    def _get_document_info(self, doc: Document) -> str:
        """获取文档信息"""
        content_preview = doc.content
        if len(content_preview) > 100:
            content_preview = content_preview[:100] + "..."

        return (
            f"文件: {doc.original_file}, 部分: {doc.index+1}, "
            f"临时文件: {doc.temp_filename}, 内容预览: {content_preview}"
        )

    def cleanup_all_worktrees(self, pattern: str = "") -> None:
        """清理所有 worktree"""
        if self.worktree_manager:
            print(get_message("cleanup_all_worktrees"))
            self.worktree_manager.cleanup_all_worktrees(pattern)
