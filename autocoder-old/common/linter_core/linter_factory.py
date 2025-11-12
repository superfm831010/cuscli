"""
Factory for creating language-specific linters.
"""

from typing import Dict, Optional, Type, List, Any, Union
from pathlib import Path

from .base_linter import BaseLinter
from .linters.python_linter import PythonLinter
from .linters.typescript_linter import TypeScriptLinter
from .linters.java_linter import JavaLinter


class LinterFactory:
    """
    Factory class for creating language-specific linters.
    
    This factory provides methods to create linters based on file extensions,
    language names, or explicit linter types.
    """
    
    # Registry of available linters
    _linter_registry: Dict[str, Type[BaseLinter]] = {
        'python': PythonLinter,
        'typescript': TypeScriptLinter,
        'java': JavaLinter,
    }
    
    # Extension to language mapping
    _extension_mapping: Dict[str, str] = {
        '.py': 'python',
        '.pyx': 'python',
        '.pyi': 'python',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'typescript',  # Treat JS as TypeScript for linting
        '.jsx': 'typescript',
        '.java': 'java',
    }
    
    @classmethod
    def create_linter(cls, language: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseLinter]:
        """
        Create a linter for the specified language.
        
        Args:
            language: The programming language name (e.g., 'python', 'typescript')
            config: Optional configuration dictionary for the linter
            
        Returns:
            A linter instance for the specified language, or None if not supported
        """
        language = language.lower()
        linter_class = cls._linter_registry.get(language)
        
        if linter_class:
            return linter_class(config)
        
        return None
    
    @classmethod
    def create_linter_for_file(cls, file_path: Union[str, Path], 
                              config: Optional[Dict[str, Any]] = None) -> Optional[BaseLinter]:
        """
        Create a linter for the specified file based on its extension.
        
        Args:
            file_path: Path to the file to lint
            config: Optional configuration dictionary for the linter
            
        Returns:
            A linter instance for the file's language, or None if not supported
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        language = cls._extension_mapping.get(extension)
        if language:
            return cls.create_linter(language, config)
        
        return None
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """
        Get a list of supported programming languages.
        
        Returns:
            List of supported language names
        """
        return list(cls._linter_registry.keys())
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        Get a list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(cls._extension_mapping.keys())
    
    @classmethod
    def is_file_supported(cls, file_path: Union[str, Path]) -> bool:
        """
        Check if a file is supported by any available linter.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file can be linted, False otherwise
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        return extension in cls._extension_mapping
    
    @classmethod
    def register_linter(cls, language: str, linter_class: Type[BaseLinter], 
                       extensions: List[str]) -> None:
        """
        Register a new linter class for a language.
        
        This allows dynamic registration of new linters without modifying the core code.
        
        Args:
            language: The programming language name
            linter_class: The linter class to register
            extensions: List of file extensions this linter supports
        """
        if not issubclass(linter_class, BaseLinter):
            raise ValueError("Linter class must inherit from BaseLinter")
        
        # Register the linter
        cls._linter_registry[language.lower()] = linter_class
        
        # Register extensions
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            cls._extension_mapping[ext.lower()] = language.lower()
    
    @classmethod
    def unregister_linter(cls, language: str) -> None:
        """
        Unregister a linter for a language.
        
        Args:
            language: The programming language name to unregister
        """
        language = language.lower()
        
        # Remove from registry
        if language in cls._linter_registry:
            del cls._linter_registry[language]
        
        # Remove associated extensions
        extensions_to_remove = [ext for ext, lang in cls._extension_mapping.items() 
                               if lang == language]
        for ext in extensions_to_remove:
            del cls._extension_mapping[ext]
    
    @classmethod
    def get_available_linters(cls) -> Dict[str, bool]:
        """
        Get the availability status of all registered linters.
        
        Returns:
            Dictionary mapping language names to availability status
        """
        availability = {}
        
        for language, linter_class in cls._linter_registry.items():
            try:
                # Create a temporary instance to check availability
                linter = linter_class()
                availability[language] = linter.is_available()
            except Exception:
                availability[language] = False
        
        return availability
    
    @classmethod
    def get_linter_info(cls, language: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific linter.
        
        Args:
            language: The programming language name
            
        Returns:
            Dictionary containing linter information, or None if not found
        """
        language = language.lower()
        linter_class = cls._linter_registry.get(language)
        
        if not linter_class:
            return None
        
        try:
            # Create a temporary instance to get information
            linter = linter_class()
            
            return {
                'language': linter.language_name,
                'class_name': linter_class.__name__,
                'supported_extensions': linter.supported_extensions,
                'is_available': linter.is_available()
            }
        except Exception:
            return {
                'language': language,
                'class_name': linter_class.__name__,
                'supported_extensions': [],
                'is_available': False
            } 