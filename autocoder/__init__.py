"""Auto-Coder root package

Early logger configuration to suppress unwanted console output before any
sub-modules add their own handlers.
"""

from __future__ import annotations

import os
from loguru import logger as _logger

# Import version
from autocoder.version import __version__

# --- Early logger setup ----------------------------------------------------
# Remove Loguru default handler immediately. This guarantees that *no* log
# record is printed to stdout/stderr before we explicitly configure sinks.
_logger.remove()

# Add a file sink so logs are still preserved.
_log_dir = os.path.join(os.getcwd(), ".auto-coder", "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, "auto-coder.log")

_logger.add(
    _log_file,
    level="INFO",
    rotation="10 MB",
    retention="1 week",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
)
