"""
Todo manager data models.
"""

import time
import uuid
from typing import Union, Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Todo:
    """Todo item data model"""
    
    content: str
    todo_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: str = "pending"
    priority: str = "medium"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    notes: Optional[str] = None
    dependencies: Optional[List[str]] = None
    
    def __post_init__(self):
        """Data validation"""
        self._validate()
    
    def _validate(self):
        """Validate todo data"""
        # Validate content
        if not self.content or (isinstance(self.content, str) and len(self.content.strip()) == 0):
            raise ValueError("Todo content cannot be empty")
        
        # Validate status
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}, valid statuses: {valid_statuses}")
        
        # Validate priority
        valid_priorities = ["low", "medium", "high"]
        if self.priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {self.priority}, valid priorities: {valid_priorities}")
        
        # Validate timestamps
        if not isinstance(self.created_at, (int, float)) or self.created_at <= 0:
            raise ValueError("Invalid created_at timestamp")
        
        if not isinstance(self.updated_at, (int, float)) or self.updated_at < self.created_at:
            raise ValueError("Invalid updated_at timestamp")
        
        # Validate todo ID
        if not isinstance(self.todo_id, str) or len(self.todo_id) == 0:
            raise ValueError("Todo ID cannot be empty")
    
    def update_status(self, status: str):
        """Update todo status"""
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        self.status = status
        self.updated_at = time.time()
    
    def update_content(self, content: str):
        """Update todo content"""
        if not content or len(content.strip()) == 0:
            raise ValueError("Todo content cannot be empty")
        
        self.content = content
        self.updated_at = time.time()
    
    def update_priority(self, priority: str):
        """Update todo priority"""
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}")
        
        self.priority = priority
        self.updated_at = time.time()
    
    def add_notes(self, notes: str):
        """Add or update notes"""
        self.notes = notes
        self.updated_at = time.time()
    
    def add_dependency(self, todo_id: str):
        """Add a dependency to another todo"""
        if self.dependencies is None:
            self.dependencies = []
        
        if todo_id not in self.dependencies:
            self.dependencies.append(todo_id)
            self.updated_at = time.time()
    
    def remove_dependency(self, todo_id: str):
        """Remove a dependency"""
        if self.dependencies and todo_id in self.dependencies:
            self.dependencies.remove(todo_id)
            self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "todo_id": self.todo_id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
            "dependencies": self.dependencies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Todo":
        """Deserialize from dictionary"""
        return cls(
            todo_id=data["todo_id"],
            content=data["content"],
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            notes=data.get("notes"),
            dependencies=data.get("dependencies")
        )


@dataclass
class TodoList:
    """Todo list data model for a conversation"""
    
    conversation_id: str
    todos: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Data validation"""
        self._validate()
    
    def _validate(self):
        """Validate todo list data"""
        # Validate conversation ID
        if not isinstance(self.conversation_id, str) or len(self.conversation_id) == 0:
            raise ValueError("Conversation ID cannot be empty")
        
        # Validate timestamps
        if not isinstance(self.created_at, (int, float)) or self.created_at <= 0:
            raise ValueError("Invalid created_at timestamp")
        
        if not isinstance(self.updated_at, (int, float)) or self.updated_at < self.created_at:
            raise ValueError("Invalid updated_at timestamp")
        
        # Validate todos list
        if not isinstance(self.todos, list):
            raise ValueError("Todos must be a list")
    
    def add_todo(self, todo: Todo):
        """Add a todo to the list"""
        self.todos.append(todo.to_dict())
        self.updated_at = time.time()
    
    def remove_todo(self, todo_id: str) -> bool:
        """Remove a todo from the list"""
        for i, todo_data in enumerate(self.todos):
            if todo_data.get("todo_id") == todo_id:
                del self.todos[i]
                self.updated_at = time.time()
                return True
        return False
    
    def get_todo(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """Get a todo from the list"""
        for todo_data in self.todos:
            if todo_data.get("todo_id") == todo_id:
                return todo_data
        return None
    
    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """Update a todo in the list"""
        for todo_data in self.todos:
            if todo_data.get("todo_id") == todo_id:
                # Update fields
                for key, value in kwargs.items():
                    if key in ["content", "status", "priority", "notes", "dependencies"]:
                        todo_data[key] = value
                
                todo_data["updated_at"] = time.time()
                self.updated_at = time.time()
                return True
        return False
    
    def get_todos_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get todos by status"""
        return [todo for todo in self.todos if todo.get("status") == status]
    
    def get_todos_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get todos by priority"""
        return [todo for todo in self.todos if todo.get("priority") == priority]
    
    def get_statistics(self) -> Dict[str, int]:
        """Get todo statistics"""
        stats = {
            "total": len(self.todos),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0
        }
        
        for todo in self.todos:
            status = todo.get("status", "pending")
            if status in stats:
                stats[status] += 1
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "todos": self.todos,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoList":
        """Deserialize from dictionary"""
        return cls(
            conversation_id=data["conversation_id"],
            todos=data.get("todos", []),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            metadata=data.get("metadata")
        ) 