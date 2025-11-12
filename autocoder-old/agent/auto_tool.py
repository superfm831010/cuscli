from autocoder.pyproject import PyProject
from autocoder.tsproject import TSProject
from autocoder.suffixproject import SuffixProject
from autocoder.common import AutoCoderArgs
from autocoder.common.interpreter import Interpreter
from autocoder.common import ExecuteSteps, ExecuteStep, detect_env
from autocoder.common import code_auto_execute
from loguru import logger
import os
import io
import byzerllm
import yaml
import json
import sys
from contextlib import contextmanager
from pydantic import BaseModel
from byzerllm.types import Bool, ImagePath
from byzerllm.utils.client import code_utils
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown


class ClickPosition(BaseModel):
    left_top_x: int
    left_top_y: int
    right_bottom_x: int
    right_bottom_y: int

    def __str__(self):
        return f"left_top_x: {self.left_top_x}, left_top_y: {self.left_top_y}, right_bottom_x: {self.right_bottom_x}, right_bottom_y: {self.right_bottom_y}"


@contextmanager
def redirect_stdout():
    original_stdout = sys.stdout
    sys.stdout = f = io.StringIO()
    try:
        yield f
    finally:
        sys.stdout = original_stdout


@byzerllm.prompt()
def context() -> str:
    """
    你坚定的相信，一切任务都可以编写  Python 代码来解决。我么会也提供了一个相应的执行代码的工具，你可以使用这个工具来执行你的代码。
    你的目标是协助用户执行各种任务，包括但不限于代码生成、修改、测试等。请仔细阅读以下信息，以便更好地完成任务。

    你当前运行的环境信息:

    操作系统: {{ env_info.os_name }} {{ env_info.os_version }}
    Python版本: {{ env_info.python_version }}
    {%- if env_info.conda_env %}
    Conda环境: {{ env_info.conda_env }}
    {%- endif %}
    {%- if env_info.virtualenv %}
    虚拟环境: {{ env_info.virtualenv }}
    {%- endif %}
    {%- if env_info.has_bash %}
    支持Bash
    {%- else %}
    不支持Bash
    {%- endif %}

    {{ project_map }}

    下面是三个核心的工具，其他工具会在其他地方介绍：

    1. run_python_code(code: str) -> str
       - 运行指定的Python代码。
       - 返回代码的标准输出或错误信息。
       - 使用时需指定项目根目录。

    2. run_shell_code(script: str) -> str
       - 运行指定的Shell代码，用于编译、运行、测试等任务。
       - 返回代码的输出或错误信息。
       - 注意：不允许执行任何包含rm命令的脚本。

    3. see_screen_and_do_something_by_generate_python_code(query: str) -> ClickPosition
         - 当前要针对屏幕做的操作描述


    你总是尝试去通过编码来解决问题，并且发挥自己的想象力，逆流而上，锲而不舍。

    特别注意：

    1. 不允许自己python库
    2. 不允许有任何删除文件或目录的操作
    3. 尽量使用 Python 代码来解决问题而不是 Shell 脚本
    4. 所有对外部环境的操作都需要 pyautogui 的最新版本来实现。
    5. 你写的代码尽量要保持合理的输出，方便后续你能正确的观察这个带阿米是不是已经达成了目标。
    6. 在使用具体软件的时候，总是要先通过click来聚焦该软件，否则你可能会意外的操作到其他软件。
    """
    return {"env_info": detect_env()}


@byzerllm.prompt()
def detect_rm_command(command: str) -> Bool:
    """
    给定如下shell脚本：

    ```shell
    {{ command }}
    ```

    如果该脚本中包含删除目录或者文件的命令，请返回True，否则返回False。
    """


