from typing import Dict, Any, Optional
import typing
import openai
from pathlib import Path
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import (
    BaseToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import UseRAGTool, ToolResult
from autocoder.common.rag_manager import RAGManager
from autocoder.rag.sdk import AutoCoderRAGClient, RAGQueryOptions
from loguru import logger

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class UseRAGToolResolver(BaseToolResolver):
    def __init__(
        self, agent: Optional["AgenticEdit"], tool: UseRAGTool, args: AutoCoderArgs
    ):
        super().__init__(agent, tool, args)
        self.tool: UseRAGTool = tool  # For type hinting
        self.rag_manager = RAGManager(args)

    def resolve(self) -> ToolResult:
        """
        通过 OpenAI SDK 或 RAG SDK 访问 RAG server 来执行查询。

        对于内置 RAG（server_name 以 builtin:// 开头），使用 RAG SDK。
        对于其他 RAG 配置，使用 OpenAI SDK。
        """
        server_name = self.tool.server_name
        query = self.tool.query

        logger.info(f"正在解析 UseRAGTool: Server='{server_name}', Query='{query}'")

        # 检查是否有可用的 RAG 配置
        if not self.rag_manager.has_configs():
            error_msg = "未找到可用的 RAG 服务器配置，请确保配置文件存在并格式正确"
            logger.error(error_msg)
            return ToolResult(success=False, message=error_msg)

        try:
            # 查找 RAG 配置
            rag_config = None
            if server_name:
                rag_config = self.rag_manager.get_config_by_name(server_name)
                if not rag_config:
                    # 如果找不到配置，检查是否是直接的 URL
                    if server_name.startswith("http"):
                        # 使用提供的 server_name 作为 base_url
                        return self._resolve_openai_rag_direct(server_name, query)
                    else:
                        error_msg = f"未找到名为 '{server_name}' 的 RAG 服务器配置\n\n{self.rag_manager.get_config_info()}"
                        logger.error(error_msg)
                        return ToolResult(success=False, message=error_msg)
            else:
                # 如果没有指定 server_name，使用第一个非内置的配置
                all_configs = self.rag_manager.get_all_configs()
                non_builtin_configs = [
                    c for c in all_configs if not c.server_name.startswith("builtin://")
                ]
                if not non_builtin_configs:
                    error_msg = "没有可用的外部 RAG 服务器配置"
                    logger.error(error_msg)
                    return ToolResult(success=False, message=error_msg)
                rag_config = non_builtin_configs[0]
                logger.info(f"未指定服务器名称，使用默认配置: {rag_config.name}")

            # 根据 server_name 判断使用哪种方式
            if rag_config.server_name.startswith("builtin://"):
                return self._resolve_builtin_rag(rag_config, query)
            else:
                return self._resolve_openai_rag(rag_config, query)

        except Exception as e:
            error_msg = f"访问 RAG server 时出错: {str(e)}"
            if not self.rag_manager.has_configs():
                error_msg += f"\n\n{self.rag_manager.get_config_info()}"
            logger.error(error_msg)
            return ToolResult(success=False, message=error_msg)

    def _normalize_required_exts(self, exts_str: str) -> str:
        """
        规范化 required_exts 字符串

        - 去除空白
        - 确保每个后缀以点开头
        - 去重
        - 返回逗号分隔的字符串
        """
        if not exts_str:
            return ""

        # 分割并去除空白
        exts = [ext.strip() for ext in exts_str.split(",")]

        # 规范化每个后缀
        normalized = []
        for ext in exts:
            if not ext:
                continue
            # 确保以点开头
            if not ext.startswith("."):
                ext = "." + ext
            normalized.append(ext)

        # 去重并保持顺序
        seen = set()
        unique_exts = []
        for ext in normalized:
            if ext not in seen:
                seen.add(ext)
                unique_exts.append(ext)

        return ",".join(unique_exts)

    def _resolve_builtin_rag(self, rag_config, query: str) -> ToolResult:
        """
        使用 RAG SDK 处理内置 RAG 查询
        """
        logger.info(f"使用 RAG SDK 处理内置 RAG: {rag_config.name}")

        # 根据 server_name 确定文档目录
        doc_dir = None
        if rag_config.server_name == "builtin://conversation":
            # 会话知识库使用 agentic 日志目录
            # 该目录存储了会话的历史记录
            base_path = (
                Path(self.args.source_dir) if self.args.source_dir else Path.cwd()
            )
            doc_dir = base_path / ".auto-coder" / "logs" / "agentic"
            if not doc_dir.exists():
                # 如果不存在会话目录，创建一个空目录
                doc_dir.mkdir(parents=True, exist_ok=True)
                logger.warning(f"会话知识库目录不存在，已创建: {doc_dir}")
        elif rag_config.server_name == "builtin://codebase":
            # 代码知识库使用项目根目录
            doc_dir = Path(self.args.source_dir) if self.args.source_dir else Path.cwd()

        if not doc_dir or not doc_dir.exists():
            error_msg = f"内置 RAG '{rag_config.name}' 的文档目录不存在: {doc_dir}"
            logger.error(error_msg)
            return ToolResult(success=False, message=error_msg)

        try:
            # 创建 RAG SDK 客户端配置
            client_config = {
                "doc_dir": str(doc_dir),
                "model": self.args.model or "v3_chat",
                "timeout": 1800,  # 30分钟超时
            }

            # 只有 codebase RAG 且配置了 codebase_rag_suffixs 时才添加 required_exts
            if (
                rag_config.server_name == "builtin://codebase"
                and self.args.codebase_rag_suffixs
            ):
                # 规范化 required_exts
                normalized_exts = self._normalize_required_exts(
                    self.args.codebase_rag_suffixs
                )
                if normalized_exts:
                    client_config["required_exts"] = normalized_exts
                    logger.info(f"使用文件后缀过滤: {normalized_exts}")

            client = AutoCoderRAGClient(**client_config)

            # 使用流式查询并打印输出
            logger.info("开始流式查询...")
            answer_parts = []

            for message in client.query_stream_messages(
                query, RAGQueryOptions(output_format="stream-json")
            ):
                if message.is_content():
                    # 打印内容
                    print(message.content, end="", flush=True)
                    answer_parts.append(message.content)
                elif message.is_stage():
                    # 打印阶段信息
                    print(f"[{message.stage_type.value}] {message.message}")

            # 换行
            print()

            # 合并所有返回的内容
            answer = "".join(answer_parts)

            logger.info(f"RAG SDK 响应成功，内容长度: {len(answer)}")
            return ToolResult(success=True, message=answer)

        except Exception as e:
            error_msg = f"使用 RAG SDK 处理 '{rag_config.name}' 时出错: {str(e)}"
            logger.error(error_msg)
            return ToolResult(success=False, message=error_msg)

    def _resolve_openai_rag(self, rag_config, query: str) -> ToolResult:
        """
        使用 OpenAI SDK 处理外部 RAG 查询
        """
        base_url = rag_config.server_name
        api_key = rag_config.api_key or "dummy-key"

        logger.info(f"使用 RAG 服务器: {base_url}")

        # 使用 OpenAI SDK 访问 RAG server
        client = openai.OpenAI(base_url=base_url, api_key=api_key)

        response = client.chat.completions.create(
            model="default",
            messages=[{"role": "user", "content": query}],
            max_tokens=8024,
        )

        result_content = response.choices[0].message.content
        logger.info(f"RAG server 响应成功，内容长度: {len(result_content)}")

        return ToolResult(success=True, message=result_content)

    def _resolve_openai_rag_direct(self, base_url: str, query: str) -> ToolResult:
        """
        直接使用 URL 访问 RAG 服务器（不需要配置）
        """
        api_key = "dummy-key"

        logger.info(f"使用直接 URL 访问 RAG 服务器: {base_url}")

        # 使用 OpenAI SDK 访问 RAG server
        client = openai.OpenAI(base_url=base_url, api_key=api_key)

        response = client.chat.completions.create(
            model="default",
            messages=[{"role": "user", "content": query}],
            max_tokens=8024,
        )

        result_content = response.choices[0].message.content
        logger.info(f"RAG server 响应成功，内容长度: {len(result_content)}")

        return ToolResult(success=True, message=result_content)
