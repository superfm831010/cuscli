from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from typing import Optional, Dict, Any, List
from autocoder.common.printer import Printer
import re
from pydantic import BaseModel

from autocoder.common.llms import LLMManager
from autocoder.common.llms.connection_test import ModelConnectionTester

class ProviderInfo(BaseModel):
    name: str
    endpoint: str
    r1_model: str
    v3_model: str
    api_key: str
    r1_input_price: float
    r1_output_price: float
    v3_input_price: float
    v3_output_price: float    


PROVIDER_INFO_LIST = [
    ProviderInfo(
        name="volcano",
        endpoint="https://ark.cn-beijing.volces.com/api/v3",   
        r1_model="deepseek-r1-250120",
        v3_model="deepseek-v3-250324",
        api_key="",
        r1_input_price=2.0,
        r1_output_price=8.0,
        v3_input_price=1.0,
        v3_output_price=4.0,
    ), 
    ProviderInfo(
        name="siliconflow",
        endpoint="https://api.siliconflow.cn/v1",        
        r1_model="Pro/deepseek-ai/DeepSeek-R1",
        v3_model="Pro/deepseek-ai/DeepSeek-V3",
        api_key="",
        r1_input_price=2.0,
        r1_output_price=4.0,
        v3_input_price=4.0,
        v3_output_price=16.0,
    ),
    ProviderInfo(
        name="deepseek",
        endpoint="https://api.deepseek.com/v1",
        r1_model="deepseek-reasoner",
        v3_model="deepseek-chat",
        api_key="",
        r1_input_price=4.0,
        r1_output_price=16.0,
        v3_input_price=2.0,
        v3_output_price=8.0,
    ),
    ProviderInfo(
        name="openrouter",
        endpoint="https://openrouter.ai/api/v1",
        r1_model="deepseek/deepseek-r1",
        v3_model="deepseek/deepseek-chat-v3-0324",
        api_key="",
        r1_input_price=0.0,
        r1_output_price=0.0,
        v3_input_price=0.0,
        v3_output_price=0.0,
    )
]

dialog_style = Style.from_dict({
            'dialog':                'bg:#2b2b2b',
            'dialog frame.label':    'bg:#2b2b2b #ffffff',
            'dialog.body':          'bg:#2b2b2b #ffffff',
            'dialog shadow':        'bg:#1f1f1f',
            'button':               'bg:#2b2b2b #808080',
            'button.focused':       'bg:#1e1e1e #ffd700 bold',
            'checkbox':             '#e6e6e6',
            'checkbox-selected':    '#0078d4',
            'radio-selected':       'bg:#0078d4 #ffffff',
            'dialog frame.border':  '#0078d4',
            'radio':                'bg:#2b2b2b #808080',
            'radio.focused':        'bg:#1e1e1e #ffd700 bold'
        })

class VolcanoEndpointValidator(Validator):
    def validate(self, document):
        text = document.text
        pattern = r'^ep-\d{14}-[a-z0-9]{5}$'
        if not re.match(pattern, text):
            raise ValidationError(
                message='Invalid endpoint format. Should be like: ep-20250204215011-vzbsg',
                cursor_position=len(text)
            )

