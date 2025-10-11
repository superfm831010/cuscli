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
            "repeat": 3,
            "consensus": 1.0,
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
            "/check": ["/file", "/folder", "/resume", "/report", "/config"],
            "/check /folder": ["/path", "/ext", "/ignore", "/workers", "/repeat", "/consensus"],
            "/check /config": ["/repeat", "/consensus"],
        }

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

/check /folder 选项:
  /path <dir>                          - 指定检查目录（默认: 当前目录）
  /ext <.py,.js>                       - 指定文件扩展名（逗号分隔）
  /ignore <tests,__pycache__>          - 忽略目录/文件（逗号分隔）
  /workers <5>                         - 并发数（默认: 5）
  /repeat <3>                          - LLM 调用次数（默认: 3）
  /consensus <1.0>                     - 共识阈值 0~1（默认: 1.0）

示例:
  /check /file autocoder/auto_coder.py
  /check /file autocoder/auto_coder.py /repeat 3 /consensus 0.8
  /check /folder
  /check /folder /path src /ext .py
  /check /folder /path src /ext .py /ignore tests,__pycache__ /repeat 3
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
            self._apply_checker_options({
                "repeat": options.get("repeat"),
                "consensus": options.get("consensus"),
            })

            # 应用共识参数
            self._apply_checker_options(common_options)

            # 导入 rich 进度条组件
            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
                TimeRemainingColumn,
            )

            # 使用进度条显示检查进度
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            ) as progress:
                # 创建进度任务（初始不确定总量）
                task = progress.add_task("初始化...", total=None)

                # 定义进度回调函数
                def progress_callback(step: str, **kwargs):
                    """处理检查进度更新"""
                    if step == "start":
                        progress.update(task, description="开始检查...")

                    elif step == "rules_loaded":
                        total_rules = kwargs.get("total_rules", 0)
                        progress.update(
                            task,
                            description=f"已加载 {total_rules} 条规则"
                        )

                    elif step == "chunked":
                        total_chunks = kwargs.get("total_chunks", 0)
                        # 设置进度条总量为 chunk 数量
                        progress.update(
                            task,
                            total=total_chunks,
                            completed=0,
                            description=f"开始检查 ({total_chunks} 个代码块)"
                        )

                    elif step == "chunk_start":
                        chunk_index = kwargs.get("chunk_index", 0)
                        total_chunks = kwargs.get("total_chunks", 1)
                        progress.update(
                            task,
                            description=f"检查代码块 {chunk_index + 1}/{total_chunks}..."
                        )

                    elif step == "chunk_done":
                        chunk_index = kwargs.get("chunk_index", 0)
                        total_chunks = kwargs.get("total_chunks", 1)
                        # 更新进度
                        progress.update(
                            task,
                            completed=chunk_index + 1,
                            description=f"已完成代码块 {chunk_index + 1}/{total_chunks}"
                        )

                    elif step == "merge_done":
                        progress.update(task, description="合并检查结果...")

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
                self.report_generator.generate_file_report(result, report_dir)

                # 根据是否有问题决定显示哪个目录
                has_issues = len(result.issues) > 0
                subdir = "with_issues" if has_issues else "no_issues"

                print()
                print(f"📄 报告已保存到: {report_dir}")
                print(f"   - {os.path.join(report_dir, 'files', subdir, self.report_generator._safe_path(file_path) + '.md')}")
                print(f"   - {os.path.join(report_dir, 'files', subdir, self.report_generator._safe_path(file_path) + '.json')}")

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

            # 创建检查任务并保存状态（Task 8.1: 进度持久化）
            project_name = os.path.basename(os.getcwd())
            # 清理项目名称
            project_name = "".join(c if c.isalnum() or c == "_" else "_" for c in project_name)

            check_id = self.progress_tracker.start_check(
                files=files,
                config={
                    "path": path,
                    "extensions": extensions,
                    "ignored": ignored,
                    "workers": workers
                },
                project_name=project_name
            )

            print(f"📝 检查任务 ID: {check_id}")
            print()

            # 批量检查（Task 9.2: 使用并发检查）
            results = []
            check_interrupted = False

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    # 显示并发数
                    task = progress.add_task(
                        f"正在检查文件... (并发: {workers})",
                        total=len(files)
                    )

                    # Task 9.2: 使用并发检查
                    for result in self.checker.check_files_concurrent(files, max_workers=workers):
                        results.append(result)

                        # Task 8.1: 标记文件完成，保存进度
                        self.progress_tracker.mark_completed(check_id, result.file_path)

                        progress.update(
                            task,
                            advance=1,
                            description=f"检查 {os.path.basename(result.file_path)} (并发: {workers})"
                        )

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
                if results:
                    logger.info(f"生成部分报告，已完成 {len(results)} 个文件")

                    # 如果是正常完成，标记状态
                    if not check_interrupted:
                        state = self.progress_tracker.load_state(check_id)
                        if state:
                            state.status = "completed"
                            self.progress_tracker.save_state(check_id, state)

                    # 生成报告
                    report_dir = self._create_report_dir(check_id)

                    # 生成单文件报告
                    for result in results:
                        self.report_generator.generate_file_report(result, report_dir)

                    # 生成汇总报告
                    self.report_generator.generate_summary_report(results, report_dir)

                    # 显示汇总
                    if check_interrupted:
                        print()
                        print(f"📄 已生成部分报告 ({len(results)}/{len(files)} 个文件)")
                        print(f"   报告位置: {report_dir}/")
                        print()
                        print(f"💡 使用以下命令恢复检查:")
                        print(f"   /check /resume {check_id}")
                        print()
                    else:
                        self._show_batch_summary(results, report_dir)

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
                    print(f"⚠️  无效的重复次数: {parts[i + 1]}，使用默认值 3")
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

    def _show_batch_summary(self, results: List, report_dir: str) -> None:
        """
        显示批量检查汇总

        Args:
            results: 检查结果列表
            report_dir: 报告目录
        """
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
            print()

            # 导入 rich 进度条
            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
                TimeRemainingColumn,
            )

            # 恢复检查（Task 9.2: 使用并发检查）
            # 获取原配置的并发数，如果没有则使用默认值5
            workers = state.config.get("workers", 5)

            results = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"恢复检查中... (并发: {workers})",
                    total=remaining
                )

                # Task 9.2: 使用并发检查
                for result in self.checker.check_files_concurrent(state.remaining_files, max_workers=workers):
                    results.append(result)

                    # 更新进度
                    self.progress_tracker.mark_completed(check_id, result.file_path)

                    progress.update(
                        task,
                        advance=1,
                        description=f"检查 {os.path.basename(result.file_path)} (并发: {workers})"
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

    def shutdown(self) -> None:
        """关闭插件"""
        logger.info(f"[{self.name}] 代码检查插件已关闭")
