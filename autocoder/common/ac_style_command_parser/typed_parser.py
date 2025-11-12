from collections import OrderedDict
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
import re

from .parser import CommandParser
from .config import (
    ParserConfig,
    CommandConfig,
    ArgumentConfig,
    ArgType,
    ParamConstraint,
)


@dataclass
class ParsedCommand:
    """解析后的命令结果"""

    name: str
    args: List[Any] = field(default_factory=list)  # 转换后的类型
    kwargs: Dict[str, Any] = field(default_factory=dict)  # 转换后的类型
    raw_args: List[str] = field(default_factory=list)  # 原始字符串
    raw_kwargs: Dict[str, str] = field(default_factory=dict)  # 原始字符串
    remainder: Optional[str] = None  # 剩余参数
    errors: List[str] = field(default_factory=list)  # 解析错误

    @property
    def is_valid(self) -> bool:
        """是否有效（无错误）"""
        return len(self.errors) == 0


class TypedCommandParser(CommandParser):
    """
    支持类型和配置的命令解析器

    Example:
        >>> from autocoder.common.ac_style_command_parser import create_config
        >>>
        >>> # 创建配置
        >>> config = (create_config()
        ...     .command("model")
        ...         .positional("name", required=True, choices=["gpt-4", "gpt-3.5"])
        ...         .max_args(1)
        ...     .command("config")
        ...         .keyword("temperature", type=float, default=0.7)
        ...         .keyword("max_tokens", type=int)
        ...     .command("task-prefix")
        ...         .positional("prefix", required=True)
        ...         .collect_remainder("query")
        ...     .build()
        ... )
        >>>
        >>> # 创建解析器
        >>> parser = TypedCommandParser(config)
        >>>
        >>> # 解析命令
        >>> result = parser.parse_typed("/model gpt-4 /config temperature=0.8")
        >>> print(result["model"].args)  # ['gpt-4'] - 已验证
        >>> print(result["config"].kwargs)  # {'temperature': 0.8} - 已转换为float
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        初始化类型化命令解析器

        Args:
            config: 解析器配置，如果为None则使用默认配置
        """
        super().__init__()
        self.config = config or ParserConfig()

    def parse_typed(self, query: str) -> OrderedDict[str, ParsedCommand]:
        """
        解析命令并进行类型转换和验证

        Args:
            query: 命令行格式的查询字符串

        Returns:
            OrderedDict[str, ParsedCommand]: 解析和验证后的命令字典
        """
        # 使用基础解析器解析
        raw_commands = self.parse(query)

        # 如果配置了全局 collect_remainder，需要调整参数分配
        remainder_text = ""
        if self.config.collect_remainder and raw_commands:
            raw_commands, remainder_text = self._redistribute_args_for_global_remainder(
                raw_commands
            )

        # 处理每个命令
        typed_commands = OrderedDict()

        for cmd_name, cmd_info in raw_commands.items():
            raw_args = cmd_info["args"]
            raw_kwargs = cmd_info["kwargs"]

            # 获取命令配置
            cmd_config = self.config.get_command_config(cmd_name)

            if cmd_config:
                # 有配置，进行验证和转换
                parsed_cmd = self._process_configured_command(
                    cmd_name, cmd_config, raw_args, raw_kwargs
                )
            else:
                # 无配置
                if self.config.strict_mode:
                    # 严格模式下，未配置的命令是错误
                    parsed_cmd = ParsedCommand(
                        name=cmd_name,
                        raw_args=raw_args,
                        raw_kwargs=raw_kwargs,
                        errors=[f"Unknown command: {cmd_name}"],
                    )
                else:
                    # 非严格模式，保持原样
                    parsed_cmd = ParsedCommand(
                        name=cmd_name,
                        args=raw_args,
                        kwargs=raw_kwargs,
                        raw_args=raw_args,
                        raw_kwargs=raw_kwargs,
                    )

            typed_commands[cmd_name] = parsed_cmd

        # 如果有剩余文本，添加到特殊的 remainder 命令中
        if remainder_text:
            remainder_cmd = ParsedCommand(
                name=self.config.remainder_name,
                args=[remainder_text],
                kwargs={},
                raw_args=[remainder_text],
                raw_kwargs={},
                remainder=remainder_text,
            )
            typed_commands[self.config.remainder_name] = remainder_cmd

        return typed_commands

    def _process_configured_command(
        self,
        cmd_name: str,
        config: CommandConfig,
        raw_args: List[str],
        raw_kwargs: Dict[str, str],
    ) -> ParsedCommand:
        """
        处理有配置的命令

        Args:
            cmd_name: 命令名
            config: 命令配置
            raw_args: 原始位置参数
            raw_kwargs: 原始键值对参数

        Returns:
            ParsedCommand: 处理后的命令
        """
        parsed_cmd = ParsedCommand(
            name=cmd_name, raw_args=raw_args, raw_kwargs=raw_kwargs
        )

        # 验证参数
        valid, errors = config.validate_args(raw_args, raw_kwargs)
        if not valid:
            parsed_cmd.errors.extend(errors)

        # 处理位置参数
        converted_args = []
        remainder_args = []

        for i, arg_value in enumerate(raw_args):
            if i < len(config.positional_args):
                # 有对应的配置
                arg_config = config.positional_args[i]
                converted_value = self._convert_value(arg_value, arg_config.type)
                converted_args.append(converted_value)
            else:
                # 超出配置的参数
                if config.collect_remainder:
                    remainder_args.append(arg_value)
                else:
                    converted_args.append(arg_value)

        # 添加默认值
        for i in range(len(raw_args), len(config.positional_args)):
            arg_config = config.positional_args[i]
            if arg_config.default is not None:
                converted_args.append(arg_config.default)
            elif arg_config.constraint != ParamConstraint.REQUIRED:
                # 可选参数，不添加
                break

        parsed_cmd.args = converted_args

        # 处理剩余参数
        if config.collect_remainder and remainder_args:
            parsed_cmd.remainder = " ".join(remainder_args)

        # 处理键值对参数
        converted_kwargs = {}

        for key, value in raw_kwargs.items():
            if key in config.keyword_args:
                arg_config = config.keyword_args[key]
                converted_value = self._convert_value(value, arg_config.type)
                converted_kwargs[key] = converted_value
            else:
                # 未配置的键值对
                if not config.collect_remainder:
                    converted_kwargs[key] = value

        # 添加默认值
        for key, arg_config in config.keyword_args.items():
            if key not in converted_kwargs and arg_config.default is not None:
                converted_kwargs[key] = arg_config.default

        parsed_cmd.kwargs = converted_kwargs

        return parsed_cmd

    def _extract_remainder(self, raw_commands: OrderedDict, query: str) -> str:
        """
        提取剩余参数文本

        Args:
            raw_commands: 解析出的原始命令
            query: 原始查询字符串

        Returns:
            剩余参数文本
        """
        if not raw_commands:
            return ""

        # 获取最后一个命令
        last_cmd_name = list(raw_commands.keys())[-1]
        last_cmd_info = raw_commands[last_cmd_name]
        last_cmd_config = self.config.get_command_config(last_cmd_name)

        if not last_cmd_config:
            # 如果最后一个命令没有配置，将其所有参数作为剩余参数
            return " ".join(last_cmd_info["args"])

        # 根据最后一个命令的配置决定如何处理剩余参数
        raw_args = last_cmd_info["args"]
        raw_kwargs = last_cmd_info["kwargs"]

        remainder_args = []

        if last_cmd_config.arg_type in [ArgType.POSITIONAL, ArgType.MIXED]:
            # 如果有位置参数配置
            if last_cmd_config.positional_args:
                # 跳过已配置的位置参数数量
                configured_count = len(last_cmd_config.positional_args)
                if len(raw_args) > configured_count:
                    remainder_args = raw_args[configured_count:]
                elif len(raw_args) == configured_count and not raw_kwargs:
                    # 如果位置参数刚好匹配且没有键值对参数，检查是否还有未解析的文本
                    # 这种情况需要从原始查询中重新提取
                    return self._extract_text_after_last_command(query, raw_commands)
            else:
                # 没有位置参数配置，所有位置参数都是剩余参数
                remainder_args = raw_args

        if last_cmd_config.arg_type in [ArgType.KEYWORD, ArgType.MIXED]:
            # 如果是键值对类型，且没有位置参数配置，所有位置参数都是剩余参数
            if not last_cmd_config.positional_args:
                remainder_args = raw_args

        return " ".join(remainder_args)

    def _redistribute_args_for_global_remainder(
        self, raw_commands: OrderedDict
    ) -> Tuple[OrderedDict, str]:
        """
        为全局 collect_remainder 重新分配参数

        根据每个命令的配置限制其参数数量，收集多余的参数作为全局 remainder

        Args:
            raw_commands: 原始解析的命令

        Returns:
            Tuple[OrderedDict, str]: 调整后的命令字典和剩余参数文本
        """
        adjusted_commands = OrderedDict()
        all_remainder_args = []

        for cmd_name, cmd_info in raw_commands.items():
            raw_args = cmd_info["args"]
            raw_kwargs = cmd_info["kwargs"]
            cmd_config = self.config.get_command_config(cmd_name)

            if cmd_config:
                # 确定该命令应该接受的最大参数数量
                max_args = None

                if cmd_config.max_positional is not None:
                    # 明确设置了 max_positional
                    max_args = cmd_config.max_positional
                elif cmd_config.positional_args:
                    # 根据位置参数配置推断
                    max_args = len(cmd_config.positional_args)
                elif cmd_config.arg_type == ArgType.KEYWORD:
                    # 纯键值对命令，不接受位置参数
                    max_args = 0

                if max_args is not None and len(raw_args) > max_args:
                    # 保留前 max_args 个参数，其余的加入 remainder
                    kept_args = raw_args[:max_args]
                    remainder_args = raw_args[max_args:]
                    all_remainder_args.extend(remainder_args)

                    adjusted_commands[cmd_name] = {
                        "args": kept_args,
                        "kwargs": raw_kwargs,
                    }
                else:
                    # 参数数量在限制范围内，保持原样
                    adjusted_commands[cmd_name] = cmd_info
            else:
                # 没有配置，保持原样
                adjusted_commands[cmd_name] = cmd_info

        remainder_text = " ".join(all_remainder_args)
        return adjusted_commands, remainder_text

    def _extract_text_after_last_command(
        self, query: str, raw_commands: OrderedDict
    ) -> str:
        """
        从原始查询中提取最后一个命令之后的文本

        Args:
            query: 原始查询字符串
            raw_commands: 解析出的原始命令

        Returns:
            最后一个命令之后的剩余文本
        """
        if not raw_commands:
            return ""

        # 找到最后一个命令在查询字符串中的位置
        last_cmd_name = list(raw_commands.keys())[-1]
        last_cmd_pattern = rf"/{re.escape(last_cmd_name)}\b"

        # 找到最后一个命令的位置
        matches = list(re.finditer(last_cmd_pattern, query))
        if not matches:
            return ""

        last_match = matches[-1]
        cmd_end_pos = last_match.end()

        # 获取最后一个命令的参数
        last_cmd_info = raw_commands[last_cmd_name]
        remaining_text = query[cmd_end_pos:].strip()

        # 移除已经解析的参数
        for arg in last_cmd_info["args"]:
            # 简单的文本替换，可能需要更精确的处理
            arg_pattern = re.escape(arg)
            remaining_text = re.sub(
                rf"\b{arg_pattern}\b", "", remaining_text, 1
            ).strip()

        for key, value in last_cmd_info["kwargs"].items():
            kv_pattern = rf"\b{re.escape(key)}={re.escape(value)}\b"
            remaining_text = re.sub(kv_pattern, "", remaining_text).strip()

        return remaining_text.strip()

    def _convert_value(self, value: str, target_type: type) -> Any:
        """
        转换值的类型

        Args:
            value: 字符串值
            target_type: 目标类型

        Returns:
            转换后的值
        """
        if target_type == str:
            return value

        if target_type == bool:
            # 特殊处理布尔值
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            elif value.lower() in ("false", "0", "no", "off"):
                return False
            else:
                return bool(value)

        try:
            return target_type(value)
        except (ValueError, TypeError):
            # 转换失败，返回原值
            return value

    def parse_with_config(
        self, query: str, config: ParserConfig
    ) -> OrderedDict[str, ParsedCommand]:
        """
        使用指定配置解析命令

        Args:
            query: 命令行格式的查询字符串
            config: 解析器配置

        Returns:
            OrderedDict[str, ParsedCommand]: 解析后的命令字典
        """
        old_config = self.config
        self.config = config
        try:
            return self.parse_typed(query)
        finally:
            self.config = old_config


