"""
Base storage interface for todo management.

This module defines the abstract base class for all storage implementations,
providing a consistent interface for todo and todo list operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class BaseStorage(ABC):
    """Abstract base class for todo storage implementations."""
    
    @abstractmethod
    def save_todo_list(self, conversation_id: str, todo_list_data: Dict[str, Any]) -> bool:
        """
        Save a todo list to storage.
        
        Args:
            conversation_id: The conversation ID
            todo_list_data: The todo list data to save
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load_todo_list(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a todo list from storage.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Todo list data or None if not found
        """
        pass
    
    @abstractmethod
    def delete_todo_list(self, conversation_id: str) -> bool:
        """
        Delete a todo list from storage.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def todo_list_exists(self, conversation_id: str) -> bool:
        """
        Check if a todo list exists in storage.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if todo list exists, False otherwise
        """
        pass
    
    @abstractmethod
    def list_conversation_ids(self) -> List[str]:
        """
        List all conversation IDs that have todo lists.
        
        Returns:
            List of conversation IDs
        """
        pass 