def get_tools(args: AutoCoderArgs, llm: byzerllm.ByzerLLM):
    def run_python_code(code: str) -> str:
        """
        你可以通过该工具运行指定的Python代码。
        输入参数 code: Python代码
        返回值是Python代码的sys output 或者 sys error 信息。

        通常你需要在代码中指定项目的根目录（前面我们已经提到了）。
        """
        interpreter = Interpreter(cwd=args.source_dir)
        s = ""
        try:
            s = interpreter.execute_steps(
                ExecuteSteps(steps=[ExecuteStep(lang="python", code=code)])
            )
        finally:
            interpreter.close()

        return s

    def run_shell_code(script: str) -> str:
        """
        你可以通过该工具运行指定的Shell代码。主要用于一些编译，运行，测试等任务。
        输入参数 script: Shell代码
        返回值是Shell代码的output 或者 error 信息。
        """

        if detect_rm_command.with_llm(llm).run(script).value:
            return "The script contains rm command, which is not allowed."

        interpreter = Interpreter(cwd=args.source_dir)
        s = ""
        try:
            s = interpreter.execute_steps(
                ExecuteSteps(steps=[ExecuteStep(lang="shell", code=script)])
            )
        finally:
            interpreter.close()

        return s

    def see_screen_and_do_something_by_generate_python_code(action_desc: str):
        """
        该工具可以帮助你查看当前屏幕截图，并且根据下一步需要做的操作来使用 pyautogui 生成操作电脑的 Python 代码。
        输入参数 action_desc: 下一步需要做的操作描述，比如在哪个地方点击某个按钮、在哪个app输入某个文字等。
        """
        @byzerllm.prompt()
        def analyze_screen_and_generate_code(
            image: ImagePath, action_desc: str, previous_result: str, attempt: int
        ) -> str:
            """
            {{ image }}
            
            目标操作：{{ action_desc }}
            
            {% if previous_result %}
            前一次尝试的代码和结果：
            ```
            {{ previous_result }}
            ```
            {% endif %}
            
            当前是第 {{ attempt }} 次尝试。
            
            请根据以下指南生成或修改 Python 代码：
            
            1. 仔细分析屏幕截图，识别相关的UI元素（如按钮、输入框、菜单等）。
            2. 根据目标操作和UI元素，使用 pyautogui 库生成相应的 Python 代码。
            3. 代码应包含必要的错误处理和验证步骤。
            4. 如果是修改前一次的代码，请解释修改原因。
            5. 输出应只包含一个代码块，使用 ```python ``` 标签包裹。
            
            注意事项：
            - 始终先聚焦目标软件，再进行操作。            
            - 添加适当的延时（pyautogui.sleep()）以确保操作的稳定性。
            - 使用 try-except 块处理可能的异常。
            - 在关键步骤后添加验证，确认操作是否成功。
            - 如果操作成功，清晰地指出成功信息。
            - 如果操作失败或需要进一步尝试，提供明确的失败原因和建议。
            - 务必不要做什么假设，而是基于屏幕截图的实际情况来编写代码,你的代码会被无任何修改直接运行。
            
            如果您认为已经达成目标或无法继续尝试，请不要生成代码，而是提供一个总结说明。
            """
        
        import pyautogui
        import tempfile
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        
        console = Console()
        vl_model = llm.get_sub_client("vl_model")
        
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_filename = temp_file.name
                screenshot.save(temp_filename)
            
            try:
                # 使用临时文件路径创建 ImagePath 对象
                image_path = ImagePath(value=temp_filename)
                
                # 生成或修改代码
                result = analyze_screen_and_generate_code.with_llm(vl_model).run(
                    image_path, action_desc, result if attempt > 1 else "", attempt
                )
                
                console.print(Panel(Markdown(result), title=f"模型输出 (尝试 {attempt})", border_style="green"))
                
                # 提取并执行代码
                codes = code_utils.extract_code(result)
                if not codes:
                    # 如果没有生成代码，可能是任务完成或无法继续
                    return result
                
                code = codes[0][1]
                execution_result = run_python_code(code)
                
                console.print(Panel(execution_result, title=f"代码执行结果 (尝试 {attempt})", border_style="yellow"))
                
                # 更新结果，包含代码和执行结果
                result = execution_result
            
                
                # 检查是否成功完成任务
                if "成功" in execution_result.lower():
                    console.print("[bold green]任务成功完成！[/bold green]")
                    return result
            
            finally:
                # 删除临时文件
                os.unlink(temp_filename)
        
        console.print("[bold red]达到最大尝试次数，任务未能完成。[/bold red]")
        return result
        
    from llama_index.core.tools import FunctionTool

    tools = [
        FunctionTool.from_defaults(run_python_code),
        FunctionTool.from_defaults(run_shell_code),
        FunctionTool.from_defaults(see_screen_and_do_something_by_generate_python_code),
    ]
    return tools


class AutoTool:
    def __init__(self, args: AutoCoderArgs, llm: byzerllm.ByzerLLM):
        self.llm = llm
        self.code_model = (
            self.llm.get_sub_client("code_model") if args.code_model else self.llm
        )
        self.vl_model = (
            self.llm.get_sub_client("vl_model") if args.vl_model else self.llm
        )
        self.args = args
        self.tools = get_tools(args=args, llm=llm)
        if self.args.project_type == "ts":
            self.pp = TSProject(args=self.args, llm=llm)
        elif self.args.project_type == "py":
            self.pp = PyProject(args=self.args, llm=llm)
        else:
            self.pp = SuffixProject(args=self.args, llm=self.llm, file_filter=None)

    def get_tree_like_directory_structure(self) -> str:
        self.pp.run()
        return self.pp.get_tree_like_directory_structure.prompt()

    def run(self, query: str, max_iterations: int = 20):
        from byzerllm.apps.llama_index.byzerai import ByzerAI
        from llama_index.core.agent import ReActAgent
        from autocoder.utils.rolling_display import rolling_progress

        agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=ByzerAI(llm=self.code_model),
            verbose=True,
            max_iterations=max_iterations,
            context=context.prompt(),
        )

        # 使用滚动显示来展示 agent 的思考过程
        with rolling_progress(max_lines=5, title="🤖 Agent 正在思考和执行任务..."):
            r = agent.chat(message=query)

        # 显示完成摘要
        console = Console()
        console.print("\n")
        console.print(Panel(
            r.response[:500] + ("..." if len(r.response) > 500 else ""),
            title="✅ 任务完成",
            border_style="green",
            padding=(1, 2)
        ))

        # print("\n\n=============EXECUTE==================")
        # executor = code_auto_execute.CodeAutoExecute(
        #     self.llm, self.args, code_auto_execute.Mode.SINGLE_ROUND
        # )
        # executor.run(query=query, context=r.response, source_code="")

        return r.response
