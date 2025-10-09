import re
from collections import OrderedDict
from typing import Dict, List, Tuple, Any, Optional


class CommandParser:
    """
    命令解析器，用于解析命令行格式的查询字符串。
    支持以下格式：
    1. /command arg1 arg2
    2. /command key1=value1 key2=value2
    3. /command arg1 key1=value1
    4. /command1 arg1 /command2 arg2
    5. /command1 /command2 arg2
    6. /command1 /command2 key=value
    7. /command key="value with spaces"
    8. /command key='value with spaces'
    
    注意：路径参数（如/path/to/file）不会被识别为命令。
    """

    def __init__(self):
        # 匹配命令的正则表达式 - 必须是以/开头，后跟单词字符或连字符，且后面必须是空白字符或字符串结尾
        # (?<!\S) 确保命令前是字符串开头或空白字符
        self.command_pattern = r'(?<!\S)/([\w-]+)(?=\s|$)'
        # 匹配键值对参数的正则表达式，支持带引号的值（包括三重引号）
        self.key_value_pattern = r'(\w+)=(?:\'\'\'([^\']*?)\'\'\'|"""([^"]*?)"""|"([^"]*?)"|\'([^\']*?)\'|([^\s"\']*))(?:\s|$)'
        # 匹配路径模式的正则表达式
        self.path_pattern = r'/\w+(?:/[^/\s]+)+'

    def parse(self, query: str) -> OrderedDict[str, Any]:
        """
        解析命令行格式的查询字符串，返回命令和参数的字典。
        
        参数:
            query: 命令行格式的查询字符串
            
        返回:
            OrderedDict[str, Any]: 命令和参数的有序字典，格式为：
                {
                    'command1': {
                        'args': ['arg1', 'arg2'],
                        'kwargs': {'key1': 'value1', 'key2': 'value with spaces'}
                    },
                    'command2': {
                        'args': [],
                        'kwargs': {'key': 'value'}
                    }
                }
        """
        if not query or not query.strip():
            return OrderedDict()

        processed_query = query
        placeholders = {}
        placeholder_counter = 0
        
        # 预处理1：标记引号内容，避免引号内的命令被识别
        quote_patterns = [
            r'\'\'\'([^\']*?)\'\'\'',  # 三重单引号
            r'"""([^"]*?)"""',        # 三重双引号  
            r'"([^"]*?)"',            # 双引号
            r'\'([^\']*?)\''          # 单引号
        ]
        
        for pattern in quote_patterns:
            for match in re.finditer(pattern, processed_query):
                quoted_content = match.group(0)
                placeholder = f"__QUOTE_PLACEHOLDER_{placeholder_counter}__"
                placeholders[placeholder] = quoted_content
                processed_query = processed_query.replace(quoted_content, placeholder, 1)
                placeholder_counter += 1

        # 预处理2：标记路径参数，避免被识别为命令
        path_matches = re.finditer(self.path_pattern, processed_query)
        
        for match in path_matches:
            path = match.group(0)
            placeholder = f"__PATH_PLACEHOLDER_{placeholder_counter}__"
            placeholders[placeholder] = path
            processed_query = processed_query.replace(path, placeholder, 1)
            placeholder_counter += 1

        # 找出所有命令
        commands = re.findall(self.command_pattern, processed_query)
        if not commands:
            return OrderedDict()

        # 将查询字符串按命令分割
        parts = re.split(self.command_pattern, processed_query)
        # 第一个元素是空字符串或之前的非命令内容，保留它
        first_part = parts[0]
        parts = parts[1:]

        result = OrderedDict()
        
        # 处理每个命令和它的参数
        for i in range(0, len(parts), 2):
            command = parts[i]
            
            # 获取此命令的参数部分
            params_str = parts[i+1].strip() if i+1 < len(parts) else ""
            
            # 恢复所有占位符的原始值
            for placeholder, original_value in placeholders.items():
                params_str = params_str.replace(placeholder, original_value)
            
            # 解析参数
            args, kwargs = self._parse_params(params_str)
            
            result[command] = {
                'args': args,
                'kwargs': kwargs
            }
            
        return result

    def _parse_params(self, params_str: str) -> Tuple[List[str], Dict[str, str]]:
        """
        解析参数字符串，区分位置参数和键值对参数。
        支持带引号(双引号或单引号)的值，引号内可以包含空格。
        保持参数的原始顺序。
        
        参数:
            params_str: 参数字符串
            
        返回:
            Tuple[List[str], Dict[str, str]]: 位置参数列表和键值对参数字典
        """
        args = []
        kwargs = {}
        
        if not params_str:
            return args, kwargs
        
        # 使用正则表达式按顺序找出所有参数（包括引号参数和键值对）
        # 这个模式会匹配：
        # 1. 键值对参数（key=value格式）
        # 2. 带引号的参数
        # 3. 普通参数
        param_pattern = r'''
            (?:
                # 键值对参数：key=value
                (\w+)=(?:\'\'\'([^\']*?)\'\'\'|"""([^"]*?)"""|"([^"]*?)"|\'([^\']*?)\'|([^\s"\']*))
                |
                # 带引号的参数
                (?:\'\'\'([^\']*?)\'\'\'|"""([^"]*?)"""|"([^"]*?)"|\'([^\']*?)\')
                |
                # 普通参数（不包含空格的）
                ([^\s"\'=]+)
            )
        '''
        
        matches = re.findall(param_pattern, params_str, re.VERBOSE)
        
        for match in matches:
            # match有11个捕获组：
            # 0: 键值对的key
            # 1-5: 键值对的value（三重单引号、三重双引号、双引号、单引号、无引号）
            # 6-9: 带引号的位置参数值（三重单引号、三重双引号、双引号、单引号）
            # 10: 普通位置参数
            
            if match[0]:  # 这是键值对参数
                key = match[0]
                value = match[1] or match[2] or match[3] or match[4] or match[5]
                kwargs[key] = value.strip()
            else:  # 这是位置参数
                # 检查是带引号的参数还是普通参数
                quoted_value = match[6] or match[7] or match[8] or match[9]
                plain_value = match[10]
                
                if quoted_value:
                    args.append(quoted_value)
                elif plain_value:
                    args.append(plain_value)
        
        return args, kwargs
    
    def parse_command(self, query: str, command: str) -> Optional[Dict[str, Any]]:
        """
        解析特定命令的参数。
        
        参数:
            query: 命令行格式的查询字符串
            command: 要解析的命令名
            
        返回:
            Optional[Dict[str, Any]]: 如果找到命令，返回其参数；否则返回None
        """
        commands = self.parse(query)
        return commands.get(command)


