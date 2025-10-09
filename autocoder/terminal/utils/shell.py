"""Shell 相关工具函数"""

import platform
import subprocess
import asyncio


def get_shell() -> str:
    """获取当前系统的默认 shell"""
    return "/bin/bash" if platform.system() != "Windows" else "cmd.exe"


async def run_shell_command_async(command: str, session=None) -> bool:
    """异步运行 shell 命令

    Args:
        command: 要执行的命令
        session: PromptSession 对象，如果提供则使用其 app.run_system_command

    Returns:
        bool: 是否成功执行
    """
    shell = get_shell()

    if session and hasattr(session, "app"):
        try:
            await session.app.run_system_command(command, wait_for_enter=False)
            return True
        except Exception:
            # 如果异步调用失败，回退到同步方式
            pass

    # 回退到同步方式
    try:
        if command == shell:
            # 直接启动 shell
            subprocess.call([shell])
        else:
            # 执行命令
            subprocess.call([shell, "-c", command])
        return True
    except Exception:
        return False
