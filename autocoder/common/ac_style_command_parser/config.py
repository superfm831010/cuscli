from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Union, Any, Callable, Type
import re


class ArgType(Enum):
    """参数类型枚举"""
    POSITIONAL = auto()  # 位置参数
    KEYWORD = auto()     # 键值对参数
    MIXED = auto()       # 混合参数（同时支持位置和键值对）
    FLAG = auto()        # 标志参数（无值，只有存在与否）


class ParamConstraint(Enum):
    """参数约束类型"""
    REQUIRED = auto()    # 必需参数
    OPTIONAL = auto()    # 可选参数
    REMAINDER = auto()   # 收集剩余参数


@dataclass
class ArgumentConfig:
    """单个参数的配置"""
    name: str
    type: Type = str  # Python类型
    constraint: ParamConstraint = ParamConstraint.OPTIONAL
    default: Any = None
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None
    choices: Optional[List[Any]] = None
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        验证参数值
        
        返回:
            tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        # 检查选项
        if self.choices and value not in self.choices:
            return False, f"Value must be one of {self.choices}"
        
        # 自定义验证器
        if self.validator:
            try:
                if not self.validator(value):
                    return False, f"Validation failed for {self.name}"
            except Exception as e:
                return False, str(e)
        
        # 类型转换验证
        if self.type != str:
            try:
                self.type(value)
            except (ValueError, TypeError):
                return False, f"Cannot convert to {self.type.__name__}"
        
        return True, None


