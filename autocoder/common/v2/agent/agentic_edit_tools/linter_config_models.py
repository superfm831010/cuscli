"""
Pydantic models for linter configuration with type validation and defaults.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from pathlib import Path


class FilePatterns(BaseModel):
    """File pattern configuration for include/exclude rules."""
    
    include: List[str] = Field(
        default=["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.java"],
        description="List of glob patterns for files to include in linting"
    )
    exclude: List[str] = Field(
        default=["*.test.*", "*.spec.*", "__pycache__", "node_modules", ".git"],
        description="List of glob patterns for files to exclude from linting"
    )
    
    @validator('include', 'exclude', pre=True)
    def ensure_list(cls, v):
        """Ensure the value is a list."""
        if isinstance(v, str):
            return [v]
        return v


class PythonConfig(BaseModel):
    """Python-specific linter configuration."""
    
    use_mypy: bool = Field(
        default=True,
        description="Enable mypy type checking"
    )
    flake8_args: List[str] = Field(
        default_factory=list,
        description="Additional arguments for flake8"
    )
    mypy_args: List[str] = Field(
        default_factory=list,
        description="Additional arguments for mypy"
    )
    flake8_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for flake8 execution in seconds"
    )
    mypy_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for mypy execution in seconds"
    )


class TypeScriptConfig(BaseModel):
    """TypeScript-specific linter configuration."""
    
    use_eslint: bool = Field(
        default=True,
        description="Enable ESLint checking"
    )
    tsc_args: List[str] = Field(
        default=["--noEmit", "--strict"],
        description="Arguments for TypeScript compiler"
    )
    eslint_args: List[str] = Field(
        default_factory=list,
        description="Additional arguments for ESLint"
    )
    tsconfig_path: Optional[str] = Field(
        default=None,
        description="Path to tsconfig.json file"
    )
    tsc_timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Timeout for tsc execution in seconds"
    )
    eslint_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for ESLint execution in seconds"
    )
    
    @validator('tsconfig_path')
    def validate_tsconfig_path(cls, v):
        """Validate tsconfig path if provided."""
        if v and not Path(v).exists():
            # Don't fail, just log warning (file might be created later)
            pass
        return v


class JavaConfig(BaseModel):
    """Java-specific linter configuration."""
    
    javac_args: List[str] = Field(
        default_factory=list,
        description="Additional arguments for javac"
    )
    javac_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for javac execution in seconds"
    )
    project_type: Literal["auto", "maven", "gradle", "local"] = Field(
        default="auto",
        description="Project type for dependency resolution"
    )
    source_paths: List[str] = Field(
        default=["src", "src/main/java"],
        description="Source directories to search"
    )
    lib_dirs: List[str] = Field(
        default=["lib", "libs"],
        description="Directories containing JAR files"
    )
    enable_dependency_resolution: bool = Field(
        default=True,
        description="Enable automatic dependency resolution"
    )
    cache_dependencies: bool = Field(
        default=True,
        description="Cache resolved classpaths for performance"
    )
    release: str = Field(
        default="8",
        description="Java release version"
    )
    use_release_flag: bool = Field(
        default=True,
        description="Use --release flag (can be disabled for older javac)"
    )


class LanguageConfig(BaseModel):
    """Container for all language-specific configurations."""
    
    python: PythonConfig = Field(
        default_factory=PythonConfig,
        description="Python linter configuration"
    )
    typescript: TypeScriptConfig = Field(
        default_factory=TypeScriptConfig,
        description="TypeScript linter configuration"
    )
    java: JavaConfig = Field(
        default_factory=JavaConfig,
        description="Java linter configuration"
    )
    
    class Config:
        extra = "allow"  # Allow additional language configurations


class ReportConfig(BaseModel):
    """Linter report configuration."""
    
    format: Literal["simple", "detailed", "json"] = Field(
        default="simple",
        description="Report format"
    )
    include_in_result: bool = Field(
        default=True,
        description="Include lint report in ToolResult content"
    )
    save_to_file: bool = Field(
        default=False,
        description="Save lint reports to files"
    )
    file_path: str = Field(
        default=".auto-coder/lint-reports/",
        description="Directory path for saving lint reports"
    )
    max_issues_shown: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of issues to show in report"
    )


class LinterConfig(BaseModel):
    """Main linter configuration model with type validation."""
    
    enabled: bool = Field(
        default=False,
        description="Global linter enable/disable switch"
    )
    mode: Literal["warning", "blocking", "silent"] = Field(
        default="warning",
        description="Linter operation mode"
    )
    check_before_modification: bool = Field(
        default=False,
        description="Run linter before applying modifications"
    )
    check_after_modification: bool = Field(
        default=True,
        description="Run linter after applying modifications"
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum parallel workers for linting"
    )
    timeout: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Global timeout for linting operations in seconds"
    )
    file_patterns: FilePatterns = Field(
        default_factory=FilePatterns,
        description="File include/exclude patterns"
    )
    language_config: LanguageConfig = Field(
        default_factory=LanguageConfig,
        description="Language-specific configurations"
    )
    report: ReportConfig = Field(
        default_factory=ReportConfig,
        description="Report generation configuration"
    )
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        use_enum_values = True
        extra = "forbid"  # Don't allow extra fields at root level
        json_schema_extra = {
            "example": {
                "enabled": True,
                "mode": "warning",
                "check_after_modification": True,
                "file_patterns": {
                    "include": ["*.py", "*.ts"],
                    "exclude": ["*.test.*"]
                },
                "language_config": {
                    "python": {
                        "use_mypy": True,
                        "flake8_args": ["--max-line-length=120"]
                    }
                },
                "report": {
                    "format": "detailed",
                    "include_in_result": True
                }
            }
        }
    
    @validator('mode')
    def validate_mode(cls, v):
        """Validate linter mode."""
        valid_modes = ["warning", "blocking", "silent"]
        if v not in valid_modes:
            raise ValueError(f"Invalid mode: {v}. Must be one of {valid_modes}")
        return v
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LinterConfig':
        """
        Create LinterConfig from a dictionary, handling nested 'linter' key.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            LinterConfig instance
        """
        # Handle both direct config and nested under 'linter' key
        if 'linter' in config_dict:
            config_data = config_dict['linter']
        else:
            config_data = config_dict
        
        # Handle legacy 'language_config' key mapping
        if 'language_config' in config_data:
            lang_config = config_data['language_config']
            
            # Map old config structure to new structure
            if 'python_config' in lang_config:
                lang_config['python'] = lang_config.pop('python_config')
            if 'typescript_config' in lang_config:
                lang_config['typescript'] = lang_config.pop('typescript_config')
            if 'java_config' in lang_config:
                lang_config['java'] = lang_config.pop('java_config')
        
        return cls(**config_data)
    
    def to_manager_config(self) -> Dict[str, Any]:
        """
        Convert to LinterManager compatible configuration.
        
        Returns:
            Dictionary suitable for LinterManager initialization
        """
        manager_config = {
            'max_workers': self.max_workers,
            'timeout': self.timeout,
            'python_config': self.language_config.python.dict(),
            'typescript_config': self.language_config.typescript.dict(),
            'java_config': self.language_config.java.dict()
        }
        
        return manager_config
    
    def should_lint_file(self, file_path: str) -> bool:
        """
        Check if a file should be linted based on patterns.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be linted
        """
        if not self.enabled:
            return False
        
        from pathlib import Path
        path = Path(file_path)
        
        # Check exclude patterns first
        for pattern in self.file_patterns.exclude:
            if path.match(pattern):
                return False
        
        # Check include patterns
        for pattern in self.file_patterns.include:
            if pattern == '*' or path.match(pattern):
                return True
        
        return False