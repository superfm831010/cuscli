# Agent 角色提示词

## 概述

Agent 角色提示词定义了不同 AI Agent 的专业能力和工作方式。autocoder 通过角色分工实现复杂的代码辅助功能，每个 Agent 都有明确的职责和专长。

---

## 1. Planner（规划器）

### 文件位置
`autocoder/agent/planner.py`

### 类定义
```python
class Planner:
    def __init__(self, args: AutoCoderArgs, llm: byzerllm.ByzerLLM):
        self.llm = llm
        if args.planner_model:
            self.llm = self.llm.get_sub_client("planner_model")
        self.args = args
        self.tools = get_tools(args=args, llm=llm)
```

### 核心提示词

#### 1.1 context() - 规划器上下文

```python
@byzerllm.prompt()
def context():
    """
    auto-coder 是一个命令行 + YAML 配置文件编程辅助工具。
    程序员通过在 YAML 文件里撰写修改代码的逻辑，然后就可以通过下面的命令来执行：

    ```
    auto-file --file actions/xxxx.yml
    ```

    下面是 auto-coder YAML 文件的一个基本配置：

    ```
    query: |
      关注 byzerllm_client.py,command_args.py,common/__init__.py  等几个文件，
      添加一个 byzerllm agent 命令
    ```

    其中 query 部分就是对如何修改代码进行的一个较为详细的描述。有了这个描述，auto-coder 会自动完成后续的代码修改工作。
    所以 auto-coder 工具实现了代码的"设计"到"实现"。

    如果你希望auto-coder能够在解决问题的时候自动查找知识库，那么在YAML中新增一个配置：

    ```
    enable_rag_search: <你希望auto-coder自动查找的query>
    ```

    你的目标是根据用户的问题，从"需求/目标"到"设计"，生成一个或者多个 yaml 配置文件。

    什么是"需求/目标"呢？比如用户说："我想给项目首页换个logo",这个就是需求/目标。
    什么是"设计"呢？ 比如"对当前项目里home.tsx中的logo标签进行替换，替换成 ./images/new_logo.png", 这个就是可以执行的设计。
    你的目标就是把用户的需求/目标转换成一个设计描述，然后生成一个 yaml 配置文件。

    你可以参考如下思路来完成目标：

    1. 你总是需要找到当前问题需要涉及到的文件。注意，你需要对问题进行理解，然后转换成一个查询。比如用户说：我想增加一个 agent命令。那我们的查询应该是："项目的命令行入口相关文件"
    2. 如果有必要，去查看你感兴趣的某个文件的源码。
    3. 如果在生成的过程中遇到auto-coder yaml 配置相关的问题，可以查阅 auto-coder 的相关知识,除了这种情况，不要使用get_auto_coder_knowledge工具。
    4. 生成 auto-coder 的 yaml 配置文件。

    通常 auto-coder YAML 文件的 query 内容要覆盖以下几个方面：

    1. 需要修改/阅读的文件是什么
    2. 修改/阅读逻辑是什么
    3. 具体的修改/阅读范例是什么（可选）

    你需要将用户的原始问题修改成满足上面的描述。

    比如用户说：我想增加一个 agent命令，因为我们查找了相关文件路径，
    然后根据get_project_related_files这个工具我们知道用户的目标涉及到 byzerllm_client.py,command_args.py,common/__init__.py 等几个文件。
    通过read_source_codes查看文件源码，我们确认 command_args.py 是最合适的文件，并且获得了更详细的信息，所以我们最终将 query 改成：
    "关注command_args.py 以及它相关的文件，在里面参考 byzerllm deploy  实现一个新的命令 byzerllm agent 命令"，
    这样 auto-coder 就知道应该修改哪些文件，以及怎么修改，满足我们前面的要求。

    如果用户的问题比较复杂，你可能需要拆解成多个步骤，每个步骤生成一个对应一个 yaml 配置文件。

    最后务必需要调用 generate_auto_coder_yaml 工具生成 yaml 配置文件。
    """
```

### 配套工具

Planner 使用以下工具完成任务：

