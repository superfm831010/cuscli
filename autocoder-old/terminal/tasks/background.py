"""后台任务：监控全局状态或执行其他后台逻辑"""

import asyncio
from pathlib import Path


async def background_task(stop_event: asyncio.Event, session=None, debug=False):
    """后台任务：可以用于监控系统状态、清理任务等"""
    counter = 0
    toolbar_refresh_counter = 0
    last_async_task_count = 0

    # 配置刷新频率（秒）
    TOOLBAR_REFRESH_INTERVAL = 5  # 默认5秒刷新一次
    FAST_REFRESH_INTERVAL = 1  # 有异步任务时1秒刷新一次

    while not stop_event.is_set():
        try:
            # 检查是否有需要处理的后台任务
            # 这里可以添加系统监控逻辑
            counter += 1
            toolbar_refresh_counter += 1

            # 检查当前异步任务状态，决定刷新频率
            current_async_task_count = 0
            try:
                from autocoder.sdk.async_runner.task_metadata import (
                    TaskMetadataManager,
                )

                async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
                meta_dir = async_agent_dir / "meta"

                if meta_dir.exists():
                    metadata_manager = TaskMetadataManager(str(meta_dir))
                    summary = metadata_manager.get_task_summary()
                    current_async_task_count = summary.get("running", 0)
            except Exception:
                # 静默处理异常
                pass

            # 智能刷新：有异步任务时更频繁刷新，无任务时降低刷新频率
            should_refresh = False
            if current_async_task_count > 0:
                # 有异步任务时，每秒刷新
                should_refresh = toolbar_refresh_counter >= FAST_REFRESH_INTERVAL
            else:
                # 无异步任务时，每5秒刷新
                should_refresh = toolbar_refresh_counter >= TOOLBAR_REFRESH_INTERVAL

            # 任务数量变化时立即刷新
            if current_async_task_count != last_async_task_count:
                should_refresh = True
                last_async_task_count = current_async_task_count

            # 执行工具栏刷新
            if should_refresh and session and hasattr(session, "app"):
                try:
                    session.app.invalidate()
                    toolbar_refresh_counter = 0
                except Exception:
                    # 静默处理刷新异常，不影响后台任务运行
                    pass

            # 每60秒执行一次清理
            if counter % 60 == 0:
                # 执行一些后台清理任务
                pass

            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            # 后台任务出错时，不要让整个应用崩溃
            if debug:
                print(f"Background task error: {e}")
            await asyncio.sleep(5)  # 出错后等待5秒再继续