def parse_query(query: str) -> OrderedDict[str, Any]:
    """
    解析命令行格式的查询字符串的便捷函数。
    
    参数:
        query: 命令行格式的查询字符串
        
    返回:
        OrderedDict[str, Any]: 命令和参数的有序字典
    """
    parser = CommandParser()
    return parser.parse(query)


def has_command(query: str, command: str) -> bool:
    """
    检查查询字符串中是否包含特定命令。
    
    参数:
        query: 命令行格式的查询字符串
        command: 要检查的命令名
        
    返回:
        bool: 如果包含命令返回True，否则返回False
    """
    parser = CommandParser()
    commands = parser.parse(query)
    return command in commands


def get_command_args(query: str, command: str) -> List[str]:
    """
    获取特定命令的位置参数。
    
    参数:
        query: 命令行格式的查询字符串
        command: 要获取参数的命令名
        
    返回:
        List[str]: 命令的位置参数列表，如果命令不存在返回空列表
    """
    parser = CommandParser()
    command_info = parser.parse_command(query, command)
    if command_info:
        return command_info['args']
    return []


def get_command_kwargs(query: str, command: str) -> Dict[str, str]:
    """
    获取特定命令的键值对参数。
    
    参数:
        query: 命令行格式的查询字符串
        command: 要获取参数的命令名
        
    返回:
        Dict[str, str]: 命令的键值对参数字典，如果命令不存在返回空字典
    """
    parser = CommandParser()
    command_info = parser.parse_command(query, command)
    if command_info:
        return command_info['kwargs']
    return {}


