"""
SDK 模块国际化消息
定义 SDK 模块中使用的所有国际化消息
"""

# SDK 错误信息
SDK_MESSAGES = {
    # CLI 选项验证错误
    "invalid_output_format": {
        "en": "Invalid output format: {{format}}, valid values are: {{valid_formats}}",
        "zh": "无效的输出格式: {{format}}，有效值为: {{valid_formats}}",
        "ja": "無効な出力形式: {{format}}、有効な値: {{valid_formats}}",
        "ar": "تنسيق الإخراج غير صحيح: {{format}}، القيم الصحيحة هي: {{valid_formats}}",
        "ru": "Неверный формат вывода: {{format}}, допустимые значения: {{valid_formats}}"
    },
    "invalid_input_format": {
        "en": "Invalid input format: {{format}}, valid values are: {{valid_formats}}",
        "zh": "无效的输入格式: {{format}}，有效值为: {{valid_formats}}",
        "ja": "無効な入力形式: {{format}}、有効な値: {{valid_formats}}",
        "ar": "تنسيق الإدخال غير صحيح: {{format}}، القيم الصحيحة هي: {{valid_formats}}",
        "ru": "Неверный формат ввода: {{format}}, допустимые значения: {{valid_formats}}"
    },
    "invalid_permission_mode": {
        "en": "Invalid permission mode: {{mode}}, valid values are: {{valid_modes}}",
        "zh": "无效的权限模式: {{mode}}，有效值为: {{valid_modes}}",
        "ja": "無効な権限モード: {{mode}}、有効な値: {{valid_modes}}",
        "ar": "وضع الأذونات غير صحيح: {{mode}}، القيم الصحيحة هي: {{valid_modes}}",
        "ru": "Неверный режим разрешений: {{mode}}, допустимые значения: {{valid_modes}}"
    },
    "invalid_max_turns": {
        "en": "max_turns must be a positive integer or -1 (unlimited)",
        "zh": "max_turns必须为正数或-1（表示不限制）",
        "ja": "max_turnsは正の整数または-1（無制限）である必要があります",
        "ar": "يجب أن يكون max_turns عددًا صحيحًا موجبًا أو -1 (غير محدود)",
        "ru": "max_turns должно быть положительным целым числом или -1 (неограниченно)"
    },
    "session_options_conflict": {
        "en": "continue_session and resume_session cannot be set at the same time",
        "zh": "continue_session和resume_session不能同时设置",
        "ja": "continue_sessionとresume_sessionを同時に設定することはできません",
        "ar": "لا يمكن تعيين continue_session و resume_session في نفس الوقت",
        "ru": "continue_session и resume_session нельзя устанавливать одновременно"
    },
    "model_auto_select_failed": {
        "en": "No model specified and auto-selection failed: no models with configured API keys found. Please specify a model using --model parameter or configure API keys for models",
        "zh": "未指定模型且无法自动选择模型：没有找到配置了API key的模型。请使用 --model 参数指定模型或配置模型的API key",
        "ja": "モデルが指定されておらず、自動選択に失敗しました：設定されたAPIキーを持つモデルが見つかりません。--modelパラメータでモデルを指定するか、モデルのAPIキーを設定してください",
        "ar": "لم يتم تحديد نموذج وفشل الاختيار التلقائي: لم يتم العثور على نماذج بمفاتيح API مكونة. يرجى تحديد نموذج باستخدام معامل --model أو تكوين مفاتيح API للنماذج",
        "ru": "Модель не указана, автовыбор не удался: не найдены модели с настроенными API-ключами. Укажите модель с помощью параметра --model или настройте API-ключи для моделей"
    },

    # CLI 参数帮助文本
    "help_continue_session": {
        "en": "Continue the most recent conversation",
        "zh": "继续最近的对话",
        "ja": "最新の会話を続ける",
        "ar": "متابعة أحدث محادثة",
        "ru": "Продолжить последний разговор"
    },
    "help_resume_session": {
        "en": "Resume a specific session",
        "zh": "恢复特定会话",
        "ja": "特定のセッションを再開する",
        "ar": "استئناف جلسة محددة",
        "ru": "Возобновить конкретную сессию"
    },
    "help_prompt": {
        "en": "Prompt content, read from stdin if not provided",
        "zh": "提示内容，如果未提供则从stdin读取",
        "ja": "プロンプト内容、提供されない場合はstdinから読み取ります",
        "ar": "محتوى المطالبة، يُقرأ من stdin إذا لم يتم توفيره",
        "ru": "Содержимое запроса, читается из stdin если не предоставлено"
    },
    "help_output_format": {
        "en": "Output format (default: text)",
        "zh": "输出格式 (默认: text)",
        "ja": "出力形式（デフォルト: text）",
        "ar": "تنسيق الإخراج (افتراضي: text)",
        "ru": "Формат вывода (по умолчанию: text)"
    },
    "help_input_format": {
        "en": "Input format (default: text)",
        "zh": "输入格式 (默认: text)",
        "ja": "入力形式（デフォルト: text）",
        "ar": "تنسيق الإدخال (افتراضي: text)",
        "ru": "Формат ввода (по умолчанию: text)"
    },
    "help_verbose": {
        "en": "Output detailed information",
        "zh": "输出详细信息",
        "ja": "詳細情報を出力する",
        "ar": "إخراج المعلومات التفصيلية",
        "ru": "Выводить подробную информацию"
    },
    "help_max_turns": {
        "en": "Maximum conversation turns (default: 10000)",
        "zh": "最大对话轮数 (默认:10000 不限制)",
        "ja": "最大会話ターン数（デフォルト: 10000）",
        "ar": "أقصى عدد من دورات المحادثة (افتراضي: 10000)",
        "ru": "Максимальное количество ходов разговора (по умолчанию: 10000)"
    },
    "help_system_prompt": {
        "en": "System prompt",
        "zh": "系统提示",
        "ja": "システムプロンプト",
        "ar": "مطالبة النظام",
        "ru": "Системный запрос"
    },
    "help_system_prompt_path": {
        "en": "Path to system prompt file",
        "zh": "系统提示文件路径",
        "ja": "システムプロンプトファイルのパス",
        "ar": "مسار ملف مطالبة النظام",
        "ru": "Путь к файлу системного запроса"
    },
    "help_allowed_tools": {
        "en": "List of allowed tools",
        "zh": "允许使用的工具列表",
        "ja": "許可されたツールのリスト",
        "ar": "قائمة الأدوات المسموحة",
        "ru": "Список разрешенных инструментов"
    },
    "help_permission_mode": {
        "en": "Permission mode (default: manual)",
        "zh": "权限模式 (默认: manual)",
        "ja": "権限モード（デフォルト: manual）",
        "ar": "وضع الأذونات (افتراضي: manual)",
        "ru": "Режим разрешений (по умолчанию: manual)"
    },
    "help_model": {
        "en": "Specify the model name (e.g., gpt-4, gpt-3.5-turbo, claude-3-sonnet), if not specified, the first model with configured API key will be selected automatically",
        "zh": "指定使用的模型名称 (如: gpt-4, gpt-3.5-turbo, claude-3-sonnet 等)，如果未指定则自动选择第一个设置了API key的模型",
        "ja": "モデル名を指定します（例：gpt-4、gpt-3.5-turbo、claude-3-sonnet）。指定しない場合、設定されたAPIキーを持つ最初のモデルが自動的に選択されます",
        "ar": "حدد اسم النموذج (مثل gpt-4، gpt-3.5-turbo، claude-3-sonnet)، إذا لم يتم تحديده، سيتم تحديد أول نموذج بمفتاح API مكون تلقائيًا",
        "ru": "Укажите название модели (например, gpt-4, gpt-3.5-turbo, claude-3-sonnet), если не указано, автоматически выберется первая модель с настроенным API-ключом"
    },
    "help_include_rules": {
        "en": "Include rules files in the context",
        "zh": "在上下文中包含规则文件",
        "ja": "コンテキストにルールファイルを含める",
        "ar": "تضمين ملفات القواعد في السياق",
        "ru": "Включить файлы правил в контекст"
    },
    "help_pr": {
        "en": "Create Pull Request",
        "zh": "创建 Pull Request",
        "ja": "プルリクエストを作成",
        "ar": "إنشاء طلب سحب",
        "ru": "Создать Pull Request"
    },
    "help_loop": {
        "en": "Number of times to execute the query in a loop (default: 1)",
        "zh": "循环执行查询的次数 (默认: 1)",
        "ja": "クエリをループで実行する回数（デフォルト：1）",
        "ar": "عدد مرات تنفيذ الاستعلام في حلقة (افتراضي: 1)",
        "ru": "Количество раз выполнения запроса в цикле (по умолчанию: 1)"
    },
    "help_loop_keep_conversation": {
        "en": "Keep conversation continuity in loops (use CONTINUE mode for subsequent loops)",
        "zh": "在循环中保持对话连续性（后续循环使用CONTINUE模式）",
        "ja": "ループで会話の連続性を保つ（後続のループでCONTINUEモードを使用）",
        "ar": "الحفاظ على استمرارية المحادثة في الحلقات (استخدام وضع CONTINUE للحلقات اللاحقة)",
        "ru": "Сохранять непрерывность разговора в циклах (использовать режим CONTINUE для последующих циклов)"
    },
    "help_loop_additional_prompt": {
        "en": "Custom additional prompt for subsequent loops (overrides default iterative improvement instructions)",
        "zh": "后续循环的自定义额外提示（覆盖默认的迭代改进指令）",
        "ja": "後続ループのカスタム追加プロンプト（デフォルトの反復改善指示を上書き）",
        "ar": "مطالبة إضافية مخصصة للحلقات اللاحقة (تتجاوز تعليمات التحسين التكراري الافتراضية)",
        "ru": "Пользовательское дополнительное приглашение для последующих циклов (переопределяет инструкции итеративного улучшения по умолчанию)"
    },
    "help_include_libs": {
        "en": "Automatically include LLM friendly packages (comma-separated list, e.g., byzerllm,act)",
        "zh": "自动包含 LLM friendly packages（逗号分隔的列表，例如：byzerllm,act）",
        "ja": "LLM friendly packages を自動的に含める（カンマ区切りリスト、例：byzerllm,act）",
        "ar": "تضمين حزم LLM الودية تلقائياً (قائمة مفصولة بفواصل، مثل: byzerllm,act)",
        "ru": "Автоматически включать LLM friendly packages (список через запятую, например: byzerllm,act)"
    },
    "help_advanced_options": {
        "en": "Advanced options",
        "zh": "高级选项",
        "ja": "高度なオプション",
        "ar": "خيارات متقدمة",
        "ru": "Расширенные опции"
    },

    # 子命令帮助文本
    "help_available_commands": {
        "en": "Available commands",
        "zh": "可用命令",
        "ja": "利用可能なコマンド",
        "ar": "الأوامر المتاحة",
        "ru": "Доступные команды"
    },
    "help_config_command": {
        "en": "Configure auto-coder settings",
        "zh": "配置 auto-coder 设置",
        "ja": "auto-coderの設定を構成",
        "ar": "تكوين إعدادات auto-coder",
        "ru": "Настроить параметры auto-coder"
    },
    "help_config_args": {
        "en": "Configuration arguments in key=value format",
        "zh": "配置参数，使用 key=value 格式",
        "ja": "key=value形式の設定引数",
        "ar": "معاملات التكوين بتنسيق key=value",
        "ru": "Аргументы конфигурации в формате key=value"
    },

    # 异步代理运行器相关帮助文本
    "help_async_group_title": {
        "en": "Async Agent Runner Options",
        "zh": "异步代理运行器选项",
        "ja": "非同期エージェントランナーオプション",
        "ar": "خيارات منفذ العميل غير المتزامن",
        "ru": "Опции асинхронного агент-раннера"
    },
    "help_async_mode": {
        "en": "Enable async agent runner mode with Markdown splitting and parallel processing",
        "zh": "启用异步代理运行器模式，支持 Markdown 分割和并行处理",
        "ja": "Markdownの分割と並列処理を伴う非同期エージェントランナーモードを有効にします",
        "ar": "تمكين وضع منفذ العميل غير المتزامن مع تقسيم Markdown والمعالجة المتوازية",
        "ru": "Включить режим асинхронного агент-раннера с разбиением Markdown и параллельной обработкой"
    },
    "help_split_mode": {
        "en": "Split mode: h1(by H1 heading), h2(by H2 heading), h3(by H3 heading), any(by specified range), delimiter(by delimiter)",
        "zh": "分割模式: h1(按一级标题), h2(按二级标题), h3(按三级标题), any(按指定范围), delimiter(按分隔符)",
        "ja": "分割モード: h1(H1見出しで), h2(H2見出しで), h3(H3見出しで), any(指定された範囲で), delimiter(区切り文字で)",
        "ar": "وضع التقسيم: h1(بواسطة عنوان H1), h2(بواسطة عنوان H2), h3(بواسطة عنوان H3), any(بواسطة نطاق محدد), delimiter(بواسطة فاصل)",
        "ru": "Режим разбиения: h1(по заголовку H1), h2(по заголовку H2), h3(по заголовку H3), any(по указанному диапазону), delimiter(по разделителю)"
    },
    "help_delimiter": {
        "en": "Custom delimiter (used when --split=delimiter, default: ===)",
        "zh": "自定义分隔符（当 --split=delimiter 时使用，默认: ===）",
        "ja": "カスタム区切り文字（--split=delimiterの場合に使用、デフォルト: ===）",
        "ar": "فاصل مخصص (يُستخدم عندما --split=delimiter، افتراضي: ===)",
        "ru": "Пользовательский разделитель (используется при --split=delimiter, по умолчанию: ===)"
    },
    "help_min_level": {
        "en": "Minimum heading level (used when --split=any, default: 1)",
        "zh": "最小标题级别（当 --split=any 时使用，默认: 1）",
        "ja": "最小見出しレベル（--split=anyの場合に使用、デフォルト: 1）",
        "ar": "أدنى مستوى عنوان (يُستخدم عندما --split=any، افتراضي: 1)",
        "ru": "Минимальный уровень заголовка (используется при --split=any, по умолчанию: 1)"
    },
    "help_max_level": {
        "en": "Maximum heading level (used when --split=any, default: 3)",
        "zh": "最大标题级别（当 --split=any 时使用，默认: 3）",
        "ja": "最大見出しレベル（--split=anyの場合に使用、デフォルト: 3）",
        "ar": "أقصى مستوى عنوان (يُستخدم عندما --split=any، افتراضي: 3)",
        "ru": "Максимальный уровень заголовка (используется при --split=any, по умолчанию: 3)"
    },
    "help_workdir": {
        "en": "Working directory (default: ../async_agent_runner_workdir)",
        "zh": "工作目录（默认: ../async_agent_runner_workdir）",
        "ja": "作業ディレクトリ（デフォルト: ../async_agent_runner_workdir）",
        "ar": "دليل العمل (افتراضي: ../async_agent_runner_workdir)",
        "ru": "Рабочий каталог (по умолчанию: ../async_agent_runner_workdir)"
    },
    "help_from_branch": {
        "en": "Base branch (auto-detect if empty, prefer current branch)",
        "zh": "基础分支（为空时自动检测，优先使用当前分支）",
        "ja": "ベースブランチ（空の場合は自動検出、現在のブランチを優先）",
        "ar": "الفرع الأساسي (كشف تلقائي إذا كان فارغًا، يُفضل الفرع الحالي)",
        "ru": "Базовая ветка (автоопределение если пуста, предпочтение текущей ветке)"
    },
    "help_bg_mode": {
        "en": "Background mode, redirect output to log file",
        "zh": "后台运行模式，输出重定向到日志文件",
        "ja": "バックグラウンドモード、出力をログファイルにリダイレクト",
        "ar": "وضع الخلفية، إعادة توجيه الإخراج إلى ملف السجل",
        "ru": "Фоновый режим, перенаправление вывода в лог-файл"
    },
    "help_task_prefix": {
        "en": "Task name prefix for worktrees (async mode only)",
        "zh": "任务名称前缀（仅用于异步模式）",
        "ja": "ワークツリーのタスク名プレフィックス（非同期モードのみ）",
        "ar": "بادئة اسم المهمة لأشجار العمل (وضع غير متزامن فقط)",
        "ru": "Префикс имени задачи для worktree (только в асинхронном режиме)"
    },
    "help_worktree_name": {
        "en": "Specify custom worktree name (async mode only, auto-generated if empty)",
        "zh": "指定自定义 worktree 名称（仅用于异步模式，为空时自动生成）",
        "ja": "カスタム worktree 名を指定（非同期モードのみ、空の場合は自動生成）",
        "ar": "تحديد اسم شجرة العمل المخصص (وضع غير متزامن فقط، يُولد تلقائيًا إذا كان فارغًا)",
        "ru": "Указать пользовательское имя worktree (только асинхронный режим, автосоздание если пуста)"
    },

    # 错误消息
    "config_command_failed": {
        "en": "Configuration command execution failed: {{error}}",
        "zh": "配置命令执行失败: {{error}}",
        "ja": "設定コマンドの実行に失敗しました: {{error}}",
        "ar": "فشل تنفيذ أمر التكوين: {{error}}",
        "ru": "Ошибка выполнения команды конфигурации: {{error}}"
    },

    # CLI 主描述和示例
    "cli_description": {
        "en": "Auto-Coder command line tool",
        "zh": "Auto-Coder 命令行工具",
        "ja": "Auto-Coderコマンドラインツール",
        "ar": "أداة السطر الأمري لـ Auto-Coder",
        "ru": "Командная строка Auto-Coder"
    },
    "cli_examples": {
        "en": """
Examples:
  # Basic usage (auto-select model with API key)
  auto-coder.run "Write a function to calculate Fibonacci numbers"
  
  # Specify model
  auto-coder.run "Write a function to calculate Fibonacci numbers" --model gpt-4
  
  # Input via pipe
  echo "Explain this code" | auto-coder.run --model gpt-4
  
  # Specify output format
  auto-coder.run "Generate a hello world function" --output-format json --model gpt-4
  
  # Continue recent conversation
  auto-coder.run --continue "Continue modifying the code" --model gpt-4
  
  # Resume specific session
  auto-coder.run --resume 550e8400-e29b-41d4-a716-446655440000 "New request" --model gpt-4
  
  # Combine multiple options
  auto-coder.run "Optimize this code" --model claude-3-sonnet --max-turns 5 --verbose
  
  # Include LLM friendly packages
  auto-coder.run "Create a byzer script" --include-libs byzerllm,act --model gpt-4

Async Agent Runner Examples:
  # Basic async mode with H1 splitting
  cat tasks.md | auto-coder.run --async --model gpt-4 --pr
  
  # Split by H2 headings
  cat tasks.md | auto-coder.run --async --split h2 --model gpt-4 --pr
  
  # Custom delimiter splitting
  cat tasks.md | auto-coder.run --async --split delimiter --delimiter "===" --model gpt-4
  
  # Split by heading range
  cat tasks.md | auto-coder.run --async --split any --min-level 2 --max-level 3 --model gpt-4
  
  # Background mode with custom workdir
  cat tasks.md | auto-coder.run --async --bg --workdir ./my_workdir --model gpt-4 --pr
  
  # Specify base branch
  cat tasks.md | auto-coder.run --async --from main --model gpt-4 --pr
  
  # Include LLM friendly packages in async mode
  cat tasks.md | auto-coder.run --async --include-libs byzerllm,act --model gpt-4 --pr
""",
        "zh": """
示例:
  # 基本使用（自动选择有API key的模型）
  auto-coder.run "Write a function to calculate Fibonacci numbers"
  
  # 指定模型
  auto-coder.run "Write a function to calculate Fibonacci numbers" --model gpt-4
  
  # 通过管道提供输入
  echo "Explain this code" | auto-coder.run --model gpt-4
  
  # 指定输出格式
  auto-coder.run "Generate a hello world function" --output-format json --model gpt-4
  
  # 继续最近的对话
  auto-coder.run --continue "继续修改代码" --model gpt-4
  
  # 恢复特定会话
  auto-coder.run --resume 550e8400-e29b-41d4-a716-446655440000 "新的请求" --model gpt-4
  
  # 组合使用多个选项
  auto-coder.run "Optimize this code" --model claude-3-sonnet --max-turns 5 --verbose

异步代理运行器示例:
  # 基本异步模式，按 H1 标题分割
  cat tasks.md | auto-coder.run --async --model gpt-4 --pr
  
  # 按 H2 标题分割
  cat tasks.md | auto-coder.run --async --split h2 --model gpt-4 --pr
  
  # 自定义分隔符分割
  cat tasks.md | auto-coder.run --async --split delimiter --delimiter "===" --model gpt-4
  
  # 按标题范围分割
  cat tasks.md | auto-coder.run --async --split any --min-level 2 --max-level 3 --model gpt-4
  
  # 后台模式，自定义工作目录
  cat tasks.md | auto-coder.run --async --bg --workdir ./my_workdir --model gpt-4 --pr
  
  # 指定基础分支
  cat tasks.md | auto-coder.run --async --from main --model gpt-4 --pr
""",
        "ja": """
例:
  # 基本的な使用方法（APIキーでモデルを自動選択）
  auto-coder.run "Write a function to calculate Fibonacci numbers"
  
  # モデルを指定
  auto-coder.run "Write a function to calculate Fibonacci numbers" --model gpt-4
  
  # パイプ経由で入力
  echo "Explain this code" | auto-coder.run --model gpt-4
  
  # 出力形式を指定
  auto-coder.run "Generate a hello world function" --output-format json --model gpt-4
  
  # 最近の会話を続ける
  auto-coder.run --continue "コードの修正を続ける" --model gpt-4
  
  # 特定のセッションを再開
  auto-coder.run --resume 550e8400-e29b-41d4-a716-446655440000 "新しいリクエスト" --model gpt-4
  
  # 複数のオプションを組み合わせ
  auto-coder.run "Optimize this code" --model claude-3-sonnet --max-turns 5 --verbose

非同期エージェントランナーの例:
  # H1分割による基本的な非同期モード
  cat tasks.md | auto-coder.run --async --model gpt-4 --pr
  
  # H2見出しで分割
  cat tasks.md | auto-coder.run --async --split h2 --model gpt-4 --pr
  
  # カスタム区切り文字で分割
  cat tasks.md | auto-coder.run --async --split delimiter --delimiter "===" --model gpt-4
  
  # 見出しレベル範囲で分割
  cat tasks.md | auto-coder.run --async --split any --min-level 2 --max-level 3 --model gpt-4
  
  # カスタム作業ディレクトリでバックグラウンドモード
  cat tasks.md | auto-coder.run --async --bg --workdir ./my_workdir --model gpt-4 --pr
  
  # ベースブランチを指定
  cat tasks.md | auto-coder.run --async --from main --model gpt-4 --pr
""",
        "ar": """
أمثلة:
  # الاستخدام الأساسي (اختيار تلقائي للنموذج مع مفتاح API)
  auto-coder.run "Write a function to calculate Fibonacci numbers"
  
  # تحديد النموذج
  auto-coder.run "Write a function to calculate Fibonacci numbers" --model gpt-4
  
  # الإدخال عبر الأنبوب
  echo "Explain this code" | auto-coder.run --model gpt-4
  
  # تحديد تنسيق الإخراج
  auto-coder.run "Generate a hello world function" --output-format json --model gpt-4
  
  # متابعة المحادثة الأخيرة
  auto-coder.run --continue "متابعة تعديل الكود" --model gpt-4
  
  # استئناف جلسة محددة
  auto-coder.run --resume 550e8400-e29b-41d4-a716-446655440000 "طلب جديد" --model gpt-4
  
  # دمج خيارات متعددة
  auto-coder.run "Optimize this code" --model claude-3-sonnet --max-turns 5 --verbose

أمثلة منفذ العميل غير المتزامن:
  # وضع غير متزامن أساسي مع تقسيم H1
  cat tasks.md | auto-coder.run --async --model gpt-4 --pr
  
  # التقسيم بواسطة عناوين H2
  cat tasks.md | auto-coder.run --async --split h2 --model gpt-4 --pr
  
  # تقسيم بفاصل مخصص
  cat tasks.md | auto-coder.run --async --split delimiter --delimiter "===" --model gpt-4
  
  # التقسيم بنطاق عناوين
  cat tasks.md | auto-coder.run --async --split any --min-level 2 --max-level 3 --model gpt-4
  
  # وضع الخلفية مع دليل عمل مخصص
  cat tasks.md | auto-coder.run --async --bg --workdir ./my_workdir --model gpt-4 --pr
  
  # تحديد الفرع الأساسي
  cat tasks.md | auto-coder.run --async --from main --model gpt-4 --pr
""",
        "ru": """
Примеры:
  # Базовое использование (автовыбор модели с API-ключом)
  auto-coder.run "Write a function to calculate Fibonacci numbers"
  
  # Указание модели
  auto-coder.run "Write a function to calculate Fibonacci numbers" --model gpt-4
  
  # Ввод через трубу
  echo "Explain this code" | auto-coder.run --model gpt-4
  
  # Указание формата вывода
  auto-coder.run "Generate a hello world function" --output-format json --model gpt-4
  
  # Продолжение последнего разговора
  auto-coder.run --continue "Продолжить изменение кода" --model gpt-4
  
  # Возобновление конкретной сессии
  auto-coder.run --resume 550e8400-e29b-41d4-a716-446655440000 "Новый запрос" --model gpt-4
  
  # Комбинирование нескольких опций
  auto-coder.run "Optimize this code" --model claude-3-sonnet --max-turns 5 --verbose

Примеры асинхронного агент-раннера:
  # Базовый асинхронный режим с разбиением по H1
  cat tasks.md | auto-coder.run --async --model gpt-4 --pr
  
  # Разбиение по заголовкам H2
  cat tasks.md | auto-coder.run --async --split h2 --model gpt-4 --pr
  
  # Разбиение по пользовательскому разделителю
  cat tasks.md | auto-coder.run --async --split delimiter --delimiter "===" --model gpt-4
  
  # Разбиение по диапазону заголовков
  cat tasks.md | auto-coder.run --async --split any --min-level 2 --max-level 3 --model gpt-4
  
  # Фоновый режим с пользовательским рабочим каталогом
  cat tasks.md | auto-coder.run --async --bg --workdir ./my_workdir --model gpt-4 --pr
  
  # Указание базовой ветки
  cat tasks.md | auto-coder.run --async --from main --model gpt-4 --pr
"""
    },
    
    # 输出信息
    "error_prefix": {
        "en": "Error: {{error}}",
        "zh": "错误: {{error}}",
        "ja": "エラー: {{error}}",
        "ar": "خطأ: {{error}}",
        "ru": "Ошибка: {{error}}"
    },
    "unhandled_error": {
        "en": "Unhandled error: {{error}}",
        "zh": "未处理的错误: {{error}}",
        "ja": "未処理のエラー: {{error}}",
        "ar": "خطأ غير معالج: {{error}}",
        "ru": "Необработанная ошибка: {{error}}"
    },
    
    # 常量描述
    "format_description_text": {
        "en": "Plain text format",
        "zh": "纯文本格式",
        "ja": "プレーンテキスト形式",
        "ar": "تنسيق نصي بسيط",
        "ru": "Простой текстовый формат"
    },
    "format_description_json": {
        "en": "JSON format",
        "zh": "JSON格式",
        "ja": "JSON形式",
        "ar": "تنسيق JSON",
        "ru": "Формат JSON"
    },
    "format_description_stream_json": {
        "en": "Streaming JSON format",
        "zh": "流式JSON格式",
        "ja": "ストリーミングJSON形式",
        "ar": "تنسيق JSON التدفقي",
        "ru": "Формат потокового JSON"
    },
    "permission_description_manual": {
        "en": "Manually confirm each operation",
        "zh": "手动确认每个操作",
        "ja": "各操作を手動で確認します",
        "ar": "تأكيد كل عملية بشكل يدوي",
        "ru": "Подтверждать каждую операцию вручную"
    },
    "permission_description_accept_edits": {
        "en": "Automatically accept file edits",
        "zh": "自动接受文件编辑",
        "ja": "ファイルの編集を自動的に承認します",
        "ar": "قبول التعديلات المطبوعة تلقائيًا",
        "ru": "Автоматически принимать изменения в файлах"
    },
    "permission_description_accept_all": {
        "en": "Automatically accept all operations",
        "zh": "自动接受所有操作",
        "ja": "すべての操作を自動的に承認します",
        "ar": "قبول جميع العمليات تلقائيًا",
        "ru": "Автоматически принимать все операции"
    },
    "message_role_user": {
        "en": "User message",
        "zh": "用户消息",
        "ja": "ユーザーメッセージ",
        "ar": "رسالة المستخدم",
        "ru": "Сообщение пользователя"
    },
    "message_role_assistant": {
        "en": "Assistant message",
        "zh": "助手消息",
        "ja": "アシスタントメッセージ",
        "ar": "رسالة المساعد",
        "ru": "Сообщение помощника"
    },
    "message_role_system": {
        "en": "System message",
        "zh": "系统消息",
        "ja": "システムメッセージ",
        "ar": "رسالة النظام",
        "ru": "Системное сообщение"
    },
    
    # 验证错误信息
    "validation_max_turns_positive": {
        "en": "must be positive integer or -1 (unlimited)",
        "zh": "必须为正整数或-1（无限制）",
        "ja": "正の整数または-1（無制限）である必要があります",
        "ar": "يجب أن يكون max_turns عددًا صحيحًا موجبًا أو -1 (غير محدود)",
        "ru": "max_turns должно быть положительным целым числом или -1 (неограниченно)"
    },
    "validation_max_turns_exceed": {
        "en": "cannot exceed 100 (unless -1 for unlimited)",
        "zh": "不能超过100（除非设为-1表示无限制）",
        "ja": "100を超えることはできません（-1の場合を除く）",
        "ar": "لا يمكن أن يتجاوز 100 (إلا إذا كان -1 للغير محدود)",
        "ru": "не может превышать 100 (если не -1 для неограниченного)"
    },
    "validation_output_format_invalid": {
        "en": "must be one of: {{valid_formats}}",
        "zh": "必须为以下值之一: {{valid_formats}}",
        "ja": "以下のいずれかである必要があります: {{valid_formats}}",
        "ar": "يجب أن يكون واحدًا من: {{valid_formats}}",
        "ru": "должно быть одним из: {{valid_formats}}"
    },
    "validation_permission_mode_invalid": {
        "en": "must be one of: {{valid_modes}}",
        "zh": "必须为以下值之一: {{valid_modes}}",
        "ja": "以下のいずれかである必要があります: {{valid_modes}}",
        "ar": "يجب أن يكون واحدًا من: {{valid_modes}}",
        "ru": "должно быть одним из: {{valid_modes}}"
    },
    "validation_allowed_tools_invalid": {
        "en": "invalid tools: {{invalid_tools}}. Valid tools: {{valid_tools}}",
        "zh": "无效的工具: {{invalid_tools}}。有效的工具: {{valid_tools}}",
        "ja": "無効なツール: {{invalid_tools}}。有効なツール: {{valid_tools}}",
        "ar": "أدوات غير صالحة: {{invalid_tools}}، الأدوات الصالحة: {{valid_tools}}",
        "ru": "Недопустимые инструменты: {{invalid_tools}}。Допустимые инструменты: {{valid_tools}}"
    },
    "validation_temperature_range": {
        "en": "must be between 0.0 and 2.0",
        "zh": "必须在0.0和2.0之间",
        "ja": "0.0から2.0の間である必要があります",
        "ar": "يجب أن يكون بين 0.0 و 2.0",
        "ru": "должно быть между 0.0 и 2.0"
    },
    "validation_timeout_positive": {
        "en": "must be positive integer",
        "zh": "必须为正整数",
        "ja": "正の整数である必要があります",
        "ar": "يجب أن يكون عددًا صحيحًا موجبًا",
        "ru": "должно быть положительным целым числом"
    },
    "validation_cwd_not_exist": {
        "en": "directory does not exist: {{path}}",
        "zh": "目录不存在: {{path}}",
        "ja": "ディレクトリが存在しません: {{path}}",
        "ar": "الدليل غير موجود: {{path}}",
        "ru": "директория не существует: {{path}}"
    },
    "validation_cwd_not_directory": {
        "en": "path is not a directory: {{path}}",
        "zh": "路径不是目录: {{path}}",
        "ja": "パスがディレクトリではありません: {{path}}",
        "ar": "المسار غير دليل",
        "ru": "путь не является директорией: {{path}}"
    },
    "validation_role_invalid": {
        "en": "Invalid role: {{role}}. Must be one of: {{valid_roles}}",
        "zh": "无效的角色: {{role}}。必须为以下值之一: {{valid_roles}}",
        "ja": "無効なロール: {{role}}。以下のいずれかである必要があります: {{valid_roles}}",
        "ar": "الدور غير صالح: {{role}}。يجب أن يكون واحدًا من: {{valid_roles}}",
        "ru": "Неверная роль: {{role}}。Должно быть одним из: {{valid_roles}}"
    },
    
    # 异常消息
    "exception_invalid_options": {
        "en": "Invalid options: {{message}}",
        "zh": "无效选项: {{message}}",
        "ja": "無効なオプション: {{message}}",
        "ar": "خيارات غير صالحة: {{message}}",
        "ru": "Недопустимые опции: {{message}}"
    },
    "exception_session_not_found": {
        "en": "Session not found: {{session_id}}",
        "zh": "会话未找到: {{session_id}}",
        "ja": "セッションが見つかりません: {{session_id}}",
        "ar": "الجلسة غير موجودة: {{session_id}}",
        "ru": "Сессия не найдена: {{session_id}}"
    },
    "exception_bridge_error": {
        "en": "Bridge error: {{message}}",
        "zh": "桥接错误: {{message}}",
        "ja": "橋接エラー: {{message}}",
        "ar": "خطأ الجسر: {{message}}",
        "ru": "Ошибка моста: {{message}}"
    },
    "exception_cli_error": {
        "en": "CLI error: {{message}}",
        "zh": "CLI错误: {{message}}",
        "ja": "CLIエラー: {{message}}",
        "ar": "خطأ CLI: {{message}}",
        "ru": "Ошибка CLI: {{message}}"
    },
    "exception_validation_error": {
        "en": "Validation error for '{{field}}': {{message}}",
        "zh": "'{{field}}'验证错误: {{message}}",
        "ja": "'{{field}}'の検証エラー: {{message}}",
        "ar": "خطأ التحقق من الحقل '{{field}}': {{message}}",
        "ru": "Ошибка валидации для '{{field}}': {{message}}"
    },
    
    # 提示内容获取错误
    "prompt_not_provided_empty_stdin": {
        "en": "No prompt provided and standard input is empty",
        "zh": "未提供提示内容且标准输入为空",
        "ja": "プロンプトが提供されておらず、標準入力が空です",
        "ar": "لم يتم توفير المطالبة، والإدخال القياسي فارغًا",
        "ru": "Содержимое запроса не предоставлено, а стандартный ввод пуст"
    },
    
    # CLI 选项验证错误
    "invalid_split_mode": {
        "en": "Invalid split mode: {{mode}}. Valid values: {{valid_modes}}",
        "zh": "无效的分割模式: {{mode}}。有效值: {{valid_modes}}",
        "ja": "無効な分割モード: {{mode}}。有効な値: {{valid_modes}}",
        "ar": "وضع التقسيم غير صالح: {{mode}}。القيم الصالحة: {{valid_modes}}",
        "ru": "Неверный режим разбиения: {{mode}}。Допустимые значения: {{valid_modes}}"
    },
    "heading_level_must_be_positive": {
        "en": "Heading level must be greater than or equal to 1",
        "zh": "标题级别必须大于等于1",
        "ja": "見出しレベルは1以上である必要があります",
        "ar": "يجب أن يكون مستوى العنوان أكبر من أو يساوي 1",
        "ru": "Уровень заголовка должен быть больше или равен 1"
    },
    "min_level_cannot_exceed_max": {
        "en": "Minimum heading level cannot be greater than maximum heading level",
        "zh": "最小标题级别不能大于最大标题级别",
        "ja": "最小見出しレベルは最大見出しレベルを超えることはできません",
        "ar": "لا يمكن أن يكون أدنى مستوى عنوان أكبر من أقصى مستوى عنوان",
        "ru": "Минимальный уровень заголовка не может быть больше максимального уровня заголовка"
    },
    "delimiter_required_for_delimiter_mode": {
        "en": "A valid delimiter must be provided when using delimiter split mode",
        "zh": "使用 delimiter 分割模式时必须提供有效的分隔符",
        "ja": "delimiter分割モードを使用する場合は有効な区切り文字を提供する必要があります",
        "ar": "يجب توفير فاصل صالح عند استخدام وضع التقسيم بواسطة الفاصل",
        "ru": "При использовании режима разбиения по разделителю должен быть предоставлен допустимый разделитель"
    },
    "prompt_not_provided_no_stdin": {
        "en": "No prompt provided and no standard input available",
        "zh": "未提供提示内容且没有标准输入",
        "ja": "プロンプトが提供されておらず、標準入力も利用できません",
        "ar": "لم يتم توفير المطالبة، ولا يمكن استخدام الإدخال القياسي",
        "ru": "Содержимое запроса не предоставлено, а стандартный ввод недоступен"
    },
    
    # 异步运行器 - Worktree Manager 消息
    "reusing_existing_worktree": {
        "en": "Reusing existing working directory: {{path}}",
        "zh": "复用现有工作目录: {{path}}",
        "ja": "既存の作業ディレクトリを再利用します: {{path}}",
        "ar": "إعادة استخدام دليل العمل الموجود: {{path}}",
        "ru": "Используем существующий рабочий каталог: {{path}}"
    },
    "worktree_already_exists": {
        "en": "Working directory already exists: {{path}}",
        "zh": "工作目录已存在: {{path}}",
        "ja": "作業ディレクトリが既に存在します: {{path}}",
        "ar": "دليل العمل موجود بالفعل: {{path}}",
        "ru": "Рабочий каталог уже существует: {{path}}"
    },
    "create_git_worktree_failed": {
        "en": "Failed to create git worktree: {{error}}",
        "zh": "创建 git worktree 失败: {{error}}",
        "ja": "git worktreeの作成に失敗しました: {{error}}",
        "ar": "فشل إنشاء عملية git worktree: {{error}}",
        "ru": "Создание git worktree не удалось: {{error}}"
    },
    "create_git_worktree": {
        "en": "Creating git worktree: {{name}}",
        "zh": "创建 git worktree: {{name}}",
        "ja": "git worktreeを作成中: {{name}}",
        "ar": "إنشاء عملية git worktree: {{name}}",
        "ru": "Создание git worktree: {{name}}"
    },
    "using_current_branch": {
        "en": "Using current branch: {{branch}}",
        "zh": "使用当前分支: {{branch}}",
        "ja": "現在のブランチを使用します: {{branch}}",
        "ar": "يستخدم الفرع الحالي: {{branch}}",
        "ru": "Используется текущая ветка: {{branch}}"
    },
    "detected_branches": {
        "en": "Detected branches: {{branches}}",
        "zh": "检测到的分支: {{branches}}",
        "ja": "検出されたブランチ: {{branches}}",
        "ar": "تم الكشف عن الفروع: {{branches}}",
        "ru": "Обнаружены ветки: {{branches}}"
    },
    "using_main_branch": {
        "en": "Using main branch",
        "zh": "使用 main 分支",
        "ja": "メインブランチを使用します",
        "ar": "يستخدم الفرع الأساسي",
        "ru": "Используется основная ветка"
    },
    "using_master_branch": {
        "en": "Using master branch",
        "zh": "使用 master 分支",
        "ja": "マスターブランチを使用します",
        "ar": "يستخدم الفرع الرئيسي",
        "ru": "Используется ветка master"
    },
    "using_first_available_branch": {
        "en": "Using first available branch: {{branch}}",
        "zh": "使用第一个可用分支: {{branch}}",
        "ja": "最初の利用可能なブランチを使用します: {{branch}}",
        "ar": "يستخدم الفرع الأول المتاح: {{branch}}",
        "ru": "Используется первая доступная ветка: {{branch}}"
    },
    "get_branch_list_failed": {
        "en": "Failed to get branch list: {{error}}",
        "zh": "获取分支列表失败: {{error}}",
        "ja": "ブランチリストの取得に失敗しました: {{error}}",
        "ar": "فشل الحصول على قائمة الفروع: {{error}}",
        "ru": "Не удалось получить список веток: {{error}}"
    },
    "using_remote_default_branch": {
        "en": "Using remote default branch: {{branch}}",
        "zh": "使用远程默认分支: {{branch}}",
        "ja": "リモートのデフォルトブランチを使用します: {{branch}}",
        "ar": "يستخدم الفرع الافتراضي للرمز البعيد: {{branch}}",
        "ru": "Используется удаленная ветка по умолчанию: {{branch}}"
    },
    "cannot_detect_any_branch": {
        "en": "Cannot detect any available branch",
        "zh": "无法检测到任何可用的分支",
        "ja": "利用可能なブランチを検出できません",
        "ar": "لا يمكن الكشف عن أي فرع متاح",
        "ru": "Не удалось обнаружить доступные ветки"
    },
    "cleanup_worktree_failed": {
        "en": "Failed to cleanup worktree: {{error}}",
        "zh": "清理 worktree 失败: {{error}}",
        "ja": "worktreeのクリーンアップに失敗しました: {{error}}",
        "ar": "فشل تنظيف عملية worktree: {{error}}",
        "ru": "Не удалось очистить worktree: {{error}}"
    },
    "get_worktree_list_failed": {
        "en": "Failed to get worktree list: {{error}}",
        "zh": "获取 worktree 列表失败: {{error}}",
        "ja": "worktreeリストの取得に失敗しました: {{error}}",
        "ar": "فشل الحصول على قائمة worktree: {{error}}",
        "ru": "Не удалось получить список worktree: {{error}}"
    },
    "write_file_failed": {
        "en": "Failed to write file: {{error}}",
        "zh": "写入文件失败: {{error}}",
        "ja": "ファイルの書き込みに失敗しました: {{error}}",
        "ar": "فشل كتابة الملف: {{error}}",
        "ru": "Не удалось записать файл: {{error}}"
    },
    
    # 异步运行器 - Async Executor 消息
    "execution_failed": {
        "en": "Execution failed: {{error}}",
        "zh": "执行失败: {{error}}",
        "ja": "実行に失敗しました: {{error}}",
        "ar": "فشل التنفيذ: {{error}}",
        "ru": "Выполнение не удалось: {{error}}"
    },
    "autocoder_run_failed_with_code": {
        "en": "auto-coder.run execution failed with return code: {{code}}",
        "zh": "auto-coder.run 执行失败，返回码: {{code}}",
        "ja": "auto-coder.runの実行に失敗しました、戻りコード: {{code}}",
        "ar": "فشل تنفيذ auto-coder.run مع كود العودة: {{code}}",
        "ru": "auto-coder.run выполнение не удалось, код возврата: {{code}}"
    },
    "execution_timeout": {
        "en": "Execution timeout",
        "zh": "执行超时",
        "ja": "実行タイムアウト",
        "ar": "وقت استئناف التنفيذ",
        "ru": "Время выполнения истекло"
    },
    "background_execution_failed": {
        "en": "Background execution failed: {{error}}",
        "zh": "后台执行失败: {{error}}",
        "ja": "バックグラウンド実行に失敗しました: {{error}}",
        "ar": "فشل التنفيذ في الخلفية: {{error}}",
        "ru": "Фоновая выполнение не удалось: {{error}}"
    },
    "foreground_execution_failed": {
        "en": "Foreground execution failed: {{error}}",
        "zh": "前台执行失败: {{error}}",
        "ja": "フォアグラウンド実行に失敗しました: {{error}}",
        "ar": "فشل التنفيذ في الأمام: {{error}}",
        "ru": "Переднее выполнение не удалось: {{error}}"
    },
    "background_task_running": {
        "en": "Running in background, log file: {{log_file}}",
        "zh": "后台运行中，日志文件: {{log_file}}",
        "ja": "バックグラウンドで実行中、ログファイル: {{log_file}}",
        "ar": "تعمل في الخلفية، ملف السجل: {{log_file}}",
        "ru": "Выполнение в фоновом режиме, лог-файл: {{log_file}}"
    },
    "background_task_completed": {
        "en": "Background task completed",
        "zh": "后台任务完成",
        "ja": "バックグラウンドタスクが完了しました",
        "ar": "تم إكمال المهمة في الخلفية",
        "ru": "Фоновая задача завершена"
    },
    "foreground_task_running": {
        "en": "Running in foreground, output as follows:",
        "zh": "前台运行中，输出如下：",
        "ja": "フォアグラウンドで実行中、出力は次のようになります:",
        "ar": "تعمل في الأمام، الإخراج كما يلي:",
        "ru": "Выполнение в переднем плане, вывод следующий:"
    },
    "foreground_task_completed": {
        "en": "Foreground task completed",
        "zh": "前台任务完成",
        "ja": "フォアグラウンドタスクが完了しました",
        "ar": "تم إكمال المهمة في الأمام",
        "ru": "Передняя задача завершена"
    },
    "processing_document": {
        "en": "Processing document: {{info}}",
        "zh": "处理文档: {{info}}",
        "ja": "ドキュメントを処理中: {{info}}",
        "ar": "يتم معالجة المستند: {{info}}",
        "ru": "Обработка документа: {{info}}"
    },
    "creating_git_worktree": {
        "en": "Creating git worktree: {{name}}",
        "zh": "创建 git worktree: {{name}}",
        "ja": "git worktreeを作成中: {{name}}",
        "ar": "إنشاء عملية git worktree: {{name}}",
        "ru": "Создание git worktree: {{name}}"
    },
    "git_worktree_created_successfully": {
        "en": "✓ Git worktree created successfully: {{path}}",
        "zh": "✓ git worktree 创建成功: {{path}}",
        "ja": "✓ git worktreeが正常に作成されました: {{path}}",
        "ar": "✓ إنشاء عملية git worktree بنجاح: {{path}}",
        "ru": "✓ git worktree создан успешно: {{path}}"
    },
    "git_worktree_creation_failed": {
        "en": "✗ Git worktree creation failed: {{error}}",
        "zh": "✗ 创建 git worktree 失败: {{error}}",
        "ja": "✗ git worktreeの作成に失敗しました: {{error}}",
        "ar": "✗ فشل إنشاء عملية git worktree: {{error}}",
        "ru": "✗ Создание git worktree не удалось: {{error}}"
    },
    "writing_content_to_file": {
        "en": "Writing content to file: {{filename}}",
        "zh": "写入内容到文件: {{filename}}",
        "ja": "ファイルに内容を書き込み中: {{filename}}",
        "ar": "كتابة المحتوى في الملف: {{filename}}",
        "ru": "Запись содержимого в файл: {{filename}}"
    },
    "file_write_successful": {
        "en": "✓ File write successful",
        "zh": "✓ 文件写入成功",
        "ja": "✓ ファイルの書き込みに成功しました",
        "ar": "✓ كتابة الملف بنجاح",
        "ru": "✓ Файл успешно записан"
    },
    "running_autocoder": {
        "en": "Running auto-coder.run...",
        "zh": "运行 auto-coder.run...",
        "ja": "auto-coder.runを実行中...",
        "ar": "تشغيل auto-coder.run...",
        "ru": "Запуск auto-coder.run..."
    },
    "processing_completed": {
        "en": "✓ Processing completed: {{name}}",
        "zh": "✓ 完成处理: {{name}}",
        "ja": "✓ 処理が完了しました: {{name}}",
        "ar": "✓ تم اكتمال المعالجة: {{name}}",
        "ru": "✓ Обработка завершена: {{name}}"
    },
    "autocoder_run_execution_failed": {
        "en": "✗ auto-coder.run execution failed: {{error}}",
        "zh": "✗ auto-coder.run 执行失败: {{error}}",
        "ja": "✗ auto-coder.runの実行に失敗しました: {{error}}",
        "ar": "✗ تنفيذ auto-coder.run فشل: {{error}}",
        "ru": "✗ auto-coder.run выполнение не удалось: {{error}}"
    },
    "document_processing_failed": {
        "en": "✗ Document processing failed: {{error}}",
        "zh": "✗ 处理文档失败: {{error}}",
        "ja": "✗ ドキュメントの処理に失敗しました: {{error}}",
        "ar": "✗ معالجة المستند فشلت: {{error}}",
        "ru": "✗ Обработка документа не удалась: {{error}}"
    },
    "cleaning_failed_worktree": {
        "en": "Cleaning failed worktree: {{name}}",
        "zh": "清理失败的 worktree: {{name}}",
        "ja": "worktreeのクリーンアップに失敗しました: {{name}}",
        "ar": "فشل تنظيف عملية worktree: {{name}}",
        "ru": "Не удалось очистить worktree: {{name}}"
    },
    "cleanup_worktree_warning": {
        "en": "Warning: Failed to cleanup worktree: {{error}}",
        "zh": "警告: 清理 worktree 失败: {{error}}",
        "ja": "警告: worktreeのクリーンアップに失敗しました: {{error}}",
        "ar": "تحذير: فشل تنظيف عملية worktree: {{error}}",
        "ru": "Предупреждение: Не удалось очистить worktree: {{error}}"
    },
    "document_processing_unexpected_error": {
        "en": "✗ Unexpected error occurred while processing document: {{error}}",
        "zh": "✗ 处理文档时发生未预期错误: {{error}}",
        "ja": "✗ ドキュメントの処理中に予期せぬエラーが発生しました: {{error}}",
        "ar": "✗ حدث خطأ غير متوقع أثناء معالجة المستند: {{error}}",
        "ru": "✗ Возникла непредвиденная ошибка при обработке документа: {{error}}"
    },
    "cleaning_worktree": {
        "en": "Cleaning worktree: {{name}}",
        "zh": "清理 worktree: {{name}}",
        "ja": "worktreeをクリーンアップ中: {{name}}",
        "ar": "تنظيف عملية worktree: {{name}}",
        "ru": "Очистка worktree: {{name}}"
    },
    "cleanup_all_worktrees": {
        "en": "Cleaning all worktrees...",
        "zh": "清理所有 worktree...",
        "ja": "すべてのworktreeをクリーンアップ中...",
        "ar": "تنظيف جميع عمليات worktree...",
        "ru": "Очистка всех worktree..."
    },
    
    # 异步运行器 - Async Handler 消息
    "no_stdin_data": {
        "en": "No data read from standard input, please use pipe to input Markdown file",
        "zh": "没有从标准输入读取到数据，请使用管道输入 Markdown 文件",
        "ja": "標準入力からデータが読み込まれませんでした、Markdownファイルをパイプで入力してください",
        "ar": "لم يتم قراءة البيانات من الإدخال القياسي، يرجى استخدام الأنبوب لإدخال ملف Markdown",
        "ru": "Данные из стандартного ввода не были прочитаны, пожалуйста, используйте трубу для ввода Markdown-файла"
    },
    "input_content_empty": {
        "en": "Input content is empty",
        "zh": "输入内容为空",
        "ja": "入力内容が空です",
        "ar": "المحتوى المدخل فارغ",
        "ru": "Введенное содержимое пусто"
    },
    "no_processable_document_content": {
        "en": "No processable document content found",
        "zh": "没有找到可处理的文档内容",
        "ja": "処理可能なドキュメントコンテンツが見つかりませんでした",
        "ar": "لم يتم العثور على محتوى مستند قابل للمعالجة",
        "ru": "Не найдено содержимое документа, которое можно обработать"
    },
    "parsed_document_parts": {
        "en": "Parsed {{count}} document parts",
        "zh": "解析到 {{count}} 个文档部分",
        "ja": "{{count}}個のドキュメントパートを解析しました",
        "ar": "تم تحليل {{count}} أجزاء من المستند",
        "ru": "Разбор {{count}} частей документа"
    },
    "starting_async_document_processing": {
        "en": "Starting async document processing...",
        "zh": "开始异步处理文档...",
        "ja": "非同期ドキュメント処理を開始します...",
        "ar": "بدء معالجة المستند بشكل غير متزامن...",
        "ru": "Начало асинхронной обработки документа..."
    },
    "async_execution_failed": {
        "en": "Async execution failed: {{error}}",
        "zh": "异步执行失败: {{error}}",
        "ja": "非同期実行に失敗しました: {{error}}",
        "ar": "فشل التنفيذ غير المتزامن: {{error}}",
        "ru": "Асинхронное выполнение не удалось: {{error}}"
    },
    "async_agent_runner_completed": {
        "en": "Async agent runner execution completed",
        "zh": "异步代理运行器执行完成",
        "ja": "非同期エージェントランナーの実行が完了しました",
        "ar": "تم إكمال إجراء منفذ العميل غير المتزامن",
        "ru": "Асинхронный агент-раннер выполнен"
    },
    "total_processed": {
        "en": "Total processed: {{total}} documents",
        "zh": "总共处理: {{total}} 个文档",
        "ja": "処理済みのドキュメント: {{total}}個",
        "ar": "المستندات المعالجة: {{total}} مستند",
        "ru": "Обработано документов: {{total}}"
    },
    "success_count": {
        "en": "Success: {{count}} documents",
        "zh": "成功: {{count}} 个",
        "ja": "成功: {{count}}個",
        "ar": "نجاح: {{count}} مستند",
        "ru": "Успешно: {{count}} документов"
    },
    "failure_count": {
        "en": "Failed: {{count}} documents",
        "zh": "失败: {{count}} 个",
        "ja": "失敗: {{count}}個",
        "ar": "فشل: {{count}} مستند",
        "ru": "Неудачно: {{count}} документов"
    },
    "log_files": {
        "en": "Log files:",
        "zh": "日志文件:",
        "ja": "ログファイル:",
        "ar": "ملفات السجل:",
        "ru": "Лог-файлы:"
    },
    "failed_tasks": {
        "en": "Failed tasks:",
        "zh": "失败的任务:",
        "ja": "失敗したタスク:",
        "ar": "المهام الفاشلة:",
        "ru": "Неудачные задачи:"
    },
    "async_agent_handler_execution_failed": {
        "en": "Async agent handler execution failed: {{error}}",
        "zh": "异步代理处理器执行失败: {{error}}",
        "ja": "非同期エージェントハンドラーの実行に失敗しました: {{error}}",
        "ar": "فشل تنفيذ منفذ العميل غير المتزامن: {{error}}",
        "ru": "Асинхронный агент-обработчик выполнение не удалось: {{error}}"
    },
    "read_stdin_failed": {
        "en": "Failed to read standard input: {{error}}",
        "zh": "读取标准输入失败: {{error}}",
        "ja": "標準入力から読み込むのに失敗しました: {{error}}",
        "ar": "فشل قراءة الإدخال القياسي: {{error}}",
        "ru": "Не удалось прочитать стандартный ввод: {{error}}"
    },
    "worktree_cleanup_completed": {
        "en": "worktree cleanup completed",
        "zh": "worktree 清理完成",
        "ja": "worktreeのクリーンアップが完了しました",
        "ar": "تم إكمال تنظيف عملية worktree",
        "ru": "Очистка worktree завершена"
    },
    "worktree_cleanup_failed": {
        "en": "Failed to cleanup worktree: {{error}}",
        "zh": "清理 worktree 失败: {{error}}",
        "ja": "worktreeのクリーンアップに失敗しました: {{error}}",
        "ar": "فشل تنظيف عملية worktree: {{error}}",
        "ru": "Не удалось очистить worktree: {{error}}"
    },
    
    # 异步运行器 - Markdown Processor 消息
    "content_empty": {
        "en": "Content is empty",
        "zh": "内容为空",
        "ja": "コンテンツが空です",
        "ar": "المحتوى فارغ",
        "ru": "Содержимое пусто"
    },
    "detected_multi_document_structure": {
        "en": "Detected multi-document structure, using multi-document parsing mode",
        "zh": "检测到多文档结构，使用多文档解析模式",
        "ja": "複数のドキュメント構造が検出され、複数のドキュメント解析モードを使用します",
        "ar": "تم الكشف على بنية عدة مستندات، استخدام وضع تحليل مستندات متعددة",
        "ru": "Обнаружена многодокументная структура, использование многодокументного режима разбора"
    },
    "multi_document_parse_failed_fallback": {
        "en": "Multi-document parsing failed: {{error}}, falling back to standard splitting",
        "zh": "多文档解析失败: {{error}}，回退到标准分割",
        "ja": "複数のドキュメント解析に失敗しました: {{error}}、標準分割にフォールバックします",
        "ar": "فشل تحليل مستندات متعددة: {{error}}، العودة إلى التقسيم القياسي",
        "ru": "Многодокументный разбор не удался: {{error}}，возвращаемся к стандартному разбиению"
    },
    "using_custom_splitter": {
        "en": "Using custom splitter",
        "zh": "使用自定义分割器",
        "ja": "カスタムスプリッターを使用します",
        "ar": "استخدام عامل تقسيم خاص",
        "ru": "Использование пользовательского разделителя"
    },
    "cannot_parse_multi_document_structure": {
        "en": "Cannot parse multi-document structure",
        "zh": "无法解析多文档结构",
        "ja": "複数のドキュメント構造を解析できません",
        "ar": "لا يمكن تحليل بنية عدة مستندات",
        "ru": "Не удалось разобрать многодокументную структуру"
    },
    
    # 异步运行器 - Pull Request 相关消息
    "checking_pr_creation": {
        "en": "Checking if Pull Request creation is needed...",
        "zh": "正在检查是否需要创建 Pull Request...",
        "ja": "プルリクエストの作成が必要かどうかを確認中...",
        "ar": "يتم التحقق مما إذا كان إنشاء طلب السحب ضروريًا...",
        "ru": "Проверка необходимости создания Pull Request..."
    },
    "found_uncommitted_changes": {
        "en": "Found uncommitted changes, committing automatically...",
        "zh": "发现未提交的更改，正在自动提交...",
        "ja": "未コミットの変更が見つかりました、自動的にコミットします...",
        "ar": "تم العثور على تغييرات غير مطابقة للتسليم، إنشاء طلب السحب تلقائيًا...",
        "ru": "Обнаружены неотправленные изменения, автоматически создание Pull Request..."
    },
    "auto_commit_failed": {
        "en": "❌ Auto commit failed, cannot create PR",
        "zh": "❌ 自动提交失败，无法创建 PR",
        "ja": "❌ 自動コミットに失敗しました、PRを作成できませんでした",
        "ar": "❌ فشل التسليم التلقائي، لا يمكن إنشاء طلب السحب",
        "ru": "❌ Автоматическое создание коммита не удалось, не удалось создать PR"
    },
    "cannot_get_current_branch": {
        "en": "❌ Cannot get current branch information",
        "zh": "❌ 无法获取当前分支信息",
        "ja": "❌ 現在のブランチ情報を取得できません",
        "ar": "❌ لا يمكن الحصول على معلومات الفرع الحالي",
        "ru": "❌ Не удалось получить информацию о текущей ветке"
    },
    "creating_pull_request": {
        "en": "Creating Pull Request: {{title}}",
        "zh": "正在创建 Pull Request: {{title}}",
        "ja": "プルリクエストを作成中: {{title}}",
        "ar": "إنشاء طلب سحب: {{title}}",
        "ru": "Создание Pull Request: {{title}}"
    },
    "pull_request_created_successfully": {
        "en": "✅ Pull Request created successfully!",
        "zh": "✅ Pull Request 创建成功!",
        "ja": "✅ プルリクエストが正常に作成されました！",
        "ar": "✅ تم إنشاء طلب السحب بنجاح!",
        "ru": "✅ Pull Request создан успешно!"
    },
    "pull_request_creation_failed": {
        "en": "❌ Pull Request creation failed: {{error}}",
        "zh": "❌ Pull Request 创建失败: {{error}}",
        "ja": "❌ プルリクエストの作成に失敗しました: {{error}}",
        "ar": "❌ فشل إنشاء طلب السحب: {{error}}",
        "ru": "❌ Создание Pull Request не удалось: {{error}}"
    },
    "pull_request_creation_error": {
        "en": "❌ Error occurred during Pull Request creation: {{error}}",
        "zh": "❌ 创建 Pull Request 时出错: {{error}}",
        "ja": "❌ プルリクエストの作成中にエラーが発生しました: {{error}}",
        "ar": "❌ حدث خطأ أثناء إنشاء طلب السحب: {{error}}",
        "ru": "❌ Возникла ошибка во время создания Pull Request: {{error}}"
    },
    
    # 异步运行器任务模式相关消息
    "async_mode_task_info": {
        "en": "{{mode}} task information:",
        "zh": "{{mode}}任务信息:",
        "ja": "{{mode}}タスク情報:",
        "ar": "{{mode}} معلومات المهمة:",
        "ru": "{{mode}} информация о задаче:"
    },
    "execution_directory": {
        "en": "Execution directory: {{dir}}",
        "zh": "执行目录: {{dir}}",
        "ja": "実行ディレクトリ: {{dir}}",
        "ar": "دليل التنفيذ: {{dir}}",
        "ru": "Исполняемый каталог: {{dir}}"
    },
    "temp_file": {
        "en": "Temp file: {{file}}",
        "zh": "临时文件: {{file}}",
        "ja": "一時ファイル: {{file}}",
        "ar": "ملف آمن: {{file}}",
        "ru": "Временный файл: {{file}}"
    },
    "using_model": {
        "en": "Using model: {{model}}",
        "zh": "使用模型: {{model}}",
        "ja": "モデルを使用します: {{model}}",
        "ar": "استخدام النموذج: {{model}}",
        "ru": "Использование модели: {{model}}"
    },
    "create_pr": {
        "en": "Create PR: {{pr}}",
        "zh": "创建 PR: {{pr}}",
        "ja": "PRを作成: {{pr}}",
        "ar": "إنشاء PR: {{pr}}",
        "ru": "Создать PR: {{pr}}"
    },
    "run_mode": {
        "en": "Run mode: {{mode}}",
        "zh": "运行模式: {{mode}}",
        "ja": "実行モード: {{mode}}",
        "ar": "وضع التشغيل: {{mode}}",
        "ru": "Режим выполнения: {{mode}}"
    },
    "full_path": {
        "en": "Full path: {{path}}",
        "zh": "完整路径: {{path}}",
        "ja": "完全なパス: {{path}}",
        "ar": "المسار الكامل: {{path}}",
        "ru": "Полный путь: {{path}}"
    },
    "meta_file_path": {
        "en": "Meta file: {{path}}",
        "zh": "元数据文件: {{path}}",
        "ja": "メタファイル: {{path}}",
        "ar": "ملف ميتا: {{path}}",
        "ru": "Мета-файл: {{path}}"
    },
    "background_mode": {
        "en": "Background mode",
        "zh": "后台模式",
        "ja": "バックグラウンドモード",
        "ar": "وضع الخلفية",
        "ru": "Фоновый режим"
    },
    "foreground_mode": {
        "en": "Foreground mode",
        "zh": "前台模式",
        "ja": "フォアグラウンドモード",
        "ar": "وضع الأمام",
        "ru": "Передний план"
    },
    
    # 异常类消息
    "sdk_error_with_code": {
        "en": "SDK Error [{{error_code}}]: {{message}}",
        "zh": "SDK错误 [{{error_code}}]: {{message}}",
        "ja": "SDKエラー [{{error_code}}]: {{message}}",
        "ar": "خطأ SDK [{{error_code}}]: {{message}}",
        "ru": "Ошибка SDK [{{error_code}}]: {{message}}"
    },
    "session_not_found": {
        "en": "Session not found: {{session_id}}",
        "zh": "会话未找到: {{session_id}}",
        "ja": "セッションが見つかりません: {{session_id}}",
        "ar": "الجلسة غير موجودة: {{session_id}}",
        "ru": "Сессия не найдена: {{session_id}}"
    },
    "invalid_options": {
        "en": "Invalid options: {{message}}",
        "zh": "无效选项: {{message}}",
        "ja": "無効なオプション: {{message}}",
        "ar": "خيارات غير صالحة: {{message}}",
        "ru": "Недопустимые опции: {{message}}"
    },
    "bridge_error": {
        "en": "Bridge error: {{message}}",
        "zh": "桥接错误: {{message}}",
        "ja": "橋接エラー: {{message}}",
        "ar": "خطأ الجسر: {{message}}",
        "ru": "Ошибка моста: {{message}}"
    },
    "bridge_error_with_original": {
        "en": "Bridge error: {{message}} (Original: {{original_error}})",
        "zh": "桥接错误: {{message}} (原始错误: {{original_error}})",
        "ja": "橋接エラー: {{message}} (元のエラー: {{original_error}})",
        "ar": "خطأ الجسر: {{message}} (الأصل: {{original_error}})",
        "ru": "Ошибка моста: {{message}} (Оригинал: {{original_error}})"
    },
    "cli_error": {
        "en": "CLI error: {{message}}",
        "zh": "CLI错误: {{message}}",
        "ja": "CLIエラー: {{message}}",
        "ar": "خطأ CLI: {{message}}",
        "ru": "Ошибка CLI: {{message}}"
    },
    "validation_error_field": {
        "en": "Validation error for '{{field}}': {{message}}",
        "zh": "'{{field}}'验证错误: {{message}}",
        "ja": "'{{field}}'の検証エラー: {{message}}",
        "ar": "خطأ التحقق من الحقل '{{field}}': {{message}}",
        "ru": "Ошибка валидации для '{{field}}': {{message}}"
    },
    
    # 异步任务管理相关消息
    "async_task_list_param_error": {
        "en": "❌ Parameter Error",
        "zh": "❌ 参数错误",
        "ja": "❌ パラメータエラー",
        "ar": "❌ خطأ في المعلمة",
        "ru": "❌ Ошибка параметра"
    },
    "async_task_list_usage": {
        "en": "Usage: [cyan]/auto async list[/cyan]\\nor: [cyan]/auto list[/cyan]\\n\\nUse [yellow]/auto async task <task_id>[/yellow] to view task details",
        "zh": "用法: [cyan]/auto async list[/cyan]\\n或: [cyan]/auto list[/cyan]\\n\\n使用 [yellow]/auto async task <task_id>[/yellow] 查看任务详情",
        "ja": "使用法: [cyan]/auto async list[/cyan]\\nまたは: [cyan]/auto list[/cyan]\\n\\n[yellow]/auto async task <task_id>[/yellow] でタスクの詳細を表示",
        "ar": "الاستخدام: [cyan]/auto async list[/cyan]\\nأو: [cyan]/auto list[/cyan]\\n\\nاستخدم [yellow]/auto async task <task_id>[/yellow] لعرض تفاصيل المهمة",
        "ru": "Использование: [cyan]/auto async list[/cyan]\\nили: [cyan]/auto list[/cyan]\\n\\nИспользуйте [yellow]/auto async task <task_id>[/yellow] для просмотра деталей задачи"
    },
    "async_task_list_title": {
        "en": "📋 Async Agent Tasks",
        "zh": "📋 异步代理任务",
        "ja": "📋 非同期エージェントタスク",
        "ar": "📋 مهام الوكيل غير المتزامن",
        "ru": "📋 Задачи асинхронного агента"
    },
    "async_task_list_no_tasks": {
        "en": "No async tasks found.\\n\\nTo start an async task:\\n[cyan]cat tasks.md | auto-coder.run --async --model gpt-4[/cyan]",
        "zh": "未找到异步任务。\\n\\n启动异步任务：\\n[cyan]cat tasks.md | auto-coder.run --async --model gpt-4[/cyan]",
        "ja": "非同期タスクが見つかりませんでした。\\n\\n非同期タスクを開始するには：\\n[cyan]cat tasks.md | auto-coder.run --async --model gpt-4[/cyan]",
        "ar": "لم يتم العثور على مهام غير متزامنة.\\n\\nلبدء مهمة غير متزامنة:\\n[cyan]cat tasks.md | auto-coder.run --async --model gpt-4[/cyan]",
        "ru": "Асинхронные задачи не найдены.\\n\\nДля запуска асинхронной задачи:\\n[cyan]cat tasks.md | auto-coder.run --async --model gpt-4[/cyan]"
    },
    "async_task_list_error": {
        "en": "Failed to load async tasks: {{error}}",
        "zh": "加载异步任务失败: {{error}}",
        "ja": "非同期タスクの読み込みに失敗しました: {{error}}",
        "ar": "فشل في تحميل المهام غير المتزامنة: {{error}}",
        "ru": "Не удалось загрузить асинхронные задачи: {{error}}"
    },
    "async_task_list_summary": {
        "en": "📊 Summary: {{total}} tasks (✅ {{completed}} completed, ⚡ {{running}} running, ❌ {{failed}} failed)",
        "zh": "📊 汇总: {{total}} 个任务 (✅ {{completed}} 已完成, ⚡ {{running}} 运行中, ❌ {{failed}} 失败)",
        "ja": "📊 概要: {{total}} タスク (✅ {{completed}} 完了, ⚡ {{running}} 実行中, ❌ {{failed}} 失敗)",
        "ar": "📊 الملخص: {{total}} مهمة (✅ {{completed}} مكتملة, ⚡ {{running}} تعمل, ❌ {{failed}} فشلت)",
        "ru": "📊 Сводка: {{total}} задач (✅ {{completed}} завершено, ⚡ {{running}} выполняется, ❌ {{failed}} неудача)"
    },
    "async_task_table_id": {
        "en": "Task ID",
        "zh": "任务ID",
        "ja": "タスクID",
        "ar": "معرف المهمة",
        "ru": "ID задачи"
    },
    "async_task_table_status": {
        "en": "Status",
        "zh": "状态",
        "ja": "ステータス",
        "ar": "الحالة",
        "ru": "Статус"
    },
    "async_task_table_model": {
        "en": "Model",
        "zh": "模型",
        "ja": "モデル",
        "ar": "النموذج",
        "ru": "Модель"
    },
    "async_task_table_created": {
        "en": "Created",
        "zh": "创建时间",
        "ja": "作成時刻",
        "ar": "وقت الإنشاء",
        "ru": "Создано"
    },
    "async_task_table_query": {
        "en": "Query Preview",
        "zh": "查询预览",
        "ja": "クエリプレビュー",
        "ar": "معاينة الاستعلام",
        "ru": "Предварительный просмотр запроса"
    },
    "async_task_table_log": {
        "en": "Log File",
        "zh": "日志文件",
        "ja": "ログファイル",
        "ar": "ملف السجل",
        "ru": "Лог-файл"
    },
    "async_task_status_completed": {
        "en": "✅ Completed",
        "zh": "✅ 已完成",
        "ja": "✅ 完了",
        "ar": "✅ مكتمل",
        "ru": "✅ Завершено"
    },
    "async_task_status_running": {
        "en": "⚡ Running",
        "zh": "⚡ 运行中",
        "ja": "⚡ 実行中",
        "ar": "⚡ يعمل",
        "ru": "⚡ Выполняется"
    },
    "async_task_status_failed": {
        "en": "❌ Failed",
        "zh": "❌ 失败",
        "ja": "❌ 失敗",
        "ar": "❌ فشل",
        "ru": "❌ Неудача"
    },
    "async_task_detail_param_error": {
        "en": "❌ Parameter Error",
        "zh": "❌ 参数错误",
        "ja": "❌ パラメータエラー",
        "ar": "❌ خطأ في المعلمة",
        "ru": "❌ Ошибка параметра"
    },
    "async_task_detail_usage": {
        "en": "Usage: [cyan]/auto async task <task_id>[/cyan]\\nor: [cyan]/auto task <task_id>[/cyan]\\n\\nUse [yellow]/auto async list[/yellow] to view all tasks",
        "zh": "用法: [cyan]/auto async task <task_id>[/cyan]\\n或: [cyan]/auto task <task_id>[/cyan]\\n\\n使用 [yellow]/auto async list[/yellow] 查看所有任务",
        "ja": "使用法: [cyan]/auto async task <task_id>[/cyan]\\nまたは: [cyan]/auto task <task_id>[/cyan]\\n\\n[yellow]/auto async list[/yellow] で全タスクを表示",
        "ar": "الاستخدام: [cyan]/auto async task <task_id>[/cyan]\\nأو: [cyan]/auto task <task_id>[/cyan]\\n\\nاستخدم [yellow]/auto async list[/yellow] لعرض جميع المهام",
        "ru": "Использование: [cyan]/auto async task <task_id>[/cyan]\\nили: [cyan]/auto task <task_id>[/cyan]\\n\\nИспользуйте [yellow]/auto async list[/yellow] для просмотра всех задач"
    },
    "async_task_detail_not_found": {
        "en": "Task not found: [red]{{task_id}}[/red]\\n\\nUse [yellow]/auto async list[/yellow] to view available tasks",
        "zh": "未找到任务: [red]{{task_id}}[/red]\\n\\n使用 [yellow]/auto async list[/yellow] 查看可用任务",
        "ja": "タスクが見つかりません: [red]{{task_id}}[/red]\\n\\n[yellow]/auto async list[/yellow] で利用可能なタスクを表示",
        "ar": "المهمة غير موجودة: [red]{{task_id}}[/red]\\n\\nاستخدم [yellow]/auto async list[/yellow] لعرض المهام المتاحة",
        "ru": "Задача не найдена: [red]{{task_id}}[/red]\\n\\nИспользуйте [yellow]/auto async list[/yellow] для просмотра доступных задач"
    },
    "async_task_detail_title": {
        "en": "🔍 Task Details",
        "zh": "🔍 任务详情",
        "ja": "🔍 タスクの詳細",
        "ar": "🔍 تفاصيل المهمة",
        "ru": "🔍 Детали задачи"
    },
    "async_task_detail_load_error": {
        "en": "Failed to load task details: {{error}}",
        "zh": "加载任务详情失败: {{error}}",
        "ja": "タスクの詳細の読み込みに失敗しました: {{error}}",
        "ar": "فشل في تحميل تفاصيل المهمة: {{error}}",
        "ru": "Не удалось загрузить детали задачи: {{error}}"
    },
    "async_task_field_id": {
        "en": "Task ID",
        "zh": "任务ID",
        "ja": "タスクID",
        "ar": "معرف المهمة",
        "ru": "ID задачи"
    },
    "async_task_field_status": {
        "en": "Status",
        "zh": "状态",
        "ja": "ステータス",
        "ar": "الحالة",
        "ru": "Статус"
    },
    "async_task_field_model": {
        "en": "Model",
        "zh": "模型",
        "ja": "モデル",
        "ar": "النموذج",
        "ru": "Модель"
    },
    "async_task_field_split_mode": {
        "en": "Split Mode",
        "zh": "分割模式",
        "ja": "分割モード",
        "ar": "وضع التقسيم",
        "ru": "Режим разбиения"
    },
    "async_task_field_created": {
        "en": "Created",
        "zh": "创建时间",
        "ja": "作成時刻",
        "ar": "وقت الإنشاء",
        "ru": "Создано"
    },
    "async_task_field_completed": {
        "en": "Completed",
        "zh": "完成时间",
        "ja": "完了時刻",
        "ar": "وقت الاكتمال",
        "ru": "Завершено"
    },
    "async_task_field_duration": {
        "en": "Duration",
        "zh": "执行耗时",
        "ja": "実行時間",
        "ar": "مدة التنفيذ",
        "ru": "Продолжительность"
    },
    "async_task_field_bg_mode": {
        "en": "Background Mode",
        "zh": "后台运行",
        "ja": "バックグラウンドモード",
        "ar": "وضع الخلفية",
        "ru": "Фоновый режим"
    },
    "async_task_field_pr_mode": {
        "en": "Create PR",
        "zh": "创建PR",
        "ja": "PR作成",
        "ar": "إنشاء PR",
        "ru": "Создать PR"
    },
    "async_task_panel_query": {
        "en": "💬 User Query",
        "zh": "💬 用户查询",
        "ja": "💬 ユーザークエリ",
        "ar": "💬 استعلام المستخدم",
        "ru": "💬 Запрос пользователя"
    },
    "async_task_panel_paths": {
        "en": "📁 Path Information",
        "zh": "📁 路径信息",
        "ja": "📁 パス情報",
        "ar": "📁 معلومات المسار",
        "ru": "📁 Информация о пути"
    },
    "async_task_panel_execution": {
        "en": "🎯 Execution Results",
        "zh": "🎯 执行结果",
        "ja": "🎯 実行結果",
        "ar": "🎯 نتائج التنفيذ",
        "ru": "🎯 Результаты выполнения"
    },
    "async_task_panel_error": {
        "en": "❌ Error Information",
        "zh": "❌ 错误信息",
        "ja": "❌ エラー情報",
        "ar": "❌ معلومات الخطأ",
        "ru": "❌ Информация об ошибке"
    },
    "async_task_field_worktree_path": {
        "en": "Worktree Path",
        "zh": "Worktree路径",
        "ja": "Worktreeパス",
        "ar": "مسار Worktree",
        "ru": "Путь Worktree"
    },
    "async_task_field_original_path": {
        "en": "Original Path",
        "zh": "原始项目路径",
        "ja": "元のプロジェクトパス",
        "ar": "المسار الأصلي",
        "ru": "Исходный путь"
    },
    "async_task_field_log_file": {
        "en": "Log File",
        "zh": "日志文件",
        "ja": "ログファイル",
        "ar": "ملف السجل",
        "ru": "Лог-файл"
    },
    "async_task_field_success": {
        "en": "Success",
        "zh": "执行成功",
        "ja": "実行成功",
        "ar": "التنفيذ الناجح",
        "ru": "Успешное выполнение"
    },
    "async_task_field_output_preview": {
        "en": "Output Preview",
        "zh": "输出预览",
        "ja": "出力プレビュー",
        "ar": "معاينة الإخراج",
        "ru": "Предварительный просмотр вывода"
    },
    "async_task_field_error_preview": {
        "en": "Error Preview",
        "zh": "错误预览",
        "ja": "エラープレビュー",
        "ar": "معاينة الخطأ",
        "ru": "Предварительный просмотр ошибки"
    },
    "async_task_field_error_details": {
        "en": "Error Details",
        "zh": "错误详情",
        "ja": "エラーの詳細",
        "ar": "تفاصيل الخطأ",
        "ru": "Детали ошибки"
    },
    "async_task_operation_hints": {
        "en": "💡 Useful Operations",
        "zh": "💡 实用操作",
        "ja": "💡 便利な操作",
        "ar": "💡 العمليات المفيدة",
        "ru": "💡 Полезные операции"
    },
    "async_task_hint_view_log": {
        "en": "View full log: [cyan]cat {{log_file}}[/cyan]",
        "zh": "查看完整日志: [cyan]cat {{log_file}}[/cyan]",
        "ja": "完全なログを表示: [cyan]cat {{log_file}}[/cyan]",
        "ar": "عرض السجل الكامل: [cyan]cat {{log_file}}[/cyan]",
        "ru": "Просмотр полного лога: [cyan]cat {{log_file}}[/cyan]"
    },
    "async_task_hint_enter_worktree": {
        "en": "Enter work directory: [cyan]cd {{worktree_path}}[/cyan]",
        "zh": "进入工作目录: [cyan]cd {{worktree_path}}[/cyan]",
        "ja": "作業ディレクトリに入る: [cyan]cd {{worktree_path}}[/cyan]",
        "ar": "دخول دليل العمل: [cyan]cd {{worktree_path}}[/cyan]",
        "ru": "Войти в рабочий каталог: [cyan]cd {{worktree_path}}[/cyan]"
    },
    "async_task_hint_back_to_list": {
        "en": "Back to task list: [cyan]/auto async list[/cyan]",
        "zh": "返回任务列表: [cyan]/auto async list[/cyan]",
        "ja": "タスクリストに戻る: [cyan]/auto async list[/cyan]",
        "ar": "العودة إلى قائمة المهام: [cyan]/auto async list[/cyan]",
        "ru": "Вернуться к списку задач: [cyan]/auto async list[/cyan]"
    },
    "async_task_value_yes": {
        "en": "Yes",
        "zh": "是",
        "ja": "はい",
        "ar": "نعم",
        "ru": "Да"
    },
    "async_task_value_no": {
        "en": "No",
        "zh": "否",
        "ja": "いいえ",
        "ar": "لا",
        "ru": "Нет"
    },
    "async_task_value_running": {
        "en": "Still running...",
        "zh": "仍在运行中...",
        "ja": "まだ実行中...",
        "ar": "ما زال قيد التشغيل...",
        "ru": "Все еще выполняется..."
    },
    "async_task_duration_format": {
        "en": "{{duration}} seconds",
        "zh": "{{duration}} 秒",
        "ja": "{{duration}} 秒",
        "ar": "{{duration}} ثانية",
        "ru": "{{duration}} секунд"
    },
} 