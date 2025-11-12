import os
from typing import Optional, List

from rich.console import Console

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query


class LibHandler:
    """处理库管理相关的操作"""

    def __init__(self):
        self.console = Console()
        self._config = None

    def _create_config(self):
        """创建 lib 命令的类型化配置"""
        if self._config is None:
            self._config = (
                create_config()
                .collect_remainder("query")  # 收集剩余参数
                .command("add")
                .positional("lib_name", required=True)
                .max_args(1)  # 添加库
                .command("remove")
                .positional("lib_name", required=True)
                .max_args(1)  # 删除库
                .command("list")
                .max_args(0)  # 列出已添加的库
                .command("list_all")
                .max_args(0)  # 列出所有可用库
                .command("set_proxy")
                .positional("proxy_url")  # 可选的代理URL
                .max_args(1)  # 设置代理
                .command("refresh")
                .max_args(0)  # 刷新仓库
                .command("get")
                .positional("package_name", required=True)
                .max_args(1)  # 获取包文档
                .build()
            )
        return self._config

    def handle_lib_command(self, args: List[str]) -> Optional[None]:
        """
        处理库管理命令的主入口

        Args:
            args: 命令参数列表

        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        if not args:
            return self._handle_no_args()

        # 使用原始的字符串匹配逻辑来保持兼容性
        subcommand = args[0]

        # 检查是否是 /help 命令
        if subcommand == "/help":
            print(get_message("lib_help_text"))
            return None

        # 获取包管理器
        package_manager = self._get_package_manager()

        if subcommand == "/add":
            return self._handle_add(args, package_manager)
        elif subcommand == "/remove":
            return self._handle_remove(args, package_manager)
        elif subcommand == "/list":
            return self._handle_list(package_manager)
        elif subcommand == "/list_all":
            return self._handle_list_all(package_manager)
        elif subcommand == "/set-proxy":
            return self._handle_set_proxy(args, package_manager)
        elif subcommand == "/refresh":
            return self._handle_refresh(package_manager)
        elif subcommand == "/get":
            return self._handle_get(args, package_manager)
        else:
            return self._handle_unknown_subcommand(subcommand)

    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        print(get_message("lib_help_text"))
        return None

    def _get_package_manager(self):
        """获取包管理器"""
        from autocoder.common.llm_friendly_package import get_package_manager

        return get_package_manager()

    def _handle_add(self, args: List[str], package_manager) -> None:
        """处理添加库命令"""
        if len(args) < 2:
            self.console.print("Please specify a library name to add")
            return None

        lib_name = args[1].strip()
        package_manager.add_library(lib_name)
        return None

    def _handle_remove(self, args: List[str], package_manager) -> None:
        """处理删除库命令"""
        if len(args) < 2:
            self.console.print("Please specify a library name to remove")
            return None

        lib_name = args[1].strip()
        package_manager.remove_library(lib_name)
        return None

    def _handle_list(self, package_manager) -> None:
        """处理列出已添加库命令"""
        package_manager.display_added_libraries()
        return None

    def _handle_list_all(self, package_manager) -> None:
        """处理列出所有可用库命令"""
        package_manager.display_all_libraries()
        return None

    def _handle_set_proxy(self, args: List[str], package_manager) -> None:
        """处理设置代理命令"""
        if len(args) == 1:
            package_manager.set_proxy()
        elif len(args) == 2:
            proxy_url = args[1]
            package_manager.set_proxy(proxy_url)
        else:
            self.console.print("Invalid number of arguments for /set-proxy")
        return None

    def _handle_refresh(self, package_manager) -> None:
        """处理刷新仓库命令"""
        package_manager.refresh_repository()
        return None

    def _handle_get(self, args: List[str], package_manager) -> None:
        """处理获取包文档命令"""
        if len(args) < 2:
            self.console.print("Please specify a package name to get")
            return None

        package_name = args[1].strip()
        package_manager.display_library_docs(package_name)
        return None

    def _handle_unknown_subcommand(self, subcommand: str) -> None:
        """处理未知子命令"""
        self.console.print(f"Unknown subcommand: {subcommand}")
        return None
