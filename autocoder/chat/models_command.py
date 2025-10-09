import json
import shlex
import fnmatch # Add fnmatch for wildcard matching
import traceback
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import byzerllm
from typing import Generator
from autocoder.common.llms import LLMManager
from autocoder.common.printer import Printer
from autocoder.common.result_manager import ResultManager
from autocoder.common.model_speed_tester import render_speed_test_in_terminal
from autocoder.utils.llms import get_single_llm
from autocoder.common.core_config import get_memory_manager

def handle_models_command(query: str):
    """    
    Handle /models subcommands:
      /models /list - List all models (default + custom)
      /models /add <n> <api_key> - Add model with simplified params
      /models /add_model name=xxx base_url=xxx ... - Add model with custom params
      /models /remove <n> - Remove model by name
      /models /chat <content> - Chat with a model
    """
    console = Console()
    printer = Printer(console=console)    
    
    memory_manager = get_memory_manager()
    product_mode = memory_manager.get_config("product_mode", "lite")
    if product_mode != "lite":
        printer.print_in_terminal("models_lite_only", style="red")
        return

    # Check if the query is empty or only whitespace
    if not query.strip():
        printer.print_in_terminal("models_usage")
        return

    # Initialize LLM Manager
    llm_manager = LLMManager()
    
    subcmd = ""
    if "/list" in query:
        subcmd = "/list"
        query = query.replace("/list", "", 1).strip()

    if "/add_model" in query:
        subcmd = "/add_model"
        query = query.replace("/add_model", "", 1).strip()

    if "/add" in query:
        subcmd = "/add"
        query = query.replace("/add", "", 1).strip()

    # alias to /add
    if "/activate" in query:
        subcmd = "/add"
        query = query.replace("/activate", "", 1).strip()    

    if "/remove" in query:
        subcmd = "/remove"
        query = query.replace("/remove", "", 1).strip()

    if "/speed-test" in query:
        subcmd = "/speed-test"
        query = query.replace("/speed-test", "", 1).strip()

    if "/speed_test" in query:
        subcmd = "/speed-test"
        query = query.replace("/speed_test", "", 1).strip() 

    if "input_price" in query:
        subcmd = "/input_price"
        query = query.replace("/input_price", "", 1).strip()

    if "output_price" in query:
        subcmd = "/output_price"
        query = query.replace("/output_price", "", 1).strip()        

    if "/speed" in query:
        subcmd = "/speed"
        query = query.replace("/speed", "", 1).strip()
        
    if "/chat" in query:
        subcmd = "/chat"
        query = query.replace("/chat", "", 1).strip()

    if not subcmd:
        printer.print_in_terminal("models_usage")        

    result_manager = ResultManager()
    
    if subcmd == "/list":
        pattern = query.strip()  # Get the filter pattern from the query
        
        # Get all models from LLM Manager
        all_models = llm_manager.get_all_models()
        models_list = list(all_models.values())
        
        if pattern:  # Apply filter if a pattern is provided
            filtered_models = [
                m for m in models_list if fnmatch.fnmatch(m.name, pattern)
            ]
        else:
            filtered_models = models_list

        if filtered_models:
            # Sort models by name
            sorted_models = sorted(filtered_models, key=lambda x: x.name)

            table = Table(
                title=printer.get_message_from_key("models_title") + (f" (Filtered by: '{pattern}')" if pattern else ""),
                expand=True,
                show_lines=True
            )
            table.add_column("Name", style="cyan", width=40, overflow="fold", no_wrap=False)
            table.add_column("Model Name", style="magenta", width=30, overflow="fold", no_wrap=False)
            table.add_column("Base URL", style="white", width=30, overflow="fold", no_wrap=False)
            table.add_column("Input Price (M)", style="magenta", width=15, overflow="fold", no_wrap=False)
            table.add_column("Output Price (M)", style="magenta", width=15, overflow="fold", no_wrap=False)
            table.add_column("API Key", style="blue", width=15, overflow="fold", no_wrap=False)
            
            for m in sorted_models:
                # Check if model has API key
                has_key = llm_manager.has_key(m.name)
                name = m.name
                if has_key:
                    name = f"{name} *"

                table.add_row(
                    name,
                    m.model_name,
                    m.base_url,
                    f"{m.input_price:.2f}",
                    f"{m.output_price:.2f}",
                    "✓" if has_key else "✗"
                )
            console.print(table)
            
            # Convert models to dict for JSON serialization
            models_data = [
                {
                    "name": m.name,
                    "model_name": m.model_name,
                    "base_url": m.base_url,
                    "input_price": m.input_price,
                    "output_price": m.output_price,
                    "has_api_key": llm_manager.has_key(m.name)
                }
                for m in sorted_models
            ]
            
            result_manager.add_result(content=json.dumps(models_data, ensure_ascii=False), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
        else:
            if pattern:
                printer.print_in_terminal("models_no_models_matching_pattern", style="yellow", pattern=pattern)
                result_manager.add_result(content=f"No models found matching pattern: {pattern}", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
            else:
                printer.print_in_terminal("models_no_models", style="yellow")
                result_manager.add_result(content="No models found", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })

    elif subcmd == "/input_price":
        args = query.strip().split()
        if len(args) >= 2:
            name = args[0]
            try:
                price = float(args[1])
                if llm_manager.update_input_price(name, price):
                    printer.print_in_terminal("models_input_price_updated", style="green", name=name, price=price)
                    result_manager.add_result(content=f"models_input_price_updated: {name} {price}", meta={
                        "action": "models",
                        "input": {
                            "query": query
                        }
                    })
                else:
                    printer.print_in_terminal("models_not_found", style="red", name=name)
                    result_manager.add_result(content=f"models_not_found: {name}", meta={
                        "action": "models",
                        "input": {
                            "query": query
                        }
                    })
            except ValueError as e:
                result_manager.add_result(content=f"models_invalid_price: {str(e)}", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
                printer.print_in_terminal("models_invalid_price", style="red", error=str(e))
        else:
            result_manager.add_result(content=printer.get_message_from_key("models_input_price_usage"), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            printer.print_in_terminal("models_input_price_usage", style="red")

    elif subcmd == "/output_price":
        args = query.strip().split()
        if len(args) >= 2:
            name = args[0]
            try:
                price = float(args[1])
                if llm_manager.update_output_price(name, price):
                    printer.print_in_terminal("models_output_price_updated", style="green", name=name, price=price)
                    result_manager.add_result(content=f"models_output_price_updated: {name} {price}", meta={
                        "action": "models",
                        "input": {
                            "query": query
                        }
                    })
                else:
                    printer.print_in_terminal("models_not_found", style="red", name=name)
                    result_manager.add_result(content=f"models_not_found: {name}", meta={
                        "action": "models",
                        "input": {
                            "query": query
                        }
                    })
            except ValueError as e:
                printer.print_in_terminal("models_invalid_price", style="red", error=str(e))
                result_manager.add_result(content=f"models_invalid_price: {str(e)}", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
        else:
            result_manager.add_result(content=printer.get_message_from_key("models_output_price_usage"), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            printer.print_in_terminal("models_output_price_usage", style="red")

    elif subcmd == "/speed":
        args = query.strip().split()
        if len(args) >= 2:
            name = args[0]
            try:
                speed = float(args[1])
                # Speed functionality not implemented in LLMManager yet
                printer.print_in_terminal("models_speed_not_implemented", style="yellow")
                result_manager.add_result(content="Speed functionality not implemented yet", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
            except ValueError as e:
                printer.print_in_terminal("models_invalid_speed", style="red", error=str(e))
                result_manager.add_result(content=f"models_invalid_speed: {str(e)}", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
        else:
            result_manager.add_result(content=printer.get_message_from_key("models_speed_usage"), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            printer.print_in_terminal("models_speed_usage", style="red")

    elif subcmd == "/speed-test" or subcmd == "/check":
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

        render_speed_test_in_terminal(product_mode, test_rounds, enable_long_context=enable_long_context)
        ## 等待优化，获取明细数据
        result_manager.add_result(content="models test success", meta={
            "action": "models",
            "input": {
                "query": query
            }
        })

    elif subcmd == "/add":
        # Support both simplified and legacy formats
        args = query.strip().split(" ")               
        if len(args) == 2:
            # Simplified: /models /add <name> <api_key>
            name, api_key = args[0], args[1]            
            result = llm_manager.update_model_with_api_key(name, api_key)
            if result:
                result_manager.add_result(content=f"models_added: {name}", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
                printer.print_in_terminal("models_added", style="green", name=name)
            else:
                result_manager.add_result(content=f"models_add_failed: {name}", meta={
                    "action": "models",
                    "input": {
                        "query": query
                    }
                })
                printer.print_in_terminal("models_add_failed", style="red", name=name)
        else:            
            # Get available model names from LLM Manager
            all_models = llm_manager.get_all_models()
            models_list = "\n".join([m for m in all_models.keys()])
            printer.print_in_terminal("models_add_usage", style="red", models=models_list)
            result_manager.add_result(content=printer.get_message_from_key_with_format("models_add_usage", models=models_list), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })

    elif subcmd == "/add_model":
        # Parse key=value pairs: /models /add_model name=abc base_url=http://xx ...       
        # Collect key=value pairs
        kv_pairs = shlex.split(query)
        data_dict = {}
        for pair in kv_pairs:
            if '=' not in pair:
                printer.print_in_terminal("models_add_model_params", style="red")
                continue
            k, v = pair.split('=', 1)
            data_dict[k.strip()] = v.strip()

        # Name is required
        if "name" not in data_dict:
            printer.print_in_terminal("models_add_model_name_required", style="red")
            return

        # Check duplication
        if llm_manager.check_model_exists(data_dict["name"]):
            printer.print_in_terminal("models_add_model_exists", style="yellow", name=data_dict["name"])
            result_manager.add_result(content=printer.get_message_from_key_with_format("models_add_model_exists", name=data_dict["name"]), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            return

        # Create model with defaults
        final_model = {
            "name": data_dict["name"],
            "model_type": data_dict.get("model_type", "saas/openai"),
            "model_name": data_dict.get("model_name", data_dict["name"]),
            "base_url": data_dict.get("base_url", "https://api.openai.com/v1"),
            "description": data_dict.get("description", ""),
            "is_reasoning": data_dict.get("is_reasoning", "false") in ["true", "True", "TRUE", "1"],
            "input_price": float(data_dict.get("input_price", "0.0")),
            "output_price": float(data_dict.get("output_price", "0.0")),
            "context_window": int(data_dict.get("context_window", "32768")),
            "max_output_tokens": int(data_dict.get("max_output_tokens", "8096"))
        }

        # Add API key if provided
        if "api_key" in data_dict:
            final_model["api_key"] = data_dict["api_key"]

        llm_manager.add_models([final_model])
        printer.print_in_terminal("models_add_model_success", style="green", name=data_dict["name"])
        result_manager.add_result(content=f"models_add_model_success: {data_dict['name']}", meta={
            "action": "models",
            "input": {
                "query": query
            }
        })

    elif subcmd == "/remove":
        args = query.strip().split(" ")
        if len(args) < 1:
            printer.print_in_terminal("models_remove_usage", style="red")
            result_manager.add_result(content=printer.get_message_from_key("models_remove_usage"), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            return
        name = args[0]
        if not llm_manager.check_model_exists(name):
            printer.print_in_terminal("models_add_model_remove", style="yellow", name=name)
            result_manager.add_result(content=printer.get_message_from_key_with_format("models_add_model_remove", name=name), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            return
        
        # 尝试删除模型
        if llm_manager.remove_model(name):
            printer.print_in_terminal("models_add_model_removed", style="green", name=name)
            result_manager.add_result(content=printer.get_message_from_key_with_format("models_add_model_removed", name=name), meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
        else:
            # 删除失败，可能是默认模型
            printer.print_in_terminal("models_remove_failed", style="red", name=name)
            result_manager.add_result(content=f"Failed to remove model: {name}. Cannot remove default models.", meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
        
    elif subcmd == "/chat":
        if not query.strip():
            printer.print_in_terminal("Please provide content in format: <model_name> <question>", style="yellow")
            result_manager.add_result(content="Please provide content in format: <model_name> <question>", meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            return
            
        # 分离模型名称和用户问题
        parts = query.strip().split(' ', 1)  # 只在第一个空格处分割
        if len(parts) < 2:
            printer.print_in_terminal("Correct format should be: <model_name> <question>, where question can contain spaces", style="yellow")
            result_manager.add_result(content="Correct format should be: <model_name> <question>, where question can contain spaces", meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
            return
            
        model_name = parts[0]
        user_question = parts[1]  # 这将包含所有剩余文本，保留空格
        memory_manager = get_memory_manager()
        product_mode = memory_manager.get_config("product_mode", "lite")
        
        try:
            # Get the model
            llm = get_single_llm(model_name, product_mode=product_mode)
            
            @byzerllm.prompt()
            def chat_func(content: str) -> str:
                """
                {{ content }}
                """
                return {} #type: ignore
            
            # Support custom llm_config parameters
            result = chat_func.with_llm(llm).run(user_question)
            output_text = ""            
            for res in result:
                output_text += res
                print(res, end="", flush=True)
            print("\n")    
            
            # Print the result
            
            result_manager.add_result(content=output_text, meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
        except Exception as e:
            error_message = f"Error chating with model: {str(e)}"
            printer.print_str_in_terminal(error_message, style="red")
            result_manager.add_result(content=error_message, meta={
                "action": "models",
                "input": {
                    "query": query
                }
            })
    else:
        printer.print_in_terminal("models_unknown_subcmd", style="yellow", subcmd=subcmd)
        result_manager.add_result(content=printer.get_message_from_key_with_format("models_unknown_subcmd", subcmd=subcmd), meta={ 
            "action": "models",
            "input": {
                "query": query
            }
        })