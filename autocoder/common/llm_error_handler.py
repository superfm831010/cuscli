"""
LLM 调用错误处理模块

提供统一的 LLM 错误识别、分类和友好提示功能
"""

import re
from typing import Tuple, Optional
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class LLMErrorType:
    """LLM 错误类型枚举"""
    AUTHENTICATION = "authentication"  # 认证错误（API key 相关）
    NETWORK = "network"  # 网络连接错误
    TIMEOUT = "timeout"  # 请求超时
    RATE_LIMIT = "rate_limit"  # API 速率限制
    MODEL_NOT_FOUND = "model_not_found"  # 模型不存在
    INVALID_REQUEST = "invalid_request"  # 请求参数错误
    SERVER_ERROR = "server_error"  # 服务器错误（5xx）
    QUOTA_EXCEEDED = "quota_exceeded"  # 配额超限
    EMPTY_RESPONSE = "empty_response"  # 响应为空
    UNKNOWN = "unknown"  # 未知错误


class LLMErrorHandler:
    """LLM 错误处理器"""

    def __init__(self):
        self.console = Console()

    def classify_error(self, error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型（LLMErrorType 中的值）
        """
        error_msg = str(error).lower()

        # 认证错误
        if any(keyword in error_msg for keyword in [
            'api key', 'apikey', 'authentication', 'unauthorized',
            'invalid_api_key', '401', 'api_key'
        ]):
            return LLMErrorType.AUTHENTICATION

        # 网络连接错误
        if any(keyword in error_msg for keyword in [
            'connection', 'network', 'unreachable', 'timeout',
            'connect', 'dns', 'socket', 'refused', 'reset'
        ]):
            # 进一步判断是否是超时
            if 'timeout' in error_msg or 'timed out' in error_msg:
                return LLMErrorType.TIMEOUT
            return LLMErrorType.NETWORK

        # 速率限制
        if any(keyword in error_msg for keyword in [
            'rate limit', 'too many requests', '429',
            'rate_limit_exceeded', 'quota'
        ]):
            return LLMErrorType.RATE_LIMIT

        # 模型不存在
        if any(keyword in error_msg for keyword in [
            'model not found', 'model_not_found', 'invalid model',
            'does not exist', '404'
        ]):
            return LLMErrorType.MODEL_NOT_FOUND

        # 请求参数错误
        if any(keyword in error_msg for keyword in [
            'invalid request', 'bad request', '400',
            'validation error', 'invalid parameter'
        ]):
            return LLMErrorType.INVALID_REQUEST

        # 服务器错误
        if any(keyword in error_msg for keyword in [
            'server error', '500', '502', '503', '504',
            'internal server', 'service unavailable'
        ]):
            return LLMErrorType.SERVER_ERROR

        # 配额超限
        if any(keyword in error_msg for keyword in [
            'quota', 'insufficient', 'balance', 'credit'
        ]):
            return LLMErrorType.QUOTA_EXCEEDED

        # 响应为空
        if any(keyword in error_msg for keyword in [
            'nonetype', 'none', 'empty response', 'no response'
        ]):
            return LLMErrorType.EMPTY_RESPONSE

        return LLMErrorType.UNKNOWN

    def get_error_info(self, error_type: str, error: Exception) -> Tuple[str, str, list]:
        """
        获取错误信息、原因和解决方案

        Args:
            error_type: 错误类型
            error: 原始异常

        Returns:
            (标题, 详细描述, 解决方案列表)
        """
        error_messages = {
            LLMErrorType.AUTHENTICATION: (
                "API 密钥认证失败",
                "无法通过 API 密钥验证，请检查配置文件中的密钥是否正确。",
                [
                    "1. 检查配置文件中的 api_key 是否正确设置",
                    "2. 确认 API 密钥未过期且有足够权限",
                    "3. 如果使用环境变量，检查 ENV 配置是否正确",
                    "4. 验证 API 密钥格式是否符合提供商要求"
                ]
            ),
            LLMErrorType.NETWORK: (
                "网络连接失败",
                "无法连接到 API 服务器，请检查网络连接和代理设置。",
                [
                    "1. 检查网络连接是否正常",
                    "2. 如果使用代理，确认代理配置正确",
                    "3. 检查防火墙是否阻止了连接",
                    "4. 尝试访问 API 提供商的状态页面确认服务是否正常"
                ]
            ),
            LLMErrorType.TIMEOUT: (
                "请求超时",
                "API 请求超过了设置的等待时间，可能是网络延迟或模型响应较慢。",
                [
                    "1. 增加超时时间配置（如果支持）",
                    "2. 检查网络连接质量",
                    "3. 尝试使用更快的模型",
                    "4. 减少输入内容长度",
                    "5. 稍后重试"
                ]
            ),
            LLMErrorType.RATE_LIMIT: (
                "API 调用频率超限",
                "请求次数超过了 API 提供商的速率限制。",
                [
                    "1. 等待一段时间后重试（通常几分钟后自动恢复）",
                    "2. 减少并发请求数量",
                    "3. 考虑升级 API 套餐以获得更高限制",
                    "4. 在配置中添加请求间隔（如果支持）"
                ]
            ),
            LLMErrorType.MODEL_NOT_FOUND: (
                "模型不存在",
                "指定的模型名称不正确或该模型不可用。",
                [
                    "1. 检查配置文件中的模型名称是否正确",
                    "2. 确认该模型在您的 API 套餐中可用",
                    "3. 查看 API 提供商文档获取可用模型列表",
                    "4. 尝试使用默认模型"
                ]
            ),
            LLMErrorType.INVALID_REQUEST: (
                "请求参数错误",
                "发送给 API 的请求参数不符合要求。",
                [
                    "1. 检查输入内容的长度是否超过模型限制",
                    "2. 验证配置文件中的参数格式",
                    "3. 查看错误详情了解具体的参数问题",
                    "4. 参考 API 文档确认正确的参数格式"
                ]
            ),
            LLMErrorType.SERVER_ERROR: (
                "服务器错误",
                "API 服务器遇到内部错误，这通常是临时性问题。",
                [
                    "1. 稍等几分钟后重试",
                    "2. 查看 API 提供商的状态页面",
                    "3. 如果问题持续，联系 API 提供商支持",
                    "4. 考虑切换到备用模型（如果配置了）"
                ]
            ),
            LLMErrorType.QUOTA_EXCEEDED: (
                "配额或余额不足",
                "API 账户的配额已用完或余额不足。",
                [
                    "1. 检查 API 账户余额",
                    "2. 查看配额使用情况",
                    "3. 充值或升级 API 套餐",
                    "4. 等待配额重置（如果是按周期限制）"
                ]
            ),
            LLMErrorType.EMPTY_RESPONSE: (
                "响应为空",
                "模型返回了空响应或响应格式异常。",
                [
                    "1. 重试请求",
                    "2. 检查输入内容是否合法",
                    "3. 尝试使用不同的模型",
                    "4. 查看日志文件获取详细错误信息"
                ]
            ),
            LLMErrorType.UNKNOWN: (
                "未知错误",
                f"发生了未分类的错误: {str(error)[:200]}",
                [
                    "1. 查看日志文件获取详细错误信息",
                    "2. 检查所有配置项是否正确",
                    "3. 尝试重启应用",
                    "4. 如果问题持续，请报告此错误"
                ]
            )
        }

        return error_messages.get(
            error_type,
            error_messages[LLMErrorType.UNKNOWN]
        )

    def format_error_message(self, error: Exception, model_name: Optional[str] = None) -> str:
        """
        格式化错误消息为友好的文本

        Args:
            error: 异常对象
            model_name: 模型名称（可选）

        Returns:
            格式化的错误消息
        """
        error_type = self.classify_error(error)
        title, description, solutions = self.get_error_info(error_type, error)

        message = f"\n{'='*60}\n"
        message += f"❌ LLM 调用失败: {title}\n"
        message += f"{'='*60}\n\n"

        if model_name:
            message += f"📌 模型: {model_name}\n\n"

        message += f"💡 问题描述:\n{description}\n\n"

        message += f"🔧 解决方案:\n"
        for solution in solutions:
            message += f"   {solution}\n"

        message += f"\n📋 原始错误:\n{str(error)}\n"
        message += f"{'='*60}\n"

        return message

    def display_error_rich(self, error: Exception, model_name: Optional[str] = None):
        """
        使用 rich 库显示美化的错误信息

        Args:
            error: 异常对象
            model_name: 模型名称（可选）
        """
        error_type = self.classify_error(error)
        title, description, solutions = self.get_error_info(error_type, error)

        # 创建错误面板内容
        content = Text()

        if model_name:
            content.append(f"📌 模型: ", style="bold cyan")
            content.append(f"{model_name}\n\n", style="cyan")

        content.append("💡 问题描述:\n", style="bold yellow")
        content.append(f"{description}\n\n", style="white")

        content.append("🔧 解决方案:\n", style="bold green")
        for solution in solutions:
            content.append(f"   {solution}\n", style="white")

        content.append("\n📋 原始错误:\n", style="bold red")
        content.append(f"{str(error)}", style="red dim")

        # 显示面板
        panel = Panel(
            content,
            title=f"[bold red]❌ LLM 调用失败: {title}[/bold red]",
            border_style="red",
            expand=False
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print("\n")

    def log_error(self, error: Exception, model_name: Optional[str] = None,
                  context: Optional[dict] = None):
        """
        记录详细的错误信息到日志

        Args:
            error: 异常对象
            model_name: 模型名称（可选）
            context: 额外的上下文信息（可选）
        """
        error_type = self.classify_error(error)
        title, description, solutions = self.get_error_info(error_type, error)

        log_msg = f"\n{'='*60}\n"
        log_msg += f"LLM 调用失败 - {title}\n"
        log_msg += f"{'='*60}\n"
        log_msg += f"错误类型: {error_type}\n"

        if model_name:
            log_msg += f"模型名称: {model_name}\n"

        log_msg += f"描述: {description}\n"

        if context:
            log_msg += f"上下文: {context}\n"

        log_msg += f"建议解决方案:\n"
        for i, solution in enumerate(solutions, 1):
            log_msg += f"  {i}. {solution}\n"

        log_msg += f"原始错误: {str(error)}\n"
        log_msg += f"{'='*60}\n"

        logger.error(log_msg, exc_info=True)

    def handle_error(self, error: Exception, model_name: Optional[str] = None,
                     display_in_terminal: bool = True, log_to_file: bool = True,
                     context: Optional[dict] = None) -> str:
        """
        统一处理错误（显示 + 日志）

        Args:
            error: 异常对象
            model_name: 模型名称（可选）
            display_in_terminal: 是否在终端显示
            log_to_file: 是否记录到日志文件
            context: 额外的上下文信息（可选）

        Returns:
            错误类型
        """
        error_type = self.classify_error(error)

        # 显示错误
        if display_in_terminal:
            try:
                self.display_error_rich(error, model_name)
            except Exception as e:
                # 如果 rich 显示失败，回退到普通文本
                logger.warning(f"Rich 显示失败，使用普通文本: {e}")
                message = self.format_error_message(error, model_name)
                print(message)

        # 记录日志
        if log_to_file:
            self.log_error(error, model_name, context)

        return error_type


# 全局错误处理器实例
_global_error_handler = None


def get_error_handler() -> LLMErrorHandler:
    """获取全局错误处理器实例"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = LLMErrorHandler()
    return _global_error_handler


def handle_llm_error(error: Exception, model_name: Optional[str] = None,
                     display: bool = True, log: bool = True,
                     context: Optional[dict] = None) -> str:
    """
    便捷函数：处理 LLM 错误

    Args:
        error: 异常对象
        model_name: 模型名称（可选）
        display: 是否在终端显示
        log: 是否记录到日志
        context: 额外的上下文信息

    Returns:
        错误类型

    Example:
        try:
            response = llm.chat_oai(...)
        except Exception as e:
            handle_llm_error(e, model_name="gpt-4", context={"file": "test.py"})
    """
    handler = get_error_handler()
    return handler.handle_error(error, model_name, display, log, context)
