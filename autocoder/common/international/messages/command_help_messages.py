"""
Command help messages for internationalization
Contains all help text messages for various commands

使用 byzerllm prompt function 风格定义帮助文本，方便编辑和维护
"""

import byzerllm


# /conf command help text definitions
@byzerllm.prompt()
def conf_help_en() -> str:
    """
    /conf command usage:
      /conf [pattern]    - Show configurations (merged view). Optional wildcard pattern (e.g., *_model, api*).
      /conf <key>:<value> - Set or update a configuration key (shortcut for /conf /set).
      /conf /global <key>:<value> - Set or update a global configuration key (shortcut).
      /conf /get <key>    - Get the value of a specific configuration key (merged view).
      /conf /set <key>:<value> - Set or update a configuration key (project scope).
                           Value parsed (bool, int, float, None) or treated as string.
                           Use quotes ("value with spaces") for explicit strings.
      /conf /drop <key> - Delete a configuration key (project scope).
      /conf /delete <key> - Delete a configuration key (project scope).
      /conf /export <path> - Export current configuration to a file.
      /conf /import <path> - Import configuration from a file.
      /conf /help        - Show this help message.

    Global configuration (stored in ~/.auto-coder):
      /conf /global /list [pattern] - List global configurations.
      /conf /global /get <key>      - Get a global configuration value.
      /conf /global /set <key> <value> - Set a global configuration.
      (Shorthand also supported: /conf /global <key>:<value>)
      /conf /global /delete <key>   - Delete a global configuration.

    Note: When reading configs, project values take precedence over global values.
    """


@byzerllm.prompt()
def conf_help_zh() -> str:
    """
    /conf 命令用法:
      /conf [pattern]    - 显示配置（合并视图）。可选通配符模式 (例如: *_model, api*).
      /conf <key>:<value> - 设置或更新配置项 (/conf /set 的快捷方式，项目级).
      /conf /global <key>:<value> - 设置或更新全局配置项（简写形式）.
      /conf /get <key>    - 获取指定配置项的值（合并视图）.
      /conf /set <key>:<value> - 设置或更新配置项（项目级）.
                           值会被解析为 (bool, int, float, None) 或字符串.
                           使用引号 ("带空格的值") 表示明确的字符串.
      /conf /drop <key> - 删除配置项（项目级）.
      /conf /delete <key> - 删除配置项（项目级）.
      /conf /export <path> - 将当前配置导出到文件.
      /conf /import <path> - 从文件导入配置.
      /conf /help        - 显示此帮助信息.

    全局配置（存储在 ~/.auto-coder）:
      /conf /global /list [pattern] - 列出全局配置.
      /conf /global /get <key>      - 获取全局配置值.
      /conf /global /set <key> <value> - 设置全局配置.
      （同样支持简写：/conf /global <key>:<value>）
      /conf /global /delete <key>   - 删除全局配置.

    注意：读取配置时，项目级配置优先于全局配置。
    """


@byzerllm.prompt()
def conf_help_ja() -> str:
    """
    /conf コマンド使用法:
      /conf [pattern]    - 設定を表示. オプションのワイルドカードパターン (例: *_model, api*).
      /conf <key>:<value> - 設定キーを設定または更新 (/conf /set のショートカット).
      /conf /get <key>    - 特定の設定キーの値を取得.
      /conf /set <key>:<value> - 設定キーを設定または更新.
                           値は (bool, int, float, None) として解析されるか文字列として扱われます.
                           明示的な文字列には引用符 ("スペースを含む値") を使用.
      /conf /drop <key> - 設定キーを削除.
      /conf /delete <key> - 設定キーを削除.
      /conf /export <path> - 現在の設定をファイルにエクスポート.
      /conf /import <path> - ファイルから設定をインポート.
      /conf /help        - このヘルプメッセージを表示.
    """


@byzerllm.prompt()
def conf_help_ar() -> str:
    """
    استخدام أمر /conf:
      /conf [pattern]    - إظهار التكوينات. نمط أحرف البدل الاختياري (مثل: *_model, api*).
      /conf <key>:<value> - تعيين أو تحديث مفتاح التكوين (اختصار لـ /conf /set).
      /conf /get <key>    - الحصول على قيمة مفتاح تكوين محدد.
      /conf /set <key>:<value> - تعيين أو تحديث مفتاح التكوين.
                           يتم تحليل القيمة كـ (bool, int, float, None) أو التعامل معها كسلسلة نصية.
                           استخدم علامات الاقتباس ("قيمة بمسافات") للسلاسل النصية الصريحة.
      /conf /drop <key> - حذف مفتاح التكوين.
      /conf /delete <key> - حذف مفتاح التكوين.
      /conf /export <path> - تصدير التكوين الحالي إلى ملف.
      /conf /import <path> - استيراد التكوين من ملف.
      /conf /help        - إظهار رسالة المساعدة هذه.
    """


@byzerllm.prompt()
def conf_help_ru() -> str:
    """
    Использование команды /conf:
      /conf [pattern]    - Показать конфигурации. Необязательный шаблон с подстановочными знаками (например: *_model, api*).
      /conf <key>:<value> - Установить или обновить ключ конфигурации (сокращение для /conf /set).
      /conf /get <key>    - Получить значение определенного ключа конфигурации.
      /conf /set <key>:<value> - Установить или обновить ключ конфигурации.
                           Значение парсится как (bool, int, float, None) или обрабатывается как строка.
                           Используйте кавычки ("значение с пробелами") для явных строк.
      /conf /drop <key> - Удалить ключ конфигурации.
      /conf /delete <key> - Удалить ключ конфигурации.
      /conf /export <path> - Экспортировать текущую конфигурацию в файл.
      /conf /import <path> - Импортировать конфигурацию из файла.
      /conf /help        - Показать это сообщение справки.
    """


