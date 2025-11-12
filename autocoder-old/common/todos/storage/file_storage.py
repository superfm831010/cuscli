"""
File-based storage implementation for todo lists.

This module provides a file system storage implementation for todo lists,
storing each conversation's todos as a separate JSON file.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger

from .base_storage import BaseStorage


class FileStorage(BaseStorage):
    """File-based storage implementation for todo lists."""
    
    def __init__(self, storage_path: str):
        """
        Initialize file storage.
        
        Args:
            storage_path: Base path for todo storage
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure storage directory exists."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_todo_list_file_path(self, conversation_id: str) -> Path:
        """
        Get file path for a conversation's todo list.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Path to the todo list file
        """
        # Sanitize conversation ID for file system
        safe_id = self._sanitize_filename(conversation_id)
        return self.storage_path / f"{safe_id}.json"
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to be safe for file system.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace unsafe characters with underscores
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limit length
        if len(safe_name) > 200:
            safe_name = safe_name[:200]
        
        return safe_name
    
    def _validate_todo_list_data(self, todo_list_data: Dict[str, Any]) -> bool:
        """
        Validate todo list data structure.
        
        Args:
            todo_list_data: Todo list data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['conversation_id', 'todos', 'created_at', 'updated_at']
        
        for field in required_fields:
            if field not in todo_list_data:
                logger.error(f"Todo list validation failed: missing field '{field}'")
                return False
        
        if not isinstance(todo_list_data['todos'], list):
            logger.error("Todo list validation failed: 'todos' must be a list")
            return False
        
        return True
    
    def _atomic_write_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """
        Atomically write data to file.
        
        Args:
            file_path: Target file path
            data: Data to write
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            # Write to temporary file first
            temp_fd, temp_path = tempfile.mkstemp(
                suffix='.tmp',
                dir=file_path.parent,
                prefix=f'{file_path.stem}_'
            )
            
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Atomic move
                Path(temp_path).replace(file_path)
                return True
                
            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise
                
        except Exception as e:
            logger.error(f"Failed to write file atomically {file_path}: {e}")
            return False
    
    def save_todo_list(self, conversation_id: str, todo_list_data: Dict[str, Any]) -> bool:
        """
        Save a todo list to storage.
        
        Args:
            conversation_id: The conversation ID
            todo_list_data: The todo list data to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Validate data
            if not self._validate_todo_list_data(todo_list_data):
                return False
            
            # Get file path
            file_path = self._get_todo_list_file_path(conversation_id)
            
            # Atomic write
            success = self._atomic_write_file(file_path, todo_list_data)
            
            if success:
                logger.debug(f"Successfully saved todo list for conversation {conversation_id}")
            else:
                logger.error(f"Failed to save todo list for conversation {conversation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving todo list for conversation {conversation_id}: {e}")
            return False
    
    def load_todo_list(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a todo list from storage.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Todo list data or None if not found
        """
        try:
            file_path = self._get_todo_list_file_path(conversation_id)
            
            if not file_path.exists():
                logger.debug(f"Todo list file not found for conversation {conversation_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate loaded data
            if not self._validate_todo_list_data(data):
                logger.error(f"Invalid todo list data for conversation {conversation_id}")
                return None
            
            logger.debug(f"Successfully loaded todo list for conversation {conversation_id}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in todo list file for conversation {conversation_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading todo list for conversation {conversation_id}: {e}")
            return None
    
    def delete_todo_list(self, conversation_id: str) -> bool:
        """
        Delete a todo list from storage.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            file_path = self._get_todo_list_file_path(conversation_id)
            
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Successfully deleted todo list for conversation {conversation_id}")
                return True
            else:
                logger.debug(f"Todo list file not found for conversation {conversation_id} (already deleted)")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting todo list for conversation {conversation_id}: {e}")
            return False
    
    def todo_list_exists(self, conversation_id: str) -> bool:
        """
        Check if a todo list exists in storage.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if todo list exists, False otherwise
        """
        try:
            file_path = self._get_todo_list_file_path(conversation_id)
            return file_path.exists()
        except Exception as e:
            logger.error(f"Error checking todo list existence for conversation {conversation_id}: {e}")
            return False
    
    def list_conversation_ids(self) -> List[str]:
        """
        List all conversation IDs that have todo lists.
        
        Returns:
            List of conversation IDs
        """
        try:
            conversation_ids = []
            
            if not self.storage_path.exists():
                return conversation_ids
            
            for file_path in self.storage_path.glob("*.json"):
                # Extract conversation ID from filename
                conversation_id = file_path.stem
                
                # Try to load and validate the file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if self._validate_todo_list_data(data):
                        # Use the conversation ID from the file content
                        actual_id = data.get('conversation_id', conversation_id)
                        conversation_ids.append(actual_id)
                        
                except Exception as e:
                    logger.warning(f"Skipping invalid todo list file {file_path}: {e}")
                    continue
            
            return conversation_ids
            
        except Exception as e:
            logger.error(f"Error listing conversation IDs: {e}")
            return [] 