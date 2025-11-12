"""系统初始化模块"""

import subprocess
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.formatted_text import HTML
from autocoder.chat_auto_coder_lang import get_message


def initialize_system(args):
    """初始化系统环境（Ray、模型等）"""
    if args.product_mode == "lite":
        return

    print(f"\n\033[1;34m{get_message('initializing')}\033[0m")

    def print_status(message, status):
        if status == "success":
            print(f"\033[32m✓ {message}\033[0m")
        elif status == "warning":
            print(f"\033[33m! {message}\033[0m")
        elif status == "error":
            print(f"\033[31m✗ {message}\033[0m")
        else:
            print(f"  {message}")

    # Check if Ray is running
    print_status(get_message("checking_ray"), "")
    ray_status = subprocess.run(["ray", "status"], capture_output=True, text=True)
    if ray_status.returncode != 0:
        print_status(get_message("ray_not_running"), "warning")
        try:
            subprocess.run(["ray", "start", "--head"], check=True)
            print_status(get_message("ray_start_success"), "success")
        except subprocess.CalledProcessError:
            print_status(get_message("ray_start_fail"), "error")
            return
    else:
        print_status(get_message("ray_running"), "success")

    # Check if deepseek_chat model is available
    print_status(get_message("checking_model"), "")
    try:
        result = subprocess.run(
            ["easy-byzerllm", "chat", "v3_chat", "你好"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print_status(get_message("model_available"), "success")
            print_status(get_message("init_complete_final"), "success")
            return
    except subprocess.TimeoutExpired:
        print_status(get_message("model_timeout"), "error")
    except subprocess.CalledProcessError:
        print_status(get_message("model_error"), "error")

    # If deepseek_chat is not available, prompt user to choose a provider
    print_status(get_message("model_not_available"), "warning")
    choice = radiolist_dialog(
        title=get_message("provider_selection"),
        text=get_message("provider_selection"),
        values=[
            ("1", "Deepseek官方(https://www.deepseek.com/)"),
        ],
    ).run()

    if choice is None:
        print_status(get_message("no_provider"), "error")
        return

    api_key = prompt(HTML(f"<b>{get_message('enter_api_key')} </b>"))

    if choice == "1":
        print_status(get_message("deploying_model").format("Deepseek官方"), "")

        deploy_cmd = [
            "byzerllm",
            "deploy",
            "--pretrained_model_type",
            "saas/openai",
            "--cpus_per_worker",
            "0.001",
            "--gpus_per_worker",
            "0",
            "--worker_concurrency",
            "1000",
            "--num_workers",
            "1",
            "--infer_params",
            f"saas.base_url=https://api.deepseek.com/v1 saas.api_key={api_key} saas.model=deepseek-chat",
            "--model",
            "v3_chat",
        ]

    try:
        subprocess.run(deploy_cmd, check=True)
        print_status(get_message("deploy_complete"), "success")
    except subprocess.CalledProcessError:
        print_status(get_message("deploy_fail"), "error")
        return

    # Validate the deployment
    print_status(get_message("validating_deploy"), "")
    try:
        validation_result = subprocess.run(
            ["easy-byzerllm", "chat", "v3_chat", "你好"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        print_status(get_message("validation_success"), "success")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print_status(get_message("validation_fail"), "error")
        print_status(get_message("manual_start"), "warning")
        print_status("easy-byzerllm chat v3_chat 你好", "")

    print_status(get_message("init_complete_final"), "success")