# /auto command help text definitions
@byzerllm.prompt()
def auto_help_en() -> str:
    """
    /auto command usage:
      /auto [query]                - Execute AI agent task with natural language query
      /auto /help                  - Show this help message
      /auto /async /name <task_name> [query]         - Execute task asynchronously in background (name is required)
      /auto /queue [query]         - Add task to execution queue
      /auto /new [query]           - Create new conversation and execute query
      /auto /resume [id]           - Resume specific conversation by ID
      /auto /list                  - List all conversations
      /auto /rename [id] [name]    - Rename conversation
      /auto /export [id] [file_path] - Export conversation to markdown file
      /auto /command [command_file] [query] - Execute with specific command template

    Examples:
      /auto Add login functionality
      /auto /async /name my_task Refactor user module
      /auto /new Implement payment feature
      /auto /export conv-12345678 ./docs/conversation.md
      /auto /command deploy.md Deploy to production
    """


@byzerllm.prompt()
def auto_help_zh() -> str:
    """
    /auto 命令用法:
      /auto [查询]                 - 使用自然语言执行 AI 智能体任务
      /auto /help                  - 显示此帮助信息
      /auto /async /name <任务名> [查询]          - 在后台异步执行任务（必须提供 /name）
      /auto /queue [查询]          - 将任务添加到执行队列
      /auto /new [查询]            - 创建新对话并执行查询
      /auto /resume [id]           - 通过ID恢复特定对话
      /auto /list                  - 列出所有对话
      /auto /rename [id] [名称]    - 重命名对话
      /auto /export [id] [文件路径] - 将对话导出为markdown文件
      /auto /command [命令文件] [查询] - 使用特定命令模板执行

    示例:
      /auto 添加登录功能
      /auto /async /name my_task 重构用户模块
      /auto /new 实现支付功能
      /auto /export conv-12345678 ./docs/conversation.md
      /auto /command deploy.md 部署到生产环境
    """


@byzerllm.prompt()
def auto_help_ja() -> str:
    """
    /auto コマンド使用法:
      /auto [クエリ]               - 自然言語でAIエージェントタスクを実行
      /auto /help                  - このヘルプメッセージを表示
      /auto /async /name <タスク名> [クエリ]        - バックグラウンドで非同期にタスクを実行（/name 必須）
      /auto /queue [クエリ]        - タスクを実行キューに追加
      /auto /new [クエリ]          - 新しい会話を作成してクエリを実行
      /auto /resume [id]           - IDで特定の会話を再開
      /auto /list                  - すべての会話をリスト
      /auto /rename [id] [名前]    - 会話の名前を変更
      /auto /export [id] [ファイルパス] - 会話をmarkdownファイルにエクスポート
      /auto /command [コマンドファイル] [クエリ] - 特定のコマンドテンプレートで実行

    例:
      /auto ログイン機能を追加
      /auto /async /name my_task ユーザーモジュールをリファクタリング
      /auto /new 支払い機能を実装
      /auto /export conv-12345678 ./docs/conversation.md
      /auto /command deploy.md 本番環境にデプロイ
    """


@byzerllm.prompt()
def auto_help_ar() -> str:
    """
    استخدام أمر /auto:
      /auto [استعلام]              - تنفيذ مهمة وكيل AI باستخدام استعلام اللغة الطبيعية
      /auto /help                  - إظهار رسالة المساعدة هذه
      /auto /async /name <اسم_المهمة> [استعلام]       - تنفيذ المهمة بشكل غير متزامن في الخلفية (name مطلوب)
      /auto /queue [استعلام]       - إضافة مهمة إلى قائمة التنفيذ
      /auto /new [استعلام]         - إنشاء محادثة جديدة وتنفيذ الاستعلام
      /auto /resume [id]           - استئناف محادثة محددة بواسطة المعرف
      /auto /list                  - قائمة بجميع المحادثات
      /auto /rename [id] [اسم]     - إعادة تسمية المحادثة
      /auto /export [id] [مسار_الملف] - تصدير المحادثة إلى ملف markdown
      /auto /command [ملف_الأمر] [استعلام] - تنفيذ باستخدام قالب أمر محدد

    أمثلة:
      /auto إضافة وظيفة تسجيل الدخول
      /auto /async /name my_task إعادة هيكلة وحدة المستخدم
      /auto /new تنفيذ ميزة الدفع
      /auto /export conv-12345678 ./docs/conversation.md
      /auto /command deploy.md النشر في الإنتاج
    """


@byzerllm.prompt()
def auto_help_ru() -> str:
    """
    Использование команды /auto:
      /auto [запрос]               - Выполнить задачу AI агента с запросом на естественном языке
      /auto /help                  - Показать это сообщение справки
      /auto /async /name <имя_задачи> [запрос]        - Выполнить задачу асинхронно в фоне (требуется /name)
      /auto /queue [запрос]        - Добавить задачу в очередь выполнения
      /auto /new [запрос]          - Создать новый разговор и выполнить запрос
      /auto /resume [id]           - Возобновить конкретный разговор по ID
      /auto /list                  - Показать все разговоры
      /auto /rename [id] [имя]     - Переименовать разговор
      /auto /export [id] [путь_к_файлу] - Экспортировать разговор в markdown файл
      /auto /command [файл_команды] [запрос] - Выполнить с конкретным шаблоном команды

    Примеры:
      /auto Добавить функцию входа
      /auto /async /name my_task Рефакторить модуль пользователя
      /auto /new Реализовать функцию оплаты
      /auto /export conv-12345678 ./docs/conversation.md
      /auto /command deploy.md Развернуть в продакшен
    """


