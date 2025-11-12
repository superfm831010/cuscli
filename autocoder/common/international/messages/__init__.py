"""
Messages module for auto-coder international support

This module automatically registers all message files and provides a unified interface.
"""

from .auto_coder_messages import AUTO_CODER_MESSAGES
from .chat_auto_coder_messages import CHAT_AUTO_CODER_MESSAGES
from .sdk_messages import SDK_MESSAGES
from .tool_display_messages import TOOL_DISPLAY_MESSAGES
from .git_helper_plugin_messages import GIT_HELPER_PLUGIN_MESSAGES
from .token_helper_plugin_messages import TOKEN_HELPER_PLUGIN_MESSAGES
from .rules_command_messages import RULES_COMMAND_MESSAGES
from .queue_command_messages import QUEUE_COMMAND_MESSAGES
from .async_command_messages import ASYNC_COMMAND_MESSAGES
from .conversation_command_messages import CONVERSATION_COMMAND_MESSAGES
from .command_help_messages import COMMAND_HELP_MESSAGES
from .workflow_exception_messages import WORKFLOW_EXCEPTION_MESSAGES
from ..message_manager import register_messages


# Automatically register all messages when the module is imported
def register_all_messages():
    """Register all messages with the global message manager"""
    register_messages(AUTO_CODER_MESSAGES)
    register_messages(CHAT_AUTO_CODER_MESSAGES)
    register_messages(SDK_MESSAGES)
    register_messages(TOOL_DISPLAY_MESSAGES)
    register_messages(GIT_HELPER_PLUGIN_MESSAGES)
    register_messages(TOKEN_HELPER_PLUGIN_MESSAGES)
    register_messages(RULES_COMMAND_MESSAGES)
    register_messages(QUEUE_COMMAND_MESSAGES)
    register_messages(ASYNC_COMMAND_MESSAGES)
    register_messages(CONVERSATION_COMMAND_MESSAGES)
    register_messages(COMMAND_HELP_MESSAGES)
    register_messages(WORKFLOW_EXCEPTION_MESSAGES)


# Auto-register on import
register_all_messages()

__all__ = [
    "AUTO_CODER_MESSAGES",
    "CHAT_AUTO_CODER_MESSAGES",
    "SDK_MESSAGES",
    "TOOL_DISPLAY_MESSAGES",
    "GIT_HELPER_PLUGIN_MESSAGES",
    "TOKEN_HELPER_PLUGIN_MESSAGES",
    "RULES_COMMAND_MESSAGES",
    "QUEUE_COMMAND_MESSAGES",
    "ASYNC_COMMAND_MESSAGES",
    "CONVERSATION_COMMAND_MESSAGES",
    "COMMAND_HELP_MESSAGES",
    "WORKFLOW_EXCEPTION_MESSAGES",
    "register_all_messages",
]
