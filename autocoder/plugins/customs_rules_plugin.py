"""
Customs Rules Plugin for Chat Auto Coder.
提供海关开发规范管理功能的插件。

功能:
- /apply-customs - 应用海关开发规范到项目
- /apply-customs /force - 强制覆盖已存在的规范文件

作者: Claude AI
创建时间: 2025-11-10
"""

import os
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple

from autocoder.plugins import Plugin, PluginManager
from loguru import logger


class CustomsRulesPlugin(Plugin):
    """海关开发规范管理插件"""

    name = "customs_rules"
    description = "海关开发规范管理，支持一键应用规范到项目"
    version = "1.0.0"

    # 需要动态补全的命令
    dynamic_cmds = [
        "/apply-customs",
        "/apply-customs /force",
    ]

    def __init__(
        self,
        manager: PluginManager,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None
    ):
        """初始化插件"""
        super().__init__(manager, config, config_path)

    def initialize(self) -> bool:
        """
        初始化插件

        Returns:
            True 如果初始化成功
        """
        try:
            logger.info(f"[{self.name}] 海关规范管理插件初始化成功")
            return True
        except Exception as e:
            logger.error(f"[{self.name}] 初始化失败: {e}", exc_info=True)
            print(f"⚠️  海关规范管理插件初始化失败: {e}")
            return False

    def get_commands(self) -> Dict[str, Tuple[Callable, str]]:
        """
        注册命令

        Returns:
            命令字典 {命令名: (处理函数, 描述)}
        """
        return {
            "apply-customs": (self.handle_apply_customs, "应用海关开发规范到项目"),
        }

    def get_completions(self) -> Dict[str, List[str]]:
        """
        提供静态补全

        Returns:
            补全字典 {命令: [子命令列表]}
        """
        return {
            "/apply-customs": ["/force"],
        }

    def handle_apply_customs(self, args_str: str) -> str:
        """
        处理 apply-customs 命令

        Args:
            args_str: 命令参数字符串

        Returns:
            执行结果消息
        """
        try:
            # 解析参数
            force = "/force" in args_str.strip()

            # 获取目标目录
            target_dir = os.path.join(os.getcwd(), ".autocoderrules")

            # 检查目标目录是否存在
            if os.path.exists(target_dir) and not force:
                return (
                    "⚠️  规范目录已存在: .autocoderrules\n"
                    "   使用 /apply-customs /force 强制覆盖"
                )

            # 应用规范文件
            return self._apply_rules(target_dir, force)

        except Exception as e:
            logger.error(f"[{self.name}] 应用规范失败: {e}", exc_info=True)
            return f"❌ 应用海关规范失败: {e}"

    def _apply_rules(self, target_dir: str, force: bool = False) -> str:
        """
        应用规范文件到目标目录

        Args:
            target_dir: 目标目录路径
            force: 是否强制覆盖

        Returns:
            执行结果消息
        """
        try:
            # 使用 importlib.resources 读取打包的内置规范
            try:
                import importlib.resources as resources
            except ImportError:
                # Python 3.7-3.8 兼容
                import importlib_resources as resources

            # 获取源资源包
            try:
                source_package = resources.files("autocoder.data.customs_rules")
            except (ImportError, ModuleNotFoundError, AttributeError) as e:
                logger.error(f"[{self.name}] 无法访问内置规范资源: {e}")
                return (
                    "❌ 无法访问内置海关规范资源\n"
                    "   请确保 cuscli 已正确安装"
                )

            # 如果目标目录存在且强制覆盖，先删除
            if force and os.path.exists(target_dir):
                logger.info(f"[{self.name}] 强制覆盖，删除现有目录: {target_dir}")
                shutil.rmtree(target_dir)

            # 创建目标目录
            os.makedirs(target_dir, exist_ok=True)

            # 复制所有资源文件
            file_count = self._copy_package_resources(source_package, target_dir)

            logger.info(f"[{self.name}] 成功复制 {file_count} 个规范文件到 {target_dir}")

            # 返回成功消息
            return (
                f"✅ 海关开发规范已应用到项目\n"
                f"   - 目标目录: .autocoderrules\n"
                f"   - 后端规则: .autocoderrules/backend/ (7个文件)\n"
                f"   - 前端规则: .autocoderrules/frontend/ (4个文件)\n"
                f"   - 规则索引: .autocoderrules/index.md\n"
                f"   - 共复制: {file_count} 个文件\n"
                f"\n"
                f"💡 提示: 使用 /check 命令检查代码是否符合规范"
            )

        except Exception as e:
            logger.error(f"[{self.name}] 复制规范文件失败: {e}", exc_info=True)
            return f"❌ 复制规范文件失败: {e}"

    def _copy_package_resources(self, source_package, target_dir: str) -> int:
        """
        递归复制包资源到目标目录

        Args:
            source_package: 源资源包（importlib.resources 对象）
            target_dir: 目标目录路径

        Returns:
            复制的文件数量
        """
        try:
            import importlib.resources as resources
        except ImportError:
            import importlib_resources as resources

        file_count = 0

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        # 遍历资源
        for item in source_package.iterdir():
            # 跳过 __pycache__ 等
            if item.name.startswith('__'):
                continue

            target_path = os.path.join(target_dir, item.name)

            if item.is_file():
                # 复制文件
                logger.debug(f"[{self.name}] 复制文件: {item.name} -> {target_path}")

                # 使用 as_file 上下文管理器来处理资源
                with resources.as_file(item) as src_path:
                    shutil.copy2(str(src_path), target_path)

                file_count += 1

            elif item.is_dir():
                # 递归复制目录
                logger.debug(f"[{self.name}] 复制目录: {item.name} -> {target_path}")
                file_count += self._copy_package_resources(item, target_path)

        return file_count
