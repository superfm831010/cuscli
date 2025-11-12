import locale
from typing import Dict, Any
from byzerllm.utils import format_str_jinja2


class MessageManager:
    """
    Central message manager for handling internationalization across the auto-coder project
    """
    
    def __init__(self):
        self._messages: Dict[str, Dict[str, str]] = {}
    
    def register_messages(self, messages: Dict[str, Dict[str, str]]):
        """
        Register a set of messages with the manager
        
        Args:
            messages: Dictionary of message keys to language-specific messages
        """
        self._messages.update(messages)
    
    def get_system_language(self) -> str:
        """
        Get the system's default language code
        
        Returns:
            Two-letter language code (e.g., 'en', 'zh'), falls back to 'en' for unsupported languages
        """
        try:
            lang_code, _ = locale.getdefaultlocale()
            if lang_code:
                detected_lang = lang_code[:2]
                # 检查是否是支持的语言，如果不是则回退到英文
                supported_languages = ['en', 'zh', 'ja', 'ar', 'ru']
                if detected_lang in supported_languages:
                    return detected_lang
                else:
                    return "en"
            return "en"
        except:
            return "en"
    
    def get_message(self, key: str) -> str:
        """
        Get a localized message by key
        
        Args:
            key: Message key to look up
            
        Returns:
            Localized message string, or empty string if not found
        """
        lang = self.get_system_language()
        if key in self._messages:
            return self._messages[key].get(lang, self._messages[key].get("en", ""))
        return ""
    
    def get_message_with_format(self, msg_key: str, **kwargs) -> str:
        """
        Get a localized message with template formatting
        
        Args:
            msg_key: Message key to look up
            **kwargs: Variables to substitute in the message template
            
        Returns:
            Formatted localized message string
        """
        message = self.get_message(msg_key)
        if message:
            return format_str_jinja2(message, **kwargs)
        return ""


# Global message manager instance
_global_message_manager = MessageManager()


def get_message_manager() -> MessageManager:
    """
    Get the global message manager instance
    
    Returns:
        Global MessageManager instance
    """
    return _global_message_manager


def register_messages(messages: Dict[str, Dict[str, str]]):
    """
    Register messages with the global message manager
    
    Args:
        messages: Dictionary of message keys to language-specific messages
    """
    _global_message_manager.register_messages(messages)


def get_system_language() -> str:
    """
    Get the system's default language code
    
    Returns:
        Two-letter language code (e.g., 'en', 'zh')
    """
    return _global_message_manager.get_system_language()


def get_message(key: str) -> str:
    """
    Get a localized message by key
    
    Args:
        key: Message key to look up
        
    Returns:
        Localized message string, or empty string if not found
    """
    return _global_message_manager.get_message(key)


def get_message_with_format(msg_key: str, **kwargs) -> str:
    """
    Get a localized message with template formatting
    
    Args:
        msg_key: Message key to look up
        **kwargs: Variables to substitute in the message template
        
    Returns:
        Formatted localized message string
    """
    return _global_message_manager.get_message_with_format(msg_key, **kwargs)


def get_supported_languages() -> list:
    """
    Get list of supported languages
    
    Returns:
        List of supported language codes
    """
    return ['en', 'zh', 'ja', 'ar', 'ru']


def is_language_supported(language: str) -> bool:
    """
    Check if a language is supported
    
    Args:
        language: Language code to check
        
    Returns:
        True if language is supported, False otherwise
    """
    return language in get_supported_languages() 