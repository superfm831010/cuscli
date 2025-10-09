"""Utility functions for terminal paste module."""

import os
import re
from typing import Optional, Tuple
from datetime import datetime, timedelta


def is_valid_paste_id(paste_id: str) -> bool:
    """Check if a paste ID is valid.
    
    Args:
        paste_id: Paste ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not paste_id:
        return False
        
    # Handle both "pasted-<uuid>" and just "<uuid>" formats
    if paste_id.startswith("pasted-"):
        uuid_part = paste_id[7:]  # Remove "pasted-" prefix
    else:
        uuid_part = paste_id
        
    # Check if it's a valid 32-character hex string (UUID without dashes)
    return bool(re.match(r"^[0-9a-f]{32}$", uuid_part))


def format_paste_info(paste_id: str, paste_dir: str) -> Optional[dict]:
    """Get formatted information about a paste file.
    
    Args:
        paste_id: Paste file ID
        paste_dir: Directory containing paste files
        
    Returns:
        Dictionary with paste information or None if file not found
    """
    if not is_valid_paste_id(paste_id):
        return None
        
    # Ensure paste_id has proper format
    if not paste_id.startswith("pasted-"):
        paste_id = f"pasted-{paste_id}"
        
    file_path = os.path.join(paste_dir, paste_id)
    
    if not os.path.exists(file_path):
        return None
        
    try:
        stat = os.stat(file_path)
        created_time = datetime.fromtimestamp(stat.st_ctime)
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        file_size = stat.st_size
        
        # Read first few lines for preview
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
            preview = "\n".join(lines[:3])
            if len(lines) > 3:
                preview += f"\n... ({len(lines) - 3} more lines)"
                
        return {
            "id": paste_id,
            "path": file_path,
            "size": file_size,
            "created": created_time,
            "modified": modified_time,
            "line_count": len(lines),
            "preview": preview[:200] + "..." if len(preview) > 200 else preview
        }
        
    except Exception:
        return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp as time ago string.
    
    Args:
        timestamp: Timestamp to format
        
    Returns:
        Human-readable time ago string
    """
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def extract_placeholder_ids(text: str) -> list[str]:
    """Extract all paste placeholder IDs from text.
    
    Args:
        text: Text to search for placeholders
        
    Returns:
        List of paste IDs found in text
    """
    if not text:
        return []
        
    pattern = re.compile(r"\[pasted-([0-9a-f]{32})\]")
    matches = pattern.findall(text)
    return [f"pasted-{match}" for match in matches]


def validate_paste_directory(paste_dir: str) -> Tuple[bool, str]:
    """Validate paste directory and return status.
    
    Args:
        paste_dir: Directory path to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        if not os.path.exists(paste_dir):
            return False, f"Directory does not exist: {paste_dir}"
            
        if not os.path.isdir(paste_dir):
            return False, f"Path is not a directory: {paste_dir}"
            
        if not os.access(paste_dir, os.R_OK | os.W_OK):
            return False, f"Directory is not readable/writable: {paste_dir}"
            
        return True, "Directory is valid"
        
    except Exception as e:
        return False, f"Error validating directory: {e}" 