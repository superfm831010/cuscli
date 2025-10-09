"""
International module for auto-coder project

This module provides internationalization (i18n) support for the auto-coder project.
It includes message management, language detection, and formatted message retrieval.
"""

from .message_manager import (
    MessageManager,
    get_message_manager,
    register_messages,
    get_system_language,
    get_message,
    get_message_with_format,
    get_supported_languages,
    is_language_supported
)

# Import messages module to trigger auto-registration
from . import messages

__all__ = [
    'MessageManager',
    'get_message_manager',
    'register_messages',
    'get_system_language',
    'get_message',
    'get_message_with_format',
    'get_supported_languages',
    'is_language_supported'
] 