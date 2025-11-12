"""
Conversation management functionality.

This module provides methods for managing conversation history.
"""

from typing import Dict, Any, List
from .models import ConversationList


class ConversationManagerMixin:
    """Mixin class providing conversation management functionality."""
    
    def get_conversation(self) -> ConversationList:
        """Get conversation history."""
        return self._memory.conversation.copy()
    
    def add_conversation_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self._memory.conversation.append({"role": role, "content": content})
        self.save_memory()
    
    def clear_conversation(self):
        """Clear conversation history."""
        self._memory.conversation = []
        self.save_memory()
    
    def set_conversation(self, conversation: ConversationList):
        """Set entire conversation history."""
        self._memory.conversation = conversation
        self.save_memory()
