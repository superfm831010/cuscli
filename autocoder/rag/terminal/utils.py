"""工具函数模块"""

import hashlib
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from autocoder.rag.utils import process_file_local
from autocoder.rag.token_counter import TokenCounter
from autocoder.version import __version__


def print_banner():
    """打印启动横幅"""
    print(
        f"""
    \033[1;32m
      _     _     __  __       _   _    _  _____ _____     _______   ____      _    ____ 
     | |   | |   |  \/  |     | \ | |  / \|_   _|_ _\ \   / / ____| |  _ \    / \  / ___|
     | |   | |   | |\/| |_____|  \| | / _ \ | |  | | \ \ / /|  _|   | |_) |  / _ \| |  _ 
     | |___| |___| |  | |_____| |\  |/ ___ \| |  | |  \ V / | |___  |  _ <  / ___ \ |_| |
     |_____|_____|_|  |_|     |_| \_/_/   \_\_| |___|  \_/  |_____| |_| \_\/_/   \_\____|
                                                                            v{__version__}
    \033[0m"""
    )


def generate_unique_name_from_path(path: str) -> str:
    """
    从路径生成唯一名称（MD5哈希），在规范化后。
    对于 Linux/Unix 系统，会移除尾部的路径分隔符。
    """
    if not path:
        return ""

    # Normalize the path (resolve absolute path and remove trailing separators)
    normalized_path = os.path.normpath(os.path.abspath(path))

    # Generate MD5 hash from the normalized path
    return hashlib.md5(normalized_path.encode("utf-8")).hexdigest()


def merge_args_with_config(args, config, arg_class, parser):
    """
    合并命令行参数和配置文件参数，优先级如下：
    1. 命令行参数非默认值，以命令行为准
    2. 命令行参数为默认值，且配置文件有值，以配置文件为准
    3. 否则用命令行参数
    """
    merged = {}
    for arg in vars(arg_class()):
        # 获取默认值
        try:
            default = parser.get_default(arg)
        except Exception:
            default = None

        if not hasattr(args, arg) and arg not in config:
            continue

        cli_value = getattr(args, arg, None)
        config_value = config.get(arg, None)

        # 判断优先级
        if cli_value != default:
            merged[arg] = cli_value
        elif config_value is not None:
            merged[arg] = config_value
        else:
            merged[arg] = cli_value

    return arg_class(**merged)


def count_tokens(tokenizer_path: str, file_path: str, output_format: str = "text"):
    """统计文件的 token 数量

    Args:
        tokenizer_path: tokenizer 文件路径
        file_path: 要统计的文件路径
        output_format: 输出格式，"text" 为 rich 表格，"json" 为 JSON 格式
    """
    import json
    from autocoder.rag.variable_holder import VariableHolder
    from tokenizers import Tokenizer

    VariableHolder.TOKENIZER_PATH = tokenizer_path
    VariableHolder.TOKENIZER_MODEL = Tokenizer.from_file(tokenizer_path)
    token_counter = TokenCounter(tokenizer_path)
    source_codes = process_file_local(file_path)

    total_chars = 0
    total_tokens = 0
    files_result = []

    for source_code in source_codes:
        content = source_code.source_code
        chars = len(content)
        tokens = token_counter.count_tokens(content)

        total_chars += chars
        total_tokens += tokens

        files_result.append(
            {
                "file": source_code.module_name,
                "characters": chars,
                "tokens": tokens,
            }
        )

    if output_format == "json":
        result = {
            "files": files_result,
            "totalCharacters": total_chars,
            "totalTokens": total_tokens,
        }
        print(json.dumps(result, ensure_ascii=False))
    else:
        # 默认使用 rich 表格输出
        console = Console()
        table = Table(title="Token Count Results")
        table.add_column("File", style="cyan")
        table.add_column("Characters", justify="right", style="magenta")
        table.add_column("Tokens", justify="right", style="green")

        for file_info in files_result:
            table.add_row(
                file_info["file"],
                str(file_info["characters"]),
                str(file_info["tokens"]),
            )

        table.add_row("Total", str(total_chars), str(total_tokens), style="bold")

        console.print(table)
