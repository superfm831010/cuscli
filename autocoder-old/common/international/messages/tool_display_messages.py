"""
Tool display messages for internationalization
Contains all messages used by the tool display functionality
"""

TOOL_DISPLAY_MESSAGES = {
    # Tool display templates
    "tool_display.read_file": {
        "en": "[bold cyan]{{ path }}[/]",
        "zh": "[bold cyan]{{ path }}[/]",
        "ja": "[bold cyan]{{ path }}[/]",
        "ar": "[bold cyan]{{ path }}[/]",
        "ru": "[bold cyan]{{ path }}[/]"
    },
    "tool_display.write_to_file": {
        "en": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]Content Snippet:[/dim]\n{{ content_snippet }}{{ ellipsis }}"
        ),
        "zh": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]内容片段：[/dim]\n{{ content_snippet }}{{ ellipsis }}"
        ),
        "ja": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]コンテンツスニペット：[/dim]\n{{ content_snippet }}{{ ellipsis }}"
        ),
        "ar": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]مقتطف المحتوى:[/dim]\n{{ content_snippet }}{{ ellipsis }}"
        ),
        "ru": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]Фрагмент содержимого:[/dim]\n{{ content_snippet }}{{ ellipsis }}"
        )
    },
    "tool_display.replace_in_file": {
        "en": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]Diff Snippet:[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "zh": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]差异片段：[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "ja": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]差分スニペット：[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "ar": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]مقتطف الفرق:[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "ru": (
            "[bold cyan]{{ path }}[/]\n\n"
            "[dim]Фрагмент различий:[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        )
    },
    "tool_display.execute_command": {
        "en": (
            "[bold yellow]{{ command }}[/]\n"
            "[dim](Requires Approval: {{ requires_approval }})[/]"
        ),
        "zh": (
            "[bold yellow]{{ command }}[/]\n"
            "[dim](需要批准：{{ requires_approval }})[/]"
        ),
        "ja": (
            "[bold yellow]{{ command }}[/]\n"
            "[dim](承認が必要：{{ requires_approval }})[/]"
        ),
        "ar": (
            "[bold yellow]{{ command }}[/]\n"
            "[dim](يتطلب الموافقة: {{ requires_approval }})[/]"
        ),
        "ru": (
            "[bold yellow]{{ command }}[/]\n"
            "[dim](Требует одобрения: {{ requires_approval }})[/]"
        )
    },
    "tool_display.list_files": {
        "en": (
            "[bold green]{{ path }}[/] "
            "{{ recursive_text }}"
        ),
        "zh": (
            "[bold green]{{ path }}[/] "
            "{{ recursive_text }}"
        ),
        "ja": (
            "[bold green]{{ path }}[/] "
            "{{ recursive_text }}"
        ),
        "ar": (
            "[bold green]{{ path }}[/] "
            "{{ recursive_text }}"
        ),
        "ru": (
            "[bold green]{{ path }}[/] "
            "{{ recursive_text }}"
        )
    },
    "tool_display.search_files": {
        "en": (
            "[bold green]{{ path }}[/]\n"
            "[dim]File Pattern:[/dim] [yellow]{{ file_pattern }}[/]\n"
            "[dim]Regex:[/dim] [yellow]{{ regex }}[/]"
        ),
        "zh": (
            "[bold green]{{ path }}[/]\n"
            "[dim]文件模式：[/dim] [yellow]{{ file_pattern }}[/]\n"
            "[dim]正则表达式：[/dim] [yellow]{{ regex }}[/]"
        ),
        "ja": (
            "[bold green]{{ path }}[/]\n"
            "[dim]ファイルパターン：[/dim] [yellow]{{ file_pattern }}[/]\n"
            "[dim]正規表現：[/dim] [yellow]{{ regex }}[/]"
        ),
        "ar": (
            "[bold green]{{ path }}[/]\n"
            "[dim]نمط الملف:[/dim] [yellow]{{ file_pattern }}[/]\n"
            "[dim]تعبير منتظم:[/dim] [yellow]{{ regex }}[/]"
        ),
        "ru": (
            "[bold green]{{ path }}[/]\n"
            "[dim]Шаблон файла:[/dim] [yellow]{{ file_pattern }}[/]\n"
            "[dim]Регулярное выражение:[/dim] [yellow]{{ regex }}[/]"
        )
    },
    "tool_display.list_code_definition_names": {
        "en": "[bold green]{{ path }}[/]",
        "zh": "[bold green]{{ path }}[/]",
        "ja": "[bold green]{{ path }}[/]",
        "ar": "[bold green]{{ path }}[/]",
        "ru": "[bold green]{{ path }}[/]"
    },
    "tool_display.ask_followup_question": {
        "en": (
            "[bold magenta]{{ question }}[/]\n"
            "{{ options_text }}"
        ),
        "zh": (
            "[bold magenta]{{ question }}[/]\n"
            "{{ options_text }}"
        ),
        "ja": (
            "[bold magenta]{{ question }}[/]\n"
            "{{ options_text }}"
        ),
        "ar": (
            "[bold magenta]{{ question }}[/]\n"
            "{{ options_text }}"
        ),
        "ru": (
            "[bold magenta]{{ question }}[/]\n"
            "{{ options_text }}"
        )
    },
    "tool_display.use_mcp": {
        "en": (
            "[dim]Server:[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]Tool:[/dim] [blue]{{ tool_name }}[/]\n"
            "[dim]Args:[/dim] {{ arguments_snippet }}{{ ellipsis }}"
        ),
        "zh": (
            "[dim]服务器：[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]工具：[/dim] [blue]{{ tool_name }}[/]\n"
            "[dim]参数：[/dim] {{ arguments_snippet }}{{ ellipsis }}"
        ),
        "ja": (
            "[dim]サーバー：[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]ツール：[/dim] [blue]{{ tool_name }}[/]\n"
            "[dim]引数：[/dim] {{ arguments_snippet }}{{ ellipsis }}"
        ),
        "ar": (
            "[dim]الخادم:[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]الأداة:[/dim] [blue]{{ tool_name }}[/]\n"
            "[dim]المعاملات:[/dim] {{ arguments_snippet }}{{ ellipsis }}"
        ),
        "ru": (
            "[dim]Сервер:[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]Инструмент:[/dim] [blue]{{ tool_name }}[/]\n"
            "[dim]Аргументы:[/dim] {{ arguments_snippet }}{{ ellipsis }}"
        )
    },
    "tool_display.use_rag": {
        "en": (
            "[dim]Server:[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]Query:[/dim] {{ query }}"
        ),
        "zh": (
            "[dim]服务器：[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]查询：[/dim] {{ query }}"
        ),
        "ja": (
            "[dim]サーバー：[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]クエリ：[/dim] {{ query }}"
        ),
        "ar": (
            "[dim]الخادم:[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]الاستعلام:[/dim] {{ query }}"
        ),
        "ru": (
            "[dim]Сервер:[/dim] [blue]{{ server_name }}[/]\n"
            "[dim]Запрос:[/dim] {{ query }}"
        )
    },
    "tool_display.ac_mod_read": {
        "en": "[dim]Module Path:[/dim] [green]{{ path }}[/]",
        "zh": "[dim]模块路径：[/dim] [green]{{ path }}[/]",
        "ja": "[dim]モジュールパス：[/dim] [green]{{ path }}[/]",
        "ar": "[dim]مسار الوحدة:[/dim] [green]{{ path }}[/]",
        "ru": "[dim]Путь модуля:[/dim] [green]{{ path }}[/]"
    },
    "tool_display.ac_mod_write": {
        "en": (
            "[dim]Module Path:[/dim] [green]{{ path }}[/]\n"
            "[dim]Changes:[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "zh": (
            "[dim]模块路径：[/dim] [green]{{ path }}[/]\n"
            "[dim]更改内容：[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "ja": (
            "[dim]モジュールパス：[/dim] [green]{{ path }}[/]\n"
            "[dim]変更内容：[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "ar": (
            "[dim]مسار الوحدة:[/dim] [green]{{ path }}[/]\n"
            "[dim]التغييرات:[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        ),
        "ru": (
            "[dim]Путь модуля:[/dim] [green]{{ path }}[/]\n"
            "[dim]Изменения:[/dim]\n{{ diff_snippet }}{{ ellipsis }}"
        )
    },
    "tool_display.ac_mod_list": {
        "en": "{{ search_text }}",
        "zh": "{{ search_text }}",
        "ja": "{{ search_text }}",
        "ar": "{{ search_text }}",
        "ru": "{{ search_text }}"
    },
    "tool_display.count_tokens": {
        "en": (
            "[dim]Path:[/dim] [green]{{ path }}[/]\n"
            "[dim]Recursive:[/dim] {{ recursive_text }}\n"
            "[dim]Include Summary:[/dim] {{ summary_text }}"
        ),
        "zh": (
            "[dim]路径：[/dim] [green]{{ path }}[/]\n"
            "[dim]递归：[/dim] {{ recursive_text }}\n"
            "[dim]包含汇总：[/dim] {{ summary_text }}"
        ),
        "ja": (
            "[dim]パス：[/dim] [green]{{ path }}[/]\n"
            "[dim]再帰的：[/dim] {{ recursive_text }}\n"
            "[dim]サマリーを含む：[/dim] {{ summary_text }}"
        ),
        "ar": (
            "[dim]المسار:[/dim] [green]{{ path }}[/]\n"
            "[dim]تكراري:[/dim] {{ recursive_text }}\n"
            "[dim]تضمين الملخص:[/dim] {{ summary_text }}"
        ),
        "ru": (
            "[dim]Путь:[/dim] [green]{{ path }}[/]\n"
            "[dim]Рекурсивно:[/dim] {{ recursive_text }}\n"
            "[dim]Включить сводку:[/dim] {{ summary_text }}"
        )
    },
    "tool_display.todo_read": {
        "en": "[dim]📝 Checking task progress and status[/dim]",
        "zh": "[dim]📝 检查任务进度和状态[/dim]",
        "ja": "[dim]📝 タスクの進捗と状態を確認中[/dim]",
        "ar": "[dim]📝 فحص تقدم المهام والحالة[/dim]",
        "ru": "[dim]📝 Проверка прогресса и статуса задач[/dim]"
    },
    "tool_display.todo_write": {
        "en": (
            "{{ task_details }}"
            "{{ notes_text }}"
        ),
        "zh": (
            "{{ task_details }}"
            "{{ notes_text }}"
        ),
        "ja": (
            "{{ task_details }}"
            "{{ notes_text }}"
        ),
        "ar": (
            "{{ task_details }}"
            "{{ notes_text }}"
        ),
        "ru": (
            "{{ task_details }}"
            "{{ notes_text }}"
        )
    },
    "tool_display.session_start": {
        "en": (
            "[bold cyan]{{ command }}[/]\n"
            "{{ timeout_text }}{{ cwd_text }}{{ env_text }}"
        ),
        "zh": (
            "[bold cyan]{{ command }}[/]\n"
            "{{ timeout_text }}{{ cwd_text }}{{ env_text }}"
        ),
        "ja": (
            "[bold cyan]{{ command }}[/]\n"
            "{{ timeout_text }}{{ cwd_text }}{{ env_text }}"
        ),
        "ar": (
            "[bold cyan]{{ command }}[/]\n"
            "{{ timeout_text }}{{ cwd_text }}{{ env_text }}"
        ),
        "ru": (
            "[bold cyan]{{ command }}[/]\n"
            "{{ timeout_text }}{{ cwd_text }}{{ env_text }}"
        )
    },
    "tool_display.session_interactive": {
        "en": (
            "[dim]Session:[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]Input:[/dim] {{ input_snippet }}{{ ellipsis }}\n"
            "{{ prompt_text }}"
        ),
        "zh": (
            "[dim]会话：[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]输入：[/dim] {{ input_snippet }}{{ ellipsis }}\n"
            "{{ prompt_text }}"
        ),
        "ja": (
            "[dim]セッション：[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]入力：[/dim] {{ input_snippet }}{{ ellipsis }}\n"
            "{{ prompt_text }}"
        ),
        "ar": (
            "[dim]الجلسة:[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]الإدخال:[/dim] {{ input_snippet }}{{ ellipsis }}\n"
            "{{ prompt_text }}"
        ),
        "ru": (
            "[dim]Сессия:[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]Ввод:[/dim] {{ input_snippet }}{{ ellipsis }}\n"
            "{{ prompt_text }}"
        )
    },
    "tool_display.session_stop": {
        "en": (
            "[dim]Session:[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]Force Stop:[/dim] {{ force_text }}"
        ),
        "zh": (
            "[dim]会话：[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]强制停止：[/dim] {{ force_text }}"
        ),
        "ja": (
            "[dim]セッション：[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]強制停止：[/dim] {{ force_text }}"
        ),
        "ar": (
            "[dim]الجلسة:[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]إيقاف قسري:[/dim] {{ force_text }}"
        ),
        "ru": (
            "[dim]Сессия:[/dim] [bold cyan]{{ session_id }}[/]\n"
            "[dim]Принудительная остановка:[/dim] {{ force_text }}"
        )
    },
    "tool_display.conversation_message_ids_read": {
        "en": "[dim]📖 Reading conversation message IDs configuration[/dim]",
        "zh": "[dim]📖 读取会话消息ID配置[/dim]",
        "ja": "[dim]📖 会話メッセージID設定を読み取り中[/dim]",
        "ar": "[dim]📖 قراءة تكوين معرفات رسائل المحادثة[/dim]",
        "ru": "[dim]📖 Чтение конфигурации ID сообщений диалога[/dim]"
    },
    "tool_display.conversation_message_ids_write": {
        "en": (
            "[dim]Action:[/dim] [yellow]{{ action }}[/]\n"
            "[dim]Message IDs:[/dim] {{ message_ids_snippet }}{{ ellipsis }}"
        ),
        "zh": (
            "[dim]操作：[/dim] [yellow]{{ action }}[/]\n"
            "[dim]消息ID：[/dim] {{ message_ids_snippet }}{{ ellipsis }}"
        ),
        "ja": (
            "[dim]アクション：[/dim] [yellow]{{ action }}[/]\n"
            "[dim]メッセージID：[/dim] {{ message_ids_snippet }}{{ ellipsis }}"
        ),
        "ar": (
            "[dim]الإجراء:[/dim] [yellow]{{ action }}[/]\n"
            "[dim]معرفات الرسائل:[/dim] {{ message_ids_snippet }}{{ ellipsis }}"
        ),
        "ru": (
            "[dim]Действие:[/dim] [yellow]{{ action }}[/]\n"
            "[dim]ID сообщений:[/dim] {{ message_ids_snippet }}{{ ellipsis }}"
        )
    },
    "tool_display.run_named_subagents": {
        "en": (
            "[dim]Execution Mode:[/dim] [yellow]{{ execution_mode }}[/]\n"
            "[dim]Number of Subagents:[/dim] {{ subagent_count }}\n"
            "{{ subagent_details }}"
        ),
        "zh": (
            "[dim]执行模式：[/dim] [yellow]{{ execution_mode }}[/]\n"
            "[dim]子代理数量：[/dim] {{ subagent_count }}\n"
            "{{ subagent_details }}"
        ),
        "ja": (
            "[dim]実行モード：[/dim] [yellow]{{ execution_mode }}[/]\n"
            "[dim]サブエージェント数：[/dim] {{ subagent_count }}\n"
            "{{ subagent_details }}"
        ),
        "ar": (
            "[dim]وضع التنفيذ:[/dim] [yellow]{{ execution_mode }}[/]\n"
            "[dim]عدد الوكلاء الفرعيين:[/dim] {{ subagent_count }}\n"
            "{{ subagent_details }}"
        ),
        "ru": (
            "[dim]Режим выполнения:[/dim] [yellow]{{ execution_mode }}[/]\n"
            "[dim]Количество подагентов:[/dim] {{ subagent_count }}\n"
            "{{ subagent_details }}"
        )
    },

    # Tool titles
    "tool_title.read_file": {
        "en": "AutoCoder wants to read a file",
        "zh": "AutoCoder 想要读取文件",
        "ja": "AutoCoder がファイルを読み取りたいです",
        "ar": "AutoCoder يريد قراءة ملف",
        "ru": "AutoCoder хочет прочитать файл"
    },
    "tool_title.write_to_file": {
        "en": "AutoCoder wants to write to a file",
        "zh": "AutoCoder 想要写入文件",
        "ja": "AutoCoder がファイルに書き込みたいです",
        "ar": "AutoCoder يريد الكتابة في ملف",
        "ru": "AutoCoder хочет записать в файл"
    },
    "tool_title.replace_in_file": {
        "en": "AutoCoder wants to replace content in a file",
        "zh": "AutoCoder 想要替换文件内容",
        "ja": "AutoCoder がファイルの内容を置き換えたいです",
        "ar": "AutoCoder يريد استبدال محتوى في ملف",
        "ru": "AutoCoder хочет заменить содержимое в файле"
    },
    "tool_title.execute_command": {
        "en": "AutoCoder wants to execute a command",
        "zh": "AutoCoder 想要执行命令",
        "ja": "AutoCoder がコマンドを実行したいです",
        "ar": "AutoCoder يريد تنفيذ أمر",
        "ru": "AutoCoder хочет выполнить команду"
    },
    "tool_title.list_files": {
        "en": "AutoCoder wants to list files",
        "zh": "AutoCoder 想要列出文件",
        "ja": "AutoCoder がファイルを一覧表示したいです",
        "ar": "AutoCoder يريد إدراج الملفات",
        "ru": "AutoCoder хочет вывести список файлов"
    },
    "tool_title.search_files": {
        "en": "AutoCoder wants to search files",
        "zh": "AutoCoder 想要搜索文件",
        "ja": "AutoCoder がファイルを検索したいです",
        "ar": "AutoCoder يريد البحث في الملفات",
        "ru": "AutoCoder хочет найти файлы"
    },
    "tool_title.list_code_definition_names": {
        "en": "AutoCoder wants to list code definitions",
        "zh": "AutoCoder 想要列出代码定义",
        "ja": "AutoCoder がコード定義を一覧表示したいです",
        "ar": "AutoCoder يريد إدراج تعريفات الكود",
        "ru": "AutoCoder хочет вывести определения кода"
    },
    "tool_title.ask_followup_question": {
        "en": "AutoCoder is asking a question",
        "zh": "AutoCoder 正在提问",
        "ja": "AutoCoder が質問をしています",
        "ar": "AutoCoder يطرح سؤالاً",
        "ru": "AutoCoder задает вопрос"
    },
    "tool_title.use_mcp": {
        "en": "AutoCoder wants to use an MCP tool",
        "zh": "AutoCoder 想要使用 MCP 工具",
        "ja": "AutoCoder がMCPツールを使用したいです",
        "ar": "AutoCoder يريد استخدام أداة MCP",
        "ru": "AutoCoder хочет использовать инструмент MCP"
    },
    "tool_title.use_rag": {
        "en": "AutoCoder wants to search knowledge base",
        "zh": "AutoCoder 想要搜索知识库",
        "ja": "AutoCoder がナレッジベースを検索したいです",
        "ar": "AutoCoder يريد البحث في قاعدة المعرفة",
        "ru": "AutoCoder хочет найти в базе знаний"
    },
    "tool_title.ac_mod_read": {
        "en": "AutoCoder wants to read an AC Module",
        "zh": "AutoCoder 想要读取 AC 模块",
        "ja": "AutoCoder がACモジュールを読み取りたいです",
        "ar": "AutoCoder يريد قراءة وحدة AC",
        "ru": "AutoCoder хочет прочитать AC модуль"
    },
    "tool_title.ac_mod_write": {
        "en": "AutoCoder wants to write an AC Module",
        "zh": "AutoCoder 想要编写 AC 模块",
        "ja": "AutoCoder がACモジュールを書きたいです",
        "ar": "AutoCoder يريد كتابة وحدة AC",
        "ru": "AutoCoder хочет написать AC модуль"
    },
    "tool_title.ac_mod_list": {
        "en": "AutoCoder wants to list AC Modules",
        "zh": "AutoCoder 想要列出 AC 模块",
        "ja": "AutoCoder がACモジュールを一覧表示したいです",
        "ar": "AutoCoder يريد إدراج وحدات AC",
        "ru": "AutoCoder хочет вывести список AC модулей"
    },
    "tool_title.count_tokens": {
        "en": "AutoCoder wants to count tokens",
        "zh": "AutoCoder 想要统计 Token 数量",
        "ja": "AutoCoder がトークンを数えたいです",
        "ar": "AutoCoder يريد عد الرموز المميزة",
        "ru": "AutoCoder хочет подсчитать токены"
    },
    "tool_title.todo_read": {
        "en": "AutoCoder wants to read the todo list",
        "zh": "AutoCoder 想要读取待办事项列表",
        "ja": "AutoCoder がTODOリストを読み取りたいです",
        "ar": "AutoCoder يريد قراءة قائمة المهام",
        "ru": "AutoCoder хочет прочитать список задач"
    },
    "tool_title.todo_write": {
        "en": "AutoCoder wants to manage todo list",
        "zh": "AutoCoder 想要管理待办事项",
        "ja": "AutoCoder がTODOリストを管理したいです",
        "ar": "AutoCoder يريد إدارة قائمة المهام",
        "ru": "AutoCoder хочет управлять списком задач"
    },
    "tool_title.session_start": {
        "en": "AutoCoder wants to start an interactive session",
        "zh": "AutoCoder 想要启动交互式会话",
        "ja": "AutoCoder がインタラクティブセッションを開始したいです",
        "ar": "AutoCoder يريد بدء جلسة تفاعلية",
        "ru": "AutoCoder хочет запустить интерактивную сессию"
    },
    "tool_title.session_interactive": {
        "en": "AutoCoder wants to interact with session",
        "zh": "AutoCoder 想要与会话交互",
        "ja": "AutoCoder がセッションと相互作用したいです",
        "ar": "AutoCoder يريد التفاعل مع الجلسة",
        "ru": "AutoCoder хочет взаимодействовать с сессией"
    },
    "tool_title.session_stop": {
        "en": "AutoCoder wants to stop interactive session",
        "zh": "AutoCoder 想要停止交互式会话",
        "ja": "AutoCoder がインタラクティブセッションを停止したいです",
        "ar": "AutoCoder يريد إيقاف الجلسة التفاعلية",
        "ru": "AutoCoder хочет остановить интерактивную сессию"
    },
    "tool_title.conversation_message_ids_read": {
        "en": "AutoCoder wants to read conversation message IDs",
        "zh": "AutoCoder 想要读取会话消息ID",
        "ja": "AutoCoder が会話メッセージIDを読み取りたいです",
        "ar": "AutoCoder يريد قراءة معرفات رسائل المحادثة",
        "ru": "AutoCoder хочет прочитать ID сообщений диалога"
    },
    "tool_title.conversation_message_ids_write": {
        "en": "AutoCoder wants to manage conversation message IDs",
        "zh": "AutoCoder 想要管理会话消息ID",
        "ja": "AutoCoder が会話メッセージIDを管理したいです",
        "ar": "AutoCoder يريد إدارة معرفات رسائل المحادثة",
        "ru": "AutoCoder хочет управлять ID сообщений диалога"
    },
    "tool_title.run_named_subagents": {
        "en": "AutoCoder wants to run named subagents",
        "zh": "AutoCoder 想要运行指定的子代理",
        "ja": "AutoCoder が名前付きサブエージェントを実行したいです",
        "ar": "AutoCoder يريد تشغيل الوكلاء الفرعيين المسمين",
        "ru": "AutoCoder хочет запустить именованных подагентов"
    },

    # TodoWriteTool action-specific titles
    "tool_title.todo_write.create": {
        "en": "AutoCoder wants to create a new todo list",
        "zh": "AutoCoder 想要创建新的待办事项列表",
        "ja": "AutoCoder が新しいTODOリストを作成したいです",
        "ar": "AutoCoder يريد إنشاء قائمة مهام جديدة",
        "ru": "AutoCoder хочет создать новый список задач"
    },
    "tool_title.todo_write.add_task": {
        "en": "AutoCoder wants to add a new task",
        "zh": "AutoCoder 想要添加新任务",
        "ja": "AutoCoder が新しいタスクを追加したいです",
        "ar": "AutoCoder يريد إضافة مهمة جديدة",
        "ru": "AutoCoder хочет добавить новую задачу"
    },
    "tool_title.todo_write.update": {
        "en": "AutoCoder wants to update a task",
        "zh": "AutoCoder 想要更新任务",
        "ja": "AutoCoder がタスクを更新したいです",
        "ar": "AutoCoder يريد تحديث مهمة",
        "ru": "AutoCoder хочет обновить задачу"
    },
    "tool_title.todo_write.mark_progress": {
        "en": "AutoCoder wants to mark a task as in progress",
        "zh": "AutoCoder 想要标记任务为进行中",
        "ja": "AutoCoder がタスクを進行中としてマークしたいです",
        "ar": "AutoCoder يريد تمييز مهمة كقيد التنفيذ",
        "ru": "AutoCoder хочет отметить задачу как выполняемую"
    },
    "tool_title.todo_write.mark_completed": {
        "en": "AutoCoder wants to mark a task as completed",
        "zh": "AutoCoder 想要标记任务为已完成",
        "ja": "AutoCoder がタスクを完了としてマークしたいです",
        "ar": "AutoCoder يريد تمييز مهمة كمكتملة",
        "ru": "AutoCoder хочет отметить задачу как завершенную"
    },

    # Tool result titles - success
    "tool_result.todo_write.success": {
        "en": "Todo list updated successfully",
        "zh": "待办事项更新成功",
        "ja": "TODOリストが正常に更新されました",
        "ar": "تم تحديث قائمة المهام بنجاح",
        "ru": "Список задач успешно обновлен"
    },
    "tool_result.todo_read.success": {
        "en": "Todo list retrieved successfully",
        "zh": "待办事项获取成功",
        "ja": "TODOリストが正常に取得されました",
        "ar": "تم استرداد قائمة المهام بنجاح",
        "ru": "Список задач успешно получен"
    },
    "tool_result.read_file.success": {
        "en": "File read successfully",
        "zh": "文件读取成功",
        "ja": "ファイルが正常に読み取られました",
        "ar": "تم قراءة الملف بنجاح",
        "ru": "Файл успешно прочитан"
    },
    "tool_result.write_to_file.success": {
        "en": "File written successfully",
        "zh": "文件写入成功",
        "ja": "ファイルが正常に書き込まれました",
        "ar": "تم كتابة الملف بنجاح",
        "ru": "Файл успешно записан"
    },
    "tool_result.replace_in_file.success": {
        "en": "File content replaced successfully",
        "zh": "文件内容替换成功",
        "ja": "ファイルの内容が正常に置き換えられました",
        "ar": "تم استبدال محتوى الملف بنجاح",
        "ru": "Содержимое файла успешно заменено"
    },
    "tool_result.execute_command.success": {
        "en": "Command executed successfully",
        "zh": "命令执行成功",
        "ja": "コマンドが正常に実行されました",
        "ar": "تم تنفيذ الأمر بنجاح",
        "ru": "Команда успешно выполнена"
    },
    "tool_result.list_files.success": {
        "en": "Files listed successfully",
        "zh": "文件列表获取成功",
        "ja": "ファイルが正常に一覧表示されました",
        "ar": "تم إدراج الملفات بنجاح",
        "ru": "Файлы успешно перечислены"
    },
    "tool_result.search_files.success": {
        "en": "File search completed successfully",
        "zh": "文件搜索完成",
        "ja": "ファイル検索が正常に完了しました",
        "ar": "تم البحث في الملفات بنجاح",
        "ru": "Поиск файлов успешно завершен"
    },
    "tool_result.list_code_definition_names.success": {
        "en": "Code definitions listed successfully",
        "zh": "代码定义列表获取成功",
        "ja": "コード定義が正常に一覧表示されました",
        "ar": "تم إدراج تعريفات الكود بنجاح",
        "ru": "Определения кода успешно перечислены"
    },
    "tool_result.ask_followup_question.success": {
        "en": "Question asked successfully",
        "zh": "问题提出成功",
        "ja": "質問が正常に投稿されました",
        "ar": "تم طرح السؤال بنجاح",
        "ru": "Вопрос успешно задан"
    },
    "tool_result.use_mcp.success": {
        "en": "MCP tool executed successfully",
        "zh": "MCP 工具执行成功",
        "ja": "MCPツールが正常に実行されました",
        "ar": "تم تنفيذ أداة MCP بنجاح",
        "ru": "Инструмент MCP успешно выполнен"
    },
    "tool_result.use_rag.success": {
        "en": "Knowledge base search completed",
        "zh": "知识库搜索完成",
        "ja": "ナレッジベース検索が完了しました",
        "ar": "تم البحث في قاعدة المعرفة",
        "ru": "Поиск в базе знаний завершен"
    },
    "tool_result.ac_mod_read.success": {
        "en": "AC Module read successfully",
        "zh": "AC 模块读取成功",
        "ja": "ACモジュールが正常に読み取られました",
        "ar": "تم قراءة وحدة AC بنجاح",
        "ru": "AC модуль успешно прочитан"
    },
    "tool_result.ac_mod_write.success": {
        "en": "AC Module updated successfully",
        "zh": "AC 模块更新成功",
        "ja": "ACモジュールが正常に更新されました",
        "ar": "تم تحديث وحدة AC بنجاح",
        "ru": "AC модуль успешно обновлен"
    },
    "tool_result.ac_mod_list.success": {
        "en": "AC Modules listed successfully",
        "zh": "AC 模块列表获取成功",
        "ja": "ACモジュールが正常に一覧表示されました",
        "ar": "تم إدراج وحدات AC بنجاح",
        "ru": "AC модули успешно перечислены"
    },
    "tool_result.count_tokens.success": {
        "en": "Token count completed",
        "zh": "Token 统计完成",
        "ja": "トークン数の計算が完了しました",
        "ar": "تم عد الرموز المميزة",
        "ru": "Подсчет токенов завершен"
    },
    "tool_result.session_start.success": {
        "en": "Interactive session started successfully",
        "zh": "交互式会话启动成功",
        "ja": "インタラクティブセッションが正常に開始されました",
        "ar": "تم بدء الجلسة التفاعلية بنجاح",
        "ru": "Интерактивная сессия успешно запущена"
    },
    "tool_result.session_interactive.success": {
        "en": "Interactive session interaction completed",
        "zh": "交互式会话交互完成",
        "ja": "インタラクティブセッションの相互作用が完了しました",
        "ar": "تم التفاعل مع الجلسة التفاعلية",
        "ru": "Взаимодействие с интерактивной сессией завершено"
    },
    "tool_result.session_stop.success": {
        "en": "Interactive session stopped successfully",
        "zh": "交互式会话停止成功",
        "ja": "インタラクティブセッションが正常に停止されました",
        "ar": "تم إيقاف الجلسة التفاعلية بنجاح",
        "ru": "Интерактивная сессия успешно остановлена"
    },
    "tool_result.conversation_message_ids_read.success": {
        "en": "Conversation message IDs retrieved successfully",
        "zh": "会话消息ID读取成功",
        "ja": "会話メッセージIDが正常に取得されました",
        "ar": "تم استرداد معرفات رسائل المحادثة بنجاح",
        "ru": "ID сообщений диалога успешно получены"
    },
    "tool_result.conversation_message_ids_write.success": {
        "en": "Conversation message IDs updated successfully",
        "zh": "会话消息ID更新成功",
        "ja": "会話メッセージIDが正常に更新されました",
        "ar": "تم تحديث معرفات رسائل المحادثة بنجاح",
        "ru": "ID сообщений диалога успешно обновлены"
    },
    "tool_result.run_named_subagents.success": {
        "en": "Subagents executed successfully",
        "zh": "子代理执行成功",
        "ja": "サブエージェントが正常に実行されました",
        "ar": "تم تنفيذ الوكلاء الفرعيين بنجاح",
        "ru": "Подагенты успешно выполнены"
    },

    # Tool result titles - failure
    "tool_result.todo_write.failure": {
        "en": "Failed to update todo list",
        "zh": "待办事项更新失败",
        "ja": "TODOリストの更新に失敗しました",
        "ar": "فشل في تحديث قائمة المهام",
        "ru": "Не удалось обновить список задач"
    },
    "tool_result.todo_read.failure": {
        "en": "Failed to retrieve todo list",
        "zh": "待办事项获取失败",
        "ja": "TODOリストの取得に失敗しました",
        "ar": "فشل في استرداد قائمة المهام",
        "ru": "Не удалось получить список задач"
    },
    "tool_result.read_file.failure": {
        "en": "Failed to read file",
        "zh": "文件读取失败",
        "ja": "ファイルの読み取りに失敗しました",
        "ar": "فشل في قراءة الملف",
        "ru": "Не удалось прочитать файл"
    },
    "tool_result.write_to_file.failure": {
        "en": "Failed to write file",
        "zh": "文件写入失败",
        "ja": "ファイルの書き込みに失敗しました",
        "ar": "فشل في كتابة الملف",
        "ru": "Не удалось записать файл"
    },
    "tool_result.replace_in_file.failure": {
        "en": "Failed to replace file content",
        "zh": "文件内容替换失败",
        "ja": "ファイルの内容の置き換えに失敗しました",
        "ar": "فشل في استبدال محتوى الملف",
        "ru": "Не удалось заменить содержимое файла"
    },
    "tool_result.execute_command.failure": {
        "en": "Command execution failed",
        "zh": "命令执行失败",
        "ja": "コマンドの実行に失敗しました",
        "ar": "فشل في تنفيذ الأمر",
        "ru": "Не удалось выполнить команду"
    },
    "tool_result.list_files.failure": {
        "en": "Failed to list files",
        "zh": "文件列表获取失败",
        "ja": "ファイルの一覧表示に失敗しました",
        "ar": "فشل في إدراج الملفات",
        "ru": "Не удалось перечислить файлы"
    },
    "tool_result.search_files.failure": {
        "en": "File search failed",
        "zh": "文件搜索失败",
        "ja": "ファイル検索に失敗しました",
        "ar": "فشل في البحث في الملفات",
        "ru": "Поиск файлов не удался"
    },
    "tool_result.list_code_definition_names.failure": {
        "en": "Failed to list code definitions",
        "zh": "代码定义列表获取失败",
        "ja": "コード定義の一覧表示に失敗しました",
        "ar": "فشل في إدراج تعريفات الكود",
        "ru": "Не удалось перечислить определения кода"
    },
    "tool_result.ask_followup_question.failure": {
        "en": "Failed to ask question",
        "zh": "问题提出失败",
        "ja": "質問の投稿に失敗しました",
        "ar": "فشل في طرح السؤال",
        "ru": "Не удалось задать вопрос"
    },
    "tool_result.use_mcp.failure": {
        "en": "MCP tool execution failed",
        "zh": "MCP 工具执行失败",
        "ja": "MCPツールの実行に失敗しました",
        "ar": "فشل في تنفيذ أداة MCP",
        "ru": "Не удалось выполнить инструмент MCP"
    },
    "tool_result.use_rag.failure": {
        "en": "Knowledge base search failed",
        "zh": "知识库搜索失败",
        "ja": "ナレッジベース検索に失敗しました",
        "ar": "فشل في البحث في قاعدة المعرفة",
        "ru": "Поиск в базе знаний не удался"
    },
    "tool_result.ac_mod_read.failure": {
        "en": "Failed to read AC Module",
        "zh": "AC 模块读取失败",
        "ja": "ACモジュールの読み取りに失敗しました",
        "ar": "فشل في قراءة وحدة AC",
        "ru": "Не удалось прочитать AC модуль"
    },
    "tool_result.ac_mod_write.failure": {
        "en": "Failed to update AC Module",
        "zh": "AC 模块更新失败",
        "ja": "ACモジュールの更新に失敗しました",
        "ar": "فشل في تحديث وحدة AC",
        "ru": "Не удалось обновить AC модуль"
    },
    "tool_result.ac_mod_list.failure": {
        "en": "Failed to list AC Modules",
        "zh": "AC 模块列表获取失败",
        "ja": "ACモジュールの一覧表示に失敗しました",
        "ar": "فشل في إدراج وحدات AC",
        "ru": "Не удалось перечислить AC модули"
    },
    "tool_result.count_tokens.failure": {
        "en": "Token count failed",
        "zh": "Token 统计失败",
        "ja": "トークン数の計算に失敗しました",
        "ar": "فشل في عد الرموز المميزة",
        "ru": "Подсчет токенов не удался"
    },
    "tool_result.session_start.failure": {
        "en": "Interactive session start failed",
        "zh": "交互式会话启动失败",
        "ja": "インタラクティブセッションの開始に失敗しました",
        "ar": "فشل في بدء الجلسة التفاعلية",
        "ru": "Не удалось запустить интерактивную сессию"
    },
    "tool_result.session_interactive.failure": {
        "en": "Interactive session interaction failed",
        "zh": "交互式会话交互失败",
        "ja": "インタラクティブセッションの相互作用に失敗しました",
        "ar": "فشل في التفاعل مع الجلسة التفاعلية",
        "ru": "Взаимодействие с интерактивной сессией не удалось"
    },
    "tool_result.session_stop.failure": {
        "en": "Interactive session stop failed",
        "zh": "交互式会话停止失败",
        "ja": "インタラクティブセッションの停止に失敗しました",
        "ar": "فشل في إيقاف الجلسة التفاعلية",
        "ru": "Не удалось остановить интерактивную сессию"
    },
    "tool_result.conversation_message_ids_read.failure": {
        "en": "Failed to read conversation message IDs",
        "zh": "会话消息ID读取失败",
        "ja": "会話メッセージIDの読み取りに失敗しました",
        "ar": "فشل في قراءة معرفات رسائل المحادثة",
        "ru": "Не удалось прочитать ID сообщений диалога"
    },
    "tool_result.conversation_message_ids_write.failure": {
        "en": "Failed to update conversation message IDs",
        "zh": "会话消息ID更新失败",
        "ja": "会話メッセージIDの更新に失敗しました",
        "ar": "فشل في تحديث معرفات رسائل المحادثة",
        "ru": "Не удалось обновить ID сообщений диалога"
    },
    "tool_result.run_named_subagents.failure": {
        "en": "Subagents execution failed",
        "zh": "子代理执行失败",
        "ja": "サブエージェントの実行に失敗しました",
        "ar": "فشل في تنفيذ الوكلاء الفرعيين",
        "ru": "Не удалось выполнить подагентов"
    },

    # Generic fallback messages
    "tool_result.success_generic": {
        "en": "Operation completed successfully",
        "zh": "操作成功完成",
        "ja": "操作が正常に完了しました",
        "ar": "تمت العملية بنجاح",
        "ru": "Операция успешно завершена"
    },
    "tool_result.failure_generic": {
        "en": "Operation failed",
        "zh": "操作执行失败",
        "ja": "操作に失敗しました",
        "ar": "فشلت العملية",
        "ru": "Операция не удалась"
    },
    "tool_display.unknown_tool": {
        "en": "Unknown tool type: {{tool_type}}\nData: {{data}}",
        "zh": "未知工具类型: {{tool_type}}\n数据: {{data}}",
        "ja": "不明なツールタイプ: {{tool_type}}\nデータ: {{data}}",
        "ar": "نوع أداة غير معروف: {{tool_type}}\nالبيانات: {{data}}",
        "ru": "Неизвестный тип инструмента: {{tool_type}}\nДанные: {{data}}"
    },
    "tool_display.template_not_found": {
        "en": "Tool display template not found",
        "zh": "工具显示模板未找到",
        "ja": "ツール表示テンプレートが見つかりません",
        "ar": "لم يتم العثور على قالب عرض الأداة",
        "ru": "Шаблон отображения инструмента не найден"
    },
    "tool_display.format_error": {
        "en": "Error formatting {{tool_type}} display: {{error}}\nTemplate: {{template}}\nContext: {{context}}",
        "zh": "格式化 {{tool_type}} 的显示时出错: {{error}}\n模板: {{template}}\n上下文: {{context}}",
        "ja": "{{tool_type}}表示のフォーマットエラー: {{error}}\nテンプレート: {{template}}\nコンテキスト: {{context}}",
        "ar": "خطأ في تنسيق عرض {{tool_type}}: {{error}}\nالقالب: {{template}}\nالسياق: {{context}}",
        "ru": "Ошибка форматирования отображения {{tool_type}}: {{error}}\nШаблон: {{template}}\nКонтекст: {{context}}"
    },

    # Utility texts used in tool display
    "tool_text.recursive": {
        "en": "(Recursively)",
        "zh": "（递归）",
        "ja": "（再帰的）",
        "ar": "（تكراري）",
        "ru": "（Рекурсивно）"
    },
    "tool_text.top_level": {
        "en": "(Top Level)",
        "zh": "（顶层）",
        "ja": "（トップレベル）",
        "ar": "（المستوى الأعلى）",
        "ru": "（Верхний уровень）"
    },
    "tool_text.options": {
        "en": "Options:",
        "zh": "选项：",
        "ja": "オプション：",
        "ar": "الخيارات:",
        "ru": "Опции:"
    },
    "tool_text.search_path": {
        "en": "Search Path:",
        "zh": "搜索路径：",
        "ja": "検索パス：",
        "ar": "مسار البحث:",
        "ru": "Путь поиска:"
    },
    "tool_text.project_root": {
        "en": "Project Root",
        "zh": "项目根目录",
        "ja": "プロジェクトルート",
        "ar": "جذر المشروع",
        "ru": "Корень проекта"
    },
    "tool_text.all": {
        "en": "(All)",
        "zh": "（全部）",
        "ja": "（すべて）",
        "ar": "（الكل）",
        "ru": "（Все）"
    },
    "tool_text.yes": {
        "en": "Yes",
        "zh": "是",
        "ja": "はい",
        "ar": "نعم",
        "ru": "Да"
    },
    "tool_text.no": {
        "en": "No",
        "zh": "否",
        "ja": "いいえ",
        "ar": "لا",
        "ru": "Нет"
    },
    "tool_text.tasks_to_create": {
        "en": "Tasks to create:",
        "zh": "要创建的任务：",
        "ja": "作成するタスク：",
        "ar": "المهام التي سيتم إنشاؤها:",
        "ru": "Задачи для создания:"
    },
    "tool_text.task_id": {
        "en": "Task ID:",
        "zh": "任务ID：",
        "ja": "タスクID：",
        "ar": "معرف المهمة:",
        "ru": "ID задачи:"
    },
    "tool_text.content": {
        "en": "Content:",
        "zh": "内容：",
        "ja": "コンテンツ：",
        "ar": "المحتوى:",
        "ru": "Содержимое:"
    },
    "tool_text.priority": {
        "en": "Priority:",
        "zh": "优先级：",
        "ja": "優先度：",
        "ar": "الأولوية:",
        "ru": "Приоритет:"
    },
    "tool_text.status": {
        "en": "Status:",
        "zh": "状态：",
        "ja": "ステータス：",
        "ar": "الحالة:",
        "ru": "Статус:"
    },
    "tool_text.notes": {
        "en": "Notes:",
        "zh": "备注：",
        "ja": "メモ：",
        "ar": "الملاحظات:",
        "ru": "Заметки:"
    },
    "tool_text.total_tasks": {
        "en": "Total tasks:",
        "zh": "总任务数：",
        "ja": "総タスク数：",
        "ar": "إجمالي المهام:",
        "ru": "Всего задач:"
    },
    "tool_text.timeout": {
        "en": "Timeout:",
        "zh": "超时时间：",
        "ja": "タイムアウト：",
        "ar": "انتهاء المهلة:",
        "ru": "Таймаут:"
    },
    "tool_text.working_directory": {
        "en": "Working Directory:",
        "zh": "工作目录：",
        "ja": "作業ディレクトリ：",
        "ar": "مجلد العمل:",
        "ru": "Рабочая директория:"
    },
    "tool_text.environment_variables": {
        "en": "Environment Variables:",
        "zh": "环境变量：",
        "ja": "環境変数：",
        "ar": "متغيرات البيئة:",
        "ru": "Переменные окружения:"
    },
    "tool_text.variables": {
        "en": "variables",
        "zh": "个变量",
        "ja": "変数",
        "ar": "متغيرات",
        "ru": "переменных"
    },
    "tool_text.expected_prompt": {
        "en": "Expected Prompt:",
        "zh": "期待提示符：",
        "ja": "期待されるプロンプト：",
        "ar": "المطالبة المتوقعة:",
        "ru": "Ожидаемый промпт:"
    },
    "tool_text.agent": {
        "en": "Agent",
        "zh": "代理",
        "ja": "エージェント",
        "ar": "الوكيل",
        "ru": "Агент"
    },
    "tool_text.task": {
        "en": "Task",
        "zh": "任务",
        "ja": "タスク",
        "ar": "المهمة",
        "ru": "Задача"
    },
    "tool_text.and_more": {
        "en": "... and {{count}} more",
        "zh": "... 还有 {{count}} 个",
        "ja": "... 他に{{count}}個",
        "ar": "... و {{count}} أخرى",
        "ru": "... и еще {{count}}"
    },
    "tool_text.no_agents_configured": {
        "en": "No subagents configured",
        "zh": "未配置子代理",
        "ja": "サブエージェントが設定されていません",
        "ar": "لا يوجد وكلاء فرعيين مكونين",
        "ru": "Подагенты не настроены"
    },
    "tool_text.raw_config": {
        "en": "Raw config",
        "zh": "原始配置",
        "ja": "生設定",
        "ar": "التكوين الخام",
        "ru": "Сырая конфигурация"
    },
    "tool_text.unknown": {
        "en": "unknown",
        "zh": "未知",
        "ja": "不明",
        "ar": "غير معروف",
        "ru": "неизвестно"
    },

    # Priority and status translations
    "tool_text.priority.high": {
        "en": "high",
        "zh": "高",
        "ja": "高",
        "ar": "عالي",
        "ru": "высокий"
    },
    "tool_text.priority.medium": {
        "en": "medium",
        "zh": "中",
        "ja": "中",
        "ar": "متوسط",
        "ru": "средний"
    },
    "tool_text.priority.low": {
        "en": "low",
        "zh": "低",
        "ja": "低",
        "ar": "منخفض",
        "ru": "низкий"
    },
    "tool_text.status.pending": {
        "en": "pending",
        "zh": "待处理",
        "ja": "保留中",
        "ar": "في الانتظار",
        "ru": "ожидающий"
    },
    "tool_text.status.in_progress": {
        "en": "in progress",
        "zh": "进行中",
        "ja": "進行中",
        "ar": "قيد التنفيذ",
        "ru": "выполняется"
    },
    "tool_text.status.completed": {
        "en": "completed",
        "zh": "已完成",
        "ja": "完了",
        "ar": "مكتمل",
        "ru": "завершено"
    },
    "tool_text.execution_mode.parallel": {
        "en": "parallel",
        "zh": "并行",
        "ja": "並列",
        "ar": "متوازي",
        "ru": "параллельный"
    },
    "tool_text.execution_mode.serial": {
        "en": "serial",
        "zh": "串行",
        "ja": "直列",
        "ar": "متسلسل",
        "ru": "последовательный"
    },
    "tool_text.execution_mode.unknown": {
        "en": "unknown",
        "zh": "未知",
        "ja": "不明",
        "ar": "غير معروف",
        "ru": "неизвестный"
    },

    # Agent thinking notice - displayed when token pruning occurs
    "agent_thinking_notice": {
        "en": "🤔 The AI agent is deeply thinking and reasoning, this may take some time. Please be patient...",
        "zh": "🤔 AI 智能体正在深度思考和推理，这可能需要一些时间，请耐心等待...",
        "ja": "🤔 AIエージェントは深く思考・推論中です。しばらくお待ちください...",
        "ar": "🤔 يفكر الوكيل الذكي بعمق ويستدل، قد يستغرق هذا بعض الوقت. يرجى التحلي بالصبر...",
        "ru": "🤔 ИИ-агент глубоко размышляет и рассуждает, это может занять некоторое время. Пожалуйста, будьте терпеливы..."
    }
} 