# /coding command help text definitions
@byzerllm.prompt()
def coding_help_en() -> str:
    """
    /coding command usage:
      /coding [query]       - Generate or modify code based on requirements
      /coding /help         - Show this help message
      /coding /apply [query] - Apply previous conversation context and generate code
      /coding /next [query] - Predict and suggest next development tasks

    Examples:
      /coding Add user authentication feature
      /coding /apply Implement password encryption
      /coding /next What should I do next?
    """


@byzerllm.prompt()
def coding_help_zh() -> str:
    """
    /coding 命令用法:
      /coding [查询]       - 根据需求生成或修改代码
      /coding /help        - 显示此帮助信息
      /coding /apply [查询] - 应用之前的对话上下文并生成代码
      /coding /next [查询] - 预测并建议下一步开发任务

    示例:
      /coding 添加用户认证功能
      /coding /apply 实现密码加密
      /coding /next 接下来应该做什么?
    """


@byzerllm.prompt()
def coding_help_ja() -> str:
    """
    /coding コマンド使用法:
      /coding [クエリ]       - 要件に基づいてコードを生成または変更
      /coding /help         - このヘルプメッセージを表示
      /coding /apply [クエリ] - 以前の会話コンテキストを適用してコードを生成
      /coding /next [クエリ] - 次の開発タスクを予測して提案

    例:
      /coding ユーザー認証機能を追加
      /coding /apply パスワード暗号化を実装
      /coding /next 次に何をすべきですか?
    """


@byzerllm.prompt()
def coding_help_ar() -> str:
    """
    استخدام أمر /coding:
      /coding [استعلام]       - إنشاء أو تعديل الكود بناءً على المتطلبات
      /coding /help         - إظهار رسالة المساعدة هذه
      /coding /apply [استعلام] - تطبيق سياق المحادثة السابقة وإنشاء الكود
      /coding /next [استعلام] - التنبؤ واقتراح مهام التطوير التالية

    أمثلة:
      /coding إضافة ميزة مصادقة المستخدم
      /coding /apply تنفيذ تشفير كلمة المرور
      /coding /next ماذا يجب أن أفعل بعد ذلك؟
    """


@byzerllm.prompt()
def coding_help_ru() -> str:
    """
    Использование команды /coding:
      /coding [запрос]       - Генерировать или изменять код на основе требований
      /coding /help         - Показать это сообщение справки
      /coding /apply [запрос] - Применить контекст предыдущего разговора и сгенерировать код
      /coding /next [запрос] - Предсказать и предложить следующие задачи разработки

    Примеры:
      /coding Добавить функцию аутентификации пользователя
      /coding /apply Реализовать шифрование пароля
      /coding /next Что мне делать дальше?
    """


# /chat command help text definitions
@byzerllm.prompt()
def chat_help_en() -> str:
    """
    /chat command usage:
      /chat [query]         - Chat with AI about code without modifying files
      /chat /help           - Show this help message
      /chat /new [query]    - Start new chat session
      /chat /learn [query]  - Learn from code and generate documentation
      /chat /review [query] - Review code changes
      /chat /no_context [query] - Chat without loading project files
      /chat /copy [query]   - Copy response to clipboard
      /chat /save [query]   - Save response to global memory
      /chat /mcp [query]    - Use MCP tools in chat
      /chat /rag [query]    - Use RAG search in chat

    Examples:
      /chat Explain the login logic
      /chat /new How does authentication work?
      /chat /learn Generate API documentation
      /chat /review Check recent changes
    """


@byzerllm.prompt()
def chat_help_zh() -> str:
    """
    /chat 命令用法:
      /chat [查询]         - 与AI聊天讨论代码，不修改文件
      /chat /help          - 显示此帮助信息
      /chat /new [查询]    - 开始新的聊天会话
      /chat /learn [查询]  - 从代码中学习并生成文档
      /chat /review [查询] - 审查代码变更
      /chat /no_context [查询] - 不加载项目文件的聊天
      /chat /copy [查询]   - 复制响应到剪贴板
      /chat /save [查询]   - 保存响应到全局记忆
      /chat /mcp [查询]    - 在聊天中使用MCP工具
      /chat /rag [查询]    - 在聊天中使用RAG搜索

    示例:
      /chat 解释登录逻辑
      /chat /new 认证是如何工作的?
      /chat /learn 生成API文档
      /chat /review 检查最近的变更
    """


@byzerllm.prompt()
def chat_help_ja() -> str:
    """
    /chat コマンド使用法:
      /chat [クエリ]         - ファイルを変更せずにAIとコードについてチャット
      /chat /help           - このヘルプメッセージを表示
      /chat /new [クエリ]    - 新しいチャットセッションを開始
      /chat /learn [クエリ]  - コードから学習してドキュメントを生成
      /chat /review [クエリ] - コード変更をレビュー
      /chat /no_context [クエリ] - プロジェクトファイルを読み込まずにチャット
      /chat /copy [クエリ]   - レスポンスをクリップボードにコピー
      /chat /save [クエリ]   - レスポンスをグローバルメモリに保存
      /chat /mcp [クエリ]    - チャットでMCPツールを使用
      /chat /rag [クエリ]    - チャットでRAG検索を使用

    例:
      /chat ログインロジックを説明
      /chat /new 認証はどのように機能しますか?
      /chat /learn APIドキュメントを生成
      /chat /review 最近の変更を確認
    """


