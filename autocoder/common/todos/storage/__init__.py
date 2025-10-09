"""
Storage module for todo management.

This module provides storage functionality for todos and todo lists,
with support for file-based storage and extensible storage backends.
"""

from .base_storage import BaseStorage
from .file_storage import FileStorage

__all__ = [
    'BaseStorage',
    'FileStorage'
] 