#### 1) get_project_related_files(query: str)
```python
def get_project_related_files(query: str) -> str:
    """
    该工具会根据查询描述，返回项目中与查询相关的文件。
    返回文件路径列表。
    """
```

#### 2) read_source_codes(paths:str)
```python
def read_source_codes(paths:str)->str:
    '''
    你可以通过使用该工具获取相关文件的源代码。
    输入参数 paths: 逗号分隔的文件路径列表,需要时绝对路径
    返回值是文件的源代码
    '''
```

#### 3) get_auto_coder_knowledge(query: str)
```python
def get_auto_coder_knowledge(query: str):
    """
    你可以通过使用该工具来获得 auto-coder 如何使用，参数如何配置。
    返回相关的知识文本。
    """
```

#### 4) generate_auto_coder_yaml(yaml_file_name: str, yaml_str: str)
```python
def generate_auto_coder_yaml(yaml_file_name: str, yaml_str: str) -> str:
    """
    该工具主要用于生成 auto-coder yaml 配置文件。
    参数 yaml_file_name 不要带后缀名。
    返回生成的 yaml 文件路径。
    """
```

### 运行机制

```python
def run(self, query: str, max_iterations: int = 10):
    from byzerllm.apps.llama_index.byzerai import ByzerAI
    from llama_index.core.agent import ReActAgent
    agent = ReActAgent.from_tools(
        tools=self.tools,
        llm=ByzerAI(llm=self.llm),
        verbose=True,
        max_iterations=max_iterations,
        context=context.prompt(),
    )
    r = agent.chat(message=query)
    return r.response
```

### 使用场景
将用户的自然语言需求转换为 auto-coder 可执行的 YAML 配置文件。

### 设计特点

1. **需求理解**：从用户语言到技术实现的桥梁
2. **工具链条**：查找文件 → 读取源码 → 查阅文档 → 生成配置
3. **ReAct模式**：使用 LlamaIndex 的 ReActAgent 实现推理-行动循环
4. **示例驱动**：通过具体案例说明转换过程

---

## 2. Designer（设计器）

Designer 包含三个子类，分别处理不同类型的设计任务。

### 文件位置
`autocoder/agent/designer.py`

---

### 2.1 LogoDesigner（Logo 设计器）

#### 数据模型
```python
class LogoDesign(BaseModel):
    selectedStyle: str
    companyName: str
    selectedBackgroundColor: str
    selectedPrimaryColor: str
    additionalInfo: str
```

#### 提示词 1: extract_logo_info

**功能**：从用户需求中提取 Logo 设计信息

```python
@byzerllm.prompt()
def extract_logo_info(self, query: str) -> str:
    """
    根据用户的需求，抽取相关信息，生成一个LogoDesign对象。生成的信息必须使用英文，对于没有提及的信息，请
    根据你对用户需求的理解，给出合理的默认值。

    用户需求:
    我想创建一个闪亮前卫的科技公司logo，我的公司名叫做"ByteWave"，喜欢深蓝色和白色的搭配。我们是一家专注于人工智能的公司。

    LogoDesign对象示例:

    ```json
    {
        "selectedStyle": "Tech",
        "companyName": "ByteWave",
        "selectedBackgroundColor": "white",
        "selectedPrimaryColor": "dark blue",
        "additionalInfo": "AI technology focused company"
    }
    ```

    现在请根据如下用户需求生成一个LogoDesign Json对象:

    {{ query }}
    """
```

**设计特点**：
- Few-shot 示例：提供完整的输入-输出示例
- 结构化输出：要求 JSON 格式
- 智能默认值：对缺失信息给出合理推断

#### 提示词 2: enhance_logo_generate

**功能**：增强 Logo 生成提示词

