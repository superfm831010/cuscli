"""
Conversation Message IDs Write Tool Resolver

This resolver handles writing conversation message IDs configurations for pruning.
It integrates with the pruner module to store message ID specifications along with
the current conversation ID, supporting create, append, and delete actions.
"""

import os
from typing import Optional
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import ConversationMessageIdsWriteTool, ToolResult
from autocoder.common import AutoCoderArgs
from autocoder.common.pruner import get_conversation_message_ids_api,ConversationMessageIdsAPI
from autocoder.common.international import get_message
from loguru import logger
import typing

from autocoder.rag.lang import get_message_with_format

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ConversationMessageIdsWriteToolResolver(BaseToolResolver):
    """
    Resolver for the ConversationMessageIdsWriteTool.
    
    This resolver handles writing conversation message IDs configurations that specify
    which messages should be deleted during conversation pruning.
    Supports create, append, and delete actions.
    """
    
    def __init__(self, agent: 'AgenticEdit', tool: ConversationMessageIdsWriteTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool = tool

    def resolve(self) -> ToolResult:
        """
        Write conversation message IDs configuration.
        
        Returns:
            ToolResult with success status and configuration details
        """
        try:
            # Validate action parameter
            valid_actions = ["create", "append", "delete"]
            if self.tool.action not in valid_actions:
                return ToolResult(
                    success=False,
                    message=get_message_with_format("conversation_message_ids_invalid_action", action=self.tool.action),
                    content={
                        "error_type": "invalid_action",
                        "valid_actions": valid_actions,
                        "provided_action": self.tool.action
                    }
                )

            # Get current conversation ID            
            conversation_id = self.agent.conversation_config.conversation_id
            
            if not conversation_id:
                return ToolResult(
                    success=False,
                    message=get_message("conversation_message_ids_no_conversation"),
                    content={
                        "error_type": "no_conversation_id",
                        "message": get_message("conversation_message_ids_no_conversation")
                    }
                )
            
            # Get message IDs API
            message_ids_api = get_conversation_message_ids_api(
                storage_dir=self.args.range_storage_dir if hasattr(self.args, 'range_storage_dir') else None
            )
            
            # Handle different actions
            if self.tool.action == "create":
                return self._handle_create_action(message_ids_api, conversation_id)
            elif self.tool.action == "append":
                return self._handle_append_action(message_ids_api, conversation_id)
            elif self.tool.action == "delete":
                return self._handle_delete_action(message_ids_api, conversation_id)
            else:
                return ToolResult(
                    success=False,
                    message=get_message_with_format("conversation_message_ids_invalid_action", action=self.tool.action),
                    content={
                        "error_type": "unimplemented_action",
                        "action": self.tool.action
                    }
                )
                
        except Exception as e:
            error_msg = get_message_with_format("conversation_message_ids_operation_exception", error=str(e))
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                content={
                    "error_type": "exception",
                    "error_message": str(e),
                    "tool_parameters": {
                        "message_ids": self.tool.message_ids,
                        "action": self.tool.action
                    }
                }
            )

    def _handle_create_action(self, message_ids_api, conversation_id: str) -> ToolResult:
        """Handle create action - create new configuration, replacing any existing one"""
        # Save message IDs configuration with default preserve_pairs=True
        success, error_msg, message_ids_obj = message_ids_api.save_conversation_message_ids(
            conversation_id=conversation_id,
            message_ids=self.tool.message_ids,
            description="Created via conversation_message_ids_write tool",
            preserve_pairs=True
        )
        
        if success and message_ids_obj:
            stats = message_ids_api.get_message_ids_statistics(conversation_id)
            
            return ToolResult(
                success=True,
                message=get_message("conversation_message_ids_create_success"),
                content={
                    "action": "create",
                    "conversation_id": conversation_id,
                    "message_ids": message_ids_obj.message_ids if message_ids_obj else [],
                    "description": message_ids_obj.description if message_ids_obj else "",
                    "preserve_pairs": message_ids_obj.preserve_pairs if message_ids_obj else True,
                    "statistics": stats,
                    "created_at": message_ids_obj.created_at if message_ids_obj else "",
                    "updated_at": message_ids_obj.updated_at if message_ids_obj else "",
                    "message": get_message("conversation_message_ids_create_success") + f"，共{len(message_ids_obj.message_ids) if message_ids_obj else 0}个消息ID。"
                }
            )
        else:
            logger.error(f"Failed to create conversation message IDs: {error_msg}")
            return ToolResult(
                success=False,
                message=get_message_with_format("conversation_message_ids_create_failed", error=error_msg),
                content={
                    "error_type": "create_failed",
                    "error_message": error_msg,
                    "conversation_id": conversation_id,
                    "message_ids": self.tool.message_ids
                }
            )

    def _handle_append_action(self, message_ids_api:ConversationMessageIdsAPI, conversation_id: str) -> ToolResult:
        """Handle append action - add to existing configuration"""
        # First, try to get existing configuration
        existing_config = message_ids_api.get_conversation_message_ids(conversation_id)
        
        if existing_config:
            # Parse existing message IDs
            existing_ids = set(existing_config.message_ids)
            # Parse new message IDs
            new_ids = set([id.strip() for id in self.tool.message_ids.split(",") if id.strip()])
            # Combine them
            combined_ids = existing_ids.union(new_ids)
            combined_ids_str = ",".join(sorted(combined_ids))
            
            # Save updated configuration
            success, error_msg, message_ids_obj = message_ids_api.save_conversation_message_ids(
                conversation_id=conversation_id,
                message_ids=combined_ids_str,
                description=existing_config.description + " | Appended via tool",
                preserve_pairs=existing_config.preserve_pairs
            )
        else:
            # No existing configuration, create new one
            success, error_msg, message_ids_obj = message_ids_api.save_conversation_message_ids(
                conversation_id=conversation_id,
                message_ids=self.tool.message_ids,
                description="Created via conversation_message_ids_write tool (append)",
                preserve_pairs=True
            )
        
        if success and message_ids_obj:
            stats = message_ids_api.get_message_ids_statistics(conversation_id)
            
            return ToolResult(
                success=True,
                message=get_message("conversation_message_ids_append_success"),
                content={
                    "action": "append",
                    "conversation_id": conversation_id,
                    "message_ids": message_ids_obj.message_ids if message_ids_obj else [],
                    "description": message_ids_obj.description if message_ids_obj else "",
                    "preserve_pairs": message_ids_obj.preserve_pairs if message_ids_obj else True,
                    "statistics": stats,
                    "created_at": message_ids_obj.created_at if message_ids_obj else "",
                    "updated_at": message_ids_obj.updated_at if message_ids_obj else "",
                    "message": get_message("conversation_message_ids_append_success") + f"，共{len(message_ids_obj.message_ids) if message_ids_obj else 0}个消息ID。"
                }
            )
        else:
            logger.error(f"Failed to append conversation message IDs: {error_msg}")
            return ToolResult(
                success=False,
                message=get_message_with_format("conversation_message_ids_append_failed", error=error_msg),
                content={
                    "error_type": "append_failed",
                    "error_message": error_msg,
                    "conversation_id": conversation_id,
                    "message_ids": self.tool.message_ids
                }
            )

    def _handle_delete_action(self, message_ids_api, conversation_id: str) -> ToolResult:
        """Handle delete action - remove from existing configuration"""
        # First, try to get existing configuration
        existing_config = message_ids_api.get_conversation_message_ids(conversation_id)
        
        if not existing_config:
            return ToolResult(
                success=False,
                message=get_message("conversation_message_ids_no_existing_config"),
                content={
                    "error_type": "no_existing_config",
                    "conversation_id": conversation_id,
                    "message": get_message("conversation_message_ids_no_existing_config")
                }
            )
        
        # Parse existing message IDs
        existing_ids = set(existing_config.message_ids)
        # Parse IDs to delete
        ids_to_delete = set([id.strip() for id in self.tool.message_ids.split(",") if id.strip()])
        # Remove them
        remaining_ids = existing_ids - ids_to_delete
        
        if not remaining_ids:
            # Delete the entire configuration if no IDs remain
            success, error_msg = message_ids_api.delete_conversation_message_ids(conversation_id)
            if success:
                return ToolResult(
                    success=True,
                    message=get_message("conversation_message_ids_delete_success"),
                    content={
                        "action": "delete",
                        "conversation_id": conversation_id,
                        "deleted_ids": list(ids_to_delete),
                        "remaining_ids": [],
                        "message": get_message("conversation_message_ids_delete_success")
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    message=get_message_with_format("conversation_message_ids_delete_failed", error=error_msg),
                    content={
                        "error_type": "delete_failed",
                        "error_message": error_msg
                    }
                )
        else:
            # Update configuration with remaining IDs
            remaining_ids_str = ",".join(sorted(remaining_ids))
            success, error_msg, message_ids_obj = message_ids_api.save_conversation_message_ids(
                conversation_id=conversation_id,
                message_ids=remaining_ids_str,
                description=existing_config.description + " | Deleted IDs via tool",
                preserve_pairs=existing_config.preserve_pairs
            )
            
            if success and message_ids_obj:
                stats = message_ids_api.get_message_ids_statistics(conversation_id)
                
                return ToolResult(
                    success=True,
                    message=get_message("conversation_message_ids_update_success"),
                    content={
                        "action": "delete",
                        "conversation_id": conversation_id,
                        "deleted_ids": list(ids_to_delete),
                        "remaining_ids": message_ids_obj.message_ids if message_ids_obj else [],
                        "description": message_ids_obj.description if message_ids_obj else "",
                        "preserve_pairs": message_ids_obj.preserve_pairs if message_ids_obj else True,
                        "statistics": stats,
                        "created_at": message_ids_obj.created_at if message_ids_obj else "",
                        "updated_at": message_ids_obj.updated_at if message_ids_obj else "",
                        "message": get_message("conversation_message_ids_update_success") + f"，剩余{len(message_ids_obj.message_ids) if message_ids_obj else 0}个消息ID。"
                    }
                )
            else:
                logger.error(f"Failed to update conversation message IDs after delete: {error_msg}")
                return ToolResult(
                    success=False,
                    message=get_message_with_format("conversation_message_ids_update_failed", error=error_msg),
                    content={
                        "error_type": "update_after_delete_failed",
                        "error_message": error_msg,
                        "conversation_id": conversation_id,
                        "message_ids": self.tool.message_ids
                    }
                )