@byzerllm.prompt()
def chat_help_ar() -> str:
    """
    استخدام أمر /chat:
      /chat [استعلام]         - الدردشة مع AI حول الكود دون تعديل الملفات
      /chat /help           - إظهار رسالة المساعدة هذه
      /chat /new [استعلام]    - بدء جلسة دردشة جديدة
      /chat /learn [استعلام]  - التعلم من الكود وإنشاء التوثيق
      /chat /review [استعلام] - مراجعة تغييرات الكود
      /chat /no_context [استعلام] - الدردشة دون تحميل ملفات المشروع
      /chat /copy [استعلام]   - نسخ الرد إلى الحافظة
      /chat /save [استعلام]   - حفظ الرد في الذاكرة العامة
      /chat /mcp [استعلام]    - استخدام أدوات MCP في الدردشة
      /chat /rag [استعلام]    - استخدام بحث RAG في الدردشة

    أمثلة:
      /chat اشرح منطق تسجيل الدخول
      /chat /new كيف تعمل المصادقة؟
      /chat /learn إنشاء توثيق API
      /chat /review التحقق من التغييرات الأخيرة
    """


@byzerllm.prompt()
def chat_help_ru() -> str:
    """
    Использование команды /chat:
      /chat [запрос]         - Чат с AI о коде без изменения файлов
      /chat /help           - Показать это сообщение справки
      /chat /new [запрос]    - Начать новую сессию чата
      /chat /learn [запрос]  - Изучить код и сгенерировать документацию
      /chat /review [запрос] - Проверить изменения кода
      /chat /no_context [запрос] - Чат без загрузки файлов проекта
      /chat /copy [запрос]   - Скопировать ответ в буфер обмена
      /chat /save [запрос]   - Сохранить ответ в глобальную память
      /chat /mcp [запрос]    - Использовать инструменты MCP в чате
      /chat /rag [запрос]    - Использовать поиск RAG в чате

    Примеры:
      /chat Объясните логику входа
      /chat /new Как работает аутентификация?
      /chat /learn Сгенерировать документацию API
      /chat /review Проверить недавние изменения
    """


# /lib command help text definitions
@byzerllm.prompt()
def lib_help_en() -> str:
    """
    /lib command usage:
      /lib /add <library>     - Add a library to the project
      /lib /remove <library>  - Remove a library from the project
      /lib /list              - List all added libraries
      /lib /list_all          - List all available libraries
      /lib /set-proxy [url]   - Set proxy for library downloads
      /lib /refresh           - Refresh the library repository
      /lib /get <package>     - Get documentation for a package
      /lib /help              - Show this help message

    Examples:
      /lib /add pandas
      /lib /remove numpy
      /lib /list
      /lib /get requests
    """


@byzerllm.prompt()
def lib_help_zh() -> str:
    """
    /lib 命令用法:
      /lib /add <库名>        - 向项目添加库
      /lib /remove <库名>     - 从项目中移除库
      /lib /list              - 列出所有已添加的库
      /lib /list_all          - 列出所有可用的库
      /lib /set-proxy [url]   - 设置库下载代理
      /lib /refresh           - 刷新库仓库
      /lib /get <包名>        - 获取包的文档
      /lib /help              - 显示此帮助信息

    示例:
      /lib /add pandas
      /lib /remove numpy
      /lib /list
      /lib /get requests
    """


@byzerllm.prompt()
def lib_help_ja() -> str:
    """
    /lib コマンド使用法:
      /lib /add <ライブラリ>   - プロジェクトにライブラリを追加
      /lib /remove <ライブラリ> - プロジェクトからライブラリを削除
      /lib /list              - 追加されたライブラリを一覧表示
      /lib /list_all          - 利用可能なライブラリを一覧表示
      /lib /set-proxy [url]   - ライブラリダウンロード用プロキシを設定
      /lib /refresh           - ライブラリリポジトリを更新
      /lib /get <パッケージ>   - パッケージのドキュメントを取得
      /lib /help              - このヘルプメッセージを表示

    例:
      /lib /add pandas
      /lib /remove numpy
      /lib /list
      /lib /get requests
    """


@byzerllm.prompt()
def lib_help_ar() -> str:
    """
    استخدام أمر /lib:
      /lib /add <مكتبة>       - إضافة مكتبة إلى المشروع
      /lib /remove <مكتبة>    - إزالة مكتبة من المشروع
      /lib /list              - عرض جميع المكتبات المضافة
      /lib /list_all          - عرض جميع المكتبات المتاحة
      /lib /set-proxy [url]   - تعيين وكيل لتحميل المكتبات
      /lib /refresh           - تحديث مستودع المكتبات
      /lib /get <حزمة>        - الحصول على وثائق الحزمة
      /lib /help              - إظهار رسالة المساعدة هذه

    أمثلة:
      /lib /add pandas
      /lib /remove numpy
      /lib /list
      /lib /get requests
    """


@byzerllm.prompt()
def lib_help_ru() -> str:
    """
    Использование команды /lib:
      /lib /add <библиотека>  - Добавить библиотеку в проект
      /lib /remove <библиотека> - Удалить библиотеку из проекта
      /lib /list              - Показать все добавленные библиотеки
      /lib /list_all          - Показать все доступные библиотеки
      /lib /set-proxy [url]   - Установить прокси для загрузки библиотек
      /lib /refresh           - Обновить репозиторий библиотек
      /lib /get <пакет>       - Получить документацию пакета
      /lib /help              - Показать это сообщение справки

    Примеры:
      /lib /add pandas
      /lib /remove numpy
      /lib /list
      /lib /get requests
    """