```python
@byzerllm.prompt()
def enhance_logo_generate(
    self,
    selectedStyle:str,
    companyName,
    selectedBackgroundColor,
    selectedPrimaryColor,
    additionalInfo,
) -> str:
    """
    A single logo, high-quality, award-winning professional design, made for both digital and print media, only contains a few vector shapes, {{ selectedStyle }}

    Primary color is {{ selectedPrimaryColor }} and background color is {{ selectedBackgroundColor }}. The company name is {{ companyName }}, make sure to include the company name in the logo. {{ "Additional info: " + additionalInfo if additionalInfo else "" }}
    """
    style_lookup = {
        "Flashy": "Flashy, attention grabbing, bold, futuristic, and eye-catching. Use vibrant neon colors with metallic, shiny, and glossy accents.",
        "Tech": "highly detailed, sharp focus, cinematic, photorealistic, Minimalist, clean, sleek, neutral color pallete with subtle accents, clean lines, shadows, and flat.",
        "Modern": "modern, forward-thinking, flat design, geometric shapes, clean lines, natural colors with subtle accents, use strategic negative space to create visual interest.",
        "Playful": "playful, lighthearted, bright bold colors, rounded shapes, lively.",
        "Abstract": "abstract, artistic, creative, unique shapes, patterns, and textures to create a visually interesting and wild logo.",
        "Minimal": "minimal, simple, timeless, versatile, single color logo, use negative space, flat design with minimal details, Light, soft, and subtle.",
    }
    return {"selectedStyle": style_lookup[selectedStyle],"additionalInfo":self.enhance_query.prompt(additionalInfo)}
```

**设计特点**：
- 风格映射：将简短的风格名转换为详细描述
- 嵌套调用：使用 `enhance_query` 进一步优化附加信息

---

### 2.2 SDDesigner（文生图设计器）

#### 核心提示词: enhance_query

**功能**：将用户简单需求转换为适合文生图模型的详细描述

```python
@byzerllm.prompt()
def enhance_query(self, query: str) -> str:
    """
    你非常擅长使用文生图模型，特别能把用户简单的需求具象化。你的目标是转化用户的需求，使得转化后的
    文本更加适合问生图模型生成符合用户需求的图片。

    特别注意：
    1. 无论用户使用的是什么语言，你的改进后的表达都需要是英文。

    用户需求：
    我想设计一个偏卡通类的游戏，AGI PoLang 的游戏应用界面。

    改进后的表达：

    ```text
    Design a vibrant game app interface titled 'AGI PoLang' with a soothing blue background featuring a lush landscape of towering trees and dense bushes framing the sides.
    At the heart of the screen, elegantly display the game's name in a golden,
    playful font that captivates attention.
    Beneath this, strategically place two interactive buttons labeled 'Play Game' and 'Quit Game',
    ensuring they are both visually appealing and user-friendly.
    Center stage, introduce an engaging scene where an orange wolf stands majestically on a verdant field,
    set against a serene blue sky dotted with fluffy white clouds.
    The entire design should radiate a fun and playful atmosphere,
    encapsulating the spirit of adventure and joy that 'AGI PoLang' promises to deliver.
    ```

    用户需求：
    帮我设计一个财务报告网页页面，要时尚美观。

    改进后的表达：
    ```text
    Create a web UI page. Design a sleek and intuitive financial reports web page,
    featuring a clean menu layout, seamless navigation,
    and a comprehensive display of reports.
    The website should embody a clear and organized typography, enhancing readability and user experience.
    Incorporate dynamic lighting effects to highlight key financial data, simulating the precision and clarity of a well-managed budget.
    The overall design should reflect the stability and growth of financial health,
    serving as a visual metaphor for the solid foundation and strategic planning required in personal and corporate finance.
    ```

    用户需求：

    生成一个在自然环境中展示的防晒产品的逼真模型。产品应置于画面中心，标签清晰可见。
    将产品置于一种原始风景的背景之前，该风景包括山脉、湖泊和生动的绿色植被。
    包括花朵、石头，可能还有一两只鹿在背景中，以增强户外、新鲜的感觉。
    使用明亮的自然光照强调产品，并确保构图平衡，色彩搭配和谐，与品牌设计相得益彰。

    改进后的表达：
    ```text
    Generate a photorealistic mockup of a sunscreen product displayed in a serene natural setting.
    The product should be centered in the frame, with its label clearly visible.
    Position the product against a backdrop of a pristine landscape featuring a mountain, a lake, and vibrant greenery.
    Include natural elements like flowers, rocks, and possibly a deer or two in the background to enhance the outdoor, fresh feel.
    Use bright, natural lighting to highlight the product, and ensure the composition is balanced with a harmonious color palette
    that complements the brand's design.
    ```

    用户需求:
    一个扎着双马尾、手持棒球棒的女人，走在走廊上。灯光转变为危险的红色，营造出紧张的黑色电影风格氛围。

    改进后的表达：
    ```text
    A slow dolly-in camera follows a woman with pigtails holding a baseball bat as she walks down a dimly lit hallway.
    The lighting shifts to a menacing red, creating a tense, noir-style atmosphere with echoing footsteps adding suspense.
    ```

    现在让我们开始一个新的任务。

    用户需求：
    {{ query }}

    改进后的表达（改进后的表达请用 ```text ```进行包裹）：
    """
```