class CommandWrapper:
    """
    命令包装器，提供对命令参数的便捷访问
    """

    def __init__(
        self, parsed_cmd: ParsedCommand, config: Optional[ParserConfig] = None
    ):
        self._parsed_cmd = parsed_cmd
        self._config = config

    def __getattr__(self, name: str) -> Any:
        """通过属性访问命令参数"""
        if name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        # 查找位置参数配置
        cmd_config = None
        if self._config:
            cmd_config = self._config.get_command_config(self._parsed_cmd.name)

        if cmd_config:
            # 如果有剩余参数且参数名匹配命令配置的 remainder_name
            if self._parsed_cmd.remainder and name == cmd_config.remainder_name:
                return self._parsed_cmd.remainder

            # 查找位置参数
            for i, arg_config in enumerate(cmd_config.positional_args):
                if arg_config.name == name and i < len(self._parsed_cmd.args):
                    return self._parsed_cmd.args[i]

            # 查找键值对参数
            if name in self._parsed_cmd.kwargs:
                return self._parsed_cmd.kwargs[name]

            # 如果键值对参数在配置中但不在 kwargs 中（用户没有提供），检查默认值
            if name in cmd_config.keyword_args:
                arg_config = cmd_config.keyword_args[name]
                # 如果有默认值，返回默认值；否则返回 None（因为它是可选的）
                return arg_config.default if arg_config.default is not None else None

        # 如果没有配置，尝试通过索引访问
        if name == "remainder" and self._parsed_cmd.remainder:
            return self._parsed_cmd.remainder

        # 回退到原始行为（用于没有配置的命令）
        if self._parsed_cmd.kwargs and name in self._parsed_cmd.kwargs:
            return self._parsed_cmd.kwargs[name]

        # 只有在没有任何配置的情况下，才使用单参数回退
        # 如果有配置但没有匹配到，应该抛出 AttributeError
        if not cmd_config:
            # 如果是简单的单参数情况，直接返回第一个参数
            if len(self._parsed_cmd.args) == 1 and not self._parsed_cmd.kwargs:
                return self._parsed_cmd.args[0]

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __repr__(self) -> str:
        return f"CommandWrapper({self._parsed_cmd.name})"


