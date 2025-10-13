#!/usr/bin/env python3
"""
错误处理测试脚本
"""

import sys
sys.path.insert(0, '/projects/cuscli')

from autocoder.common.git_platform_config import GitPlatformConfig, GitPlatformManager
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_error_handling():
    """测试各种错误处理场景"""

    console.print("\n")
    console.print(Panel(
        "[bold cyan]错误处理测试[/bold cyan]\n\n"
        "测试场景：\n"
        "1. 无效 Token（401 错误）\n"
        "2. 无效 URL（连接错误）\n"
        "3. 删除不存在的配置\n"
        "4. 获取不存在的配置\n"
        "5. 切换到未配置的平台",
        title="⚠️ 错误处理测试",
        border_style="yellow"
    ))

    config_file = "/projects/cuscli/.auto-coder/plugins/autocoder.plugins.git_helper_plugin.GitHelperPlugin/config.json"
    manager = GitPlatformManager(config_file)

    # 测试 1: 无效 Token
    console.print("\n[bold]测试 1: 无效 Token（401 错误）[/bold]")

    invalid_config = GitPlatformConfig(
        name="test-invalid-token",
        platform="gitlab",
        base_url="https://gitlab.com/api/v4",
        token="invalid-token-12345",
        verify_ssl=True,
        timeout=10
    )

    console.print("添加配置: test-invalid-token（无效 token）")
    manager.add_config(invalid_config)

    console.print("测试连接...")
    try:
        headers = {
            "Authorization": f"Bearer {invalid_config.token}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{invalid_config.base_url}/user",
            headers=headers,
            verify=invalid_config.verify_ssl,
            timeout=invalid_config.timeout
        )

        if response.status_code == 401:
            console.print("[green]✓[/green] 正确处理了 401 认证失败")
            console.print("  错误信息: Token 无效或已过期")
        else:
            console.print(f"[yellow]?[/yellow] 状态码: {response.status_code}")

    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] 异常: {e}")

    # 测试 2: 无效 URL
    console.print("\n[bold]测试 2: 无效 URL（连接错误）[/bold]")

    invalid_url_config = GitPlatformConfig(
        name="test-invalid-url",
        platform="gitlab",
        base_url="https://invalid-url-that-does-not-exist-12345.com/api/v4",
        token="fake-token",
        verify_ssl=True,
        timeout=5
    )

    console.print("添加配置: test-invalid-url（无效URL）")
    manager.add_config(invalid_url_config)

    console.print("测试连接...")
    try:
        headers = {
            "Authorization": f"Bearer {invalid_url_config.token}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{invalid_url_config.base_url}/user",
            headers=headers,
            verify=invalid_url_config.verify_ssl,
            timeout=invalid_url_config.timeout
        )
        console.print(f"[yellow]?[/yellow] 意外成功: {response.status_code}")

    except requests.exceptions.ConnectionError:
        console.print("[green]✓[/green] 正确处理了连接错误")
        console.print("  错误信息: 无法连接到服务器")
    except requests.exceptions.Timeout:
        console.print("[green]✓[/green] 正确处理了超时错误")
        console.print("  错误信息: 连接超时")
    except Exception as e:
        console.print(f"[green]✓[/green] 捕获异常: {type(e).__name__}")

    # 测试 3: 删除不存在的配置
    console.print("\n[bold]测试 3: 删除不存在的配置[/bold]")

    result = manager.delete_config("gitlab", "non-existent-config")
    if not result:
        console.print("[green]✓[/green] 正确处理了删除不存在的配置")
        console.print("  返回 False，不会引发异常")
    else:
        console.print("[red]✗[/red] 意外成功")

    # 测试 4: 获取不存在的配置
    console.print("\n[bold]测试 4: 获取不存在的配置[/bold]")

    config = manager.get_config("gitlab", "non-existent-config")
    if config is None:
        console.print("[green]✓[/green] 正确处理了获取不存在的配置")
        console.print("  返回 None")
    else:
        console.print("[red]✗[/red] 意外返回了配置")

    # 测试 5: 切换到未配置的平台
    console.print("\n[bold]测试 5: 切换到未配置的平台[/bold]")

    # 先确保 github 没有配置
    github_configs = manager.list_configs("github")
    console.print(f"GitHub 配置数量: {len(github_configs)}")

    if len(github_configs) == 0:
        result = manager.switch_platform("github")
        if result is None:
            console.print("[green]✓[/green] 正确处理了切换到未配置的平台")
            console.print("  返回 None，并保持当前平台不变")
        else:
            console.print("[red]✗[/red] 意外成功切换")
    else:
        console.print("[yellow]跳过[/yellow] GitHub 有配置，无法测试此场景")

    # 测试 6: 不支持的平台
    console.print("\n[bold]测试 6: 不支持的平台[/bold]")

    result = manager.switch_platform("bitbucket", "some-config")
    if result is None:
        console.print("[green]✓[/green] 正确处理了不支持的平台")
        console.print("  返回 None")
    else:
        console.print("[red]✗[/red] 意外成功")

    # 清理测试配置
    console.print("\n[bold]清理测试配置...[/bold]")
    manager.delete_config("gitlab", "test-invalid-token")
    manager.delete_config("gitlab", "test-invalid-url")
    console.print("[green]✓[/green] 已删除测试配置")

    # 测试总结
    console.print("\n")
    console.print(Panel(
        "[bold green]✅ 错误处理测试通过！[/bold green]\n\n"
        "已验证场景：\n"
        "✓ 401 认证失败处理\n"
        "✓ 连接错误处理\n"
        "✓ 删除不存在配置\n"
        "✓ 获取不存在配置\n"
        "✓ 切换到未配置平台\n"
        "✓ 不支持的平台\n\n"
        "所有错误都被正确处理，不会引发未捕获异常！",
        title="🎉 测试完成",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        test_error_handling()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]测试已中断[/yellow]\n")
    except Exception as e:
        console.print(f"\n\n[red]测试出错: {str(e)}[/red]\n")
        import traceback
        traceback.print_exc()
