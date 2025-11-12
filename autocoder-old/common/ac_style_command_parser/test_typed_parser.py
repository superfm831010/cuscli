import pytest
from typing import List, Dict, Any

from .config import (
    ConfigBuilder,
    create_config
)

from .typed_parser import (
    ParsedCommand,
    TypedCommandParser,
    parse_typed_query
)


class TestTypedCommandParser:
    """测试 TypedCommandParser 类"""

    def test_basic_typed_parsing(self):
        """测试基本的类型化解析"""
        config = (create_config()
                  .command("model")
                  .positional("name", required=True)
                  .command("config")
                  .keyword("temperature", type=float)
                  .keyword("max_tokens", type=int)
                  .build()
                  )

        parser = TypedCommandParser(config)
        result = parser.parse_typed(
            "/model gpt-4 /config temperature=0.8 max_tokens=100")

        assert "model" in result
        assert result["model"].args == ["gpt-4"]
        assert result["model"].is_valid

        assert "config" in result
        assert result["config"].kwargs["temperature"] == 0.8  # 转换为float
        assert result["config"].kwargs["max_tokens"] == 100  # 转换为int
        assert result["config"].is_valid

    def test_typed_parsing_with_validation_errors(self):
        """测试带验证错误的类型化解析"""
        config = (create_config()
                  .command("model")
                  .positional("name", required=True, choices=["gpt-3.5", "gpt-4"])
                  .build()
                  )

        parser = TypedCommandParser(config)
        result = parser.parse_typed("/model gpt-5")

        assert "model" in result
        assert not result["model"].is_valid
        assert len(result["model"].errors) > 0

    def test_typed_parsing_with_defaults(self):
        """测试带默认值的类型化解析"""
        config = (create_config()
                  .command("config")
                  .keyword("temperature", type=float, default=0.7)
                  .keyword("max_tokens", type=int, default=100)
                  .build()
                  )

        parser = TypedCommandParser(config)
        result = parser.parse_typed("/config temperature=0.9")

        assert result["config"].kwargs["temperature"] == 0.9
        assert result["config"].kwargs["max_tokens"] == 100  # 使用默认值

    def test_typed_parsing_with_remainder(self):
        """测试收集剩余参数的类型化解析"""
        config = (create_config()
                  .command("task")
                  .positional("prefix", required=True)
                  .collect_remainder("query")
                  .build()
                  )

        parser = TypedCommandParser(config)
        result = parser.parse_typed("/task mytask this is the query")

        assert result["task"].args == ["mytask"]
        assert result["task"].remainder == "this is the query"

    def test_typed_parsing_strict_mode(self):
        """测试严格模式"""
        config = (create_config()
                  .strict(True)
                  .command("known")
                  .build()
                  )

        parser = TypedCommandParser(config)
        result = parser.parse_typed("/known /unknown")

        assert result["known"].is_valid
        assert not result["unknown"].is_valid
        assert "Unknown command" in result["unknown"].errors[0]

    def test_bool_type_conversion(self):
        """测试布尔类型转换"""
        config = (create_config()
                  .command("flags")
                  .keyword("verbose", type=bool)
                  .keyword("debug", type=bool)
                  .build()
                  )

        parser = TypedCommandParser(config)

        # 测试各种布尔值表示
        result = parser.parse_typed("/flags verbose=true debug=false")
        assert result["flags"].kwargs["verbose"] is True
        assert result["flags"].kwargs["debug"] is False

        result = parser.parse_typed("/flags verbose=1 debug=0")
        assert result["flags"].kwargs["verbose"] is True
        assert result["flags"].kwargs["debug"] is False

        result = parser.parse_typed("/flags verbose=yes debug=no")
        assert result["flags"].kwargs["verbose"] is True
        assert result["flags"].kwargs["debug"] is False


