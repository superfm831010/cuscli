"""
Git Helper Plugin for Chat Auto Coder.
Provides convenient Git commands and information display.
"""

import os
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple

from autocoder.plugins import Plugin, PluginManager
from autocoder.common.international import register_messages, get_message, get_message_with_format


class GitHelperPlugin(Plugin):
    """Git helper plugin for the Chat Auto Coder."""

    name = "git_helper"
    description = "Git helper plugin providing Git commands and status"
    version = "0.1.0"

    def __init__(self, manager: PluginManager, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """Initialize the Git helper plugin."""
        super().__init__(manager, config, config_path)

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
                     "/log", "/pull", "/push", "/reset", "/github", "/gitlab"],
            "/git /reset": ["hard", "soft", "mixed"],
            "/git /github": ["/setup", "/list", "/modify", "/delete", "/test"],
            "/git /gitlab": ["/setup", "/list", "/modify", "/delete", "/test"],
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

        # 添加 GitHub 配置名称补全
        try:
            github_configs = self.platform_manager.list_configs("github")
            config_names = [c.name for c in github_configs]
            if config_names:
                completions["/git /github /modify"] = config_names
                completions["/git /github /delete"] = config_names
                completions["/git /github /test"] = config_names
        except Exception:
            pass

        # 添加 GitLab 配置名称补全
        try:
            gitlab_configs = self.platform_manager.list_configs("gitlab")
            config_names = [c.name for c in gitlab_configs]
            if config_names:
                completions["/git /gitlab /modify"] = config_names
                completions["/git /gitlab /delete"] = config_names
                completions["/git /gitlab /test"] = config_names
        except Exception:
            pass

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

    def handle_git(self, args: str) -> None:
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
            self.handle_github(sub_args)
        elif subcommand == "/gitlab":
            self.handle_gitlab(sub_args)
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
  /git /platform            - 平台切换管理（Phase 4）

详细帮助:
  /git /github /help        - GitHub 配置帮助
  /git /gitlab /help        - GitLab 配置帮助

