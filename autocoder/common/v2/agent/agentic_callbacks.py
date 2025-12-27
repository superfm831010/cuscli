from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from loguru import logger


class AgenticCallbackPoint(str, Enum):
    """
    枚举类，定义所有可用的回调点
    """

    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    CONVERSATION_MESSAGE_APPENDED = "conversation_message_appended"
    PRE_TOOL_CALL = "pre_tool_call"
    POST_TOOL_CALL = "post_tool_call"
    API_REQUEST_START = "api_request_start"
    API_REQUEST_END = "api_request_end"
    TOOL_GENERATED_STARTED = "tool_generated_started"
    TOOL_GENERATED_END = "tool_generated_end"
    PRE_RULES_LOADED = "pre_rules_loaded"
    POST_RULES_LOADED = "post_rules_loaded"
    PRE_LLM_FRIENDLY_PACKAGES_LOADED = "pre_llm_friendly_packages_loaded"
    POST_LLM_FRIENDLY_PACKAGES_LOADED = "post_llm_friendly_packages_loaded"
    PRE_TOOLS_LOADED = "pre_tools_loaded"
    POST_TOOLS_LOADED = "post_tools_loaded"
    PRE_CONVERSATION_RESUMED = "pre_conversation_resumed"
    POST_CONVERSATION_RESUMED = "post_conversation_resumed"


class AgenticContext(BaseModel):
    """
    回调函数的上下文类，目前保持为空，未来可以扩展
    """

    # 目前保持为空，未来可以添加需要的上下文信息
    # 例如：conversation_id, user_id, session_info 等
    pass


# 定义回调函数的类型签名（支持可选的 payload 参数）
AgenticCallbackFunction = Callable[[AgenticContext, Optional[Dict[str, Any]]], None]


