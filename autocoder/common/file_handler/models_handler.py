import os
import json
import shlex
from typing import Optional

from rich.console import Console
from rich.table import Table

from autocoder.common.international import get_message
from autocoder.common.ac_style_command_parser import create_config, parse_typed_query
from autocoder.auto_coder_runner import get_current_memory
from autocoder.common.result_manager import ResultManager
from autocoder.common.printer import Printer


class ModelsHandler:
    """处理模型管理相关的操作"""
    
    def __init__(self):
        self.console = Console()
        self.printer = Printer(console=self.console)
        self._config = None
    
    def _create_config(self):
        """创建 models 命令的类型化配置"""
        if self._config is None:
            self._config = (create_config()
                .collect_remainder("query")  # 收集剩余参数
                .command("list")
                .max_args(0)  # 列出所有模型
                .command("add")
                .positional("name", required=True)
                .positional("api_key", required=True)
                .max_args(2)  # 简化添加模型
                .command("add_model")
                .collect_remainder("params")  # 收集key=value参数
                .max_args(-1)  # 自定义参数添加模型
                .command("remove")
                .positional("name", required=True)
                .max_args(1)  # 删除模型
                .command("speed_test")
                .positional("rounds", type=int)
                .keyword("long_context", type=bool)
                .max_args(1)  # 速度测试
                .command("input_price")
                .positional("name", required=True)
                .positional("price", type=float, required=True)
                .max_args(2)  # 设置输入价格
                .command("output_price")
                .positional("name", required=True)
                .positional("price", type=float, required=True)
                .max_args(2)  # 设置输出价格
                .command("speed")
                .positional("name", required=True)
                .positional("speed_value", type=float, required=True)
                .max_args(2)  # 设置速度
                .build()
            )
        return self._config
    
    def handle_models_command(self, query: str) -> Optional[None]:
        """
        处理模型管理命令的主入口
        
        Args:
            query: 查询字符串
            
        Returns:
            None: 表示处理了命令，应该返回而不继续执行
        """
        original_query = query
        query = query.strip()
        
        # 检查产品模式限制
        memory = get_current_memory()
        product_mode = memory.get("product_mode", "lite")
        if product_mode != "lite":
            self.printer.print_in_terminal("models_lite_only", style="red")
            return None
        
        # 使用原始的字符串匹配逻辑来保持兼容性
        subcmd = ""
        
        if "/list" in query:
            subcmd = "/list"
            query = query.replace("/list", "", 1).strip()
        elif "/add_model" in query:
            subcmd = "/add_model"
            query = query.replace("/add_model", "", 1).strip()
        elif "/add" in query:
            subcmd = "/add"
            query = query.replace("/add", "", 1).strip()
        elif "/activate" in query:  # alias to /add
            subcmd = "/add"
            query = query.replace("/activate", "", 1).strip()
        elif "/remove" in query:
            subcmd = "/remove"
            query = query.replace("/remove", "", 1).strip()
        elif "/speed-test" in query:
            subcmd = "/speed-test"
            query = query.replace("/speed-test", "", 1).strip()
        elif "/speed_test" in query:
            subcmd = "/speed-test"
            query = query.replace("/speed_test", "", 1).strip()
        elif "/input_price" in query:
            subcmd = "/input_price"
            query = query.replace("/input_price", "", 1).strip()
        elif "/output_price" in query:
            subcmd = "/output_price"
            query = query.replace("/output_price", "", 1).strip()
        elif "/speed" in query:
            subcmd = "/speed"
            query = query.replace("/speed", "", 1).strip()
        
        if not subcmd:
            return self._handle_no_args()
        
        # 根据子命令调用对应的处理方法
        if subcmd == "/list":
            return self._handle_list()
        elif subcmd == "/add":
            return self._handle_add_simple(query)
        elif subcmd == "/add_model":
            return self._handle_add_model_kv(query)
        elif subcmd == "/remove":
            return self._handle_remove_simple(query)
        elif subcmd == "/speed-test":
            return self._handle_speed_test_simple(query)
        elif subcmd == "/input_price":
            return self._handle_input_price_simple(query)
        elif subcmd == "/output_price":
            return self._handle_output_price_simple(query)
        elif subcmd == "/speed":
            return self._handle_speed_simple(query)
        else:
            self.printer.print_in_terminal("models_unknown_subcmd", style="yellow", subcmd=subcmd)
            return None
    
    def _handle_no_args(self) -> None:
        """处理无参数情况"""
        self.printer.print_in_terminal("models_usage")
        return None
    
    def _get_llm_manager(self):
        """获取LLM管理器"""
        from autocoder.common.llms import LLMManager
        return LLMManager()
    
    def _handle_list(self) -> None:
        """处理列表命令"""
        llm_manager = self._get_llm_manager()
        models_dict = llm_manager.get_all_models()  # Dict[str, LLMModel]
        models_data = [model.dict() for model in models_dict.values()]  # 转换为字典列表
        result_manager = ResultManager()
        
        if models_data:
            # Sort models by speed (average_speed)
            sorted_models = sorted(
                models_data, key=lambda x: float(x.get('average_speed', 0)))
            sorted_models.reverse()

            table = Table(
                title=self.printer.get_message_from_key("models_title"),
                expand=True,
                show_lines=True
            )
            table.add_column("Name", style="cyan", width=30,
                             overflow="fold", no_wrap=False)
            table.add_column("Model Name", style="magenta",
                             width=30, overflow="fold", no_wrap=False)
            table.add_column("Base URL", style="white",
                             width=40, overflow="fold", no_wrap=False)
            table.add_column("Input Price (M)", style="magenta",
                             width=15, overflow="fold", no_wrap=False)
            table.add_column("Output Price (M)", style="magenta",
                             width=15, overflow="fold", no_wrap=False)
            table.add_column("Speed (s/req)", style="blue",
                             width=15, overflow="fold", no_wrap=False)
            
            for m in sorted_models:
                # Check if api_key_path exists and file exists
                is_api_key_set = "api_key" in m
                name = m.get("name", "")
                if is_api_key_set:
                    api_key = m.get("api_key", "").strip()
                    if not api_key:
                        self.printer.print_in_terminal(
                            "models_api_key_empty", style="yellow", name=name)
                    name = f"{name} *"

                table.add_row(
                    name,
                    m.get("model_name", ""),
                    m.get("base_url", ""),
                    f"{m.get('input_price', 0.0):.2f}",
                    f"{m.get('output_price', 0.0):.2f}",
                    f"{m.get('average_speed', 0.0):.3f}"
                )
            self.console.print(table)
            result_manager.add_result(content=json.dumps(sorted_models, ensure_ascii=False), meta={
                "action": "models",
                "input": {"query": "list"}
            })
        else:
            self.printer.print_in_terminal("models_no_models", style="yellow")
            result_manager.add_result(content="No models found", meta={
                "action": "models",
                "input": {"query": "list"}
            })
        
        return None
    
    def _handle_add_simple(self, query: str) -> None:
        """处理简化添加命令"""
        args = query.strip().split(" ")
        if len(args) != 2:
            llm_manager = self._get_llm_manager()
            models_list = "\n".join([m.name for m in llm_manager.get_default_models()])
            self.printer.print_in_terminal("models_add_usage", style="red", models=models_list)
            
            result_manager = ResultManager()
            result_manager.add_result(
                content=self.printer.get_message_from_key_with_format("models_add_usage", models=models_list), 
                meta={"action": "models", "input": {"query": f"add {query}"}}
            )
            return None
        
        name, api_key = args[0], args[1]
        llm_manager = self._get_llm_manager()
        result_manager = ResultManager()
        
        result_success = llm_manager.update_model_with_api_key(name, api_key)
        if result_success:
            result_manager.add_result(content=f"models_added: {name}", meta={
                "action": "models",
                "input": {"query": f"add {name}"}
            })
            self.printer.print_in_terminal("models_added", style="green", name=name)
        else:
            result_manager.add_result(content=f"models_add_failed: {name}", meta={
                "action": "models",
                "input": {"query": f"add {name}"}
            })
            self.printer.print_in_terminal("models_add_failed", style="red", name=name)
        
        return None
    
    def _handle_add_model_kv(self, query: str) -> None:
        """处理自定义参数添加命令"""
        # Parse key=value pairs
        kv_pairs = shlex.split(query) if query else []
        data_dict = {}
        for pair in kv_pairs:
            if '=' not in pair:
                self.printer.print_in_terminal("models_add_model_params", style="red")
                continue
            k, v = pair.split('=', 1)
            data_dict[k.strip()] = v.strip()

        # Name is required
        if "name" not in data_dict:
            self.printer.print_in_terminal("models_add_model_name_required", style="red")
            return None

        llm_manager = self._get_llm_manager()
        models_dict = llm_manager.get_all_models()
        models_data = [model.dict() for model in models_dict.values()]
        result_manager = ResultManager()
        
        # Check duplication
        if any(m["name"] == data_dict["name"] for m in models_data):
            self.printer.print_in_terminal("models_add_model_exists", style="yellow", name=data_dict["name"])
            result_manager.add_result(
                content=self.printer.get_message_from_key_with_format("models_add_model_exists", name=data_dict["name"]), 
                meta={"action": "models", "input": {"query": f"add_model {data_dict['name']}"}}
            )
            return None

        # Create model with defaults
        final_model = {
            "name": data_dict["name"],
            "model_type": data_dict.get("model_type", "saas/openai"),
            "model_name": data_dict.get("model_name", data_dict["name"]),
            "base_url": data_dict.get("base_url", "https://api.openai.com/v1"),
            "api_key_path": data_dict.get("api_key_path", "api.openai.com"),
            "description": data_dict.get("description", ""),
            "is_reasoning": data_dict.get("is_reasoning", "false") in ["true", "True", "TRUE", "1"]
        }

        models_data.append(final_model)
        llm_manager.registry.save()
        self.printer.print_in_terminal("models_add_model_success", style="green", name=data_dict["name"])
        result_manager.add_result(content=f"models_add_model_success: {data_dict['name']}", meta={
            "action": "models",
            "input": {"query": f"add_model {data_dict['name']}"}
        })
        
        return None
    
    def _handle_remove_simple(self, query: str) -> None:
        """处理删除命令"""
        args = query.strip().split(" ")
        if len(args) < 1 or not args[0]:
            self.printer.print_in_terminal("models_add_usage", style="red")
            result_manager = ResultManager()
            result_manager.add_result(content=self.printer.get_message_from_key("models_add_usage"), meta={
                "action": "models",
                "input": {"query": f"remove {query}"}
            })
            return None
        
        name = args[0]
        llm_manager = self._get_llm_manager()
        models_dict = llm_manager.get_all_models()
        models_data = [model.dict() for model in models_dict.values()]
        result_manager = ResultManager()
        
        filtered_models = [m for m in models_data if m["name"] != name]
        if len(filtered_models) == len(models_data):
            self.printer.print_in_terminal("models_add_model_remove", style="yellow", name=name)
            result_manager.add_result(
                content=self.printer.get_message_from_key_with_format("models_add_model_remove", name=name), 
                meta={"action": "models", "input": {"query": f"remove {name}"}}
            )
            return None
        
        llm_manager.registry.save()
        self.printer.print_in_terminal("models_add_model_removed", style="green", name=name)
        result_manager.add_result(
            content=self.printer.get_message_from_key_with_format("models_add_model_removed", name=name), 
            meta={"action": "models", "input": {"query": f"remove {name}"}}
        )
        
        return None
    
    def _handle_speed_test_simple(self, query: str) -> None:
        """处理速度测试命令"""
        from autocoder.common.model_speed_tester import render_speed_test_in_terminal
        
        test_rounds = 1  # 默认测试轮数
        enable_long_context = False
        
        if "/long_context" in query:
            enable_long_context = True
            query = query.replace("/long_context", "", 1).strip()
        
        if "/long-context" in query:
            enable_long_context = True
            query = query.replace("/long-context", "", 1).strip()
        
        # 解析可选的测试轮数参数
        args = query.strip().split()
        if args and args[0].isdigit():
            test_rounds = int(args[0])
        
        memory = get_current_memory()
        product_mode = memory.get("product_mode", "lite")
        
        render_speed_test_in_terminal(product_mode, test_rounds, enable_long_context=enable_long_context)
        
        result_manager = ResultManager()
        result_manager.add_result(content="models test success", meta={
            "action": "models",
            "input": {"query": f"speed_test {test_rounds}"}
        })
        
        return None
    
    def _handle_input_price_simple(self, query: str) -> None:
        """处理输入价格设置命令"""
        args = query.strip().split()
        if len(args) < 2:
            result_manager = ResultManager()
            result_manager.add_result(content=self.printer.get_message_from_key("models_input_price_usage"), meta={
                "action": "models",
                "input": {"query": f"input_price {query}"}
            })
            self.printer.print_in_terminal("models_input_price_usage", style="red")
            return None
        
        name = args[0]
        try:
            price = float(args[1])
        except ValueError as e:
            result_manager = ResultManager()
            result_manager.add_result(content=f"models_invalid_price: {str(e)}", meta={
                "action": "models",
                "input": {"query": f"input_price {query}"}
            })
            self.printer.print_in_terminal("models_invalid_price", style="red", error=str(e))
            return None
        
        llm_manager = self._get_llm_manager()
        result_manager = ResultManager()
        
        if llm_manager.update_model_input_price(name, price):
            self.printer.print_in_terminal("models_input_price_updated", style="green", name=name, price=price)
            result_manager.add_result(content=f"models_input_price_updated: {name} {price}", meta={
                "action": "models",
                "input": {"query": f"input_price {name} {price}"}
            })
        else:
            self.printer.print_in_terminal("models_not_found", style="red", name=name)
            result_manager.add_result(content=f"models_not_found: {name}", meta={
                "action": "models",
                "input": {"query": f"input_price {name} {price}"}
            })
        
        return None
    
    def _handle_output_price_simple(self, query: str) -> None:
        """处理输出价格设置命令"""
        args = query.strip().split()
        if len(args) < 2:
            result_manager = ResultManager()
            result_manager.add_result(content=self.printer.get_message_from_key("models_output_price_usage"), meta={
                "action": "models",
                "input": {"query": f"output_price {query}"}
            })
            self.printer.print_in_terminal("models_output_price_usage", style="red")
            return None
        
        name = args[0]
        try:
            price = float(args[1])
        except ValueError as e:
            self.printer.print_in_terminal("models_invalid_price", style="red", error=str(e))
            result_manager = ResultManager()
            result_manager.add_result(content=f"models_invalid_price: {str(e)}", meta={
                "action": "models",
                "input": {"query": f"output_price {query}"}
            })
            return None
        
        llm_manager = self._get_llm_manager()
        result_manager = ResultManager()
        
        if llm_manager.update_model_output_price(name, price):
            self.printer.print_in_terminal("models_output_price_updated", style="green", name=name, price=price)
            result_manager.add_result(content=f"models_output_price_updated: {name} {price}", meta={
                "action": "models",
                "input": {"query": f"output_price {name} {price}"}
            })
        else:
            self.printer.print_in_terminal("models_not_found", style="red", name=name)
            result_manager.add_result(content=f"models_not_found: {name}", meta={
                "action": "models",
                "input": {"query": f"output_price {name} {price}"}
            })
        
        return None
    
    def _handle_speed_simple(self, query: str) -> None:
        """处理速度设置命令"""
        args = query.strip().split()
        if len(args) < 2:
            result_manager = ResultManager()
            result_manager.add_result(content=self.printer.get_message_from_key("models_speed_usage"), meta={
                "action": "models",
                "input": {"query": f"speed {query}"}
            })
            self.printer.print_in_terminal("models_speed_usage", style="red")
            return None
        
        name = args[0]
        try:
            speed_value = float(args[1])
        except ValueError as e:
            self.printer.print_in_terminal("models_invalid_speed", style="red", error=str(e))
            result_manager = ResultManager()
            result_manager.add_result(content=f"models_invalid_speed: {str(e)}", meta={
                "action": "models",
                "input": {"query": f"speed {query}"}
            })
            return None
        
        llm_manager = self._get_llm_manager()
        result_manager = ResultManager()
        
        if llm_manager.update_model_speed(name, speed_value):
            self.printer.print_in_terminal("models_speed_updated", style="green", name=name, speed=speed_value)
            result_manager.add_result(content=f"models_speed_updated: {name} {speed_value}", meta={
                "action": "models",
                "input": {"query": f"speed {name} {speed_value}"}
            })
        else:
            self.printer.print_in_terminal("models_not_found", style="red", name=name)
            result_manager.add_result(content=f"models_not_found: {name}", meta={
                "action": "models",
                "input": {"query": f"speed {name} {speed_value}"}
            })
        
        return None