示例:
  /git /status
  /git /commit "feat: 添加新功能"
  /git /checkout develop
  /git /reset soft HEAD~1
  /git /github /setup       - 配置 GitHub 连接
  /git /gitlab /setup       - 配置 GitLab 连接
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

    def handle_github(self, args: str) -> None:
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
            self._github_setup()
        elif subcmd == "/list":
            self._github_list()
        elif subcmd == "/modify":
            self._github_modify(sub_args)
        elif subcmd == "/delete":
            self._github_delete(sub_args)
        elif subcmd == "/test":
            self._github_test(sub_args)
        else:
            print(f"❌ 未知的子命令: {subcmd}")
            self._show_github_help()

    def _github_setup(self) -> None:
        """GitHub 引导式配置"""
        from prompt_toolkit import prompt
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.prompt import Confirm

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
            name = prompt("   名称: ").strip()
            if not name:
                console.print("[red]❌ 配置名称不能为空[/red]")
                return

            # 检查是否已存在
            if self.platform_manager.get_config("github", name):
                if not Confirm.ask(f"配置 '{name}' 已存在，是否覆盖？", default=False):
                    console.print("[yellow]已取消[/yellow]")
                    return

            # 2. API 地址
            console.print("\n[cyan]2. GitHub API 地址[/cyan]")
            console.print("   [dim]默认：https://api.github.com[/dim]")
            console.print("   [dim]企业版：https://github.example.com/api/v3[/dim]")
            base_url = prompt("   地址 [默认: https://api.github.com]: ").strip()
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
            token = prompt("   Token: ", is_password=True).strip()
            if not token:
                console.print("[red]❌ Token 不能为空[/red]")
                return

            # 4. SSL 验证
            console.print("\n[cyan]4. SSL 验证 (可选)[/cyan]")
            verify_ssl = Confirm.ask("   验证 SSL 证书？", default=True)

            # 5. 超时设置
            console.print("\n[cyan]5. 超时设置 (可选)[/cyan]")
            timeout_str = prompt("   超时时间（秒） [默认: 30]: ").strip()
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

            if not Confirm.ask("是否保存以上配置？", default=True):
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

                # 自动测试连接
                if Confirm.ask("\n是否测试连接？", default=True):
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

    def _github_modify(self, name: str) -> None:
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
        from prompt_toolkit import prompt
        from rich.prompt import Confirm

        # API 地址
        new_url = prompt(f"API 地址 [{config.base_url}]: ").strip()
        if new_url:
            config.base_url = new_url

        # Token
        change_token = Confirm.ask("是否更换 Token？", default=False)
        if change_token:
            new_token = prompt("新 Token: ", is_password=True).strip()
            if new_token:
                config.token = new_token

        # SSL 验证
        config.verify_ssl = Confirm.ask(
            f"验证 SSL？",
            default=config.verify_ssl
        )

        # 超时
        new_timeout = prompt(f"超时时间（秒） [{config.timeout}]: ").strip()
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

    def _github_delete(self, name: str) -> None:
        """删除 GitHub 配置"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /github /delete <配置名>")
            return

        from rich.console import Console
        from rich.prompt import Confirm

        console = Console()

        if not self.platform_manager.get_config("github", name):
            console.print(f"\n[red]❌ 配置不存在: {name}[/red]\n")
            return

        if Confirm.ask(f"确认删除配置 '{name}'？", default=False):
            if self.platform_manager.delete_config("github", name):
                console.print(f"\n[green]✅ 已删除配置: {name}[/green]\n")
            else:
                console.print(f"\n[red]❌ 删除失败[/red]\n")
        else:
            console.print("\n[yellow]已取消[/yellow]\n")

    def _github_test(self, name: str) -> None:
        """测试 GitHub 连接"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /github /test <配置名>")
            return

        config = self.platform_manager.get_config("github", name)
        if not config:
            print(f"❌ 配置不存在: {name}")
            return

        from rich.console import Console
        from rich.status import Status
        import requests

        console = Console()

        with Status("[cyan]正在测试连接...", console=console):
            try:
                # 测试 GitHub API
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
                    user_data = response.json()
                    username = user_data.get("login", "unknown")

                    # 更新测试时间
                    config.update_last_tested()
                    self.platform_manager.save_configs()

                    console.print(f"\n[green]✅ 连接成功！[/green]")
                    console.print(f"   用户: {username}")
                    console.print(f"   API: {config.base_url}\n")
                else:
                    console.print(f"\n[red]❌ 连接失败[/red]")
                    console.print(f"   状态码: {response.status_code}")
                    console.print(f"   响应: {response.text[:200]}\n")

            except requests.exceptions.Timeout:
                console.print(f"\n[red]❌ 连接超时[/red]")
                console.print(f"   超时时间: {config.timeout}秒\n")
            except requests.exceptions.SSLError:
                console.print(f"\n[red]❌ SSL 证书验证失败[/red]")
                console.print(f"   如果是自签名证书，可以关闭 SSL 验证\n")
            except Exception as e:
                console.print(f"\n[red]❌ 测试失败: {e}[/red]\n")

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

    def handle_gitlab(self, args: str) -> None:
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
            self._gitlab_setup()
        elif subcmd == "/list":
            self._gitlab_list()
        elif subcmd == "/modify":
            self._gitlab_modify(sub_args)
        elif subcmd == "/delete":
            self._gitlab_delete(sub_args)
        elif subcmd == "/test":
            self._gitlab_test(sub_args)
        else:
            print(f"❌ 未知的子命令: {subcmd}")
            self._show_gitlab_help()

    def _gitlab_setup(self) -> None:
        """GitLab 引导式配置"""
        from prompt_toolkit import prompt
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.prompt import Confirm

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
            name = prompt("   名称: ").strip()
            if not name:
                console.print("[red]❌ 配置名称不能为空[/red]")
                return

            if self.platform_manager.get_config("gitlab", name):
                if not Confirm.ask(f"配置 '{name}' 已存在，是否覆盖？", default=False):
                    console.print("[yellow]已取消[/yellow]")
                    return

            # 2. GitLab 地址
            console.print("\n[cyan]2. GitLab 地址[/cyan]")
            console.print("   [dim]公网 GitLab: https://gitlab.com[/dim]")
            console.print("   [dim]私有部署: https://gitlab.example.com[/dim]")
            base_url_input = prompt("   地址: ").strip()

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
            token = prompt("   Token: ", is_password=True).strip()
            if not token:
                console.print("[red]❌ Token 不能为空[/red]")
                return

            # 4. SSL 验证（私有部署可能需要禁用）
            console.print("\n[cyan]4. SSL 验证 (可选)[/cyan]")
            console.print("   [dim]内网私有部署可能需要选择 'n'[/dim]")
            verify_ssl = Confirm.ask("   验证 SSL 证书？", default=True)

            # 5. 超时设置
            console.print("\n[cyan]5. 超时设置 (可选)[/cyan]")
            timeout_str = prompt("   超时时间（秒） [默认: 30]: ").strip()
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

            if not Confirm.ask("是否保存以上配置？", default=True):
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

                # 自动测试连接
                if Confirm.ask("\n是否测试连接？", default=True):
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

    def _gitlab_modify(self, name: str) -> None:
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
        from prompt_toolkit import prompt
        from rich.prompt import Confirm

        # API 地址
        new_url = prompt(f"API 地址 [{config.base_url}]: ").strip()
        if new_url:
            config.base_url = new_url

        # Token
        change_token = Confirm.ask("是否更换 Token？", default=False)
        if change_token:
            new_token = prompt("新 Token: ", is_password=True).strip()
            if new_token:
                config.token = new_token

        # SSL 验证
        config.verify_ssl = Confirm.ask(
            f"验证 SSL？",
            default=config.verify_ssl
        )

        # 超时
        new_timeout = prompt(f"超时时间（秒） [{config.timeout}]: ").strip()
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

    def _gitlab_delete(self, name: str) -> None:
        """删除 GitLab 配置"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /gitlab /delete <配置名>")
            return

        from rich.console import Console
        from rich.prompt import Confirm

        console = Console()

        if not self.platform_manager.get_config("gitlab", name):
            console.print(f"\n[red]❌ 配置不存在: {name}[/red]\n")
            return

        if Confirm.ask(f"确认删除配置 '{name}'？", default=False):
            if self.platform_manager.delete_config("gitlab", name):
                console.print(f"\n[green]✅ 已删除配置: {name}[/green]\n")
            else:
                console.print(f"\n[red]❌ 删除失败[/red]\n")
        else:
            console.print("\n[yellow]已取消[/yellow]\n")

    def _gitlab_test(self, name: str) -> None:
        """测试 GitLab 连接"""
        name = name.strip()
        if not name:
            print("❌ 请指定配置名称")
            print("用法: /git /gitlab /test <配置名>")
            return

        config = self.platform_manager.get_config("gitlab", name)
        if not config:
            print(f"❌ 配置不存在: {name}")
            return

        from rich.console import Console
        from rich.status import Status
        import requests

        console = Console()

        with Status("[cyan]正在测试连接...", console=console):
            try:
                # 测试 GitLab API
                headers = {
                    "PRIVATE-TOKEN": config.token,
                    "Accept": "application/json"
                }

                response = requests.get(
                    f"{config.base_url}/user",
                    headers=headers,
                    verify=config.verify_ssl,
                    timeout=config.timeout
                )

                if response.status_code == 200:
                    user_data = response.json()
                    username = user_data.get("username", "unknown")

                    # 更新测试时间
                    config.update_last_tested()
                    self.platform_manager.save_configs()

                    console.print(f"\n[green]✅ 连接成功！[/green]")
                    console.print(f"   用户: {username}")
                    console.print(f"   API: {config.base_url}\n")
                else:
                    console.print(f"\n[red]❌ 连接失败[/red]")
                    console.print(f"   状态码: {response.status_code}")
                    console.print(f"   响应: {response.text[:200]}\n")

            except requests.exceptions.Timeout:
                console.print(f"\n[red]❌ 连接超时[/red]")
                console.print(f"   超时时间: {config.timeout}秒\n")
            except requests.exceptions.SSLError:
                console.print(f"\n[red]❌ SSL 证书验证失败[/red]")
                console.print(f"   如果是自签名证书，可以关闭 SSL 验证\n")
            except Exception as e:
                console.print(f"\n[red]❌ 测试失败: {e}[/red]\n")

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
