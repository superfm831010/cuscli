"""远程服务管理器 - 管理远程资源的同步和下载"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

from autocoder.remote_service.api_client import RemoteAPIClient
from autocoder.remote_service.models import (
    ResourceType,
    RemoteResource,
    SyncResult,
    ResourceStats,
)


# 资源类型对应的本地目录名和文件扩展名
RESOURCE_TYPE_CONFIG = {
    ResourceType.AGENTS: {
        "local_dir": ".autocoderagents",
        "extension": ".md",
    },
    ResourceType.WORKFLOWS: {
        "local_dir": ".autocoderworkflow",
        "extension": ".yaml",
    },
    ResourceType.TOOLS: {
        "local_dir": ".auto-coder/.autocodertools",
        "extension": ".md",
    },
    ResourceType.COMMANDS: {
        "local_dir": ".autocodercommands",
        "extension": ".md",
    },
}


class RemoteServiceManager:
    """远程服务管理器"""

    def __init__(
        self,
        project_root: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化远程服务管理器

        Args:
            project_root: 项目根目录，默认为当前目录
            base_url: API 基础 URL，默认为 https://api.auto-coder.chat
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.client = RemoteAPIClient(base_url=base_url)

    def get_resources_stats(self) -> ResourceStats:
        """
        获取远程资源统计

        Returns:
            ResourceStats 对象
        """
        return self.client.get_resources_stats()

    def list_remote_resources(
        self,
        resource_type: Optional[ResourceType] = None,
    ) -> List[RemoteResource]:
        """
        列出远程资源

        Args:
            resource_type: 资源类型，None 表示所有类型

        Returns:
            远程资源列表
        """
        return self.client.get_all_resources(resource_type)

    def get_local_dir(self, resource_type: ResourceType) -> Path:
        """
        获取本地资源目录路径

        Args:
            resource_type: 资源类型

        Returns:
            本地目录 Path 对象
        """
        config = RESOURCE_TYPE_CONFIG.get(resource_type)
        if not config:
            raise ValueError(f"不支持的资源类型: {resource_type}")
        return self.project_root / config["local_dir"]

    def get_local_file_path(self, resource_type: ResourceType, filename: str) -> Path:
        """
        获取本地资源文件路径

        Args:
            resource_type: 资源类型
            filename: 文件名（可能包含扩展名）

        Returns:
            本地文件 Path 对象
        """
        config = RESOURCE_TYPE_CONFIG.get(resource_type)
        if not config:
            raise ValueError(f"不支持的资源类型: {resource_type}")

        local_dir = self.get_local_dir(resource_type)
        extension = config["extension"]

        # 去除现有扩展名，统一使用配置的扩展名
        # 例如：example-workflow.md -> example-workflow.yaml
        base_name = Path(filename).stem
        filename = f"{base_name}{extension}"

        return local_dir / filename

    def sync_resource(
        self,
        resource_type: ResourceType,
        filename: str,
        force: bool = False,
    ) -> bool:
        """
        同步单个资源

        Args:
            resource_type: 资源类型
            filename: 文件名
            force: 是否强制覆盖

        Returns:
            是否成功同步
        """
        local_path = self.get_local_file_path(resource_type, filename)

        # 检查本地文件是否存在
        if local_path.exists() and not force:
            logger.debug(f"本地文件已存在，跳过: {local_path}")
            return False

        try:
            # 下载资源内容（二进制方式）
            content_bytes = self.client.download_resource(resource_type, filename)
            if not content_bytes:
                logger.warning(f"获取资源内容为空: {filename}")
                return False

            # 确保目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件（二进制方式，支持文本和二进制文件）
            local_path.write_bytes(content_bytes)
            logger.info(f"已同步: {local_path}")
            return True

        except Exception as e:
            logger.error(f"同步资源失败 {filename}: {e}")
            return False

    def sync_all_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        force: bool = False,
    ) -> SyncResult:
        """
        同步所有资源

        Args:
            resource_type: 资源类型，None 表示同步 agents 和 workflows
            force: 是否强制覆盖本地文件

        Returns:
            SyncResult 同步结果
        """
        result = SyncResult(success=True)

        types_to_sync = (
            [resource_type]
            if resource_type
            else [
                ResourceType.AGENTS,
                ResourceType.WORKFLOWS,
                ResourceType.TOOLS,
                ResourceType.COMMANDS,
            ]
        )

        for res_type in types_to_sync:
            try:
                # 获取远程资源列表
                resources = self.client.get_all_resources(res_type)
                logger.info(f"找到 {len(resources)} 个 {res_type.value} 资源")

                for resource in resources:
                    filename = resource.name
                    local_path = self.get_local_file_path(res_type, filename)

                    # 检查是否需要同步
                    if local_path.exists() and not force:
                        result.add_skipped(str(local_path))
                        continue

                    # 同步资源
                    if self.sync_resource(res_type, filename, force=force):
                        result.add_synced(str(local_path))
                    else:
                        result.add_failed(str(local_path))

            except Exception as e:
                logger.error(f"同步 {res_type.value} 资源时出错: {e}")
                result.success = False
                result.error = str(e)

        return result

    def print_resources_list(
        self,
        resource_type: Optional[ResourceType] = None,
    ) -> None:
        """
        打印远程资源列表

        Args:
            resource_type: 资源类型，None 表示所有类型
        """
        try:
            # 获取统计信息
            stats = self.get_resources_stats()
            print(f"\n📊 远程资源统计:")
            print(f"   Agents: {stats.agents_count}")
            print(f"   Workflows: {stats.workflows_count}")
            print(f"   Tools: {stats.tools_count}")
            print(f"   Commands: {stats.commands_count}")
            print(f"   总计: {stats.total_count}")

            # 获取资源列表
            resources = self.list_remote_resources(resource_type)

            if not resources:
                print("\n⚠️  没有找到远程资源")
                return

            # 按类型分组显示
            agents = [r for r in resources if r.type == ResourceType.AGENTS]
            workflows = [r for r in resources if r.type == ResourceType.WORKFLOWS]
            tools = [r for r in resources if r.type == ResourceType.TOOLS]
            commands = [r for r in resources if r.type == ResourceType.COMMANDS]

            if agents and (
                resource_type is None or resource_type == ResourceType.AGENTS
            ):
                print(f"\n📝 Agents ({len(agents)}):")
                for agent in agents:
                    desc = f" - {agent.description}" if agent.description else ""
                    print(f"   • {agent.name}{desc}")

            if workflows and (
                resource_type is None or resource_type == ResourceType.WORKFLOWS
            ):
                print(f"\n🔄 Workflows ({len(workflows)}):")
                for workflow in workflows:
                    desc = f" - {workflow.description}" if workflow.description else ""
                    print(f"   • {workflow.name}{desc}")

            if tools and (resource_type is None or resource_type == ResourceType.TOOLS):
                print(f"\n🔧 Tools ({len(tools)}):")
                for tool in tools:
                    desc = f" - {tool.description}" if tool.description else ""
                    print(f"   • {tool.name}{desc}")

            if commands and (
                resource_type is None or resource_type == ResourceType.COMMANDS
            ):
                print(f"\n⚡ Commands ({len(commands)}):")
                for cmd in commands:
                    desc = f" - {cmd.description}" if cmd.description else ""
                    print(f"   • {cmd.name}{desc}")

            print()

        except Exception as e:
            print(f"\n❌ 获取远程资源列表失败: {e}")

    def print_sync_result(self, result: SyncResult) -> None:
        """
        打印同步结果

        Args:
            result: SyncResult 对象
        """
        if result.success:
            print(f"\n✅ 同步完成!")
        else:
            print(f"\n⚠️  同步完成（有错误）")

        print(f"   已同步: {result.synced_count}")
        print(f"   已跳过: {result.skipped_count}")
        print(f"   失败: {result.failed_count}")

        if result.synced_files:
            print(f"\n📥 已同步的文件:")
            for f in result.synced_files:
                print(f"   • {f}")

        if result.skipped_files and len(result.skipped_files) <= 10:
            print(f"\n⏭️  跳过的文件（本地已存在）:")
            for f in result.skipped_files:
                print(f"   • {f}")
        elif result.skipped_files:
            print(f"\n⏭️  跳过了 {len(result.skipped_files)} 个本地已存在的文件")

        if result.failed_files:
            print(f"\n❌ 失败的文件:")
            for f in result.failed_files:
                print(f"   • {f}")

        if result.error:
            print(f"\n错误信息: {result.error}")

        print()

    def close(self):
        """关闭客户端连接"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def handle_remote_command(
    command_args: str, project_root: Optional[str] = None
) -> None:
    """
    处理 /remote 命令

    Args:
        command_args: 命令参数
        project_root: 项目根目录
    """
    args = command_args.strip().split()

    if not args or args[0] in ("help", "/help", "-h", "--help"):
        _print_remote_help()
        return

    subcommand = args[0].lstrip("/")

    with RemoteServiceManager(project_root=project_root) as manager:
        if subcommand == "resources":
            # /remote /resources [agents|workflows|tools|commands]
            resource_type = _parse_resource_type(args[1] if len(args) > 1 else None)
            manager.print_resources_list(resource_type)

        elif subcommand == "sync":
            # /remote /sync [--force] [agents|workflows|tools|commands]
            force = "--force" in args or "-f" in args
            resource_type = None

            for arg in args[1:]:
                if arg.startswith("-"):
                    continue
                resource_type = _parse_resource_type(arg)
                if resource_type:
                    break

            print(f"\n🔄 开始同步远程资源...")
            if force:
                print("   (强制覆盖模式)")

            result = manager.sync_all_resources(
                resource_type=resource_type,
                force=force,
            )
            manager.print_sync_result(result)

        else:
            print(f"\n❌ 未知的子命令: {subcommand}")
            _print_remote_help()