@dataclass
class TypedQueryCommand:
    """
    类型化的查询命令结果，提供便捷的属性访问

    与 QueryCommand 类似，但支持类型转换和验证
    """

    _commands: OrderedDict[str, ParsedCommand] = field(default_factory=OrderedDict)
    _config: Optional[ParserConfig] = None
    _query: str = ""

    def __getattr__(self, name: str) -> Any:
        """通过属性访问命令参数"""
        if name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        # 特殊处理 query 属性 - 优先从配置的 remainder_name 获取
        if name == "query":
            if self._config and self._config.collect_remainder:
                remainder_name = self._config.remainder_name
                if remainder_name in self._commands:
                    remainder_cmd = self._commands[remainder_name]
                    return remainder_cmd.remainder or ""
            return self._query

        # 查找命令
        parsed_cmd = self._get_command(name)
        if parsed_cmd:
            # 获取命令配置
            cmd_config = None
            if self._config:
                cmd_config = self._config.get_command_config(parsed_cmd.name)

            # 如果有配置（位置参数或键值对参数），检查是否需要 CommandWrapper
            if cmd_config and (cmd_config.positional_args or cmd_config.keyword_args):
                # 特殊处理：如果只有一个位置参数且参数名为 "value"，且没有剩余参数和键值对参数，直接返回值
                if (
                    len(cmd_config.positional_args) == 1
                    and cmd_config.positional_args[0].name == "value"
                    and len(parsed_cmd.args) == 1
                    and not parsed_cmd.remainder
                    and not parsed_cmd.kwargs
                ):
                    return parsed_cmd.args[0]
                # 其他情况返回 CommandWrapper 以支持嵌套访问
                return CommandWrapper(parsed_cmd, self._config)

            # 如果有剩余参数但没有位置参数配置，直接返回剩余参数
            if parsed_cmd.remainder:
                return parsed_cmd.remainder

            # 如果有键值对参数但没有配置，返回字典
            if parsed_cmd.kwargs:
                return parsed_cmd.kwargs

            # 如果有位置参数
            if parsed_cmd.args:
                return (
                    parsed_cmd.args[0] if len(parsed_cmd.args) == 1 else parsed_cmd.args
                )

            # 命令存在但没有参数
            return ""

        return None

    def _get_command(self, name: str) -> Optional[ParsedCommand]:
        """获取命令（支持连字符转换）"""
        # 直接查找
        if name in self._commands:
            return self._commands[name]

        # 尝试连字符转换
        hyphen_name = name.replace("_", "-")
        if hyphen_name in self._commands:
            return self._commands[hyphen_name]

        return None

    def has_command(self, command: str) -> bool:
        """检查是否包含指定命令"""
        return self._get_command(command) is not None

    def get_command(self, command: str) -> Optional[ParsedCommand]:
        """获取解析后的命令对象"""
        return self._get_command(command)

    def get_errors(self) -> Dict[str, List[str]]:
        """获取所有命令的错误"""
        errors = {}
        for cmd_name, parsed_cmd in self._commands.items():
            if parsed_cmd.errors:
                errors[cmd_name] = parsed_cmd.errors
        return errors

    def is_valid(self) -> bool:
        """检查是否所有命令都有效"""
        return all(cmd.is_valid for cmd in self._commands.values())

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        commands_str = ", ".join(self._commands.keys())
        valid_str = "valid" if self.is_valid() else "has errors"
        return f"TypedQueryCommand(commands=[{commands_str}], {valid_str})"


