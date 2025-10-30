"""
LangChain Memory Manager for Network Chatbot

Provides conversation memory management using LangChain to maintain context
across multiple chat turns. Integrates with Django's Conversation/Message models.
"""
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)

# Lazy imports for LangChain (only load when needed)
_LANGCHAIN_AVAILABLE = False
_ConversationBufferMemory = None
_ConversationBufferWindowMemory = None
_ConversationSummaryMemory = None

try:
    from langchain.memory import (
        ConversationBufferMemory,
        ConversationBufferWindowMemory,
        ConversationSummaryMemory,
    )
    from langchain.schema import HumanMessage, AIMessage
    _LANGCHAIN_AVAILABLE = True
    _ConversationBufferMemory = ConversationBufferMemory
    _ConversationBufferWindowMemory = ConversationBufferWindowMemory
    _ConversationSummaryMemory = ConversationSummaryMemory
    logger.info("LangChain memory modules loaded successfully")
except ImportError as e:
    logger.warning(f"LangChain not available: {e}. Memory features disabled.")


class ChatbotMemoryManager:
    """
    Manages conversation memory using LangChain.
    
    Features:
    - Buffer Memory: Stores full conversation history
    - Window Memory: Stores last N messages (configurable)
    - Summary Memory: Summarizes old messages to save tokens
    
    Environment Variables:
        CHATBOT_MEMORY_TYPE: buffer | window | summary (default: window)
        CHATBOT_MEMORY_WINDOW_SIZE: Number of messages to remember (default: 10)
        CHATBOT_MEMORY_MAX_TOKEN_LIMIT: Max tokens for summary mode (default: 2000)
    """
    
    def __init__(
        self,
        conversation_id: str,
        memory_type: Optional[str] = None,
        window_size: Optional[int] = None,
    ):
        """
        Initialize memory manager for a conversation.
        
        Args:
            conversation_id: UUID of the Django Conversation object
            memory_type: Type of memory (buffer, window, summary)
            window_size: Number of messages to keep (for window mode)
        """
        self.conversation_id = conversation_id
        self.memory_type = memory_type or os.getenv("CHATBOT_MEMORY_TYPE", "window")
        self.window_size = window_size or int(os.getenv("CHATBOT_MEMORY_WINDOW_SIZE", "10"))
        self.max_token_limit = int(os.getenv("CHATBOT_MEMORY_MAX_TOKEN_LIMIT", "2000"))
        
        self.memory = None
        self._enabled = _LANGCHAIN_AVAILABLE
        
        if self._enabled:
            self._initialize_memory()
        else:
            logger.warning(f"Memory manager for {conversation_id} created but LangChain unavailable")
    
    def _initialize_memory(self):
        """Initialize the appropriate LangChain memory type."""
        if not self._enabled:
            return
        
        try:
            if self.memory_type == "buffer":
                # Full conversation history
                self.memory = _ConversationBufferMemory(
                    memory_key="history",
                    return_messages=True,
                    input_key="input",
                    output_key="output"
                )
                logger.info(f"Initialized BufferMemory for conversation {self.conversation_id}")
            
            elif self.memory_type == "window":
                # Last N messages only
                self.memory = _ConversationBufferWindowMemory(
                    k=self.window_size,
                    memory_key="history",
                    return_messages=True,
                    input_key="input",
                    output_key="output"
                )
                logger.info(f"Initialized WindowMemory (k={self.window_size}) for conversation {self.conversation_id}")
            
            elif self.memory_type == "summary":
                # Summarized history (requires LLM - not implemented yet)
                logger.warning("Summary memory requires LLM integration. Falling back to window memory.")
                self.memory = _ConversationBufferWindowMemory(
                    k=self.window_size,
                    memory_key="history",
                    return_messages=True
                )
            
            else:
                logger.error(f"Unknown memory type: {self.memory_type}. Falling back to window.")
                self.memory = _ConversationBufferWindowMemory(k=self.window_size, memory_key="history", return_messages=True)
        
        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}", exc_info=True)
            self._enabled = False
    
    def add_user_message(self, message: str):
        """Add a user message to memory."""
        if not self._enabled or not self.memory:
            return
        
        try:
            self.memory.chat_memory.add_user_message(message)
            logger.debug(f"Added user message to conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Failed to add user message: {e}")
    
    def add_ai_message(self, message: str):
        """Add an AI response to memory."""
        if not self._enabled or not self.memory:
            return
        
        try:
            self.memory.chat_memory.add_ai_message(message)
            logger.debug(f"Added AI message to conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Failed to add AI message: {e}")
    
    def get_context(self) -> str:
        """
        Get formatted conversation history as context string.
        
        Returns:
            Formatted conversation history or empty string if unavailable
        """
        if not self._enabled or not self.memory:
            return ""
        
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return ""
            
            # Format messages as context
            context_lines = []
            for msg in messages:
                if hasattr(msg, 'type'):
                    if msg.type == "human":
                        context_lines.append(f"User: {msg.content}")
                    elif msg.type == "ai":
                        context_lines.append(f"Assistant: {msg.content}")
            
            return "\n".join(context_lines)
        
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return ""
    
    def get_last_n_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """
        Get last N messages as list of dicts.
        
        Args:
            n: Number of recent messages to retrieve
            
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        if not self._enabled or not self.memory:
            return []
        
        try:
            messages = self.memory.chat_memory.messages[-n:]
            result = []
            for msg in messages:
                if hasattr(msg, 'type'):
                    role = "user" if msg.type == "human" else "assistant"
                    result.append({"role": role, "content": msg.content})
            return result
        except Exception as e:
            logger.error(f"Failed to get last messages: {e}")
            return []
    
    def clear(self):
        """Clear conversation memory."""
        if not self._enabled or not self.memory:
            return
        
        try:
            self.memory.clear()
            logger.info(f"Cleared memory for conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
    
    def load_from_django_messages(self, messages):
        """
        Load conversation history from Django Message queryset.
        
        Args:
            messages: QuerySet of Message objects ordered by created_at
        """
        if not self._enabled or not self.memory:
            return
        
        try:
            for msg in messages:
                if msg.role == "user":
                    self.memory.chat_memory.add_user_message(msg.content)
                elif msg.role == "assistant":
                    self.memory.chat_memory.add_ai_message(msg.content)
            
            logger.info(f"Loaded {messages.count()} messages into memory for conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Failed to load Django messages: {e}", exc_info=True)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about current memory state."""
        if not self._enabled or not self.memory:
            return {"enabled": False, "message_count": 0}
        
        try:
            messages = self.memory.chat_memory.messages
            return {
                "enabled": True,
                "memory_type": self.memory_type,
                "message_count": len(messages),
                "window_size": self.window_size if self.memory_type == "window" else None,
                "conversation_id": self.conversation_id
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"enabled": False, "error": str(e)}
    
    def is_enabled(self) -> bool:
        """Check if memory management is enabled."""
        return self._enabled and self.memory is not None


# Singleton cache for memory managers (keyed by conversation_id)
_memory_cache: Dict[str, ChatbotMemoryManager] = {}


def get_memory_manager(conversation_id: str) -> ChatbotMemoryManager:
    """
    Get or create a memory manager for a conversation.
    
    Args:
        conversation_id: UUID string of the conversation
        
    Returns:
        ChatbotMemoryManager instance
    """
    if conversation_id not in _memory_cache:
        _memory_cache[conversation_id] = ChatbotMemoryManager(conversation_id)
    
    return _memory_cache[conversation_id]


def clear_memory_cache():
    """Clear all cached memory managers (useful for testing)."""
    global _memory_cache
    _memory_cache.clear()
    logger.info("Cleared all memory manager caches")
