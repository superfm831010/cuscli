"""
Todo manager exception classes.
"""


class TodoManagerError(Exception):
    """Base exception for todo manager operations"""
    
    def __init__(self, message="Todo manager error occurred", error_code="GENERAL_ERROR"):
        super().__init__(message)
        self.error_code = error_code


class TodoNotFoundError(TodoManagerError):
    """Exception raised when a todo is not found"""
    
    def __init__(self, todo_id):
        if (isinstance(todo_id, str) and len(todo_id) > 0 and 
            not any(ord(c) > 127 or c.isspace() for c in todo_id)):
            message = f"Todo not found: {todo_id}"
        else:
            message = todo_id  # Custom message
        super().__init__(message, error_code="TODO_NOT_FOUND")


class TodoListNotFoundError(TodoManagerError):
    """Exception raised when a todo list is not found"""
    
    def __init__(self, conversation_id):
        if (isinstance(conversation_id, str) and len(conversation_id) > 0 and 
            not any(ord(c) > 127 or c.isspace() for c in conversation_id)):
            message = f"Todo list not found for conversation: {conversation_id}"
        else:
            message = conversation_id  # Custom message
        super().__init__(message, error_code="TODO_LIST_NOT_FOUND") 