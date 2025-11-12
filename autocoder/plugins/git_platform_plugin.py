"""
Git Helper Plugin for Chat Auto Coder.
Provides convenient Git commands and information display.
"""

import os
import subprocess
import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from autocoder.plugins import Plugin, PluginManager
from autocoder.common.international import register_messages, get_message, get_message_with_format


# ==================================================
# 异步辅助函数：用于在异步环境中进行用户交互
# ==================================================

async def async_input(prompt_text: str, is_password: bool = False) -> str:
    """
    异步输入函数，使用 prompt_toolkit 的异步 API

    Args:
        prompt_text: 提示文本
        is_password: 是否为密码输入（隐藏输入内容）

    Returns:
        用户输入的字符串
    """
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory

    session = PromptSession(history=InMemoryHistory())
    try:
        result = await session.prompt_async(prompt_text, is_password=is_password)
        return result
    except (KeyboardInterrupt, EOFError):
        return ""


async def async_confirm(prompt_text: str, default: bool = True) -> bool:
    """
    异步确认函数（yes/no）

    Args:
        prompt_text: 提示文本
        default: 默认值（True=yes, False=no）

    Returns:
        用户选择的布尔值
    """
    default_hint = " [Y/n]" if default else " [y/N]"
    full_prompt = prompt_text + default_hint + ": "

    while True:
        response = await async_input(full_prompt)
        response = response.strip().lower()

        # 如果用户直接回车，使用默认值
        if not response:
            return default

        # 解析用户输入
        if response in ['y', 'yes', 'Y', 'Yes', 'YES', '是', 'shi', 'ok']:
            return True
        elif response in ['n', 'no', 'N', 'No', 'NO', '否', 'fou']:
            return False
        else:
            # 输入无效，继续循环
            print("请输入 y/yes 或 n/no")
            continue


