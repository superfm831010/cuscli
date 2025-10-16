"""
模型连通性测试工具

提供测试 LLM 模型连接是否正常的功能
"""

import asyncio
import sys
from typing import Dict, Tuple, Optional, Union
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

import byzerllm

from .schema import LLMModel, DEFAULT_API_KEY
from .factory import LLMFactory


class ModelConnectionTester:
    """模型连通性测试器"""

    # 测试用的简单消息
    TEST_MESSAGE = "Hello"
    # 超时时间（秒）
    TIMEOUT_SECONDS = 10

    def __init__(self, console: Optional[Console] = None):
        """
        初始化测试器

        Args:
            console: Rich Console 对象，如果不提供则创建新的
        """
        self.console = console or Console()

    def test_connection(
        self,
        model_config: Union[Dict, LLMModel],
        product_mode: str = "lite",
        show_progress: bool = True
    ) -> Tuple[bool, str]:
        """
        测试模型连接

        Args:
            model_config: 模型配置（字典或 LLMModel 对象）
            product_mode: 产品模式 ("lite" 或 "pro")
            show_progress: 是否显示进度提示

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息或成功消息)
        """
        # 转换为 LLMModel 对象
        if isinstance(model_config, dict):
            try:
                model = LLMModel(**model_config)
            except Exception as e:
                return False, f"模型配置格式错误: {str(e)}"
        else:
            model = model_config

        # 显示进度
        if show_progress:
            spinner = Spinner("dots", text="正在测试模型连接...")
            with Live(spinner, console=self.console, refresh_per_second=10):
                return self._do_test(model, product_mode)
        else:
            return self._do_test(model, product_mode)

    def _do_test(self, model: LLMModel, product_mode: str) -> Tuple[bool, str]:
        """
        执行实际的测试

        Args:
            model: LLM 模型配置
            product_mode: 产品模式

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 1. 验证基本配置
            if not model.model_name:
                return False, "模型名称不能为空"

            if not model.base_url:
                return False, "API地址不能为空"

            # 2. 检查 API Key
            api_key = model.get_api_key()
            if not api_key:
                return False, "未配置 API Key"

            # 如果使用默认Key，跳过测试
            if api_key == DEFAULT_API_KEY:
                return True, "模型不需要 API Key，跳过连接测试"

            # 3. 创建 LLM 实例
            try:
                llm = LLMFactory.create_llm(model, product_mode)
            except Exception as e:
                return False, f"创建 LLM 实例失败: {str(e)}"

            # 4. 尝试发送测试消息
            try:
                # 使用 asyncio 来支持超时
                if sys.platform == 'win32':
                    # Windows 平台需要特殊处理事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            self._async_test_chat(llm)
                        )
                    finally:
                        loop.close()
                else:
                    # Unix/Linux 平台
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    result = loop.run_until_complete(
                        self._async_test_chat(llm)
                    )

                return result

            except asyncio.TimeoutError:
                return False, f"连接超时（超过 {self.TIMEOUT_SECONDS} 秒）"
            except Exception as e:
                error_msg = str(e)

                # 针对常见错误提供更友好的提示
                if "401" in error_msg or "Unauthorized" in error_msg:
                    return False, "API Key 无效或未授权"
                elif "404" in error_msg or "Not Found" in error_msg:
                    return False, f"模型 '{model.model_name}' 不存在或 API 地址错误"
                elif "timeout" in error_msg.lower():
                    return False, "网络连接超时，请检查网络或 API 地址"
                elif "connection" in error_msg.lower():
                    return False, "无法连接到 API 服务器，请检查 API 地址"
                else:
                    return False, f"测试失败: {error_msg}"

        except Exception as e:
            return False, f"测试过程出错: {str(e)}"

    async def _async_test_chat(self, llm: Union[byzerllm.ByzerLLM, byzerllm.SimpleByzerLLM]) -> Tuple[bool, str]:
        """
        异步测试聊天功能

        Args:
            llm: LLM 实例

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 设置超时
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm.chat_oai,
                    conversations=[{
                        "role": "user",
                        "content": self.TEST_MESSAGE
                    }]
                ),
                timeout=self.TIMEOUT_SECONDS
            )

            # 检查响应
            if response and len(response) > 0:
                output = response[0].output if hasattr(response[0], 'output') else str(response[0])
                if output:
                    return True, f"连接成功! 响应: {output[:50]}{'...' if len(output) > 50 else ''}"
                else:
                    return False, "API 返回空响应"
            else:
                return False, "API 返回无效响应"

        except Exception as e:
            raise  # 重新抛出异常让外层处理


def test_model_connection_simple(
    model_config: Union[Dict, LLMModel],
    product_mode: str = "lite"
) -> bool:
    """
    简单的连通性测试函数（只返回是否成功）

    Args:
        model_config: 模型配置
        product_mode: 产品模式

    Returns:
        bool: 是否成功
    """
    tester = ModelConnectionTester(console=Console())
    success, _ = tester.test_connection(model_config, product_mode, show_progress=False)
    return success
