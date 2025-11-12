"""
Pruner module for AutoCoder.

This module provides various conversation and content pruning capabilities including:
- Context pruning for file contents
- Conversation pruning for chat history
- Agentic conversation pruning for tool outputs
- Range-based conversation pruning with pair preservation
"""

# Core pruning classes
from .context_pruner import PruneContext
from .conversation_pruner import ConversationPruner
from .agentic_conversation_pruner import AgenticConversationPruner
from .tool_content_detector import ToolContentDetector

# Message IDs-based pruning (replacing range-based pruning)
from .conversation_message_ids_manager import (
    ConversationMessageIds, 
    ConversationMessageIdsManager, 
    get_conversation_message_ids_manager
)
from .conversation_message_ids_api import (
    ConversationMessageIdsAPI,
    MessageIdsValidationResult,
    MessageIdsParseResult,
    get_conversation_message_ids_api
)
from .conversation_message_ids_pruner import (
    ConversationMessageIdsPruner,
    MessageIdsPruningResult,
    MessagePair
)
from .conversation_normalizer import (
    ConversationNormalizer,
    NormalizationStrategy,
    NormalizationResult
)

__all__ = [
    # Core pruning
    "PruneContext",
    "ConversationPruner", 
    "AgenticConversationPruner",
    "ToolContentDetector",
    
    # Message IDs-based pruning - Manager layer
    "ConversationMessageIds",
    "ConversationMessageIdsManager",
    "get_conversation_message_ids_manager",
    
    # Message IDs-based pruning - API layer
    "ConversationMessageIdsAPI",
    "MessageIdsValidationResult", 
    "MessageIdsParseResult",
    "get_conversation_message_ids_api",
    
    # Message IDs-based pruning - Pruner layer
    "ConversationMessageIdsPruner",
    "MessageIdsPruningResult",
    "MessagePair",
    
    # Conversation normalization
    "ConversationNormalizer",
    "NormalizationStrategy",
    "NormalizationResult"
]
