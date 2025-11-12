"""统一的命令处理器"""

import asyncio
from typing import TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor
from autocoder.common.global_cancel import global_cancel, CancelRequestedException
from autocoder.events.event_manager_singleton import gengerate_event_file_path
from autocoder.auto_coder_runner import configure
from autocoder.inner.agentic import RunAgentic
from autocoder.common.v2.agent.agentic_edit_types import ConversationAction
from ..models import ConversationBuffer

if TYPE_CHECKING:
    from ..app import AutoCoderChatApp


class CommandHandler:
    """处理所有命令的统一处理器"""

    def __init__(
        self, conversation_buffer: ConversationBuffer, app_instance: "AutoCoderChatApp"
    ):
        self.conversation_buffer = conversation_buffer
        self.app = app_instance
        # 创建线程池用于执行同步生成器
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="agentic-worker"
        )

    async def handle_command(self, command: str):
        """处理命令"""
        try:
            # 退出命令
            if command in ["exit", "/exit"]:
                self.app.exit()

            # /auto 命令或直接输入查询
            elif command.startswith("/auto") or not command.startswith("/"):
                # 处理 /auto 命令或直接的查询
                if not command:
                    self.conversation_buffer.add_system_message(
                        "Please provide a query"
                    )
                else:
                    await self._execute_auto_command(command)

            # 未知命令
            else:
                self.conversation_buffer.add_system_message(
                    f"Unknown command: {command}. Use /auto <query> or /exit"
                )

        except Exception as e:
            self.conversation_buffer.add_system_message(f"Error: {str(e)}")

    async def _execute_auto_command(self, query: str):
        """执行 /auto 命令（使用线程池避免阻塞事件循环）"""
        event_file, _ = gengerate_event_file_path()
        global_cancel.register_token(event_file)
        configure(f"event_file:{event_file}")

        self.app.invalidate()

        # 创建事件队列用于线程和协程之间通信
        event_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def run_agentic_in_thread():
            """在线程中运行同步生成器"""
            try:
                agentic = RunAgentic()
                for event in agentic.run_with_events(
                    query=query,
                    pre_commit=False,
                    post_commit=False,
                    pr=False,
                    cancel_token=event_file,
                    conversation_action=ConversationAction.RESUME,
                ):
                    # 将事件放入队列（线程安全）
                    asyncio.run_coroutine_threadsafe(
                        event_queue.put(("event", event)), loop
                    )
            except CancelRequestedException:
                # 取消请求异常
                asyncio.run_coroutine_threadsafe(
                    event_queue.put(("cancelled", None)), loop
                )
            except Exception as e:
                # 其他异常
                asyncio.run_coroutine_threadsafe(event_queue.put(("error", e)), loop)
            finally:
                # 发送结束信号
                asyncio.run_coroutine_threadsafe(event_queue.put(("done", None)), loop)

        try:
            # 在线程池中启动生成器
            loop.run_in_executor(self.executor, run_agentic_in_thread)

            # 异步消费事件队列
            while True:
                msg_type, data = await event_queue.get()

                if msg_type == "event":
                    # 处理事件
                    self.conversation_buffer.add_event(data)
                    self.app.invalidate()
                    # 让出控制权，确保 Ctrl+C 能被及时处理
                    await asyncio.sleep(0)

                elif msg_type == "cancelled":
                    # 任务被取消
                    self.conversation_buffer.add_system_message("Task cancelled")
                    self.app.invalidate()
                    break

                elif msg_type == "error":
                    # 发生错误
                    self.conversation_buffer.add_system_message(f"Error: {str(data)}")
                    self.app.invalidate()
                    break

                elif msg_type == "done":
                    # 正常结束
                    break

        except Exception as e:
            self.conversation_buffer.add_system_message(f"Error: {str(e)}")
        finally:
            global_cancel.reset_token(event_file)
            self.app.invalidate()
