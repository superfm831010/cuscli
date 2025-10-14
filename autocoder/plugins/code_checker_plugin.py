"""
Code Checker Plugin for Chat Auto Coder.
提供代码规范检查功能的插件。

功能:
- /check /file <filepath> - 检查单个文件
- /check /folder [/path <dir>] [/ext .py,.js] [/ignore tests] - 检查目录
- /check /resume [check_id] - 恢复中断的检查
- /check /report [check_id] - 查看检查报告

作者: Claude AI
创建时间: 2025-10-10
"""

import os
import shlex
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime

from autocoder.plugins import Plugin, PluginManager
from loguru import logger
from autocoder.checker.git_helper import GitFileHelper, TempFileManager
from autocoder.checker.types import GitInfo


class CodeCheckerPlugin(Plugin):
    """代码检查插件"""

    name = "code_checker"
    description = "代码规范检查插件，支持检查单文件和批量检查目录"
    version = "1.0.0"

    # 需要动态补全的命令
    dynamic_cmds = [
        "/check /file",
        "/check /resume",
        "/check /config",
        "/check /folder",
        "/check /git /commit",
        "/check /git /diff",
    ]

    def __init__(
        self,
        manager: PluginManager,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None
    ):
        """初始化插件"""
        super().__init__(manager, config, config_path)

        # 延迟初始化 checker，在实际使用时才初始化
        self.checker = None
        self.rules_loader = None
        self.file_processor = None
        self.report_generator = None
        self.progress_tracker = None
        self.checker_defaults = {
            "repeat": 1,
            "consensus": 1.0,  # 单次调用模式，快速检查
        }

    def initialize(self) -> bool:
        """
        初始化插件

        Returns:
            True 如果初始化成功
        """
        try:
            # 导入所需模块
            from autocoder.checker.rules_loader import RulesLoader
            from autocoder.checker.file_processor import FileProcessor
            from autocoder.checker.report_generator import ReportGenerator
            from autocoder.checker.progress_tracker import ProgressTracker

            # 初始化不需要 LLM 的组件
            self.rules_loader = RulesLoader()
            self.file_processor = FileProcessor()
            self.report_generator = ReportGenerator()
            self.progress_tracker = ProgressTracker()

            self._load_checker_defaults()

            logger.info(f"[{self.name}] 代码检查插件初始化成功")
            logger.info(f"[{self.name}] CodeChecker 将在首次使用时初始化")

            return True

        except Exception as e:
            logger.error(f"[{self.name}] 初始化失败: {e}", exc_info=True)
            print(f"⚠️  代码检查插件初始化失败: {e}")
            return False

    def _ensure_checker(self):
        """
        确保 checker 已初始化

        CodeChecker 需要 LLM 实例，只在实际使用时才初始化
        """
        if self.checker is not None:
            return

        try:
            # 导入需要的模块
            from autocoder.checker.core import CodeChecker
            from autocoder.auto_coder import AutoCoderArgs
            from autocoder.utils.llms import get_single_llm
            from autocoder.common.core_config import get_memory_manager
            from autocoder.common.llms import LLMManager

            # 获取配置
            memory_manager = get_memory_manager()
            conf = memory_manager.get_all_config()

            # 智能获取模型配置
            # 1. 优先使用 chat_model（chat 模式专用）
            # 2. 其次使用 model（通用模型）
            # 3. 最后尝试获取第一个可用模型
            model_name = conf.get("chat_model") or conf.get("model")

            if not model_name:
                # 如果配置中没有模型，尝试从 LLMManager 获取第一个有 API key 的模型
                llm_manager = LLMManager()
                all_models = llm_manager.get_all_models()

                # 查找第一个有 API key 的模型
                for name, model in all_models.items():
                    if llm_manager.has_key(name):
                        model_name = name
                        logger.info(f"[{self.name}] 配置中未指定模型，自动选择: {model_name}")
                        break

                if not model_name:
                    raise RuntimeError(
                        "未配置模型，且未找到可用的模型\n"
                        "请使用以下方式之一配置模型：\n"
                        "1. /models /add <model_name> <api_key> - 添加并激活模型\n"
                        "2. /config model <model_name> - 设置当前使用的模型"
                    )

            product_mode = conf.get("product_mode", "lite")

            # 获取 LLM 实例
            llm = get_single_llm(model_name, product_mode)
            if llm is None:
                raise RuntimeError(
                    f"无法获取 LLM 实例 (model={model_name}, mode={product_mode})\n"
                    "可能的原因：\n"
                    "1. 模型未配置 API key，请使用: /models /add {model_name} <api_key>\n"
                    "2. 模型不存在，请使用: /models /list 查看可用模型"
                )

            # 根据插件配置构建 CodeChecker 相关参数
            checker_config: Dict[str, Any] = self.config.get("checker", {}) if self.config else {}
            llm_config: Dict[str, Any] = {}
            args_kwargs: Dict[str, Any] = {}

            if isinstance(checker_config, dict):
                raw_llm_cfg = checker_config.get("llm") or checker_config.get("llm_config")
                if isinstance(raw_llm_cfg, dict):
                    llm_config.update(raw_llm_cfg)

                if "llm_temperature" in checker_config:
                    args_kwargs["checker_llm_temperature"] = checker_config["llm_temperature"]
                if "llm_top_p" in checker_config:
                    args_kwargs["checker_llm_top_p"] = checker_config["llm_top_p"]
                if "llm_seed" in checker_config:
                    args_kwargs["checker_llm_seed"] = checker_config["llm_seed"]

                if "chunk_overlap_multiplier" in checker_config:
                    args_kwargs["checker_chunk_overlap_multiplier"] = checker_config["chunk_overlap_multiplier"]
                if "chunk_token_limit" in checker_config:
                    args_kwargs["checker_chunk_token_limit"] = checker_config["chunk_token_limit"]

            if llm_config:
                args_kwargs["checker_llm_config"] = llm_config

            # 创建一个基础的 Args 对象，注入检查器配置
            args = AutoCoderArgs(**args_kwargs)

            # 初始化 CodeChecker
            self.checker = CodeChecker(llm, args)

            logger.info(f"[{self.name}] CodeChecker 初始化成功 (model={model_name})")
            self._apply_checker_options({})

        except ImportError as e:
            error_msg = f"无法导入所需模块: {e}\n请确保已完成 Phase 1-6 的开发"
            logger.error(f"[{self.name}] {error_msg}")
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"CodeChecker 初始化失败: {e}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            raise RuntimeError(error_msg)

    def get_commands(self) -> Dict[str, Tuple[Callable, str]]:
        """
        注册命令

        Returns:
            命令字典 {命令名: (处理函数, 描述)}
        """
        return {
            "check": (self.handle_check, "代码规范检查命令"),
        }

    def get_completions(self) -> Dict[str, List[str]]:
        """
        提供静态补全

        Returns:
            补全字典 {命令前缀: 补全选项列表}
        """
        return {
            "/check": ["/file", "/folder", "/resume", "/report", "/config", "/git"],
            "/check /folder": ["/path", "/ext", "/ignore", "/workers", "/repeat", "/consensus"],
            "/check /config": ["/repeat", "/consensus"],
            "/check /git": ["/staged", "/unstaged", "/commit", "/diff"],
            "/check /git /staged": ["/repeat", "/consensus", "/workers", "/diff-only"],
            "/check /git /unstaged": ["/repeat", "/consensus", "/workers", "/diff-only"],
            "/check /git /commit": ["/repeat", "/consensus", "/workers", "/diff-only"],
            "/check /git /diff": ["/repeat", "/consensus", "/workers", "/diff-only"],
        }

    def _get_option_completions(
        self, command: str, current_input: str
    ) -> List[Tuple[str, str]]:
        """
        获取命令的选项补全（如 /repeat、/consensus、/workers、/diff-only）

        Args:
            command: 命令，如 "/check /git /diff"
            current_input: 当前完整输入

        Returns:
            补全选项列表 [(补全文本, 显示文本), ...]
        """
        # 从 get_completions() 获取该命令的选项列表
        completions_dict = self.get_completions()
        options = completions_dict.get(command, [])

        if not options:
            return []

        # 解析当前输入，获取已经输入的选项
        tokens = shlex.split(current_input)
        base_tokens = command.split()

        # 提取已经输入的选项（以 / 开头的参数）
        existing_options = set()
        for i in range(len(base_tokens), len(tokens)):
            if tokens[i].startswith('/'):
                existing_options.add(tokens[i])

        # 判断当前是否在输入选项（末尾是否有正在输入的选项前缀）
        prefix = ""
        if current_input.endswith(" "):
            # 末尾有空格，前缀为空
            prefix = ""
        elif len(tokens) > len(base_tokens):
            # 检查最后一个 token 是否是选项前缀
            last_token = tokens[-1]
            if last_token.startswith('/'):
                prefix = last_token

        # 过滤掉已输入的选项，并匹配前缀
        suggestions: List[Tuple[str, str]] = []
        for option in options:
            # 跳过已经输入过的选项
            if option in existing_options:
                continue
            # 匹配前缀
            if not prefix or option.startswith(prefix):
                suggestions.append((option, option))

        return suggestions

    def get_dynamic_completions(
        self, command: str, current_input: str
    ) -> List[Tuple[str, str]]:
        """
        提供动态补全

        Args:
            command: 基础命令，如 "/check /file"
            current_input: 当前完整输入

        Returns:
            补全选项列表 [(补全文本, 显示文本), ...]
        """
        if command == "/check /file":
            # 文件路径补全
            return self._complete_file_path(current_input)

        elif command == "/check /resume":
            # check_id 补全
            return self._complete_check_id(current_input)

        elif command in {"/check /config", "/check /folder"}:
            tokens = shlex.split(current_input)
            base_tokens = command.split()

            if current_input.endswith(" "):
                prefix = ""
            elif len(tokens) > len(base_tokens):
                prefix = tokens[-1]
            else:
                prefix = ""

            suggestions: List[Tuple[str, str]] = []
            for option in ["/repeat", "/consensus"]:
                if not prefix or option.startswith(prefix):
                    suggestions.append((option, option))

            return suggestions

        elif command == "/check /git /commit":
            # Git commit 补全 - 先补全 commit，然后补全选项
            tokens = shlex.split(current_input)
            base_tokens = command.split()  # ["/check", "/git", "/commit"]

            # 计算已输入的非选项参数数量（不以 / 开头的参数）
            non_option_args = []
            for i in range(len(base_tokens), len(tokens)):
                if not tokens[i].startswith('/'):
                    non_option_args.append(tokens[i])

            # 判断当前应该补全什么
            has_trailing_space = current_input != current_input.rstrip()

            if has_trailing_space:
                # 末尾有空格，说明当前参数已完成
                if len(non_option_args) == 0:
                    # 还没有输入 commit，补全 commit
                    return self._complete_git_commits(current_input)
                else:
                    # 已有 commit，补全选项
                    return self._get_option_completions(command, current_input)
            else:
                # 末尾没有空格，正在输入当前参数
                if len(non_option_args) == 0:
                    # 正在输入 commit
                    return self._complete_git_commits(current_input)
                else:
                    # 正在输入选项或其他参数
                    last_token = tokens[-1]
                    if last_token.startswith('/'):
                        # 正在输入选项，返回选项补全
                        return self._get_option_completions(command, current_input)
                    else:
                        # 可能在继续输入 commit hash，不补全
                        return []

        elif command == "/check /git /diff":
            # Git diff 补全 - 支持两个 commit 参数，然后补全选项
            tokens = shlex.split(current_input)
            base_tokens = command.split()  # ["/check", "/git", "/diff"]

            # 计算已输入的非选项参数数量（不以 / 开头的参数）
            non_option_args = []
            for i in range(len(base_tokens), len(tokens)):
                if not tokens[i].startswith('/'):
                    non_option_args.append(tokens[i])

            # 判断当前应该补全第几个 commit
            # 关键：先检查是否有尾部空格，判断用户是否完成当前参数输入
            has_trailing_space = current_input != current_input.rstrip()

            if has_trailing_space:
                # 末尾有空格，说明当前参数已完成，准备输入下一个
                if len(non_option_args) == 0:
                    # 还没有输入任何 commit，补全第一个
                    return self._complete_git_commits(current_input)
                elif len(non_option_args) == 1:
                    # 已有1个 commit，补全第二个
                    return self._complete_git_commits(current_input)
                else:
                    # 已经有两个 commit 了，补全选项
                    return self._get_option_completions(command, current_input)
            else:
                # 末尾没有空格，正在输入当前参数
                if len(non_option_args) == 0:
                    # 正在输入第一个 commit
                    return self._complete_git_commits(current_input)
                elif len(non_option_args) == 1:
                    # 正在输入第二个 commit
                    return self._complete_git_commits(current_input)
                else:
                    # 正在输入第三个参数
                    last_token = tokens[-1]
                    if last_token.startswith('/'):
                        # 正在输入选项，返回选项补全
                        return self._get_option_completions(command, current_input)
                    else:
                        # 可能在继续输入 commit hash，不补全
                        return []

        return []

    def _complete_file_path(self, current_input: str) -> List[Tuple[str, str]]:
        """
        补全文件路径

        Args:
            current_input: 当前输入

        Returns:
            补全选项列表
        """
        parts = current_input.split()
        prefix = parts[-1] if len(parts) > 2 else ""

        # 获取目录和文件前缀
        dir_path = os.path.dirname(prefix) or "."
        file_prefix = os.path.basename(prefix)

        completions = []
        if os.path.isdir(dir_path):
            try:
                for entry in os.listdir(dir_path):
                    if entry.startswith(file_prefix):
                        full_path = os.path.join(dir_path, entry)
                        # 目录添加 /，文件不添加
                        display = entry + ("/" if os.path.isdir(full_path) else "")
                        completions.append((full_path, display))
            except PermissionError:
                pass  # 忽略无权限的目录

        return completions

    def _complete_check_id(self, current_input: str) -> List[Tuple[str, str]]:
        """
        补全 check_id（可恢复的检查）

        Args:
            current_input: 当前输入

        Returns:
            补全选项列表
        """
        # 获取所有检查记录
        checks = self.progress_tracker.list_checks()

        # 过滤出未完成的检查
        incomplete = [c for c in checks if c.get("status") == "incomplete"]

        # 构造补全选项
        completions = []
        for check in incomplete:
            check_id = check.get("check_id", "")
            progress = check.get("progress", "0/0")
            display = f"{check_id} ({progress})"
            completions.append((check_id, display))

        return completions

    def _complete_git_commits(self, current_input: str) -> List[Tuple[str, str]]:
        """
        补全 git commits（用于 /check /git /commit 和 /check /git /diff）

        Args:
            current_input: 当前输入

        Returns:
            补全选项列表 [(完整引用, 显示文本), ...]
        """
        completions = []

        try:
            # 初始化 GitFileHelper
            git_helper = GitFileHelper()

            # 1. 获取本地未推送的 commits（优先显示）
            local_commits = []
            try:
                # 检查是否有远程分支
                repo = git_helper.repo
                if repo.heads:
                    current_branch = repo.active_branch
                    # 尝试获取对应的远程跟踪分支
                    if current_branch.tracking_branch():
                        remote_branch = current_branch.tracking_branch()
                        # 获取本地领先远程的 commits
                        local_only = list(repo.iter_commits(f'{remote_branch.name}..{current_branch.name}'))

                        for commit in local_only:
                            short_hash = commit.hexsha[:7]
                            message = commit.message.strip().split('\n')[0]
                            if len(message) > 45:
                                message = message[:42] + "..."

                            # 添加 [本地] 标记
                            display = f"{short_hash} - [本地] {message}"
                            local_commits.append((short_hash, display))

                        logger.debug(f"找到 {len(local_commits)} 个本地未推送的 commits")
            except Exception as e:
                logger.debug(f"获取本地 commits 失败（可能没有远程分支）: {e}")

            # 将本地 commits 添加到补全列表
            completions.extend(local_commits)

            # 2. 获取最近20个 commits 的短哈希和消息（排除已添加的本地 commits）
            try:
                # 使用 GitPython 获取最近20个 commits
                commits = list(git_helper.repo.iter_commits('HEAD', max_count=20))

                # 已添加的本地 commits 的哈希集合
                local_hashes = {c[0] for c in local_commits}

                for commit in commits:
                    short_hash = commit.hexsha[:7]

                    # 跳过已经作为本地 commit 添加的
                    if short_hash in local_hashes:
                        continue

                    # 获取第一行 commit 消息
                    message = commit.message.strip().split('\n')[0]
                    # 截断过长的消息
                    if len(message) > 50:
                        message = message[:47] + "..."

                    # 格式化显示
                    display = f"{short_hash} - {message}"
                    completions.append((short_hash, display))

            except Exception as e:
                logger.warning(f"获取 commits 失败: {e}")

            # 3. 添加常用的相对引用
            relative_refs = [
                ("HEAD", "HEAD (最新 commit)"),
                ("HEAD~1", "HEAD~1 (前1个 commit)"),
                ("HEAD~2", "HEAD~2 (前2个 commit)"),
                ("HEAD~3", "HEAD~3 (前3个 commit)"),
                ("HEAD~5", "HEAD~5 (前5个 commit)"),
                ("HEAD~10", "HEAD~10 (前10个 commit)"),
            ]

            for ref, display in relative_refs:
                completions.append((ref, display))

            # 4. 添加分支名
            try:
                branches = [b.name for b in git_helper.repo.branches]
                for branch in branches[:5]:  # 最多显示5个分支
                    completions.append((branch, f"{branch} (分支)"))
            except Exception as e:
                logger.warning(f"获取分支失败: {e}")

        except Exception as e:
            logger.warning(f"Git 补全失败: {e}")
            # 降级：返回基本的相对引用
            completions = [
                ("HEAD", "HEAD"),
                ("HEAD~1", "HEAD~1"),
                ("HEAD~2", "HEAD~2"),
                ("HEAD~3", "HEAD~3"),
            ]

        return completions

    def handle_check(self, args: str) -> None:
        """
        处理 /check 命令

        命令格式:
        - /check /file <filepath>
        - /check /folder [options]
        - /check /resume [check_id]
        - /check /report [check_id]

        Args:
            args: 命令参数
        """
        args = args.strip()

        # 如果没有子命令，显示帮助
        if not args:
            self._show_help()
            return

        # 解析子命令
        parts = args.split(maxsplit=1)
        subcommand = parts[0]
        sub_args = parts[1] if len(parts) > 1 else ""

        # 路由到对应的处理函数
        if subcommand == "/file":
            self._check_file(sub_args)
        elif subcommand == "/config":
            self._config_checker(sub_args)
        elif subcommand == "/folder":
            self._check_folder(sub_args)
        elif subcommand == "/resume":
            self._resume_check(sub_args)
        elif subcommand == "/report":
            self._show_report(sub_args)
        elif subcommand == "/git":
            self._check_git(sub_args)
        else:
            print(f"❌ 未知的子命令: {subcommand}")
            self._show_help()

    def _show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
