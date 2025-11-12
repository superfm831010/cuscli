"""Paste manager for handling paste file operations."""

import os
import uuid
from typing import Optional
from pathlib import Path


class PasteManager:
    """Manager for handling paste file operations."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize paste manager.
        
        Args:
            base_dir: Base directory for paste files. If None, uses current working directory.
        """
        self.base_dir = base_dir or os.getcwd()
        self.paste_dir = os.path.join(self.base_dir, ".auto-coder", "pastes")
        self._ensure_paste_dir()
    
    def _ensure_paste_dir(self) -> None:
        """Ensure paste directory exists."""
        os.makedirs(self.paste_dir, exist_ok=True)
    
    def save_paste(self, content: str) -> str:
        """Save paste content to file and return file ID.
        
        Args:
            content: Content to save
            
        Returns:
            File ID (without path)
        """
        file_id = f"pasted-{uuid.uuid4().hex}"
        file_path = os.path.join(self.paste_dir, file_id)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return file_id
        except Exception as e:
            raise RuntimeError(f"Failed to save paste content: {e}")
    
    def read_paste(self, file_id: str) -> Optional[str]:
        """Read paste content from file.
        
        Args:
            file_id: File ID to read
            
        Returns:
            File content or None if file not found
        """
        # Handle both "pasted-<uuid>" and just "<uuid>" formats
        if not file_id.startswith("pasted-"):
            file_id = f"pasted-{file_id}"
            
        file_path = os.path.join(self.paste_dir, file_id)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to read paste file {file_id}: {e}")
    
    def cleanup_old_pastes(self, max_age_hours: int = 24) -> int:
        """Clean up old paste files.
        
        Args:
            max_age_hours: Maximum age in hours for paste files
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        if not os.path.exists(self.paste_dir):
            return 0
            
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        try:
            for filename in os.listdir(self.paste_dir):
                if filename.startswith("pasted-"):
                    file_path = os.path.join(self.paste_dir, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            cleaned_count += 1
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup old pastes: {e}")
            
        return cleaned_count
    
    def list_pastes(self) -> list[str]:
        """List all paste file IDs.
        
        Returns:
            List of paste file IDs
        """
        if not os.path.exists(self.paste_dir):
            return []
            
        try:
            files = []
            for filename in os.listdir(self.paste_dir):
                if filename.startswith("pasted-") and os.path.isfile(
                    os.path.join(self.paste_dir, filename)
                ):
                    files.append(filename)
            return sorted(files)
        except Exception as e:
            raise RuntimeError(f"Failed to list paste files: {e}") 