# Phase 5: 连接测试功能实现

## 🎯 阶段目标

实现 GitHub 和 GitLab 的连接测试功能，验证配置的有效性。

## 📋 前置条件

- ✅ Phase 1-4 已完成
- ✅ 已配置至少一个平台

## 🔧 实施步骤

### 步骤 1: 实现 GitHub 连接测试

在 `GitHelperPlugin` 类中添加：

```python
def _github_test(self, name: str) -> None:
    """测试 GitHub 连接"""
    import requests
    from rich.console import Console
    from rich.spinner import Spinner

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
```

---

### 步骤 2: 实现 GitLab 连接测试

```python
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

            response = requests.get(
                f"{config.base_url}/user",
                headers=headers,
                verify=config.verify_ssl,
                timeout=config.timeout
            )

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

            elif response.status_code == 401:
                console.print("[red]❌ 认证失败[/red]")
                console.print("   Token 无效或已过期\n")

            elif response.status_code == 403:
                console.print("[red]❌ 访问被拒绝[/red]")
                console.print("   Token 权限不足\n")

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
```

---

### 步骤 3: 添加依赖

确保 `requests` 库已安装（通常已包含在项目依赖中）。

如果需要，在项目的依赖文件中添加：
```
requests>=2.28.0
```

---

## 🧪 测试要点

### GitHub 连接测试

1. **有效 Token 测试**
   ```bash
   /git /github /setup
   # 输入真实的 GitHub Token
   /git /github /test <配置名>
   ```
   预期：显示用户信息，连接成功

2. **无效 Token 测试**
   ```bash
   /git /github /setup
   # 输入: token: fake-invalid-token
   /git /github /test <配置名>
   ```
   预期：显示 401 认证失败

3. **SSL 错误测试**
   - 使用无效的 HTTPS 地址
   - 预期：显示 SSL 错误和修复建议

4. **超时测试**
   - 修改配置，设置超时为 1 秒
   - 使用慢速网络或无效地址
   - 预期：显示超时错误

### GitLab 连接测试

1. **公网 GitLab 测试**
   ```bash
   /git /gitlab /setup
   # 地址: https://gitlab.com
   # Token: (真实 token)
   /git /gitlab /test <配置名>
   ```
   预期：显示用户信息和 GitLab 版本

2. **私有 GitLab 模拟**
   ```bash
   /git /gitlab /setup
   # 地址: https://invalid-gitlab.example.com
   # Token: fake-token
   # SSL: n
   /git /gitlab /test <配置名>
   ```
   预期：连接错误

---

## ✅ 完成标志

- [x] GitHub 连接测试正常工作
- [x] GitLab 连接测试正常工作
- [x] 成功时显示用户信息
- [x] 失败时显示清晰的错误信息
- [x] SSL 错误有修复建议
- [x] 测试成功后更新 `last_tested` 时间
- [x] 支持进度指示器

---

## 📝 提交代码

```bash
git add autocoder/plugins/git_helper_plugin.py
git commit -m "feat(git-plugin): 实现连接测试功能

- 实现 GitHub 连接测试 (/git /github /test)
- 实现 GitLab 连接测试 (/git /gitlab /test)
- 显示用户信息和版本信息
- 完善错误处理和提示
- 更新最后测试时间
- 添加进度指示器
"
```

---

## 🎉 Phase 5 完成！

➡️ **下一步**: 阅读 `06-phase6-pr-integration.md`，集成 PR 管理模块
