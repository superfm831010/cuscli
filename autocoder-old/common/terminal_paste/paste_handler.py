"""Terminal paste event handler and placeholder resolver."""

import re
from typing import Optional, Callable
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
from prompt_toolkit.clipboard import ClipboardData
from prompt_toolkit.keys import Keys
from .paste_manager import PasteManager


# Global paste manager instance
_paste_manager: Optional[PasteManager] = None

# 占位符正则表达式，匹配 [pasted-<uuid>] 格式（32位十六进制，无连字符）
PLACEHOLDER_PATTERN = re.compile(r"\[pasted-([0-9a-f]{32})\]")


def get_paste_manager() -> PasteManager:
    """Get or create global paste manager instance."""
    global _paste_manager
    if _paste_manager is None:
        _paste_manager = PasteManager()
    return _paste_manager


def register_paste_handler(kb: KeyBindings) -> None:
    """Register paste handler with prompt_toolkit key bindings.
    
    Args:
        kb: KeyBindings instance to register with
        
    Note:
        This function sets up a custom paste handler that intercepts multi-line
        paste operations and saves them to files with placeholder replacement.
        
        Supports multiple paste methods:
        - Bracketed paste (automatic detection of pasted content)
        - Ctrl+V (standard paste shortcut)
        - Ctrl+P (legacy binding)
        - Cmd+V (Mac paste shortcut, mapped as Meta+V)
    """
    
    def paste_handler_impl(event):
        """Handle paste operations with file saving for multi-line content."""
        try:
            # Get the current application
            app = event.app
            
            # Get clipboard content
            clipboard_data = app.clipboard.get_data()
            if not clipboard_data:
                return
                
            text = clipboard_data.text
            if not text:
                return
            
            # Check if it's multi-line content (more than 1 line)
            lines = text.splitlines()
            if len(lines) > 1:
                # Save multi-line content to file and insert placeholder
                paste_manager = get_paste_manager()
                file_id = paste_manager.save_paste(text)
                
                # Create placeholder - file_id already contains "pasted-" prefix
                placeholder = f"[{file_id}]"
                
                # Insert placeholder instead of actual content
                event.current_buffer.insert_text(placeholder)                
            else:
                # For single-line content, just paste normally
                event.current_buffer.insert_text(text)
                
        except Exception as e:
            print(f"\033[91m✗ Error in paste handler: {e}\033[0m")
            # Fall back to normal paste behavior
            try:
                clipboard_data = event.app.clipboard.get_data()
                if clipboard_data and clipboard_data.text:
                    event.current_buffer.insert_text(clipboard_data.text)
            except:
                pass
    
    # Bind to bracketed paste event (most reliable for all paste operations)
    @kb.add(Keys.BracketedPaste)
    def bracketed_paste_handler(event):
        """Handle bracketed paste events (automatic paste detection)."""
        try:
            # For bracketed paste, the pasted text is directly available in event.data
            text = event.data
            if not text:
                return
            
            # Check if it's multi-line content (more than 1 line)
            lines = text.splitlines()
            if len(lines) > 1:
                # Save multi-line content to file and insert placeholder
                paste_manager = get_paste_manager()
                file_id = paste_manager.save_paste(text)
                
                # Create placeholder - file_id already contains "pasted-" prefix
                placeholder = f"[{file_id}]"
                
                # Insert placeholder instead of actual content
                event.current_buffer.insert_text(placeholder)                
            else:
                # For single-line content, just paste normally
                event.current_buffer.insert_text(text)
                
        except Exception as e:
            print(f"\033[91m✗ Error in bracketed paste handler: {e}\033[0m")
            # Fall back to inserting the text directly
            try:
                if hasattr(event, 'data') and event.data:
                    event.current_buffer.insert_text(event.data)
            except:
                pass
    
    # Bind to standard paste shortcuts as backup
    @kb.add('c-v')  # Ctrl+V (standard paste)
    def ctrl_v_paste_handler(event):
        """Handle Ctrl+V paste events."""
        paste_handler_impl(event)
    
    @kb.add('c-p')  # Ctrl+P (legacy binding)
    def ctrl_p_paste_handler(event):
        """Handle Ctrl+P paste events (legacy)."""
        paste_handler_impl(event)
    
    # For Mac users: Cmd+V is often mapped as Meta+V in terminals
    @kb.add('escape', 'v')  # Meta+V (often mapped from Cmd+V on Mac)
    def meta_v_paste_handler(event):
        """Handle Meta+V paste events (Mac Cmd+V equivalent)."""
        paste_handler_impl(event)


def resolve_paste_placeholders(text: str) -> str:
    """Resolve paste placeholders in text to actual content.
    
    Args:
        text: Input text that may contain placeholders
        
    Returns:
        Text with placeholders replaced by actual content
    """
    if not text or "[pasted-" not in text:
        return text
        
    paste_manager = get_paste_manager()
    
    def replace_placeholder(match) -> str:
        """Replace a single placeholder with its content."""
        uuid_part = match.group(1)  # Extract UUID from [pasted-<uuid>]
        file_id = f"pasted-{uuid_part}"  # Reconstruct full file_id
        
        try:
            content = paste_manager.read_paste(file_id)
            if content is not None:
                return content
            else:
                # File not found, keep placeholder for debugging
                print(f"\033[93m⚠ Paste file not found: {file_id}\033[0m")
                return match.group(0)
        except Exception as e:
            print(f"\033[91m✗ Error reading paste file: {e}\033[0m")
            return match.group(0)
    
    # Replace all placeholders in the text
    resolved_text = PLACEHOLDER_PATTERN.sub(replace_placeholder, text)
    
    # Show user if any replacements were made
    if resolved_text != text:
        placeholder_count = len(PLACEHOLDER_PATTERN.findall(text))
        print(f"\033[92m✓ Resolved {placeholder_count} paste placeholder(s)\033[0m")
    
    return resolved_text


def cleanup_old_pastes(max_age_hours: int = 24) -> int:
    """Clean up old paste files.
    
    Args:
        max_age_hours: Maximum age in hours for paste files
        
    Returns:
        Number of files cleaned up
    """
    paste_manager = get_paste_manager()
    return paste_manager.cleanup_old_pastes(max_age_hours)


def list_paste_files() -> list[str]:
    """List all paste file IDs.
    
    Returns:
        List of paste file IDs
    """
    paste_manager = get_paste_manager()
    return paste_manager.list_pastes() 