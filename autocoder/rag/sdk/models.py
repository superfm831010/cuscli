"""
AutoCoder RAG SDK 数据模型

定义SDK中使用的各种数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json
import os
import platform
from datetime import datetime


# 类型别名
RAGEnvVars = Dict[str, str]


def append_path(additional_path: str, current_path: Optional[str] = None) -> str:
    """
    以跨平台方式追加 PATH 环境变量

    Args:
        additional_path: 要追加的路径
        current_path: 当前 PATH 值（默认使用 os.environ.get('PATH')）

    Returns:
        追加后的 PATH 值

    示例::

        # Unix/Linux/macOS
        path = append_path('/custom/bin')
        # 结果: '/usr/bin:/usr/local/bin:/custom/bin'

        # Windows
        path = append_path('C:\\custom\\bin')
        # 结果: 'C:\\Windows\\System32;C:\\custom\\bin'
    """
    delimiter = ";" if platform.system() == "Windows" else ":"
    base_path = current_path if current_path is not None else os.environ.get("PATH", "")
    return f"{base_path}{delimiter}{additional_path}" if base_path else additional_path


def prepend_path(additional_path: str, current_path: Optional[str] = None) -> str:
    """
    以跨平台方式前置 PATH 环境变量

    Args:
        additional_path: 要前置的路径
        current_path: 当前 PATH 值（默认使用 os.environ.get('PATH')）

    Returns:
        前置后的 PATH 值

    示例::

        # Unix/Linux/macOS
        path = prepend_path('/custom/bin')
        # 结果: '/custom/bin:/usr/bin:/usr/local/bin'

        # Windows
        path = prepend_path('C:\\custom\\bin')
        # 结果: 'C:\\custom\\bin;C:\\Windows\\System32'
    """
    delimiter = ";" if platform.system() == "Windows" else ":"
    base_path = current_path if current_path is not None else os.environ.get("PATH", "")
    return f"{additional_path}{delimiter}{base_path}" if base_path else additional_path


class MessageType(Enum):
    """消息类型枚举"""

    START = "start"
    STAGE = "stage"
    CONTENT = "content"
    CONTEXTS = "contexts"
    END = "end"


class StageType(Enum):
    """处理阶段类型枚举"""

    PROCESSING = "processing"
    RETRIEVAL = "retrieval"
    FILTERING = "filtering"
    CHUNKING = "chunking"
    GENERATION = "generation"


@dataclass
class TokenInfo:
    """Token 信息"""

    input: int = 0
    generated: int = 0


@dataclass
class Message:
    """
    统一的 RAG 消息对象

    用于处理 auto-coder.rag run 的 stream-json 输出格式。

    示例::

        # 解析 JSON 消息
        json_data = '{"event_type": "content", "data": {"content": "Hello"}, "timestamp": "2025-10-20T17:31:25.777563"}'
        message = Message.from_json(json_data)

        # 检查消息类型
        if message.is_content():
            print(f"内容: {message.content}")

        # 检查阶段类型
        if message.is_stage() and message.stage_type == StageType.PROCESSING:
            print(f"处理中: {message.message}")
    """

    # 消息类型
    event_type: MessageType

    # 时间戳
    timestamp: datetime

    # 数据内容（根据 event_type 不同而不同）
    data: Dict[str, Any] = field(default_factory=dict)

    # 原始 JSON 字符串（用于调试）
    raw_json: Optional[str] = None

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """从 JSON 字符串创建 Message 对象"""
        try:
            data = json.loads(json_str.strip())

            # 解析时间戳
            timestamp_str = data.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now()

            # 解析事件类型
            event_type_str = data.get("event_type", "")
            try:
                event_type = MessageType(event_type_str)
            except ValueError:
                raise ValueError(f"未知的事件类型: {event_type_str}")

            return cls(
                event_type=event_type,
                timestamp=timestamp,
                data=data.get("data", {}),
                raw_json=json_str,
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的 JSON 格式: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    # 便捷方法：检查消息类型
    def is_start(self) -> bool:
        """是否为开始消息"""
        return self.event_type == MessageType.START

    def is_stage(self) -> bool:
        """是否为阶段消息"""
        return self.event_type == MessageType.STAGE

    def is_content(self) -> bool:
        """是否为内容消息"""
        return self.event_type == MessageType.CONTENT

    def is_contexts(self) -> bool:
        """是否为上下文消息"""
        return self.event_type == MessageType.CONTEXTS

    def is_end(self) -> bool:
        """是否为结束消息"""
        return self.event_type == MessageType.END

    # 便捷方法：获取特定数据
    @property
    def status(self) -> Optional[str]:
        """获取状态信息（start/end 消息）"""
        return self.data.get("status")

    @property
    def stage_type(self) -> Optional[StageType]:
        """获取阶段类型（stage 消息）"""
        stage_type_str = self.data.get("type")
        if stage_type_str:
            try:
                return StageType(stage_type_str)
            except ValueError:
                return None
        return None

    @property
    def message(self) -> Optional[str]:
        """获取消息内容（stage 消息）"""
        return self.data.get("message")

    @property
    def content(self) -> Optional[str]:
        """获取内容（content 消息）"""
        return self.data.get("content")

    @property
    def contexts(self) -> Optional[List[str]]:
        """获取上下文列表（contexts 消息）"""
        return self.data.get("contexts")

    @property
    def tokens(self) -> Optional[TokenInfo]:
        """获取 Token 信息"""
        tokens_data = self.data.get("tokens")
        if tokens_data:
            return TokenInfo(
                input=tokens_data.get("input", 0),
                generated=tokens_data.get("generated", 0),
            )
        return None

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """获取元数据（end 消息）"""
        return self.data.get("metadata")

    # 便捷方法：检查阶段类型
    def is_processing_stage(self) -> bool:
        """是否为处理阶段"""
        return self.is_stage() and self.stage_type == StageType.PROCESSING

    def is_retrieval_stage(self) -> bool:
        """是否为检索阶段"""
        return self.is_stage() and self.stage_type == StageType.RETRIEVAL

    def is_filtering_stage(self) -> bool:
        """是否为过滤阶段"""
        return self.is_stage() and self.stage_type == StageType.FILTERING

    def is_chunking_stage(self) -> bool:
        """是否为分块阶段"""
        return self.is_stage() and self.stage_type == StageType.CHUNKING

    def is_generation_stage(self) -> bool:
        """是否为生成阶段"""
        return self.is_stage() and self.stage_type == StageType.GENERATION

    def __str__(self) -> str:
        """字符串表示"""
        if self.is_content():
            return f"Content: {self.content}"
        elif self.is_stage():
            return f"Stage[{self.stage_type.value}]: {self.message}"
        elif self.is_start():
            return f"Start: {self.status}"
        elif self.is_end():
            return f"End: {self.status}"
        elif self.is_contexts():
            return f"Contexts: {len(self.contexts or [])} items"
        else:
            return f"Message[{self.event_type.value}]"


@dataclass
class RAGConfig:
    """
    RAG SDK全局配置

    配置 RAG 客户端的行为和参数。

    最简配置::

        config = RAGConfig(doc_dir="/path/to/docs")

    完整配置::

        config = RAGConfig(
            doc_dir="/path/to/docs",
            model="v3_chat",
            agentic=True,  # 使用 AgenticRAG
            product_mode="pro",  # Pro 模式
            rag_context_window_limit=100000,
            enable_hybrid_index=True,
            timeout=600,  # 10分钟超时
        )
    """

    # 文档目录（必需）
    doc_dir: str

    # 命令路径（可选，默认使用 'auto-coder.rag'）
    command_path: str = "auto-coder.rag"

    # 模型配置
    model: str = "v3_chat"

    # 模型配置文件路径
    model_file: str = ""

    # 超时配置（秒）
    timeout: int = 300  # 默认5分钟

    # RAG 配置参数
    rag_context_window_limit: int = 56000
    full_text_ratio: float = 0.7
    segment_ratio: float = 0.2
    rag_doc_filter_relevance: int = 0

    # 模式选择
    agentic: bool = False  # 是否使用 AgenticRAG
    product_mode: str = "lite"  # lite 或 pro

    # 索引配置
    enable_hybrid_index: bool = False
    disable_auto_window: bool = False
    disable_segment_reorder: bool = False

    # 可选模型配置
    recall_model: str = ""
    chunk_model: str = ""
    qa_model: str = ""
    emb_model: str = ""
    agentic_model: str = ""
    context_prune_model: str = ""

    # tokenizer 路径
    tokenizer_path: Optional[str] = None

    # 其他参数
    required_exts: str = ""
    ray_address: str = "auto"

    # 环境变量配置
    envs: Optional[RAGEnvVars] = None

    # Windows UTF-8 环境变量自动配置（默认 False）
    # 当为 True 且在 Windows 平台时，自动添加: PYTHONIOENCODING=utf-8, LANG=zh_CN.UTF-8, LC_ALL=zh_CN.UTF-8, CHCP=65001
    windows_utf8_env: bool = False


@dataclass
class RAGQueryOptions:
    """
    单次查询的配置选项

    用于覆盖全局配置的查询级别选项。

    示例::

        # 使用默认选项
        options = RAGQueryOptions()

        # 自定义选项
        options = RAGQueryOptions(
            output_format="json",
            agentic=True,  # 本次查询使用 AgenticRAG
            model="custom_model",
            timeout=600,  # 本次查询10分钟超时
        )
    """

    # 输出格式: text, json, stream-json
    output_format: str = "text"

    # 是否使用 AgenticRAG (覆盖全局配置)
    agentic: Optional[bool] = None

    # 产品模式 (覆盖全局配置)
    product_mode: Optional[str] = None

    # 模型 (覆盖全局配置)
    model: Optional[str] = None

    # 模型配置文件路径 (覆盖全局配置)
    model_file: Optional[str] = None

    # 超时时间（秒，覆盖全局配置）
    timeout: Optional[int] = None

    # 环境变量配置（覆盖全局配置）
    envs: Optional[RAGEnvVars] = None


@dataclass
class RAGResponse:
    """
    RAG 查询响应

    包含查询结果、上下文和元数据。

    示例::

        response = client.query_with_contexts("如何使用?")

        if response.success:
            print(f"答案: {response.answer}")
            print(f"参考了 {len(response.contexts)} 个文档")
        else:
            print(f"错误: {response.error}")
    """

    # 查询是否成功
    success: bool

    # 答案内容
    answer: str

    # 使用的上下文
    contexts: List[str] = field(default_factory=list)

    # 错误信息（如果有）
    error: Optional[str] = None

    # 元数据
    metadata: dict = field(default_factory=dict)

    @property
    def has_error(self) -> bool:
        """是否有错误"""
        return not self.success or self.error is not None

    @classmethod
    def success_response(
        cls,
        answer: str,
        contexts: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> "RAGResponse":
        """创建成功响应"""
        return cls(
            success=True,
            answer=answer,
            contexts=contexts or [],
            metadata=metadata or {},
        )

    @classmethod
    def error_response(cls, error: str) -> "RAGResponse":
        """创建错误响应"""
        return cls(success=False, answer="", error=error)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "answer": self.answer,
            "contexts": self.contexts,
            "error": self.error,
            "metadata": self.metadata,
        }


class RAGError(Exception):
    """RAG SDK基础异常类"""

    pass


class ValidationError(RAGError):
    """参数验证异常"""

    pass


class ExecutionError(RAGError):
    """执行异常"""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code
