from byzerllm.utils import format_str_jinja2
import locale
from .international import (
    get_system_language as _get_system_language,
    get_message as _get_message,
    get_message_with_format as _get_message_with_format
)

# Import messages module to auto-register all messages
from .international.messages import register_all_messages

# Messages are now automatically registered through the messages module


def get_system_language():
    """
    Get the system's default language code
    Delegates to the international module
    """
    return _get_system_language()


def get_message(key):
    """
    Get a localized message by key
    Delegates to the international module
    """
    return _get_message(key)


def get_message_with_format(msg_key: str, **kwargs):
    """
    Get a localized message with template formatting
    Delegates to the international module
    """
    return _get_message_with_format(msg_key, **kwargs)