def parse_typed_query(
    query: str, config: Optional[ParserConfig] = None
) -> TypedQueryCommand:
    """
    解析类型化的查询命令

    Args:
        query: 命令行格式的查询字符串
        config: 解析器配置

    Returns:
        TypedQueryCommand: 类型化的查询命令对象

    Example:
        >>> from autocoder.common.ac_style_command_parser import create_config
        >>>
        >>> config = (create_config()
        ...     .command("model")
        ...         .positional("name", required=True)
        ...     .command("temperature")
        ...         .positional("value", type=float)
        ...     .build()
        ... )
        >>>
        >>> result = parse_typed_query("/model gpt-4 /temperature 0.8", config)
        >>> print(result.model)  # "gpt-4"
        >>> print(result.temperature)  # 0.8 (float类型)
        >>> print(result.is_valid())  # True
    """
    parser = TypedCommandParser(config)
    parsed_commands = parser.parse_typed(query)

    result = TypedQueryCommand()
    result._commands = parsed_commands
    result._config = config

    # 如果配置了全局 collect_remainder，query 会从特殊的 remainder 命令中获取
    # 否则，从第一个有剩余参数的命令中获取
    if config and config.collect_remainder:
        # query 会通过 __getattr__ 自动从 remainder_name 命令中获取
        pass
    else:
        # 兼容旧的行为：从第一个有剩余参数的命令中获取
        for cmd_name, parsed_cmd in parsed_commands.items():
            if parsed_cmd.remainder:
                result._query = parsed_cmd.remainder
                break

    return result
