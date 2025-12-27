"""引导模块 - RAG 系统的主入口"""

import platform
from autocoder.rag.terminal.args import parse_arguments
from autocoder.rag.terminal.init import initialize_system
from autocoder.rag.terminal.utils import print_banner
from autocoder.rag.terminal.command_handlers import (
    handle_benchmark_command,
    handle_serve_command,
    handle_build_hybrid_index_command,
    handle_tools_command,
    handle_run_command,
)
import importlib.resources as resources


def load_tokenizer():
    from autocoder.rag.variable_holder import VariableHolder
    from tokenizers import Tokenizer

    try:
        tokenizer_path = str(resources.files("autocoder") / "data" / "tokenizer.json")
        VariableHolder.TOKENIZER_PATH = tokenizer_path
        VariableHolder.TOKENIZER_MODEL = Tokenizer.from_file(tokenizer_path)
    except FileNotFoundError:
        tokenizer_path = None


if platform.system() == "Windows":
    from colorama import init

    init()


def run_cli(input_args=None):
    """CLI 入口函数"""
    # 打印启动横幅
    load_tokenizer()

    # 解析参数
    args, parser, subparsers = parse_arguments(input_args)

    # 根据命令执行对应的处理逻辑
    if args.command == "benchmark":
        handle_benchmark_command(args)
    elif args.command == "serve":
        print_banner()
        # 处理 lite/pro 模式（需要在 initialize_system 之前设置 product_mode）
        if hasattr(args, "lite") and args.lite:
            args.product_mode = "lite"
        elif hasattr(args, "pro") and args.pro:
            args.product_mode = "pro"
        # 初始化系统（如果不是 quick 模式）
        if not args.quick:
            initialize_system(args)
        # 传递 serve 子命令的 parser，用于 merge_args_with_config 获取默认值
        serve_parser = subparsers.get("serve")
        handle_serve_command(args, serve_parser)
    elif args.command == "run":
        # run 命令直接执行查询，不需要系统初始化
        handle_run_command(args)
    elif args.command == "build_hybrid_index":
        handle_build_hybrid_index_command(args)
    elif args.command == "tools":
        handle_tools_command(args)
    else:
        parser.print_help()
