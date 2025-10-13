# Phase 2: GitHub 配置管理实现

## 🎯 阶段目标

在 Git Helper 插件中实现 GitHub 配置的完整管理功能。

## 📋 前置条件

- ✅ Phase 1 已完成（配置管理框架已搭建）
- ✅ 测试通过 `test_git_platform_config.py`

## 🔧 实施步骤

### 步骤 1: 扩展 GitHelperPlugin 初始化

**文件：** `autocoder/plugins/git_helper_plugin.py`

在类的 `__init__` 方法中添加平台配置管理器：

```python
def __init__(self, manager: PluginManager, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
    """Initialize the Git helper plugin."""
    super().__init__(manager, config, config_path)

    self.git_available = self._check_git_available()
    self.default_branch = self.config.get("default_branch", "main")

    # 新增：初始化平台配置管理器
    from autocoder.common.git_platform_config import GitPlatformManager
    self.platform_manager = GitPlatformManager(self.config_path)
```

---

### 步骤 2: 注册 GitHub 命令

在 `get_commands()` 方法中添加（保持现有代码不变）：

```python
def get_commands(self) -> Dict[str, Tuple[Callable, str]]:
    """Get commands provided by this plugin."""
    return {
        "git": (self.handle_git, "Git 辅助工具，管理版本控制"),
    }
```

---

### 步骤 3: 扩展命令路由

修改 `handle_git` 方法，添加 `/github` 路由：

```python
def handle_git(self, args: str) -> None:
    """Handle the /git command and route to specific subcommand handlers."""
    args = args.strip()

    if not args:
        self._show_git_help()
        return

    parts = args.split(maxsplit=1)
    subcommand = parts[0]
    sub_args = parts[1] if len(parts) > 1 else ""

    # 现有路由保持不变
    if subcommand == "/status":
        self.git_status(sub_args)
    # ... 其他现有命令 ...

    # 新增：GitHub 配置管理路由
    elif subcommand == "/github":
        self.handle_github(sub_args)

    else:
        print(f"❌ 未知的子命令: {subcommand}")
        self._show_git_help()
```

---

### 步骤 4: 实现 GitHub 配置处理

在 `GitHelperPlugin` 类中添加新方法：

```python
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
```

---

### 步骤 5: 实现引导式配置

```python
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
```

---

### 步骤 6: 实现列表显示

```python
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
```

---

### 步骤 7: 实现修改和删除功能

```python
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
```

---

### 步骤 8: 实现帮助信息

```python
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
```

---

### 步骤 9: 更新主帮助信息

修改 `_show_git_help()` 方法，添加 GitHub 相关帮助：

```python
def _show_git_help(self) -> None:
    """Display help information for git commands."""
    print("""
📋 Git 命令帮助

使用方法:
  /git /status              - 查看仓库状态
  /git /commit <message>    - 提交更改（自动 add .）
  /git /branch [args]       - 分支管理
  ... (现有命令保持不变) ...

  /git /github              - GitHub 配置管理
  /git /gitlab              - GitLab 配置管理（Phase 3）
  /git /platform            - 平台切换管理（Phase 4）

详细帮助:
  /git /github /help        - GitHub 配置帮助
    """)
```

---

## 🧪 测试要点

### 1. 引导式配置测试

```bash
/git /github /setup
```

按照提示输入：
- 配置名称：test-github
- API 地址：(回车使用默认)
- Token：(输入测试 token 或随意输入)
- SSL 验证：y
- 超时：(回车使用默认)

预期：显示确认表格，保存成功

### 2. 列表显示测试

```bash
/git /github /list
```

预期：显示刚才创建的配置

### 3. 修改配置测试

```bash
/git /github /modify test-github
```

修改超时时间为 60

预期：修改成功

### 4. 删除配置测试

```bash
/git /github /delete test-github
```

确认删除

预期：删除成功

---

## ✅ 完成标志

- [x] `/git /github` 命令可以正常路由
- [x] `/git /github /setup` 引导式配置流程完整
- [x] `/git /github /list` 可以显示配置列表
- [x] `/git /github /modify` 可以修改配置
- [x] `/git /github /delete` 可以删除配置
- [x] 所有输入验证和错误处理正常
- [x] 配置文件正确保存和加载

---

## 📝 提交代码

```bash
git add autocoder/plugins/git_helper_plugin.py
git commit -m "feat(git-plugin): 实现 GitHub 配置管理功能

- 添加 /git /github 命令组
- 实现引导式 GitHub 配置 (/setup)
- 实现配置列表显示 (/list)
- 实现配置修改功能 (/modify)
- 实现配置删除功能 (/delete)
- 集成 GitPlatformManager
"
```

---

## 🎉 Phase 2 完成！

➡️ **下一步**: 阅读 `03-phase3-gitlab-config.md`，实现 GitLab 配置管理功能
