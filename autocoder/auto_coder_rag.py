import logging
logging.getLogger("ppocr").setLevel(logging.WARNING)

import argparse
from typing import Optional, List
import byzerllm
from autocoder.rag.api_server import serve, ServerArgs
from autocoder.rag.rag_entry import RAGFactory
from autocoder.rag.agentic_rag import AgenticRAG
from autocoder.rag.long_context_rag import LongContextRAG
from autocoder.rag.llm_wrapper import LLWrapper
from autocoder.common import AutoCoderArgs
from autocoder.lang import lang_desc
import locale
from autocoder.chat_auto_coder_lang import get_message
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.formatted_text import HTML
import platform
import subprocess
import shlex
from rich.console import Console
from rich.table import Table
import os
import hashlib
from loguru import logger
import sys
import asyncio
from datetime import datetime
from autocoder.common.file_monitor.monitor import FileMonitor
from autocoder.common.rulefiles import get_rules

from autocoder.rag.utils import process_file_local
import importlib.resources as resources
from autocoder.rag.token_counter import TokenCounter
from autocoder.rag.types import RAGServiceInfo
from autocoder.version import __version__
from autocoder.rags import get_rag_config

if platform.system() == "Windows":
    from colorama import init

    init()


def generate_unique_name_from_path(path: str) -> str:
    """
    Generate a unique name (MD5 hash) from a path after normalizing it.
    For Linux/Unix systems, trailing path separators are removed.
    """
    if not path:
        return ""
    
    # Normalize the path (resolve absolute path and remove trailing separators)
    normalized_path = os.path.normpath(os.path.abspath(path))
    
    # Generate MD5 hash from the normalized path
    return hashlib.md5(normalized_path.encode("utf-8")).hexdigest()


