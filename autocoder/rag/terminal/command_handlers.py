"""命令处理逻辑模块"""

import asyncio
import os
import sys
from datetime import datetime
import byzerllm
from loguru import logger

from autocoder.common import AutoCoderArgs
from autocoder.rag.api_server import serve, ServerArgs
from autocoder.rag.rag_entry import RAGFactory
from autocoder.rag.agentic_rag import AgenticRAG
from autocoder.rag.long_context_rag import LongContextRAG
from autocoder.rag.llm_wrapper import LLWrapper
from autocoder.rag.types import RAGServiceInfo
from autocoder.rags import get_rag_config
from autocoder.common.file_monitor.monitor import FileMonitor
from autocoder.common.rulefiles import get_rules
from autocoder.rag.terminal.utils import (
    generate_unique_name_from_path,
    merge_args_with_config,
    count_tokens,
)
from autocoder.common.recall_validation import validate_recall
from autocoder.common.chunk_validation import validate_chunk
from autocoder.common.llms import LLMManager
from autocoder.rag.terminal.formatters import format_rag_output

# 配置加载时需要跳过的字段（这些是系统内部字段，不应从保存的配置中恢复）
_SKIP_CONFIG_FIELDS = {
    "name",
    "status",
    "created_at",
    "updated_at",
    "process_id",
    "stdout_fd",
    "stderr_fd",
    "cache_build_task_id",
}


def handle_run_command(args):
    """处理 run 命令 - 直接运行 RAG 查询，不启动服务器

    主要步骤:
    1. 读取查询内容（从 --query 或 stdin）
    2. 设置 product_mode (lite/pro)
    3. 创建 AutoCoderArgs
    4. 初始化 LLM
    5. 创建 RAG 实例（AgenticRAG 或 LongContextRAG）
    6. 执行查询
    7. 输出结果
    """
    # 步骤1: 读取查询内容
    query = args.query

    # 如果没有提供 --query，从 stdin 读取（支持管道）
    if not query:
        if not sys.stdin.isatty():
            query = sys.stdin.read().strip()
        else:
            logger.error("No query provided. Use --query or pipe input via stdin")
            print("错误: 没有提供查询内容。请使用 --query 参数或通过管道传入。")
            print("示例: echo '你的问题' | auto-coder.rag run --doc_dir /path/to/docs")
            return

    if not query:
        logger.error("Empty query provided")
        print("错误: 查询内容为空")
        return

    # 步骤2: 设置 product_mode
    if args.pro:
        args.product_mode = "pro"
    elif args.lite:
        args.product_mode = "lite"
    # 否则使用默认值 (lite)

    # 步骤3: 创建 AutoCoderArgs
    auto_coder_args = AutoCoderArgs(
        source_dir=args.doc_dir,
        rag_context_window_limit=args.rag_context_window_limit,
        full_text_ratio=args.full_text_ratio,
        segment_ratio=args.segment_ratio,
        rag_doc_filter_relevance=args.rag_doc_filter_relevance,
        required_exts=args.required_exts,
        enable_hybrid_index=args.enable_hybrid_index,
        disable_auto_window=args.disable_auto_window,
        disable_segment_reorder=args.disable_segment_reorder,
        model=args.model,
        emb_model=args.emb_model,
        product_mode=args.product_mode or "lite",
        model_file=args.model_file,
        hybrid_index_max_output_tokens=args.hybrid_index_max_output_tokens,
        rag_storage_type=args.rag_storage_type,
        rag_run_once=True,  # Run command is one-time execution
        index_filter_workers=args.index_filter_workers,
        index_filter_file_num=args.index_filter_file_num,
        metaso_api_key=args.metaso_api_key,
    )

    # 生成 RAG build name
    auto_coder_args.rag_build_name = generate_unique_name_from_path(args.doc_dir)

    # 步骤4: 初始化 LLM
    llm = _setup_llm(args, auto_coder_args)

    # 步骤5: 创建 RAG 实例
    if args.agentic:
        rag = AgenticRAG(
            llm=llm,
            args=auto_coder_args,
            path=args.doc_dir,
            tokenizer_path=args.tokenizer_path,
        )
    else:
        rag = LongContextRAG(
            llm=llm,
            args=auto_coder_args,
            path=args.doc_dir,
            tokenizer_path=args.tokenizer_path,
        )

    # 步骤6: 执行查询
    conversations = [{"role": "user", "content": query}]

    try:
        result_generator, contexts = rag.stream_chat_oai(conversations)

        # 步骤7: 使用格式化器输出结果
        format_rag_output(result_generator, contexts, args.output_format)

    except Exception as e:
        logger.error(f"Error executing RAG query: {str(e)}")
        import traceback

        traceback.print_exc()
        print(f"\n错误: {str(e)}")
        return
    finally:
        rag.close()
        # 确保 stdout 被刷新，以便 Node.js 进程能正确读取所有输出
        sys.stdout.flush()
        # Run 模式是一次性执行，完成后强制退出进程
        # 这确保所有守护线程和资源都能被正确清理
        # 使用 os._exit 而不是 exit，避免触发 atexit 钩子
        os._exit(0)


