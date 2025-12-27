"""
Chat auto-coder messages for internationalization
Contains all messages used by the chat auto-coder interface
"""

CHAT_AUTO_CODER_MESSAGES = {
    "auto_command_analyzing": {
        "en": "Analyzing Command Request",
        "zh": "正在分析命令请求",
        "ja": "コマンドリクエストを分析中",
        "ar": "تحليل طلب الأمر",
        "ru": "Анализ запроса команды",
    },
    "mcp_remove_error": {
        "en": "Error removing MCP server: {{error}}",
        "zh": "移除 MCP 服务器时出错:{{error}}",
        "ja": "MCPサーバーの削除エラー: {{error}}",
        "ar": "خطأ في إزالة خادم MCP: {{error}}",
        "ru": "Ошибка удаления MCP сервера: {{error}}",
    },
    "mcp_remove_success": {
        "en": "Successfully removed MCP server: {{result}}",
        "zh": "成功移除 MCP 服务器：{{result}}",
        "ja": "MCPサーバーを正常に削除しました: {{result}}",
        "ar": "تم حذف خادم MCP بنجاح: {{result}}",
        "ru": "MCP сервер успешно удален: {{result}}",
    },
    "mcp_list_running_error": {
        "en": "Error listing running MCP servers: {{error}}",
        "zh": "列出运行中的 MCP 服务器时出错：{{error}}",
        "ja": "実行中のMCPサーバーのリスト表示エラー: {{error}}",
        "ar": "خطأ في إدراج خوادم MCP قيد التشغيل: {{error}}",
        "ru": "Ошибка при получении списка работающих MCP серверов: {{error}}",
    },
    "mcp_list_running_title": {
        "en": "Running MCP servers:",
        "zh": "正在运行的 MCP 服务器：",
        "ja": "実行中のMCPサーバー:",
        "ar": "خوادم MCP قيد التشغيل:",
        "ru": "Работающие MCP серверы:",
    },
    "mcp_list_builtin_error": {
        "en": "Error listing builtin MCP servers: {{error}}",
        "zh": "列出内置 MCP 服务器时出错：{{error}}",
        "ja": "内蔵MCPサーバーのリスト表示エラー: {{error}}",
        "ar": "خطأ في إدراج خوادم MCP المدمجة: {{error}}",
        "ru": "Ошибка при получении списка встроенных MCP серверов: {{error}}",
    },
    "mcp_list_builtin_title": {
        "en": "Available builtin MCP servers:",
        "zh": "可用的内置 MCP 服务器：",
        "ja": "利用可能な内蔵MCPサーバー:",
        "ar": "خوادم MCP المدمجة المتاحة:",
        "ru": "Доступные встроенные MCP серверы:",
    },
    "mcp_list_external_title": {
        "en": "Available external MCP servers:",
        "zh": "可用的外部 MCP 服务器：",
        "ja": "利用可能な外部MCPサーバー:",
        "ar": "خوادم MCP الخارجية المتاحة:",
        "ru": "Доступные внешние MCP серверы:",
    },
    "mcp_list_marketplace_title": {
        "en": "Available marketplace MCP servers:",
        "zh": "可用的市场 MCP 服务器：",
        "ja": "利用可能なマーケットプレイスMCPサーバー:",
        "ar": "خوادم MCP المتاحة في السوق:",
        "ru": "Доступные MCP серверы из маркетплейса:",
    },
    "mcp_refresh_error": {
        "en": "Error refreshing MCP servers: {{error}}",
        "zh": "刷新 MCP 服务器时出错：{{error}}",
        "ja": "MCPサーバーの更新エラー: {{error}}",
        "ar": "خطأ في تحديث خوادم MCP: {{error}}",
        "ru": "Ошибка обновления MCP серверов: {{error}}",
    },
    "mcp_refresh_success": {
        "en": "Successfully refreshed MCP servers",
        "zh": "成功刷新 MCP 服务器",
        "ja": "MCPサーバーを正常に更新しました",
        "ar": "تم تحديث خوادم MCP بنجاح",
        "ru": "MCP серверы успешно обновлены",
    },
    "mcp_install_error": {
        "en": "Error installing MCP server: {{error}}",
        "zh": "安装 MCP 服务器时出错：{{error}}",
        "ja": "MCPサーバーのインストールエラー: {{error}}",
        "ar": "خطأ في تثبيت خادم MCP: {{error}}",
        "ru": "Ошибка установки MCP сервера: {{error}}",
    },
    "mcp_install_success": {
        "en": "Successfully installed MCP server: {{result}}",
        "zh": "成功安装 MCP 服务器：{{result}}",
        "ja": "MCPサーバーを正常にインストールしました: {{result}}",
        "ar": "تم تثبيت خادم MCP بنجاح: {{result}}",
        "ru": "MCP сервер успешно установлен: {{result}}",
    },
    "mcp_query_empty": {
        "en": "Please enter your query.",
        "zh": "请输入您的查询。",
        "ja": "クエリを入力してください。",
        "ar": "يرجى إدخال استفسارك.",
        "ru": "Пожалуйста, введите ваш запрос.",
    },
    "mcp_error_title": {
        "en": "Error",
        "zh": "错误",
        "ja": "エラー",
        "ar": "خطأ",
        "ru": "Ошибка",
    },
    "mcp_response_title": {
        "en": "MCP Response",
        "zh": "MCP 响应",
        "ja": "MCP応答",
        "ar": "استجابة MCP",
        "ru": "Ответ MCP",
    },
    "initializing": {
        "en": "🚀 Initializing system...",
        "zh": "🚀 正在初始化系统...",
        "ja": "🚀 システムを初期化中...",
        "ar": "🚀 تهيئة النظام...",
        "ru": "🚀 Инициализация системы...",
    },
    "not_initialized": {
        "en": "The current directory is not initialized as an auto-coder project.",
        "zh": "当前目录未初始化为auto-coder项目。",
        "ja": "現在のディレクトリはauto-coderプロジェクトとして初期化されていません。",
        "ar": "الدليل الحالي غير مهيأ كمشروع auto-coder.",
        "ru": "Текущий каталог не инициализирован как проект auto-coder.",
    },
    "init_prompt": {
        "en": "Do you want to initialize the project now? (y/n): ",
        "zh": "是否现在初始化项目？(y/n): ",
        "ja": "今すぐプロジェクトを初期化しますか？ (y/n): ",
        "ar": "هل تريد تهيئة المشروع الآن؟ (y/n): ",
        "ru": "Хотите инициализировать проект сейчас? (y/n): ",
    },
    "init_success": {
        "en": "Project initialized successfully.",
        "zh": "项目初始化成功。",
        "ja": "プロジェクトの初期化に成功しました。",
        "ar": "تم تهيئة المشروع بنجاح.",
        "ru": "Проект успешно инициализирован.",
    },
    "init_fail": {
        "en": "Failed to initialize the project.",
        "zh": "项目初始化失败。",
        "ja": "プロジェクトの初期化に失敗しました。",
        "ar": "فشلت تهيئة المشروع.",
        "ru": "Не удалось инициализировать проект.",
    },
    "init_manual": {
        "en": "Please try manually: auto-coder init --source_dir .",
        "zh": "请尝试手动初始化：auto-coder init --source_dir .",
        "ja": "手動で実行してください: auto-coder init --source_dir .",
        "ar": "يرجى المحاولة يدوياً: auto-coder init --source_dir .",
        "ru": "Попробуйте выполнить вручную: auto-coder init --source_dir .",
    },
    "exit_no_init": {
        "en": "Exiting without initialization.",
        "zh": "退出而不初始化。",
        "ja": "初期化せずに終了します。",
        "ar": "الخروج دون تهيئة.",
        "ru": "Выход без инициализации.",
    },
    "created_dir": {
        "en": "Created directory: {{path}}",
        "zh": "创建目录：{{path}}",
        "ja": "ディレクトリを作成しました: {{path}}",
        "ar": "تم إنشاء الدليل: {{path}}",
        "ru": "Создан каталог: {{path}}",
    },
    "init_complete": {
        "en": "Project initialization completed.",
        "zh": "项目初始化完成。",
        "ja": "プロジェクトの初期化が完了しました。",
        "ar": "اكتملت تهيئة المشروع.",
        "ru": "Инициализация проекта завершена.",
    },
    "checking_ray": {
        "en": "Checking Ray status...",
        "zh": "正在检查Ray状态...",
        "ja": "Rayのステータスを確認中...",
        "ar": "التحقق من حالة Ray...",
        "ru": "Проверка статуса Ray...",
    },
    "ray_not_running": {
        "en": "Ray is not running. Starting Ray...",
        "zh": "Ray未运行。正在启动Ray...",
        "ja": "Rayが実行されていません。Rayを起動中...",
        "ar": "Ray غير قيد التشغيل. بدء تشغيل Ray...",
        "ru": "Ray не запущен. Запуск Ray...",
    },
    "ray_start_success": {
        "en": "Ray started successfully.",
        "zh": "Ray启动成功。",
        "ja": "Rayが正常に起動しました。",
        "ar": "تم بدء تشغيل Ray بنجاح.",
        "ru": "Ray успешно запущен.",
    },
    "ray_start_fail": {
        "en": "Failed to start Ray. Please start it manually.",
        "zh": "Ray启动失败。请手动启动。",
        "ja": "Rayの起動に失敗しました。手動で起動してください。",
        "ar": "فشل في بدء تشغيل Ray. يرجى البدء يدوياً.",
        "ru": "Не удалось запустить Ray. Пожалуйста, запустите вручную.",
    },
    "ray_running": {
        "en": "Ray is already running.",
        "zh": "Ray已经在运行。",
        "ja": "Rayはすでに実行中です。",
        "ar": "Ray قيد التشغيل بالفعل.",
        "ru": "Ray уже запущен.",
    },
    "checking_model": {
        "en": "Checking deepseek_chat model availability...",
        "zh": "正在检查deepseek_chat模型可用性...",
        "ja": "deepseek_chatモデルの可用性を確認中...",
        "ar": "التحقق من توفر نموذج deepseek_chat...",
        "ru": "Проверка доступности модели deepseek_chat...",
    },
    "model_available": {
        "en": "deepseek_chat model is available.",
        "zh": "deepseek_chat模型可用。",
        "ja": "deepseek_chatモデルが利用可能です。",
        "ar": "نموذج deepseek_chat متاح.",
        "ru": "Модель deepseek_chat доступна.",
    },
    "model_timeout": {
        "en": "Command timed out. deepseek_chat model might not be available.",
        "zh": "命令超时。deepseek_chat模型可能不可用。",
        "ja": "コマンドがタイムアウトしました。deepseek_chatモデルが利用できない可能性があります。",
        "ar": "انتهت مهلة الأمر. قد لا يكون نموذج deepseek_chat متاحاً.",
        "ru": "Истекло время выполнения команды. Модель deepseek_chat может быть недоступна.",
    },
    "model_error": {
        "en": "Error occurred while checking deepseek_chat model.",
        "zh": "检查deepseek_chat模型时出错。",
        "ja": "deepseek_chatモデルの確認中にエラーが発生しました。",
        "ar": "حدث خطأ أثناء التحقق من نموذج deepseek_chat.",
        "ru": "Произошла ошибка при проверке модели deepseek_chat.",
    },
    "model_not_available": {
        "en": "deepseek_chat model is not available.",
        "zh": "deepseek_chat模型不可用。",
        "ja": "deepseek_chatモデルは利用できません。",
        "ar": "نموذج deepseek_chat غير متاح.",
        "ru": "Модель deepseek_chat недоступна.",
    },
    "provider_selection": {
        "en": "Select a provider for deepseek_chat model:",
        "zh": "为deepseek_chat模型选择一个提供商：",
        "ja": "deepseek_chatモデルのプロバイダーを選択してください:",
        "ar": "اختر مزود لنموذج deepseek_chat:",
        "ru": "Выберите провайдера для модели deepseek_chat:",
    },
    "no_provider": {
        "en": "No provider selected. Exiting initialization.",
        "zh": "未选择提供商。退出初始化。",
        "ja": "プロバイダーが選択されていません。初期化を終了します。",
        "ar": "لم يتم اختيار مزود. الخروج من التهيئة.",
        "ru": "Провайдер не выбран. Выход из инициализации.",
    },
    "enter_api_key": {
        "en": "Please enter your API key（https://www.deepseek.com/）: ",
        "zh": "请输入您的API密钥（https://www.deepseek.com/）：",
        "ja": "APIキーを入力してください（https://www.deepseek.com/）: ",
        "ar": "يرجى إدخال مفتاح API الخاص بك（https://www.deepseek.com/）: ",
        "ru": "Пожалуйста, введите ваш API ключ（https://www.deepseek.com/）: ",
    },
    "deploying_model": {
        "en": "Deploying deepseek_chat model using {}...",
        "zh": "正在使用{}部署deepseek_chat模型...",
        "ja": "{}を使用してdeepseek_chatモデルをデプロイ中...",
        "ar": "نشر نموذج deepseek_chat باستخدام {}...",
        "ru": "Развертывание модели deepseek_chat с использованием {}...",
    },
    "deploy_complete": {
        "en": "Deployment completed.",
        "zh": "部署完成。",
        "ja": "デプロイが完了しました。",
        "ar": "اكتمل النشر.",
        "ru": "Развертывание завершено.",
    },
    "deploy_fail": {
        "en": "Deployment failed. Please try again or deploy manually.",
        "zh": "部署失败。请重试或手动部署。",
        "ja": "デプロイに失敗しました。再試行するか手動でデプロイしてください。",
        "ar": "فشل النشر. يرجى المحاولة مرة أخرى أو النشر يدوياً.",
        "ru": "Развертывание не удалось. Пожалуйста, попробуйте снова или разверните вручную.",
    },
    "validating_deploy": {
        "en": "Validating the deployment...",
        "zh": "正在验证部署...",
        "ja": "デプロイを検証中...",
        "ar": "التحقق من صحة النشر...",
        "ru": "Проверка развертывания...",
    },
    "validation_success": {
        "en": "Validation successful. deepseek_chat model is now available.",
        "zh": "验证成功。deepseek_chat模型现在可用。",
        "ja": "検証に成功しました。deepseek_chatモデルが利用可能になりました。",
        "ar": "نجح التحقق. نموذج deepseek_chat متاح الآن.",
        "ru": "Проверка прошла успешно. Модель deepseek_chat теперь доступна.",
    },
    "validation_fail": {
        "en": "Validation failed. The model might not be deployed correctly.",
        "zh": "验证失败。模型可能未正确部署。",
        "ja": "検証に失敗しました。モデルが正しくデプロイされていない可能性があります。",
        "ar": "فشل التحقق. قد لا يكون النموذج منشوراً بشكل صحيح.",
        "ru": "Проверка не удалась. Модель может быть развернута неправильно.",
    },
    "manual_start": {
        "en": "Please try to start the model manually using:",
        "zh": "请尝试使用以下命令手动启动模型：",
        "ja": "以下のコマンドを使用してモデルを手動で起動してください:",
        "ar": "يرجى محاولة بدء تشغيل النموذج يدوياً باستخدام:",
        "ru": "Пожалуйста, попробуйте запустить модель вручную, используя:",
    },
    "init_complete_final": {
        "en": "Initialization completed.",
        "zh": "初始化完成。",
        "ja": "初期化が完了しました。",
        "ar": "اكتملت التهيئة.",
        "ru": "Инициализация завершена.",
    },
    "project_type_config": {
        "en": "Project Type Configuration",
        "zh": "项目类型配置",
        "ja": "プロジェクトタイプ設定",
        "ar": "تكوين نوع المشروع",
        "ru": "Конфигурация типа проекта",
    },
    "project_type_supports": {
        "en": "The project_type supports:",
        "zh": "项目类型支持：",
        "ja": "プロジェクトタイプがサポートする項目:",
        "ar": "يدعم نوع المشروع:",
        "ru": "Тип проекта поддерживает:",
    },
    "language_suffixes": {
        "en": "  - Language suffixes (e.g., .py, .java, .ts)",
        "zh": "  - 语言后缀（例如：.py, .java, .ts）",
        "ja": "  - 言語の拡張子（例：.py, .java, .ts）",
        "ar": "  - لواحق اللغة (مثل .py, .java, .ts)",
        "ru": "  - Расширения языков (например, .py, .java, .ts)",
    },
    "predefined_types": {
        "en": "  - Predefined types: py (Python), ts (TypeScript/JavaScript)",
        "zh": "  - 预定义类型：py（Python）, ts（TypeScript/JavaScript）",
        "ja": "  - 定義済みタイプ: py (Python), ts (TypeScript/JavaScript)",
        "ar": "  - الأنواع المحددة مسبقاً: py (Python), ts (TypeScript/JavaScript)",
        "ru": "  - Предопределенные типы: py (Python), ts (TypeScript/JavaScript)",
    },
    "mixed_projects": {
        "en": "For mixed language projects, use comma-separated values.",
        "zh": "对于混合语言项目，使用逗号分隔的值。",
        "ja": "混合言語プロジェクトの場合は、カンマ区切りの値を使用してください。",
        "ar": "للمشاريع متعددة اللغات، استخدم قيماً مفصولة بفواصل.",
        "ru": "Для проектов со смешанными языками используйте значения, разделенные запятыми.",
    },
    "examples": {
        "en": "Examples: '.java,.scala' or '.py,.ts'",
        "zh": "示例：'.java,.scala' 或 '.py,.ts'",
        "ja": "例: '.java,.scala' または '.py,.ts'",
        "ar": "أمثلة: '.java,.scala' أو '.py,.ts'",
        "ru": "Примеры: '.java,.scala' или '.py,.ts'",
    },
    "default_type": {
        "en": "Default is 'py' if left empty.",
        "zh": "如果留空，默认为 'py'。",
        "ja": "空白の場合、デフォルトは 'py' です。",
        "ar": "الافتراضي هو 'py' إذا ترك فارغاً.",
        "ru": "По умолчанию 'py', если оставить пустым.",
    },
    "enter_project_type": {
        "en": "Enter the project type: ",
        "zh": "请输入项目类型：",
        "ja": "プロジェクトタイプを入力してください: ",
        "ar": "أدخل نوع المشروع: ",
        "ru": "Введите тип проекта: ",
    },
    "project_type_set": {
        "en": "Project type set to:",
        "zh": "项目类型设置为：",
        "ja": "プロジェクトタイプが設定されました:",
        "ar": "تم تعيين نوع المشروع إلى:",
        "ru": "Тип проекта установлен как:",
    },
    "using_default_type": {
        "en": "will automatically collect extensions of code file, otherwise default to 'py'",
        "zh": "使用默认项目类型，会自动查找代码代码相关的后缀名，如果项目为空，则默认为py",
        "ja": "デフォルトのプロジェクトタイプを使用し、コードファイルの拡張子を自動的に収集します。プロジェクトが空の場合はpyがデフォルトです",
        "ar": "سيجمع امتدادات ملفات الكود تلقائياً، وإلا فالافتراضي هو 'py'",
        "ru": "автоматически соберет расширения файлов кода, иначе по умолчанию 'py'",
    },
    "change_setting_later": {
        "en": "You can change this setting later using",
        "zh": "您可以稍后使用以下命令更改此设置",
        "ja": "この設定は後で以下のコマンドで変更できます",
        "ar": "يمكنك تغيير هذا الإعداد لاحقاً باستخدام",
        "ru": "Вы можете изменить эту настройку позже, используя",
    },
    "supported_commands": {
        "en": "Supported commands:",
        "zh": "支持的命令：",
        "ja": "サポートされているコマンド:",
        "ar": "الأوامر المدعومة:",
        "ru": "Поддерживаемые команды:",
    },
    "commands": {
        "en": "Commands",
        "zh": "命令",
        "ja": "コマンド",
        "ar": "الأوامر",
        "ru": "Команды",
    },
    "description": {
        "en": "Description",
        "zh": "描述",
        "ja": "説明",
        "ar": "الوصف",
        "ru": "Описание",
    },
    "add_files_desc": {
        "en": "Add files to the current session",
        "zh": "将文件添加到当前会话",
        "ja": "現在のセッションにファイルを追加",
        "ar": "إضافة ملفات إلى الجلسة الحالية",
        "ru": "Добавить файлы в текущую сессию",
    },
    "remove_files_desc": {
        "en": "Remove files from the current session",
        "zh": "从当前会话中移除文件",
        "ja": "現在のセッションからファイルを削除",
        "ar": "إزالة ملفات من الجلسة الحالية",
        "ru": "Удалить файлы из текущей сессии",
    },
    "chat_desc": {
        "en": "Chat with the AI about the current active files to get insights",
        "zh": "与AI聊天，获取关于当前活动文件的见解",
        "ja": "現在のアクティブファイルについてAIとチャットして洞察を得る",
        "ar": "الدردشة مع الذكاء الاصطناعي حول الملفات النشطة الحالية للحصول على رؤى",
        "ru": "Чат с ИИ о текущих активных файлах для получения инсайтов",
    },
    "coding_desc": {
        "en": "Request the AI to modify code based on requirements",
        "zh": "根据需求请求AI修改代码",
        "ja": "要件に基づいてAIにコードの修正を依頼",
        "ar": "طلب من الذكاء الاصطناعي تعديل الكود بناءً على المتطلبات",
        "ru": "Попросить ИИ изменить код на основе требований",
    },
    "ask_desc": {
        "en": "Ask the AI any questions or get insights about the current project, without modifying code",
        "zh": "向AI提问或获取关于当前项目的见解，不修改代码",
        "ja": "現在のプロジェクトについてAIに質問や洞察を求める（コード修正なし）",
        "ar": "اسأل الذكاء الاصطناعي أي أسئلة أو احصل على رؤى حول المشروع الحالي، دون تعديل الكود",
        "ru": "Задавать ИИ вопросы или получать инсайты о текущем проекте без изменения кода",
    },
    "summon_desc": {
        "en": "Summon the AI to perform complex tasks using the auto_tool agent",
        "zh": "召唤AI使用auto_tool代理执行复杂任务",
        "ja": "auto_toolエージェントを使用して複雑なタスクを実行するようAIを召喚",
        "ar": "استدعاء الذكاء الاصطناعي لأداء مهام معقدة باستخدام وكيل auto_tool",
        "ru": "Вызвать ИИ для выполнения сложных задач с использованием агента auto_tool",
    },
    "revert_desc": {
        "en": "Revert commits from last coding chat",
        "zh": "撤销上次代码聊天的提交",
        "ja": "最後のコーディングチャットからのコミットを取り消し",
        "ar": "التراجع عن التزامات من آخر محادثة برمجة",
        "ru": "Отменить коммиты из последнего чата кодирования",
    },
    "conf_desc": {
        "en": "Set configuration. Use /conf project_type:<type> to set project type for indexing",
        "zh": "设置配置。使用 /conf project_type:<type> 设置索引的项目类型",
        "ja": "設定を行う。/conf project_type:<type> を使用してインデックス用のプロジェクトタイプを設定",
        "ar": "تعيين التكوين. استخدم /conf project_type:<type> لتعيين نوع المشروع للفهرسة",
        "ru": "Настроить конфигурацию. Используйте /conf project_type:<type> для установки типа проекта для индексации",
    },
    "index_query_desc": {
        "en": "Query the project index",
        "zh": "查询项目索引",
        "ja": "プロジェクトインデックスを検索",
        "ar": "استعلام فهرس المشروع",
        "ru": "Запросить индекс проекта",
    },
    "index_build_desc": {
        "en": "Trigger building the project index",
        "zh": "触发构建项目索引",
        "ja": "プロジェクトインデックスの構築をトリガー",
        "ar": "تشغيل بناء فهرس المشروع",
        "ru": "Запустить построение индекса проекта",
    },
    "list_files_desc": {
        "en": "List all active files in the current session",
        "zh": "列出当前会话中的所有活动文件",
        "ja": "現在のセッション内のすべてのアクティブファイルをリスト",
        "ar": "إدراج جميع الملفات النشطة في الجلسة الحالية",
        "ru": "Список всех активных файлов в текущей сессии",
    },
    "help_desc": {
        "en": "Show this help message",
        "zh": "显示此帮助消息",
        "ja": "このヘルプメッセージを表示",
        "ar": "إظهار رسالة المساعدة هذه",
        "ru": "Показать это справочное сообщение",
    },
    "exclude_dirs_desc": {
        "en": "Add directories to exclude from project",
        "zh": "添加要从项目中排除的目录",
        "ja": "プロジェクトから除外するディレクトリを追加",
        "ar": "إضافة دلائل لاستبعادها من المشروع",
        "ru": "Добавить каталоги для исключения из проекта",
    },
    "shell_desc": {
        "en": "Execute a shell command or switch to shell mode",
        "zh": "执行shell命令或切换到shell模式",
        "ja": "シェルコマンドを実行またはシェルモードに切り替え",
        "ar": "تنفيذ أمر shell أو التبديل إلى وضع shell",
        "ru": "Выполнить команду shell или переключиться в режим shell",
    },
    "shell_mode_desc": {
        "en": "Shell mode - all non-command input will be executed as shell commands",
        "zh": "Shell模式 - 所有非命令输入都将作为shell命令执行",
        "ja": "シェルモード - すべての非コマンド入力はシェルコマンドとして実行されます",
        "ar": "وضع Shell - سيتم تنفيذ جميع المدخلات غير الأوامر كأوامر shell",
        "ru": "Режим Shell - все некомандные вводы будут выполнены как команды shell",
    },
    "index_export_success": {
        "en": "Successfully exported index to {{ path }}",
        "zh": "成功导出索引到 {{ path }}",
        "ja": "インデックスを {{ path }} に正常にエクスポートしました",
        "ar": "تم تصدير الفهرس بنجاح إلى {{ path }}",
        "ru": "Индекс успешно экспортирован в {{ path }}",
    },
    "index_export_fail": {
        "en": "Failed to export index to {{ path }}",
        "zh": "导出索引到 {{ path }} 失败",
        "ja": "{{ path }} へのインデックスエクスポートに失敗しました",
        "ar": "فشل في تصدير الفهرس إلى {{ path }}",
        "ru": "Не удалось экспортировать индекс в {{ path }}",
    },
    "index_import_success": {
        "en": "Successfully imported index from {{ path }}",
        "zh": "成功从 {{ path }} 导入索引",
        "ja": "{{ path }} からインデックスを正常にインポートしました",
        "ar": "تم استيراد الفهرس بنجاح من {{ path }}",
        "ru": "Индекс успешно импортирован из {{ path }}",
    },
    "index_import_fail": {
        "en": "Failed to import index from {{ path }}",
        "zh": "从 {{ path }} 导入索引失败",
        "ja": "{{ path }} からのインデックスインポートに失敗しました",
        "ar": "فشل في استيراد الفهرس من {{ path }}",
        "ru": "Не удалось импортировать индекс из {{ path }}",
    },
    "index_not_found": {
        "en": "Index file not found at {{ path }}",
        "zh": "在 {{ path }} 未找到索引文件",
        "ja": "{{ path }} でインデックスファイルが見つかりません",
        "ar": "ملف الفهرس غير موجود في {{ path }}",
        "ru": "Файл индекса не найден в {{ path }}",
    },
    "index_backup_success": {
        "en": "Backed up existing index to {{ path }}",
        "zh": "已备份现有索引到 {{ path }}",
        "ja": "既存のインデックスを {{ path }} にバックアップしました",
        "ar": "تم نسخ الفهرس الموجود احتياطياً إلى {{ path }}",
        "ru": "Существующий индекс создан резервная копия в {{ path }}",
    },
    "index_convert_path_fail": {
        "en": "Could not convert path {{ path }}",
        "zh": "无法转换路径 {{ path }}",
        "ja": "パス {{ path }} を変換できませんでした",
        "ar": "لا يمكن تحويل المسار {{ path }}",
        "ru": "Не удалось преобразовать путь {{ path }}",
    },
    "index_error": {
        "en": "Error in index operation: {{ error }}",
        "zh": "索引操作出错：{{ error }}",
        "ja": "インデックス操作でエラーが発生しました: {{ error }}",
        "ar": "خطأ في عملية الفهرس: {{ error }}",
        "ru": "Ошибка при выполнении операции индекса: {{ error }}",
    },
    "voice_input_desc": {
        "en": "Convert voice input to text",
        "zh": "将语音输入转换为文本",
        "ja": "音声入力をテキストに変換",
        "ar": "تحويل إدخال الصوت إلى نص",
        "ru": "Преобразовать голосовой ввод в текст",
    },
    "mode_desc": {
        "en": "Switch input mode",
        "zh": "切换输入模式",
        "ja": "入力モードを切り替え",
        "ar": "تبديل وضع الإدخال",
        "ru": "Переключить режим ввода",
    },
    "conf_key": {"en": "Key", "zh": "键", "ja": "キー", "ar": "المفتاح", "ru": "Ключ"},
    "conf_value": {
        "en": "Value",
        "zh": "值",
        "ja": "値",
        "ar": "القيمة",
        "ru": "Значение",
    },
    "conf_title": {
        "en": "Configuration Settings",
        "zh": "配置设置",
        "ja": "設定",
        "ar": "إعدادات التكوين",
        "ru": "Настройки конфигурации",
    },
    "conf_subtitle": {
        "en": "Use /conf <key>:<value> to modify these settings",
        "zh": "使用 /conf <key>:<value> 修改这些设置",
        "ja": "/conf <key>:<value> を使用してこれらの設定を変更してください",
        "ar": "استخدم /conf <key>:<value> لتعديل هذه الإعدادات",
        "ru": "Используйте /conf <ключ>:<значение> для изменения этих настроек",
    },
    "lib_desc": {
        "en": "Manage libraries",
        "zh": "管理库",
        "ja": "ライブラリを管理",
        "ar": "إدارة المكتبات",
        "ru": "Управление библиотеками",
    },
    "exit_desc": {
        "en": "Exit the program",
        "zh": "退出程序",
        "ja": "プログラムを終了",
        "ar": "إنهاء البرنامج",
        "ru": "Выйти из программы",
    },
    "design_desc": {
        "en": "Generate SVG image based on the provided description",
        "zh": "根据需求设计SVG图片",
        "ja": "提供された説明に基づいてSVG画像を生成",
        "ar": "إنشاء صورة SVG بناءً على الوصف المقدم",
        "ru": "Создать SVG изображение на основе предоставленного описания",
    },
    "commit_desc": {
        "en": "Auto generate yaml file and commit changes based on user's manual changes",
        "zh": "根据用户人工修改的代码自动生成yaml文件并提交更改",
        "ja": "ユーザーの手動変更に基づいてyamlファイルを自動生成し、変更をコミット",
        "ar": "إنشاء ملف yaml تلقائياً والتزام بالتغييرات بناءً على التعديلات اليدوية للمستخدم",
        "ru": "Автоматически создать yaml файл и зафиксировать изменения на основе ручных изменений пользователя",
    },
    "models_desc": {
        "en": "Manage model configurations, only available in lite mode",
        "zh": "管理模型配置，仅在lite模式下可用",
        "ja": "モデル設定を管理（liteモードでのみ利用可能）",
        "ar": "إدارة تكوينات النماذج، متاح فقط في وضع lite",
        "ru": "Управление конфигурациями моделей, доступно только в lite режиме",
    },
    "models_usage": {
        "en": """Usage: /models <command>
Available subcommands:
  provider/model <api_key> - Activate a built-in model and set its API key (recommended for quick start).
  /list [pattern]          - List all configured models (built-in + custom). Optionally filter by pattern (supports wildcards).
  /chat <model_name> <question> - Chat with a specific model to test it.
  /add_provider            - Add a custom provider. Provide parameters in 'key=value' format, e.g., name=my_model model_name=gpt-4 base_url=... api_key=...
  /remove <name>           - Remove a configured model by its name (only custom models can be removed).
  /input_price <name> <value> - Set the input price for a model (unit: Million tokens).
  /output_price <name> <value> - Set the output price for a model (unit: Million tokens).
  /speed <name> <value> - Set the average speed for a model (unit: seconds per request).
  /speed-test [<rounds>] - Test the speed of configured models. Optionally specify the number of rounds.
  /speed-test /long_context [<rounds>] - Test model speed using a long context. Optionally specify the number of rounds.""",
        "zh": """用法: /models <命令>
可用的子命令:
  provider/model <API密钥> - 激活一个内置模型并设置其 API 密钥 (推荐快速开始)。
  /list [模式]             - 列出所有已配置的模型 (包括内置和自定义)。可选择使用模式过滤 (支持通配符)。
  /chat <模型名称> <问题>  - 与指定模型对话以测试它。
  /add_provider            - 添加一个自定义 provider。参数使用 'key=value' 格式提供，例如：name=my_model model_name=gpt-4 base_url=... api_key=...
  /remove <名称>           - 根据名称移除一个已配置的模型 (仅能删除自定义模型)。
  /input_price <名称> <价格> - 设置指定模型的输入价格 (单位: 百万 Token)。
  /output_price <名称> <价格> - 设置指定模型的输出价格 (单位: 百万 Token)。
  /speed <名称> <速度> - 设置指定模型的平均速度 (单位: 秒/请求)。
  /speed-test [<轮数>] - 测试已配置模型的速度。可以指定测试轮数 (可选)。
  /speed-test /long_context [<轮数>] - 使用长文本上下文测试模型速度。可以指定测试轮数 (可选)。""",
        "ja": """使用法: /models <コマンド>
利用可能なサブコマンド:
  provider/model <APIキー> - 内蔵モデルを有効化し、APIキーを設定（クイックスタート推奨）。
  /list [パターン]         - 設定済みのすべてのモデルをリスト（内蔵 + カスタム）。オプションでパターンでフィルタ（ワイルドカード対応）。
  /chat <モデル名> <質問>  - 指定されたモデルとチャットしてテストします。
  /add_provider            - カスタムプロバイダーを追加。'key=value' 形式でパラメータを提供。例: name=my_model model_name=gpt-4 base_url=... api_key=...
  /remove <名前>           - 名前でモデルを削除（カスタムモデルのみ削除可能）。
  /input_price <名前> <価格> - モデルの入力価格を設定（単位: 百万トークン）。
  /output_price <名前> <価格> - モデルの出力価格を設定（単位: 百万トークン）。
  /speed <名前> <速度> - モデルの平均速度を設定（単位: 秒/リクエスト）。
  /speed-test [<ラウンド数>] - 設定済みモデルの速度をテスト。オプションでラウンド数を指定。
  /speed-test /long_context [<ラウンド数>] - 長いコンテキストを使用してモデル速度をテスト。オプションでラウンド数を指定。""",
        "ar": """الاستخدام: /models <الأمر>
الأوامر الفرعية المتاحة:
  provider/model <مفتاح API> - تفعيل نموذج مدمج وتعيين مفتاح API الخاص به (موصى به للبداية السريعة).
  /list [نمط]              - إدراج جميع النماذج المكونة (مدمجة + مخصصة). تصفية اختيارية بالنمط (يدعم أحرف البدل).
  /chat <اسم النموذج> <السؤال> - الدردشة مع نموذج محدد لاختباره.
  /add_provider            - إضافة مزود مخصص. قدم المعاملات بصيغة 'key=value'، مثل: name=my_model model_name=gpt-4 base_url=... api_key=...
  /remove <الاسم>          - إزالة نموذج مكون بالاسم (يمكن إزالة النماذج المخصصة فقط).
  /input_price <الاسم> <القيمة> - تعيين سعر الإدخال للنموذج (الوحدة: مليون رمز).
  /output_price <الاسم> <القيمة> - تعيين سعر الإخراج للنموذج (الوحدة: مليون رمز).
  /speed <الاسم> <القيمة> - تعيين السرعة المتوسطة للنموذج (الوحدة: ثوان لكل طلب).
  /speed-test [<الجولات>] - اختبار سرعة النماذج المكونة. حدد عدد الجولات اختيارياً.
  /speed-test /long_context [<الجولات>] - اختبار سرعة النموذج باستخدام سياق طويل. حدد عدد الجولات اختيارياً.""",
        "ru": """Использование: /models <команда>
Доступные подкоманды:
  provider/model <api_ключ> - Активировать встроенную модель и установить её API ключ (рекомендуется для быстрого старта).
  /list [шаблон]           - Список всех настроенных моделей (встроенные + пользовательские). Опциональная фильтрация по шаблону (поддержка подстановочных знаков).
  /chat <имя_модели> <вопрос> - Чат с конкретной моделью для тестирования.
  /add_provider            - Добавить пользовательского провайдера. Укажите параметры в формате 'ключ=значение', например: name=my_model model_name=gpt-4 base_url=... api_key=...
  /remove <имя>            - Удалить настроенную модель по имени (можно удалить только пользовательские модели).
  /input_price <имя> <значение> - Установить цену ввода для модели (единица: Миллион токенов).
  /output_price <имя> <значение> - Установить цену вывода для модели (единица: Миллион токенов).
  /speed <имя> <значение> - Установить среднюю скорость для модели (единица: секунды на запрос).
  /speed-test [<раунды>] - Тест скорости настроенных моделей. По желанию укажите количество раундов.
  /speed-test /long_context [<раунды>] - Тест скорости модели с длинным контекстом. По желанию укажите количество раундов.""",
    },
    "models_added": {
        "en": "Added/Updated model '{{name}}' successfully.",
        "zh": "成功添加/更新模型 '{{name}}'。",
        "ja": "モデル '{{name}}' を正常に追加/更新しました。",
        "ar": "تم إضافة/تحديث النموذج '{{name}}' بنجاح.",
        "ru": "Модель '{{name}}' успешно добавлена/обновлена.",
    },
    "models_auto_set_model": {
        "en": "Auto-configured model to '{{name}}' (no model was previously set).",
        "zh": "已自动设置当前模型为 '{{name}}'（之前未设置模型）。",
        "ja": "モデルを '{{name}}' に自動設定しました（以前はモデルが設定されていませんでした）。",
        "ar": "تم تكوين النموذج تلقائيًا إلى '{{name}}' (لم يتم تعيين نموذج مسبقًا).",
        "ru": "Модель автоматически настроена на '{{name}}' (ранее модель не была установлена).",
    },
    "models_add_failed": {
        "en": "Failed to add model '{{name}}'. Model not found in defaults.",
        "zh": "添加模型 '{{name}}' 失败。在默认模型中未找到该模型。",
        "ja": "モデル '{{name}}' の追加に失敗しました。デフォルトモデルで見つかりません。",
        "ar": "فشل في إضافة النموذج '{{name}}'. النموذج غير موجود في الافتراضيات.",
        "ru": "Не удалось добавить модель '{{name}}'. Модель не найдена в значениях по умолчанию.",
    },
    "models_add_usage": {
        "en": "Usage: /models /add <name> <api_key> \n Available models: \n{{models}}",
        "zh": "用法: /models /add <name> <api_key> \n 可用模型: \n{{models}}",
        "ja": "使用法: /models /add <name> <api_key> \n 利用可能なモデル: \n{{models}}",
        "ar": "الاستخدام: /models /add <name> <api_key> \n النماذج المتاحة: \n{{models}}",
        "ru": "Использование: /models /add <имя> <api_ключ> \n Доступные модели: \n{{models}}",
    },
    "models_add_model_params": {
        "en": "Please provide parameters in key=value format",
        "zh": "请提供 key=value 格式的参数",
        "ja": "key=value 形式でパラメータを提供してください",
        "ar": "يرجى تقديم المعاملات بصيغة key=value",
        "ru": "Пожалуйста, предоставьте параметры в формате ключ=значение",
    },
    "models_add_model_name_required": {
        "en": "'name' parameter is required",
        "zh": "缺少必需的 'name' 参数",
        "ja": "'name' パラメータが必要です",
        "ar": "معامل 'name' مطلوب",
        "ru": "Требуется параметр 'name'",
    },
    "models_add_model_exists": {
        "en": "Model '{{name}}' already exists.",
        "zh": "模型 '{{name}}' 已存在。",
        "ja": "モデル '{{name}}' は既に存在します。",
        "ar": "النموذج '{{name}}' موجود بالفعل.",
        "ru": "Модель '{{name}}' уже существует.",
    },
    "models_add_model_success": {
        "en": "Successfully added custom model: {{name}}",
        "zh": "成功添加自定义模型: {{name}}",
        "ja": "カスタムモデル {{name}} を正常に追加しました",
        "ar": "تم إضافة النموذج المخصص {{name}} بنجاح",
        "ru": "Пользовательская модель {{name}} успешно добавлена",
    },
    "models_add_model_remove": {
        "en": "Model '{{name}}' not found.",
        "zh": "找不到模型 '{{name}}'。",
        "ja": "モデル '{{name}}' が見つかりません。",
        "ar": "النموذج '{{name}}' غير موجود.",
        "ru": "Модель '{{name}}' не найдена.",
    },
    "models_add_model_removed": {
        "en": "Removed model: {{name}}",
        "zh": "已移除模型: {{name}}",
        "ja": "モデルを削除しました: {{name}}",
        "ar": "تم إزالة النموذج: {{name}}",
        "ru": "Модель удалена: {{name}}",
    },
    "models_unknown_subcmd": {
        "en": "Unknown subcommand: {{subcmd}}",
        "zh": "未知的子命令: {{subcmd}}",
        "ja": "未知のサブコマンド: {{subcmd}}",
        "ar": "أمر فرعي غير معروف: {{subcmd}}",
        "ru": "Неизвестная подкоманда: {{subcmd}}",
    },
    "models_input_price_updated": {
        "en": "Updated input price for model {{name}} to {{price}} M/token",
        "zh": "已更新模型 {{name}} 的输入价格为 {{price}} M/token",
        "ja": "モデル {{name}} の入力価格を {{price}} M/token に更新しました",
        "ar": "تم تحديث سعر الإدخال للنموذج {{name}} إلى {{price}} M/token",
        "ru": "Обновлена цена ввода для модели {{name}} до {{price}} М/токен",
    },
    "models_output_price_updated": {
        "en": "Updated output price for model {{name}} to {{price}} M/token",
        "zh": "已更新模型 {{name}} 的输出价格为 {{price}} M/token",
        "ja": "モデル {{name}} の出力価格を {{price}} M/token に更新しました",
        "ar": "تم تحديث سعر الإخراج للنموذج {{name}} إلى {{price}} M/token",
        "ru": "Обновлена цена вывода для модели {{name}} до {{price}} М/токен",
    },
    "models_invalid_price": {
        "en": "Invalid price value: {{error}}",
        "zh": "无效的价格值: {{error}}",
        "ja": "無効な価格値: {{error}}",
        "ar": "قيمة سعر غير صالحة: {{error}}",
        "ru": "Неверное значение цены: {{error}}",
    },
    "models_input_price_usage": {
        "en": "Usage: /models /input_price <name> <value>",
        "zh": "用法: /models /input_price <name> <value>",
        "ja": "使用法: /models /input_price <name> <value>",
        "ar": "الاستخدام: /models /input_price <name> <value>",
        "ru": "Использование: /models /input_price <имя> <значение>",
    },
    "models_output_price_usage": {
        "en": "Usage: /models /output_price <name> <value>",
        "zh": "用法: /models /output_price <name> <value>",
        "ja": "使用法: /models /output_price <name> <value>",
        "ar": "الاستخدام: /models /output_price <name> <value>",
        "ru": "Использование: /models /output_price <имя> <значение>",
    },
    "models_speed_updated": {
        "en": "Updated speed for model {{name}} to {{speed}} s/request",
        "zh": "已更新模型 {{name}} 的速度为 {{speed}} 秒/请求",
        "ja": "モデル {{name}} の速度を {{speed}} 秒/リクエスト に更新しました",
        "ar": "تم تحديث سرعة النموذج {{name}} إلى {{speed}} ثانية/طلب",
        "ru": "Обновлена скорость для модели {{name}} до {{speed}} сек/запрос",
    },
    "models_invalid_speed": {
        "en": "Invalid speed value: {{error}}",
        "zh": "无效的速度值: {{error}}",
        "ja": "無効な速度値: {{error}}",
        "ar": "قيمة سرعة غير صالحة: {{error}}",
        "ru": "Неверное значение скорости: {{error}}",
    },
    "models_speed_usage": {
        "en": "Usage: /models /speed <name> <value>",
        "zh": "用法: /models /speed <name> <value>",
        "ja": "使用法: /models /speed <name> <value>",
        "ar": "الاستخدام: /models /speed <name> <value>",
        "ru": "Использование: /models /speed <имя> <значение>",
    },
    "models_title": {
        "en": "All Models (内置 + models.json)",
        "zh": "所有模型 (内置 + models.json)",
        "ja": "すべてのモデル (内蔵 + models.json)",
        "ar": "جميع النماذج (مدمج + models.json)",
        "ru": "Все модели (встроенные + models.json)",
    },
    "models_no_models": {
        "en": "No models found.",
        "zh": "未找到任何模型。",
        "ja": "モデルが見つかりません。",
        "ar": "لم يتم العثور على نماذج.",
        "ru": "Модели не найдены.",
    },
    "models_no_models_matching_pattern": {
        "en": "No models found matching pattern: {{pattern}}",
        "zh": "未找到匹配模式的模型: {{pattern}}",
        "ja": "パターン {{pattern}} に一致するモデルが見つかりません",
        "ar": "لم يتم العثور على نماذج تطابق النمط: {{pattern}}",
        "ru": "Модели, соответствующие шаблону {{pattern}}, не найдены",
    },
    "models_lite_only": {
        "en": "The /models command is only available in lite mode",
        "zh": "/models 命令仅在 lite 模式下可用",
        "ja": "/models コマンドは lite モードでのみ利用可能です",
        "ar": "أمر /models متاح فقط في وضع lite",
        "ru": "Команда /models доступна только в lite режиме",
    },
    "models_api_key_exists": {
        "en": "API key file exists: {{path}}",
        "zh": "API密钥文件存在: {{path}}",
        "ja": "APIキーファイルが存在します: {{path}}",
        "ar": "ملف مفتاح API موجود: {{path}}",
        "ru": "Файл API ключа существует: {{path}}",
    },
    "models_not_found": {
        "en": "Model '{{name}}' not found in built-in models.",
        "zh": "在内置模型中未找到模型 '{{name}}'。",
        "ja": "内蔵モデルでモデル '{{name}}' が見つかりません。",
        "ar": "النموذج '{{name}}' غير موجود في النماذج المدمجة.",
        "ru": "Модель '{{name}}' не найдена во встроенных моделях.",
    },
    "models_not_found_hint": {
        "en": "\nTip: Use '/models /list' to view all available built-in models.",
        "zh": "\n提示：使用 '/models /list' 查看所有可用的内置模型。",
        "ja": "\nヒント: '/models /list' を使用して、利用可能なすべての内蔵モデルを表示します。",
        "ar": "\nتلميح: استخدم '/models /list' لعرض جميع النماذج المدمجة المتاحة.",
        "ru": "\nПодсказка: Используйте '/models /list' для просмотра всех доступных встроенных моделей.",
    },
    "models_activate_usage": {
        "en": "Usage: /models <provider/model_name> <api_key>",
        "zh": "用法: /models <provider/model_name> <api_key>",
        "ja": "使用法: /models <provider/model_name> <api_key>",
        "ar": "الاستخدام: /models <provider/model_name> <api_key>",
        "ru": "Использование: /models <provider/model_name> <api_key>",
    },
    "models_activate_example": {
        "en": "Example: /models deepseek/deepseek-chat sk-xxx",
        "zh": "示例: /models deepseek/deepseek-chat sk-xxx",
        "ja": "例: /models deepseek/deepseek-chat sk-xxx",
        "ar": "مثال: /models deepseek/deepseek-chat sk-xxx",
        "ru": "Пример: /models deepseek/deepseek-chat sk-xxx",
    },
    "models_activate_list_hint": {
        "en": "\nUse '/models /list' to view all available models.",
        "zh": "\n使用 '/models /list' 查看所有可用的模型。",
        "ja": "\n'/models /list' を使用して、利用可能なすべてのモデルを表示します。",
        "ar": "\nاستخدم '/models /list' لعرض جميع النماذج المتاحة.",
        "ru": "\nИспользуйте '/models /list' для просмотра всех доступных моделей.",
    },
    "models_remove_failed": {
        "en": "Failed to remove model '{{name}}'. Cannot remove default models.",
        "zh": "移除模型 '{{name}}' 失败。无法移除默认模型。",
        "ja": "モデル '{{name}}' の削除に失敗しました。デフォルトモデルは削除できません。",
        "ar": "فشل في إزالة النموذج '{{name}}'. لا يمكن إزالة النماذج الافتراضية.",
        "ru": "Не удалось удалить модель '{{name}}'. Невозможно удалить модели по умолчанию.",
    },
    "models_speed_not_implemented": {
        "en": "Speed functionality is not implemented yet.",
        "zh": "速度功能尚未实现。",
        "ja": "速度機能はまだ実装されていません。",
        "ar": "وظيفة السرعة لم يتم تنفيذها بعد.",
        "ru": "Функционал скорости пока не реализован.",
    },
    "config_invalid_format": {
        "en": "Error: Invalid configuration format. Use 'key:value' or '/drop key'.",
        "zh": "错误：配置格式无效。请使用 'key:value' 或 '/drop key'。",
        "ja": "エラー: 設定形式が無効です。'key:value' または '/drop key' を使用してください。",
        "ar": "خطأ: تنسيق التكوين غير صالح. استخدم 'key:value' أو '/drop key'.",
        "ru": "Ошибка: Неверный формат конфигурации. Используйте 'ключ:значение' или '/drop ключ'.",
    },
    "config_value_empty": {
        "en": "Error: Value cannot be empty. Use 'key:value'.",
        "zh": "错误：值不能为空。请使用 'key:value'。",
        "ja": "エラー: 値は空にできません。'key:value' を使用してください。",
        "ar": "خطأ: القيمة لا يمكن أن تكون فارغة. استخدم 'key:value'.",
        "ru": "Ошибка: Значение не может быть пустым. Используйте 'ключ:значение'.",
    },
    "config_set_success": {
        "en": "Set {{key}} to {{value}}",
        "zh": "已设置 {{key}} 为 {{value}}",
        "ja": "{{key}} を {{value}} に設定しました",
        "ar": "تم تعيين {{key}} إلى {{value}}",
        "ru": "Установлено {{key}} в {{value}}",
    },
    "config_delete_success": {
        "en": "Deleted configuration: {{key}}",
        "zh": "已删除配置：{{key}}",
        "ja": "設定を削除しました: {{key}}",
        "ar": "تم حذف التكوين: {{key}}",
        "ru": "Конфигурация удалена: {{key}}",
    },
    "config_not_found": {
        "en": "Configuration not found: {{key}}",
        "zh": "未找到配置：{{key}}",
        "ja": "設定が見つかりません: {{key}}",
        "ar": "التكوين غير موجود: {{key}}",
        "ru": "Конфигурация не найдена: {{key}}",
    },
    "add_files_matched": {
        "en": "All specified files are already in the current session or no matches found.",
        "zh": "所有指定的文件都已在当前会话中或未找到匹配项。",
        "ja": "指定されたファイルはすべて現在のセッションに既に含まれているか、一致するものが見つかりません。",
        "ar": "جميع الملفات المحددة موجودة بالفعل في الجلسة الحالية أو لم يتم العثور على تطابقات.",
        "ru": "Все указанные файлы уже в текущей сессии или совпадения не найдены.",
    },
    "add_files_added_files": {
        "en": "Added Files",
        "zh": "已添加的文件",
        "ja": "追加されたファイル",
        "ar": "الملفات المضافة",
        "ru": "Добавленные файлы",
    },
    "add_files_no_args": {
        "en": "Please provide arguments for the /add_files command.",
        "zh": "请为 /add_files 命令提供参数。",
        "ja": "/add_files コマンドの引数を提供してください。",
        "ar": "يرجى تقديم وسائط لأمر /add_files.",
        "ru": "Пожалуйста, предоставьте аргументы для команды /add_files.",
    },
    "remove_files_all": {
        "en": "Removed all files.",
        "zh": "已移除所有文件。",
        "ja": "すべてのファイルを削除しました。",
        "ar": "تم إزالة جميع الملفات.",
        "ru": "Все файлы удалены.",
    },
    "remove_files_removed": {
        "en": "Removed Files",
        "zh": "已移除的文件",
        "ja": "削除されたファイル",
        "ar": "الملفات المحذوفة",
        "ru": "Удаленные файлы",
    },
    "remove_files_none": {
        "en": "No files were removed.",
        "zh": "没有文件被移除。",
        "ja": "ファイルは削除されませんでした。",
        "ar": "لم يتم إزالة أي ملفات.",
        "ru": "Файлы не были удалены.",
    },
    "files_removed": {
        "en": "Files Removed",
        "zh": "移除的文件",
        "ja": "削除されたファイル",
        "ar": "الملفات المحذوفة",
        "ru": "Удаленные файлы",
    },
    "models_api_key_empty": {
        "en": "Warning : {{name}} API key is empty. Please set a valid API key.",
        "zh": "警告:  {{name}}  API key 为空。请设置一个有效的 API key。",
        "ja": "警告: {{name}} の API キーが空です。有効な API キーを設定してください。",
        "ar": "تحذير: مفتاح API الخاص بـ {{name}} فارغ. يرجى تعيين مفتاح API صالح.",
        "ru": "Предупреждение: API ключ {{name}} пуст. Пожалуйста, установите действительный API ключ.",
    },
    "commit_generating": {
        "en": "{{ model_name }} Generating commit message...",
        "zh": "{{ model_name }} 正在生成提交信息...",
        "ja": "{{ model_name }} がコミットメッセージを生成中...",
        "ar": "{{ model_name }} ينشئ رسالة الالتزام...",
        "ru": "{{ model_name }} генерирует сообщение коммита...",
    },
    "auto_command_reasoning_title": {
        "en": "Reply",
        "zh": "回复",
        "ja": "返信",
        "ar": "الرد",
        "ru": "Ответ",
    },
    "commit_message": {
        "en": "{{ model_name }} Generated commit message: {{ message }}",
        "zh": "{{ model_name }} 生成的提交信息: {{ message }}",
        "ja": "{{ model_name }} が生成したコミットメッセージ: {{ message }}",
        "ar": "رسالة الالتزام المولدة بواسطة {{ model_name }}: {{ message }}",
        "ru": "{{ model_name }} сгенерировал сообщение коммита: {{ message }}",
    },
    "commit_failed": {
        "en": "{{ model_name }} Failed to generate commit message: {{ error }}",
        "zh": "{{ model_name }} 生成提交信息失败: {{ error }}",
        "ja": "{{ model_name }} がコミットメッセージの生成に失敗しました: {{ error }}",
        "ar": "فشل {{ model_name }} في توليد رسالة الالتزام: {{ error }}",
        "ru": "{{ model_name }} не удалось сгенерировать сообщение коммита: {{ error }}",
    },
    "confirm_execute": {
        "en": "Do you want to execute this script?",
        "zh": "是否执行此脚本?",
        "ja": "このスクリプトを実行しますか？",
        "ar": "هل تريد تنفيذ هذا السكريبت؟",
        "ru": "Хотите выполнить этот скрипт?",
    },
    "official_doc": {
        "en": "Official Documentation: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
        "zh": "官方文档: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
        "ja": "公式ドキュメント: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
        "ar": "الوثائق الرسمية: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
        "ru": "Официальная документация: https://uelng8wukz.feishu.cn/wiki/NhPNwSRcWimKFIkQINIckloBncI",
    },
    "plugins_desc": {
        "en": "Manage plugins",
        "zh": "管理插件",
        "ja": "プラグインを管理",
        "ar": "إدارة الإضافات",
        "ru": "Управление плагинами",
    },
    "plugins_usage": {
        "en": "Usage: /plugins <command>\nAvailable subcommands:\n  /plugins /list - List all available plugins\n  /plugins /load <name> - Load a plugin\n  /plugins /unload <name> - Unload a plugin\n  /plugins/dirs - List plugin directories\n  /plugins/dirs /add <path> - Add a plugin directory\n  /plugins/dirs /remove <path> - Remove a plugin directory\n  /plugins/dirs /clear - Clear all plugin directories",
        "zh": "用法: /plugins <命令>\n可用的子命令:\n  /plugins /list - 列出所有可用插件\n  /plugins /load <名称> - 加载一个插件\n  /plugins /unload <名称> - 卸载一个插件\n  /plugins/dirs - 列出插件目录\n  /plugins/dirs /add <路径> - 添加一个插件目录\n  /plugins/dirs /remove <路径> - 移除一个插件目录\n  /plugins/dirs /clear - 清除所有插件目录",
        "ja": "使用法: /plugins <コマンド>\n利用可能なサブコマンド:\n  /plugins /list - 利用可能なすべてのプラグインをリスト\n  /plugins /load <名前> - プラグインを読み込み\n  /plugins /unload <名前> - プラグインをアンロード\n  /plugins/dirs - プラグインディレクトリをリスト\n  /plugins/dirs /add <パス> - プラグインディレクトリを追加\n  /plugins/dirs /remove <パス> - プラグインディレクトリを削除\n  /plugins/dirs /clear - すべてのプラグインディレクトリをクリア",
        "ar": "الاستخدام: /plugins <الأمر>\nالأوامر الفرعية المتاحة:\n  /plugins /list - إدراج جميع الإضافات المتاحة\n  /plugins /load <الاسم> - تحميل إضافة\n  /plugins /unload <الاسم> - إلغاء تحميل إضافة\n  /plugins/dirs - إدراج دلائل الإضافات\n  /plugins/dirs /add <المسار> - إضافة دليل إضافة\n  /plugins/dirs /remove <المسار> - إزالة دليل إضافة\n  /plugins/dirs /clear - مسح جميع دلائل الإضافات",
        "ru": "Использование: /plugins <команда>\nДоступные подкоманды:\n  /plugins /list - Список всех доступных плагинов\n  /plugins /load <имя> - Загрузить плагин\n  /plugins /unload <имя> - Выгрузить плагин\n  /plugins/dirs - Список каталогов плагинов\n  /plugins/dirs /add <путь> - Добавить каталог плагинов\n  /plugins/dirs /remove <путь> - Удалить каталог плагинов\n  /plugins/dirs /clear - Очистить все каталоги плагинов",
    },
    "mcp_server_info_error": {
        "en": "Error getting MCP server info: {{error}}",
        "zh": "获取 MCP 服务器信息时出错：{{error}}",
        "ja": "MCPサーバー情報の取得エラー: {{error}}",
        "ar": "خطأ في الحصول على معلومات خادم MCP: {{error}}",
        "ru": "Ошибка получения информации MCP сервера: {{error}}",
    },
    "mcp_server_info_title": {
        "en": "Connected MCP Server Info",
        "zh": "已连接的MCP服务器信息",
        "ja": "接続されたMCPサーバー情報",
        "ar": "معلومات خادم MCP المتصل",
        "ru": "Информация о подключенном MCP сервере",
    },
    "active_context_desc": {
        "en": "Manage active context tasks, list all tasks and their status",
        "zh": "管理活动上下文任务，列出所有任务及其状态",
        "ja": "アクティブなコンテキストタスクを管理し、すべてのタスクとその状態を一覧表示",
        "ar": "إدارة مهام السياق النشط، إدراج جميع المهام وحالتها",
        "ru": "Управление активными контекстными задачами, список всех задач и их статус",
    },
    "auto_desc": {
        "en": "Smart command analysis and execution with AI assistance",
        "zh": "通过AI辅助进行智能命令分析和执行",
        "ja": "AIアシスタントによるスマートなコマンド分析と実行",
        "ar": "تحليل وتنفيذ الأوامر الذكية بمساعدة الذكاء الاصطناعي",
        "ru": "Умный анализ и выполнение команд с помощью ИИ",
    },
    "auto_new_desc": {
        "en": "Start a new AI conversation session",
        "zh": "开始一个新的AI对话会话",
        "ja": "新しいAI会話セッションを開始",
        "ar": "بدء جلسة محادثة ذكاء اصطناعي جديدة",
        "ru": "Начать новую сессию разговора с ИИ",
    },
    "auto_resume_desc": {
        "en": "Resume a previous conversation by ID",
        "zh": "通过ID恢复之前的对话",
        "ja": "IDで以前の会話を再開",
        "ar": "استئناف محادثة سابقة بواسطة المعرف",
        "ru": "Возобновить предыдущий разговор по ID",
    },
    "auto_list_desc": {
        "en": "List all conversation sessions",
        "zh": "列出所有对话会话",
        "ja": "すべての会話セッションを一覧表示",
        "ar": "إدراج جميع جلسات المحادثة",
        "ru": "Список всех сессий разговоров",
    },
    "auto_command_desc": {
        "en": "Execute commands from a template file",
        "zh": "从模板文件执行命令",
        "ja": "テンプレートファイルからコマンドを実行",
        "ar": "تنفيذ الأوامر من ملف القالب",
        "ru": "Выполнить команды из файла шаблона",
    },
    "marketplace_add_success": {
        "en": "Successfully added marketplace item: {{name}}",
        "zh": "成功添加市场项目：{{name}}",
        "ja": "マーケットプレイスアイテムを正常に追加しました: {{name}}",
        "ar": "تم إضافة عنصر السوق بنجاح: {{name}}",
        "ru": "Успешно добавлен элемент маркетплейса: {{name}}",
    },
    "marketplace_add_error": {
        "en": "Error adding marketplace item: {{name}} - {{error}}",
        "zh": "添加市场项目时出错：{{name}} - {{error}}",
        "ja": "マーケットプレイスアイテムの追加エラー: {{name}} - {{error}}",
        "ar": "خطأ في إضافة عنصر السوق: {{name}} - {{error}}",
        "ru": "Ошибка добавления элемента маркетплейса: {{name}} - {{error}}",
    },
    "rules_desc": {
        "en": "Analyze current files with rules and create code learning notes",
        "zh": "使用规则分析当前文件并创建代码学习笔记",
        "ja": "ルールを使用して現在のファイルを分析し、コード学習ノートを作成",
        "ar": "تحليل الملفات الحالية بالقواعد وإنشاء ملاحظات تعلم الكود",
        "ru": "Анализировать текущие файлы по правилам и создавать заметки для изучения кода",
    },
    "rules_file_list_title": {
        "en": "Rules Files List (Pattern: {{pattern}})",
        "zh": "规则文件列表 (匹配: {{pattern}})",
        "ja": "ルールファイルリスト (パターン: {{pattern}})",
        "ar": "قائمة ملفات القواعد (النمط: {{pattern}})",
        "ru": "Список файлов правил (Шаблон: {{pattern}})",
    },
    "rules_file_path": {
        "en": "File Path",
        "zh": "文件路径",
        "ja": "ファイルパス",
        "ar": "مسار الملف",
        "ru": "Путь к файлу",
    },
    "rules_content_length": {
        "en": "Content Length",
        "zh": "内容长度",
        "ja": "コンテンツ長",
        "ar": "طول المحتوى",
        "ru": "Длина содержимого",
    },
    "rules_help_subtitle": {
        "en": "Use '/rules help' for more information",
        "zh": "使用 '/rules help' 获取更多帮助",
        "ja": "詳細については '/rules help' を使用してください",
        "ar": "استخدم '/rules help' للحصول على مزيد من المعلومات",
        "ru": "Используйте '/rules help' для получения дополнительной информации",
    },
    "rules_no_files_found": {
        "en": "No rules files found. Use '/rules /help' to learn how to add rules.",
        "zh": "未找到任何规则文件。请使用 '/rules /help' 了解如何添加规则。",
        "ja": "ルールファイルが見つかりません。'/rules /help' を使用してルールの追加方法を確認してください。",
        "ar": "لم يتم العثور على ملفات قواعد. استخدم '/rules /help' لتعلم كيفية إضافة القواعد.",
        "ru": "Файлы правил не найдены. Используйте '/rules /help' чтобы узнать, как добавить правила.",
    },
    "rules_no_matching_files": {
        "en": "No rules files found matching pattern '{{pattern}}'.",
        "zh": "没有找到匹配模式 '{{pattern}}' 的规则文件。",
        "ja": "パターン '{{pattern}}' に一致するルールファイルが見つかりません。",
        "ar": "لم يتم العثور على ملفات قواعد تطابق النمط '{{pattern}}'.",
        "ru": "Файлы правил, соответствующие шаблону '{{pattern}}', не найдены.",
    },
    "rules_remove_param_required": {
        "en": "Error: 'remove' command requires a parameter (file pattern). Usage: /rules /remove <pattern>",
        "zh": "错误: 'remove' 命令需要一个参数（文件匹配模式）。用法: /rules /remove <匹配模式>",
        "ja": "エラー: 'remove' コマンドにはパラメータ（ファイルパターン）が必要です。使用法: /rules /remove <パターン>",
        "ar": "خطأ: أمر 'remove' يتطلب معامل (نمط الملف). الاستخدام: /rules /remove <pattern>",
        "ru": "Ошибка: команда 'remove' требует параметр (шаблон файла). Использование: /rules /remove <шаблон>",
    },
    "rules_no_files_to_remove": {
        "en": "No rules files found matching pattern '{{pattern}}'.",
        "zh": "没有找到匹配模式 '{{pattern}}' 的规则文件。",
        "ja": "パターン '{{pattern}}' に一致するルールファイルが見つかりません。",
        "ar": "لم يتم العثور على ملفات قواعد تطابق النمط '{{pattern}}'.",
        "ru": "Файлы правил, соответствующие шаблону '{{pattern}}', не найдены.",
    },
    "rules_delete_error": {
        "en": "Error deleting file '{{file_path}}': {{error}}",
        "zh": "删除文件 '{{file_path}}' 时出错: {{error}}",
        "ja": "ファイル '{{file_path}}' の削除エラー: {{error}}",
        "ar": "خطأ في حذف الملف '{{file_path}}': {{error}}",
        "ru": "Ошибка удаления файла '{{file_path}}': {{error}}",
    },
    "rules_delete_success": {
        "en": "Successfully deleted {{count}} rules files.",
        "zh": "成功删除了 {{count}} 个规则文件。",
        "ja": "{{count}} 個のルールファイルを正常に削除しました。",
        "ar": "تم حذف {{count}} من ملفات القواعد بنجاح.",
        "ru": "Успешно удалено {{count}} файлов правил.",
    },
    "rules_no_active_files": {
        "en": "Error: No files selected for analysis. Please use 'add_files' command to add files first.",
        "zh": "错误: 没有选择任何文件进行分析。请先使用 'add_files' 命令添加文件。",
        "ja": "エラー: 分析用のファイルが選択されていません。まず 'add_files' コマンドでファイルを追加してください。",
        "ar": "خطأ: لم يتم اختيار أي ملفات للتحليل. يرجى استخدام أمر 'add_files' لإضافة الملفات أولاً.",
        "ru": "Ошибка: Файлы для анализа не выбраны. Пожалуйста, сначала используйте команду 'add_files' для добавления файлов.",
    },
    "rules_file_read_error": {
        "en": "Error reading file '{{file_path}}': {{error}}",
        "zh": "读取文件 '{{file_path}}' 时出错: {{error}}",
        "ja": "ファイル '{{file_path}}' の読み取りエラー: {{error}}",
        "ar": "خطأ في قراءة الملف '{{file_path}}': {{error}}",
        "ru": "Ошибка чтения файла '{{file_path}}': {{error}}",
    },
    "rules_analysis_error": {
        "en": "Error analyzing code: {{error}}",
        "zh": "分析代码时出错: {{error}}",
        "ja": "コード分析エラー: {{error}}",
        "ar": "خطأ في تحليل الكود: {{error}}",
        "ru": "Ошибка анализа кода: {{error}}",
    },
    "rules_help_text": {
        "en": """
/rules command usage:
  /rules [query]       - Analyze current added files, optionally provide specific query content.  
  /rules /list [pattern] - List all rules files. Optionally provide wildcard pattern (e.g. *.md).
  /rules /remove <pattern> - Delete rules files matching the specified pattern.
  /rules /get <pattern> - Display the content of rules files matching the specified pattern.
  /rules /help or /rules help - Show this help message.

Rules file usage:
  Rules files are stored in the project's .autocoderrules/ directory, in Markdown format.
  The system automatically monitors changes to this directory and updates rules.
        """,
        "zh": """
/rules 命令用法:
  /rules [查询内容]    - 分析当前已添加的文件，可选提供具体查询内容。  
  /rules /list [匹配模式] - 列出所有规则文件。可选提供通配符匹配模式 (例如: *.md).
  /rules /remove <匹配模式> - 删除匹配指定模式的规则文件。
  /rules /get <匹配模式> - 显示匹配指定模式的规则文件内容。
  /rules /help 或 /rules help - 显示此帮助信息。

规则文件用法:
  规则文件存储在项目的 .autocoderrules/ 目录下，为 Markdown 格式。
  系统会自动监控该目录的变化并更新规则。
        """,
        "ja": """
/rules コマンド使用法:
  /rules [クエリ]      - 現在追加されているファイルを分析、オプションで特定のクエリ内容を提供。
  /rules /list [パターン] - すべてのルールファイルをリスト。オプションでワイルドカードパターンを提供 (例: *.md)。
  /rules /remove <パターン> - 指定されたパターンに一致するルールファイルを削除。
  /rules /get <パターン> - 指定されたパターンに一致するルールファイルの内容を表示。
  /rules /help または /rules help - このヘルプメッセージを表示。

ルールファイル使用法:
  ルールファイルはプロジェクトの .autocoderrules/ ディレクトリにMarkdown形式で格納されます。
  システムはこのディレクトリの変更を自動的に監視し、ルールを更新します。
        """,
        "ar": """
استخدام أمر /rules:
  /rules [الاستعلام]     - تحليل الملفات المضافة حالياً، اختيارياً تقديم محتوى استعلام محدد.
  /rules /list [النمط] - إدراج جميع ملفات القواعد. اختيارياً تقديم نمط بدل (مثل *.md).
  /rules /remove <النمط> - حذف ملفات القواعد المطابقة للنمط المحدد.
  /rules /get <النمط> - عرض محتوى ملفات القواعد المطابقة للنمط المحدد.
  /rules /help أو /rules help - إظهار رسالة المساعدة هذه.

استخدام ملف القواعد:
  يتم تخزين ملفات القواعد في دليل .autocoderrules/ للمشروع، بصيغة Markdown.
  يراقب النظام تلقائياً التغييرات في هذا الدليل ويحدث القواعد.
        """,
        "ru": """
Использование команды /rules:
  /rules [запрос]       - Анализировать текущие добавленные файлы, по желанию предоставить конкретный контент запроса.
  /rules /list [шаблон] - Список всех файлов правил. По желанию предоставить шаблон подстановки (например *.md).
  /rules /remove <шаблон> - Удалить файлы правил, соответствующие указанному шаблону.
  /rules /get <шаблон> - Отобразить содержимое файлов правил, соответствующих указанному шаблону.
  /rules /help или /rules help - Показать это справочное сообщение.

Использование файла правил:
  Файлы правил хранятся в каталоге .autocoderrules/ проекта в формате Markdown.
  Система автоматически отслеживает изменения в этом каталоге и обновляет правила.
        """,
    },
    "rules_unknown_command": {
        "en": "Unknown subcommand '/rules {{subcommand}}'. Use '/rules /help' for help.",
        "zh": "未知的子命令 '/rules {{subcommand}}'。请使用 '/rules /help' 获取帮助。",
        "ja": "未知のサブコマンド '/rules {{subcommand}}'。ヘルプについては '/rules /help' を使用してください。",
        "ar": "أمر فرعي غير معروف '/rules {{subcommand}}'. استخدم '/rules /help' للحصول على المساعدة.",
        "ru": "Неизвестная подкоманда '/rules {{subcommand}}'. Используйте '/rules /help' для справки.",
    },
    "rules_command_error": {
        "en": "Error executing '/rules {{subcommand}}': {{error}}",
        "zh": "执行 '/rules {{subcommand}}' 时发生错误: {{error}}",
        "ja": "'/rules {{subcommand}}' の実行エラー: {{error}}",
        "ar": "خطأ في تنفيذ '/rules {{subcommand}}': {{error}}",
        "ru": "Ошибка выполнения '/rules {{subcommand}}': {{error}}",
    },
    "rules_get_param_required": {
        "en": "Error: 'get' command requires a parameter (file pattern). Usage: /rules /get <pattern>",
        "zh": "错误: 'get' 命令需要一个参数（文件匹配模式）。用法: /rules /get <匹配模式>",
        "ja": "エラー: 'get' コマンドにはパラメータ（ファイルパターン）が必要です。使用法: /rules /get <パターン>",
        "ar": "خطأ: أمر 'get' يتطلب معامل (نمط الملف). الاستخدام: /rules /get <pattern>",
        "ru": "Ошибка: команда 'get' требует параметр (шаблон файла). Использование: /rules /get <шаблон>",
    },
    "rules_get_no_matching_files": {
        "en": "No rules files found matching pattern '{{pattern}}'.",
        "zh": "没有找到匹配模式 '{{pattern}}' 的规则文件。",
        "ja": "パターン '{{pattern}}' に一致するルールファイルが見つかりません。",
        "ar": "لم يتم العثور على ملفات قواعد تطابق النمط '{{pattern}}'.",
        "ru": "Файлы правил, соответствующие шаблону '{{pattern}}', не найдены.",
    },
    "rules_get_file_title": {
        "en": "Rule File: {{file_path}}",
        "zh": "规则文件: {{file_path}}",
        "ja": "ルールファイル: {{file_path}}",
        "ar": "ملف القواعد: {{file_path}}",
        "ru": "Файл правил: {{file_path}}",
    },
    "rules_get_read_error": {
        "en": "Error reading file '{{file_path}}': {{error}}",
        "zh": "读取文件 '{{file_path}}' 时出错: {{error}}",
        "ja": "ファイル '{{file_path}}' の読み取りエラー: {{error}}",
        "ar": "خطأ في قراءة الملف '{{file_path}}': {{error}}",
        "ru": "Ошибка чтения файла '{{file_path}}': {{error}}",
    },
    "rules_commit_param_required": {
        "en": "Error: 'commit' command requires parameters. Usage: /rules /commit <commit_id> /query <query>",
        "zh": "错误: 'commit' 命令需要参数。用法: /rules /commit <commit_id> /query <查询内容>",
        "ja": "エラー: 'commit' コマンドにはパラメータが必要です。使用法: /rules /commit <commit_id> /query <クエリ>",
        "ar": "خطأ: أمر 'commit' يتطلب معاملات. الاستخدام: /rules /commit <commit_id> /query <query>",
        "ru": "Ошибка: команда 'commit' требует параметры. Использование: /rules /commit <commit_id> /query <запрос>",
    },
    "rules_commit_format_error": {
        "en": "Error: Command format must be '/rules /commit <commit_id> /query <query>'",
        "zh": "错误：命令格式必须为 '/rules /commit <commit_id> /query <你的需求>'",
        "ja": "エラー: コマンド形式は '/rules /commit <commit_id> /query <クエリ>' である必要があります",
        "ar": "خطأ: تنسيق الأمر يجب أن يكون '/rules /commit <commit_id> /query <query>'",
        "ru": "Ошибка: Формат команды должен быть '/rules /commit <commit_id> /query <запрос>'",
    },
    "rules_commit_id_required": {
        "en": "Error: Commit ID must be provided",
        "zh": "错误：必须提供 commit ID",
        "ja": "エラー: コミットIDを提供する必要があります",
        "ar": "خطأ: يجب توفير معرف الالتزام",
        "ru": "Ошибка: Необходимо указать ID коммита",
    },
    "rules_query_required": {
        "en": "Error: Query content must be provided",
        "zh": "错误：必须提供查询内容",
        "ja": "エラー: クエリ内容を提供する必要があります",
        "ar": "خطأ: يجب توفير محتوى الاستعلام",
        "ru": "Ошибка: Необходимо указать содержимое запроса",
    },
    "rules_commit_success": {
        "en": "Successfully analyzed commit {{commit_id}}, query: {{query}}",
        "zh": "成功分析 commit {{commit_id}}，查询：{{query}}",
        "ja": "コミット {{commit_id}} の分析が成功しました、クエリ: {{query}}",
        "ar": "تم تحليل الالتزام {{commit_id}} بنجاح، الاستعلام: {{query}}",
        "ru": "Успешно проанализирован коммит {{commit_id}}, запрос: {{query}}",
    },
    "rules_commit_error": {
        "en": "Error analyzing commit {{commit_id}}: {{error}}",
        "zh": "分析 commit {{commit_id}} 时出错：{{error}}",
        "ja": "コミット {{commit_id}} の分析エラー: {{error}}",
        "ar": "خطأ في تحليل الالتزام {{commit_id}}: {{error}}",
        "ru": "Ошибка анализа коммита {{commit_id}}: {{error}}",
    },
    "wait_system_processing": {
        "en": "⚠️  System is processing, please wait... (max wait time: {{timeout}} seconds)",
        "zh": "⚠️  系统正在处理中，请稍等... (最多等待 {{timeout}} 秒)",
        "ja": "⚠️  システムが処理中です、お待ちください... (最大待機時間: {{timeout}} 秒)",
        "ar": "⚠️  النظام قيد المعالجة، يرجى الانتظار... (الحد الأقصى لوقت الانتظار: {{timeout}} ثانية)",
        "ru": "⚠️  Система обрабатывает, пожалуйста, подождите... (максимальное время ожидания: {{timeout}} секунд)",
    },
    "wait_processing_dots": {
        "en": "Waiting{{dots}} ({{remaining}} seconds remaining)",
        "zh": "等待中{{dots}} (剩余 {{remaining}} 秒)",
        "ja": "待機中{{dots}} (残り {{remaining}} 秒)",
        "ar": "في الانتظار{{dots}} ({{remaining}} ثانية متبقية)",
        "ru": "Ожидание{{dots}} (осталось {{remaining}} секунд)",
    },
    "wait_timeout_allow_continue": {
        "en": "⏰ Wait timeout ({{timeout}} seconds), allowing new command input",
        "zh": "⏰ 等待超时 ({{timeout}} 秒)，允许继续输入新指令",
        "ja": "⏰ 待機タイムアウト ({{timeout}} 秒)、新しいコマンド入力を許可します",
        "ar": "⏰ انتهت مهلة الانتظار ({{timeout}} ثانية)، مسموح بإدخال أوامر جديدة",
        "ru": "⏰ Истекло время ожидания ({{timeout}} секунд), разрешен ввод новых команд",
    },
    "wait_system_ready": {
        "en": "✅ System is ready, you can continue operating",
        "zh": "✅ 系统已准备就绪，可以继续操作",
        "ja": "✅ システムの準備ができました、操作を続行できます",
        "ar": "✅ النظام جاهز، يمكنك متابعة العمل",
        "ru": "✅ Система готова, вы можете продолжить работу",
    },
    "exit_ctrl_d": {
        "en": "Exit: Ctrl+D",
        "zh": "退出: Ctrl+D",
        "ja": "終了: Ctrl+D",
        "ar": "الخروج: Ctrl+D",
        "ru": "Выход: Ctrl+D",
    },
    "goodbye": {
        "en": "GoodBye!",
        "zh": "再见！",
        "ja": "さようなら！",
        "ar": "وداعاً!",
        "ru": "До свидания!",
    },
    "shell_interactive_desc": {
        "en": "Start an interactive sub-shell",
        "zh": "启动交互式子shell",
        "ja": "対話式サブシェルを開始",
        "ar": "بدء صدفة فرعية تفاعلية",
        "ru": "Запустить интерактивную суб-оболочку",
    },
    "shell_single_command_desc": {
        "en": "Execute a single shell command",
        "zh": "执行单行shell命令",
        "ja": "単一のシェルコマンドを実行",
        "ar": "تنفيذ أمر shell واحد",
        "ru": "Выполнить одну команду shell",
    },
    "workflow_shortcut_desc": {
        "en": "Execute a workflow (shortcut for /workflow)",
        "zh": "执行工作流 (/workflow 的快捷方式)",
        "ja": "ワークフローを実行 (/workflow のショートカット)",
        "ar": "تنفيذ سير العمل (اختصار لـ /workflow)",
        "ru": "Выполнить workflow (ярлык для /workflow)",
    },
    "plugin_commands_title": {
        "en": "Plugin Commands:",
        "zh": "插件命令：",
        "ja": "プラグインコマンド:",
        "ar": "أوامر الإضافات:",
        "ru": "Команды плагинов:",
    },
    "plugin_command_header": {
        "en": "Command",
        "zh": "命令",
        "ja": "コマンド",
        "ar": "الأمر",
        "ru": "Команда",
    },
    "plugin_description_header": {
        "en": "Description",
        "zh": "描述",
        "ja": "説明",
        "ar": "الوصف",
        "ru": "Описание",
    },
    "plugin_from_unknown": {
        "en": "from unknown plugin",
        "zh": "来自未知插件",
        "ja": "不明なプラグインから",
        "ar": "من إضافة غير معروفة",
        "ru": "от неизвестного плагина",
    },
    "plugin_from": {"en": "from", "zh": "来自", "ja": "から", "ar": "من", "ru": "от"},
    "loaded_plugins_builtin": {
        "en": "Loaded {{count}} builtin plugin(s)",
        "zh": "已加载 {{count}} 个内置插件",
        "ja": "{{count}} 個の内蔵プラグインを読み込みました",
        "ar": "تم تحميل {{count}} من الإضافات المدمجة",
        "ru": "Загружено {{count}} встроенных плагинов",
    },
    "no_builtin_plugins_loaded": {
        "en": "No builtin plugins loaded",
        "zh": "未加载内置插件",
        "ja": "内蔵プラグインは読み込まれていません",
        "ar": "لم يتم تحميل إضافات مدمجة",
        "ru": "Встроенные плагины не загружены",
    },
    "please_enter_request": {
        "en": "Please enter your request.",
        "zh": "请输入您的请求。",
        "ja": "リクエストを入力してください。",
        "ar": "يرجى إدخال طلبك.",
        "ru": "Пожалуйста, введите ваш запрос.",
    },
    "please_enter_design_request": {
        "en": "Please enter your design request.",
        "zh": "请输入您的设计请求。",
        "ja": "デザインリクエストを入力してください。",
        "ar": "يرجى إدخال طلب التصميم الخاص بك.",
        "ru": "Пожалуйста, введите ваш запрос на дизайн.",
    },
    "please_enter_query": {
        "en": "Please enter your query.",
        "zh": "请输入您的查询。",
        "ja": "クエリを入力してください。",
        "ar": "يرجى إدخال استفسارك.",
        "ru": "Пожалуйста, введите ваш запрос.",
    },
    "switched_to_shell_mode": {
        "en": "Switched to shell mode. All non-command input will be executed as shell commands.",
        "zh": "已切换到shell模式。所有非命令输入都将作为shell命令执行。",
        "ja": "シェルモードに切り替えました。すべての非コマンド入力はシェルコマンドとして実行されます。",
        "ar": "تم التبديل إلى وضع shell. سيتم تنفيذ جميع المدخلات غير الأوامر كأوامر shell.",
        "ru": "Переключен в режим shell. Все некомандные вводы будут выполнены как команды shell.",
    },
    "unknown_command": {
        "en": "Unknown command: {{command}}",
        "zh": "未知命令：{{command}}",
        "ja": "未知のコマンド: {{command}}",
        "ar": "أمر غير معروف: {{command}}",
        "ru": "Неизвестная команда: {{command}}",
    },
    "type_help_for_commands": {
        "en": "Type /help to see available commands.",
        "zh": "输入 /help 查看可用命令。",
        "ja": "/help と入力して利用可能なコマンドを表示してください。",
        "ar": "اكتب /help لرؤية الأوامر المتاحة.",
        "ru": "Введите /help, чтобы увидеть доступные команды.",
    },
    "type_help_to_see_commands": {
        "en": "Type /help to see available commands.",
        "zh": "输入 /help 查看可用命令。",
        "ja": "/help と入力して利用可能なコマンドを表示してください。",
        "ar": "اكتب /help لرؤية الأوامر المتاحة.",
        "ru": "Введите /help, чтобы увидеть доступные команды.",
    },
    "loaded_plugins_title": {
        "en": "Loaded Plugins:",
        "zh": "已加载的插件：",
        "ja": "読み込まれたプラグイン:",
        "ar": "المكونات الإضافية المحملة:",
        "ru": "Загруженные плагины:",
    },
}