class GitPlatformPlugin(Plugin):
    """Git platform plugin for the Chat Auto Coder."""

    name = "git_platform"
    description = "Git 平台管理插件（GitHub/GitLab 配置）"
    version = "0.1.0"

    # 需要动态补全的命令列表
    dynamic_cmds = [
        "/git /github /modify",
        "/git /github /delete",
        "/git /github /test",
        "/git /gitlab /modify",
        "/git /gitlab /delete",
        "/git /gitlab /test",
        "/git /platform /switch",
    ]

    def __init__(self, manager: PluginManager, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """Initialize the Git platform plugin."""
        config_dir = Path.home() / ".auto-coder" / "plugins" / "autocoder.plugins.GitPlatformPlugin"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"
        super().__init__(manager, config, str(config_file))
        self.config_path = str(config_file)

        self.git_available = self._check_git_available()
        self.default_branch = self.config.get("default_branch", "main")

        # 初始化平台配置管理器
        from autocoder.common.git_platform_config import GitPlatformManager
        self.platform_manager = GitPlatformManager(self.config_path)

    def _check_git_available(self) -> bool:
        """Check if Git is available."""
        try:
            subprocess.run(
                ["git", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return True
        except Exception:
            return False

    def initialize(self) -> bool:
        """Initialize the plugin.

        Returns:
            True if initialization was successful
        """
        if not self.git_available:
            print(f"[{self.name}] {get_message('git_not_available_warning')}")
            return True

        print(f"[{self.name}] {get_message('git_helper_initialized')}")
        return True

    def get_commands(self) -> Dict[str, Tuple[Callable, str]]:
        """Get commands provided by this plugin.

        Returns:
            A dictionary of command name to handler and description
        """
        return {
            "git": (self.handle_git, "Git 辅助工具，管理版本控制"),
        }

    def get_completions(self) -> Dict[str, List[str]]:
        """Get completions provided by this plugin.

        Returns:
            A dictionary mapping command prefixes to completion options
        """
        completions = {
            "/git": ["/status", "/commit", "/branch", "/checkout", "/diff",
                     "/log", "/pull", "/push", "/reset", "/github", "/gitlab", "/platform"],
            "/git /reset": ["hard", "soft", "mixed"],
            "/git /github": ["/setup", "/list", "/modify", "/delete", "/test"],
            "/git /gitlab": ["/setup", "/list", "/modify", "/delete", "/test"],
            "/git /platform": ["/switch", "/list"],
            "/git /platform /switch": ["github", "gitlab"],
        }

        # 添加分支补全
        if self.git_available:
            try:
                branches = self._get_git_branches()
                completions["/git /checkout"] = branches
                completions["/git /branch"] = branches + [
                    "--delete",
                    "--all",
                    "--remote",
                    "new",
                ]
            except Exception:
                pass

        return completions

    def get_dynamic_completions(
        self, command: str, current_input: str
    ) -> List[Tuple[str, str]]:
        """Get dynamic completions based on the current command context.

        Args:
            command: The base command (e.g., "/git /github /modify")
            current_input: The full current input

        Returns:
            A list of tuples containing (completion_text, display_text)
        """
        completions = []

        # GitHub 配置名补全
        if command in ["/git /github /modify", "/git /github /delete", "/git /github /test"]:
            configs = self.platform_manager.list_configs("github")
            for config in configs:
                display = f"{config.name} ({config.base_url})"
                completions.append((config.name, display))

        # GitLab 配置名补全
        elif command in ["/git /gitlab /modify", "/git /gitlab /delete", "/git /gitlab /test"]:
            configs = self.platform_manager.list_configs("gitlab")
            for config in configs:
                display = f"{config.name} ({config.base_url})"
                completions.append((config.name, display))

        # 平台切换补全（两级）
        elif command == "/git /platform /switch":
            parts = current_input.split()

            if len(parts) <= 3:
                # 第一级：平台类型
                completions = [
                    ("github", "GitHub"),
                    ("gitlab", "GitLab"),
                ]
            else:
                # 第二级：配置名
                platform = parts[3] if len(parts) > 3 else ""

                if platform in ["github", "gitlab"]:
                    configs = self.platform_manager.list_configs(platform)
                    for config in configs:
                        # 标记当前激活的配置
                        current = ""
                        if (self.platform_manager.current_platform == platform and
                            self.platform_manager.current_config.get(platform) == config.name):
                            current = " ✓"

                        display = f"{config.name}{current} ({config.base_url})"
                        completions.append((config.name, display))

        return completions

    def _run_git_command(self, args: List[str]) -> Tuple[int, str, str]:
        """Run a Git command.

        Args:
            args: The command arguments

        Returns:
            A tuple of (return_code, stdout, stderr)
        """
        if not self.git_available:
            return 1, "", get_message("git_not_available")

        try:
            process = subprocess.run(
                ["git"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return process.returncode, process.stdout, process.stderr
        except Exception as e:
            return 1, "", str(e)

    def _get_git_branches(self) -> List[str]:
        """Get Git branches.

        Returns:
            A list of branch names
        """
        code, stdout, _ = self._run_git_command(
            ["branch", "--list", "--format=%(refname:short)"]
        )
        if code == 0:
            return [b.strip() for b in stdout.splitlines() if b.strip()]
        return []

    async def handle_git(self, args: str) -> None:
        """Handle the /git command and route to specific subcommand handlers.

        Args:
            args: Subcommand and arguments, e.g., "/status" or "/commit message"
        """
        args = args.strip()

        # 如果没有子命令，显示帮助
        if not args:
            self._show_git_help()
            return

        # 解析子命令
        parts = args.split(maxsplit=1)
        subcommand = parts[0]
        sub_args = parts[1] if len(parts) > 1 else ""

        # 路由到对应的处理函数
        if subcommand == "/status":
            self.git_status(sub_args)
        elif subcommand == "/commit":
            self.git_commit(sub_args)
        elif subcommand == "/branch":
            self.git_branch(sub_args)
        elif subcommand == "/checkout":
            self.git_checkout(sub_args)
        elif subcommand == "/diff":
            self.git_diff(sub_args)
        elif subcommand == "/log":
            self.git_log(sub_args)
        elif subcommand == "/pull":
            self.git_pull(sub_args)
        elif subcommand == "/push":
            self.git_push(sub_args)
        elif subcommand == "/reset":
            self.handle_reset(sub_args)
        elif subcommand == "/github":
            await self.handle_github(sub_args)
        elif subcommand == "/gitlab":
            await self.handle_gitlab(sub_args)
        elif subcommand == "/platform":
            self.handle_platform(sub_args)
        else:
            print(f"❌ 未知的子命令: {subcommand}")
            self._show_git_help()

    def _show_git_help(self) -> None:
        """Display help information for git commands."""
        print("""
📋 Git 命令帮助

基础命令:
  /git /status              - 查看仓库状态
  /git /commit <message>    - 提交更改（自动 add .）
  /git /branch [args]       - 分支管理
  /git /checkout <branch>   - 切换分支
  /git /diff [args]         - 查看差异
  /git /log [args]          - 查看提交历史（默认显示最近10条）
  /git /pull [args]         - 拉取远程更新
  /git /push [args]         - 推送到远程
  /git /reset <mode> [commit] - 重置（hard/soft/mixed）

平台管理:
  /git /github              - GitHub 配置管理
  /git /gitlab              - GitLab 配置管理
  /git /platform            - 平台切换管理

详细帮助:
  /git /github /help        - GitHub 配置帮助
  /git /gitlab /help        - GitLab 配置帮助
  /git /platform /help      - 平台切换帮助

示例:
  /git /status
  /git /commit "feat: 添加新功能"
  /git /checkout develop
  /git /reset soft HEAD~1
  /git /github /setup       - 配置 GitHub 连接
  /git /gitlab /setup       - 配置 GitLab 连接
  /git /platform /switch gitlab - 切换到 GitLab 平台
        """)

    def git_status(self, args: str) -> None:
        """Handle the git/status command."""
        code, stdout, stderr = self._run_git_command(["status"])
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_commit(self, args: str) -> None:
        """Handle the git/commit command."""
        if not args:
            print(get_message("commit_message_required"))
            return

        # 首先执行添加所有更改 (git add .)
        self._run_git_command(["add", "."])

        # 执行提交
        code, stdout, stderr = self._run_git_command(["commit", "-m", args])
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_branch(self, args: str) -> None:
        """Handle the git/branch command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["branch"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_checkout(self, args: str) -> None:
        """Handle the git/checkout command."""
        if not args:
            print(get_message("checkout_branch_required"))
            return

        args_list = args.split()
        code, stdout, stderr = self._run_git_command(["checkout"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_diff(self, args: str) -> None:
        """Handle the git/diff command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["diff"] + args_list)
        if code == 0:
            if stdout:
                print(f"\n{stdout}")
            else:
                print(get_message("no_differences"))
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_log(self, args: str) -> None:
        """Handle the git/log command."""
        args_list = args.split() if args else ["--oneline", "-n", "10"]
        code, stdout, stderr = self._run_git_command(["log"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_pull(self, args: str) -> None:
        """Handle the git/pull command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["pull"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def git_push(self, args: str) -> None:
        """Handle the git/push command."""
        args_list = args.split() if args else []
        code, stdout, stderr = self._run_git_command(["push"] + args_list)
        if code == 0:
            print(f"\n{stdout}")
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    def handle_reset(self, args: str) -> None:
        """Handle the git/reset command.
        
        Args:
            args: The reset mode (hard/soft/mixed) and optional commit hash
        """
        if not args:
            print(get_message("reset_mode_required"))
            return
            
        args_list = args.split()
        mode = args_list[0]
        commit = args_list[1] if len(args_list) > 1 else "HEAD"
        
        if mode not in ["hard", "soft", "mixed"]:
            print(get_message_with_format("invalid_reset_mode", mode=mode))
            return
            
        code, stdout, stderr = self._run_git_command(["reset", f"--{mode}", commit])
        if code == 0:
            print(f"\n{stdout}")
            print(get_message_with_format("reset_success", mode=mode, commit=commit))
        else:
            print(f"{get_message('error_prefix')} {stderr}")

    async def handle_github(self, args: str) -> None:
        """
        处理 /git /github 命令

        子命令：
        - /setup - 引导式配置
        - /list - 列出所有配置
        - /modify <name> - 修改配置
        - /delete <name> - 删除配置
        - /test <name> - 测试连接
        """
        args = args.strip()

        if not args or args == "/help":
            self._show_github_help()
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0]
        sub_args = parts[1] if len(parts) > 1 else ""

        if subcmd == "/setup":
            await self._github_setup()
        elif subcmd == "/list":
            self._github_list()
        elif subcmd == "/modify":
            await self._github_modify(sub_args)
        elif subcmd == "/delete":
            await self._github_delete(sub_args)
        elif subcmd == "/test":
            self._github_test(sub_args)
        else:
            print(f"❌ 未知的子命令: {subcmd}")
            self._show_github_help()

    async def _github_setup(self) -> None:
        """GitHub 引导式配置"""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # 欢迎界面
        console.print("\n")
        console.print(Panel(
            "[bold cyan]GitHub 配置向导[/bold cyan]\n\n"
            "让我们配置您的 GitHub 连接\n\n"
            "[yellow]提示：[/yellow] 配置将保存在插件配置文件中",
            title="🚀 GitHub 配置",
            border_style="cyan"
        ))

        try:
            # 1. 配置名称
            console.print("\n[cyan]1. 配置名称[/cyan]")
            console.print("   输入便于识别的名称（如 'personal-github', 'work-github'）")
            name = (await async_input("   名称: ")).strip()
            if not name:
                console.print("[red]❌ 配置名称不能为空[/red]")
                return

            # 检查是否已存在
            if self.platform_manager.get_config("github", name):
                if not await async_confirm(f"配置 '{name}' 已存在，是否覆盖？", default=False):
                    console.print("[yellow]已取消[/yellow]")
                    return

            # 2. API 地址
            console.print("\n[cyan]2. GitHub API 地址[/cyan]")
            console.print("   [dim]默认：https://api.github.com[/dim]")
            console.print("   [dim]企业版：https://github.example.com/api/v3[/dim]")
            base_url = (await async_input("   地址 [默认: https://api.github.com]: ")).strip()
            if not base_url:
                base_url = "https://api.github.com"

            # 3. Personal Access Token
            console.print("\n[cyan]3. Personal Access Token[/cyan]")
            console.print("   💡 如何获取：")
            console.print("      1. GitHub → Settings → Developer settings")
            console.print("      2. Personal access tokens → Tokens (classic)")
            console.print("      3. Generate new token")
            console.print("      4. 勾选权限: repo, read:user")
            console.print("      5. 复制生成的 token\n")
            token = (await async_input("   Token: ", is_password=True)).strip()
            if not token:
                console.print("[red]❌ Token 不能为空[/red]")
                return

            # 4. SSL 验证
            console.print("\n[cyan]4. SSL 验证 (可选)[/cyan]")
            verify_ssl = await async_confirm("   验证 SSL 证书？", default=True)

            # 5. 超时设置
            console.print("\n[cyan]5. 超时设置 (可选)[/cyan]")
            timeout_str = (await async_input("   超时时间（秒） [默认: 30]: ")).strip()
            timeout = 30
            if timeout_str:
                try:
                    timeout = int(timeout_str)
                except ValueError:
                    console.print("[yellow]⚠️  无效值，使用默认值 30[/yellow]")

            # 确认信息
            console.print("\n")
            table = Table(title="📋 确认配置信息", show_header=True, header_style="bold magenta")
            table.add_column("配置项", style="cyan", width=20)
            table.add_column("值", style="green")

            table.add_row("配置名称", name)
            table.add_row("平台类型", "GitHub")
            table.add_row("API 地址", base_url)
            table.add_row("Access Token", "******（已设置）")
            table.add_row("SSL 验证", "是" if verify_ssl else "否")
            table.add_row("超时时间", f"{timeout} 秒")

            console.print(table)
            console.print()

            if not await async_confirm("是否保存以上配置？", default=True):
                console.print("[yellow]已取消[/yellow]")
                return

            # 保存配置
            from autocoder.common.git_platform_config import GitPlatformConfig

            config = GitPlatformConfig(
                name=name,
                platform="github",
                base_url=base_url,
                token=token,
                verify_ssl=verify_ssl,
                timeout=timeout
            )

            if self.platform_manager.add_config(config):
                console.print("\n")
                console.print(Panel(
                    f"[bold green]✓[/bold green] GitHub 配置 '{name}' 已保存！\n\n"
                    "使用以下命令切换到此配置：\n"
                    f"[cyan]/git /platform /switch github {name}[/cyan]",
                    title="✅ 配置成功",
                    border_style="green"
                ))

                # 如果这是当前平台的配置，同步到 PR 模块
                if self.platform_manager.current_platform == "github":
                    current_config = self.platform_manager.get_current_config()
                    if current_config and current_config.name == name:
                        self._sync_to_pr_module(current_config)

                # 自动测试连接
                if await async_confirm("\n是否测试连接？", default=True):
                    self._github_test(name)
            else:
                console.print("[red]❌ 保存配置失败[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]已取消[/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ 配置过程出错: {e}[/red]")

    def _github_list(self) -> None:
        """列出所有 GitHub 配置"""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        configs = self.platform_manager.list_configs("github")

        if not configs:
            console.print("\n[yellow]📭 还没有 GitHub 配置[/yellow]")
            console.print("\n使用 [cyan]/git /github /setup[/cyan] 添加配置\n")
            return

        # 获取当前配置
        current_platform = self.platform_manager.current_platform
        current_name = self.platform_manager.current_config.get("github", "")

        table = Table(title="📋 GitHub 配置列表", show_header=True, header_style="bold magenta")
        table.add_column("配置名称", style="cyan")
        table.add_column("API 地址", style="green")
        table.add_column("SSL 验证", style="yellow")
        table.add_column("超时", style="blue")
        table.add_column("最后测试", style="dim")
        table.add_column("状态", style="bold")

        for config in configs:
            # 标记当前激活的配置
            status = ""
            if current_platform == "github" and config.name == current_name:
                status = "✅ 当前"

            ssl_str = "✓" if config.verify_ssl else "✗"
            last_tested = config.last_tested[:10] if config.last_tested else "未测试"

            table.add_row(
                config.name,
                config.base_url,
                ssl_str,
                f"{config.timeout}s",
                last_tested,
                status
            )

        console.print("\n")
        console.print(table)
        console.print()

    async def _github_modify(self, name: str) -> None:
        """修改 GitHub 配置"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /github /modify <配置名>")
            return

        config = self.platform_manager.get_config("github", name)
        if not config:
            print(f"❌ 配置不存在: {name}")
            return

        from rich.console import Console
        console = Console()

        console.print(f"\n[cyan]修改配置: {name}[/cyan]")
        console.print("[dim]直接回车保持原值[/dim]\n")

        # 依次修改各个字段
        # API 地址
        new_url = (await async_input(f"API 地址 [{config.base_url}]: ")).strip()
        if new_url:
            config.base_url = new_url

        # Token
        change_token = await async_confirm("是否更换 Token？", default=False)
        if change_token:
            new_token = (await async_input("新 Token: ", is_password=True)).strip()
            if new_token:
                config.token = new_token

        # SSL 验证
        config.verify_ssl = await async_confirm(
            f"验证 SSL？",
            default=config.verify_ssl
        )

        # 超时
        new_timeout = (await async_input(f"超时时间（秒） [{config.timeout}]: ")).strip()
        if new_timeout:
            try:
                config.timeout = int(new_timeout)
            except ValueError:
                console.print("[yellow]⚠️  无效值，保持原值[/yellow]")

        # 保存
        if self.platform_manager.save_configs():
            console.print(f"\n[green]✅ 配置 '{name}' 已更新[/green]\n")
        else:
            console.print(f"\n[red]❌ 更新失败[/red]\n")

    async def _github_delete(self, name: str) -> None:
        """删除 GitHub 配置"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /github /delete <配置名>")
            return

        from rich.console import Console

        console = Console()

        if not self.platform_manager.get_config("github", name):
            console.print(f"\n[red]❌ 配置不存在: {name}[/red]\n")
            return

        if await async_confirm(f"确认删除配置 '{name}'？", default=False):
            if self.platform_manager.delete_config("github", name):
                console.print(f"\n[green]✅ 已删除配置: {name}[/green]\n")
            else:
                console.print(f"\n[red]❌ 删除失败[/red]\n")
        else:
            console.print("\n[yellow]已取消[/yellow]\n")

    def _github_test(self, name: str) -> None:
        """测试 GitHub 连接"""
        import requests
        from rich.console import Console

        console = Console()

        name = name.strip()
        if not name:
            console.print("\n[red]❌ 请指定配置名称[/red]")
            console.print("用法: [cyan]/git /github /test <配置名>[/cyan]\n")
            return

        config = self.platform_manager.get_config("github", name)
        if not config:
            console.print(f"\n[red]❌ 配置不存在: {name}[/red]\n")
            return

        console.print(f"\n🔍 正在测试 GitHub 连接: {config.name}")
        console.print(f"   地址: {config.base_url}\n")

        # 显示进度
        with console.status("[bold green]测试中...", spinner="dots"):
            try:
                # 调用 GitHub API
                headers = {
                    "Authorization": f"token {config.token}",
                    "Accept": "application/vnd.github.v3+json"
                }

                response = requests.get(
                    f"{config.base_url}/user",
                    headers=headers,
                    verify=config.verify_ssl,
                    timeout=config.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    username = data.get("login", "未知")
                    user_id = data.get("id", "未知")
                    user_type = data.get("type", "User")

                    # 更新最后测试时间
                    config.update_last_tested()
                    self.platform_manager.save_configs()

                    # 显示成功信息
                    console.print("[green]✅ 连接成功！[/green]\n")
                    console.print(f"[bold]用户信息：[/bold]")
                    console.print(f"  用户名: {username}")
                    console.print(f"  用户ID: {user_id}")
                    console.print(f"  类型: {user_type}")

                    # 显示 API 限额信息
                    rate_limit = response.headers.get("X-RateLimit-Limit")
                    rate_remaining = response.headers.get("X-RateLimit-Remaining")
                    if rate_limit and rate_remaining:
                        console.print(f"\n[dim]API 限额: {rate_remaining}/{rate_limit}[/dim]")

                    console.print()

                elif response.status_code == 401:
                    console.print("[red]❌ 认证失败[/red]")
                    console.print("   Token 无效或已过期\n")

                elif response.status_code == 403:
                    console.print("[red]❌ 访问被拒绝[/red]")
                    console.print("   可能是 Token 权限不足或 API 限额耗尽\n")

                else:
                    console.print(f"[red]❌ 连接失败[/red]")
                    console.print(f"   HTTP {response.status_code}: {response.reason}\n")

            except requests.exceptions.SSLError as e:
                console.print("[red]❌ SSL 证书验证失败[/red]")
                console.print(f"   {str(e)}")
                console.print("\n💡 尝试禁用 SSL 验证:")
                console.print(f"   [cyan]/git /github /modify {name}[/cyan]\n")

            except requests.exceptions.Timeout:
                console.print("[red]❌ 连接超时[/red]")
                console.print(f"   超过 {config.timeout} 秒未响应\n")

            except requests.exceptions.ConnectionError as e:
                console.print("[red]❌ 连接错误[/red]")
                console.print("   无法连接到服务器")
                console.print(f"   请检查网络和地址: {config.base_url}\n")

            except Exception as e:
                console.print(f"[red]❌ 测试失败: {str(e)}[/red]\n")

    def _show_github_help(self) -> None:
        """显示 GitHub 命令帮助"""
        print("""
📋 GitHub 配置管理

使用方法:
  /git /github /setup              - 引导式配置 GitHub
  /git /github /list               - 列出所有 GitHub 配置
  /git /github /modify <name>      - 修改指定配置
  /git /github /delete <name>      - 删除指定配置
  /git /github /test <name>        - 测试连接

示例:
  /git /github /setup
  /git /github /list
  /git /github /modify personal-github
  /git /github /delete old-config
        """)

    async def handle_gitlab(self, args: str) -> None:
        """
        处理 /git /gitlab 命令

        子命令：
        - /setup - 引导式配置
        - /list - 列出所有配置
        - /modify <name> - 修改配置
        - /delete <name> - 删除配置
        - /test <name> - 测试连接
        """
        args = args.strip()

        if not args or args == "/help":
            self._show_gitlab_help()
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0]
        sub_args = parts[1] if len(parts) > 1 else ""

        if subcmd == "/setup":
            await self._gitlab_setup()
        elif subcmd == "/list":
            self._gitlab_list()
        elif subcmd == "/modify":
            await self._gitlab_modify(sub_args)
        elif subcmd == "/delete":
            await self._gitlab_delete(sub_args)
        elif subcmd == "/test":
            self._gitlab_test(sub_args)
        else:
            print(f"❌ 未知的子命令: {subcmd}")
            self._show_gitlab_help()

    async def _gitlab_setup(self) -> None:
        """GitLab 引导式配置"""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        console.print("\n")
        console.print(Panel(
            "[bold cyan]GitLab 配置向导[/bold cyan]\n\n"
            "让我们配置您的 GitLab 连接\n\n"
            "[yellow]提示：[/yellow] 支持 GitLab.com 和私有部署",
            title="🚀 GitLab 配置",
            border_style="cyan"
        ))

        try:
            # 1. 配置名称
            console.print("\n[cyan]1. 配置名称[/cyan]")
            console.print("   输入便于识别的名称（如 'company-gitlab', 'personal-gitlab'）")
            name = (await async_input("   名称: ")).strip()
            if not name:
                console.print("[red]❌ 配置名称不能为空[/red]")
                return

            if self.platform_manager.get_config("gitlab", name):
                if not await async_confirm(f"配置 '{name}' 已存在，是否覆盖？", default=False):
                    console.print("[yellow]已取消[/yellow]")
                    return

            # 2. GitLab 地址
            console.print("\n[cyan]2. GitLab 地址[/cyan]")
            console.print("   [dim]公网 GitLab: https://gitlab.com[/dim]")
            console.print("   [dim]私有部署: https://gitlab.example.com[/dim]")
            console.print("   [dim]内网 GitLab: http://10.x.x.x （会自动添加 /api/v4）[/dim]")
            base_url_input = (await async_input("   地址: ")).strip()

            if not base_url_input:
                console.print("[red]❌ GitLab 地址不能为空[/red]")
                return

            # 自动添加 API 路径
            if not base_url_input.endswith("/api/v4"):
                if base_url_input == "https://gitlab.com":
                    base_url = "https://gitlab.com/api/v4"
                else:
                    base_url = f"{base_url_input.rstrip('/')}/api/v4"
            else:
                base_url = base_url_input

            # 3. Personal Access Token
            console.print("\n[cyan]3. Personal Access Token[/cyan]")
            console.print("   💡 如何获取：")
            console.print("      1. 登录 GitLab")
            console.print("      2. Settings → Access Tokens")
            console.print("      3. Add new token")
            console.print("      4. 勾选权限: api")
            console.print("      5. 复制生成的 token\n")
            token = (await async_input("   Token: ", is_password=True)).strip()
            if not token:
                console.print("[red]❌ Token 不能为空[/red]")
                return

            # 4. SSL 验证（私有部署可能需要禁用）
            console.print("\n[cyan]4. SSL 验证 (可选)[/cyan]")
            console.print("   [dim]内网私有部署可能需要选择 'n'[/dim]")
            verify_ssl = await async_confirm("   验证 SSL 证书？", default=True)

            # 5. 超时设置
            console.print("\n[cyan]5. 超时设置 (可选)[/cyan]")
            timeout_str = (await async_input("   超时时间（秒） [默认: 30]: ")).strip()
            timeout = 30
            if timeout_str:
                try:
                    timeout = int(timeout_str)
                except ValueError:
                    console.print("[yellow]⚠️  无效值，使用默认值 30[/yellow]")

            # 确认信息
            console.print("\n")
            table = Table(title="📋 确认配置信息", show_header=True, header_style="bold magenta")
            table.add_column("配置项", style="cyan", width=20)
            table.add_column("值", style="green")

            table.add_row("配置名称", name)
            table.add_row("平台类型", "GitLab")
            table.add_row("GitLab 地址", base_url_input)
            table.add_row("API 地址", base_url)
            table.add_row("Access Token", "******（已设置）")
            table.add_row("SSL 验证", "是" if verify_ssl else "否")
            table.add_row("超时时间", f"{timeout} 秒")

            console.print(table)
            console.print()

            if not await async_confirm("是否保存以上配置？", default=True):
                console.print("[yellow]已取消[/yellow]")
                return

            # 保存配置
            from autocoder.common.git_platform_config import GitPlatformConfig

            config = GitPlatformConfig(
                name=name,
                platform="gitlab",
                base_url=base_url,
                token=token,
                verify_ssl=verify_ssl,
                timeout=timeout
            )

            if self.platform_manager.add_config(config):
                console.print("\n")
                console.print(Panel(
                    f"[bold green]✓[/bold green] GitLab 配置 '{name}' 已保存！\n\n"
                    "使用以下命令切换到此配置：\n"
                    f"[cyan]/git /platform /switch gitlab {name}[/cyan]",
                    title="✅ 配置成功",
                    border_style="green"
                ))

                # 如果这是当前平台的配置，同步到 PR 模块
                if self.platform_manager.current_platform == "gitlab":
                    current_config = self.platform_manager.get_current_config()
                    if current_config and current_config.name == name:
                        self._sync_to_pr_module(current_config)

                # 自动测试连接
                if await async_confirm("\n是否测试连接？", default=True):
                    self._gitlab_test(name)
            else:
                console.print("[red]❌ 保存配置失败[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]已取消[/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ 配置过程出错: {e}[/red]")

    def _gitlab_list(self) -> None:
        """列出所有 GitLab 配置"""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        configs = self.platform_manager.list_configs("gitlab")

        if not configs:
            console.print("\n[yellow]📭 还没有 GitLab 配置[/yellow]")
            console.print("\n使用 [cyan]/git /gitlab /setup[/cyan] 添加配置\n")
            return

        # 获取当前配置
        current_platform = self.platform_manager.current_platform
        current_name = self.platform_manager.current_config.get("gitlab", "")

        table = Table(title="📋 GitLab 配置列表", show_header=True, header_style="bold magenta")
        table.add_column("配置名称", style="cyan")
        table.add_column("API 地址", style="green")
        table.add_column("SSL 验证", style="yellow")
        table.add_column("超时", style="blue")
        table.add_column("最后测试", style="dim")
        table.add_column("状态", style="bold")

        for config in configs:
            # 标记当前激活的配置
            status = ""
            if current_platform == "gitlab" and config.name == current_name:
                status = "✅ 当前"

            ssl_str = "✓" if config.verify_ssl else "✗"
            last_tested = config.last_tested[:10] if config.last_tested else "未测试"

            table.add_row(
                config.name,
                config.base_url,
                ssl_str,
                f"{config.timeout}s",
                last_tested,
                status
            )

        console.print("\n")
        console.print(table)
        console.print()

    async def _gitlab_modify(self, name: str) -> None:
        """修改 GitLab 配置"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /gitlab /modify <配置名>")
            return

        config = self.platform_manager.get_config("gitlab", name)
        if not config:
            print(f"❌ 配置不存在: {name}")
            return

        from rich.console import Console
        console = Console()

        console.print(f"\n[cyan]修改配置: {name}[/cyan]")
        console.print("[dim]直接回车保持原值[/dim]\n")

        # 依次修改各个字段
        # API 地址
        new_url = (await async_input(f"API 地址 [{config.base_url}]: ")).strip()
        if new_url:
            config.base_url = new_url

        # Token
        change_token = await async_confirm("是否更换 Token？", default=False)
        if change_token:
            new_token = (await async_input("新 Token: ", is_password=True)).strip()
            if new_token:
                config.token = new_token

        # SSL 验证
        config.verify_ssl = await async_confirm(
            f"验证 SSL？",
            default=config.verify_ssl
        )

        # 超时
        new_timeout = (await async_input(f"超时时间（秒） [{config.timeout}]: ")).strip()
        if new_timeout:
            try:
                config.timeout = int(new_timeout)
            except ValueError:
                console.print("[yellow]⚠️  无效值，保持原值[/yellow]")

        # 保存
        if self.platform_manager.save_configs():
            console.print(f"\n[green]✅ 配置 '{name}' 已更新[/green]\n")
        else:
            console.print(f"\n[red]❌ 更新失败[/red]\n")

    async def _gitlab_delete(self, name: str) -> None:
        """删除 GitLab 配置"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /gitlab /delete <配置名>")
            return

        from rich.console import Console

        console = Console()

        if not self.platform_manager.get_config("gitlab", name):
            console.print(f"\n[red]❌ 配置不存在: {name}[/red]\n")
            return

        if await async_confirm(f"确认删除配置 '{name}'？", default=False):
            if self.platform_manager.delete_config("gitlab", name):
                console.print(f"\n[green]✅ 已删除配置: {name}[/green]\n")
            else:
                console.print(f"\n[red]❌ 删除失败[/red]\n")
        else:
            console.print("\n[yellow]已取消[/yellow]\n")

    def _gitlab_test(self, name: str) -> None:
        """测试 GitLab 连接"""
        import requests
        from rich.console import Console

        console = Console()

        name = name.strip()
        if not name:
            console.print("\n[red]❌ 请指定配置名称[/red]")
            console.print("用法: [cyan]/git /gitlab /test <配置名>[/cyan]\n")
            return

        config = self.platform_manager.get_config("gitlab", name)
        if not config:
            console.print(f"\n[red]❌ 配置不存在: {name}[/red]\n")
            return

        console.print(f"\n🔍 正在测试 GitLab 连接: {config.name}")
        console.print(f"   地址: {config.base_url}\n")

        with console.status("[bold green]测试中...", spinner="dots"):
            try:
                # 调用 GitLab API
                headers = {
                    "Authorization": f"Bearer {config.token}",
                    "Content-Type": "application/json"
                }

                # 尝试标准 GitLab API 端点 /user
                response = requests.get(
                    f"{config.base_url}/user",
                    headers=headers,
                    verify=config.verify_ssl,
                    timeout=config.timeout
                )

                # 标准 API 成功
                if response.status_code == 200:
                    data = response.json()
                    username = data.get("username", "未知")
                    user_id = data.get("id", "未知")
                    name_full = data.get("name", "未知")

                    # 更新最后测试时间
                    config.update_last_tested()
                    self.platform_manager.save_configs()

                    # 显示成功信息
                    console.print("[green]✅ 连接成功！[/green]\n")
                    console.print(f"[bold]用户信息：[/bold]")
                    console.print(f"  用户名: {username}")
                    console.print(f"  姓名: {name_full}")
                    console.print(f"  用户ID: {user_id}")

                    # 尝试获取 GitLab 版本
                    try:
                        version_response = requests.get(
                            f"{config.base_url}/version",
                            headers=headers,
                            verify=config.verify_ssl,
                            timeout=config.timeout
                        )
                        if version_response.status_code == 200:
                            version_data = version_response.json()
                            gitlab_version = version_data.get("version", "未知")
                            console.print(f"\n[dim]GitLab 版本: {gitlab_version}[/dim]")
                    except:
                        pass

                    console.print()

                # 标准 API 失败，尝试内网 GitLab API 端点 /version
                elif response.status_code in [401, 403, 404]:
                    console.print(f"[yellow]⚠️  标准端点 /user 访问失败 (HTTP {response.status_code})[/yellow]")
                    console.print("[yellow]   尝试内网 GitLab API 端点...[/yellow]\n")

                    # 尝试 /version 端点（内网 GitLab 可能使用这个端点）
                    version_response = requests.get(
                        f"{config.base_url}/version",
                        headers=headers,
                        verify=config.verify_ssl,
                        timeout=config.timeout
                    )

                    if version_response.status_code == 200:
                        version_data = version_response.json()
                        gitlab_version = version_data.get("version", "未知")

                        # 更新最后测试时间
                        config.update_last_tested()
                        self.platform_manager.save_configs()

                        # 显示成功信息
                        console.print("[green]✅ 连接成功！（内网 GitLab）[/green]\n")
                        console.print(f"[bold]GitLab 版本信息：[/bold]")
                        console.print(f"  版本: {gitlab_version}")
                        console.print(f"  API 路径: {config.base_url}")
                        console.print(f"\n[dim]💡 检测到内网 GitLab，API 路径结构可能与标准 GitLab 不同[/dim]")

                        # 尝试访问项目端点验证 token 权限
                        try:
                            projects_response = requests.get(
                                f"{config.base_url}/version/projects",
                                headers=headers,
                                verify=config.verify_ssl,
                                timeout=config.timeout
                            )
                            if projects_response.status_code == 200:
                                console.print(f"[dim]   Token 权限验证: ✓ 可访问项目列表[/dim]")
                        except:
                            pass

                        console.print()

                    elif version_response.status_code == 401:
                        console.print("[red]❌ 认证失败[/red]")
                        console.print("   Token 无效或已过期\n")

                    elif version_response.status_code == 403:
                        console.print("[red]❌ 访问被拒绝[/red]")
                        console.print("   Token 权限不足\n")

                    else:
                        console.print(f"[red]❌ 连接失败[/red]")
                        console.print(f"   HTTP {version_response.status_code}: {version_response.reason}\n")
                        console.print("[yellow]💡 提示：[/yellow]")
                        console.print("   1. 请确认 Token 有效且权限充足")
                        console.print("   2. 如果是内网 GitLab，请咨询管理员确认正确的 API 端点\n")

                else:
                    console.print(f"[red]❌ 连接失败[/red]")
                    console.print(f"   HTTP {response.status_code}: {response.reason}\n")

            except requests.exceptions.SSLError as e:
                console.print("[red]❌ SSL 证书验证失败[/red]")
                console.print(f"   {str(e)}")
                console.print("\n💡 这在私有部署的 GitLab 中很常见")
                console.print("   尝试禁用 SSL 验证:")
                console.print(f"   [cyan]/git /gitlab /modify {name}[/cyan]\n")

            except requests.exceptions.Timeout:
                console.print("[red]❌ 连接超时[/red]")
                console.print(f"   超过 {config.timeout} 秒未响应\n")

            except requests.exceptions.ConnectionError:
                console.print("[red]❌ 连接错误[/red]")
                console.print("   无法连接到服务器")
                console.print(f"   请检查网络和地址: {config.base_url}\n")

            except Exception as e:
                console.print(f"[red]❌ 测试失败: {str(e)}[/red]\n")

    def _show_gitlab_help(self) -> None:
        """显示 GitLab 命令帮助"""
        print("""
📋 GitLab 配置管理

使用方法:
  /git /gitlab /setup              - 引导式配置 GitLab
  /git /gitlab /list               - 列出所有 GitLab 配置
  /git /gitlab /modify <name>      - 修改指定配置
  /git /gitlab /delete <name>      - 删除指定配置
  /git /gitlab /test <name>        - 测试连接

示例:
  /git /gitlab /setup
  /git /gitlab /list
  /git /gitlab /modify company-gitlab
        """)

    def _sync_to_pr_module(self, config) -> None:
        """
        同步配置到 PR 模块

        Args:
            config: GitPlatformConfig 对象
        """
        try:
            from autocoder.common.pull_requests.manager import set_global_config
            from autocoder.common.pull_requests.models import PRConfig, PlatformType
            from loguru import logger

            # 将 GitPlatformConfig 转换为 PRConfig
            pr_config = PRConfig(
                platform=PlatformType(config.platform),
                token=config.token,
                base_url=config.base_url,
                timeout=config.timeout,
                verify_ssl=config.verify_ssl
            )

            # 设置全局配置
            set_global_config(pr_config)
            logger.info(f"已同步配置到 PR 模块: {config.platform}/{config.name}")

        except Exception as e:
            from loguru import logger
            logger.error(f"同步配置到 PR 模块失败: {e}")

    def handle_platform(self, args: str) -> None:
        """
        处理 /git /platform 命令

        子命令：
        - (无) - 显示当前平台状态
        - /switch <platform> [config_name] - 切换平台
        - /list - 列出所有平台配置概览
        """
        args = args.strip()

        if not args or args == "/help":
            if not args:
                self._platform_status()
            else:
                self._show_platform_help()
            return

        parts = args.split(maxsplit=2)
        subcmd = parts[0]

        if subcmd == "/switch":
            platform = parts[1] if len(parts) > 1 else ""
            config_name = parts[2] if len(parts) > 2 else ""
            self._platform_switch(platform, config_name)
        elif subcmd == "/list":
            self._platform_list()
        else:
            print(f"❌ 未知的子命令: {subcmd}")
            self._show_platform_help()

    def _platform_status(self) -> None:
        """显示当前平台状态"""
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        current_config = self.platform_manager.get_current_config()

        if not current_config:
            console.print("\n[yellow]⚠️  未配置任何平台[/yellow]\n")
            console.print("请先配置平台：")
            console.print("  [cyan]/git /github /setup[/cyan]  - 配置 GitHub")
            console.print("  [cyan]/git /gitlab /setup[/cyan]  - 配置 GitLab\n")
            return

        # 构建状态信息
        platform_name = "GitHub" if current_config.platform == "github" else "GitLab"
        ssl_status = "✓ 启用" if current_config.verify_ssl else "✗ 禁用"

        status_text = (
            f"[bold cyan]平台：[/bold cyan] {platform_name}\n"
            f"[bold cyan]配置：[/bold cyan] {current_config.name}\n"
            f"[bold cyan]地址：[/bold cyan] {current_config.base_url}\n"
            f"[bold cyan]SSL：[/bold cyan] {ssl_status}\n"
            f"[bold cyan]超时：[/bold cyan] {current_config.timeout} 秒"
        )

        # 最后测试时间
        if current_config.last_tested:
            test_time = current_config.last_tested[:19].replace('T', ' ')
            status_text += f"\n[bold cyan]测试：[/bold cyan] {test_time}"

        console.print("\n")
        console.print(Panel(
            status_text,
            title="📍 当前平台配置",
            border_style="cyan"
        ))
        console.print()

    def _platform_switch(self, platform: str, config_name: str = "") -> None:
        """切换平台"""
        from rich.console import Console

        console = Console()

        if not platform:
            console.print("\n[red]❌ 请指定平台类型[/red]")
            console.print("\n用法: [cyan]/git /platform /switch <platform> [config_name][/cyan]")
            console.print("\n平台类型: github, gitlab\n")
            return

        platform = platform.lower()

        if platform not in ["github", "gitlab"]:
            console.print(f"\n[red]❌ 不支持的平台: {platform}[/red]")
            console.print("\n支持的平台: github, gitlab\n")
            return

        # 检查是否有配置
        if not self.platform_manager.has_config(platform):
            console.print(f"\n[red]❌ 平台 {platform} 还没有配置[/red]\n")
            console.print(f"请先配置: [cyan]/git /{platform} /setup[/cyan]\n")
            return

        # 如果未指定配置名，显示可用配置让用户选择
        if not config_name:
            configs = self.platform_manager.list_configs(platform)

            if len(configs) == 1:
                # 只有一个配置，直接使用
                config_name = configs[0].name
            else:
                # 多个配置，显示列表
                console.print(f"\n[yellow]平台 {platform} 有多个配置，请指定：[/yellow]\n")
                for i, cfg in enumerate(configs, 1):
                    marker = "✓" if self.platform_manager.current_config.get(platform) == cfg.name else " "
                    console.print(f"  [{marker}] {i}. {cfg.name} ({cfg.base_url})")
                console.print(f"\n用法: [cyan]/git /platform /switch {platform} <配置名>[/cyan]\n")
                return

        # 执行切换
        new_config = self.platform_manager.switch_platform(platform, config_name)

        if new_config:
            platform_name = "GitHub" if platform == "github" else "GitLab"
            console.print(f"\n[green]✅ 已切换到 {platform_name}: {new_config.name}[/green]")
            console.print(f"   地址: {new_config.base_url}\n")

            # 同步到 PR 模块（Phase 6 实现）
            self._sync_to_pr_module(new_config)
        else:
            console.print(f"\n[red]❌ 切换失败: 配置 '{config_name}' 不存在[/red]\n")

    def _platform_list(self) -> None:
        """列出所有平台配置概览"""
        from rich.console import Console
        from rich.table import Table

        console = Console()

        # 获取所有配置
        github_configs = self.platform_manager.list_configs("github")
        gitlab_configs = self.platform_manager.list_configs("gitlab")

        if not github_configs and not gitlab_configs:
            console.print("\n[yellow]📭 还没有配置任何平台[/yellow]\n")
            console.print("请先配置平台：")
            console.print("  [cyan]/git /github /setup[/cyan]  - 配置 GitHub")
            console.print("  [cyan]/git /gitlab /setup[/cyan]  - 配置 GitLab\n")
            return

        current_platform = self.platform_manager.current_platform
        current_configs = self.platform_manager.current_config

        # 创建表格
        table = Table(title="📋 所有平台配置概览", show_header=True, header_style="bold magenta")
        table.add_column("平台", style="cyan", width=10)
        table.add_column("配置名称", style="green", width=20)
        table.add_column("地址", style="blue")
        table.add_column("状态", style="bold", width=10)

        # 添加 GitHub 配置
        for config in github_configs:
            status = ""
            if current_platform == "github" and current_configs.get("github") == config.name:
                status = "✅ 当前"

            table.add_row("GitHub", config.name, config.base_url, status)

        # 添加 GitLab 配置
        for config in gitlab_configs:
            status = ""
            if current_platform == "gitlab" and current_configs.get("gitlab") == config.name:
                status = "✅ 当前"

            table.add_row("GitLab", config.name, config.base_url, status)

        console.print("\n")
        console.print(table)
        console.print()

    def _show_platform_help(self) -> None:
        """显示平台命令帮助"""
        print("""
📋 平台管理

使用方法:
  /git /platform                           - 显示当前平台状态
  /git /platform /switch <platform> [name] - 切换平台
  /git /platform /list                     - 列出所有平台配置

示例:
  /git /platform
  /git /platform /switch gitlab
  /git /platform /switch github work-github
  /git /platform /list
        """)

    def get_help_text(self) -> Optional[str]:
        """Get the help text displayed in the startup screen.

        Returns:
            Help text with formatted subcommands
        """
        return """  \033[94m/git\033[0m - \033[92mGit 辅助工具\033[0m
    \033[94m/git /status\033[0m - 查看仓库状态
    \033[94m/git /commit\033[0m \033[93m<message>\033[0m - 提交更改
    \033[94m/git /branch\033[0m \033[93m[args]\033[0m - 分支管理
    \033[94m/git /checkout\033[0m \033[93m<branch>\033[0m - 切换分支
    \033[94m/git /diff\033[0m \033[93m[args]\033[0m - 查看差异
    \033[94m/git /log\033[0m \033[93m[args]\033[0m - 查看提交历史
    \033[94m/git /pull\033[0m \033[93m[args]\033[0m - 拉取远程更新
    \033[94m/git /push\033[0m \033[93m[args]\033[0m - 推送到远程
    \033[94m/git /reset\033[0m \033[93m<mode> [commit]\033[0m - 重置（hard/soft/mixed）
    \033[94m/git /github\033[0m - GitHub 配置管理
    \033[94m/git /gitlab\033[0m - GitLab 配置管理"""

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        print(f"[{self.name}] {get_message('git_helper_shutdown')}")
