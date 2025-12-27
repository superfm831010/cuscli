import json
import shlex
import fnmatch  # Add fnmatch for wildcard matching
from rich.console import Console
from rich.table import Table
import byzerllm
from autocoder.common.llms import LLMManager
from autocoder.common.printer import Printer
from autocoder.common.result_manager import ResultManager
from autocoder.common.model_speed_tester import render_speed_test_in_terminal
from autocoder.utils.llms import get_single_llm
from autocoder.common.core_config import get_memory_manager


def handle_models_command(query: str):
    """
    Handle /models subcommands:
      /models /list [pattern] - List all models (default + custom), optionally filter by pattern
      /models provider/model_name <api_key> - Activate a model with API key
      /models /add_provider name=xxx base_url=xxx ... - Add custom provider
      /models /remove <name> - Remove custom model by name
      /models /chat <model_name> <question> - Chat with a model
      /models /speed-test [rounds] - Test model speed
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

    if "/add_provider" in query:
        subcmd = "/add_provider"
        query = query.replace("/add_provider", "", 1).strip()

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

    # 如果没有找到任何子命令，检查是否是简化的激活命令格式: provider/model_name <api_key>
    if not subcmd and query.strip():
        parts = query.strip().split()
        if len(parts) >= 2 and "/" in parts[0]:
            # 这是简化的激活命令
            subcmd = "/activate"
        else:
            printer.print_in_terminal("models_usage")
            return

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
            # Sort models by provider and name
            sorted_models = sorted(
                filtered_models, key=lambda x: (x.provider or "", x.name)
            )

            table = Table(
                title=printer.get_message_from_key("models_title")
                + (f" (Filtered by: '{pattern}')" if pattern else ""),
                expand=True,
                show_lines=True,
            )
            table.add_column(
                "Provider/Model", style="cyan", width=40, overflow="fold", no_wrap=False
            )
            table.add_column(
                "Description", style="white", width=30, overflow="fold", no_wrap=False
            )
            table.add_column(
                "Input Price (M)",
                style="magenta",
                width=15,
                overflow="fold",
                no_wrap=False,
            )
            table.add_column(
                "Output Price (M)",
                style="magenta",
                width=15,
                overflow="fold",
                no_wrap=False,
            )
            table.add_column(
                "API Key", style="blue", width=15, overflow="fold", no_wrap=False
            )

            for m in sorted_models:
                # Check if model has API key
                has_key = llm_manager.has_key(m.name)
                display_name = m.name
                if has_key:
                    display_name = f"{display_name} ✓"

                table.add_row(
                    display_name,
                    m.description or "",
                    f"{m.input_price:.2f}",
                    f"{m.output_price:.2f}",
                    "✓" if has_key else "✗",
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
                    "has_api_key": llm_manager.has_key(m.name),
                }
                for m in sorted_models
            ]

            result_manager.add_result(
                content=json.dumps(models_data, ensure_ascii=False),
                meta={"action": "models", "input": {"query": query}},
            )
        else:
            if pattern:
                printer.print_in_terminal(
                    "models_no_models_matching_pattern", style="yellow", pattern=pattern
                )
                result_manager.add_result(
                    content=f"No models found matching pattern: {pattern}",
                    meta={"action": "models", "input": {"query": query}},
                )
            else:
                printer.print_in_terminal("models_no_models", style="yellow")
                result_manager.add_result(
                    content="No models found",
                    meta={"action": "models", "input": {"query": query}},
                )

    elif subcmd == "/input_price":
        args = query.strip().split()
        if len(args) >= 2:
            name = args[0]
            try:
                price = float(args[1])
                if llm_manager.update_input_price(name, price):
                    printer.print_in_terminal(
                        "models_input_price_updated",
                        style="green",
                        name=name,
                        price=price,
                    )
                    result_manager.add_result(
                        content=f"models_input_price_updated: {name} {price}",
                        meta={"action": "models", "input": {"query": query}},
                    )
                else:
                    printer.print_in_terminal(
                        "models_not_found", style="red", name=name
                    )
                    result_manager.add_result(
                        content=f"models_not_found: {name}",
                        meta={"action": "models", "input": {"query": query}},
                    )
            except ValueError as e:
                result_manager.add_result(
                    content=f"models_invalid_price: {str(e)}",
                    meta={"action": "models", "input": {"query": query}},
                )
                printer.print_in_terminal(
                    "models_invalid_price", style="red", error=str(e)
                )
        else:
            result_manager.add_result(
                content=printer.get_message_from_key("models_input_price_usage"),
                meta={"action": "models", "input": {"query": query}},
            )
            printer.print_in_terminal("models_input_price_usage", style="red")

    elif subcmd == "/output_price":
        args = query.strip().split()
        if len(args) >= 2:
            name = args[0]
            try:
                price = float(args[1])
                if llm_manager.update_output_price(name, price):
                    printer.print_in_terminal(
                        "models_output_price_updated",
                        style="green",
                        name=name,
                        price=price,
                    )
                    result_manager.add_result(
                        content=f"models_output_price_updated: {name} {price}",
                        meta={"action": "models", "input": {"query": query}},
                    )
                else:
                    printer.print_in_terminal(
                        "models_not_found", style="red", name=name
                    )
                    result_manager.add_result(
                        content=f"models_not_found: {name}",
                        meta={"action": "models", "input": {"query": query}},
                    )
            except ValueError as e:
                printer.print_in_terminal(
                    "models_invalid_price", style="red", error=str(e)
                )
                result_manager.add_result(
                    content=f"models_invalid_price: {str(e)}",
                    meta={"action": "models", "input": {"query": query}},
                )
        else:
            result_manager.add_result(
                content=printer.get_message_from_key("models_output_price_usage"),
                meta={"action": "models", "input": {"query": query}},
            )
            printer.print_in_terminal("models_output_price_usage", style="red")

    elif subcmd == "/speed":
        args = query.strip().split()
        if len(args) >= 2:
            name = args[0]
            try:
                speed = float(args[1])
                # Speed functionality not implemented in LLMManager yet
                printer.print_in_terminal(
                    "models_speed_not_implemented", style="yellow"
                )
                result_manager.add_result(
                    content="Speed functionality not implemented yet",
                    meta={"action": "models", "input": {"query": query}},
                )
            except ValueError as e:
                printer.print_in_terminal(
                    "models_invalid_speed", style="red", error=str(e)
                )
                result_manager.add_result(
                    content=f"models_invalid_speed: {str(e)}",
                    meta={"action": "models", "input": {"query": query}},
                )
        else:
            result_manager.add_result(
                content=printer.get_message_from_key("models_speed_usage"),
                meta={"action": "models", "input": {"query": query}},
            )
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

        render_speed_test_in_terminal(
            product_mode, test_rounds, enable_long_context=enable_long_context
        )
        ## 等待优化，获取明细数据
        result_manager.add_result(
            content="models test success",
            meta={"action": "models", "input": {"query": query}},
        )

    elif subcmd == "/activate":
        # 简化的激活命令: /models provider/model_name <api_key>
        args = query.strip().split(" ")
        if len(args) >= 2:
            name, api_key = args[0], args[1]

            # 检查模型是否存在于内置模型中
            if not llm_manager.check_model_exists(name):
                printer.print_in_terminal("models_not_found", style="red", name=name)
                printer.print_in_terminal("models_not_found_hint", style="yellow")

                result_manager.add_result(
                    content=printer.get_message_from_key_with_format(
                        "models_not_found", name=name
                    )
                    + printer.get_message_from_key("models_not_found_hint"),
                    meta={"action": "models", "input": {"query": query}},
                )
                return

            result = llm_manager.update_model_with_api_key(name, api_key)
            if result:
                result_manager.add_result(
                    content=f"models_activated: {name}",
                    meta={"action": "models", "input": {"query": query}},
                )
                printer.print_in_terminal("models_added", style="green", name=name)

                # 检查 model 配置是否存在（合并视图：全局+项目），如果不存在则自动设置为刚激活的模型
                if not memory_manager.has_config("model", source="merged"):
                    memory_manager.set_config("model", name)
                    printer.print_in_terminal(
                        "models_auto_set_model", style="cyan", name=name
                    )
            else:
                result_manager.add_result(
                    content=f"models_activate_failed: {name}",
                    meta={"action": "models", "input": {"query": query}},
                )
                printer.print_in_terminal("models_add_failed", style="red", name=name)
        else:
            # 参数不足时的错误提示
            printer.print_in_terminal("models_activate_usage", style="red")
            printer.print_in_terminal("models_activate_example", style="yellow")
            printer.print_in_terminal("models_activate_list_hint", style="yellow")

            result_manager.add_result(
                content=printer.get_message_from_key("models_activate_usage")
                + "\n"
                + printer.get_message_from_key("models_activate_example")
                + printer.get_message_from_key("models_activate_list_hint"),
                meta={"action": "models", "input": {"query": query}},
            )

    elif subcmd == "/add_provider":
        # Parse key=value pairs: /models /add_model name=abc base_url=http://xx ...
        # Collect key=value pairs
        kv_pairs = shlex.split(query)
        data_dict = {}
        for pair in kv_pairs:
            if "=" not in pair:
                printer.print_in_terminal("models_add_model_params", style="red")
                continue
            k, v = pair.split("=", 1)
            data_dict[k.strip()] = v.strip()

        # Name is required
        if "name" not in data_dict:
            printer.print_in_terminal("models_add_model_name_required", style="red")
            return

        # Check duplication
        if llm_manager.check_model_exists(data_dict["name"]):
            printer.print_in_terminal(
                "models_add_model_exists", style="yellow", name=data_dict["name"]
            )
            result_manager.add_result(
                content=printer.get_message_from_key_with_format(
                    "models_add_model_exists", name=data_dict["name"]
                ),
                meta={"action": "models", "input": {"query": query}},
            )
            return

        # Create model with defaults
        final_model = {
            "name": data_dict["name"],
            "model_type": data_dict.get("model_type", "saas/openai"),
            "model_name": data_dict.get("model_name", data_dict["name"]),
            "base_url": data_dict.get("base_url", "https://api.openai.com/v1"),
            "provider": data_dict.get("provider", None),
            "api_key_path": data_dict.get("api_key_path", ""),
            "description": data_dict.get("description", ""),
            "is_reasoning": data_dict.get("is_reasoning", "false")
            in ["true", "True", "TRUE", "1"],
            "input_price": float(data_dict.get("input_price", "0.0")),
            "output_price": float(data_dict.get("output_price", "0.0")),
            "context_window": int(data_dict.get("context_window", "32768")),
            "max_output_tokens": int(data_dict.get("max_output_tokens", "8096")),
        }

        # Add API key if provided
        if "api_key" in data_dict:
            final_model["api_key"] = data_dict["api_key"]

        llm_manager.add_models([final_model])
        printer.print_in_terminal(
            "models_add_model_success", style="green", name=data_dict["name"]
        )
        result_manager.add_result(
            content=f"models_add_model_success: {data_dict['name']}",
            meta={"action": "models", "input": {"query": query}},
        )

    elif subcmd == "/remove":
        args = query.strip().split(" ")
        if len(args) < 1:
            printer.print_in_terminal("models_remove_usage", style="red")
            result_manager.add_result(
                content=printer.get_message_from_key("models_remove_usage"),
                meta={"action": "models", "input": {"query": query}},
            )
            return
        name = args[0]
        if not llm_manager.check_model_exists(name):
            printer.print_in_terminal(
                "models_add_model_remove", style="yellow", name=name
            )
            result_manager.add_result(
                content=printer.get_message_from_key_with_format(
                    "models_add_model_remove", name=name
                ),
                meta={"action": "models", "input": {"query": query}},
            )
            return

        # 尝试删除模型
        if llm_manager.remove_model(name):
            printer.print_in_terminal(
                "models_add_model_removed", style="green", name=name
            )
            result_manager.add_result(
                content=printer.get_message_from_key_with_format(
                    "models_add_model_removed", name=name
                ),
                meta={"action": "models", "input": {"query": query}},
            )
        else:
            # 删除失败，可能是默认模型
            printer.print_in_terminal("models_remove_failed", style="red", name=name)
            result_manager.add_result(
                content=f"Failed to remove model: {name}. Cannot remove default models.",
                meta={"action": "models", "input": {"query": query}},
            )

    elif subcmd == "/chat":
        if not query.strip():
            printer.print_in_terminal(
                "Please provide content in format: <model_name> <question>",
                style="yellow",
            )
            result_manager.add_result(
                content="Please provide content in format: <model_name> <question>",
                meta={"action": "models", "input": {"query": query}},
            )
            return

        # 分离模型名称和用户问题
        parts = query.strip().split(" ", 1)  # 只在第一个空格处分割
        if len(parts) < 2:
            printer.print_in_terminal(
                "Correct format should be: <model_name> <question>, where question can contain spaces",
                style="yellow",
            )
            result_manager.add_result(
                content="Correct format should be: <model_name> <question>, where question can contain spaces",
                meta={"action": "models", "input": {"query": query}},
            )
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
                return {}  # type: ignore

            # Support custom llm_config parameters using stream_chat_oai
            result = llm.stream_chat_oai(
                conversations=[{"role": "user", "content": user_question}],
                delta_mode=True,
            )

            output_text = ""
            in_thinking = False
            for chunk in result:
                reasoning_content = (
                    chunk[1].reasoning_content if chunk[1].reasoning_content else ""
                )
                content = chunk[0] if chunk[0] else ""

                if reasoning_content:
                    if not in_thinking:
                        print("<inner_thinking>", end="", flush=True)
                        output_text += "<inner_thinking>"
                        in_thinking = True
                    print(reasoning_content, end="", flush=True)
                    output_text += reasoning_content

                if content:
                    if in_thinking:
                        print("</inner_thinking>", end="", flush=True)
                        output_text += "</inner_thinking>"
                        in_thinking = False
                    print(content, end="", flush=True)
                    output_text += content

            if in_thinking:
                print("</inner_thinking>", end="", flush=True)
                output_text += "</inner_thinking>\n"

            print("\n")

            # Print the result

            result_manager.add_result(
                content=output_text,
                meta={"action": "models", "input": {"query": query}},
            )
        except Exception as e:
            error_message = f"Error chating with model: {str(e)}"
            printer.print_str_in_terminal(error_message, style="red")
            result_manager.add_result(
                content=error_message,
                meta={"action": "models", "input": {"query": query}},
            )
    else:
        printer.print_in_terminal(
            "models_unknown_subcmd", style="yellow", subcmd=subcmd
        )
        result_manager.add_result(
            content=printer.get_message_from_key_with_format(
                "models_unknown_subcmd", subcmd=subcmd
            ),
            meta={"action": "models", "input": {"query": query}},
        )
