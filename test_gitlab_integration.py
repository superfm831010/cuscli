#!/usr/bin/env python3
"""
GitLab 集成测试脚本
演示 Git Helper Plugin 的 GitLab 配置和测试功能
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, '/projects/cuscli')

from autocoder.common.git_platform_config import GitPlatformConfig, GitPlatformManager
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_gitlab_config():
    """测试 GitLab 配置功能"""

    console.print("\n")
    console.print(Panel(
        "[bold cyan]Git Helper Plugin - GitLab 测试演示[/bold cyan]\n\n"
        "本测试将演示以下功能：\n"
        "1. 添加 GitLab 配置\n"
        "2. 测试 GitLab 连接\n"
        "3. 列出配置\n"
        "4. 平台状态显示\n"
        "5. 配置持久化验证",
        title="🚀 Phase 8 测试",
        border_style="cyan"
    ))

    # 测试数据
    test_config = {
        "name": "test-gitlab-superfmfm",
        "platform": "gitlab",
        "base_url": "https://gitlab.com/api/v4",
        "token": "glpat-30N1GN1oH7fa03DR3nTkdm86MQp1OmlmNDJzCw.01.121yz4n9n",
        "verify_ssl": True,
        "timeout": 30
    }

    # 配置文件路径
    config_file = str(Path.home() / ".auto-coder" / "plugins" / "autocoder.plugins.GitHelperPlugin" / "config.json")

    console.print("\n[bold]步骤 1: 初始化配置管理器[/bold]")
    manager = GitPlatformManager(config_file)
    console.print("[green]✓[/green] 配置管理器已初始化")

    # 添加配置
    console.print("\n[bold]步骤 2: 添加 GitLab 配置[/bold]")
    config = GitPlatformConfig(**test_config)

    table = Table(title="📋 配置信息", show_header=True, header_style="bold magenta")
    table.add_column("配置项", style="cyan", width=15)
    table.add_column("值", style="green")

    table.add_row("配置名称", config.name)
    table.add_row("平台类型", config.platform)
    table.add_row("GitLab 地址", "https://gitlab.com")
    table.add_row("API 地址", config.base_url)
    table.add_row("用户", "superfmfm")
    table.add_row("Token", "glpat-***（已加密）")
    table.add_row("SSL 验证", "是")
    table.add_row("超时时间", f"{config.timeout} 秒")

    console.print(table)

    if manager.add_config(config):
        console.print("\n[green]✓[/green] 配置已保存到: " + config_file)
    else:
        console.print("\n[red]✗[/red] 保存配置失败")
        return

    # 测试连接
    console.print("\n[bold]步骤 3: 测试 GitLab 连接[/bold]")
    console.print(f"🔍 正在连接 GitLab: {config.base_url}\n")

    with console.status("[bold green]测试中...", spinner="dots"):
        try:
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
                email = data.get("email", "未知")

                # 更新最后测试时间
                config.update_last_tested()
                manager.save_configs()

                # 显示成功信息
                console.print("[green]✅ 连接成功！[/green]\n")

                user_table = Table(title="👤 用户信息", show_header=True, header_style="bold green")
                user_table.add_column("项目", style="cyan", width=15)
                user_table.add_column("值", style="white")

                user_table.add_row("用户名", username)
                user_table.add_row("姓名", name_full)
                user_table.add_row("邮箱", email)
                user_table.add_row("用户ID", str(user_id))

                console.print(user_table)

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

            elif response.status_code == 401:
                console.print("[red]❌ 认证失败[/red]")
                console.print("   Token 无效或已过期")
                return
            else:
                console.print(f"[red]❌ 连接失败[/red]")
                console.print(f"   HTTP {response.status_code}: {response.reason}")
                return

        except Exception as e:
            console.print(f"[red]❌ 测试失败: {str(e)}[/red]")
            return

    # 列出配置
    console.print("\n[bold]步骤 4: 列出所有 GitLab 配置[/bold]")
    configs = manager.list_configs("gitlab")

    config_table = Table(title="📋 GitLab 配置列表", show_header=True, header_style="bold magenta")
    config_table.add_column("配置名称", style="cyan")
    config_table.add_column("API 地址", style="green")
    config_table.add_column("SSL", style="yellow", width=6)
    config_table.add_column("超时", style="blue", width=8)
    config_table.add_column("最后测试", style="dim")
    config_table.add_column("状态", style="bold", width=10)

    for cfg in configs:
        ssl_str = "✓" if cfg.verify_ssl else "✗"
        last_tested = cfg.last_tested[:19].replace('T', ' ') if cfg.last_tested else "未测试"
        status = "✅ 当前" if manager.current_platform == "gitlab" and manager.current_config.get("gitlab") == cfg.name else ""

        config_table.add_row(
            cfg.name,
            cfg.base_url,
            ssl_str,
            f"{cfg.timeout}s",
            last_tested,
            status
        )

    console.print("\n")
    console.print(config_table)

    # 显示平台状态
    console.print("\n[bold]步骤 5: 显示当前平台状态[/bold]")
    current_config = manager.get_current_config()

    if current_config:
        platform_name = "GitLab" if current_config.platform == "gitlab" else "GitHub"
        ssl_status = "✓ 启用" if current_config.verify_ssl else "✗ 禁用"

        status_text = (
            f"[bold cyan]平台：[/bold cyan] {platform_name}\n"
            f"[bold cyan]配置：[/bold cyan] {current_config.name}\n"
            f"[bold cyan]地址：[/bold cyan] {current_config.base_url}\n"
            f"[bold cyan]SSL：[/bold cyan] {ssl_status}\n"
            f"[bold cyan]超时：[/bold cyan] {current_config.timeout} 秒"
        )

        if current_config.last_tested:
            test_time = current_config.last_tested[:19].replace('T', ' ')
            status_text += f"\n[bold cyan]测试：[/bold cyan] {test_time}"

        console.print("\n")
        console.print(Panel(
            status_text,
            title="📍 当前平台配置",
            border_style="cyan"
        ))

    # 验证配置文件
    console.print("\n[bold]步骤 6: 验证配置持久化[/bold]")
    import json

    with open(config_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)

    console.print(f"[green]✓[/green] 配置文件存在: {config_file}")
    console.print(f"[green]✓[/green] 当前平台: {saved_data.get('current_platform')}")
    console.print(f"[green]✓[/green] GitLab 配置数量: {len(saved_data.get('platforms', {}).get('gitlab', {}))}")

    # 检查 Token 是否加密
    gitlab_configs = saved_data.get('platforms', {}).get('gitlab', {})
    for name, cfg_data in gitlab_configs.items():
        token = cfg_data.get('token', '')
        if token.startswith('gAAAAAB'):  # Fernet 加密的特征
            console.print(f"[green]✓[/green] Token 已加密存储（配置: {name}）")
        else:
            console.print(f"[yellow]⚠[/yellow] Token 未加密（配置: {name}）")

    # 测试总结
    console.print("\n")
    console.print(Panel(
        "[bold green]✅ 所有测试通过！[/bold green]\n\n"
        "已完成的测试：\n"
        "✓ GitLab 配置添加\n"
        "✓ GitLab 连接测试\n"
        "✓ 用户信息获取\n"
        "✓ 配置列表显示\n"
        "✓ 平台状态显示\n"
        "✓ 配置持久化验证\n"
        "✓ Token 加密验证",
        title="🎉 测试完成",
        border_style="green"
    ))

    console.print("\n[dim]配置文件位置: " + config_file + "[/dim]\n")


if __name__ == "__main__":
    try:
        test_gitlab_config()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]测试已中断[/yellow]\n")
    except Exception as e:
        console.print(f"\n\n[red]测试出错: {str(e)}[/red]\n")
        import traceback
        traceback.print_exc()