# /commit command help text definitions
@byzerllm.prompt()
def commit_help_en() -> str:
    """
    /commit command usage:
      /commit [message]     - Generate and commit changes with AI-generated commit message
      /commit /help          - Show this help message
      /commit /no_diff       - Commit without showing diff (future feature)

    Examples:
      /commit Fix user authentication bug
      /commit Add new feature for payment processing
      /commit Refactor database connection logic
    """


@byzerllm.prompt()
def commit_help_zh() -> str:
    """
    /commit 命令用法:
      /commit [消息]         - 使用AI生成的提交消息提交代码变更
      /commit /help          - 显示此帮助信息
      /commit /no_diff       - 不显示差异直接提交（未来功能）

    示例:
      /commit 修复用户认证bug
      /commit 添加支付处理新功能
      /commit 重构数据库连接逻辑
    """


@byzerllm.prompt()
def commit_help_ja() -> str:
    """
    /commit コマンド使用法:
      /commit [メッセージ]   - AI生成のコミットメッセージで変更をコミット
      /commit /help          - このヘルプメッセージを表示
      /commit /no_diff       - 差分を表示せずにコミット（将来の機能）

    例:
      /commit ユーザー認証バグを修正
      /commit 支払い処理の新機能を追加
      /commit データベース接続ロジックをリファクタリング
    """


@byzerllm.prompt()
def commit_help_ar() -> str:
    """
    استخدام أمر /commit:
      /commit [رسالة]       - إجراء commit للتغييرات مع رسالة commit مولدة بواسطة AI
      /commit /help          - إظهار رسالة المساعدة هذه
      /commit /no_diff       - إجراء commit دون إظهار الاختلافات (ميزة مستقبلية)

    أمثلة:
      /commit إصلاح خطأ مصادقة المستخدم
      /commit إضافة ميزة جديدة لمعالجة الدفع
      /commit إعادة هيكلة منطق اتصال قاعدة البيانات
    """


@byzerllm.prompt()
def commit_help_ru() -> str:
    """
    Использование команды /commit:
      /commit [сообщение]   - Зафиксировать изменения с сообщением коммита, сгенерированным AI
      /commit /help          - Показать это сообщение справки
      /commit /no_diff       - Зафиксировать без показа различий (будущая функция)

    Примеры:
      /commit Исправить ошибку аутентификации пользователя
      /commit Добавить новую функцию обработки платежей
      /commit Рефакторинг логики подключения к базе данных
    """


# /workflow command help text definitions
@byzerllm.prompt()
def workflow_help_en() -> str:
    """
    /workflow command usage:
      /workflow <workflow_name>              - Run a predefined workflow
      /workflow <workflow_name> key=value    - Run workflow with variable overrides
      /workflow /help                        - Show this help message

    Description:
      Execute predefined workflows with optional variable overrides via key-value pairs.

    Examples:
      /workflow my-workflow
      /workflow my-workflow query="Implement login"
      /workflow deploy env=prod version=1.0
      /workflow analysis task="Review code" depth=2

    Workflow search paths (by priority):
      1. .autocoderworkflow/                 (project-level, highest priority)
      2. .auto-coder/.autocoderworkflow/     (project-level)
      3. ~/.auto-coder/.autocoderworkflow/   (global-level)
    """


@byzerllm.prompt()
def workflow_help_zh() -> str:
    """
    /workflow 命令用法:
      /workflow <workflow名称>               - 运行预定义的workflow
      /workflow <workflow名称> key=value     - 运行workflow并覆盖变量
      /workflow /help                        - 显示此帮助信息

    说明:
      执行预定义的workflow，支持通过键值对参数覆盖workflow中的变量。

    示例:
      /workflow my-workflow
      /workflow my-workflow query="实现登录"
      /workflow deploy env=prod version=1.0
      /workflow analysis task="审查代码" depth=2

    Workflow 搜索路径（按优先级）:
      1. .autocoderworkflow/                 (项目级，最高优先级)
      2. .auto-coder/.autocoderworkflow/     (项目级)
      3. ~/.auto-coder/.autocoderworkflow/   (全局级)
    """


@byzerllm.prompt()
def workflow_help_ja() -> str:
    """
    /workflow コマンド使用法:
      /workflow <workflow名>                 - 事前定義されたworkflowを実行
      /workflow <workflow名> key=value       - 変数をオーバーライドしてworkflowを実行
      /workflow /help                        - このヘルプメッセージを表示

    説明:
      事前定義されたworkflowを実行し、キーと値のペアを使用して変数をオーバーライドできます。

    例:
      /workflow my-workflow
      /workflow my-workflow query="ログインを実装"
      /workflow deploy env=prod version=1.0
      /workflow analysis task="コードレビュー" depth=2

    Workflow 検索パス（優先順位順）:
      1. .autocoderworkflow/                 (プロジェクトレベル、最高優先度)
      2. .auto-coder/.autocoderworkflow/     (プロジェクトレベル)
      3. ~/.auto-coder/.autocoderworkflow/   (グローバルレベル)
    """