class QueryCommand:
    """
    封装解析后的命令查询结果，提供便捷的属性访问方式。
    
    支持通过属性访问子命令的参数，命令名中的连字符会自动转换为下划线。
    例如：/task-prefix 可以通过 obj.task_prefix 访问
    """
    
    def __init__(self, parsed_commands: OrderedDict[str, Any], 
                 sub_commands: Optional[List[str]] = None,
                 last_command_takes_rest: bool = True):
        """
        初始化 QueryCommand 对象。
        
        参数:
            parsed_commands: 解析后的命令字典
            sub_commands: 需要特殊处理的子命令列表
            last_command_takes_rest: 如果为True，最后一个子命令只取第一个参数，
                                    剩余参数作为整体query
        """
        self._commands = parsed_commands
        self._sub_commands = sub_commands or []
        self._last_command_takes_rest = last_command_takes_rest
        self._query = ""
        
        # 处理子命令和剩余参数
        self._process_commands()
    
    def _process_commands(self):
        """处理命令，提取子命令参数和剩余的query"""
        if not self._sub_commands or not self._last_command_takes_rest:
            # 如果没有指定子命令或不需要特殊处理，直接返回
            return
        
        # 找到最后一个指定的子命令在命令列表中的位置
        last_sub_command_key = None
        last_sub_command_position = -1
        
        # 遍历所有解析出的命令，按顺序查找
        for i, (cmd_key, cmd_info) in enumerate(self._commands.items()):
            # 检查这个命令是否在子命令列表中
            if cmd_key in self._sub_commands:
                last_sub_command_key = cmd_key
                last_sub_command_position = i
            # 也检查连字符转下划线的版本
            elif cmd_key.replace('-', '_') in self._sub_commands:
                last_sub_command_key = cmd_key
                last_sub_command_position = i
            elif cmd_key.replace('_', '-') in self._sub_commands:
                last_sub_command_key = cmd_key
                last_sub_command_position = i
        
        if last_sub_command_key is None:
            return
        
        # 获取最后一个子命令的信息
        command_info = self._commands[last_sub_command_key]
        args = command_info.get('args', [])
        
        if len(args) > 1:
            # 只保留第一个参数给命令，剩余的作为query
            first_arg = args[0]
            rest_args = args[1:]
            
            # 更新命令的参数
            self._commands[last_sub_command_key]['args'] = [first_arg]
            
            # 设置query为剩余参数
            self._query = " ".join(rest_args)
        
        # 处理其他子命令，确保每个子命令只保留第一个参数
        for cmd_key in list(self._commands.keys()):
            if cmd_key != last_sub_command_key and (
                cmd_key in self._sub_commands or 
                cmd_key.replace('-', '_') in self._sub_commands or
                cmd_key.replace('_', '-') in self._sub_commands
            ):
                cmd_args = self._commands[cmd_key].get('args', [])
                if len(cmd_args) > 1:
                    # 只保留第一个参数
                    self._commands[cmd_key]['args'] = [cmd_args[0]]
    
    def __getattr__(self, name: str) -> Any:
        """
        通过属性访问命令参数。
        
        参数:
            name: 属性名（命令名，连字符会被转换为下划线）
            
        返回:
            如果命令存在且有参数，返回第一个参数；
            如果命令存在但没有参数，返回空字符串；
            如果命令不存在，返回None
        """
        if name.startswith('_'):
            # 访问私有属性
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        # 特殊处理 query 属性
        if name == 'query':
            return self._query
        
        # 尝试直接查找命令
        if name in self._commands:
            command_info = self._commands[name]
            args = command_info.get('args', [])
            kwargs = command_info.get('kwargs', {})
            
            # 如果有键值对参数，返回键值对字典
            if kwargs:
                return kwargs
            # 如果有位置参数，返回第一个参数
            if args:
                return args[0] if len(args) == 1 else args
            # 命令存在但没有参数
            return ""
        
        # 尝试将下划线转换为连字符查找
        hyphen_name = name.replace('_', '-')
        if hyphen_name in self._commands:
            command_info = self._commands[hyphen_name]
            args = command_info.get('args', [])
            kwargs = command_info.get('kwargs', {})
            
            # 如果有键值对参数，返回键值对字典
            if kwargs:
                return kwargs
            # 如果有位置参数，返回第一个参数
            if args:
                return args[0] if len(args) == 1 else args
            # 命令存在但没有参数
            return ""
        
        # 命令不存在
        return None
    
    def has_command(self, command: str) -> bool:
        """
        检查是否包含指定命令。
        
        参数:
            command: 命令名
            
        返回:
            bool: 如果包含命令返回True，否则返回False
        """
        # 检查原始命令名和转换后的命令名（双向转换）
        return (command in self._commands or 
                command.replace('-', '_') in self._commands or
                command.replace('_', '-') in self._commands)
    
    def get_command_info(self, command: str) -> Optional[Dict[str, Any]]:
        """
        获取指定命令的完整信息。
        
        参数:
            command: 命令名
            
        返回:
            Optional[Dict[str, Any]]: 命令信息字典，包含args和kwargs
        """
        if command in self._commands:
            return self._commands[command]
        
        # 尝试转换命令名
        normalized_cmd = command.replace('-', '_')
        if normalized_cmd in self._commands:
            return self._commands[normalized_cmd]
        
        return None
    
    def get_all_commands(self) -> List[str]:
        """
        获取所有命令名列表。
        
        返回:
            List[str]: 命令名列表
        """
        return list(self._commands.keys())
    
    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        commands_str = ", ".join(self._commands.keys())
        return f"QueryCommand(commands=[{commands_str}], query='{self._query}')"


def get_query_command(query: str, 
                     sub_commands: Optional[List[str]] = None,
                     last_command_takes_rest: bool = True) -> QueryCommand:
    """
    解析命令查询并返回QueryCommand对象，提供便捷的属性访问。
    
    这个函数特别适合处理如下场景：
    /async /model gpt-4 /task-prefix mytask this is the actual query
    
    其中 /model 和 /task-prefix 是子命令，每个只取第一个参数，
    剩余的 "this is the actual query" 作为整体的查询内容。
    
    参数:
        query: 命令行格式的查询字符串
        sub_commands: 需要特殊处理的子命令列表，如 ["model", "task-prefix"]
        last_command_takes_rest: 如果为True，最后一个子命令只取第一个参数，
                                剩余参数作为整体query
        
    返回:
        QueryCommand: 封装了解析结果的对象，支持属性访问
        
    使用示例:
        >>> v = get_query_command("/async /model gpt-4 /task-prefix mytask hello world", 
        ...                      sub_commands=["model", "task-prefix"])
        >>> v.model  # 返回 "gpt-4"
        >>> v.task_prefix  # 返回 "mytask"
        >>> v.query  # 返回 "hello world"
    """
    parser = CommandParser()
    parsed_commands = parser.parse(query)
    
    return QueryCommand(parsed_commands, sub_commands, last_command_takes_rest)