📋 代码检查命令帮助

使用方法:
  /check /file <filepath>              - 检查单个文件
  /check /config [/repeat <次数>] [/consensus <0-1>] - 设置默认 LLM 重试与共识阈值
  /check /folder [options]             - 检查目录
  /check /resume [check_id]            - 恢复中断的检查
  /check /report [check_id]            - 查看检查报告

  /check /git /staged [options]        - 检查暂存区文件 (NEW)
  /check /git /unstaged [options]      - 检查工作区修改 (NEW)
  /check /git /commit <ref> [options]  - 检查指定 commit (NEW)
  /check /git /diff <ref1> [ref2] [opts] - 检查 commit 差异 (NEW)

Git 引用格式 (commit/diff 命令支持):
  HEAD, HEAD~N                         - 相对引用 (HEAD~1=前1个commit)
  <branch>                             - 分支名 (如 main, dev)
  <tag>                                - 标签名 (如 v1.0.0)
  <hash>                               - 完整或短哈希值 (如 abc1234)

/check /folder 选项:
  /path <dir>                          - 指定检查目录（默认: 当前目录）
  /ext <.py,.js>                       - 指定文件扩展名（逗号分隔）
  /ignore <tests,__pycache__>          - 忽略目录/文件（逗号分隔）
  /workers <5>                         - 并发数（默认: 5）
  /repeat <1>                          - LLM 调用次数（默认: 1）
  /consensus <1.0>                     - 共识阈值 0~1（默认: 1.0）

