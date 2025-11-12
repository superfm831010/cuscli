"""
Cache manager for todo caching.

This module provides a high-level interface for managing caches of
todo lists, with support for cache warming, invalidation,
and statistics reporting.
"""

import logging
from typing import Optional, List, Dict, Any

from .base_cache import BaseCache
from .memory_cache import MemoryCache
from ..models import TodoList

logger = logging.getLogger(__name__)


class CacheManager:
    """High-level cache manager for todo lists."""
    
    def __init__(self, todo_cache: Optional[BaseCache] = None):
        """
        Initialize cache manager.
        
        Args:
            todo_cache: Cache instance for todo lists
        """
        self.todo_cache = todo_cache or MemoryCache(
            max_size=50, default_ttl=300.0  # 5 minutes default
        )
        
        # Ensure cache implements required interface
        self._validate_cache_interface(self.todo_cache)
    
    def _validate_cache_interface(self, cache: BaseCache) -> None:
        """Validate that cache implements required interface."""
        required_methods = ['get', 'set', 'delete', 'clear', 'exists', 'size', 'keys']
        for method in required_methods:
            if not hasattr(cache, method) or not callable(getattr(cache, method)):
                raise TypeError(f"Cache must implement {method} method")
    
    def _get_todo_list_key(self, conversation_id: str) -> str:
        """Generate cache key for todo list."""
        return f"todos:{conversation_id}"
    
    def cache_todo_list(
        self, 
        todo_list: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache a todo list.
        
        Args:
            todo_list: The todo list to cache
            ttl: Time to live in seconds, None for default
        """
        try:
            conversation_id = todo_list.get('conversation_id')
            if not conversation_id:
                logger.error("Cannot cache todo list without conversation_id")
                return
                
            key = self._get_todo_list_key(conversation_id)
            self.todo_cache.set(key, todo_list, ttl=ttl)
            logger.debug(f"Cached todo list for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to cache todo list for conversation {conversation_id}: {e}")
    
    def get_todo_list(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a todo list from cache.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The cached todo list or None if not found
        """
        try:
            key = self._get_todo_list_key(conversation_id)
            todo_list = self.todo_cache.get(key)
            if todo_list:
                logger.debug(f"Cache hit for todo list of conversation {conversation_id}")
            else:
                logger.debug(f"Cache miss for todo list of conversation {conversation_id}")
            return todo_list
        except Exception as e:
            logger.error(f"Failed to get todo list for conversation {conversation_id} from cache: {e}")
            return None
    
    def invalidate_todo_list(self, conversation_id: str) -> bool:
        """
        Invalidate cached todo list.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if todo list was cached and removed, False otherwise
        """
        try:
            key = self._get_todo_list_key(conversation_id)
            result = self.todo_cache.delete(key)
            if result:
                logger.debug(f"Invalidated todo list for conversation {conversation_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to invalidate todo list for conversation {conversation_id}: {e}")
            return False
    
    def cache_todo_lists(
        self, 
        todo_lists: List[Dict[str, Any]],
        ttl: Optional[float] = None
    ) -> int:
        """
        Cache multiple todo lists.
        
        Args:
            todo_lists: List of todo lists to cache
            ttl: Time to live in seconds, None for default
            
        Returns:
            Number of todo lists successfully cached
        """
        count = 0
        for todo_list in todo_lists:
            try:
                self.cache_todo_list(todo_list, ttl=ttl)
                count += 1
            except Exception as e:
                conversation_id = todo_list.get('conversation_id', 'unknown')
                logger.error(f"Failed to cache todo list for conversation {conversation_id}: {e}")
        
        return count
    
    def invalidate_todo_lists(self, conversation_ids: List[str]) -> Dict[str, bool]:
        """
        Invalidate multiple todo lists.
        
        Args:
            conversation_ids: List of conversation IDs to invalidate
            
        Returns:
            Dictionary mapping conversation IDs to invalidation results
        """
        results = {}
        for conversation_id in conversation_ids:
            results[conversation_id] = self.invalidate_todo_list(conversation_id)
        
        return results
    
    def clear_all_caches(self) -> None:
        """Clear all caches."""
        try:
            self.todo_cache.clear()
            logger.info("Cleared all todo caches")
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all caches.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = {
                "todo_cache": {
                    "size": self.todo_cache.size(),
                    "max_size": getattr(self.todo_cache, 'max_size', 'unknown')
                }
            }
            
            # Add detailed stats if available
            if hasattr(self.todo_cache, 'get_statistics'):
                get_stats_method = getattr(self.todo_cache, 'get_statistics')
                stats["todo_cache"].update(
                    get_stats_method()
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {
                "todo_cache": {"size": 0, "max_size": "unknown"},
                "error": str(e)
            }
    
    def is_todo_list_cached(self, conversation_id: str) -> bool:
        """
        Check if a todo list is cached.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if todo list is cached, False otherwise
        """
        try:
            key = self._get_todo_list_key(conversation_id)
            return self.todo_cache.exists(key)
        except Exception as e:
            logger.error(f"Failed to check if todo list for conversation {conversation_id} is cached: {e}")
            return False
    
    def get_cached_conversation_ids(self) -> List[str]:
        """
        Get all cached conversation IDs.
        
        Returns:
            List of conversation IDs currently cached
        """
        try:
            keys = self.todo_cache.keys()
            # Extract conversation IDs from cache keys
            conversation_ids = []
            for key in keys:
                if key.startswith("todos:"):
                    conversation_ids.append(key[6:])  # Remove "todos:" prefix
            return conversation_ids
        except Exception as e:
            logger.error(f"Failed to get cached conversation IDs: {e}")
            return [] 