def handle_benchmark_command(args):
    """处理 benchmark 命令"""
    try:
        from autocoder.rag.benchmark import benchmark_openai, benchmark_byzerllm
    except ImportError:
        logger.error(
            "Benchmark module not found. This feature may have been removed or moved."
        )
        print("错误: benchmark 功能模块未找到")
        return

    if args.type == "openai":
        if not args.api_key:
            print("OpenAI API key is required for OpenAI client benchmark")
            return
        asyncio.run(
            benchmark_openai(
                args.model,
                args.parallel,
                args.api_key,
                args.base_url,
                args.rounds,
                args.query,
            )
        )
    else:  # byzerllm
        benchmark_byzerllm(args.model, args.parallel, args.rounds, args.query)


def handle_serve_command(args, serve_parser):
    """处理 serve 命令

    主要步骤:
    1. 加载保存的配置（如果指定了 --name）
    2. 设置 product_mode (lite/pro)
    3. 合并参数配置
    4. 设置本地图床
    5. 生成 RAG build name
    6. 检查 ByzerStorage（pro 模式 + hybrid_index）
    7. 初始化 LLM
    8. 创建 RAG 实例
    9. 启动文件监控
    10. 启动服务
    """
    # 步骤1: 加载保存的配置
    server_args_config = {}
    auto_coder_args_config = {}

    if args.name:
        saved_config = get_rag_config(args.name)
        if saved_config:
            logger.info(f"加载已保存的RAG配置: {args.name}")

            # 合并配置，跳过系统内部字段
            for key, value in saved_config.items():
                if key in _SKIP_CONFIG_FIELDS:
                    continue
                server_args_config[key] = value
                setattr(args, key, value)

            # 特殊处理 infer_params 字段
            if "infer_params" in saved_config and saved_config["infer_params"]:
                for infer_key, infer_value in saved_config["infer_params"].items():
                    auto_coder_args_config[infer_key] = infer_value

            logger.info(
                f"配置合并完成，使用文档目录: {getattr(args, 'doc_dir', 'N/A')}"
            )
        else:
            logger.warning(f"未找到名为 '{args.name}' 的RAG配置")

    # 步骤2: 设置 product_mode
    if args.pro:
        args.product_mode = "pro"
    else:
        args.product_mode = "lite"

    # 步骤3: 合并参数配置
    server_args = merge_args_with_config(
        args, server_args_config, ServerArgs, serve_parser
    )
    auto_coder_args = merge_args_with_config(
        args, server_args_config, AutoCoderArgs, serve_parser
    )

    # 传递 model_file 参数
    if hasattr(args, "model_file") and args.model_file:
        auto_coder_args.model_file = args.model_file

    # Serve 模式是常驻服务，使用异步增量更新
    auto_coder_args.rag_run_once = False

    # 步骤4: 设置本地图床地址
    if args.enable_local_image_host:
        host = server_args.host or "127.0.0.1"
        # 如果监听所有地址，本地访问用 127.0.0.1
        if host == "0.0.0.0":
            host = "127.0.0.1"
        port = str(server_args.port)
        auto_coder_args.local_image_host = f"{host}:{port}"

    # 步骤5: 生成 RAG build name（用于标识此 RAG 实例）
    if server_args.doc_dir:
        auto_coder_args.rag_build_name = generate_unique_name_from_path(
            server_args.doc_dir
        )
        auto_coder_args.source_dir = server_args.doc_dir
        logger.info(f"Generated RAG build name: {auto_coder_args.rag_build_name}")

    # 步骤6: 检查 ByzerStorage（仅 pro 模式 + hybrid_index 时需要）
    if auto_coder_args.enable_hybrid_index and args.product_mode == "pro":
        try:
            from byzerllm.apps.byzer_storage.simple_api import ByzerStorage

            storage = ByzerStorage(
                "byzerai_store", "rag", auto_coder_args.rag_build_name
            )
            storage.retrieval.cluster_info("byzerai_store")
        except Exception as e:
            logger.error(
                "When enable_hybrid_index is true, ByzerStorage must be started"
            )
            logger.error("Please run 'byzerllm storage start' first")
            return

    # 步骤7: 初始化 LLM（根据 product_mode 选择 pro 或 lite）
    llm = _setup_llm(args, auto_coder_args)

    # 步骤8: 创建 RAG 实例（AgenticRAG 或 LongContextRAG）
    if server_args.doc_dir:
        auto_coder_args.rag_build_name = generate_unique_name_from_path(
            server_args.doc_dir
        )

        # 根据 --agentic 参数选择 RAG 类型
        if args.agentic:
            rag = AgenticRAG(
                llm=llm,
                args=auto_coder_args,
                path=server_args.doc_dir,
                tokenizer_path=server_args.tokenizer_path,
            )
        else:
            rag = LongContextRAG(
                llm=llm,
                args=auto_coder_args,
                path=server_args.doc_dir,
                tokenizer_path=server_args.tokenizer_path,
            )
    else:
        raise Exception("doc_dir is required")

    # 创建 LLM Wrapper（包装 LLM 和 RAG）
    llm_wrapper = LLWrapper(llm=llm, rag=rag)

    # 保存服务信息（用于服务管理和监控）
    service_info = RAGServiceInfo(
        host=server_args.host or "127.0.0.1",
        port=server_args.port,
        model=args.model,
        _pid=os.getpid(),
        _timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        args={k: v for k, v in vars(args).items() if not k.startswith("_")},
    )
    try:
        service_info.save()
    except Exception as e:
        logger.warning(f"Failed to save service info: {str(e)}")

    # 步骤9: 启动文件监控（监控文档目录变化）
    if server_args.doc_dir:
        try:
            # 使用单例模式获取/创建监控实例（每个目录只能有一个监控实例）
            monitor = FileMonitor(server_args.doc_dir)

            if not monitor.is_running():
                monitor.start()
                logger.info(
                    f"File monitor started for directory: {server_args.doc_dir}"
                )
            else:
                # 检查已运行的监控是否为同一目录
                if monitor.root_dir == os.path.abspath(server_args.doc_dir):
                    logger.info(
                        f"File monitor already running for directory: {monitor.root_dir}"
                    )
                else:
                    logger.warning(
                        f"File monitor is running for a different directory ({monitor.root_dir}), "
                        f"cannot start a new one for {args.source_dir}."
                    )

            # 加载规则文件（.gitignore, .autocoderignore 等）
            logger.info(f"Getting rules for {server_args.doc_dir}")
            _ = get_rules(server_args.doc_dir)

        except ValueError as ve:
            logger.error(
                f"Failed to initialize file monitor for {args.source_dir}: {ve}"
            )
        except ImportError as ie:
            logger.error(f"Failed to start file monitor: {ie}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while starting file monitor "
                f"for {args.source_dir}: {e}"
            )

    # 步骤10: 启动 RAG 服务
    serve(llm=llm_wrapper, args=server_args)