/check /git 通用选项:
  /repeat <1>                          - LLM 调用次数（默认: 1）
  /consensus <1.0>                     - 共识阈值 0~1（默认: 1.0）
  /workers <5>                         - 并发数（默认: 5）

示例:
  /check /file autocoder/auto_coder.py
  /check /file autocoder/auto_coder.py /repeat 3 /consensus 0.8
  /check /folder
  /check /folder /path src /ext .py
  /check /folder /path src /ext .py /ignore tests,__pycache__ /repeat 3

  # Git 检查示例
  /check /git /staged                    # 检查暂存区
  /check /git /unstaged                  # 检查工作区修改
  /check /git /commit HEAD               # 检查最新 commit
  /check /git /commit HEAD~1             # 检查前1个 commit
  /check /git /commit main               # 检查 main 分支最新 commit
  /check /git /commit abc1234            # 使用哈希值
  /check /git /diff HEAD~3 HEAD          # 检查最近3个 commits
  /check /git /diff main dev             # 检查两个分支的差异

  /check /resume check_20250110_143022
  /check /report check_20250110_143022
        """
        print(help_text)

    def _check_file(self, args: str) -> None:
        """
        检查单个文件

        Args:
            args: 文件路径
        """
        tokens = shlex.split(args)
        if not tokens:
            print("❌ 请指定文件路径")
            print("用法: /check /file <filepath> [/repeat <次数>] [/consensus <0-1>]")
            return

        file_path = tokens[0]
        option_tokens = tokens[1:]
        common_options = self._parse_common_options(option_tokens)

        if not file_path:
            print("❌ 请指定文件路径")
            print("用法: /check /file <filepath> [/repeat <次数>] [/consensus <0-1>]")
            return

        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return

        if not os.path.isfile(file_path):
            print(f"❌ 不是文件: {file_path}")
            return

        print(f"🔍 正在检查文件: {file_path}")
        print()

        try:
            # 确保 checker 已初始化
            self._ensure_checker()

            # 应用共识参数
            self._apply_checker_options(common_options)

            # 导入进度显示组件
            from autocoder.checker.progress_display import ProgressDisplay, SimpleProgressCallback

            # 使用新的进度显示系统
            progress_display = ProgressDisplay()

            with progress_display.display_progress():
                # 创建进度回调适配器（传递repeat和consensus参数）
                progress_callback = SimpleProgressCallback(
                    progress_display,
                    file_path,
                    repeat=self.checker.llm_repeat,
                    consensus=self.checker.llm_consensus_ratio
                )

                # 执行检查（传入进度回调）
                result = self.checker.check_file(file_path, progress_callback=progress_callback)

            # 显示结果
            if result.status == "success":
                print("✅ 检查完成！")
                print()
                print(f"文件: {result.file_path}")
                print(f"发现问题: {len(result.issues)}")
                print(f"├─ ❌ 错误: {result.error_count}")
                print(f"├─ ⚠️  警告: {result.warning_count}")
                print(f"└─ ℹ️  提示: {result.info_count}")

                # 生成报告
                check_id = self._create_check_id()
                report_dir = self._create_report_dir(check_id)

                try:
                    self.report_generator.generate_file_report(result, report_dir)

                    # 根据是否有问题决定显示哪个目录
                    has_issues = len(result.issues) > 0
                    subdir = "with_issues" if has_issues else "no_issues"

                    # 构建文件路径
                    safe_filename = self.report_generator._safe_path(file_path)
                    md_path = os.path.join(report_dir, 'files', subdir, f"{safe_filename}.md")
                    json_path = os.path.join(report_dir, 'files', subdir, f"{safe_filename}.json")

                    # 验证文件是否真的存在
                    md_exists = os.path.exists(md_path)
                    json_exists = os.path.exists(json_path)

                    print()
                    if md_exists and json_exists:
                        print(f"📄 报告已保存到: {report_dir}")
                        print(f"   - {md_path}")
                        print(f"   - {json_path}")

                        # 提示日志文件位置
                        log_path = os.path.join(report_dir, 'check.log')
                        if os.path.exists(log_path):
                            print(f"📋 详细日志: {log_path}")
                    else:
                        print("⚠️  报告生成部分失败:")
                        if not md_exists:
                            print(f"   ❌ Markdown 报告未创建: {md_path}")
                        if not json_exists:
                            print(f"   ❌ JSON 报告未创建: {json_path}")
                        print()
                        print("💡 可能的原因:")
                        print("   - 磁盘空间不足")
                        print("   - 文件路径过长或包含特殊字符")
                        print("   - 文件系统权限限制")

                        # 提示可以查看日志
                        log_path = os.path.join(report_dir, 'check.log')
                        if os.path.exists(log_path):
                            print()
                            print(f"💡 查看详细日志: {log_path}")

                except Exception as e:
                    print()
                    print(f"❌ 报告生成失败: {e}")
                    print()
                    print("💡 排查建议:")
                    print("   1. 检查磁盘空间是否充足")
                    print("   2. 检查当前目录是否有写入权限")
                    print("   3. 检查文件路径是否包含特殊字符")
                    print(f"   4. 查看详细日志: .auto-coder/logs/auto-coder.log")
                    logger.error(f"报告生成失败: {e}", exc_info=True)

            elif result.status == "skipped":
                print(f"⏭️  文件已跳过: {file_path}")
                print("   原因: 无适用的检查规则")

            elif result.status == "timeout":
                print(f"⏱️  文件检查超时: {file_path}")
                print(f"   错误: {result.error_message}")

            elif result.status == "failed":
                print(f"❌ 检查失败: {file_path}")
                print(f"   错误: {result.error_message}")

        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            logger.error(f"检查文件失败: {e}", exc_info=True)

    def _check_folder(self, args: str) -> None:
        """
        检查目录

        Args:
            args: 选项参数
                /path <dir> - 指定目录
                /ext <.py,.js> - 指定扩展名
                /ignore <tests,__pycache__> - 忽略目录/文件
                /workers <5> - 并发数
        """
        # 解析参数
        options = self._parse_folder_options(args)

        path = options.get("path", ".")
        extensions = options.get("extensions", None)
        ignored = options.get("ignored", None)
        workers = options.get("workers", 5)

        print(f"🔍 正在检查目录: {path}")
        print()

        # 检查目录是否存在
        if not os.path.exists(path):
            print(f"❌ 目录不存在: {path}")
            return

        if not os.path.isdir(path):
            print(f"❌ 不是目录: {path}")
            return

        check_id = None

        try:
            # 导入所需模块
            from autocoder.checker.types import FileFilters
            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
                TimeRemainingColumn,
            )

            # 扫描文件
            filters = FileFilters(
                extensions=extensions if extensions else None,
                ignored=ignored if ignored else None
            )

            print("📂 扫描文件...")
            files = self.file_processor.scan_files(path, filters)

            if not files:
                print("⚠️  未找到符合条件的文件")
                return

            print(f"✅ 找到 {len(files)} 个文件")
            print()

            # 确保 checker 已初始化
            self._ensure_checker()

            # 应用 repeat/consensus 参数（如果用户指定了）
            repeat_opt = options.get("repeat")
            consensus_opt = options.get("consensus")
            if repeat_opt is not None or consensus_opt is not None:
                self._apply_checker_options({
                    "repeat": repeat_opt,
                    "consensus": consensus_opt,
                })

            # 创建检查任务并保存状态（Task 8.1: 进度持久化）
            project_name = os.path.basename(os.getcwd())
            # 清理项目名称
            project_name = "".join(c if c.isalnum() or c == "_" else "_" for c in project_name)

            # 生成 check_id 并创建报告目录
            check_id = self._create_check_id()
            report_dir = self._create_report_dir(check_id)

            # 启动任务日志记录
            from autocoder.checker.task_logger import TaskLogger
            task_logger = TaskLogger(report_dir)
            task_logger.start()

            try:
                logger.info(f"开始检查任务: {check_id}, 文件数: {len(files)}, 并发: {workers}")

                # 创建检查任务状态
                check_id = self.progress_tracker.start_check(
                    files=files,
                    config={
                        "path": path,
                        "extensions": extensions,
                        "ignored": ignored,
                        "workers": workers
                    },
                    project_name=project_name,
                    report_dir=report_dir
                )

                print(f"📝 检查任务 ID: {check_id}")
                print(f"📄 报告目录: {report_dir}")
                print(f"📋 任务日志: {task_logger.get_log_path()}")
                print()

                # 导入进度显示组件
                from autocoder.checker.progress_display import ProgressDisplay

                # 批量检查（Task 9.2: 使用并发检查）
                results = []
                check_interrupted = False
                snapshot_interval = 100  # 每100个文件生成一次快照

                # 使用新的进度显示系统
                progress_display = ProgressDisplay()

                # 更新 LLM 配置显示（与单文件审核保持一致）
                progress_display.update_llm_config(
                    repeat=self.checker.llm_repeat,
                    consensus=self.checker.llm_consensus_ratio
                )

                # 创建线程安全的并发进度回调
                from threading import Lock
                update_lock = Lock()

                def concurrent_progress_callback(step: str, **kwargs):
                    """并发场景下的进度回调（线程安全）"""
                    with update_lock:
                        if step == "chunked":
                            progress_display.update_chunk_progress(
                                total_chunks=kwargs.get("total_chunks", 0),
                                completed_chunks=0
                            )
                        elif step == "chunk_start":
                            progress_display.update_chunk_progress(
                                current_chunk=kwargs.get("chunk_index", 0),
                                chunk_info={
                                    "start_line": kwargs.get("start_line"),
                                    "end_line": kwargs.get("end_line"),
                                    "tokens": kwargs.get("tokens"),
                                }
                            )
                        elif step == "chunk_done":
                            progress_display.update_chunk_progress(
                                completed_chunks=kwargs.get("chunk_index", 0) + 1
                            )
                        elif step == "llm_call_start":
                            progress_display.update_llm_progress(
                                event="start",
                                attempt=kwargs.get("attempt", 1),
                                total_attempts=kwargs.get("total_attempts", 1)
                            )
                        elif step == "llm_call_end":
                            progress_display.update_llm_progress(
                                event="end",
                                attempt=kwargs.get("attempt", 1),
                                duration=kwargs.get("duration", 0.0),
                                issues_found=kwargs.get("issues_found", 0)
                            )
                        elif step == "merge_done":
                            # 并发场景下，保留最新活动信息，不立即清空
                            # 这样用户可以持续看到检查详情（虽然会在不同文件间切换）
                            pass

                try:
                    with progress_display.display_progress():
                        # 初始化文件级进度
                        progress_display.update_file_progress(
                            total_files=len(files),
                            completed_files=0
                        )

                        # Task 9.2: 使用并发检查（传递进度回调）
                        for idx, result in enumerate(
                            self.checker.check_files_concurrent(files, max_workers=workers, progress_callback=concurrent_progress_callback),
                            1
                        ):
                            results.append(result)

                            # 立即保存结果到持久化存储（防止数据丢失）
                            try:
                                self.progress_tracker.save_file_result(check_id, result)
                            except Exception as e:
                                logger.error(f"保存文件结果失败 {result.file_path}: {e}", exc_info=True)

                            # Task 8.1: 标记文件完成，保存进度
                            self.progress_tracker.mark_completed(check_id, result.file_path)

                            # 更新文件级进度
                            progress_display.update_file_progress(
                                completed_files=idx
                            )

                            # 每100个文件生成一次快照
                            if idx % snapshot_interval == 0:
                                logger.info(f"已完成 {idx}/{len(files)} 个文件，生成中间快照")
                                try:
                                    # 生成中间报告
                                    self.report_generator.generate_summary_report(
                                        results,
                                        report_dir
                                    )
                                    logger.info(f"中间快照已生成: {idx} 个文件")
                                except Exception as e:
                                    logger.error(f"生成中间快照失败: {e}", exc_info=True)

                except KeyboardInterrupt:
                    # Task 8.1: 处理中断
                    print()
                    print()
                    check_interrupted = True
                    state = self.progress_tracker.load_state(check_id)
                    if state:
                        state.status = "interrupted"
                        self.progress_tracker.save_state(check_id, state)

                    print("⚠️  检查已中断")
                    print(f"   检查 ID: {check_id}")
                    print(f"   已完成: {len(results)}/{len(files)} 个文件")
                    print(f"   剩余: {len(files) - len(results)} 个文件")
                    print()

                    logger.info(f"检查已中断: {check_id}, 已完成 {len(results)}/{len(files)}")

                finally:
                    # 确保即使中断或出错也生成部分报告
                    # 如果 results 为空，尝试从持久化存储加载
                    if not results:
                        logger.warning(f"results 为空，尝试从持久化存储加载...")
                        try:
                            results = self.progress_tracker.load_all_results(check_id)
                            logger.info(f"从持久化存储加载了 {len(results)} 个结果")
                        except Exception as e:
                            logger.error(f"从持久化存储加载结果失败: {e}", exc_info=True)

                    if results:
                        logger.info(f"生成部分报告，已完成 {len(results)} 个文件")

                        # 如果是正常完成，标记状态
                        if not check_interrupted:
                            state = self.progress_tracker.load_state(check_id)
                            if state:
                                state.status = "completed"
                                self.progress_tracker.save_state(check_id, state)

                        # report_dir 已在前面创建，直接使用

                    # 生成单文件报告（统计失败数量）
                    failed_reports = []
                    for result in results:
                        try:
                            self.report_generator.generate_file_report(result, report_dir)
                        except Exception as e:
                            failed_reports.append((result.file_path, str(e)))
                            logger.error(f"生成文件报告失败 {result.file_path}: {e}", exc_info=True)

                    # 生成汇总报告
                    try:
                        self.report_generator.generate_summary_report(results, report_dir)
                    except Exception as e:
                        logger.error(f"生成汇总报告失败: {e}", exc_info=True)
                        print()
                        print(f"⚠️  汇总报告生成失败: {e}")

                    # 如果有报告生成失败，显示警告
                    if failed_reports:
                        print()
                        print(f"⚠️  {len(failed_reports)} 个文件的报告生成失败:")
                        for file_path, error in failed_reports[:5]:  # 最多显示5个
                            print(f"   - {file_path}: {error}")
                        if len(failed_reports) > 5:
                            print(f"   ... 还有 {len(failed_reports) - 5} 个文件")
                        print()
                        print("💡 排查建议:")
                        print("   1. 检查磁盘空间是否充足")
                        print("   2. 检查文件路径是否包含特殊字符")
                        print(f"   3. 查看详细日志: .auto-coder/logs/auto-coder.log")

                    # 显示汇总
                    if check_interrupted:
                        print()
                        print(f"📄 已生成部分报告 ({len(results)}/{len(files)} 个文件)")
                        print(f"   报告位置: {report_dir}/")
                        if failed_reports:
                            print(f"   ⚠️  {len(failed_reports)} 个文件的报告生成失败")
                        print()
                        print(f"💡 使用以下命令恢复检查:")
                        print(f"   /check /resume {check_id}")
                        print()
                    else:
                        self._show_batch_summary(results, report_dir, failed_reports)

            finally:
                # 确保停止任务日志记录器
                task_logger.stop()
                logger.info(f"任务日志已停止: {check_id}")

        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            logger.error(f"检查目录失败: {e}", exc_info=True)

            # 如果创建了检查记录，标记为失败
            if check_id:
                try:
                    state = self.progress_tracker.load_state(check_id)
                    if state and state.status != "completed":
                        state.status = "failed"
                        self.progress_tracker.save_state(check_id, state)
                except Exception:
                    pass

    def _parse_folder_options(self, args: str) -> Dict[str, Any]:
        """
        解析 /check /folder 的选项参数

        Args:
            args: 参数字符串

        Returns:
            选项字典
        """
        options = {
            "path": ".",
            "extensions": None,
            "ignored": None,
            "workers": 5,
            "repeat": None,
            "consensus": None,
        }

        if not args.strip():
            return options

        # 简单的参数解析（/key value 格式）
        parts = shlex.split(args)
        i = 0
        while i < len(parts):
            part = parts[i]

            if part == "/path" and i + 1 < len(parts):
                options["path"] = parts[i + 1]
                i += 2
            elif part == "/ext" and i + 1 < len(parts):
                # 扩展名列表，逗号分隔
                exts = parts[i + 1].split(",")
                options["extensions"] = [ext.strip() for ext in exts]
                i += 2
            elif part == "/ignore" and i + 1 < len(parts):
                # 忽略列表，逗号分隔
                ignores = parts[i + 1].split(",")
                options["ignored"] = [ign.strip() for ign in ignores]
                i += 2
            elif part == "/workers" and i + 1 < len(parts):
                try:
                    options["workers"] = int(parts[i + 1])
                except ValueError:
                    print(f"⚠️  无效的并发数: {parts[i + 1]}，使用默认值 5")
                i += 2
            elif part == "/repeat" and i + 1 < len(parts):
                try:
                    options["repeat"] = int(parts[i + 1])
                except ValueError:
                    print(f"⚠️  无效的重复次数: {parts[i + 1]}，使用默认值 1")
                i += 2
            elif part == "/consensus" and i + 1 < len(parts):
                try:
                    options["consensus"] = float(parts[i + 1])
                except ValueError:
                    print(f"⚠️  无效的共识阈值: {parts[i + 1]}，使用默认值 1.0")
                i += 2
            else:
                # 跳过未知选项
                i += 1

        return options

    def _load_checker_defaults(self) -> None:
        """从配置中加载默认的 repeat/consensus 设置"""
        checker_conf = {}
        if isinstance(self.config, dict):
            checker_conf = self.config.get("checker", {}) or {}

        defaults = checker_conf.get("defaults", {}) if isinstance(checker_conf, dict) else {}

        repeat = defaults.get("repeat")
        consensus = defaults.get("consensus")

        if isinstance(repeat, (int, float)):
            self.checker_defaults["repeat"] = max(1, int(repeat))

        if isinstance(consensus, (int, float)) and 0 < float(consensus) <= 1:
            self.checker_defaults["consensus"] = float(consensus)

        logger.info(
            f"[{self.name}] 默认 LLM repeat={self.checker_defaults['repeat']}, "
            f"consensus={self.checker_defaults['consensus']}"
        )

    def _config_checker(self, args: str) -> None:
        """处理 /check /config 命令"""
        tokens = shlex.split(args)

        if not tokens:
            print("当前默认设置：")
            print(f"  repeat = {self.checker_defaults['repeat']}")
            print(f"  consensus = {self.checker_defaults['consensus']}")
            print("用法: /check /config [/repeat <次数>] [/consensus <0-1>]")
            return

        options = self._parse_common_options(tokens)

        updated = False

        if options.get("repeat") is not None:
            try:
                self.checker_defaults["repeat"] = max(1, int(options["repeat"]))
                updated = True
            except (TypeError, ValueError):
                print(f"⚠️  无效的重复次数: {options['repeat']}，保持原值")

        if options.get("consensus") is not None:
            try:
                value = float(options["consensus"])
                if 0 < value <= 1:
                    self.checker_defaults["consensus"] = value
                    updated = True
                else:
                    print("⚠️  共识阈值需在 (0,1] 区间，保持原值")
            except (TypeError, ValueError):
                print(f"⚠️  无效的共识阈值: {options['consensus']}，保持原值")

        if updated:
            if not isinstance(self.config, dict):
                self.config = {}

            checker_conf = self.config.setdefault("checker", {})
            defaults_conf = checker_conf.setdefault("defaults", {})
            defaults_conf["repeat"] = self.checker_defaults["repeat"]
            defaults_conf["consensus"] = self.checker_defaults["consensus"]

            # 持久化配置
            self.export_config()

            if self.checker:
                self._apply_checker_options({})

            print("✅ 默认配置已更新：")
            print(f"  repeat = {self.checker_defaults['repeat']}")
            print(f"  consensus = {self.checker_defaults['consensus']}")
        else:
            print("未修改配置。当前默认值：")
            print(f"  repeat = {self.checker_defaults['repeat']}")
            print(f"  consensus = {self.checker_defaults['consensus']}")

    def _parse_common_options(self, tokens: List[str]) -> Dict[str, Optional[Any]]:
        """解析通用的 LLM 共识相关选项"""
        options: Dict[str, Optional[Any]] = {"repeat": None, "consensus": None}

        if not tokens:
            return options

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == "/repeat" and i + 1 < len(tokens):
                try:
                    options["repeat"] = int(tokens[i + 1])
                except ValueError:
                    print(
                        f"⚠️  无效的重复次数: {tokens[i + 1]}，保持当前默认值"
                    )
                i += 2
            elif token == "/consensus" and i + 1 < len(tokens):
                try:
                    options["consensus"] = float(tokens[i + 1])
                except ValueError:
                    print(
                        f"⚠️  无效的共识阈值: {tokens[i + 1]}，保持当前默认值"
                    )
                i += 2
            else:
                i += 1

        return options

    def _apply_checker_options(self, options: Dict[str, Optional[Any]]) -> None:
        """将解析后的共识参数应用到 CodeChecker"""
        if not self.checker:
            return

        repeat = options.get("repeat")
        consensus = options.get("consensus")

        repeat_value = self.checker_defaults["repeat"]
        if repeat is not None:
            try:
                repeat_value = max(1, int(repeat))
            except (TypeError, ValueError):
                print(
                    f"⚠️  重复次数无效({repeat})，继续使用默认值 {self.checker_defaults['repeat']}"
                )

        consensus_value = self.checker_defaults["consensus"]
        if consensus is not None:
            try:
                consensus_value = float(consensus)
            except (TypeError, ValueError):
                print(
                    f"⚠️  共识阈值无效({consensus})，继续使用默认值 {self.checker_defaults['consensus']}"
                )

        if consensus_value <= 0 or consensus_value > 1:
            print(
                f"⚠️  共识阈值需在 (0,1] 区间，已回退到默认值 {self.checker_defaults['consensus']}"
            )
            consensus_value = self.checker_defaults["consensus"]

        self.checker.llm_repeat = repeat_value
        self.checker.llm_consensus_ratio = consensus_value
        logger.info(
            f"[{self.name}] 使用 LLM repeat={repeat_value}, consensus={consensus_value}"
        )

    def _show_batch_summary(self, results: List, report_dir: str, failed_reports: List = None) -> None:
        """
        显示批量检查汇总

        Args:
            results: 检查结果列表
            report_dir: 报告目录
            failed_reports: 报告生成失败的文件列表 [(file_path, error), ...]
        """
        if failed_reports is None:
            failed_reports = []

        print()
        print("=" * 60)
        print("📊 检查完成！")
        print("=" * 60)
        print()

        # 统计
        total_files = len(results)
        checked_files = len([r for r in results if r.status == "success"])
        skipped_files = len([r for r in results if r.status == "skipped"])
        failed_files = len([r for r in results if r.status == "failed"])
        timeout_files = len([r for r in results if r.status == "timeout"])

        total_issues = sum(len(r.issues) for r in results)
        total_errors = sum(r.error_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        total_infos = sum(r.info_count for r in results)

        print(f"检查文件: {total_files}")
        print(f"├─ ✅ 成功: {checked_files}")
        print(f"├─ ⏭️  跳过: {skipped_files}")
        print(f"├─ ⏱️  超时: {timeout_files}")
        print(f"└─ ❌ 失败: {failed_files}")
        print()

        print(f"总问题数: {total_issues}")
        print(f"├─ ❌ 错误: {total_errors}")
        print(f"├─ ⚠️  警告: {total_warnings}")
        print(f"└─ ℹ️  提示: {total_infos}")
        print()

        # 显示问题最多的文件（前5个）
        if total_issues > 0:
            files_with_issues_list = [(r.file_path, len(r.issues)) for r in results if len(r.issues) > 0]
            files_with_issues_list.sort(key=lambda x: x[1], reverse=True)

            print("问题最多的文件:")
            for i, (file_path, count) in enumerate(files_with_issues_list[:5], 1):
                # 截断过长的路径
                display_path = file_path
                if len(display_path) > 50:
                    display_path = "..." + display_path[-47:]
                print(f"{i}. {display_path} ({count} 个问题)")
            print()

        # 统计有问题和无问题的文件数量
        files_with_issues_count = len([r for r in results if len(r.issues) > 0])
        files_no_issues_count = len([r for r in results if len(r.issues) == 0])

        print(f"📄 详细报告: {report_dir}/")
        print(f"   - 汇总报告: {os.path.join(report_dir, 'summary.md')}")
        print(f"   - 有问题的文件 ({files_with_issues_count} 个): {os.path.join(report_dir, 'files', 'with_issues/')}")
        print(f"   - 无问题的文件 ({files_no_issues_count} 个): {os.path.join(report_dir, 'files', 'no_issues/')}")

        # 显示日志文件
        log_path = os.path.join(report_dir, 'check.log')
        if os.path.exists(log_path):
            print(f"📋 详细日志: {log_path}")
            print("   (包含完整的检查执行过程，便于问题排查)")

        # 显示报告生成失败的信息
        if failed_reports:
            print()
            print(f"⚠️  警告: {len(failed_reports)} 个文件的报告生成失败")
            log_hint = f"或查看日志文件: {log_path}" if os.path.exists(log_path) else ""
            print(f"   请查看上面的详细错误信息{log_hint}")

        print()
        print("💡 提示: 优先查看 files/with_issues/ 目录中的报告进行修复")
        print()
        print("=" * 60)

    def _resume_check(self, args: str) -> None:
        """
        恢复中断的检查

        Task 8.3: 实现 /check /resume 命令

        Args:
            args: check_id（可选）
        """
        check_id = args.strip()

        # 如果没有提供 check_id，列出可恢复的检查
        if not check_id:
            self._list_resumable_checks()
            return

        print(f"🔄 恢复检查: {check_id}")
        print()

        try:
            # 确保 checker 已初始化
            self._ensure_checker()

            # 加载状态
            state = self.progress_tracker.load_state(check_id)
            if not state:
                print(f"❌ 检查记录不存在: {check_id}")
                print()
                print("💡 使用 /check /resume 查看可恢复的检查")
                return

            if state.status == "completed":
                print(f"⚠️  检查任务已完成，无需恢复")
                return

            # 显示进度信息
            remaining = len(state.remaining_files)
            total = len(state.total_files)
            completed = len(state.completed_files)

            print(f"📊 检查进度:")
            print(f"   总文件数: {total}")
            print(f"   已完成: {completed}")
            print(f"   剩余: {remaining}")

            # 提示可以查看日志了解中断原因
            report_dir = os.path.join("codecheck", check_id)
            log_path = os.path.join(report_dir, 'check.log')
            if os.path.exists(log_path):
                print(f"📋 查看详细日志（包含中断前的执行过程）: {log_path}")

            print()

            # 导入进度显示组件
            from autocoder.checker.progress_display import ProgressDisplay

            # 恢复检查（Task 9.2: 使用并发检查）
            # 获取原配置的并发数，如果没有则使用默认值5
            workers = state.config.get("workers", 5)

            # 使用新的进度显示系统
            progress_display = ProgressDisplay()

            # 更新 LLM 配置显示（与单文件审核保持一致）
            progress_display.update_llm_config(
                repeat=self.checker.llm_repeat,
                consensus=self.checker.llm_consensus_ratio
            )

            # 创建线程安全的并发进度回调
            from threading import Lock
            update_lock = Lock()

            def concurrent_progress_callback(step: str, **kwargs):
                """并发场景下的进度回调（线程安全）"""
                with update_lock:
                    if step == "chunked":
                        progress_display.update_chunk_progress(
                            total_chunks=kwargs.get("total_chunks", 0),
                            completed_chunks=0
                        )
                    elif step == "chunk_start":
                        progress_display.update_chunk_progress(
                            current_chunk=kwargs.get("chunk_index", 0),
                            chunk_info={
                                "start_line": kwargs.get("start_line"),
                                "end_line": kwargs.get("end_line"),
                                "tokens": kwargs.get("tokens"),
                            }
                        )
                    elif step == "chunk_done":
                        progress_display.update_chunk_progress(
                            completed_chunks=kwargs.get("chunk_index", 0) + 1
                        )
                    elif step == "llm_call_start":
                        progress_display.update_llm_progress(
                            event="start",
                            attempt=kwargs.get("attempt", 1),
                            total_attempts=kwargs.get("total_attempts", 1)
                        )
                    elif step == "llm_call_end":
                        progress_display.update_llm_progress(
                            event="end",
                            attempt=kwargs.get("attempt", 1),
                            duration=kwargs.get("duration", 0.0),
                            issues_found=kwargs.get("issues_found", 0)
                        )
                    elif step == "merge_done":
                        # 并发场景下，保留最新活动信息，不立即清空
                        # 这样用户可以持续看到检查详情（虽然会在不同文件间切换）
                        pass

            results = []
            with progress_display.display_progress():
                # 初始化文件级进度
                progress_display.update_file_progress(
                    total_files=remaining,
                    completed_files=0
                )

                # Task 9.2: 使用并发检查（传递进度回调）
                for idx, result in enumerate(
                    self.checker.check_files_concurrent(state.remaining_files, max_workers=workers, progress_callback=concurrent_progress_callback),
                    1
                ):
                    results.append(result)

                    # 更新进度
                    self.progress_tracker.mark_completed(check_id, result.file_path)

                    # 更新文件级进度
                    progress_display.update_file_progress(
                        completed_files=idx
                    )

            # 标记检查完成
            state = self.progress_tracker.load_state(check_id)
            if state:
                state.status = "completed"
                self.progress_tracker.save_state(check_id, state)

            # 生成/更新报告
            report_dir = os.path.join("codecheck", check_id)

            # 生成单文件报告
            for result in results:
                self.report_generator.generate_file_report(result, report_dir)

            # 生成汇总报告（注意：这里只包含本次恢复的结果）
            # TODO: 如果需要完整汇总，需要加载之前的结果并合并
            self.report_generator.generate_summary_report(results, report_dir)

            # 显示汇总
            print()
            print("=" * 60)
            print("✅ 恢复完成！")
            print("=" * 60)
            print()
            print(f"本次检查文件: {remaining}")
            total_issues = sum(len(r.issues) for r in results)
            print(f"发现问题: {total_issues}")
            print()
            print(f"📄 详细报告: {report_dir}/")

            # 提示日志文件
            log_path = os.path.join(report_dir, 'check.log')
            if os.path.exists(log_path):
                print(f"📋 详细日志: {log_path}")

            print()

        except ValueError as e:
            # 检查记录不存在或已完成
            print(f"❌ {e}")
        except Exception as e:
            print(f"❌ 恢复检查失败: {e}")
            logger.error(f"恢复检查失败: {e}", exc_info=True)

    def _list_resumable_checks(self) -> None:
        """
        列出可恢复的检查任务

        Task 8.3: 实现可恢复检查列表
        """
        checks = self.progress_tracker.list_checks()

        # 过滤出未完成的检查（interrupted 或 running 状态）
        incomplete = [
            c for c in checks
            if c.get("status") not in ["completed"]
        ]

        if not incomplete:
            print("📭 没有可恢复的检查任务")
            print()
            print("💡 使用 /check /folder 开始新的检查")
            return

        print("📋 可恢复的检查任务:")
        print()

        for i, check in enumerate(incomplete, 1):
            check_id = check.get("check_id", "")
            start_time = check.get("start_time", "")
            status = check.get("status", "")
            completed = check.get("completed", 0)
            total = check.get("total", 0)
            remaining = check.get("remaining", 0)
            progress_pct = check.get("progress", 0.0)

            # 格式化状态显示
            status_icon = {
                "running": "🔄",
                "interrupted": "⏸️",
                "failed": "❌"
            }.get(status, "❓")

            print(f"{i}. {status_icon} {check_id}")
            print(f"   时间: {start_time}")
            print(f"   状态: {status}")
            print(f"   进度: {completed}/{total} ({progress_pct:.1f}%)")
            print(f"   剩余: {remaining} 个文件")
            print()

        print("💡 使用 /check /resume <check_id> 恢复检查")
        print()

    def _show_report(self, args: str) -> None:
        """
        查看检查报告

        Args:
            args: check_id
        """
        # TODO: Task 7.x - 实现报告查看
        print("⚠️  /check /report 功能即将实现")
        print(f"   参数: {args}")

    def _create_check_id(self) -> str:
        """
        生成唯一的检查 ID

        Returns:
            check_id: 格式为 {project_name}_{timestamp}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = os.path.basename(os.getcwd())
        # 清理项目名称中的特殊字符
        project_name = "".join(c if c.isalnum() or c == "_" else "_" for c in project_name)
        return f"{project_name}_{timestamp}"

    def _create_report_dir(self, check_id: str = None) -> str:
        """
        创建报告目录

        Args:
            check_id: 检查 ID，如果为 None 则自动生成

        Returns:
            报告目录路径
        """
        if check_id is None:
            check_id = self._create_check_id()

        report_dir = os.path.join("codecheck", check_id)
        os.makedirs(report_dir, exist_ok=True)
        # 创建分类子目录：有问题和无问题
        os.makedirs(os.path.join(report_dir, "files", "with_issues"), exist_ok=True)
        os.makedirs(os.path.join(report_dir, "files", "no_issues"), exist_ok=True)

        return report_dir

    def _create_check_id_with_prefix(self, prefix: str) -> str:
        """
        生成带前缀的检查 ID

        Args:
            prefix: 前缀（如 git_staged, git_commit_abc1234）

        Returns:
            check_id: 格式为 {prefix}_{timestamp}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"

    # ===== Git 集成功能 =====

    def _check_git(self, args: str) -> None:
        """
        处理 /check /git 命令

        Args:
            args: 子命令和参数
        """
        args = args.strip()

        if not args:
            print("❌ 请指定 git 子命令")
            print()
            print("可用子命令:")
            print("  /check /git /staged              - 检查暂存区文件")
            print("  /check /git /unstaged            - 检查工作区修改文件")
            print("  /check /git /commit <hash>       - 检查指定 commit")
            print("  /check /git /diff <c1> [c2]      - 检查两个 commit 间差异")
            return

        # 解析子命令
        parts = shlex.split(args)
        subcommand = parts[0]
        sub_args = parts[1:]

        # 路由到具体处理函数
        if subcommand == "/staged":
            self._check_git_staged(sub_args)
        elif subcommand == "/unstaged":
            self._check_git_unstaged(sub_args)
        elif subcommand == "/commit":
            self._check_git_commit(sub_args)
        elif subcommand == "/diff":
            self._check_git_diff(sub_args)
        else:
            print(f"❌ 未知的 git 子命令: {subcommand}")

    def _check_git_staged(self, args: List[str]) -> None:
        """
        检查暂存区文件（已 add 但未 commit）

        Args:
            args: 选项参数列表
        """
        print("🔍 检查暂存区文件...")
        print()

        try:
            # 初始化 GitFileHelper
            git_helper = GitFileHelper()

            # 获取暂存区文件
            files = git_helper.get_staged_files()

            if not files:
                print("📭 暂存区没有文件")
                print()
                print("💡 提示: 使用 git add <文件> 将文件添加到暂存区")
                return

            print(f"✅ 找到 {len(files)} 个暂存区文件")
            print()

            # 解析选项
            options = self._parse_git_check_options(args)

            # Phase 3: 如果启用了 diff-only 模式，获取 diff info
            if options.get("diff_only"):
                print("🎯 Diff-Only 模式：将仅审核修改的代码行")
                print()

                try:
                    # 获取 diff 信息
                    diff_info_dict = git_helper.get_staged_diff_info()

                    if not diff_info_dict:
                        print("⚠️  无法获取 diff 信息，将使用全文件审核模式")
                    else:
                        # 计算审核范围统计
                        total_audit_lines = 0
                        for file_path, diff_info in diff_info_dict.items():
                            if diff_info.has_modifications():
                                for hunk in diff_info.hunks:
                                    total_audit_lines += hunk.new_count

                        # 传递 diff_info 到执行函数
                        options['diff_info_dict'] = diff_info_dict

                        print(f"📊 审核范围：约 {total_audit_lines} 行修改代码（+ 上下文）")
                        print()
                except Exception as e:
                    logger.warning(f"获取 diff 信息失败: {e}，使用全文件审核模式")
                    print(f"⚠️  获取 diff 信息失败，将使用全文件审核模式")
                    print()

            # Phase 4: 添加 repo_path 到 options（用于路径映射）
            options['repo_path'] = git_helper.repo_path

            # 执行检查（复用现有逻辑）
            self._execute_batch_check(
                files=files,
                check_type="git_staged",
                options=options
            )

        except RuntimeError as e:
            print(f"❌ {e}")
            logger.error(f"Git 暂存区检查失败: {e}", exc_info=True)
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            logger.error(f"Git 暂存区检查失败: {e}", exc_info=True)

    def _check_git_unstaged(self, args: List[str]) -> None:
        """
        检查工作区修改文件（已修改但未 add）

        Args:
            args: 选项参数列表
        """
        print("🔍 检查工作区修改文件...")
        print()

        try:
            git_helper = GitFileHelper()
            files = git_helper.get_unstaged_files()

            if not files:
                print("📭 工作区没有修改文件")
                print()
                print("💡 提示: 修改文件后即可检查，使用 git status 查看状态")
                return

            print(f"✅ 找到 {len(files)} 个修改文件")
            print()

            options = self._parse_git_check_options(args)

            # Phase 3: 如果启用了 diff-only 模式，获取 diff info
            if options.get("diff_only"):
                print("🎯 Diff-Only 模式：将仅审核修改的代码行")
                print()

                try:
                    # 获取 diff 信息
                    diff_info_dict = git_helper.get_unstaged_diff_info()

                    if not diff_info_dict:
                        print("⚠️  无法获取 diff 信息，将使用全文件审核模式")
                    else:
                        # 计算审核范围统计
                        total_audit_lines = 0
                        for file_path, diff_info in diff_info_dict.items():
                            if diff_info.has_modifications():
                                for hunk in diff_info.hunks:
                                    total_audit_lines += hunk.new_count

                        # 传递 diff_info 到执行函数
                        options['diff_info_dict'] = diff_info_dict

                        print(f"📊 审核范围：约 {total_audit_lines} 行修改代码（+ 上下文）")
                        print()
                except Exception as e:
                    logger.warning(f"获取 diff 信息失败: {e}，使用全文件审核模式")
                    print(f"⚠️  获取 diff 信息失败，将使用全文件审核模式")
                    print()

            # Phase 4: 添加 repo_path 到 options（用于路径映射）
            options['repo_path'] = git_helper.repo_path

            self._execute_batch_check(
                files=files,
                check_type="git_unstaged",
                options=options
            )

        except RuntimeError as e:
            print(f"❌ {e}")
            logger.error(f"Git 工作区检查失败: {e}", exc_info=True)
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            logger.error(f"Git 工作区检查失败: {e}", exc_info=True)

    def _check_git_commit(self, args: List[str]) -> None:
        """
        检查指定 commit 的变更文件

        Args:
            args: [commit_hash, ...options]
        """
        if not args:
            print("❌ 请指定 commit 哈希值")
            print("用法: /check /git /commit <commit_hash> [/repeat N] [/consensus 0.8]")
            return

        commit_hash = args[0]
        option_args = args[1:]

        print(f"🔍 检查 commit {commit_hash}...")
        print()

        try:
            git_helper = GitFileHelper()

            # 获取 commit 信息
            commit_info = git_helper.get_commit_info(commit_hash)
            print(f"📝 Commit: {commit_info['short_hash']}")
            print(f"   作者: {commit_info['author']}")
            print(f"   日期: {commit_info['date']}")
            print(f"   信息: {commit_info['message'].splitlines()[0]}")
            print()

            # 获取变更文件（相对路径）
            files = git_helper.get_commit_files(commit_hash)

            if not files:
                print("📭 该 commit 没有文件变更")
                return

            print(f"✅ 找到 {len(files)} 个变更文件")
            print()

            # 准备文件（Phase 3: 支持历史文件提取）
            prepared_files, temp_manager = self._prepare_git_files(
                files,
                git_helper,
                commit_hash
            )

            if not prepared_files:
                print("⚠️  没有可检查的文件")
                # 清理临时文件（如果有）
                if temp_manager:
                    temp_manager.cleanup()
                return

            options = self._parse_git_check_options(option_args)
            options['commit_info'] = commit_info  # 传递 commit 信息用于报告

            # Phase 3: 如果启用了 diff-only 模式，获取 diff info
            if options.get("diff_only"):
                print("🎯 Diff-Only 模式：将仅审核修改的代码行")
                print()

                try:
                    # 获取 diff 信息
                    diff_info_dict = git_helper.get_commit_diff_info(commit_hash)

                    if not diff_info_dict:
                        print("⚠️  无法获取 diff 信息，将使用全文件审核模式")
                    else:
                        # 计算审核范围统计
                        total_audit_lines = 0
                        for file_path, diff_info in diff_info_dict.items():
                            if diff_info.has_modifications():
                                for hunk in diff_info.hunks:
                                    total_audit_lines += hunk.new_count

                        # 传递 diff_info 到执行函数
                        options['diff_info_dict'] = diff_info_dict

                        print(f"📊 审核范围：约 {total_audit_lines} 行修改代码（+ 上下文）")
                        print()
                except Exception as e:
                    logger.warning(f"获取 diff 信息失败: {e}，使用全文件审核模式")
                    print(f"⚠️  获取 diff 信息失败，将使用全文件审核模式")
                    print()

            # Phase 4: 添加 repo_path 到 options（用于路径映射）
            options['repo_path'] = git_helper.repo_path

            # Phase 3: 传递 temp_manager 以便检查后自动清理
            self._execute_batch_check(
                files=prepared_files,
                check_type=f"git_commit_{commit_info['short_hash']}",
                options=options,
                temp_manager=temp_manager
            )

        except ValueError as e:
            print(f"❌ {e}")
        except RuntimeError as e:
            print(f"❌ {e}")
            logger.error(f"Git commit 检查失败: {e}", exc_info=True)
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            logger.error(f"Git commit 检查失败: {e}", exc_info=True)

    def _check_git_diff(self, args: List[str]) -> None:
        """
        检查两个 commit 之间的差异文件

        Args:
            args: [commit1, [commit2], ...options]
        """
        if not args:
            print("❌ 请指定 commit")
            print("用法: /check /git /diff <commit1> [commit2] [options]")
            print("     commit2 默认为 HEAD")
            return

        commit1 = args[0]

        # 判断第二个参数是选项还是 commit
        if len(args) > 1 and not args[1].startswith('/'):
            commit2 = args[1]
            option_args = args[2:]
        else:
            commit2 = "HEAD"
            option_args = args[1:]

        print(f"🔍 检查 diff: {commit1}...{commit2}")
        print()

        try:
            git_helper = GitFileHelper()

            # 获取差异文件
            files = git_helper.get_diff_files(commit1, commit2)

            if not files:
                print(f"📭 {commit1} 和 {commit2} 之间没有差异")
                return

            print(f"✅ 找到 {len(files)} 个差异文件")
            print()

            # 准备文件（Phase 3: 使用 commit2 的版本）
            prepared_files, temp_manager = self._prepare_git_files(
                files,
                git_helper,
                commit2
            )

            if not prepared_files:
                print("⚠️  没有可检查的文件")
                # 清理临时文件（如果有）
                if temp_manager:
                    temp_manager.cleanup()
                return

            options = self._parse_git_check_options(option_args)
            options['diff_info'] = f"{commit1}...{commit2}"

            # Phase 3: 如果启用了 diff-only 模式，获取 diff info
            if options.get("diff_only"):
                print("🎯 Diff-Only 模式：将仅审核修改的代码行")
                print()

                try:
                    # 获取 diff 信息
                    diff_info_dict = git_helper.get_diff_between_commits(commit1, commit2)

                    if not diff_info_dict:
                        print("⚠️  无法获取 diff 信息，将使用全文件审核模式")
                    else:
                        # 计算审核范围统计
                        total_audit_lines = 0
                        for file_path, diff_info in diff_info_dict.items():
                            if diff_info.has_modifications():
                                for hunk in diff_info.hunks:
                                    total_audit_lines += hunk.new_count

                        # 传递 diff_info 到执行函数
                        options['diff_info_dict'] = diff_info_dict

                        print(f"📊 审核范围：约 {total_audit_lines} 行修改代码（+ 上下文）")
                        print()
                except Exception as e:
                    logger.warning(f"获取 diff 信息失败: {e}，使用全文件审核模式")
                    print(f"⚠️  获取 diff 信息失败，将使用全文件审核模式")
                    print()

            # Phase 4: 添加 repo_path 到 options（用于路径映射）
            options['repo_path'] = git_helper.repo_path

            # Phase 3: 传递 temp_manager 以便检查后自动清理
            self._execute_batch_check(
                files=prepared_files,
                check_type=f"git_diff_{commit1[:7]}_{commit2[:7]}",
                options=options,
                temp_manager=temp_manager
            )

        except ValueError as e:
            print(f"❌ {e}")
        except RuntimeError as e:
            print(f"❌ {e}")
            logger.error(f"Git diff 检查失败: {e}", exc_info=True)
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            logger.error(f"Git diff 检查失败: {e}", exc_info=True)

    def _parse_git_check_options(self, args: List[str]) -> Dict[str, Any]:
        """
        解析 git 检查的选项参数

        Args:
            args: 参数列表

        Returns:
            选项字典 {repeat, consensus, workers, diff_only}
        """
        options = {
            "repeat": None,
            "consensus": None,
            "workers": 5,  # 默认并发数
            "diff_only": False  # Phase 3: diff-only 模式
        }

        i = 0
        while i < len(args):
            arg = args[i]

            if arg == "/repeat" and i + 1 < len(args):
                try:
                    options["repeat"] = int(args[i + 1])
                except ValueError:
                    print(f"⚠️  无效的重复次数: {args[i + 1]}")
                i += 2
            elif arg == "/consensus" and i + 1 < len(args):
                try:
                    options["consensus"] = float(args[i + 1])
                except ValueError:
                    print(f"⚠️  无效的共识阈值: {args[i + 1]}")
                i += 2
            elif arg == "/workers" and i + 1 < len(args):
                try:
                    options["workers"] = int(args[i + 1])
                except ValueError:
                    print(f"⚠️  无效的并发数: {args[i + 1]}")
                i += 2
            elif arg == "/diff-only":
                # Phase 3: 启用 diff-only 模式
                options["diff_only"] = True
                i += 1
            else:
                i += 1

        return options

    def _prepare_git_files(
        self,
        files: List[str],
        git_helper: GitFileHelper,
        commit_hash: Optional[str] = None
    ) -> Tuple[List[str], Optional[TempFileManager]]:
        """
        准备 git 文件供检查（Phase 3 完整版）

        对于工作区文件（staged/unstaged），直接返回绝对路径
        对于历史文件（commit），从 Git 对象中提取内容到临时文件

        Args:
            files: 文件路径列表（可能是相对路径或绝对路径）
            git_helper: GitFileHelper 实例
            commit_hash: 如果指定，表示从该 commit 提取文件

        Returns:
            (准备好的文件路径列表, 临时文件管理器)
            如果不需要临时文件，管理器为 None
        """
        repo_path = git_helper.repo_path

        # 如果是工作区或暂存区文件，直接返回绝对路径
        if commit_hash is None:
            prepared = []
            for file_path in files:
                # 转换为绝对路径
                if os.path.isabs(file_path):
                    abs_path = file_path
                else:
                    abs_path = os.path.join(repo_path, file_path)

                # 检查文件是否存在
                if os.path.exists(abs_path):
                    prepared.append(abs_path)
                else:
                    logger.warning(f"文件不存在: {abs_path}")

            logger.info(f"准备了 {len(prepared)}/{len(files)} 个工作区文件")
            return prepared, None

        # 历史文件：需要提取到临时目录（Phase 3）
        temp_manager = TempFileManager()
        prepared = []
        skipped_binary = 0
        skipped_large = 0
        skipped_error = 0

        for file_path in files:
            try:
                # 检查是否为二进制文件
                if git_helper.is_binary_file(file_path, commit_hash):
                    logger.debug(f"跳过二进制文件: {file_path}")
                    skipped_binary += 1
                    continue

                # 获取文件内容（会自动跳过大文件）
                content = git_helper.get_file_content_at_commit(
                    file_path,
                    commit_hash
                )

                if content is None:
                    logger.warning(f"无法获取文件内容: {file_path}@{commit_hash}")
                    skipped_error += 1
                    continue

                # 创建临时文件
                temp_path = temp_manager.create_temp_file(file_path, content)
                prepared.append(temp_path)

            except OSError as e:
                logger.error(f"创建临时文件失败: {file_path}, {e}")
                skipped_error += 1
                continue
            except Exception as e:
                logger.error(f"准备文件失败: {file_path}, {e}", exc_info=True)
                skipped_error += 1
                continue

        # 显示统计信息
        total_skipped = skipped_binary + skipped_large + skipped_error
        logger.info(
            f"准备了 {len(prepared)}/{len(files)} 个历史文件 "
            f"(跳过: 二进制 {skipped_binary}, 错误 {skipped_error})"
        )

        if total_skipped > 0:
            print(f"💡 跳过 {total_skipped} 个文件：")
            if skipped_binary > 0:
                print(f"   - {skipped_binary} 个二进制文件")
            if skipped_error > 0:
                print(f"   - {skipped_error} 个无法获取的文件（可能已删除或过大）")
            print()

        return prepared, temp_manager

    def _execute_batch_check(
        self,
        files: List[str],
        check_type: str,
        options: Dict[str, Any],
        temp_manager: Optional[TempFileManager] = None
    ) -> None:
        """
        执行批量检查（复用现有逻辑）

        Args:
            files: 文件列表
            check_type: 检查类型（用于生成 check_id）
            options: 检查选项
            temp_manager: 临时文件管理器（Phase 3: 用于历史文件检查）
        """
        workers = options.get("workers", 5)

        # Phase 4: 提取并转换 diff_info_dict（如果存在）
        diff_info_dict = options.get("diff_info_dict")
        abs_diff_info_dict: Optional[Dict[str, Any]] = None

        if diff_info_dict:
            logger.info(f"Diff-Only 模式：{len(diff_info_dict)} 个文件有 diff 信息")

            # Phase 4: 路径映射转换（相对路径 -> 绝对路径）
            # diff_info_dict 的键是相对路径，但 files 列表是绝对路径
            # 需要构建绝对路径到 FileDiffInfo 的映射
            abs_diff_info_dict = {}

            # 尝试从 git_helper 获取 repo_path（如果是 Git 检查）
            repo_path = options.get("repo_path", os.getcwd())

            for abs_path in files:
                # 计算相对路径
                try:
                    rel_path = os.path.relpath(abs_path, repo_path)
                    # 标准化路径分隔符（Git 使用正斜杠）
                    rel_path = rel_path.replace(os.sep, '/')

                    # 查找 diff_info
                    if rel_path in diff_info_dict:
                        abs_diff_info_dict[abs_path] = diff_info_dict[rel_path]
                        logger.debug(f"路径映射: {rel_path} -> {abs_path}")
                except ValueError:
                    # relpath 可能抛出异常（如跨盘符）
                    logger.warning(f"无法计算相对路径: {abs_path} (repo: {repo_path})")
                    continue

            logger.info(
                f"路径映射完成: {len(diff_info_dict)} 个相对路径 -> "
                f"{len(abs_diff_info_dict)} 个绝对路径"
            )
        else:
            logger.info("全文件审核模式")

        # 确保 checker 已初始化
        self._ensure_checker()

        # 应用 repeat/consensus 参数
        self._apply_checker_options({
            "repeat": options.get("repeat"),
            "consensus": options.get("consensus"),
        })

        # 生成 check_id
        check_id = self._create_check_id_with_prefix(check_type)
        report_dir = self._create_report_dir(check_id)

        # 启动任务日志
        from autocoder.checker.task_logger import TaskLogger
        task_logger = TaskLogger(report_dir)
        task_logger.start()

        try:
            logger.info(f"开始检查任务: {check_id}, 文件数: {len(files)}")

            print(f"📝 检查任务 ID: {check_id}")
            print(f"📄 报告目录: {report_dir}")
            print()

            # 导入进度显示
            from autocoder.checker.progress_display import ProgressDisplay

            results = []
            progress_display = ProgressDisplay()

            # 更新 LLM 配置显示（与单文件审核保持一致）
            progress_display.update_llm_config(
                repeat=self.checker.llm_repeat,
                consensus=self.checker.llm_consensus_ratio
            )

            # 创建线程安全的并发进度回调
            from threading import Lock
            update_lock = Lock()

            def concurrent_progress_callback(step: str, **kwargs):
                """并发场景下的进度回调（线程安全）"""
                with update_lock:
                    if step == "chunked":
                        progress_display.update_chunk_progress(
                            total_chunks=kwargs.get("total_chunks", 0),
                            completed_chunks=0
                        )
                    elif step == "chunk_start":
                        progress_display.update_chunk_progress(
                            current_chunk=kwargs.get("chunk_index", 0),
                            chunk_info={
                                "start_line": kwargs.get("start_line"),
                                "end_line": kwargs.get("end_line"),
                                "tokens": kwargs.get("tokens"),
                            }
                        )
                    elif step == "chunk_done":
                        progress_display.update_chunk_progress(
                            completed_chunks=kwargs.get("chunk_index", 0) + 1
                        )
                    elif step == "llm_call_start":
                        progress_display.update_llm_progress(
                            event="start",
                            attempt=kwargs.get("attempt", 1),
                            total_attempts=kwargs.get("total_attempts", 1)
                        )
                    elif step == "llm_call_end":
                        progress_display.update_llm_progress(
                            event="end",
                            attempt=kwargs.get("attempt", 1),
                            duration=kwargs.get("duration", 0.0),
                            issues_found=kwargs.get("issues_found", 0)
                        )
                    elif step == "merge_done":
                        # 并发场景下，保留最新活动信息，不立即清空
                        # 这样用户可以持续看到检查详情（虽然会在不同文件间切换）
                        pass

            with progress_display.display_progress():
                progress_display.update_file_progress(
                    total_files=len(files),
                    completed_files=0
                )

                # Phase 4: 并发检查（传递进度回调和 diff_info_dict）
                for idx, result in enumerate(
                    self.checker.check_files_concurrent(
                        files,
                        max_workers=workers,
                        progress_callback=concurrent_progress_callback,
                        diff_info_dict=abs_diff_info_dict  # Phase 4: 传递 diff_info
                    ),
                    1
                ):
                    # Phase 3: 如果使用了临时文件，恢复原始路径（用于报告）
                    if temp_manager:
                        original_path = temp_manager.get_original_path(result.file_path)
                        if original_path:
                            result.file_path = original_path
                            logger.debug(f"恢复原始路径: {original_path}")

                    results.append(result)

                    # 更新进度
                    progress_display.update_file_progress(completed_files=idx)

            # 生成报告
            for result in results:
                self.report_generator.generate_file_report(result, report_dir)

            # Phase 4: 构造 GitInfo（如果是 Git 检查）
            git_info = None
            if 'commit_info' in options:
                # Commit 检查
                commit_info = options['commit_info']
                git_info = GitInfo(
                    type="commit",
                    commit_hash=commit_info['hash'],
                    short_hash=commit_info['short_hash'],
                    message=commit_info['message'],
                    author=commit_info['author'],
                    date=commit_info['date'],
                    files_changed=len(files)
                )
            elif 'diff_info' in options:
                # Diff 检查
                diff_parts = options['diff_info'].split('...')
                git_info = GitInfo(
                    type="diff",
                    commit1=diff_parts[0] if len(diff_parts) > 0 else "",
                    commit2=diff_parts[1] if len(diff_parts) > 1 else "HEAD",
                    files_changed=len(files)
                )
            elif check_type == "git_staged":
                # 暂存区检查
                try:
                    git_helper = GitFileHelper()
                    branch = git_helper.repo.active_branch.name
                    git_info = GitInfo(
                        type="staged",
                        branch=branch,
                        files_changed=len(files)
                    )
                except Exception as e:
                    logger.warning(f"获取分支信息失败: {e}")
            elif check_type == "git_unstaged":
                # 工作区检查
                try:
                    git_helper = GitFileHelper()
                    branch = git_helper.repo.active_branch.name
                    git_info = GitInfo(
                        type="unstaged",
                        branch=branch,
                        files_changed=len(files)
                    )
                except Exception as e:
                    logger.warning(f"获取分支信息失败: {e}")

            # 生成汇总报告（Phase 4: 传递 git_info）
            self.report_generator.generate_summary_report(results, report_dir, git_info=git_info)

            # 显示汇总
            self._show_batch_summary(results, report_dir)

        finally:
            task_logger.stop()

            # Phase 3: 清理临时文件
            if temp_manager:
                temp_manager.cleanup()
                logger.info("临时文件已清理")

    def get_help_text(self) -> Optional[str]:
        """Get the help text displayed in the startup screen.

        Returns:
            Help text with formatted subcommands
        """
        return """  \033[94m/check\033[0m - \033[92m代码规范检查插件\033[0m
    \033[94m/check /file\033[0m \033[93m<filepath>\033[0m - 检查单个文件
    \033[94m/check /folder\033[0m \033[93m[options]\033[0m - 检查目录
    \033[94m/check /git\033[0m \033[93m<subcommand>\033[0m - Git 文件检查 (NEW)
    \033[94m/check /resume\033[0m \033[93m[check_id]\033[0m - 恢复中断的检查
    \033[94m/check /config\033[0m \033[93m[options]\033[0m - 配置默认参数"""

    def shutdown(self) -> None:
        """关闭插件"""
        print(f"[{self.name}] 代码检查插件已关闭")