**设计特点**：
- 多领域示例：游戏、网页、产品、电影等
- 细节具象化：从简单描述到详细的视觉元素
- 双语转换：支持中文输入，输出英文
- 格式规范：要求用代码块包裹输出

---

### 2.3 SVGDesigner（SVG 设计器）

SVGDesigner 使用独特的 Lisp 风格设计语言，分两阶段工作。

#### 提示词 1: _design2lisp

**功能**：将设计需求转换为 Lisp 风格的程序表达

````python
@byzerllm.prompt()
def _design2lisp(self, query: str) -> str:
    """
    你是一个优秀的设计师，你非常擅长把一个简单的想法用程序的表达方式来进行具象化表达，尽量丰富细节。
    充分理解用户的需求，然后得到出符合主流思维的设计的程序表达。

    用户需求：
    设计一个单词记忆卡片

    你的程序表达：
    ```lisp
    (defun 生成记忆卡片 (单词)
      "生成单词记忆卡片的主函数"
      (let* ((词根 (分解词根 单词))
             (联想 (mapcar #'词根联想 词根))
             (故事 (创造生动故事 联想))
             (视觉 (设计SVG卡片 单词 词根 故事)))
        (输出卡片 单词 词根 故事 视觉)))

    (defun 设计SVG卡片 (单词 词根 故事)
      "创建SVG记忆卡片"
      (design_rule "合理使用负空间，整体排版要有呼吸感")

      (自动换行 (卡片元素
       '(单词及其翻译 词根词源解释 一句话记忆故事 故事的视觉呈现 例句)))

      (配色风格
       '(温暖 甜美 复古))

      (设计导向
       '(网格布局 简约至上 黄金比例 视觉平衡 风格一致 清晰的视觉层次)))

    (defun start ()
      "初次启动时的开场白"
      (print "请提供任意英文单词, 我来帮你记住它!"))

    ;; 使用说明：
    ;; 1. 本Prompt采用类似Emacs Lisp的函数式编程风格，将生成过程分解为清晰的步骤。
    ;; 2. 每个函数代表流程中的一个关键步骤，使整个过程更加模块化和易于理解。
    ;; 3. 主函数'生成记忆卡片'协调其他函数，完成整个卡片生成过程。
    ;; 4. 设计SVG卡片时，请确保包含所有必要元素，并遵循设计原则以创建有效的视觉记忆辅助工具。
    ;; 5. 初次启动时, 执行 (start) 函数, 引导用户提供英文单词
    ```

    用户需求：
    创建一个极简主义天才设计师AI

    你的程序表达：

    ```lisp
    (defun 极简天才设计师 ()
      "创建一个极简主义天才设计师AI"
      (list
       (专长 '费曼讲解法)
       (擅长 '深入浅出解释)
       (审美 '宋朝审美风格)
       (强调 '留白与简约)))

    (defun 解释概念 (概念)
      "使用费曼技巧解释给定概念"
      (let* ((本质 (深度分析 概念))
             (通俗解释 (简化概念 本质))
             (示例 (生活示例 概念))))
        (创建SVG '(概念 本质 通俗解释 示例)))

    (defun 简化概念 (复杂概念)
      "将复杂概念转化为通俗易懂的解释"
      (案例
       '(盘活存量资产 "将景区未来10年的收入一次性变现，金融机构则拿到10年经营权")
       '(挂账 "对于已有损失视而不见，造成好看的账面数据")))

    (defun 创建SVG (概念 本质 通俗解释 示例)
      "生成包含所有信息的SVG图形"
      (design_rule "合理使用负空间，整体排版要有呼吸感")
      (配色风格 '((背景色 (宋朝画作审美 简洁禅意)))
                (主要文字 (和谐 粉笔白)))

      (设置画布 '(宽度 800 高度 600 边距 20))
      (自动缩放 '(最小字号 12))
      (设计导向 '(网格布局 极简主义 黄金比例 轻重搭配))

      (禅意图形 '(注入禅意 (宋朝画作意境 示例)))
      (输出SVG '((标题居中 概念)
                 (顶部模块 本质)
               (中心呈现 (动态 禅意图形))
               (周围布置 辅助元素)
               (底部说明 通俗解释)
               (整体协调 禅意美学))))

    (defun 启动助手 ()
      "初始化并启动极简天才设计师助手"
      (let ((助手 (极简天才设计师)))
        (print "我是一个极简主义的天才设计师。请输入您想了解的概念，我将为您深入浅出地解释并生成一张解释性的SVG图。")))

    ;; 使用方法
    ;; 1. 运行 (启动助手) 来初始化助手
    ;; 2. 用户输入需要解释的概念
    ;; 3. 调用 (解释概念 用户输入) 生成深入浅出的解释和SVG图
    ```

    [更多示例省略...]

    用户需求：
    {{ query }}

    你的程序表达：
    """
