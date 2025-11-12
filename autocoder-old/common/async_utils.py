"""
Utility functions for handling async/sync conversions consistently.
"""

import asyncio
import concurrent.futures
from typing import TypeVar, Callable, Awaitable, Any
from functools import wraps

T = TypeVar('T')


def run_async_in_sync(async_func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    """
    Run an async function in a synchronous context.
    
    This function handles both cases:
    1. When called from within an existing event loop (runs in a thread)
    2. When called from a synchronous context (creates new event loop)
    
    Args:
        async_func: The async function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the async function
    """
    def run_in_new_loop():
        """Run the async function in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(async_func(*args, **kwargs))
            # Wait for all tasks to complete
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            return result
        finally:
            # Cancel any remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
    
    try:
        # Check if we're in an async context
        asyncio.get_running_loop()
        # We're in an async context, run in a thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            return future.result()
    except RuntimeError:
        # No event loop running, we can run directly
        return run_in_new_loop()


def async_to_sync(async_func: Callable[..., Awaitable[T]]) -> Callable[..., T]:
    """
    Decorator to create a synchronous version of an async function.
    
    Usage:
        @async_to_sync
        async def my_async_func():
            await asyncio.sleep(1)
            return "done"
            
        # Can now be called synchronously
        result = my_async_func()
    """
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        return run_async_in_sync(async_func, *args, **kwargs)
    return wrapper


class AsyncSyncMixin:
    """
    Mixin class that provides automatic sync versions of async methods.
    
    For any async method `foo`, this mixin automatically provides a `foo_sync` method.
    """
    
    def __getattr__(self, name: str) -> Any:
        if name.endswith('_sync'):
            async_name = name[:-5]  # Remove '_sync' suffix
            async_method = getattr(self, async_name, None)
            
            if async_method and asyncio.iscoroutinefunction(async_method):
                # Create a sync wrapper
                def sync_wrapper(*args, **kwargs):
                    return run_async_in_sync(async_method, *args, **kwargs)
                
                # Cache it for future calls
                setattr(self, name, sync_wrapper)
                return sync_wrapper
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") 