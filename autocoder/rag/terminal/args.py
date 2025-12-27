"""命令行参数解析模块"""

import argparse
import locale
import importlib.resources as resources
from autocoder.lang import lang_desc
from autocoder.version import __version__


def get_tokenizer_path():
    """获取默认的 tokenizer 路径"""
    try:
        tokenizer_path = str(resources.files("autocoder") / "data" / "tokenizer.json")
    except FileNotFoundError:
        tokenizer_path = None
    return tokenizer_path


def create_parser():
    """创建并配置参数解析器"""
    system_lang, _ = locale.getdefaultlocale()
    lang = "zh" if system_lang and system_lang.startswith("zh") else "en"
    desc = lang_desc[lang]
    tokenizer_path = get_tokenizer_path()

    parser = argparse.ArgumentParser(description="Auto Coder RAG Server")
    parser.add_argument(
        "--model_file", default="", help="Path to model configuration file"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build hybrid index command
    _add_build_index_parser(subparsers, desc, tokenizer_path)

    # Serve command
    _add_serve_parser(subparsers, desc, tokenizer_path)

    # Run command (直接运行RAG，不启动服务器)
    _add_run_parser(subparsers, desc, tokenizer_path)

    # Benchmark command
    _add_benchmark_parser(subparsers)

    # Tools command
    _add_tools_parser(subparsers, tokenizer_path)

    return parser


def _add_build_index_parser(subparsers, desc, tokenizer_path):
    """添加构建索引命令的参数解析器"""
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
    build_index_parser.add_argument("--model", default="v3_chat", help=desc["model"])
    build_index_parser.add_argument(
        "--model_file", default="", help="Path to model configuration file"
    )

    build_index_parser.add_argument("--on_ray", action="store_true", help="Run on Ray")

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
    build_index_parser.add_argument(
        "--hybrid_index_max_output_tokens",
        type=int,
        default=1000000,
        help="The maximum number of tokens in the output. This is only used when enable_hybrid_index is true.",
    )


def _add_serve_parser(subparsers, desc, tokenizer_path):
    """添加服务命令的参数解析器"""
    serve_parser = subparsers.add_parser("serve", help="Start the RAG server")
    serve_parser.add_argument(
        "--quick", action="store_true", help="Skip system initialization"
    )
    serve_parser.add_argument("--file", default="", help=desc["file"])
    serve_parser.add_argument("--model", default="v3_chat", help=desc["model"])
    serve_parser.add_argument(
        "--model_file", default="", help="Path to model configuration file"
    )
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
        help="Document directory path, also used as the root directory for serving static files",
    )
    serve_parser.add_argument(
        "--enable_local_image_host",
        action="store_true",
        help=" enable local image host for local Chat app",
    )
    serve_parser.add_argument(
        "--agentic", action="store_true", help="使用 AgenticRAG 而不是 LongContextRAG"
    )
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
        help="Maximum length allowed for static file paths (larger value to better support Chinese characters)",
    )
    serve_parser.add_argument(
        "--enable_nginx_x_accel",
        action="store_true",
        help="Enable Nginx X-Accel-Redirect for static file serving when behind Nginx",
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

    serve_parser.add_argument(
        "--data_cells_max_num",
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


def _add_run_parser(subparsers, desc, tokenizer_path):
    """添加 run 命令的参数解析器

    run 命令用于直接运行 RAG 查询，不启动服务器。
    支持从标准输入读取 prompt，例如: echo "问题" | auto-coder.rag run
    """
    run_parser = subparsers.add_parser(
        "run", help="Run RAG query directly without starting a server"
    )

    # 基本参数
    run_parser.add_argument("--model", default="v3_chat", help=desc["model"])
    run_parser.add_argument(
        "--model_file", default="", help="Path to model configuration file"
    )
    run_parser.add_argument("--doc_dir", required=True, help="Document directory path")
    run_parser.add_argument(
        "--query", default="", help="Query text (if not provided, read from stdin)"
    )

    # RAG 配置参数
    run_parser.add_argument(
        "--agentic", action="store_true", help="使用 AgenticRAG 而不是 LongContextRAG"
    )
    run_parser.add_argument(
        "--rag_context_window_limit",
        type=int,
        default=56000,
        help="The input context window limit for RAG",
    )
    run_parser.add_argument(
        "--full_text_ratio",
        type=float,
        default=0.7,
        help="The ratio of full text area in the input context window (0.0 to 1.0)",
    )
    run_parser.add_argument(
        "--segment_ratio",
        type=float,
        default=0.2,
        help="The ratio of segment area in the input context window (0.0 to 1.0)",
    )
    run_parser.add_argument(
        "--rag_doc_filter_relevance",
        type=int,
        default=5,
        help="Document relevance threshold",
    )
    run_parser.add_argument(
        "--required_exts", default="", help=desc["doc_build_parse_required_exts"]
    )

    run_parser.add_argument(
        "--index_filter_workers",
        type=int,
        default=100,
        help=desc["index_filter_workers"],
    )
    run_parser.add_argument(
        "--index_filter_file_num",
        type=int,
        default=3,
        help=desc["index_filter_file_num"],
    )

    # 模型配置
    run_parser.add_argument(
        "--tokenizer_path", default=tokenizer_path, help="Path to tokenizer file"
    )
    run_parser.add_argument(
        "--recall_model", default="", help="The model used for recall documents"
    )
    run_parser.add_argument(
        "--chunk_model", default="", help="The model used for chunk documents"
    )
    run_parser.add_argument(
        "--qa_model", default="", help="The model used for question answering"
    )
    run_parser.add_argument(
        "--emb_model", default="", help="The model used for embedding documents"
    )
    run_parser.add_argument(
        "--agentic_model", default="", help="The model used for agentic operations"
    )
    run_parser.add_argument(
        "--context_prune_model", default="", help="The model used for context pruning"
    )

    # 模式选择
    run_parser.add_argument(
        "--product_mode",
        type=str,
        default="lite",
        help="The mode of the auto-coder.rag, lite/pro default is lite for run command",
    )
    run_parser.add_argument(
        "--lite",
        action="store_true",
        help="Run in lite mode (equivalent to --product_mode=lite)",
    )
    run_parser.add_argument(
        "--pro",
        action="store_true",
        help="Run in pro mode (equivalent to --product_mode=pro)",
    )

    # 其他参数
    run_parser.add_argument("--ray_address", default="auto", help=desc["ray_address"])
    run_parser.add_argument(
        "--enable_hybrid_index",
        action="store_true",
        help="Enable hybrid index",
    )
    run_parser.add_argument(
        "--disable_auto_window",
        action="store_true",
        help="Disable automatic window adaptation for documents",
    )
    run_parser.add_argument(
        "--disable_segment_reorder",
        action="store_true",
        help="Disable reordering of document segments after retrieval",
    )
    run_parser.add_argument(
        "--hybrid_index_max_output_tokens",
        type=int,
        default=1000000,
        help="The maximum number of tokens in the output. This is only used when enable_hybrid_index is true.",
    )
    run_parser.add_argument(
        "--rag_storage_type",
        type=str,
        default="duckdb",
        help="The storage type of the RAG, duckdb or byzer-storage",
    )
    run_parser.add_argument(
        "--output_format",
        choices=["text", "json", "stream-json"],
        default="text",
        help="Output format: text (only answer), json (with metadata), or stream-json (streaming json output)",
    )

    # Web 搜索 API 密钥
    run_parser.add_argument(
        "--metaso_api_key",
        default="",
        help="Metaso API key for web search and crawl functionality (used in agentic mode)",
    )


def _add_benchmark_parser(subparsers):
    """添加基准测试命令的参数解析器"""
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Benchmark LLM client performance"
    )
    benchmark_parser.add_argument(
        "--model", default="v3_chat", help="Model to benchmark"
    )
    benchmark_parser.add_argument(
        "--model_file", default="", help="Path to model configuration file"
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


def _add_tools_parser(subparsers, tokenizer_path):
    """添加工具命令的参数解析器"""
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

    tools_parser.add_argument(
        "--model_file", default="", help="Path to model configuration file"
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
    count_parser.add_argument(
        "--output_format",
        default="text",
        choices=["text", "json"],
        help="Output format: text (rich table) or json",
    )


def parse_arguments(input_args=None):
    """解析命令行参数

    Returns:
        tuple: (args, parser, subparsers_dict) 其中 subparsers_dict 包含各个子命令的 parser
    """
    parser = create_parser()
    args = parser.parse_args(input_args)

    # 重新获取 subparsers 以便访问各个子命令的 parser
    # 这是为了支持 merge_args_with_config 需要访问特定子parser的默认值
    subparsers_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]

    subparsers_dict = {}
    if subparsers_actions:
        subparsers_dict = subparsers_actions[0].choices

    return args, parser, subparsers_dict
