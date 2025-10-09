"""
Main todo manager that integrates with conversations.

This module provides the TodoManager class, which serves as
the primary interface for todo and task management, integrating
with the conversations module to get current conversation context.
"""

import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger

from .config import TodoManagerConfig
from .exceptions import (
    TodoManagerError,
    TodoNotFoundError,
    TodoListNotFoundError
)
from .models import Todo, TodoList
from .storage import FileStorage
from .cache import CacheManager

# Import conversations module to get current conversation
try:
    from autocoder.common.conversations.get_conversation_manager import get_conversation_manager
except ImportError:
    logger.warning("Conversations module not available, todo manager will work without conversation integration")
    get_conversation_manager = None


class TodoManager:
    """
    Main todo manager integrating with conversations.
    
    This class provides a unified interface for todo and task management,
    with integrated storage, caching, and conversation context.
    """
    
    def __init__(self, config: Optional[TodoManagerConfig] = None):
        """
        Initialize the todo manager.
        
        Args:
            config: Configuration object for the manager
        """
        self.config = config or TodoManagerConfig()
        
        # Initialize components
        self._init_storage()
        self._init_cache()
        
        # Statistics tracking
        self._stats = {
            'todo_lists_created': 0,
            'todo_lists_loaded': 0,
            'todos_added': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _init_storage(self):
        """Initialize storage components."""
        # Ensure storage directory exists
        storage_path = Path(self.config.storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage backend
        self.storage = FileStorage(str(storage_path))
    
    def _init_cache(self):
        """Initialize cache system."""
        from .cache import MemoryCache
        
        # Initialize cache manager
        todo_cache = MemoryCache(
            max_size=self.config.max_cache_size,
            default_ttl=self.config.cache_ttl
        )
        self.cache_manager = CacheManager(todo_cache=todo_cache)
    
    def _get_current_conversation_id(self) -> Optional[str]:
        """
        Get current conversation ID from conversation manager.
        
        Returns:
            Current conversation ID or None if not available
        """
        if get_conversation_manager is None:
            logger.debug("Conversation manager not available")
            return None
        
        try:
            conversation_manager = get_conversation_manager()
            current_id = conversation_manager.get_current_conversation_id()
            logger.debug(f"Current conversation ID: {current_id}")
            return current_id
        except Exception as e:
            logger.error(f"Failed to get current conversation ID: {e}")
            return None
    
    def _get_or_create_todo_list(self, conversation_id: str) -> TodoList:
        """
        Get or create a todo list for a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            TodoList object
        """
        # Try cache first
        cached_data = self.cache_manager.get_todo_list(conversation_id)
        if cached_data:
            self._stats['cache_hits'] += 1
            return TodoList.from_dict(cached_data)
        
        self._stats['cache_misses'] += 1
        
        # Try storage
        stored_data = self.storage.load_todo_list(conversation_id)
        if stored_data:
            todo_list = TodoList.from_dict(stored_data)
            # Cache it
            self.cache_manager.cache_todo_list(stored_data)
            self._stats['todo_lists_loaded'] += 1
            return todo_list
        
        # Create new todo list
        todo_list = TodoList(conversation_id=conversation_id)
        self._stats['todo_lists_created'] += 1
        return todo_list
    
    def _save_todo_list(self, todo_list: TodoList) -> bool:
        """
        Save a todo list to storage and cache.
        
        Args:
            todo_list: TodoList to save
            
        Returns:
            True if save was successful
        """
        try:
            # Convert to dict
            todo_list_data = todo_list.to_dict()
            
            # Save to storage
            if not self.storage.save_todo_list(todo_list.conversation_id, todo_list_data):
                return False
            
            # Update cache
            self.cache_manager.cache_todo_list(todo_list_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save todo list for conversation {todo_list.conversation_id}: {e}")
            return False
    
    # Todo Management Methods
    
    def create_todos(
        self,
        content: str,
        conversation_id: Optional[str] = None,
        priority: str = "medium",
        notes: Optional[str] = None
    ) -> List[str]:
        """
        Create multiple todos from content.
        
        Args:
            content: Content to parse into todos
            conversation_id: Conversation ID (uses current if None)
            priority: Priority level
            notes: Optional notes
            
        Returns:
            List of created todo IDs
            
        Raises:
            TodoManagerError: If creation fails
        """
        try:
            # Get conversation ID
            if conversation_id is None:
                conversation_id = self._get_current_conversation_id()
                if conversation_id is None:
                    raise TodoManagerError("No current conversation available and no conversation_id provided")
            
            # Parse content into todos
            todo_contents = self._parse_content_to_todos(content)
            
            if not todo_contents:
                raise TodoManagerError("No valid todos found in content")
            
            # Get or create todo list
            todo_list = self._get_or_create_todo_list(conversation_id)
            
            # Create todos
            created_ids = []
            for todo_content in todo_contents:
                todo = Todo(
                    content=todo_content,
                    priority=priority,
                    notes=notes
                )
                todo_list.add_todo(todo)
                created_ids.append(todo.todo_id)
                self._stats['todos_added'] += 1
            
            # Save todo list
            if not self._save_todo_list(todo_list):
                raise TodoManagerError("Failed to save todo list")
            
            logger.info(f"Created {len(created_ids)} todos for conversation {conversation_id}")
            return created_ids
            
        except TodoManagerError:
            raise
        except Exception as e:
            raise TodoManagerError(f"Failed to create todos: {e}")
    
    def add_todo(
        self,
        content: str,
        conversation_id: Optional[str] = None,
        status: str = "pending",
        priority: str = "medium",
        notes: Optional[str] = None
    ) -> str:
        """
        Add a single todo.
        
        Args:
            content: Todo content
            conversation_id: Conversation ID (uses current if None)
            status: Todo status
            priority: Priority level
            notes: Optional notes
            
        Returns:
            Created todo ID
            
        Raises:
            TodoManagerError: If creation fails
        """
        try:
            # Get conversation ID
            if conversation_id is None:
                conversation_id = self._get_current_conversation_id()
                if conversation_id is None:
                    raise TodoManagerError("No current conversation available and no conversation_id provided")
            
            # Get or create todo list
            todo_list = self._get_or_create_todo_list(conversation_id)
            
            # Create todo
            todo = Todo(
                content=content,
                status=status,
                priority=priority,
                notes=notes
            )
            todo_list.add_todo(todo)
            self._stats['todos_added'] += 1
            
            # Save todo list
            if not self._save_todo_list(todo_list):
                raise TodoManagerError("Failed to save todo list")
            
            logger.info(f"Added todo {todo.todo_id} to conversation {conversation_id}")
            return todo.todo_id
            
        except TodoManagerError:
            raise
        except Exception as e:
            raise TodoManagerError(f"Failed to add todo: {e}")
    
    def get_todos(
        self,
        conversation_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get todos for a conversation.
        
        Args:
            conversation_id: Conversation ID (uses current if None)
            status: Filter by status
            priority: Filter by priority
            
        Returns:
            List of todo data
            
        Raises:
            TodoListNotFoundError: If todo list doesn't exist
        """
        try:
            # Get conversation ID
            if conversation_id is None:
                conversation_id = self._get_current_conversation_id()
                if conversation_id is None:
                    raise TodoManagerError("No current conversation available and no conversation_id provided")
            
            # Check if todo list exists
            if not self.storage.todo_list_exists(conversation_id):
                return []  # Return empty list instead of raising error
            
            # Get todo list
            todo_list = self._get_or_create_todo_list(conversation_id)
            
            # Get all todos
            todos = todo_list.todos
            
            # Apply filters
            if status:
                todos = [t for t in todos if t.get('status') == status]
            
            if priority:
                todos = [t for t in todos if t.get('priority') == priority]
            
            return todos
            
        except TodoManagerError:
            raise
        except Exception as e:
            raise TodoManagerError(f"Failed to get todos: {e}")
    
    def update_todo(
        self,
        todo_id: str,
        conversation_id: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update a todo.
        
        Args:
            todo_id: Todo ID
            conversation_id: Conversation ID (uses current if None)
            content: New content
            status: New status
            priority: New priority
            notes: New notes
            
        Returns:
            True if update was successful
            
        Raises:
            TodoNotFoundError: If todo doesn't exist
        """
        try:
            # Get conversation ID
            if conversation_id is None:
                conversation_id = self._get_current_conversation_id()
                if conversation_id is None:
                    raise TodoManagerError("No current conversation available and no conversation_id provided")
            
            # Get todo list
            todo_list = self._get_or_create_todo_list(conversation_id)
            
            # Find todo
            todo_data = todo_list.get_todo(todo_id)
            if not todo_data:
                raise TodoNotFoundError(todo_id)
            
            # Update fields
            update_kwargs = {}
            if content is not None:
                update_kwargs['content'] = content
            if status is not None:
                update_kwargs['status'] = status
            if priority is not None:
                update_kwargs['priority'] = priority
            if notes is not None:
                update_kwargs['notes'] = notes
            
            # Update todo
            success = todo_list.update_todo(todo_id, **update_kwargs)
            if not success:
                raise TodoNotFoundError(todo_id)
            
            # Save todo list
            if not self._save_todo_list(todo_list):
                raise TodoManagerError("Failed to save todo list")
            
            logger.info(f"Updated todo {todo_id} in conversation {conversation_id}")
            return True
            
        except (TodoNotFoundError, TodoManagerError):
            raise
        except Exception as e:
            raise TodoManagerError(f"Failed to update todo: {e}")
    
    def delete_todo(
        self,
        todo_id: str,
        conversation_id: Optional[str] = None
    ) -> bool:
        """
        Delete a todo.
        
        Args:
            todo_id: Todo ID
            conversation_id: Conversation ID (uses current if None)
            
        Returns:
            True if deletion was successful
            
        Raises:
            TodoNotFoundError: If todo doesn't exist
        """
        try:
            # Get conversation ID
            if conversation_id is None:
                conversation_id = self._get_current_conversation_id()
                if conversation_id is None:
                    raise TodoManagerError("No current conversation available and no conversation_id provided")
            
            # Get todo list
            todo_list = self._get_or_create_todo_list(conversation_id)
            
            # Remove todo
            success = todo_list.remove_todo(todo_id)
            if not success:
                raise TodoNotFoundError(todo_id)
            
            # Save todo list
            if not self._save_todo_list(todo_list):
                raise TodoManagerError("Failed to save todo list")
            
            logger.info(f"Deleted todo {todo_id} from conversation {conversation_id}")
            return True
            
        except (TodoNotFoundError, TodoManagerError):
            raise
        except Exception as e:
            raise TodoManagerError(f"Failed to delete todo: {e}")
    
    def get_statistics(self, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get todo statistics.
        
        Args:
            conversation_id: Conversation ID (uses current if None)
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get conversation ID
            if conversation_id is None:
                conversation_id = self._get_current_conversation_id()
                if conversation_id is None:
                    return {"error": "No current conversation available"}
            
            # Get todo list
            if not self.storage.todo_list_exists(conversation_id):
                return {
                    "conversation_id": conversation_id,
                    "total": 0,
                    "pending": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "cancelled": 0
                }
            
            todo_list = self._get_or_create_todo_list(conversation_id)
            stats = todo_list.get_statistics()
            
            # Create a new dictionary to avoid type issues
            result_stats: Dict[str, Any] = dict(stats)
            result_stats["conversation_id"] = conversation_id
            result_stats["manager_stats"] = self._stats
            result_stats["cache_stats"] = self.cache_manager.get_cache_statistics()
            
            return result_stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
    
    def _parse_content_to_todos(self, content: str) -> List[str]:
        """
        Parse content into individual todo items.
        
        Args:
            content: Content to parse
            
        Returns:
            List of todo content strings
        """
        import re
        
        todos = []
        
        # First, try to parse <task> tags
        task_pattern = r'<task>(.*?)</task>'
        task_matches = re.findall(task_pattern, content, re.DOTALL)
        
        if task_matches:
            # Found <task> tags, use them
            for task_content in task_matches:
                task_content = task_content.strip()
                if task_content:
                    todos.append(task_content)
        else:
            # Fallback to line-by-line parsing
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Remove common prefixes like "1.", "- ", "* ", etc.
                line = line.lstrip('0123456789.- *\t')
                
                if line:
                    todos.append(line)
        
        return todos
    
    def clear_cache(self):
        """Clear all caches."""
        self.cache_manager.clear_all_caches()
    
    def close(self):
        """Clean up resources."""
        # Clear caches
        self.clear_cache() 