class TestTypedQueryCommand:
    """测试 TypedQueryCommand 类"""

    def test_basic_typed_query_command(self):
        """测试基本的类型化查询命令"""
        config = (create_config()
                  .command("model")
                  .positional("name", required=True)
                  .command("temperature")
                  # value 名字比较特殊，作为位置参数，可以直接通过 result.temperature 访问
                  .positional("value", type=float)
                  .build()
                  )

        result = parse_typed_query("/model gpt-4 /temperature 0.8", config)

        assert result.model.name == "gpt-4"
        assert result.temperature == 0.8
        assert isinstance(result.temperature, float)

    def test_typed_query_command_with_remainder(self):
        """测试带剩余参数的类型化查询命令"""
        config = (create_config()
                  .command("task")
                  .positional("prefix", required=True)
                  .collect_remainder("query")
                  .build()
                  )

        result = parse_typed_query("/task mytask this is the query", config)

        assert result.task.prefix == "mytask"
        assert result.task.query == "this is the query"

    def test_typed_query_command_validation(self):
        """测试类型化查询命令的验证"""
        config = (create_config()
                  .command("model")
                  .positional("name", required=True, choices=["gpt-3.5", "gpt-4"])
                  .build()
                  )

        result = parse_typed_query("/model gpt-5", config)

        assert not result.is_valid()
        errors = result.get_errors()
        assert "model" in errors

    def test_typed_query_command_get_command(self):
        """测试获取解析后的命令对象"""
        config = (create_config()
                  .command("config")
                  .keyword("temperature", type=float)
                  .build()
                  )

        result = parse_typed_query("/config temperature=0.8", config)

        parsed_cmd = result.get_command("config")
        assert isinstance(parsed_cmd, ParsedCommand)
        assert parsed_cmd.name == "config"
        assert parsed_cmd.kwargs["temperature"] == 0.8

    def test_typed_query_command_hyphen_conversion(self):
        """测试连字符转换"""
        config = (create_config()
                  .command("task-prefix")
                  # value 名字比较特殊，作为位置参数，可以直接通过 result.task_prefix 访问
                  .positional("value")
                  .build()
                  )

        result = parse_typed_query("/task-prefix mytask", config)

        # 可以用下划线访问
        assert result.task_prefix == "mytask"
        assert result.has_command("task-prefix")
        assert result.has_command("task_prefix")


class TestIntegrationScenarios:
    """集成测试场景"""    
    def test_validation_and_error_reporting(self):
        """测试验证和错误报告"""
        config = (create_config()
                  .strict(True)  # 严格模式
                  .command("deploy")
                  .positional("app", required=True)
                  .keyword("env", required=True, choices=["dev", "staging", "prod"])
                  .keyword("version", required=True)
                  .build()
                  )

        # 缺少必需参数
        result = parse_typed_query("/deploy myapp", config)
        assert not result.is_valid()
        errors = result.get_errors()
        assert "deploy" in errors
        assert any("env" in e for e in errors["deploy"])

        # 无效的选项值
        result = parse_typed_query(
            "/deploy myapp env=test version=1.0", config)
        assert not result.is_valid()
        errors = result.get_errors()
        assert any("must be one of" in e for e in errors["deploy"])

        # 未知命令（严格模式）
        result = parse_typed_query("/unknown", config)
        assert not result.is_valid()
        errors = result.get_errors()
        assert "unknown" in errors


class TestCommandLevelRemainder:
    """测试命令级别的剩余参数收集"""        
    def test_async_command_scenario(self):
        global_config = (create_config()
                         .collect_remainder("query")
                         .command("async")
                         .max_args(0)
                         .command("model")
                         # 用 name 也可以；用 "value" 可直接 result.model 返回值
                         .positional("value", required=True)
                         .max_args(1)
                         .command("loop")
                         .positional("value", type=int)
                         .command("name")
                         .max_args(1)                         
                         .build()
                         )

        result = parse_typed_query(
            "/async /model gpt-4 /loop 3 /name task-01 analysis Process the data", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data"

        result = parse_typed_query(
            "/async /model gpt-4 /name task-01 /loop 3 analysis Process the data", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data"

        result = parse_typed_query(
            "/async /name task-01 /model gpt-4 /loop 3 analysis Process the data", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data"

    def test_quoted_string_scenario(self):
        global_config = (create_config()
                         .collect_remainder("query")
                         .command("async")
                         .max_args(0)
                         .command("model")
                         # 用 name 也可以；用 "value" 可直接 result.model 返回值
                         .positional("value", required=True)
                         .max_args(1)
                         .command("loop")
                         .positional("value", type=int)
                         .command("name")
                         .max_args(1)    
                         .command("wow") 
                         .keyword("name", type=str)
                         .keyword("x", type=str)
                         .build()
                         )

        result = parse_typed_query(
            "/async /model gpt-4 /loop 3 /name task-01 \"analysis Process the data\"", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data"

        result = parse_typed_query(
            "/async /model gpt-4 /name task-01 /loop 3 \"analysis Process the data\"", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data"

        result = parse_typed_query(
            "/async /name task-01 /model gpt-4 /loop 3 \"\"\"analysis Process the data\"\"\"", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data"       


        result = parse_typed_query(
            "/async /name task-01 /model gpt-4 /wow name=test x=\"analysis2 Process the data\" /loop 3 \"\"\"analysis Process the data\"\"\"", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data" 
        assert result.wow.name == "test"
        assert result.wow.x == "analysis2 Process the data"


        result = parse_typed_query(
            "/async /name task-01 /model gpt-4 /wow name=test x=\"\"\"analysis2 \Process the data\"\"\" /loop 3 \"\"\"analysis Process the data\"\"\"", global_config)
        assert result.model == "gpt-4"
        assert result.loop == 3
        assert result.name == "task-01"
        assert result.query == "analysis Process the data" 
        assert result.wow.name == "test"
        assert result.wow.x == "analysis2 \Process the data"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