@byzerllm.prompt()
def workflow_help_ar() -> str:
    """
    استخدام أمر /workflow:
      /workflow <اسم_workflow>               - تشغيل workflow محدد مسبقاً
      /workflow <اسم_workflow> key=value     - تشغيل workflow مع تجاوز المتغيرات
      /workflow /help                        - إظهار رسالة المساعدة هذه

    الوصف:
      تنفيذ workflows المحددة مسبقاً مع إمكانية تجاوز المتغيرات عبر أزواج المفتاح والقيمة.

    أمثلة:
      /workflow my-workflow
      /workflow my-workflow query="تنفيذ تسجيل الدخول"
      /workflow deploy env=prod version=1.0
      /workflow analysis task="مراجعة الكود" depth=2

    مسارات البحث عن Workflow (حسب الأولوية):
      1. .autocoderworkflow/                 (مستوى المشروع، أعلى أولوية)
      2. .auto-coder/.autocoderworkflow/     (مستوى المشروع)
      3. ~/.auto-coder/.autocoderworkflow/   (مستوى عام)
    """


@byzerllm.prompt()
def workflow_help_ru() -> str:
    """
    Использование команды /workflow:
      /workflow <имя_workflow>               - Запустить предопределенный workflow
      /workflow <имя_workflow> key=value     - Запустить workflow с переопределением переменных
      /workflow /help                        - Показать это сообщение справки

    Описание:
      Выполнение предопределенных workflow с возможностью переопределения переменных через пары ключ-значение.

    Примеры:
      /workflow my-workflow
      /workflow my-workflow query="Реализовать вход"
      /workflow deploy env=prod version=1.0
      /workflow analysis task="Проверить код" depth=2

    Пути поиска Workflow (по приоритету):
      1. .autocoderworkflow/                 (уровень проекта, наивысший приоритет)
      2. .auto-coder/.autocoderworkflow/     (уровень проекта)
      3. ~/.auto-coder/.autocoderworkflow/   (глобальный уровень)
    """


# /async command help text definitions
@byzerllm.prompt()
def async_help_en() -> str:
    """
    /auto /async command usage:
      /auto /async /name <task_name> [query] - Execute task asynchronously in background (name is required)
      /auto /async /help                  - Show this help message
      /auto /async /list                  - List all async tasks
      /auto /async /task [task_id]        - Show details of a specific task
      /auto /async /kill <task_id>        - Kill a running task
      /auto /async /drop <task_id>        - Delete a task and all its related files

    Usage (name required):
      /auto /async /name <task_name> "<your query>"
      /auto /async /name <task_name> /model <model_name> "<your query>"
      /auto /async /name <task_name> /loop <count> "<your query>"
      /auto /async /name <task_name> /time <duration> "<your query>"
      /auto /async /name <task_name> /workflow <workflow_name> "<your query>"
      /auto /async /name <task_name> /vars '{"k":"v"}' "<your query>"

    Options:
      /name <task_name>   Required. Unique identifier for this async task.
      /model <model_name> Optional. Use a specific model.
      /loop <count>        Optional. Execute task multiple times.
      /time <duration>     Optional. Execute task for a specified duration (e.g., 5m, 1h).
      /workflow <name>     Optional. Execute a workflow by name.
      /vars <json>         Optional. JSON variables for the task.

    Examples:
      /auto /async /name my_task "Implement user authentication"
      /auto /async /name my_task /model gpt-4 "Refactor user module"
      /auto /async /name my_task /loop 3 "Continuous improvement task"
      /auto /async /name my_task /time 5m "Background analysis task"
      /auto /async /name my_task /workflow deploy "Deploy to staging"
      /auto /async /drop task123
    """


@byzerllm.prompt()
def async_help_zh() -> str:
    """
    /auto /async 命令用法:
      /auto /async /name <任务名> [查询] - 在后台异步执行任务（/name 为必选）
      /auto /async /help                  - 显示此帮助信息
      /auto /async /list                  - 列出所有异步任务
      /auto /async /task [任务ID]        - 显示特定任务的详情
      /auto /async /kill <任务ID>        - 终止正在运行的任务
      /auto /async /drop <任务ID>        - 删除任务及其所有相关文件

    用法（必须包含 /name）:
      /auto /async /name <任务名> "你的需求"
      /auto /async /name <任务名> /model <模型名> "你的需求"
      /auto /async /name <任务名> /loop <次数> "你的需求"
      /auto /async /name <任务名> /time <时长> "你的需求"
      /auto /async /name <任务名> /workflow <工作流名> "你的需求"
      /auto /async /name <任务名> /vars '{"k":"v"}' "你的需求"

    参数:
      /name <任务名>     必选。用于唯一标识该异步任务。
      /model <模型名>    可选。指定使用的模型。
      /loop <次数>       可选。多次执行任务。
      /time <时长>       可选。指定执行时长（如 5m, 1h）。
      /workflow <名称>   可选。按名称执行工作流。
      /vars <json>       可选。任务 JSON 变量。

    示例:
      /auto /async /name my_task "实现用户认证功能"
      /auto /async /name my_task /model gpt-4 "重构用户模块"
      /auto /async /name my_task /loop 3 "持续改进任务"
      /auto /async /name my_task /time 5m "后台分析任务"
      /auto /async /name my_task /workflow deploy "部署到预发环境"
      /auto /async /drop task123
    """


