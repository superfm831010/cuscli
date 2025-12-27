"""
AutoCoder RAG SDK 客户端

提供调用 auto-coder.rag run 功能的客户端类。
"""

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Generator, List, Optional

from .models import (
    ExecutionError,
    Message,
    MessageType,
    StageType,
    RAGConfig,
    RAGError,
    RAGQueryOptions,
    RAGResponse,
    ValidationError,
)


class AutoCoderRAGClient:
    """
    AutoCoder RAG 客户端

    提供便捷的方法来调用 auto-coder.rag run 命令进行文档问答。

    示例:
        基础用法::

            client = AutoCoderRAGClient(doc_dir="/path/to/docs")
            answer = client.query("如何使用这个项目?")
            print(answer)

        流式输出::

            for chunk in client.query_stream("项目功能是什么?"):
                print(chunk, end="", flush=True)

        上下文管理器::

            with AutoCoderRAGClient(doc_dir="/path/to/docs") as client:
                answer = client.quick_query("问题")

        获取上下文::

            response = client.query_with_contexts("如何安装?")
            print(f"答案: {response.answer}")
            print(f"上下文: {len(response.contexts)}个文档")
    """

    def __init__(
        self,
        doc_dir: Optional[str] = None,
        config: Optional[RAGConfig] = None,
        **kwargs,
    ):
        """
        初始化 RAG 客户端

        Args:
            doc_dir: 文档目录（快捷方式，与config互斥）
            config: RAG配置对象（完整配置，与doc_dir互斥）
            **kwargs: 额外的配置参数，用于快捷配置
                例如: AutoCoderRAGClient(doc_dir=".", agentic=True, timeout=600)

        示例::

            # 方式1: 最简单 - 只提供文档目录
            client = AutoCoderRAGClient(doc_dir="./docs")

            # 方式2: 快捷配置 - 提供doc_dir和其他参数
            client = AutoCoderRAGClient(doc_dir="./docs", agentic=True, timeout=600)

            # 方式3: 完整配置 - 使用config对象
            config = RAGConfig(doc_dir="./docs", agentic=True)
            client = AutoCoderRAGClient(config=config)

        Raises:
            RAGError: 当同时提供doc_dir和config，或两者都未提供时
        """
        # 参数验证
        if config is not None and doc_dir is not None:
            raise RAGError(
                "不能同时提供 doc_dir 和 config 参数\n"
                "请使用以下方式之一:\n"
                "  1. AutoCoderRAGClient(doc_dir='./docs')\n"
                "  2. AutoCoderRAGClient(config=config)"
            )

        if config is None and doc_dir is None:
            raise RAGError(
                "必须提供 doc_dir 或 config 参数\n"
                "示例: AutoCoderRAGClient(doc_dir='./docs')"
            )

        # 创建配置
        if config is not None:
            # 使用提供的config
            if kwargs:
                raise RAGError(
                    "使用 config 参数时，不能使用额外的关键字参数\n"
                    "请将所有配置放在 RAGConfig 对象中"
                )
            self.config = config
        else:
            # 使用 doc_dir 和 kwargs 创建配置
            self.config = RAGConfig(doc_dir=doc_dir, **kwargs)

        self._validate_config()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # 清理资源（如果需要）
        pass

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        mode = "AgenticRAG" if self.config.agentic else "LongContextRAG"
        return (
            f"AutoCoderRAGClient(doc_dir='{self.config.doc_dir}', "
            f"model='{self.config.model}', mode='{mode}', "
            f"product_mode='{self.config.product_mode}')"
        )

    def _validate_config(self) -> None:
        """验证配置有效性"""
        # 验证文档目录存在
        doc_path = Path(self.config.doc_dir)
        if not doc_path.exists():
            raise ValidationError(
                f"文档目录不存在: {self.config.doc_dir}\n"
                f"请确保提供有效的文档目录路径"
            )

        # 验证产品模式
        valid_modes = ["lite", "pro"]
        if self.config.product_mode not in valid_modes:
            raise ValidationError(
                f"不支持的产品模式: {self.config.product_mode}\n"
                f"支持的模式: {', '.join(valid_modes)}"
            )

        # 验证比例参数范围
        if not (0.0 <= self.config.full_text_ratio <= 1.0):
            raise ValidationError(
                f"full_text_ratio 必须在 0.0-1.0 之间，当前值: {self.config.full_text_ratio}"
            )

        if not (0.0 <= self.config.segment_ratio <= 1.0):
            raise ValidationError(
                f"segment_ratio 必须在 0.0-1.0 之间，当前值: {self.config.segment_ratio}"
            )

    def _get_command_path(self) -> str:
        """
        获取命令的完整路径

        在 Windows 上，使用 shutil.which() 来查找可执行文件的完整路径，
        以解决 subprocess 在不使用 shell=True 时无法找到命令的问题。

        Returns:
            命令的完整路径
        """
        command = self.config.command_path

        # 如果已经是完整路径，直接返回
        if os.path.isabs(command):
            return command

        # 使用 shutil.which() 查找命令
        full_path = shutil.which(command)
        if full_path:
            return full_path

        # 在 Windows 上，尝试添加 .exe 后缀
        if platform.system() == "Windows":
            full_path = shutil.which(f"{command}.exe")
            if full_path:
                return full_path

        # 如果找不到，返回原始命令（让后续错误处理来报告问题）
        return command

    def _can_use_subprocess(self) -> bool:
        """检查是否可以使用 subprocess 调用 auto-coder.rag"""
        try:
            # 测试命令是否能正常响应
            result = subprocess.run(
                [self._get_command_path(), "--help"],
                capture_output=True,
                text=True,
                timeout=60,  # 60秒超时
                env=self._build_env(),
            )

            return result.returncode == 0

        except Exception:
            return False

    def _build_env(self, options: Optional[RAGQueryOptions] = None) -> Dict[str, str]:
        """
        构建子进程环境变量

        合并优先级（从低到高）：
        1. os.environ (系统环境变量)
        2. windows_utf8_env (Windows UTF-8 自动配置)
        3. config.envs (全局配置)
        4. options.envs (单次查询配置)

        Args:
            options: 查询选项，包含可选的 envs 字段

        Returns:
            合并后的环境变量字典
        """
        # 1. 复制系统环境变量
        env = os.environ.copy()

        # 2. Windows UTF-8 自动配置
        if self.config.windows_utf8_env and platform.system() == "Windows":
            env.update(
                {
                    "PYTHONIOENCODING": "utf-8",
                    "LANG": "zh_CN.UTF-8",
                    "LC_ALL": "zh_CN.UTF-8",
                    "CHCP": "65001",
                }
            )

        # 3. 全局配置的环境变量
        if self.config.envs:
            env.update(self.config.envs)

        # 4. 单次查询的环境变量（优先级最高）
        if options and options.envs:
            env.update(options.envs)

        return env

    def query(self, question: str, options: Optional[RAGQueryOptions] = None) -> str:
        """
        执行 RAG 查询，返回完整答案

        Args:
            question: 用户问题
            options: 查询选项

        Returns:
            答案字符串

        Raises:
            RAGError: 当执行失败时
        """
        opts = options or RAGQueryOptions()

        # 验证输出格式
        if opts.output_format not in ["text", "json", "stream-json"]:
            raise ValidationError(f"不支持的输出格式: {opts.output_format}")

        # 获取超时时间
        timeout = opts.timeout if opts.timeout is not None else self.config.timeout

        # 构建命令
        cmd = self._build_command(opts)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                input=question,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._build_env(opts),
            )

            if result.returncode != 0:
                error_msg = (
                    result.stderr or f"命令执行失败，退出码: {result.returncode}"
                )
                raise ExecutionError(error_msg, result.returncode)

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise ExecutionError("查询执行超时")
        except Exception as e:
            if isinstance(e, (RAGError, ExecutionError)):
                raise
            raise RAGError(f"执行查询时发生错误: {str(e)}")

    def query_stream(
        self, question: str, options: Optional[RAGQueryOptions] = None
    ) -> Generator[str, None, None]:
        """
        执行 RAG 查询，流式返回结果

        Args:
            question: 用户问题
            options: 查询选项

        Yields:
            答案片段
        """
        opts = options or RAGQueryOptions()

        # 流式输出只支持 text 格式
        if opts.output_format not in ["text", "stream-json"]:
            opts.output_format = "text"

        cmd = self._build_command(opts)

        try:
            # 使用 Popen 进行流式输出
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=self._build_env(opts),
            )

            # 写入问题
            if process.stdin:
                process.stdin.write(question)
                process.stdin.close()

            # 流式读取输出
            if process.stdout:
                for line in process.stdout:
                    yield line.rstrip("\n")

            # 等待进程结束
            process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read() if process.stderr else ""
                raise ExecutionError(
                    stderr or f"命令执行失败，退出码: {process.returncode}",
                    process.returncode,
                )

        except Exception as e:
            if isinstance(e, (RAGError, ExecutionError)):
                raise
            raise RAGError(f"流式查询时发生错误: {str(e)}")

    def query_with_contexts(
        self, question: str, options: Optional[RAGQueryOptions] = None
    ) -> RAGResponse:
        """
        执行 RAG 查询，返回答案和上下文

        Args:
            question: 用户问题
            options: 查询选项

        Returns:
            RAGResponse 对象，包含答案和上下文
        """
        opts = options or RAGQueryOptions()

        # 使用 JSON 格式获取完整信息
        original_format = opts.output_format
        opts.output_format = "json"

        try:
            result = self.query(question, opts)

            # 解析 JSON 响应
            data = json.loads(result)

            return RAGResponse(
                success=True,
                answer=data.get("answer", ""),
                contexts=data.get("contexts", []),
                metadata=data.get("metadata", {}),
            )

        except json.JSONDecodeError as e:
            return RAGResponse.error_response(f"JSON解析失败: {str(e)}")
        except Exception as e:
            if isinstance(e, RAGError):
                return RAGResponse.error_response(str(e))
            return RAGResponse.error_response(f"查询失败: {str(e)}")
        finally:
            opts.output_format = original_format

    def _build_command(self, options: RAGQueryOptions) -> List[str]:
        """构建命令行参数"""
        cmd = [self._get_command_path(), "run", "--doc_dir", self.config.doc_dir]

        # 模型参数
        model = options.model or self.config.model
        if model:
            cmd.extend(["--model", model])

        # 模型配置文件
        model_file = options.model_file or self.config.model_file
        if model_file:
            cmd.extend(["--model_file", model_file])

        # 输出格式
        cmd.extend(["--output_format", options.output_format])

        # RAG 模式
        agentic = (
            options.agentic if options.agentic is not None else self.config.agentic
        )
        if agentic:
            cmd.append("--agentic")

        # 产品模式
        product_mode = options.product_mode or self.config.product_mode
        if product_mode == "pro":
            cmd.append("--pro")
        elif product_mode == "lite":
            cmd.append("--lite")

        # RAG 参数
        cmd.extend(
            [
                "--rag_context_window_limit",
                str(self.config.rag_context_window_limit),
                "--full_text_ratio",
                str(self.config.full_text_ratio),
                "--segment_ratio",
                str(self.config.segment_ratio),
                "--rag_doc_filter_relevance",
                str(self.config.rag_doc_filter_relevance),
            ]
        )

        # 可选模型
        if self.config.recall_model:
            cmd.extend(["--recall_model", self.config.recall_model])
        if self.config.chunk_model:
            cmd.extend(["--chunk_model", self.config.chunk_model])
        if self.config.qa_model:
            cmd.extend(["--qa_model", self.config.qa_model])
        if self.config.emb_model:
            cmd.extend(["--emb_model", self.config.emb_model])
        if self.config.agentic_model:
            cmd.extend(["--agentic_model", self.config.agentic_model])
        if self.config.context_prune_model:
            cmd.extend(["--context_prune_model", self.config.context_prune_model])

        # Tokenizer
        if self.config.tokenizer_path:
            cmd.extend(["--tokenizer_path", self.config.tokenizer_path])

        # 索引选项
        if self.config.enable_hybrid_index:
            cmd.append("--enable_hybrid_index")
        if self.config.disable_auto_window:
            cmd.append("--disable_auto_window")
        if self.config.disable_segment_reorder:
            cmd.append("--disable_segment_reorder")

        # 其他参数
        if self.config.required_exts:
            cmd.extend(["--required_exts", self.config.required_exts])

        return cmd

    def get_version(self) -> str:
        """获取 auto-coder.rag 版本"""
        try:
            result = subprocess.run(
                [self._get_command_path(), "--version"],
                capture_output=True,
                text=True,
                timeout=60,  # 60秒超时
                env=self._build_env(),
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def check_availability(self) -> bool:
        """检查 auto-coder.rag 命令是否可用"""
        return self._can_use_subprocess()

    def quick_query(self, question: str) -> str:
        """
        便捷方法：执行查询并返回文本答案

        等价于 query(question, RAGQueryOptions(output_format="text"))

        Args:
            question: 用户问题

        Returns:
            答案字符串
        """
        return self.query(question, RAGQueryOptions(output_format="text"))

    def query_json(self, question: str) -> dict:
        """
        便捷方法：执行查询并返回JSON格式结果

        Args:
            question: 用户问题

        Returns:
            JSON字典

        Raises:
            RAGError: 当JSON解析失败时
        """
        result = self.query(question, RAGQueryOptions(output_format="json"))
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            raise RAGError(f"JSON解析失败: {str(e)}")

    def query_stream_messages(
        self, question: str, options: Optional[RAGQueryOptions] = None
    ) -> Generator[Message, None, None]:
        """
        执行查询并返回 Message 对象流

        这个方法使用 stream-json 格式，返回结构化的 Message 对象，
        可以更精确地控制和处理不同类型的消息。

        Args:
            question: 用户问题
            options: 查询选项（默认使用 stream-json 格式）

        Yields:
            Message: 结构化的消息对象

        Raises:
            ValidationError: 参数验证失败
            ExecutionError: 命令执行失败
            RAGError: 其他错误

        示例::

            # 基础用法
            for message in client.query_stream_messages("如何使用?"):
                if message.is_content():
                    print(message.content, end="", flush=True)
                elif message.is_stage():
                    print(f"[{message.stage_type.value}] {message.message}")

            # 只处理内容消息
            content_parts = []
            for message in client.query_stream_messages("问题"):
                if message.is_content():
                    content_parts.append(message.content)

            # 检查处理阶段
            for message in client.query_stream_messages("问题"):
                if message.is_retrieval_stage():
                    print(f"正在检索: {message.message}")
                elif message.is_generation_stage():
                    print(f"正在生成: {message.message}")
        """
        if options is None:
            options = RAGQueryOptions(output_format="stream-json")
        else:
            # 确保使用 stream-json 格式
            options = RAGQueryOptions(
                output_format="stream-json",
                agentic=options.agentic,
                product_mode=options.product_mode,
                model=options.model,
                timeout=options.timeout,
            )

        cmd = self._build_command(options)

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲
                env=self._build_env(options),
            )

            # 发送问题
            process.stdin.write(question)
            process.stdin.close()

            # 读取输出
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    message = Message.from_json(line)
                    yield message
                except ValueError as e:
                    # 如果解析失败，跳过这行
                    continue

            # 等待进程完成
            return_code = process.wait()
            if return_code != 0:
                stderr_output = process.stderr.read()
                raise ExecutionError(
                    f"命令执行失败，退出码: {return_code}\n错误输出: {stderr_output}",
                    return_code,
                )

        except subprocess.TimeoutExpired:
            process.kill()
            raise ExecutionError("查询执行超时")
        except Exception as e:
            if isinstance(e, (ValidationError, ExecutionError, RAGError)):
                raise
            raise RAGError(f"执行查询时发生错误: {e}")

    def query_collect_messages(
        self, question: str, options: Optional[RAGQueryOptions] = None
    ) -> RAGResponse:
        """
        执行查询并返回包含 Message 流的 RAGResponse

        这个方法收集所有的 Message 对象，并构建一个包含完整信息的 RAGResponse。

        Args:
            question: 用户问题
            options: 查询选项

        Returns:
            RAGResponse: 包含答案、上下文和元数据的响应对象

        示例::

            response = client.query_collect_messages("如何使用?")
            print(f"答案: {response.answer}")
            print(f"上下文数量: {len(response.contexts)}")
            print(f"元数据: {response.metadata}")
        """
        content_parts = []
        contexts = []
        metadata = {}
        tokens_info = {"input": 0, "generated": 0}

        try:
            for message in self.query_stream_messages(question, options):
                if message.is_content():
                    content_parts.append(message.content or "")
                elif message.is_contexts():
                    contexts.extend(message.contexts or [])
                elif message.is_end():
                    metadata = message.metadata or {}
                elif message.tokens:
                    tokens_info["input"] += message.tokens.input
                    tokens_info["generated"] += message.tokens.generated

            answer = "".join(content_parts)

            # 添加 token 信息到元数据
            metadata["tokens"] = tokens_info

            return RAGResponse.success_response(answer, contexts, metadata)

        except Exception as e:
            return RAGResponse.error_response(str(e))
