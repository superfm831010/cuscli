"""
交互式引导用户配置第一个模型
"""

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from typing import Optional, Dict
from .manager import LLMManager


def guide_first_model_setup() -> bool:
    """
    引导用户配置第一个模型的交互式流程

    Returns:
        bool: 是否成功配置模型
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
            return False

        # 确认信息
        if not _confirm_model_config(console, model_config):
            console.print("[yellow]配置已取消[/yellow]")
            return False

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
            return True
        else:
            console.print("[red]配置保存失败[/red]")
            return False

    except KeyboardInterrupt:
        console.print("\n[yellow]配置已取消[/yellow]")
        return False
    except Exception as e:
        console.print(f"\n[red]配置过程出错: {str(e)}[/red]")
        return False


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
    console.print("\n[cyan]4. API Key[/cyan] (可选，留空跳过)")
    console.print("   [dim]提示：API Key 将加密保存到 ~/.auto-coder/keys/ 目录[/dim]")
    api_key = prompt("   Key: ", is_password=True).strip()

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
        table.add_row("API Key", "******（已设置）")
    else:
        table.add_row("API Key", "[dim]（未设置）[/dim]")

    console.print(table)
    console.print()

    return Confirm.ask("是否保存以上配置？", default=True)


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