def initialize_system(args):
    if args.product_mode == "lite":
        return

    print(f"\n\033[1;34m{get_message('initializing')}\033[0m")

    def print_status(message, status):
        if status == "success":
            print(f"\033[32m✓ {message}\033[0m")
        elif status == "warning":
            print(f"\033[33m! {message}\033[0m")
        elif status == "error":
            print(f"\033[31m✗ {message}\033[0m")
        else:
            print(f"  {message}")

    # Check if Ray is running
    print_status(get_message("checking_ray"), "")
    ray_status = subprocess.run(["ray", "status"], capture_output=True, text=True)
    if ray_status.returncode != 0:
        print_status(get_message("ray_not_running"), "warning")
        try:
            subprocess.run(["ray", "start", "--head"], check=True)
            print_status(get_message("ray_start_success"), "success")
        except subprocess.CalledProcessError:
            print_status(get_message("ray_start_fail"), "error")
            return
    else:
        print_status(get_message("ray_running"), "success")

    # Check if deepseek_chat model is available
    print_status(get_message("checking_model"), "")
    try:
        result = subprocess.run(
            ["easy-byzerllm", "chat", "v3_chat", "你好"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print_status(get_message("model_available"), "success")
            print_status(get_message("init_complete_final"), "success")
            return
    except subprocess.TimeoutExpired:
        print_status(get_message("model_timeout"), "error")
    except subprocess.CalledProcessError:
        print_status(get_message("model_error"), "error")

    # If deepseek_chat is not available, prompt user to choose a provider
    print_status(get_message("model_not_available"), "warning")
    choice = radiolist_dialog(
        title=get_message("provider_selection"),
        text=get_message("provider_selection"),
        values=[
            ("1", "Deepseek官方(https://www.deepseek.com/)"),
        ],
    ).run()

    if choice is None:
        print_status(get_message("no_provider"), "error")
        return

    api_key = prompt(HTML(f"<b>{get_message('enter_api_key')} </b>"))

    if choice == "1":
        print_status(get_message("deploying_model").format("Deepseek官方"), "")

        deploy_cmd = [
            "byzerllm",
            "deploy",
            "--pretrained_model_type",
            "saas/openai",
            "--cpus_per_worker",
            "0.001",
            "--gpus_per_worker",
            "0",
            "--worker_concurrency",
            "1000",
            "--num_workers",
            "1",
            "--infer_params",
            f"saas.base_url=https://api.deepseek.com/v1 saas.api_key={api_key} saas.model=deepseek-chat",
            "--model",
            "v3_chat",
        ]

    try:
        subprocess.run(deploy_cmd, check=True)
        print_status(get_message("deploy_complete"), "success")
    except subprocess.CalledProcessError:
        print_status(get_message("deploy_fail"), "error")
        return

    # Validate the deployment
    print_status(get_message("validating_deploy"), "")
    try:
        validation_result = subprocess.run(
            ["easy-byzerllm", "chat", "v3_chat", "你好"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        print_status(get_message("validation_success"), "success")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print_status(get_message("validation_fail"), "error")
        print_status(get_message("manual_start"), "warning")
        print_status("easy-byzerllm chat v3_chat 你好", "")

    print_status(get_message("init_complete_final"), "success")


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

                
        if not hasattr(args,arg) and arg not in config:            
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


def main(input_args: Optional[List[str]] = None):
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

    try:
        tokenizer_path = str(resources.files("autocoder") / "data" / "tokenizer.json")
    except FileNotFoundError:
        tokenizer_path = None

    system_lang, _ = locale.getdefaultlocale()
    lang = "zh" if system_lang and system_lang.startswith("zh") else "en"
    desc = lang_desc[lang]
    parser = argparse.ArgumentParser(description="Auto Coder RAG Server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build hybrid index command
    build_index_parser = subparsers.add_parser(
        "build_hybrid_index", help="Build hybrid index for RAG"
    )

    build_index_parser.add_argument(
        "--rag_storage_type",
        type=str,
        default="duckdb",
        help="The storage type of the RAG, duckdb or byzer-storage",
    )

    build_index_parser.add_argument(
        "--rag_index_build_workers",
        type=int,
        default=5,
        help="The number of workers to build the RAG index",
    )

    build_index_parser.add_argument(
        "--quick", action="store_true", help="Skip system initialization"
    )
    build_index_parser.add_argument("--file", default="", help=desc["file"])
    build_index_parser.add_argument(
        "--model", default="v3_chat", help=desc["model"]
    )
    
    build_index_parser.add_argument(
        "--on_ray", action="store_true", help="Run on Ray"
    )

    build_index_parser.add_argument(
        "--index_model", default="", help=desc["index_model"]
    )
    build_index_parser.add_argument("--emb_model", default="", help=desc["emb_model"])
    build_index_parser.add_argument(
        "--ray_address", default="auto", help=desc["ray_address"]
    )
    build_index_parser.add_argument(
        "--required_exts", default="", help=desc["doc_build_parse_required_exts"]
    )
    build_index_parser.add_argument(
        "--source_dir", default=".", help="Source directory path"
    )
    build_index_parser.add_argument(
        "--tokenizer_path", default=tokenizer_path, help="Path to tokenizer file"
    )
    build_index_parser.add_argument(
        "--doc_dir", default="", help="Document directory path"
    )
    build_index_parser.add_argument(
        "--enable_hybrid_index", action="store_true", help="Enable hybrid index"
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the RAG server")
    serve_parser.add_argument(
        "--quick", action="store_true", help="Skip system initialization"
    )
    serve_parser.add_argument("--file", default="", help=desc["file"])
    serve_parser.add_argument("--model", default="v3_chat", help=desc["model"])
    serve_parser.add_argument("--index_model", default="", help=desc["index_model"])    
    serve_parser.add_argument("--ray_address", default="auto", help=desc["ray_address"])
    serve_parser.add_argument(
        "--index_filter_workers",
        type=int,
        default=100,
        help=desc["index_filter_workers"],
    )
    serve_parser.add_argument(
        "--index_filter_file_num",
        type=int,
        default=3,
        help=desc["index_filter_file_num"],
    )
    serve_parser.add_argument(
        "--rag_context_window_limit",
        type=int,
        default=56000,
        help="The input context window limit for RAG",
    )
    serve_parser.add_argument(
        "--full_text_ratio",
        type=float,
        default=0.7,
        help="The ratio of full text area in the input context window (0.0 to 1.0)",
    )
    serve_parser.add_argument(
        "--segment_ratio",
        type=float,
        default=0.2,
        help="The ratio of segment area in the input context window (0.0 to 1.0)",
    )
    serve_parser.add_argument(
        "--required_exts", default="", help=desc["doc_build_parse_required_exts"]
    )
    serve_parser.add_argument(
        "--rag_doc_filter_relevance", type=int, default=5, help=""
    )
    serve_parser.add_argument("--source_dir", default=".", help="")
    serve_parser.add_argument("--host", default="", help="")
    serve_parser.add_argument("--port", type=int, default=8000, help="")
    serve_parser.add_argument("--name", default="", help="RAG服务的名称（可选）")
    serve_parser.add_argument("--workers", type=int, default=4, help="")
    serve_parser.add_argument("--uvicorn_log_level", default="info", help="")
    serve_parser.add_argument("--allow_credentials", action="store_true", help="")
    serve_parser.add_argument("--allowed_origins", default=["*"], help="")
    serve_parser.add_argument("--allowed_methods", default=["*"], help="")
    serve_parser.add_argument("--allowed_headers", default=["*"], help="")
    serve_parser.add_argument("--api_key", default="", help="")
    serve_parser.add_argument("--served_model_name", default="", help="")
    serve_parser.add_argument("--prompt_template", default="", help="")
    serve_parser.add_argument("--ssl_keyfile", default="", help="")
    serve_parser.add_argument("--ssl_certfile", default="", help="")
    serve_parser.add_argument("--response_role", default="assistant", help="")
    serve_parser.add_argument(
        "--doc_dir", 
        default="", 
        help="Document directory path, also used as the root directory for serving static files"
    )
    serve_parser.add_argument("--enable_local_image_host", action="store_true", help=" enable local image host for local Chat app")
    serve_parser.add_argument("--agentic", action="store_true", help="使用 AgenticRAG 而不是 LongContextRAG")
    serve_parser.add_argument("--tokenizer_path", default=tokenizer_path, help="")
    serve_parser.add_argument(
        "--collections", default="", help="Collection name for indexing"
    )
    serve_parser.add_argument(
        "--base_dir",
        default="",
        help="Path where the processed text embeddings were stored",
    )
    serve_parser.add_argument(
        "--monitor_mode",
        action="store_true",
        help="Monitor mode for the doc update",
    )
    serve_parser.add_argument(
        "--max_static_path_length", 
        type=int,
        default=3000,
        help="Maximum length allowed for static file paths (larger value to better support Chinese characters)"
    )
    serve_parser.add_argument(
        "--enable_nginx_x_accel",
        action="store_true",
        help="Enable Nginx X-Accel-Redirect for static file serving when behind Nginx"
    )
    serve_parser.add_argument(
        "--disable_auto_window",
        action="store_true",
        help="Disable automatic window adaptation for documents",
    )
    serve_parser.add_argument(
        "--disable_segment_reorder",
        action="store_true",
        help="Disable reordering of document segments after retrieval",
    )

    serve_parser.add_argument(
        "--disable_inference_enhance",
        action="store_true",
        help="Disable enhanced inference mode",
    )
    serve_parser.add_argument(
        "--inference_deep_thought",
        action="store_true",
        help="Enable deep thought in inference mode",
    )
    serve_parser.add_argument(
        "--inference_slow_without_deep_thought",
        action="store_true",
        help="Enable slow inference without deep thought",
    )
    serve_parser.add_argument(
        "--inference_compute_precision",
        type=int,
        default=64,
        help="The precision of the inference compute",
    )

    serve_parser.add_argument(
        "--enable_hybrid_index",
        action="store_true",
        help="Enable hybrid index",
    )

    serve_parser.add_argument(
        "--rag_storage_type",
        type=str,
        default="duckdb",
        help="The storage type of the RAG, duckdb or byzer-storage",
    )    

    serve_parser.add_argument(
        "--hybrid_index_max_output_tokens",
        type=int,
        default=1000000,
        help="The maximum number of tokens in the output. This is only used when enable_hybrid_index is true.",
    )

    serve_parser.add_argument(
        "--without_contexts",
        action="store_true",
        help="Whether to return responses without contexts. only works when pro plugin is installed",
    )

    serve_parser.add_argument("--data_cells_max_num",
        type=int,
        default=2000,
        help="Maximum number of data cells to process",
    )

    serve_parser.add_argument(
        "--product_mode",
        type=str,
        default="pro",
        help="The mode of the auto-coder.rag, lite/pro default is pro",
    )
    serve_parser.add_argument(
        "--lite",
        action="store_true",
        help="Run in lite mode (equivalent to --product_mode=lite)",
    )
    serve_parser.add_argument(
        "--pro",
        action="store_true",
        help="Run in pro mode (equivalent to --product_mode=pro)",
    )

    serve_parser.add_argument(
        "--recall_model",
        default="",
        help="The model used for recall documents",
    )

    serve_parser.add_argument(
        "--chunk_model",
        default="",
        help="The model used for chunk documents",
    )

    serve_parser.add_argument(
        "--qa_model",
        default="",
        help="The model used for question answering",
    )

    serve_parser.add_argument(
        "--emb_model",
        default="",
        help="The model used for embedding documents",
    )

    serve_parser.add_argument(
        "--agentic_model",
        default="",
        help="The model used for agentic operations",
    )

    serve_parser.add_argument(
        "--context_prune_model",
        default="",
        help="The model used for context pruning",
    )

    serve_parser.add_argument(
        "--firecrawl_api_key",
        default="",
        help="Firecrawl API key for web search and crawl functionality",
    )
    serve_parser.add_argument(
        "--metaso_api_key",
        default="",
        help="Metaso API key for web search and crawl functionality",
    )
    serve_parser.add_argument(
        "--bochaai_api_key",
        default="",
        help="BochaAI API key for web search and crawl functionality",
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Benchmark LLM client performance"
    )
    benchmark_parser.add_argument(
        "--model", default="v3_chat", help="Model to benchmark"
    )
    benchmark_parser.add_argument(
        "--parallel", type=int, default=10, help="Number of parallel requests"
    )
    benchmark_parser.add_argument(
        "--rounds", type=int, default=1, help="Number of rounds to run"
    )
    benchmark_parser.add_argument(
        "--type",
        choices=["openai", "byzerllm"],
        default="byzerllm",
        help="Client type to benchmark",
    )
    benchmark_parser.add_argument(
        "--api_key", default="", help="OpenAI API key for OpenAI client"
    )
    benchmark_parser.add_argument(
        "--base_url", default="", help="Base URL for OpenAI client"
    )
    benchmark_parser.add_argument(
        "--query", default="Hello, how are you?", help="Query to use for benchmarking"
    )

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="Various tools")
    tools_subparsers = tools_parser.add_subparsers(dest="tool", help="Available tools")
    tools_parser.add_argument(
        "--product_mode",
        type=str,
        default="pro",
        help="The mode of the auto-coder.rag, lite/pro default is pro",
    )
    tools_parser.add_argument(
        "--lite",
        action="store_true",
        help="Run in lite mode (equivalent to --product_mode=lite)",
    )
    tools_parser.add_argument(
        "--pro",
        action="store_true",
        help="Run in pro mode (equivalent to --product_mode=pro)",
    )

    # Count tool
    count_parser = tools_subparsers.add_parser("count", help="Count tokens in a file")

    # Recall validation tool
    recall_parser = tools_subparsers.add_parser(
        "recall", help="Validate recall model performance"
    )
    recall_parser.add_argument(
        "--model", required=True, help="Model to use for recall validation"
    )
    recall_parser.add_argument(
        "--content", default=None, help="Content to validate against"
    )
    recall_parser.add_argument(
        "--query", default=None, help="Query to use for validation"
    )

    # Add chunk model validation tool
    chunk_parser = tools_subparsers.add_parser(
        "chunk", help="Validate chunk model performance"
    )
    chunk_parser.add_argument(
        "--model", required=True, help="Model to use for chunk validation"
    )
    chunk_parser.add_argument(
        "--content", default=None, help="Content to validate against"
    )
    chunk_parser.add_argument(
        "--query", default=None, help="Query to use for validation"
    )
    count_parser.add_argument(
        "--tokenizer_path",
        default=tokenizer_path,        
        help="Path to the tokenizer",
    )
    count_parser.add_argument(
        "--file", required=True, help="Path to the file to count tokens"
    )

    args = parser.parse_args(input_args)

    if args.command == "benchmark":
        from .benchmark import benchmark_openai, benchmark_byzerllm

        if args.type == "openai":
            if not args.api_key:
                print("OpenAI API key is required for OpenAI client benchmark")
                return
            asyncio.run(
                benchmark_openai(
                    args.model, args.parallel, args.api_key, args.base_url, args.rounds, args.query
                )
            )
        else:  # byzerllm
            benchmark_byzerllm(args.model, args.parallel, args.rounds, args.query)

    elif args.command == "serve":
        # 如果用户传递了 --name 参数，则加载已保存的配置并与命令行参数合并
        server_args_config = {}
        auto_coder_args_config = {}
        if args.name:
            saved_config = get_rag_config(args.name)
            if saved_config:
                logger.info(f"加载已保存的RAG配置: {args.name}")
                # 将保存的配置合并到 args 中（命令行参数优先）
                for key, value in saved_config.items():
                    # 跳过一些不应该被合并的字段
                    skip_fields = {'name', 'status', 'created_at', 'updated_at', 'process_id', 'stdout_fd', 'stderr_fd', 'cache_build_task_id'}
                    if key in skip_fields:
                        continue 
                    server_args_config[key] = value
                    setattr(args, key, value)
                # 特殊处理 infer_params 字段
                if 'infer_params' in saved_config and saved_config['infer_params']:
                    for infer_key, infer_value in saved_config['infer_params'].items():
                        auto_coder_args_config[infer_key] = infer_value
                logger.info(f"配置合并完成，使用文档目录: {getattr(args, 'doc_dir', 'N/A')}")
            else:
                logger.warning(f"未找到名为 '{args.name}' 的RAG配置")
        
        # Handle lite/pro flags
        if args.pro:
            args.product_mode = "pro"
        else:
            args.product_mode = "lite"
        
        if not args.quick:
            initialize_system(args)
        
        # 使用新的合并逻辑
        server_args = merge_args_with_config(args, server_args_config, ServerArgs, serve_parser)
        auto_coder_args = merge_args_with_config(args, server_args_config, AutoCoderArgs, serve_parser)
        # 设置本地图床的地址
        if args.enable_local_image_host:
            host = server_args.host or "127.0.0.1"
            if host == "0.0.0.0":
                host = "127.0.0.1"
            port = str(server_args.port)
            auto_coder_args.local_image_host = f"{host}:{port}"


        # Generate unique name for RAG build if doc_dir exists
        if server_args.doc_dir:
            auto_coder_args.rag_build_name = generate_unique_name_from_path(server_args.doc_dir)
            auto_coder_args.source_dir = server_args.doc_dir
            logger.info(f"Generated RAG build name: {auto_coder_args.rag_build_name}")        

        if auto_coder_args.enable_hybrid_index and args.product_mode == "pro":
            # 尝试连接storage
            try:
                from byzerllm.apps.byzer_storage.simple_api import ByzerStorage

                storage = ByzerStorage("byzerai_store", "rag", auto_coder_args.rag_build_name)
                storage.retrieval.cluster_info("byzerai_store")
            except Exception as e:
                logger.error(
                    "When enable_hybrid_index is true, ByzerStorage must be started"
                )
                logger.error("Please run 'byzerllm storage start' first")
                return                        
        
        

        if args.product_mode == "pro":
            byzerllm.connect_cluster(address=args.ray_address)
            llm = byzerllm.ByzerLLM()
            llm.skip_nontext_check = True
            llm.setup_default_model_name(args.model)

            # Setup sub models if specified
            if args.recall_model:
                recall_model = byzerllm.ByzerLLM()
                recall_model.setup_default_model_name(args.recall_model)
                recall_model.skip_nontext_check = True
                llm.setup_sub_client("recall_model", recall_model)

            if args.chunk_model:
                chunk_model = byzerllm.ByzerLLM()
                chunk_model.setup_default_model_name(args.chunk_model)
                llm.setup_sub_client("chunk_model", chunk_model)

            if args.qa_model:
                qa_model = byzerllm.ByzerLLM()
                qa_model.setup_default_model_name(args.qa_model)
                qa_model.skip_nontext_check = True
                llm.setup_sub_client("qa_model", qa_model)

            if args.emb_model:
                emb_model = byzerllm.ByzerLLM()
                emb_model.setup_default_model_name(args.emb_model)
                emb_model.skip_nontext_check = True
                llm.setup_sub_client("emb_model", emb_model)

            if args.agentic_model:
                agentic_model = byzerllm.ByzerLLM()
                agentic_model.setup_default_model_name(args.agentic_model)
                agentic_model.skip_nontext_check = True
                llm.setup_sub_client("agentic_model", agentic_model)

            if args.context_prune_model:
                context_prune_model = byzerllm.ByzerLLM()
                context_prune_model.setup_default_model_name(args.context_prune_model)
                context_prune_model.skip_nontext_check = True
                llm.setup_sub_client("context_prune_model", context_prune_model)

            # 当启用hybrid_index时,检查必要的组件
            if auto_coder_args.enable_hybrid_index:
                if not args.emb_model and not llm.is_model_exist("emb"):
                    logger.error(
                        "When enable_hybrid_index is true, an 'emb' model must be deployed"
                    )
                    return
                llm.setup_default_emb_model_name(args.emb_model or "emb")

        if args.product_mode == "lite":
            from autocoder.common.llms import LLMManager
            llm_manager = LLMManager()
            
            def get_model_info_dict(model_name):
                """Helper function to get model info in the expected dictionary format"""
                model_info = llm_manager.get_model_info(model_name, "lite")
                if not model_info:
                    raise ValueError(f"模型 {model_name} 不存在")
                return model_info
            
            model_info = get_model_info_dict(args.model)
            llm = byzerllm.SimpleByzerLLM(default_model_name=args.model)
            llm.deploy(
                model_path="",
                pretrained_model_type=model_info["model_type"],
                udf_name=args.model,
                infer_params={
                    "saas.base_url": model_info["base_url"],
                    "saas.api_key": model_info["api_key"],
                    "saas.model": model_info["model_name"],
                    "saas.is_reasoning": model_info["is_reasoning"],
                    "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                }
            )

            # Setup sub models if specified
            if args.recall_model:
                model_info = get_model_info_dict(args.recall_model)
                recall_model = byzerllm.SimpleByzerLLM(default_model_name=args.recall_model)
                recall_model.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.recall_model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )
                llm.setup_sub_client("recall_model", recall_model)

            if args.chunk_model:
                model_info = get_model_info_dict(args.chunk_model)
                chunk_model = byzerllm.SimpleByzerLLM(default_model_name=args.chunk_model)
                chunk_model.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.chunk_model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )
                llm.setup_sub_client("chunk_model", chunk_model)

            if args.qa_model:
                model_info = get_model_info_dict(args.qa_model)
                qa_model = byzerllm.SimpleByzerLLM(default_model_name=args.qa_model)
                qa_model.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.qa_model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )
                llm.setup_sub_client("qa_model", qa_model)                

            if args.emb_model:
                model_info = get_model_info_dict(args.emb_model)
                emb_model = byzerllm.SimpleByzerLLM(default_model_name=args.emb_model)
                emb_model.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.emb_model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": False,
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )
                llm.setup_sub_client("emb_model", emb_model)

            if args.agentic_model:
                model_info = get_model_info_dict(args.agentic_model)
                agentic_model = byzerllm.SimpleByzerLLM(default_model_name=args.agentic_model)
                agentic_model.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.agentic_model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )
                llm.setup_sub_client("agentic_model", agentic_model)

            if args.context_prune_model:
                model_info = get_model_info_dict(args.context_prune_model)
                context_prune_model = byzerllm.SimpleByzerLLM(default_model_name=args.context_prune_model)
                context_prune_model.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.context_prune_model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )
                llm.setup_sub_client("context_prune_model", context_prune_model)

            if args.enable_hybrid_index:
                if not args.emb_model:
                    raise Exception("When enable_hybrid_index is true, an 'emb' model must be specified")                

        if server_args.doc_dir:            
            auto_coder_args.rag_build_name = generate_unique_name_from_path(server_args.doc_dir)
            if args.agentic:
                rag = AgenticRAG(llm=llm, args=auto_coder_args, path=server_args.doc_dir, tokenizer_path=server_args.tokenizer_path)
            else:
                rag = LongContextRAG(llm=llm, args=auto_coder_args, path=server_args.doc_dir, tokenizer_path=server_args.tokenizer_path)
        else:
            raise Exception("doc_dir is required")

        llm_wrapper = LLWrapper(llm=llm, rag=rag)
        # Save service info    
        service_info = RAGServiceInfo(
            host=server_args.host or "127.0.0.1",
            port=server_args.port,
            model=args.model,
            _pid=os.getpid(),
            _timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  
            args={k: v for k, v in vars(args).items() if not k.startswith("_")}
        )
        try:
            service_info.save()
        except Exception as e:
            logger.warning(f"Failed to save service info: {str(e)}")

        # Start FileMonitor if monitor_mode is enabled and source_dir is provided
        if server_args.doc_dir:
            try:
                # Use singleton pattern to get/create monitor instance
                # FileMonitor ensures only one instance runs per root_dir
                monitor = FileMonitor(server_args.doc_dir)
                if not monitor.is_running():
                    # TODO: Register specific callbacks here if needed in the future
                    # Example: monitor.register(os.path.join(args.source_dir, "specific_file.py"), my_callback)
                    monitor.start()
                    logger.info(f"File monitor started for directory: {server_args.doc_dir}")
                else:
                    # Log if monitor was already running (e.g., started by another part of the app)
                    # Check if the existing monitor's root matches the current request
                    if monitor.root_dir == os.path.abspath(server_args.doc_dir):
                         logger.info(f"File monitor already running for directory: {monitor.root_dir}")
                    else:
                         logger.warning(f"File monitor is running for a different directory ({monitor.root_dir}), cannot start a new one for {args.source_dir}.")
                
                logger.info(f"Getting rules for {server_args.doc_dir}")
                _ = get_rules(server_args.doc_dir)         

            except ValueError as ve: # Catch specific error if root_dir is invalid during init
                 logger.error(f"Failed to initialize file monitor for {args.source_dir}: {ve}")
            except ImportError as ie: # Catch if watchfiles is not installed
                 logger.error(f"Failed to start file monitor: {ie}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while starting file monitor for {args.source_dir}: {e}")
        
        serve(llm=llm_wrapper, args=server_args)
    elif args.command == "build_hybrid_index":
        auto_coder_args = AutoCoderArgs(
            **{
                arg: getattr(args, arg)
                for arg in vars(AutoCoderArgs())
                if hasattr(args, arg)
            }
        )

        # Generate unique name for RAG build if doc_dir exists
        if args.doc_dir:
            auto_coder_args.rag_build_name = generate_unique_name_from_path(args.doc_dir)
            logger.info(f"Generated RAG build name: {auto_coder_args.rag_build_name}")

        auto_coder_args.enable_hybrid_index = True
        auto_coder_args.rag_type = "simple"

        if args.on_ray:

            try:
                from byzerllm.apps.byzer_storage.simple_api import ByzerStorage

                storage = ByzerStorage("byzerai_store", "rag", "files")
                storage.retrieval.cluster_info("byzerai_store")
            except Exception as e:
                logger.error(
                    "When enable_hybrid_index is true, ByzerStorage must be started"
                )
                logger.error("Please run 'byzerllm storage start' first")
                return

            llm = byzerllm.ByzerLLM()
            llm.setup_default_model_name(args.model)

            # 当启用hybrid_index时,检查必要的组件
            if auto_coder_args.enable_hybrid_index:
                if not llm.is_model_exist("emb"):
                    logger.error(
                        "When enable_hybrid_index is true, an 'emb' model must be deployed"
                    )
                    return
                llm.setup_default_emb_model_name("emb")
        else:
            from autocoder.common.llms import LLMManager
            llm_manager = LLMManager()
            model_info = llm_manager.get_model_info(args.model, "lite")
            if not model_info:
                raise ValueError(f"模型 {args.model} 不存在")
            llm = byzerllm.SimpleByzerLLM(default_model_name=args.model)
            llm.deploy(
                model_path="",
                pretrained_model_type=model_info["model_type"],
                udf_name=args.model,
                infer_params={
                    "saas.base_url": model_info["base_url"],
                    "saas.api_key": model_info["api_key"],
                    "saas.model": model_info["model_name"],
                    "saas.is_reasoning": model_info["is_reasoning"],
                    "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                }
            )

            emb_model_info = llm_manager.get_model_info(args.emb_model, "lite")
            if not emb_model_info:
                raise ValueError(f"模型 {args.emb_model} 不存在")
            emb_model = byzerllm.SimpleByzerLLM(default_model_name=args.emb_model)
            emb_model.deploy(
                model_path="",
                pretrained_model_type=emb_model_info["model_type"],
                udf_name=args.emb_model,
                infer_params={
                    "saas.base_url": emb_model_info["base_url"],
                    "saas.api_key": emb_model_info["api_key"],
                    "saas.model": emb_model_info["model_name"],
                    "saas.is_reasoning": False,
                    "saas.max_output_tokens": emb_model_info.get("max_output_tokens", 8096)
                }
            )
            llm.setup_sub_client("emb_model", emb_model)
        
        rag = RAGFactory.get_rag(
            llm=llm,
            args=auto_coder_args,
            path=args.doc_dir,
            tokenizer_path=args.tokenizer_path,
        )

        if hasattr(rag.document_retriever, "cacher"):
            rag.document_retriever.cacher.build_cache()
        else:
            logger.error(
                "The document retriever does not support hybrid index building"
            )
        try:    
            monitor = FileMonitor(args.doc_dir)    
            monitor.stop()
        except Exception as e:
            logger.warning(f"Failed to stop file monitor: {e}")            

    elif args.command == "tools":
        if args.tool == "count":
            # auto-coder.rag tools count --tokenizer_path /Users/allwefantasy/Downloads/tokenizer.json --file /Users/allwefantasy/data/yum/schema/schema.xlsx
            count_tokens(args.tokenizer_path, args.file)
        elif args.tool == "recall":
            from .common.recall_validation import validate_recall
            from autocoder.common.llms import LLMManager

            # Handle lite/pro flags
            if args.lite:
                args.product_mode = "lite"
            elif args.pro:
                args.product_mode = "pro"

            if args.product_mode == "pro":
                llm = byzerllm.ByzerLLM.from_default_model(args.model)
            else:  # lite mode
                llm_manager = LLMManager()
                model_info = llm_manager.get_model_info(args.model, "lite")
                if not model_info:
                    raise ValueError(f"模型 {args.model} 不存在")
                llm = byzerllm.SimpleByzerLLM(default_model_name=args.model)
                llm.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )

            content = None if not args.content else [args.content]
            result = validate_recall(llm, content=content, query=args.query)
            print(f"Recall Validation Result:\n{result}")

        elif args.tool == "chunk":
            from .common.chunk_validation import validate_chunk
            from autocoder.common.llms import LLMManager
            
            if args.lite:
                args.product_mode = "lite"
            elif args.pro:
                args.product_mode = "pro"

            if args.product_mode == "pro":
                llm = byzerllm.ByzerLLM.from_default_model(args.model)
            else:  # lite mode
                chunk_llm_manager = LLMManager()
                model_info = chunk_llm_manager.get_model_info(args.model, "lite")
                if not model_info:
                    raise ValueError(f"模型 {args.model} 不存在")
                llm = byzerllm.SimpleByzerLLM(default_model_name=args.model)
                llm.deploy(
                    model_path="",
                    pretrained_model_type=model_info["model_type"],
                    udf_name=args.model,
                    infer_params={
                        "saas.base_url": model_info["base_url"],
                        "saas.api_key": model_info["api_key"],
                        "saas.model": model_info["model_name"],
                        "saas.is_reasoning": model_info["is_reasoning"],
                        "saas.max_output_tokens": model_info.get("max_output_tokens", 8096)
                    }
                )

            content = None if not args.content else [args.content]
            result = validate_chunk(llm, content=content, query=args.query)
            print(f"Chunk Model Validation Result:\n{result}")


def count_tokens(tokenizer_path: str, file_path: str):
    from autocoder.rag.variable_holder import VariableHolder
    from tokenizers import Tokenizer
    VariableHolder.TOKENIZER_PATH = tokenizer_path
    VariableHolder.TOKENIZER_MODEL = Tokenizer.from_file(tokenizer_path)
    token_counter = TokenCounter(tokenizer_path)    
    source_codes = process_file_local(file_path)

    console = Console()
    table = Table(title="Token Count Results")
    table.add_column("File", style="cyan")
    table.add_column("Characters", justify="right", style="magenta")
    table.add_column("Tokens", justify="right", style="green")

    total_chars = 0
    total_tokens = 0

    for source_code in source_codes:
        content = source_code.source_code
        chars = len(content)
        tokens = token_counter.count_tokens(content)

        total_chars += chars
        total_tokens += tokens

        table.add_row(source_code.module_name, str(chars), str(tokens))

    table.add_row("Total", str(total_chars), str(total_tokens), style="bold")

    console.print(table)


if __name__ == "__main__":
    main()