@byzerllm.prompt()
def async_help_ja() -> str:
    """
    /auto /async コマンド使用法:
      /auto /async /name <タスク名> [クエリ] - バックグラウンドで非同期にタスクを実行（/name は必須）
      /auto /async /help                  - このヘルプメッセージを表示
      /auto /async /list                  - すべての非同期タスクをリスト
      /auto /async /task [タスクID]      - 特定のタスクの詳細を表示
      /auto /async /kill <タスクID>      - 実行中のタスクを終了
      /auto /async /drop <タスクID>      - タスクとすべての関連ファイルを削除

    使用法（/name は必須）:
      /auto /async /name <タスク名> "クエリ"
      /auto /async /name <タスク名> /model <モデル名> "クエリ"
      /auto /async /name <タスク名> /loop <回数> "クエリ"
      /auto /async /name <タスク名> /time <時間> "クエリ"
      /auto /async /name <タスク名> /workflow <ワークフロー名> "クエリ"
      /auto /async /name <タスク名> /vars '{"k":"v"}' "クエリ"

    オプション:
      /name <タスク名>   必須。非同期タスクの一意の識別子。
      /model <モデル名>  任意。特定のモデルを使用。
      /loop <回数>       任意。タスクを複数回実行。
      /time <時間>       任意。指定した時間実行（例: 5m, 1h）。
      /workflow <名前>   任意。ワークフロー名で実行。
      /vars <json>       任意。タスクの JSON 変数。

    例:
      /auto /async /name my_task "ユーザー認証を実装"
      /auto /async /name my_task /model gpt-4 "ユーザーモジュールをリファクタリング"
      /auto /async /name my_task /loop 3 "継続的改善タスク"
      /auto /async /name my_task /time 5m "バックグラウンド分析タスク"
      /auto /async /name my_task /workflow deploy "ステージングにデプロイ"
      /auto /async /drop task123
    """


@byzerllm.prompt()
def async_help_ar() -> str:
    """
    استخدام أمر /auto /async:
      /auto /async /name <اسم_المهمة> [استعلام] - تنفيذ المهمة بشكل غير متزامن في الخلفية (name مطلوب)
      /auto /async /help                  - إظهار رسالة المساعدة هذه
      /auto /async /list                  - قائمة بجميع المهام غير المتزامنة
      /auto /async /task [معرف_المهمة]  - إظهار تفاصيل مهمة محددة
      /auto /async /kill <معرف_المهمة>  - إنهاء مهمة قيد التشغيل
      /auto /async /drop <معرف_المهمة>  - حذف المهمة وجميع الملفات ذات الصلة

    الاستخدام (name مطلوب):
      /auto /async /name <اسم_المهمة> "استعلامك"
      /auto /async /name <اسم_المهمة> /model <اسم_النموذج> "استعلامك"
      /auto /async /name <اسم_المهمة> /loop <عدد> "استعلامك"
      /auto /async /name <اسم_المهمة> /time <المدة> "استعلامك"
      /auto /async /name <اسم_المهمة> /workflow <اسم_workflow> "استعلامك"
      /auto /async /name <اسم_المهمة> /vars '{"k":"v"}' "استعلامك"

    الخيارات:
      /name <اسم_المهمة>   مطلوب. معرّف فريد للمهمة غير المتزامنة.
      /model <اسم_النموذج> اختياري. استخدام نموذج محدد.
      /loop <عدد>           اختياري. تنفيذ المهمة عدة مرات.
      /time <المدة>          اختياري. تنفيذ لمدة محددة (مثال: 5m, 1h).
      /workflow <الاسم>     اختياري. تنفيذ workflow بالاسم.
      /vars <json>          اختياري. متغيرات JSON للمهمة.

    أمثلة:
      /auto /async /name my_task "تنفيذ مصادقة المستخدم"
      /auto /async /name my_task /model gpt-4 "إعادة هيكلة وحدة المستخدم"
      /auto /async /name my_task /loop 3 "مهمة تحسين مستمرة"
      /auto /async /name my_task /time 5m "مهمة تحليل في الخلفية"
      /auto /async /name my_task /workflow deploy "النشر إلى بيئة staging"
      /auto /async /drop task123
    """


@byzerllm.prompt()
def async_help_ru() -> str:
    """
    Использование команды /auto /async:
      /auto /async /name <имя_задачи> [запрос] - Выполнить задачу асинхронно в фоне (требуется параметр /name)
      /auto /async /help                  - Показать это сообщение справки
      /auto /async /list                  - Показать все асинхронные задачи
      /auto /async /task [идентификатор] - Показать детали конкретной задачи
      /auto /async /kill <идентификатор> - Завершить выполняющуюся задачу
      /auto /async /drop <идентификатор> - Удалить задачу и все связанные с ней файлы

    Использование (требуется /name):
      /auto /async /name <имя_задачи> "<запрос>"
      /auto /async /name <имя_задачи> /model <имя_модели> "<запрос>"
      /auto /async /name <имя_задачи> /loop <количество> "<запрос>"
      /auto /async /name <имя_задачи> /time <продолжительность> "<запрос>"
      /auto /async /name <имя_задачи> /workflow <имя_workflow> "<запрос>"
      /auto /async /name <имя_задачи> /vars '{"k":"v"}' "<запрос>"

    Параметры:
      /name <имя_задачи>   Обязательно. Уникальный идентификатор асинхронной задачи.
      /model <имя_модели>  Необязательно. Использовать конкретную модель.
      /loop <количество>   Необязательно. Выполнить несколько раз.
      /time <продолжительность> Необязательно. Выполнять указанное время (напр., 5m, 1h).
      /workflow <имя>     Необязательно. Выполнить workflow по имени.
      /vars <json>         Необязательно. JSON-переменные задачи.

    Примеры:
      /auto /async /name my_task "Реализовать аутентификацию пользователя"
      /auto /async /name my_task /model gpt-4 "Рефакторинг модуля пользователя"
      /auto /async /name my_task /loop 3 "Задача непрерывного улучшения"
      /auto /async /name my_task /time 5m "Задача фонового анализа"
      /auto /async /name my_task /workflow deploy "Деплой на staging"
      /auto /async /drop task123
    """


