"""
交互式引导用户配置第一个模型
"""

from autocoder.common.async_prompt import prompt
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
from typing import Optional, Dict
from .manager import LLMManager
from .connection_test import ModelConnectionTester, DEFAULT_API_KEY


def guide_first_model_setup() -> Optional[str]:
    """
    引导用户配置第一个模型的交互式流程

    Returns:
        Optional[str]: 成功时返回模型名称，失败或取消时返回 None
    """
    console = Console()

    # 显示欢迎信息
    console.print("\n")
    console.print(Panel(
        "[bold cyan]首次模型配置引导[/bold cyan]\n\n"
        "未检测到任何模型配置，让我们配置第一个模型。\n\n"
        "[yellow]提示：[/yellow] 配置的模型信息将保存在 [green]~/.auto-coder/keys/models.json[/green]",
        title="🚀 欢迎",
        border_style="cyan"
    ))

    try:
        # 收集模型信息
        model_config = _prompt_model_info(console)

        if not model_config:
            console.print("[yellow]配置已取消[/yellow]")
            return None

        # 确认信息
        if not _confirm_model_config(console, model_config):
            console.print("[yellow]配置已取消[/yellow]")
            return None

        # 测试连接
        test_result = _test_model_connection(console, model_config)
        if test_result == "cancel":
            console.print("[yellow]配置已取消[/yellow]")
            return None
        elif test_result == "retry":
            # 用户选择重新配置
            console.print("\n[cyan]请重新输入配置信息[/cyan]")
            return guide_first_model_setup()

        # 保存配置
        success = _save_model_config(console, model_config)

        if success:
            console.print("\n")
            console.print(Panel(
                f"[bold green]✓[/bold green] 模型 [bold]{model_config['name']}[/bold] 配置成功！\n\n"
                "你现在可以使用以下命令查看已配置的模型：\n"
                "[cyan]/models[/cyan]",
                title="✅ 配置成功",
                border_style="green"
            ))
            return model_config['name']
        else:
            console.print("[red]配置保存失败[/red]")
            return None

    except KeyboardInterrupt:
        console.print("\n[yellow]配置已取消[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n[red]配置过程出错: {str(e)}[/red]")
        return None


def _prompt_model_info(console: Console) -> Optional[Dict]:
    """
    交互式收集模型信息

    Args:
        console: Rich Console 对象

    Returns:
        模型配置字典，如果用户取消则返回 None
    """
    console.print("\n[bold]请输入模型配置信息：[/bold]\n")

    # 模型显示名称
    console.print("[cyan]1. 模型显示名称[/cyan] (例如: my-model, deepseek-chat)")
    name = prompt("   名称: ").strip()
    if not name:
        console.print("[red]错误: 模型名称不能为空[/red]")
        return None

    # API 地址
    console.print("\n[cyan]2. 模型API地址[/cyan] (例如: https://api.openai.com/v1)")
    base_url = prompt("   地址: ").strip()
    if not base_url:
        console.print("[red]错误: API地址不能为空[/red]")
        return None

    # 模型实际名称
    console.print("\n[cyan]3. 模型实际名称[/cyan] (例如: gpt-4, deepseek-chat)")
    model_name = prompt("   名称: ").strip()
    if not model_name:
        console.print("[red]错误: 模型实际名称不能为空[/red]")
        return None

    # API Key (可选)
    console.print("\n[cyan]4. API Key[/cyan] (可选，留空将使用默认值)")
    console.print("   [dim]提示：如果接口不需要Key，可以直接留空[/dim]")
    console.print("   [dim]API Key 将加密保存到 ~/.auto-coder/keys/ 目录[/dim]")
    api_key = prompt("   Key: ", is_password=True).strip()

    # 如果用户留空，使用默认Key
    if not api_key:
        api_key = DEFAULT_API_KEY
        console.print("   [yellow]未输入Key，将使用默认值（适用于不需要Key的接口）[/yellow]")

    # 构建模型配置
    model_config = {
        "name": name,
        "description": f"User configured model: {name}",
        "model_name": model_name,
        "model_type": "saas/openai",  # 默认使用 OpenAI 兼容格式
        "base_url": base_url,
        "provider": "custom",
        "api_key": api_key if api_key else None,
        "is_reasoning": False,
        "input_price": 0.0,
        "output_price": 0.0,
        "max_output_tokens": 8096,
        "context_window": 128000
    }

    return model_config


def _confirm_model_config(console: Console, model_config: Dict) -> bool:
    """
    确认模型配置信息

    Args:
        console: Rich Console 对象
        model_config: 模型配置字典

    Returns:
        bool: 用户是否确认
    """
    console.print("\n")

    # 创建表格显示配置信息
    table = Table(title="📋 确认配置信息", show_header=True, header_style="bold magenta")
    table.add_column("配置项", style="cyan", width=20)
    table.add_column("值", style="green")

    table.add_row("显示名称", model_config["name"])
    table.add_row("API地址", model_config["base_url"])
    table.add_row("模型名称", model_config["model_name"])
    table.add_row("模型类型", model_config["model_type"])

    if model_config.get("api_key"):
        if model_config["api_key"] == DEFAULT_API_KEY:
            table.add_row("API Key", "[yellow]（不需要Key）[/yellow]")
        else:
            table.add_row("API Key", "******（已设置）")
    else:
        table.add_row("API Key", "[dim]（未设置）[/dim]")

    console.print(table)
    console.print()

    return Confirm.ask("是否保存以上配置？", default=True)