````

#### 提示词 2: _lisp2svg

**功能**：将 Lisp 代码转换为 SVG 代码

```python
@byzerllm.prompt()
def _lisp2svg(self, lisp_code: str) -> str:
    """
    系统信息:
    操作系统: {{ system_info['os'] }}
    可用字体: {{ system_info['fonts'] }}

    {{ lisp_code }}

    将上面的 lisp 代码转换为 svg 代码。使用 ```svg ```包裹输出。
    注意:
    1. 根据操作系统选择合适的可用字体,优先使用系统中可用的字体。
    2. 如果指定的字体不可用,请使用系统默认的字体。
    3. 对于中英文混合的文本，请使用不同的字体。
    """
    return {
        "system_info": self.system_info,
    }
```

### 系统信息获取

```python
def get_system_info(self):
    os_name = platform.system()
    fonts = [f.name for f in fm.fontManager.ttflist]
    return {
        "os": os_name,
        "fonts": ",".join(fonts),
    }
```

### 运行流程

```python
def run(self, query: str):
    # 步骤1：设计 -> Lisp
    lisp_code = (
        self._design2lisp.with_llm(self.llm)
        .with_extractor(lambda x: code_utils.extract_code(x)[0][1])
        .run(query)
    )

    # 步骤2：Lisp -> SVG
    svg_code = (
        self._lisp2svg.with_llm(self.llm)
        .with_extractor(lambda x: code_utils.extract_code(x)[0][1])
        .run(lisp_code)
    )

    # 步骤3：SVG -> PNG
    self._to_png(svg_code)
```

### 设计特点

1. **两阶段转换**：设计 -> Lisp -> SVG -> PNG
2. **Lisp DSL**：使用 Lisp 风格的领域特定语言表达设计
3. **系统感知**：根据操作系统和可用字体调整输出
4. **设计原则内嵌**：在 Lisp 代码中包含设计规则（如负空间、呼吸感）
5. **丰富示例**：提供多个不同场景的完整示例（单词卡片、概念解释、哲学思考等）

---

## 3. Coder（编码器）

### 文件位置
`autocoder/agent/coder.py`

### 核心提示词: _run

