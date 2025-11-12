"""
MCP Tools Server Module

This module provides the McpServer class for handling MCP server operations
in a thread-safe manner. It manages requests and responses through async queues.
"""

import asyncio
from asyncio import Queue as AsyncQueue
import threading
import signal
import atexit
from typing import Union
from loguru import logger

from .hub import McpHub, MCP_BUILD_IN_SERVERS
from .executor import McpExecutor
from .installer import McpServerInstaller
from .types import (
    McpRequest, McpInstallRequest, McpRemoveRequest, McpListRequest,
    McpListRunningRequest, McpRefreshRequest, McpServerInfoRequest,
    McpResponse, ServerInfo, InstallResult, RemoveResult, ListResult,
    ListRunningResult, RefreshResult, QueryResult, ErrorResult,
    StringResult, MarketplaceAddRequest, MarketplaceAddResult,
    MarketplaceUpdateRequest, MarketplaceUpdateResult, MarketplaceMCPServerItem
)
from autocoder.utils.llms import get_single_llm
from autocoder.chat_auto_coder_lang import get_message_with_format


class McpServer:
    """
    MCP Server handling class that manages MCP operations in a thread-safe manner.
    
    This class provides an async interface for MCP operations while maintaining
    thread safety through proper queue management.
    """
    
    def __init__(self):
        self._request_queue = AsyncQueue()
        self._response_queue = AsyncQueue()
        self._running = False
        self._task = None
        self._loop = None
        self._thread = None
        self._installer = McpServerInstaller()
        self._shutdown_event = threading.Event()

    def start(self):
        """Start the MCP server in a separate thread"""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the MCP server"""
        if not self._running:
            return
            
        self._running = False
        self._shutdown_event.set()
        
        if self._loop and self._loop.is_running():
            # Cancel the task gracefully
            if self._task and not self._task.done():
                self._loop.call_soon_threadsafe(self._task.cancel)
            
            # Send None to break the request processing loop
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._request_queue.put(None), self._loop
                )
                future.result(timeout=1.0)
            except Exception:
                pass
            
            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                logger.warning("MCP server thread did not stop gracefully")

    def _run_event_loop(self):
        """Run the event loop in the dedicated thread"""
        if self._loop is None:
            return
            
        asyncio.set_event_loop(self._loop)
        
        try:
            self._task = self._loop.create_task(self._process_request())
            self._loop.run_forever()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in MCP server event loop")
        except Exception as e:
            logger.error(f"Error in MCP server event loop: {e}")
        finally:
            # Clean up
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    self._loop.run_until_complete(self._task)
                except asyncio.CancelledError:
                    pass
            
            # Close the loop
            try:
                self._loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")

    async def _process_request(self):
        """
        Process incoming requests and generate responses
        """
        hub = McpHub()
        
        try:
            # May block if there are abnormal contents in mcp settings.json
            await hub.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize MCP hub: {e}")
            return

        while self._running:
            try:
                # Use timeout to allow checking _running flag
                try:
                    request = await asyncio.wait_for(
                        self._request_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                    
                if request is None:
                    break

                if isinstance(request, McpInstallRequest):
                    response = await self._installer.install_server(request, hub)
                    await self._response_queue.put(response)

                elif isinstance(request, McpRemoveRequest):
                    try:
                        await hub.remove_server_config(request.server_name)
                        await self._response_queue.put(McpResponse(
                            result=get_message_with_format("mcp_remove_success", result=request.server_name),
                            raw_result=RemoveResult(
                                success=True,
                                server_name=request.server_name
                            )
                        ))
                    except Exception as e:
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("mcp_remove_error", error=str(e)),
                            raw_result=RemoveResult(
                                success=False,
                                server_name=request.server_name,
                                error=str(e)
                            )
                        ))

                elif isinstance(request, McpListRequest):
                    try:
                        # Get built-in servers
                        builtin_servers = []
                        for name, config in MCP_BUILD_IN_SERVERS.items():
                            marketplace_item = MarketplaceMCPServerItem(
                                name=name,
                                description=f"Built-in: {name}",
                                mcp_type="command",
                                command=config.get("command") or "",
                                args=config.get("args", []),
                                env=config.get("env", {})
                            )
                            builtin_servers.append(marketplace_item)

                        # Get external servers
                        external_servers = self._installer.get_mcp_external_servers()
                        external_items = []
                        for server in external_servers:
                            marketplace_item = MarketplaceMCPServerItem(
                                name=server.name,
                                description=server.description,
                                mcp_type="command"
                            )
                            external_items.append(marketplace_item)

                        # Get marketplace items
                        marketplace_items = hub.get_marketplace_items()
                        
                        # Combine results for display
                        result_sections = []
                        
                        if builtin_servers:
                            builtin_title = get_message_with_format("mcp_list_builtin_title")
                            builtin_list = [f"- {item.name}" for item in builtin_servers]
                            result_sections.append(builtin_title)
                            result_sections.append("\n".join(builtin_list))
                            
                        if external_items:
                            external_title = get_message_with_format("mcp_list_external_title")
                            external_list = [f"- {item.name} ({item.description})" for item in external_items]
                            result_sections.append(external_title)
                            result_sections.append("\n".join(external_list))
                            
                        if marketplace_items:
                            marketplace_title = get_message_with_format("mcp_list_marketplace_title")
                            marketplace_list = [f"- {item.name} ({item.description})" for item in marketplace_items]
                            result_sections.append(marketplace_title)
                            result_sections.append("\n".join(marketplace_list))
                        
                        result = "\n\n".join(result_sections)
                        
                        # Create raw result with MarketplaceMCPServerItem objects
                        raw_result = ListResult(
                            builtin_servers=builtin_servers,
                            external_servers=external_items,
                            marketplace_items=marketplace_items
                        )

                        await self._response_queue.put(McpResponse(result=result, raw_result=raw_result))
                    except Exception as e:
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("mcp_list_builtin_error", error=str(e)),
                            raw_result=ListResult(error=str(e))
                        ))

                elif isinstance(request, McpServerInfoRequest):
                    try:
                        llm = get_single_llm(request.model, product_mode=request.product_mode or "lite")
                        if llm is None:
                            raise ValueError("Failed to get LLM instance")
                        mcp_executor = McpExecutor(hub, llm)
                        result = mcp_executor.get_connected_servers_info()
                        await self._response_queue.put(McpResponse(
                            result=result, 
                            raw_result=StringResult(result=result)
                        ))
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("mcp_server_info_error", error=str(e)),
                            raw_result=ErrorResult(error=str(e))
                        ))

                elif isinstance(request, McpListRunningRequest):
                    try:
                        servers = hub.get_servers()
                        running_servers = "\n".join([f"- {server.name}" for server in servers])
                        result = running_servers if running_servers else ""
                        await self._response_queue.put(McpResponse(
                            result=result,
                            raw_result=ListRunningResult(
                                servers=[ServerInfo(name=server.name) for server in servers]
                            )
                        ))
                    except Exception as e:
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("mcp_list_running_error", error=str(e)),
                            raw_result=ListRunningResult(error=str(e))
                        ))

                elif isinstance(request, McpRefreshRequest):
                    try:
                        if request.name:
                            await hub.refresh_server_connection(request.name)
                        else:
                            await hub.initialize()
                        await self._response_queue.put(McpResponse(
                            result=get_message_with_format("mcp_refresh_success"),
                            raw_result=RefreshResult(
                                success=True,
                                name=request.name
                            )
                        ))
                    except Exception as e:
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("mcp_refresh_error", error=str(e)),
                            raw_result=RefreshResult(
                                success=False,
                                name=request.name,
                                error=str(e)
                            )
                        ))
                
                elif isinstance(request, MarketplaceAddRequest):
                    try:
                        # Create a MarketplaceMCPServerItem from the request
                        item = MarketplaceMCPServerItem(
                            name=request.name,
                            description=request.description,
                            mcp_type=request.mcp_type,
                            command=request.command or "",
                            args=request.args or [],
                            env=request.env or {},
                            url=request.url or ""
                        )
                        
                        # Add the item to the marketplace
                        success = await hub.add_marketplace_item(item)
                        
                        if success:
                            await self._response_queue.put(McpResponse(
                                result=get_message_with_format("marketplace_add_success", name=request.name),
                                raw_result=MarketplaceAddResult(
                                    success=True,
                                    name=request.name
                                )
                            ))
                        else:
                            await self._response_queue.put(McpResponse(
                                result="", 
                                error=get_message_with_format("marketplace_add_error", name=request.name),
                                raw_result=MarketplaceAddResult(
                                    success=False,
                                    name=request.name,
                                    error=f"Failed to add marketplace item: {request.name}"
                                )
                            ))
                    except Exception as e:
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("marketplace_add_error", name=request.name, error=str(e)),
                            raw_result=MarketplaceAddResult(
                                success=False,
                                name=request.name,
                                error=str(e)
                            )
                        ))

                elif isinstance(request, MarketplaceUpdateRequest):
                    try:
                        # Create a MarketplaceMCPServerItem from the request
                        item = MarketplaceMCPServerItem(
                            name=request.name,
                            description=request.description,
                            mcp_type=request.mcp_type,
                            command=request.command or "",
                            args=request.args or [],
                            env=request.env or {},
                            url=request.url or ""
                        )
                        
                        # Update the item in the marketplace
                        success = await hub.update_marketplace_item(request.name, item)
                        
                        if success:
                            await self._response_queue.put(McpResponse(
                                result=get_message_with_format("marketplace_update_success", name=request.name),
                                raw_result=MarketplaceUpdateResult(
                                    success=True,
                                    name=request.name
                                )
                            ))
                        else:
                            await self._response_queue.put(McpResponse(
                                result="", 
                                error=get_message_with_format("marketplace_update_error", name=request.name),
                                raw_result=MarketplaceUpdateResult(
                                    success=False,
                                    name=request.name,
                                    error=f"Failed to update marketplace item: {request.name}"
                                )
                            ))
                    except Exception as e:
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("marketplace_update_error", name=request.name, error=str(e)),
                            raw_result=MarketplaceUpdateResult(
                                success=False,
                                name=request.name,
                                error=str(e)
                            )
                        ))

                else:
                    # Handle general MCP requests
                    if not request.query.strip():
                        await self._response_queue.put(McpResponse(
                            result="", 
                            error=get_message_with_format("mcp_query_empty"),
                            raw_result=QueryResult(
                                success=False,
                                error="Empty query"
                            )
                        ))
                        continue

                    llm = get_single_llm(request.model, product_mode=request.product_mode)
                    mcp_executor = McpExecutor(hub, llm)
                    conversations = [{"role": "user", "content": request.query}]
                    _, results = await mcp_executor.run(conversations)

                    if not results:
                        await self._response_queue.put(McpResponse(
                            result=get_message_with_format("mcp_error_title"),
                            error="No results",
                            raw_result=QueryResult(
                                success=False,
                                error="No results"
                            )
                        ))
                    else:
                        results_str = "\n\n".join(
                            mcp_executor.format_mcp_result(result) for result in results)
                        await self._response_queue.put(McpResponse(
                            result=get_message_with_format("mcp_response_title") + "\n" + results_str,
                            raw_result=QueryResult(
                                success=True,
                                results=results
                            )
                        ))
            except asyncio.CancelledError:
                logger.info("MCP request processing was cancelled")
                break
            except Exception as e:
                logger.error(f"Error in MCP request processing: {e}")
                try:
                    await self._response_queue.put(McpResponse(
                        result="", 
                        error=get_message_with_format("mcp_error_title") + ": " + str(e),
                        raw_result=ErrorResult(error=str(e))
                    ))
                except Exception:
                    pass
        
        # Clean up hub connections
        try:
            await hub.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down MCP hub: {e}")

    def send_request(self, request: Union[McpRequest, McpServerInfoRequest]) -> McpResponse:
        """
        Send a request to the MCP server and wait for response
        
        Args:
            request: The request to send
            
        Returns:
            McpResponse: The response from the server
        """
        if not self._running:
            self.start()
        
        async def _send():
            await self._request_queue.put(request)
            return await self._response_queue.get()
        
        if self._loop is None:
            return McpResponse(result="", error="Event loop not available")
        
        try:
            future = asyncio.run_coroutine_threadsafe(_send(), self._loop)
            return future.result(timeout=30.0)  # Add timeout to prevent hanging
        except asyncio.TimeoutError:
            return McpResponse(result="", error="Request timeout")
        except Exception as e:
            return McpResponse(result="", error=f"Request failed: {str(e)}")


# Global MCP server instance
_mcp_server = None


def get_mcp_server():
    """Get the global MCP server instance"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = McpServer()
        _mcp_server.start()
        # Register cleanup function
        atexit.register(_cleanup_mcp_server)
    return _mcp_server


def _cleanup_mcp_server():
    """Clean up the global MCP server instance"""
    global _mcp_server
    if _mcp_server is not None:
        logger.info("Cleaning up MCP server...")
        _mcp_server.stop()
        _mcp_server = None