def handle_build_hybrid_index_command(args):
    """处理 build_hybrid_index 命令"""
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
        llm_manager = LLMManager(
            models_json_path=args.model_file if args.model_file else None
        )
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
                "saas.max_output_tokens": model_info.get("max_output_tokens", 8096),
            },
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
                "saas.max_output_tokens": emb_model_info.get("max_output_tokens", 8096),
            },
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
        logger.error("The document retriever does not support hybrid index building")
    try:
        monitor = FileMonitor(args.doc_dir)
        monitor.stop()
    except Exception as e:
        logger.warning(f"Failed to stop file monitor: {e}")


def handle_tools_command(args):
    """处理 tools 命令"""
    if args.tool == "count":
        # auto-coder.rag tools count --tokenizer_path /Users/allwefantasy/Downloads/tokenizer.json --file /Users/allwefantasy/data/yum/schema/schema.xlsx --output_format json
        output_format = getattr(args, "output_format", "text")
        count_tokens(args.tokenizer_path, args.file, output_format)
    elif args.tool == "recall":
        _handle_recall_tool(args)
    elif args.tool == "chunk":
        _handle_chunk_tool(args)


def _handle_recall_tool(args):
    """处理 recall 工具"""

    # Handle lite/pro flags
    if args.lite:
        args.product_mode = "lite"
    elif args.pro:
        args.product_mode = "pro"

    if args.product_mode == "pro":
        llm = byzerllm.ByzerLLM.from_default_model(args.model)
    else:  # lite mode
        llm_manager = LLMManager(
            models_json_path=args.model_file if args.model_file else None
        )
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
                "saas.max_output_tokens": model_info.get("max_output_tokens", 8096),
            },
        )

    content = None if not args.content else [args.content]
    result = validate_recall(llm, content=content, query=args.query)
    print(f"Recall Validation Result:\n{result}")


