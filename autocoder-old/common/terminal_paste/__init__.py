"""Terminal paste handling module for auto-coder.

This module provides functionality to intercept terminal paste events,
save pasted content to files, and resolve placeholders in user input.
"""

from .paste_handler import register_paste_handler, resolve_paste_placeholders
from .paste_manager import PasteManager

__all__ = [
    "register_paste_handler",
    "resolve_paste_placeholders", 
    "PasteManager"
] 