@dataclass
class CommandConfig:
    """
    单个命令的配置
    
    Example:
        >>> config = CommandConfig(
        ...     name="deploy",
        ...     arg_type=ArgType.MIXED,
        ...     positional_args=[
        ...         ArgumentConfig("app_name", constraint=ParamConstraint.REQUIRED),
        ...         ArgumentConfig("version", default="latest")
        ...     ],
        ...     keyword_args={
        ...         "env": ArgumentConfig("env", choices=["dev", "prod"]),
        ...         "force": ArgumentConfig("force", type=bool, default=False)
        ...     }
        ... )
    """
    name: str
    arg_type: ArgType = ArgType.MIXED
    positional_args: List[ArgumentConfig] = field(default_factory=list)
    keyword_args: Dict[str, ArgumentConfig] = field(default_factory=dict)
    max_positional: Optional[int] = None  # 最大位置参数数量
    min_positional: int = 0  # 最小位置参数数量
    collect_remainder: bool = False  # 是否收集剩余参数
    remainder_name: str = "remainder"  # 剩余参数的名称
    description: str = ""
    aliases: List[str] = field(default_factory=list)  # 命令别名
    
    def __post_init__(self):
        """初始化后的验证"""
        if self.arg_type == ArgType.POSITIONAL and self.keyword_args:
            raise ValueError(f"Command '{self.name}' with POSITIONAL arg_type cannot have keyword_args")
        
        if self.arg_type == ArgType.KEYWORD and self.positional_args:
            raise ValueError(f"Command '{self.name}' with KEYWORD arg_type cannot have positional_args")
        
        # 计算必需的位置参数数量
        required_count = sum(1 for arg in self.positional_args 
                           if arg.constraint == ParamConstraint.REQUIRED)
        if required_count > self.min_positional:
            self.min_positional = required_count
    
    def validate_args(self, args: List[str], kwargs: Dict[str, str]) -> tuple[bool, List[str]]:
        """
        验证参数
        
        返回:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 验证参数类型
        if self.arg_type == ArgType.POSITIONAL and kwargs:
            errors.append(f"Command '{self.name}' does not accept keyword arguments")
        
        if self.arg_type == ArgType.KEYWORD and args:
            errors.append(f"Command '{self.name}' does not accept positional arguments")
        
        # 验证位置参数数量
        if self.arg_type in [ArgType.POSITIONAL, ArgType.MIXED]:
            if len(args) < self.min_positional:
                errors.append(f"Command '{self.name}' requires at least {self.min_positional} positional arguments")
            
            if self.max_positional and len(args) > self.max_positional:
                if not self.collect_remainder:
                    errors.append(f"Command '{self.name}' accepts at most {self.max_positional} positional arguments")
        
        # 验证具体的位置参数
        for i, arg_config in enumerate(self.positional_args):
            if i < len(args):
                valid, error = arg_config.validate(args[i])
                if not valid:
                    errors.append(f"Positional argument {i+1} ({arg_config.name}): {error}")
            elif arg_config.constraint == ParamConstraint.REQUIRED:
                errors.append(f"Missing required positional argument: {arg_config.name}")
        
        # 验证键值对参数
        if self.arg_type in [ArgType.KEYWORD, ArgType.MIXED]:
            for key, value in kwargs.items():
                if key in self.keyword_args:
                    valid, error = self.keyword_args[key].validate(value)
                    if not valid:
                        errors.append(f"Keyword argument '{key}': {error}")
                else:
                    # 未知的键值对参数
                    if not self.collect_remainder:
                        errors.append(f"Unknown keyword argument: {key}")
            
            # 检查必需的键值对参数
            for key, arg_config in self.keyword_args.items():
                if arg_config.constraint == ParamConstraint.REQUIRED and key not in kwargs:
                    errors.append(f"Missing required keyword argument: {key}")
        
        return len(errors) == 0, errors


@dataclass
class ParserConfig:
    """
    解析器的完整配置
    
    Example:
        >>> config = ParserConfig()
        >>> config.add_command(
        ...     CommandConfig(
        ...         name="model",
        ...         arg_type=ArgType.POSITIONAL,
        ...         positional_args=[
        ...             ArgumentConfig("model_name", constraint=ParamConstraint.REQUIRED)
        ...         ],
        ...         max_positional=1
        ...     )
        ... )
        >>> config.add_command(
        ...     CommandConfig(
        ...         name="config",
        ...         arg_type=ArgType.KEYWORD,
        ...         keyword_args={
        ...             "temperature": ArgumentConfig("temperature", type=float),
        ...             "max_tokens": ArgumentConfig("max_tokens", type=int)
        ...         }
        ...     )
        ... )
    """
    commands: Dict[str, CommandConfig] = field(default_factory=dict)
    strict_mode: bool = False  # 严格模式：未配置的命令将报错
    case_sensitive: bool = True  # 命令名大小写敏感
    allow_unknown_commands: bool = True  # 是否允许未知命令
    collect_remainder: bool = False  # 是否在全局级别收集剩余参数
    remainder_name: str = "query"  # 剩余参数的名称
    command_prefix: str = "/"  # 命令前缀
    
    def add_command(self, config: CommandConfig) -> 'ParserConfig':
        """
        添加命令配置（支持链式调用）
        
        Args:
            config: 命令配置
            
        Returns:
            self: 返回自身以支持链式调用
        """
        self.commands[config.name] = config
        # 添加别名
        for alias in config.aliases:
            self.commands[alias] = config
        return self
    
    def remove_command(self, name: str) -> 'ParserConfig':
        """移除命令配置"""
        if name in self.commands:
            config = self.commands[name]
            del self.commands[name]
            # 移除别名
            for alias in config.aliases:
                if alias in self.commands:
                    del self.commands[alias]
        return self
    
    def get_command_config(self, name: str) -> Optional[CommandConfig]:
        """获取命令配置"""
        if not self.case_sensitive:
            name = name.lower()
            for cmd_name, config in self.commands.items():
                if cmd_name.lower() == name:
                    return config
        return self.commands.get(name)
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        验证配置的完整性和一致性
        
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查命令名冲突
        seen_names = set()
        for name in self.commands.keys():
            lower_name = name.lower() if not self.case_sensitive else name
            if lower_name in seen_names:
                errors.append(f"Duplicate command name: {name}")
            seen_names.add(lower_name)
        
        # 验证每个命令配置
        for name, config in self.commands.items():
            if config.name != name and name not in config.aliases:
                errors.append(f"Command name mismatch: {name} vs {config.name}")
        
        return len(errors) == 0, errors


class ConfigBuilder:
    """
    配置构建器，提供流式API来构建配置
    
    Example:
        >>> config = (ConfigBuilder()
        ...     .command("model")
        ...         .positional("name", required=True)
        ...         .max_args(1)
        ...     .command("config")
        ...         .keyword("temperature", type=float, default=0.7)
        ...         .keyword("max_tokens", type=int, choices=[100, 500, 1000])
        ...     .build()
        ... )
    """
    
    def __init__(self):
        self.parser_config = ParserConfig()
        self.current_command: Optional[CommandConfig] = None
        self._positional_args: List[ArgumentConfig] = []
        self._keyword_args: Dict[str, ArgumentConfig] = {}
    
    def command(self, name: str, arg_type: ArgType = ArgType.MIXED, 
                description: str = "", aliases: Optional[List[str]] = None) -> 'ConfigBuilder':
        """开始配置一个新命令"""
        # 保存之前的命令
        self._save_current_command()
        
        # 创建新命令
        self.current_command = CommandConfig(
            name=name,
            arg_type=arg_type,
            description=description,
            aliases=aliases or []
        )
        self._positional_args = []
        self._keyword_args = {}
        return self
    
    def positional(self, name: str, type: Type = str, required: bool = False,
                  default: Any = None, description: str = "",
                  validator: Optional[Callable] = None,
                  choices: Optional[List[Any]] = None) -> 'ConfigBuilder':
        """添加位置参数"""
        if not self.current_command:
            raise ValueError("Must call command() first")
        
        constraint = ParamConstraint.REQUIRED if required else ParamConstraint.OPTIONAL
        arg_config = ArgumentConfig(
            name=name,
            type=type,
            constraint=constraint,
            default=default,
            description=description,
            validator=validator,
            choices=choices
        )
        self._positional_args.append(arg_config)
        return self
    
    def keyword(self, name: str, type: Type = str, required: bool = False,
               default: Any = None, description: str = "",
               validator: Optional[Callable] = None,
               choices: Optional[List[Any]] = None) -> 'ConfigBuilder':
        """添加键值对参数"""
        if not self.current_command:
            raise ValueError("Must call command() first")
        
        constraint = ParamConstraint.REQUIRED if required else ParamConstraint.OPTIONAL
        arg_config = ArgumentConfig(
            name=name,
            type=type,
            constraint=constraint,
            default=default,
            description=description,
            validator=validator,
            choices=choices
        )
        self._keyword_args[name] = arg_config
        return self
    
    def max_args(self, count: int) -> 'ConfigBuilder':
        """设置最大位置参数数量"""
        if not self.current_command:
            raise ValueError("Must call command() first")
        self.current_command.max_positional = count
        return self
    
    def min_args(self, count: int) -> 'ConfigBuilder':
        """设置最小位置参数数量"""
        if not self.current_command:
            raise ValueError("Must call command() first")
        self.current_command.min_positional = count
        return self
    
    def collect_remainder(self, name: str = "query") -> 'ConfigBuilder':
        """配置收集剩余参数。如果在命令上下文中，则设置命令级别；否则设置全局级别"""
        if self.current_command:
            # 在命令上下文中，设置命令级别的收集剩余参数
            self.current_command.collect_remainder = True
            self.current_command.remainder_name = name
        else:
            # 不在命令上下文中，设置全局级别的收集剩余参数
            self.parser_config.collect_remainder = True
            self.parser_config.remainder_name = name
        return self
    
    def command_collect_remainder(self, enabled: bool = True, name: str = "remainder") -> 'ConfigBuilder':
        """配置当前命令级别收集剩余参数（把剩余位置参数拼接成一个参数）"""
        if not self.current_command:
            raise ValueError("Must call command() first")
        self.current_command.collect_remainder = enabled
        self.current_command.remainder_name = name
        return self
    
    def strict(self, enabled: bool = True) -> 'ConfigBuilder':
        """设置严格模式"""
        self.parser_config.strict_mode = enabled
        return self
    
    def case_sensitive(self, enabled: bool = True) -> 'ConfigBuilder':
        """设置大小写敏感"""
        self.parser_config.case_sensitive = enabled
        return self
    
    def _save_current_command(self):
        """保存当前命令配置"""
        if self.current_command:
            self.current_command.positional_args = self._positional_args
            self.current_command.keyword_args = self._keyword_args
            self.parser_config.add_command(self.current_command)
    
    def build(self) -> ParserConfig:
        """构建最终的配置"""
        self._save_current_command()
        valid, errors = self.parser_config.validate()
        if not valid:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
        return self.parser_config


def create_config() -> ConfigBuilder:
    """
    创建配置构建器的便捷函数
    
    Example:
        >>> config = (create_config()
        ...     .command("async")
        ...     .command("model")
        ...         .positional("name", required=True)
        ...         .max_args(1)
        ...     .command("task-prefix")
        ...         .positional("prefix", required=True)
        ...         .collect_remainder("query")
        ...     .build()
        ... )
    """
    return ConfigBuilder()
    
    def command_collect_remainder(self, enabled: bool = True, name: str = "remainder") -> 'ConfigBuilder':
        """配置当前命令级别收集剩余参数（把剩余位置参数拼接成一个参数）"""
        if not self.current_command:
            raise ValueError("Must call command() first")
        self.current_command.collect_remainder = enabled
        self.current_command.remainder_name = name
        return self