class ModelProviderSelector:
    def __init__(self):
        self.printer = Printer()
        self.console = Console()
        self.llm_manager = LLMManager()

    def to_models_json(self, provider_info: ProviderInfo) -> List[Dict[str, Any]]:
        """
        Convert provider info to models.json format.
        Returns a list of model configurations matching the format in models.py default_models_list.
        
        Args:
            provider_info: ProviderInfo object containing provider details
            
        Returns:
            List[Dict[str, Any]]: List of model configurations
        """
        models = []
        
        # Add R1 model (for reasoning/design/review)
        if provider_info.r1_model:
            models.append({
                "name": f"r1_chat",
                "description": f"{provider_info.name} R1 is for design/review",
                "model_name": provider_info.r1_model,
                "model_type": "saas/openai",
                "base_url": provider_info.endpoint,
                "api_key": provider_info.api_key,
                "api_key_path": f"r1_chat",
                "is_reasoning": True,
                "input_price": provider_info.r1_input_price,
                "output_price": provider_info.r1_output_price,
                "average_speed": 0.0,
                "context_window": 32768,
                "max_output_tokens": 8096
            })
            
        # Add V3 model (for coding)
        if provider_info.v3_model:
            models.append({
                "name": f"v3_chat",
                "description": f"{provider_info.name} Chat is for coding",
                "model_name": provider_info.v3_model,
                "model_type": "saas/openai",
                "base_url": provider_info.endpoint,
                "api_key": provider_info.api_key,
                "api_key_path": f"v3_chat",
                "is_reasoning": False,
                "input_price": provider_info.v3_input_price,
                "output_price": provider_info.v3_output_price,
                "average_speed": 0.0,
                "context_window": 32768,
                "max_output_tokens": 8096
            })
            
        return models
        
    def select_provider(self) -> Optional[Dict[str, Any]]:
        """
        Let user select a model provider and input necessary credentials.
        Returns a dictionary with provider info or None if cancelled.
        """
        

        result = radiolist_dialog(
            title=self.printer.get_message_from_key("model_provider_select_title"),
            text=self.printer.get_message_from_key("model_provider_select_text"),
            values=[
                ("volcano", self.printer.get_message_from_key("model_provider_volcano")),
                ("siliconflow", self.printer.get_message_from_key("model_provider_siliconflow")),
                ("deepseek", self.printer.get_message_from_key("model_provider_deepseek")),
                ("openrouter", self.printer.get_message_from_key("model_provider_openrouter"))
            ],
            style=dialog_style
        ).run()
        
        if result is None:
            return None

    
        provider_info = None
        for provider in PROVIDER_INFO_LIST:
            if provider.name == result:
                provider_info = provider
                break
        
        if provider_info is None:
            return None
        
        # if result == "volcano":
        #     # Get R1 endpoint
        #     r1_endpoint = input_dialog(
        #         title=self.printer.get_message_from_key("model_provider_api_key_title"),
        #         text=self.printer.get_message_from_key("model_provider_volcano_r1_text"),
        #         validator=VolcanoEndpointValidator(),
        #         style=dialog_style
        #     ).run()
            
        #     if r1_endpoint is None:
        #         return None
            
        #     provider_info.r1_model = r1_endpoint
            
        #     # Get V3 endpoint
        #     v3_endpoint = input_dialog(
        #         title=self.printer.get_message_from_key("model_provider_api_key_title"),
        #         text=self.printer.get_message_from_key("model_provider_volcano_v3_text"),
        #         validator=VolcanoEndpointValidator(),
        #         style=dialog_style
        #     ).run()
            
        #     if v3_endpoint is None:
        #         return None
                
        #     provider_info.v3_model = v3_endpoint
        
        # Get API key for all providers
        api_key = input_dialog(
            title=self.printer.get_message_from_key("model_provider_api_key_title"),
            text=self.printer.get_message_from_key(f"model_provider_{result}_api_key_text"),
            password=True,
            style=dialog_style
        ).run()
        
        if api_key is None:
            return None
            
        provider_info.api_key = api_key

        # 使用新的 LLMManager 添加模型
        models_to_add = self.to_models_json(provider_info)

        # 测试连接（测试第一个模型即可，通常是 v3_chat）
        if models_to_add:
            test_result = self._test_provider_connection(models_to_add[0])
            if not test_result:
                # 测试失败，用户选择取消
                return None

        self.llm_manager.add_models(models_to_add)  # type: ignore

        self.printer.print_panel(
            self.printer.get_message_from_key("model_provider_selected"),
            text_options={"justify": "left"},
            panel_options={
                "title": self.printer.get_message_from_key("model_provider_success_title"),
                "border_style": "green"
            }
        )

        return provider_info.dict()

    def _test_provider_connection(self, model_config: Dict[str, Any]) -> bool:
        """
        测试提供商连接

        Args:
            model_config: 模型配置字典

        Returns:
            bool: 是否继续（True=继续保存，False=取消）
        """
        self.console.print("\n")
        self.console.print(Panel(
            "[bold cyan]测试模型连接[/bold cyan]\n\n"
            f"正在测试模型 [bold]{model_config['name']}[/bold] 的连接...",
            border_style="cyan"
        ))

        # 执行连接测试
        tester = ModelConnectionTester(self.console)
        success, message = tester.test_connection(model_config, product_mode="lite", show_progress=True)

        self.console.print()

        if success:
            # 测试成功
            self.console.print(Panel(
                f"[bold green]✓ 连接测试成功！[/bold green]\n\n{message}",
                border_style="green",
                title="测试通过"
            ))
            return True
        else:
            # 测试失败
            self.console.print(Panel(
                f"[bold red]✗ 连接测试失败[/bold red]\n\n[yellow]错误信息：[/yellow]\n{message}\n\n"
                "[dim]可能的原因：[/dim]\n"
                "  • API Key 不正确\n"
                "  • API 地址错误\n"
                "  • 模型名称不存在\n"
                "  • 网络连接问题",
                border_style="red",
                title="测试失败"
            ))

            # 询问用户是否继续
            continue_anyway = Confirm.ask(
                "\n是否忽略测试失败，继续保存配置？",
                default=False
            )

            if continue_anyway:
                self.console.print("[yellow]⚠️  已忽略连接测试，继续保存配置[/yellow]")
                return True
            else:
                self.console.print("[yellow]已取消配置[/yellow]")
                return False