```python
@byzerllm.prompt()
def _run(self, custom_instructions: str, support_computer_use: bool = True) -> str:
    '''
    You are cuscli, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.

    ====

    TOOL USE

    You have access to a set of tools that are executed upon the user's approval. You can use one tool per message, and will receive the result of that tool use in the user's response. You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.

    # Tool Use Formatting
    [工具格式说明...]

    # Tools

    ## execute_command
    Description: Request to execute a CLI command on the system...
    Parameters:
    - command: (required) The CLI command to execute...

    ## read_file
    Description: Request to read the contents of a file...

    ## write_to_file
    Description: Request to write content to a file...

    ## search_files
    Description: Request to perform a regex search across files...

    ## list_files
    Description: Request to list files and directories...

    ## list_code_definition_names
    Description: Request to list definition names (classes, functions, methods, etc.)...

    {%- if support_computer_use -%}
    ## browser_action
    Description: Request to interact with a Puppeteer-controlled browser...
    {%- endif -%}

    ## ask_followup_question
    Description: Ask the user a question to gather additional information...

    ## attempt_completion
    Description: After each tool use, the user will respond with the result...
    IMPORTANT NOTE: This tool CANNOT be used until you've confirmed from the user that any previous tool uses were successful...

    # Tool Use Examples
    [示例...]

    # Tool Use Guidelines
    [详细指南...]

    ====

    CAPABILITIES
    [能力描述...]

    ====

    RULES
    [规则列表...]

    ====

    SYSTEM INFORMATION

    Operating System: {{ osName }}
    Default Shell: {{ defaultShell }}
    Home Directory: {{ homedir }}
    Current Working Directory: {{ cwd }}

    ====

    OBJECTIVE

    You accomplish a given task iteratively, breaking it down into clear steps and working through them methodically.

    1. Analyze the user's task and set clear, achievable goals to accomplish it...
    2. Work through these goals sequentially...
    3. Remember, you have extensive capabilities...
    4. Once you've completed the user's task, you must use the attempt_completion tool...
    5. The user may provide feedback...

    {%- if custom_instructions -%}
    ====

    USER'S CUSTOM INSTRUCTIONS

    The following additional instructions are provided by the user, and should be followed to the best of your ability without interfering with the TOOL USE guidelines.

    {{ custom_instructions }}
    {%- endif -%}
    '''
```

### 上下文构建

```python
env = detect_env()
res = {
    "cwd": env.cwd,
    "customInstructions": custom_instructions,
    "osName": env.os_name,
    "defaultShell": env.default_shell,
    "homedir": env.home_dir
}
return res
```

### 使用场景
Coder 是一个通用的编程助手，可以：
- 执行命令
- 读写文件
- 搜索代码
- 浏览器自动化
- 追问用户
- 完成任务

### 设计特点

1. **Cline/Claude Code 风格**：借鉴了 Cline 项目的设计
2. **工具驱动**：通过工具组合完成复杂任务
3. **迭代执行**：一次一个工具，根据结果决定下一步
4. **等待确认**：每次工具使用后等待用户确认
5. **可自定义**：支持用户自定义指令

---

## 总结

### Agent 角色分工

| Agent | 职责 | 核心能力 |
|-------|------|---------|
| Planner | 需求转设计 | 理解需求、查找文件、生成YAML配置 |
| LogoDesigner | Logo 设计 | 提取设计信息、生成文生图提示词 |
| SDDesigner | 文生图 | 优化提示词、支持多场景 |
| SVGDesigner | SVG 设计 | Lisp DSL、系统感知、两阶段转换 |
| Coder | 编程助手 | 命令执行、文件操作、代码搜索 |

### 设计模式总结

1. **分层提示词**：信息提取 -> 内容增强 -> 格式转换
2. **Few-Shot 学习**：通过丰富示例引导行为
3. **结构化输出**：JSON、Lisp、SVG等明确格式
4. **工具编排**：ReActAgent、工具链、迭代执行
5. **系统感知**：根据操作系统、字体等调整输出

---

**文档创建时间**：2025-10-17
**相关文件**：
- `autocoder/agent/planner.py`
- `autocoder/agent/designer.py`
- `autocoder/agent/coder.py`