def _handle_chunk_tool(args):
    """处理 chunk 工具"""
    if args.lite:
        args.product_mode = "lite"
    elif args.pro:
        args.product_mode = "pro"

    if args.product_mode == "pro":
        llm = byzerllm.ByzerLLM.from_default_model(args.model)
    else:  # lite mode
        chunk_llm_manager = LLMManager(
            models_json_path=args.model_file if args.model_file else None
        )
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
                "saas.max_output_tokens": model_info.get("max_output_tokens", 8096),
            },
        )

    content = None if not args.content else [args.content]
    result = validate_chunk(llm, content=content, query=args.query)
    print(f"Chunk Model Validation Result:\n{result}")


def _setup_llm(args, auto_coder_args):
    """设置并配置 LLM"""
    if args.product_mode == "pro":
        return _setup_llm_pro(args, auto_coder_args)
    else:
        return _setup_llm_lite(args, auto_coder_args)


def _setup_llm_pro(args, auto_coder_args):
    """Pro 模式下设置 LLM"""
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

    return llm


def _setup_llm_lite(args, auto_coder_args):
    """Lite 模式下设置 LLM"""
    from autocoder.common.llms import LLMManager

    llm_manager = LLMManager(
        models_json_path=args.model_file if args.model_file else None
    )

    def get_model_info_dict(model_name):
        """获取模型信息的辅助函数"""
        model_info = llm_manager.get_model_info(model_name, "lite")
        if not model_info:
            raise ValueError(f"模型 {model_name} 不存在")
        return model_info

    def deploy_simple_llm(model_name):
        """部署单个 SimpleByzerLLM 模型的辅助函数"""
        model_info = get_model_info_dict(model_name)
        model = byzerllm.SimpleByzerLLM(default_model_name=model_name)
        model.deploy(
            model_path="",
            pretrained_model_type=model_info["model_type"],
            udf_name=model_name,
            infer_params={
                "saas.base_url": model_info["base_url"],
                "saas.api_key": model_info["api_key"],
                "saas.model": model_info["model_name"],
                "saas.is_reasoning": model_info["is_reasoning"],
                "saas.max_output_tokens": model_info.get("max_output_tokens", 8096),
            },
        )
        return model

    # 部署主模型
    llm = deploy_simple_llm(args.model)

    # 部署子模型（如果指定）
    if args.recall_model:
        llm.setup_sub_client("recall_model", deploy_simple_llm(args.recall_model))

    if args.chunk_model:
        llm.setup_sub_client("chunk_model", deploy_simple_llm(args.chunk_model))

    if args.qa_model:
        llm.setup_sub_client("qa_model", deploy_simple_llm(args.qa_model))

    if args.emb_model:
        llm.setup_sub_client("emb_model", deploy_simple_llm(args.emb_model))

    if args.agentic_model:
        llm.setup_sub_client("agentic_model", deploy_simple_llm(args.agentic_model))

    if args.context_prune_model:
        llm.setup_sub_client(
            "context_prune_model", deploy_simple_llm(args.context_prune_model)
        )

    if auto_coder_args.enable_hybrid_index:
        if not args.emb_model:
            raise Exception(
                "When enable_hybrid_index is true, an 'emb' model must be specified"
            )

    return llm