# Workflow command runtime messages
WORKFLOW_MESSAGES = {
    "workflow_error_no_name": {
        "en": "Error: Please specify workflow name",
        "zh": "错误: 请指定 workflow 名称",
        "ja": "エラー: workflow 名を指定してください",
        "ar": "خطأ: يرجى تحديد اسم workflow",
        "ru": "Ошибка: Укажите имя workflow",
    },
    "workflow_help_hint": {
        "en": "Use /workflow /help to see help information",
        "zh": "使用 /workflow /help 查看帮助信息",
        "ja": "/workflow /help を使用してヘルプ情報を表示",
        "ar": "استخدم /workflow /help لعرض معلومات المساعدة",
        "ru": "Используйте /workflow /help для просмотра справки",
    },
    "workflow_running": {
        "en": "Running workflow: {{workflow_name}}",
        "zh": "正在运行 workflow: {{workflow_name}}",
        "ja": "workflow を実行中: {{workflow_name}}",
        "ar": "تشغيل workflow: {{workflow_name}}",
        "ru": "Запуск workflow: {{workflow_name}}",
    },
    "workflow_parameters": {
        "en": "Parameters: {{kwargs}}",
        "zh": "参数: {{kwargs}}",
        "ja": "パラメータ: {{kwargs}}",
        "ar": "المعاملات: {{kwargs}}",
        "ru": "Параметры: {{kwargs}}",
    },
    "workflow_not_found": {
        "en": "Error: Workflow file not found: {{workflow_name}}",
        "zh": "错误: 未找到 workflow 文件: {{workflow_name}}",
        "ja": "エラー: workflow ファイルが見つかりません: {{workflow_name}}",
        "ar": "خطأ: لم يتم العثور على ملف workflow: {{workflow_name}}",
        "ru": "Ошибка: Файл workflow не найден: {{workflow_name}}",
    },
    "workflow_available_list": {
        "en": "Available workflows:",
        "zh": "可用的 workflows:",
        "ja": "利用可能な workflows:",
        "ar": "workflows المتاحة:",
        "ru": "Доступные workflows:",
    },
    "workflow_none_found": {
        "en": "(No workflows found)",
        "zh": "(没有找到任何 workflow)",
        "ja": "(workflow が見つかりません)",
        "ar": "(لم يتم العثور على أي workflows)",
        "ru": "(Workflows не найдены)",
    },
    "workflow_run_failed": {
        "en": "Failed to run workflow: {{error}}",
        "zh": "运行 workflow 失败: {{error}}",
        "ja": "workflow の実行に失敗しました: {{error}}",
        "ar": "فشل تشغيل workflow: {{error}}",
        "ru": "Не удалось запустить workflow: {{error}}",
    },
    "workflow_available_title": {
        "en": "Available workflows:",
        "zh": "可用的 workflows:",
        "ja": "利用可能な workflows:",
        "ar": "workflows المتاحة:",
        "ru": "Доступные workflows:",
    },
    "workflow_no_workflows_found": {
        "en": "No workflows found",
        "zh": "当前没有找到任何 workflow",
        "ja": "workflow が見つかりません",
        "ar": "لم يتم العثور على أي workflows",
        "ru": "Workflows не найдены",
    },
}


# Build the final message dictionary from prompt functions
# 使用 prompt() 获取 docstring 内容
COMMAND_HELP_MESSAGES = {
    "conf_help_text": {
        "en": conf_help_en.prompt(),
        "zh": conf_help_zh.prompt(),
        "ja": conf_help_ja.prompt(),
        "ar": conf_help_ar.prompt(),
        "ru": conf_help_ru.prompt(),
    },
    "auto_help_text": {
        "en": auto_help_en.prompt(),
        "zh": auto_help_zh.prompt(),
        "ja": auto_help_ja.prompt(),
        "ar": auto_help_ar.prompt(),
        "ru": auto_help_ru.prompt(),
    },
    "coding_help_text": {
        "en": coding_help_en.prompt(),
        "zh": coding_help_zh.prompt(),
        "ja": coding_help_ja.prompt(),
        "ar": coding_help_ar.prompt(),
        "ru": coding_help_ru.prompt(),
    },
    "chat_help_text": {
        "en": chat_help_en.prompt(),
        "zh": chat_help_zh.prompt(),
        "ja": chat_help_ja.prompt(),
        "ar": chat_help_ar.prompt(),
        "ru": chat_help_ru.prompt(),
    },
    "commit_help_text": {
        "en": commit_help_en.prompt(),
        "zh": commit_help_zh.prompt(),
        "ja": commit_help_ja.prompt(),
        "ar": commit_help_ar.prompt(),
        "ru": commit_help_ru.prompt(),
    },
    "lib_help_text": {
        "en": lib_help_en.prompt(),
        "zh": lib_help_zh.prompt(),
        "ja": lib_help_ja.prompt(),
        "ar": lib_help_ar.prompt(),
        "ru": lib_help_ru.prompt(),
    },
    "workflow_help_text": {
        "en": workflow_help_en.prompt(),
        "zh": workflow_help_zh.prompt(),
        "ja": workflow_help_ja.prompt(),
        "ar": workflow_help_ar.prompt(),
        "ru": workflow_help_ru.prompt(),
    },
    "async_help_text": {
        "en": async_help_en.prompt(),
        "zh": async_help_zh.prompt(),
        "ja": async_help_ja.prompt(),
        "ar": async_help_ar.prompt(),
        "ru": async_help_ru.prompt(),
    },
}

# Merge workflow runtime messages into COMMAND_HELP_MESSAGES
COMMAND_HELP_MESSAGES.update(WORKFLOW_MESSAGES)