def _parse_resource_type(type_arg: Optional[str]) -> Optional[ResourceType]:
    """解析资源类型参数"""
    if not type_arg:
        return None

    type_lower = type_arg.lower()
    if type_lower in ("agents", "agent"):
        return ResourceType.AGENTS
    elif type_lower in ("workflows", "workflow"):
        return ResourceType.WORKFLOWS
    elif type_lower in ("tools", "tool"):
        return ResourceType.TOOLS
    elif type_lower in ("commands", "command"):
        return ResourceType.COMMANDS
    return None


def _print_remote_help() -> None:
    """打印 /remote 命令帮助"""
    help_text = """
📡 /remote - 远程资源管理

用法:
  /remote /resources [type]      列出远程可用的资源
  /remote /sync [options] [type] 同步远程资源到本地

参数:
  type        资源类型: agents | workflows | tools | commands (可选，默认全部)

选项:
  --force, -f  强制覆盖本地已存在的文件

示例:
  /remote /resources              列出所有远程资源
  /remote /resources agents       只列出 agents
  /remote /resources tools        只列出 tools
  /remote /sync                   同步所有资源（跳过已存在）
  /remote /sync --force           强制同步所有资源
  /remote /sync agents            只同步 agents
  /remote /sync --force workflows 强制同步 workflows
  /remote /sync tools             只同步 tools
  /remote /sync commands          只同步 commands

说明:
  资源将同步到以下目录:
  • Agents    -> .autocoderagents/
  • Workflows -> .autocoderworkflow/
  • Tools     -> .auto-coder/.autocodertools/
  • Commands  -> .autocodercommands/
"""
    print(help_text)
