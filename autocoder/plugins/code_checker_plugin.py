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

            # 获取配置
            memory_manager = get_memory_manager()
            conf = memory_manager.get_all_config()

            # 获取模型配置
            model_name = conf.get("model", "deepseek/deepseek-chat")
            product_mode = conf.get("product_mode", "lite")

            # 获取 LLM 实例
            llm = get_single_llm(model_name, product_mode)
            if llm is None:
                raise RuntimeError(
                    f"无法获取 LLM 实例 (model={model_name}, mode={product_mode})\n"
                    "请确保 auto-coder 已正确初始化并配置了模型"
                )

            # 创建一个基础的 Args 对象（使用默认值）
            # 如果需要更多配置，可以从 config 中读取
            args = AutoCoderArgs()

            # 初始化 CodeChecker
            self.checker = CodeChecker(llm, args)

            logger.info(f"[{self.name}] CodeChecker 初始化成功 (model={model_name})")

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
            "/check": ["/file", "/folder", "/resume", "/report"],
            "/check /folder": ["/path", "/ext", "/ignore", "/workers"],
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
  /check /folder [options]             - 检查目录
  /check /resume [check_id]            - 恢复中断的检查
  /check /report [check_id]            - 查看检查报告

/check /folder 选项:
  /path <dir>                          - 指定检查目录（默认: 当前目录）
  /ext <.py,.js>                       - 指定文件扩展名（逗号分隔）
  /ignore <tests,__pycache__>          - 忽略目录/文件（逗号分隔）
  /workers <5>                         - 并发数（默认: 5）

示例:
  /check /file autocoder/auto_coder.py
  /check /folder
  /check /folder /path src /ext .py
  /check /folder /path src /ext .py /ignore tests,__pycache__
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
        file_path = args.strip()

        if not file_path:
            print("❌ 请指定文件路径")
            print("用法: /check /file <filepath>")
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

            # 执行检查
            result = self.checker.check_file(file_path)

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

                print()
                print(f"📄 报告已保存到: {report_dir}")
                print(f"   - {os.path.join(report_dir, 'files', self.report_generator._safe_path(file_path) + '.md')}")
                print(f"   - {os.path.join(report_dir, 'files', self.report_generator._safe_path(file_path) + '.json')}")

            elif result.status == "skipped":
                print(f"⏭️  文件已跳过: {file_path}")
                print("   原因: 无适用的检查规则")

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
        """
        # TODO: Task 7.3 - 实现目录检查
        print("⚠️  /check /folder 功能即将在 Task 7.3 实现")
        print(f"   参数: {args}")

    def _resume_check(self, args: str) -> None:
        """
        恢复中断的检查

        Args:
            args: check_id
        """
        # TODO: Task 7.x - 实现检查恢复
        print("⚠️  /check /resume 功能即将实现")
        print(f"   参数: {args}")

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
        os.makedirs(os.path.join(report_dir, "files"), exist_ok=True)

        return report_dir

    def shutdown(self) -> None:
        """关闭插件"""
        logger.info(f"[{self.name}] 代码检查插件已关闭")
