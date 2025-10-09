
import pytest
from collections import OrderedDict
from typing import Dict, List, Any

# 导入被测模块
from .parser import (
    CommandParser,
    parse_query,
    has_command,
    get_command_args,
    get_command_kwargs,
    get_query_command
)


class TestCommandParser:
    """CommandParser类的单元测试"""
    
    @pytest.fixture
    def parser(self):
        """提供CommandParser实例"""
        return CommandParser()
    
    def test_init(self, parser):
        """测试CommandParser初始化"""
        assert parser is not None
        assert hasattr(parser, 'command_pattern')
        assert hasattr(parser, 'key_value_pattern') 
        assert hasattr(parser, 'path_pattern')
    
    def test_empty_query(self, parser):
        """测试空查询字符串"""
        assert parser.parse("") == {}
        assert parser.parse("   ") == {}
        assert parser.parse(None) == {}
    
    def test_single_command_no_args(self, parser):
        """测试单个命令无参数"""
        result = parser.parse("/help")
        expected = {
            "help": {
                "args": [],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_single_command_with_args(self, parser):
        """测试单个命令带位置参数"""
        result = parser.parse("/add file1.txt file2.py")
        expected = {
            "add": {
                "args": ["file1.txt", "file2.py"],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_single_command_with_kwargs(self, parser):
        """测试单个命令带键值对参数"""
        result = parser.parse("/config model=gpt-4 temperature=0.7")
        expected = {
            "config": {
                "args": [],
                "kwargs": {
                    "model": "gpt-4",
                    "temperature": "0.7"
                }
            }
        }
        assert result == expected
    
    def test_single_command_mixed_params(self, parser):
        """测试单个命令混合参数"""
        result = parser.parse("/deploy myapp env=prod version=1.0")
        expected = {
            "deploy": {
                "args": ["myapp"],
                "kwargs": {
                    "env": "prod",
                    "version": "1.0"
                }
            }
        }
        assert result == expected

    def test_single_command_new_params(self, parser):
        """测试单个命令混合参数"""
        result = parser.parse('/new "把 /Users/williamzhu/.auto-coder/async_agent/tasks/stdin_20250815101939_e9042b6c 中未commit变更合并回来"')
        expected = {
            "new": {
                "args": ['把 /Users/williamzhu/.auto-coder/async_agent/tasks/stdin_20250815101939_e9042b6c 中未commit变更合并回来'],
                "kwargs": {}
            }
        }
        assert result == expected   

    def test_single_command_async_params(self, parser):
        """测试单个命令混合参数"""
        result = parser.parse("/async \"/list @./src/agent.ts 中,while 循环里有loop call limit 限制,当前会发出一个 emitEvent 事件,同时也需要发出一个渲染事件(opts.render方法)\"")
        expected = {
            "async": {
                "args": ['/list @./src/agent.ts 中,while 循环里有loop call limit 限制,当前会发出一个 emitEvent 事件,同时也需要发出一个渲染事件(opts.render方法)'],
                "kwargs": {}
            }
        }
        assert result == expected      
    
    def test_quoted_args_double_quotes(self, parser):
        """测试双引号参数"""
        result = parser.parse('/say "hello world" "this is a test"')
        expected = {
            "say": {
                "args": ["hello world", "this is a test"],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_quoted_args_single_quotes(self, parser):
        """测试单引号参数"""
        result = parser.parse("/say 'hello world' 'this is a test'")
        expected = {
            "say": {
                "args": ["hello world", "this is a test"],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_quoted_kwargs(self, parser):
        """测试带引号的键值对参数"""
        result = parser.parse('/config message="hello world" path=\'/tmp/test dir\'')
        expected = {
            "config": {
                "args": [],
                "kwargs": {
                    "message": "hello world",
                    "path": "/tmp/test dir"
                }
            }
        }
        assert result == expected
    
    def test_multiple_commands(self, parser):
        """测试多个命令"""
        result = parser.parse("/add file1.txt /remove file2.txt")
        expected = {
            "add": {
                "args": ["file1.txt"],
                "kwargs": {}
            },
            "remove": {
                "args": ["file2.txt"],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_multiple_commands_with_mixed_params(self, parser):
        """测试多个命令带混合参数"""
        result = parser.parse("/deploy app1 env=prod /config model=gpt-4 /status")
        expected = {
            "deploy": {
                "args": ["app1"],
                "kwargs": {"env": "prod"}
            },
            "config": {
                "args": [],
                "kwargs": {"model": "gpt-4"}
            },
            "status": {
                "args": [],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_command_order_preservation(self, parser):
        """测试命令顺序保持"""
        result = parser.parse("/third /first /second arg1 /fourth key=value")
        
        # 验证返回的是OrderedDict
        assert isinstance(result, OrderedDict)
        
        # 验证命令顺序
        command_order = list(result.keys())
        expected_order = ["third", "first", "second", "fourth"]
        assert command_order == expected_order
        
        # 验证内容正确性
        assert result["third"]["args"] == []
        assert result["first"]["args"] == []
        assert result["second"]["args"] == ["arg1"]
        assert result["fourth"]["kwargs"] == {"key": "value"}
    
    def test_path_not_recognized_as_command(self, parser):
        """测试路径不被识别为命令"""
        result = parser.parse("/add /path/to/file.txt /config model=gpt-4")
        expected = {
            "add": {
                "args": ["/path/to/file.txt"],
                "kwargs": {}
            },
            "config": {
                "args": [],
                "kwargs": {"model": "gpt-4"}
            }
        }
        assert result == expected
    
    def test_complex_path_handling(self, parser):
        """测试复杂路径处理"""
        result = parser.parse("/analyze /home/user/project/src/main.py /output /tmp/results")
        expected = {
            "analyze": {
                "args": ["/home/user/project/src/main.py"],
                "kwargs": {}
            },
            "output": {
                "args": ["/tmp/results"],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_command_with_dots_not_recognized(self, parser):
        """测试带点的字符串不被识别为命令"""
        result = parser.parse("check /config.json /setup.py")
        # 不以/开头，所以没有命令被识别
        assert result == {}
    
    def test_parse_command_existing(self, parser):
        """测试解析特定存在的命令"""
        query = "/add file1.txt /remove file2.txt mode=force"
        result = parser.parse_command(query, "remove")
        expected = {
            "args": ["file2.txt"],
            "kwargs": {"mode": "force"}
        }
        assert result == expected
    
    def test_parse_command_nonexistent(self, parser):
        """测试解析不存在的命令"""
        query = "/add file1.txt /remove file2.txt"
        result = parser.parse_command(query, "deploy")
        assert result is None
    
    def test_edge_case_empty_kwargs_value(self, parser):
        """测试空的键值对值"""
        result = parser.parse("/config key1= key2=value")
        expected = {
            "config": {
                "args": [],
                "kwargs": {
                    "key1": "",
                    "key2": "value"
                }
            }
        }
        assert result == expected
    
    def test_edge_case_special_characters_in_values(self, parser):
        """测试值中包含特殊字符"""
        result = parser.parse("/config url=https://api.example.com/v1 pattern='*.py'")
        expected = {
            "config": {
                "args": [],
                "kwargs": {
                    "url": "https://api.example.com/v1",
                    "pattern": "*.py"
                }
            }
        }
        assert result == expected
    
    def test_command_at_end_of_string(self, parser):
        """测试字符串末尾的命令"""
        result = parser.parse("some text /help")
        expected = {
            "help": {
                "args": [],
                "kwargs": {}
            }
        }
        assert result == expected
    
    def test_auto_new_complex_scenario(self, parser):
        """测试复杂的自动化场景：/auto /new 运行使用交互式方式运行 auto-coder.chat 然后在里面运行 /rules /list"""
        query = "/auto /new 运行使用交互式方式运行 auto-coder.chat 然后在里面运行 /rules /list"
        result = parser.parse(query)
        expected = {
            "auto": {
                "args": [],
                "kwargs": {}
            },
            "new": {
                "args": ["运行使用交互式方式运行", "auto-coder.chat", "然后在里面运行"],
                "kwargs": {}
            },
            "rules": {
                "args": [],
                "kwargs": {}
            },
            "list": {
                "args": [],
                "kwargs": {}
            }
        }
        assert result == expected

    def test_auto_new_complex_scenario2(self, parser):
        """测试复杂的自动化场景：/auto /new 运行使用交互式方式运行 auto-coder.chat 然后在里面运行 /rules /list"""
        query = '/auto /new "运行使用交互式方式运行 auto-coder.chat 然后在里面运行 /rules /list"'
        result = parser.parse(query)
        expected = {
            "auto": {
                "args": [],
                "kwargs": {}
            },
            "new": {
                "args": ["运行使用交互式方式运行 auto-coder.chat 然后在里面运行 /rules /list"],
                "kwargs": {}
            }            
        }
        assert result == expected    


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_parse_query_function(self):
        """测试parse_query函数"""
        result = parse_query("/add file1.txt mode=fast")
        
        # 验证返回的是OrderedDict
        assert isinstance(result, OrderedDict)
        
        expected = {
            "add": {
                "args": ["file1.txt"],
                "kwargs": {"mode": "fast"}
            }
        }
        assert result == expected
    
    def test_has_command_true(self):
        """测试has_command函数 - 命令存在"""
        assert has_command("/add file1.txt /remove file2.txt", "add") == True
        assert has_command("/add file1.txt /remove file2.txt", "remove") == True
    
    def test_has_command_false(self):
        """测试has_command函数 - 命令不存在"""
        assert has_command("/add file1.txt /remove file2.txt", "deploy") == False
        assert has_command("no commands here", "add") == False
        assert has_command("", "add") == False
    
    def test_get_command_args_existing(self):
        """测试get_command_args函数 - 命令存在"""
        query = "/add file1.txt file2.py /remove file3.txt"
        assert get_command_args(query, "add") == ["file1.txt", "file2.py"]
        assert get_command_args(query, "remove") == ["file3.txt"]
    
    def test_get_command_args_nonexistent(self):
        """测试get_command_args函数 - 命令不存在"""
        query = "/add file1.txt file2.py"
        assert get_command_args(query, "remove") == []
        assert get_command_args("", "add") == []
    
    def test_get_command_kwargs_existing(self):
        """测试get_command_kwargs函数 - 命令存在"""
        query = "/config model=gpt-4 temp=0.7 /deploy env=prod"
        assert get_command_kwargs(query, "config") == {"model": "gpt-4", "temp": "0.7"}
        assert get_command_kwargs(query, "deploy") == {"env": "prod"}
    
    def test_get_command_kwargs_nonexistent(self):
        """测试get_command_kwargs函数 - 命令不存在"""
        query = "/config model=gpt-4"
        assert get_command_kwargs(query, "deploy") == {}
        assert get_command_kwargs("", "config") == {}


class TestComplexScenarios:
    """测试复杂场景"""
    
    def test_real_world_scenario_1(self):
        """测试真实场景1：文件操作命令"""
        query = '/add "src/main.py" "tests/test_main.py" /config model="gpt-4" temperature=0.7 /deploy env=production version="1.2.3"'
        result = parse_query(query)
        
        expected = {
            "add": {
                "args": ["src/main.py", "tests/test_main.py"],
                "kwargs": {}
            },
            "config": {
                "args": [],
                "kwargs": {
                    "model": "gpt-4",
                    "temperature": "0.7"
                }
            },
            "deploy": {
                "args": [],
                "kwargs": {
                    "env": "production",
                    "version": "1.2.3"
                }
            }
        }
        assert result == expected
    
    def test_real_world_scenario_2(self):
        """测试真实场景2：包含路径的复杂命令"""
        query = "/analyze /home/user/project/src /output /tmp/analysis.json format=json verbose=true"
        result = parse_query(query)
        
        expected = {
            "analyze": {
                "args": ["/home/user/project/src"],
                "kwargs": {}
            },
            "output": {
                "args": ["/tmp/analysis.json"],
                "kwargs": {
                    "format": "json",
                    "verbose": "true"
                }
            }
        }
        assert result == expected
    
    def test_real_world_scenario_3(self):
        """测试真实场景3：混合引号和特殊字符"""
        query = """/search pattern="*.py" path='/home/user/My Documents/project' /filter exclude="__pycache__" """
        result = parse_query(query)
        
        expected = {
            "search": {
                "args": [],
                "kwargs": {
                    "pattern": "*.py",
                    "path": "/home/user/My Documents/project"
                }
            },
            "filter": {
                "args": [],
                "kwargs": {
                    "exclude": "__pycache__"
                }
            }
        }
        assert result == expected
    
    def test_edge_case_consecutive_commands(self):
        """测试连续命令"""
        query = "/start /stop /restart mode=fast"
        result = parse_query(query)
        
        expected = {
            "start": {
                "args": [],
                "kwargs": {}
            },
            "stop": {
                "args": [],
                "kwargs": {}
            },
            "restart": {
                "args": [],
                "kwargs": {"mode": "fast"}
            }
        }
        assert result == expected
    
    def test_edge_case_command_with_numbers_and_underscores(self):
        """测试包含数字和下划线的命令"""
        query = "/test_case_1 /deploy_v2 app_name=test123"
        result = parse_query(query)
        
        expected = {
            "test_case_1": {
                "args": [],
                "kwargs": {}
            },
            "deploy_v2": {
                "args": [],
                "kwargs": {"app_name": "test123"}
            }
        }
        assert result == expected


class TestErrorHandling:
    """测试错误处理和边界情况"""
    
    def test_malformed_quotes(self):
        """测试格式错误的引号"""
        # 这些应该仍能部分解析，不会抛出异常
        parser = CommandParser()
        
        # 未闭合的引号 - 应该被当作普通参数处理
        result = parser.parse('/test "unclosed quote arg')
        assert "test" in result
        
        # 混合引号
        result = parser.parse('/test "mixed\' quotes"')
        assert "test" in result
    
    def test_special_characters_in_commands(self):
        """测试命令中的特殊字符"""
        parser = CommandParser()
        
        # 命令名可以包含单词字符和连字符，但不能包含点号
        result = parser.parse("/test-command /test.command")
        expected = OrderedDict({
            'test-command': {'args': ['/test.command'], 'kwargs': {}}
        })
        assert result == expected
    
    def test_whitespace_handling(self):
        """测试空白字符处理"""
        parser = CommandParser()
        
        query = "  /add    file1.txt    file2.py   key=value   "
        result = parser.parse(query)
        
        expected = {
            "add": {
                "args": ["file1.txt", "file2.py"],
                "kwargs": {"key": "value"}
            }
        }
        assert result == expected
    
    def test_unicode_characters(self):
        """测试Unicode字符"""
        parser = CommandParser()
        
        query = '/test "中文参数" key="中文值"'
        result = parser.parse(query)
        
        expected = {
            "test": {
                "args": ["中文参数"],
                "kwargs": {"key": "中文值"}
            }
        }
        assert result == expected


# 参数化测试用例
@pytest.mark.parametrize("query,expected_commands", [
    ("/help", ["help"]),
    ("/add /remove", ["add", "remove"]),
    ("/config model=gpt-4", ["config"]),
    ("no commands", []),
    ("/start /stop /restart", ["start", "stop", "restart"]),
])
def test_command_detection_parametrized(query, expected_commands):
    """参数化测试命令检测"""
    result = parse_query(query)
    actual_commands = list(result.keys())
    assert actual_commands == expected_commands


@pytest.mark.parametrize("query,command,expected_args", [
    ("/add file1 file2", "add", ["file1", "file2"]),
    ("/remove", "remove", []),
    ("/test arg1 'arg with spaces'", "test", ["arg1", "arg with spaces"]),
    ("", "any", []),
])
def test_get_args_parametrized(query, command, expected_args):
    """参数化测试获取参数"""
    assert get_command_args(query, command) == expected_args


@pytest.mark.parametrize("query,command,expected_kwargs", [
    ("/config model=gpt-4 temp=0.7", "config", {"model": "gpt-4", "temp": "0.7"}),
    ("/deploy", "deploy", {}),
    ("/test key='value with spaces'", "test", {"key": "value with spaces"}),
    ("", "any", {}),
])
def test_get_kwargs_parametrized(query, command, expected_kwargs):
    """参数化测试获取键值对参数"""
    assert get_command_kwargs(query, command) == expected_kwargs


class TestQueryCommand:
    """测试 QueryCommand 类和 get_query_command 函数"""
    
    def test_basic_query_command(self):
        """测试基本的 QueryCommand 功能"""
        query = "/model gpt-4 /temperature 0.7"
        v = get_query_command(query)
        
        assert v.model == "gpt-4"
        assert v.temperature == "0.7"
        assert v.query == ""
    
    def test_query_command_with_sub_commands(self):
        """测试带子命令的 QueryCommand"""
        query = "/async /model gpt-4 /task-prefix mytask hello world"
        v = get_query_command(query, sub_commands=["model", "task-prefix"])
        
        assert v.model == "gpt-4"
        assert v.task_prefix == "mytask"
        assert v.query == "hello world"
    
    def test_query_command_hyphen_to_underscore(self):
        """测试连字符自动转换为下划线"""
        query = "/task-prefix mytask /api-key secret123"
        v = get_query_command(query)
        
        # 可以用下划线访问
        assert v.task_prefix == "mytask"
        assert v.api_key == "secret123"
    
    def test_query_command_multiple_args(self):
        """测试多个参数的处理"""
        query = "/async /model gpt-4 /task-prefix mytask arg1 arg2 arg3"
        v = get_query_command(query, sub_commands=["model", "task-prefix"])
        
        assert v.model == "gpt-4"
        assert v.task_prefix == "mytask"
        assert v.query == "arg1 arg2 arg3"
    
    def test_query_command_no_special_handling(self):
        """测试不进行特殊处理的情况"""
        query = "/model gpt-4 extra /task-prefix mytask arg1 arg2"
        v = get_query_command(query, sub_commands=None)
        
        # 没有指定sub_commands，所以不会特殊处理
        assert v.model == ["gpt-4", "extra"]
        assert v.task_prefix == ["mytask", "arg1", "arg2"]
        assert v.query == ""
    
    def test_query_command_with_kwargs(self):
        """测试带键值对参数的命令"""
        query = "/config model=gpt-4 temperature=0.7"
        v = get_query_command(query)
        
        config = v.config
        assert isinstance(config, dict)
        assert config["model"] == "gpt-4"
        assert config["temperature"] == "0.7"
    
    def test_query_command_mixed_args_kwargs(self):
        """测试混合参数的命令"""
        query = "/deploy myapp env=prod version=1.0"
        v = get_query_command(query)
        
        # deploy 命令有位置参数和键值对参数
        # 当有kwargs时，返回kwargs
        deploy_info = v.get_command_info("deploy")
        assert deploy_info["args"] == ["myapp"]
        assert deploy_info["kwargs"] == {"env": "prod", "version": "1.0"}
    
    def test_query_command_has_command(self):
        """测试 has_command 方法"""
        query = "/model gpt-4 /task-prefix mytask"
        v = get_query_command(query)
        
        assert v.has_command("model") == True
        assert v.has_command("task-prefix") == True
        assert v.has_command("task_prefix") == True  # 也可以用下划线形式
        assert v.has_command("nonexistent") == False
    
    def test_query_command_get_all_commands(self):
        """测试 get_all_commands 方法"""
        query = "/first /second /third"
        v = get_query_command(query)
        
        commands = v.get_all_commands()
        assert commands == ["first", "second", "third"]
    
    def test_query_command_nonexistent_attribute(self):
        """测试访问不存在的属性"""
        query = "/model gpt-4"
        v = get_query_command(query)
        
        assert v.model == "gpt-4"
        assert v.nonexistent is None
    
    def test_query_command_empty_command(self):
        """测试空参数的命令"""
        query = "/start /stop /restart"
        v = get_query_command(query)
        
        assert v.start == ""
        assert v.stop == ""
        assert v.restart == ""
    
    def test_query_command_complex_scenario(self):
        """测试复杂场景"""
        query = '/async /model gpt-4-turbo /task-prefix analysis "Process the following data" with multiple words'
        v = get_query_command(query, sub_commands=["model", "task-prefix"])
        
        assert v.model == "gpt-4-turbo"
        assert v.task_prefix == "analysis"  # 第一个参数
        assert v.query == 'Process the following data with multiple words'  # 剩余参数
    
    def test_query_command_last_command_not_in_list(self):
        """测试最后一个命令不在子命令列表中"""
        query = "/model gpt-4 /other command /final arg1 arg2 arg3"
        v = get_query_command(query, sub_commands=["model"])
        
        # model 是子命令但不是最后一个，所以保持原样
        assert v.model == "gpt-4"
        # other 和 final 不在子命令列表中，保持原样
        assert v.other == "command"
        assert v.final == ["arg1", "arg2", "arg3"]
        assert v.query == ""
    
    def test_query_command_disable_last_takes_rest(self):
        """测试禁用 last_command_takes_rest"""
        query = "/model gpt-4 /task-prefix mytask arg1 arg2"
        v = get_query_command(query, 
                            sub_commands=["model", "task-prefix"],
                            last_command_takes_rest=False)
        
        # 禁用了特殊处理，所以所有参数都保留
        assert v.model == "gpt-4"
        assert v.task_prefix == ["mytask", "arg1", "arg2"]
        assert v.query == ""
    
    def test_query_command_repr(self):
        """测试 __repr__ 方法"""
        query = "/model gpt-4 /task-prefix mytask hello"
        v = get_query_command(query, sub_commands=["task-prefix"])
        
        repr_str = repr(v)
        assert "QueryCommand" in repr_str
        assert "model" in repr_str
        assert "task-prefix" in repr_str


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v"])
