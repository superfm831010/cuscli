# Phase 3: GitLab 配置管理实现

## 🎯 阶段目标

实现 GitLab 配置管理功能，支持公网和私有部署的 GitLab 实例。

## 📋 前置条件

- ✅ Phase 1 已完成
- ✅ Phase 2 已完成（GitHub 配置管理）

## 🔧 实施步骤

### 核心实现

**文件：** `autocoder/plugins/git_helper_plugin.py`

GitLab 的实现与 GitHub 非常相似，可以复用大部分代码结构。

### 步骤 1: 添加命令路由

在 `handle_git` 方法中添加：

```python
elif subcommand == "/gitlab":
    self.handle_gitlab(sub_args)
```

### 步骤 2: 实现 GitLab 命令处理

```python
def handle_gitlab(self, args: str) -> None:
    """处理 /git /gitlab 命令"""
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
```

### 步骤 3: 实现 GitLab 引导式配置

**关键差异：GitLab 的默认 API 地址和 Token 获取方式**

```python
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
```

### 步骤 4: 实现列表、修改、删除

**这些方法与 GitHub 版本几乎相同，只需将 "github" 替换为 "gitlab"：**

```python
def _gitlab_list(self) -> None:
    """列出所有 GitLab 配置"""
    # 复制 _github_list 的实现，将 "github" 替换为 "gitlab"
    # 将 "GitHub" 替换为 "GitLab"
    # 其他逻辑保持不变


def _gitlab_modify(self, name: str) -> None:
    """修改 GitLab 配置"""
    # 复制 _github_modify 的实现，将 "github" 替换为 "gitlab"


def _gitlab_delete(self, name: str) -> None:
    """删除 GitLab 配置"""
    # 复制 _github_delete 的实现，将 "github" 替换为 "gitlab"


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
```

**提示：** 可以考虑重构，提取通用方法避免代码重复，但为了简单起见，Phase 3 可以先复制实现。

---

## 🧪 测试要点

### 测试准备

您需要：
1. **GitLab 账号**（gitlab.com 或私有实例）
2. **Personal Access Token**
   - 登录 GitLab
   - Settings → Access Tokens
   - 创建 token，勾选 `api` 权限

### 功能测试

1. **公网 GitLab 配置**
   ```bash
   /git /gitlab /setup
   ```
   输入：
   - 名称：personal-gitlab
   - 地址：https://gitlab.com
   - Token：（您的真实 token）
   - SSL：y

2. **私有 GitLab 配置（模拟）**
   ```bash
   /git /gitlab /setup
   ```
   输入：
   - 名称：company-gitlab
   - 地址：https://gitlab.example.com
   - Token：fake-token-for-testing
   - SSL：n

3. **列表显示**
   ```bash
   /git /gitlab /list
   ```

4. **修改和删除**
   ```bash
   /git /gitlab /modify company-gitlab
   /git /gitlab /delete company-gitlab
   ```

---

## ✅ 完成标志

- [x] `/git /gitlab /setup` 可以正常配置
- [x] 支持自动添加 `/api/v4` 路径
- [x] SSL 验证选项正常工作
- [x] `/git /gitlab /list` 显示正常
- [x] `/git /gitlab /modify` 和 `/delete` 正常工作
- [x] 配置正确保存到文件

---

## 📝 提交代码

```bash
git add autocoder/plugins/git_helper_plugin.py
git commit -m "feat(git-plugin): 实现 GitLab 配置管理功能

- 添加 /git /gitlab 命令组
- 实现引导式 GitLab 配置
- 支持公网和私有部署
- 自动添加 /api/v4 API 路径
- 支持 SSL 验证开关
"
```

---

## 🎉 Phase 3 完成！

➡️ **下一步**: 阅读 `04-phase4-platform-switch.md`，实现平台切换功能