def _test_model_connection(console: Console, model_config: Dict) -> str:
    """
    测试模型连接

    Args:
        console: Rich Console 对象
        model_config: 模型配置字典

    Returns:
        str: 测试结果 ("success", "skip", "retry", "cancel")
    """
    console.print("\n")
    console.print(Panel(
        "[bold cyan]步骤 3/3: 测试模型连接[/bold cyan]\n\n"
        "即将测试模型连接，确保配置正确...",
        border_style="cyan"
    ))

    # 如果没有 API Key 或使用默认Key，提示跳过测试
    if not model_config.get("api_key") or model_config.get("api_key") == DEFAULT_API_KEY:
        console.print("[yellow]⚠️  未配置 API Key 或使用默认Key，跳过连接测试[/yellow]")
        return "success"

    # 执行连接测试
    tester = ModelConnectionTester(console)
    success, message = tester.test_connection(model_config, product_mode="lite", show_progress=True)

    console.print()

    if success:
        # 测试成功
        console.print(Panel(
            f"[bold green]✓ 连接测试成功！[/bold green]\n\n{message}",
            border_style="green",
            title="测试通过"
        ))
        return "success"
    else:
        # 测试失败
        console.print(Panel(
            f"[bold red]✗ 连接测试失败[/bold red]\n\n[yellow]错误信息：[/yellow]\n{message}\n\n"
            "[dim]可能的原因：[/dim]\n"
            "  • API Key 不正确\n"
            "  • API 地址错误\n"
            "  • 模型名称不存在\n"
            "  • 网络连接问题",
            border_style="red",
            title="测试失败"
        ))

        # 询问用户如何处理
        console.print("\n[bold]请选择下一步操作：[/bold]")
        console.print("  [cyan]1[/cyan] - 重新配置")
        console.print("  [cyan]2[/cyan] - 忽略测试，继续保存")
        console.print("  [cyan]3[/cyan] - 取消配置")

        choice = Prompt.ask(
            "你的选择",
            choices=["1", "2", "3"],
            default="1"
        )

        if choice == "1":
            return "retry"
        elif choice == "2":
            console.print("[yellow]⚠️  已忽略连接测试，继续保存配置[/yellow]")
            return "success"
        else:
            return "cancel"


def _save_model_config(console: Console, model_config: Dict) -> bool:
    """
    保存模型配置

    Args:
        console: Rich Console 对象
        model_config: 模型配置字典

    Returns:
        bool: 是否成功保存
    """
    try:
        llm_manager = LLMManager()

        # 添加模型
        llm_manager.add_models([model_config])

        return True

    except Exception as e:
        console.print(f"[red]保存配置时出错: {str(e)}[/red]")
        return False


def guide_add_model() -> Optional[str]:
    """
    引导用户添加新模型的交互式流程（用于 /models /add 命令）

    与 guide_first_model_setup() 类似，但欢迎信息不同

    Returns:
        Optional[str]: 成功时返回模型名称，失败或取消时返回 None
    """
    console = Console()

    # 显示欢迎信息（与首次配置不同）
    console.print("\n")
    console.print(Panel(
        "[bold cyan]添加新模型[/bold cyan]\n\n"
        "配置一个新的模型。\n\n"
        "[yellow]提示：[/yellow] 配置的模型信息将保存在 [green]~/.auto-coder/keys/models.json[/green]",
        title="➕ 添加模型",
        border_style="cyan"
    ))

    try:
        # 收集模型信息
        model_config = _prompt_model_info(console)

        if not model_config:
            console.print("[yellow]配置已取消[/yellow]")
            return None

        # 检查模型名称是否已存在
        llm_manager = LLMManager()
        if llm_manager.check_model_exists(model_config['name']):
            console.print(f"[red]错误: 模型名称 '{model_config['name']}' 已存在[/red]")
            console.print("[yellow]提示: 请使用 /models /list 查看现有模型[/yellow]")
            return None

        # 确认信息
        if not _confirm_model_config(console, model_config):
            console.print("[yellow]配置已取消[/yellow]")
            return None

        # 测试连接
        test_result = _test_model_connection(console, model_config)
        if test_result == "cancel":
            console.print("[yellow]配置已取消[/yellow]")
            return None
        elif test_result == "retry":
            # 用户选择重新配置
            console.print("\n[cyan]请重新输入配置信息[/cyan]")
            return guide_add_model()

        # 保存配置
        success = _save_model_config(console, model_config)

        if success:
            console.print("\n")
            console.print(Panel(
                f"[bold green]✓[/bold green] 模型 [bold]{model_config['name']}[/bold] 添加成功！\n\n"
                "你现在可以使用以下命令：\n"
                f"  [cyan]/models /switch {model_config['name']}[/cyan] - 切换到此模型\n"
                "  [cyan]/models /list[/cyan] - 查看所有模型",
                title="✅ 添加成功",
                border_style="green"
            ))
            return model_config['name']
        else:
            console.print("[red]配置保存失败[/red]")
            return None

    except KeyboardInterrupt:
        console.print("\n[yellow]配置已取消[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n[red]配置过程出错: {str(e)}[/red]")
        return None