class AgenticCallBacks(BaseModel):
    """
    Agentic 回调管理器

    提供回调点注册和执行功能，支持多个回调函数注册到同一个回调点。
    使用 Pydantic 确保强类型安全。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    # 使用私有属性存储回调函数映射
    _callbacks: Dict[AgenticCallbackPoint, List[AgenticCallbackFunction]] = PrivateAttr(
        default_factory=dict
    )

    def __init__(self, **data):
        super().__init__(**data)
        # 初始化所有回调点的空列表
        for callback_point in AgenticCallbackPoint:
            if callback_point not in self._callbacks:
                self._callbacks[callback_point] = []

    def register(
        self,
        callback_point: AgenticCallbackPoint,
        callback_func: AgenticCallbackFunction,
    ) -> bool:
        """
        注册回调函数到指定的回调点

        Args:
            callback_point: 回调点枚举值
            callback_func: 回调函数，签名为 (context: AgenticContext) -> None

        Returns:
            bool: 注册成功返回 True，失败返回 False
        """
        try:
            if callback_point not in self._callbacks:
                self._callbacks[callback_point] = []

            # 检查函数是否已经注册，避免重复注册
            if callback_func not in self._callbacks[callback_point]:
                self._callbacks[callback_point].append(callback_func)
                return True
            else:
                logger.warning(f"回调函数已存在于 {callback_point.value}")
                return False

        except Exception as e:
            logger.error(f"注册回调函数失败: {e}")
            return False

    def unregister(
        self,
        callback_point: AgenticCallbackPoint,
        callback_func: AgenticCallbackFunction,
    ) -> bool:
        """
        从指定回调点注销回调函数

        Args:
            callback_point: 回调点枚举值
            callback_func: 要注销的回调函数

        Returns:
            bool: 注销成功返回 True，失败返回 False
        """
        try:
            if (
                callback_point in self._callbacks
                and callback_func in self._callbacks[callback_point]
            ):
                self._callbacks[callback_point].remove(callback_func)
                return True
            else:
                logger.warning(f"在 {callback_point.value} 中未找到要注销的回调函数")
                return False

        except Exception as e:
            logger.error(f"注销回调函数失败: {e}")
            return False

    def execute_callbacks(
        self,
        callback_point: AgenticCallbackPoint,
        context: Optional[AgenticContext] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> List[Exception]:
        """
        执行指定回调点的所有回调函数

        Args:
            callback_point: 回调点枚举值
            context: 回调上下文，如果为 None 则创建空的上下文
            payload: 可选的载荷数据，传递给回调函数

        Returns:
            List[Exception]: 执行过程中发生的异常列表，空列表表示全部成功
        """
        if context is None:
            context = AgenticContext()

        errors = []

        if callback_point not in self._callbacks:
            return errors

        callbacks = self._callbacks[callback_point]

        for i, callback_func in enumerate(callbacks):
            try:
                # 尝试使用新签名（支持 payload）
                callback_func(context, payload)
            except TypeError as e:
                # 向后兼容：如果是参数错误，尝试使用旧签名（仅 context）
                if "positional argument" in str(e) or "arguments" in str(e):
                    try:
                        callback_func(context)
                        logger.debug(
                            f"回调函数 {callback_func.__name__ if hasattr(callback_func, '__name__') else 'unknown'} 使用旧签名（仅 context 参数）"
                        )
                    except Exception as fallback_error:
                        logger.error(
                            f"回调函数执行失败（尝试旧签名后仍失败）: {fallback_error}"
                        )
                        errors.append(fallback_error)
                else:
                    # 非参数数量问题的 TypeError，直接记录
                    errors.append(e)
            except Exception as e:
                errors.append(e)

        return errors

    def get_callback_count(self, callback_point: AgenticCallbackPoint) -> int:
        """
        获取指定回调点注册的回调函数数量

        Args:
            callback_point: 回调点枚举值

        Returns:
            int: 注册的回调函数数量
        """
        return len(self._callbacks.get(callback_point, []))

    def get_all_callback_counts(self) -> Dict[str, int]:
        """
        获取所有回调点的回调函数数量

        Returns:
            Dict[str, int]: 回调点名称到回调函数数量的映射
        """
        return {
            callback_point.value: len(callbacks)
            for callback_point, callbacks in self._callbacks.items()
        }

    def clear_callbacks(self, callback_point: AgenticCallbackPoint) -> int:
        """
        清除指定回调点的所有回调函数

        Args:
            callback_point: 回调点枚举值

        Returns:
            int: 清除的回调函数数量
        """
        if callback_point in self._callbacks:
            count = len(self._callbacks[callback_point])
            self._callbacks[callback_point].clear()
            logger.debug(f"已清除 {callback_point.value} 的 {count} 个回调函数")
            return count
        return 0

    def clear_all_callbacks(self) -> int:
        """
        清除所有回调点的回调函数

        Returns:
            int: 清除的回调函数总数量
        """
        total_count = 0
        for callback_point in AgenticCallbackPoint:
            total_count += self.clear_callbacks(callback_point)

        logger.debug(f"已清除所有回调函数，总计 {total_count} 个")
        return total_count

    def has_callbacks(self, callback_point: AgenticCallbackPoint) -> bool:
        """
        检查指定回调点是否有注册的回调函数

        Args:
            callback_point: 回调点枚举值

        Returns:
            bool: 有回调函数返回 True，否则返回 False
        """
        return self.get_callback_count(callback_point) > 0


# 创建全局回调管理器实例
_global_callbacks = AgenticCallBacks()


def get_global_callbacks() -> AgenticCallBacks:
    """
    获取全局回调管理器实例

    Returns:
        AgenticCallBacks: 全局回调管理器实例
    """
    return _global_callbacks


def register_global_callback(
    callback_point: AgenticCallbackPoint, callback_func: AgenticCallbackFunction
) -> bool:
    """
    注册回调函数到全局回调管理器

    Args:
        callback_point: 回调点枚举值
        callback_func: 回调函数

    Returns:
        bool: 注册成功返回 True，失败返回 False
    """
    return _global_callbacks.register(callback_point, callback_func)


def execute_global_callbacks(
    callback_point: AgenticCallbackPoint,
    context: Optional[AgenticContext] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> List[Exception]:
    """
    执行全局回调管理器中指定回调点的所有回调函数

    Args:
        callback_point: 回调点枚举值
        context: 回调上下文
        payload: 可选的载荷数据

    Returns:
        List[Exception]: 执行过程中发生的异常列表
    """
    return _global_callbacks.execute_callbacks(callback_point, context, payload)
