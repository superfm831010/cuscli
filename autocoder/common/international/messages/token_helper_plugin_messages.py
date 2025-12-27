"""
Token Helper Plugin 国际化消息
定义 Token Helper Plugin 中使用的所有国际化消息
"""

# Token Helper Plugin 消息
TOKEN_HELPER_PLUGIN_MESSAGES = {
    # 插件状态消息
    "plugin_token_initialized": {
        "en": "Token Helper plugin initialized",
        "zh": "Token助手插件已初始化",
        "ja": "Tokenヘルパープラグインが初期化されました",
        "ar": "تم تهيئة مكون Token المساعد",
        "ru": "Плагин помощника Token инициализирован"
    },
    "plugin_token_shutdown": {
        "en": "Token Helper plugin shutdown",
        "zh": "Token助手插件已关闭",
        "ja": "Tokenヘルパープラグインがシャットダウンされました",
        "ar": "تم إغلاق مكون Token المساعد",
        "ru": "Плагин помощника Token выключен"
    },

    # 命令描述
    "plugin_token_cmd_count_desc": {
        "en": "Count tokens in all project files",
        "zh": "统计项目所有文件的token数量",
        "ja": "プロジェクトの全ファイルのトークン数をカウント",
        "ar": "عد الرموز في جميع ملفات المشروع",
        "ru": "Подсчитать токены во всех файлах проекта"
    },
    "plugin_token_cmd_top_desc": {
        "en": "Show top N files by token count",
        "zh": "显示token数量最多的N个文件",
        "ja": "トークン数上位N件のファイルを表示",
        "ar": "عرض أعلى N ملفات حسب عدد الرموز",
        "ru": "Показать топ N файлов по количеству токенов"
    },
    "plugin_token_cmd_file_desc": {
        "en": "Count tokens in a specific file or directory",
        "zh": "统计指定文件或目录的token数量",
        "ja": "特定のファイルまたはディレクトリのトークン数をカウント",
        "ar": "عد الرموز في ملف أو دليل محدد",
        "ru": "Подсчитать токены в определенном файле или директории"
    },
    "plugin_token_cmd_summary_desc": {
        "en": "Show token count summary for the project",
        "zh": "显示项目token统计摘要",
        "ja": "プロジェクトのトークン数サマリーを表示",
        "ar": "عرض ملخص عدد الرموز للمشروع",
        "ru": "Показать сводку по токенам проекта"
    },

    # 操作过程消息
    "plugin_token_counting_project": {
        "en": "Counting tokens in project: {{project_dir}}",
        "zh": "正在统计项目token: {{project_dir}}",
        "ja": "プロジェクトのトークンをカウント中: {{project_dir}}",
        "ar": "عد الرموز في المشروع: {{project_dir}}",
        "ru": "Подсчет токенов в проекте: {{project_dir}}"
    },
    "plugin_token_file_types": {
        "en": "File types: {{project_type}}",
        "zh": "文件类型: {{project_type}}",
        "ja": "ファイルタイプ: {{project_type}}",
        "ar": "أنواع الملفات: {{project_type}}",
        "ru": "Типы файлов: {{project_type}}"
    },
    "plugin_token_scanning_files": {
        "en": "Scanning files and counting tokens...",
        "zh": "扫描文件并统计token...",
        "ja": "ファイルをスキャンしてトークンをカウント中...",
        "ar": "فحص الملفات وعد الرموز...",
        "ru": "Сканирование файлов и подсчет токенов..."
    },
    "plugin_token_processed_files": {
        "en": "Processed {{file_count}} files...",
        "zh": "已处理 {{file_count}} 个文件...",
        "ja": "{{file_count}}件のファイルを処理しました...",
        "ar": "تم معالجة {{file_count}} ملفًا...",
        "ru": "Обработано {{file_count}} файлов..."
    },
    "plugin_token_count_complete": {
        "en": "Token count complete!",
        "zh": "Token统计完成!",
        "ja": "トークンカウントが完了しました!",
        "ar": "اكتمل عد الرموز!",
        "ru": "Подсчет токенов завершен!"
    },
    "plugin_token_total_files": {
        "en": "Total files: {{file_count}}",
        "zh": "总文件数: {{file_count}}",
        "ja": "総ファイル数: {{file_count}}",
        "ar": "إجمالي الملفات: {{file_count}}",
        "ru": "Всего файлов: {{file_count}}"
    },
    "plugin_token_total_tokens": {
        "en": "Total tokens: {{total_tokens}}",
        "zh": "总token数: {{total_tokens}}",
        "ja": "総トークン数: {{total_tokens}}",
        "ar": "إجمالي الرموز: {{total_tokens}}",
        "ru": "Всего токенов: {{total_tokens}}"
    },

    # 帮助提示消息
    "plugin_token_use_top_help": {
        "en": "Use /token/top N to see the top N files by token count",
        "zh": "使用 /token/top N 查看token数量最多的N个文件",
        "ja": "/token/top N を使用してトークン数上位N件のファイルを表示",
        "ar": "استخدم /token/top N لرؤية أعلى N ملفات حسب عدد الرموز",
        "ru": "Используйте /token/top N для просмотра топ N файлов по токенам"
    },
    "plugin_token_use_summary_help": {
        "en": "Use /token/summary to see a summary by file type",
        "zh": "使用 /token/summary 查看按文件类型分组的摘要",
        "ja": "/token/summary を使用してファイルタイプ別のサマリーを表示",
        "ar": "استخدم /token/summary لرؤية ملخص حسب نوع الملف",
        "ru": "Используйте /token/summary для просмотра сводки по типам файлов"
    },

    # 错误消息
    "plugin_token_error_prefix": {
        "en": "Error:",
        "zh": "错误:",
        "ja": "エラー:",
        "ar": "خطأ:",
        "ru": "Ошибка:"
    },
    "plugin_token_no_data": {
        "en": "No token count data available. Run /token/count first.",
        "zh": "没有token统计数据。请先运行 /token/count。",
        "ja": "トークンカウントデータがありません。最初に /token/count を実行してください。",
        "ar": "لا توجد بيانات عدد الرموز. قم بتشغيل /token/count أولاً.",
        "ru": "Нет данных о подсчете токенов. Сначала выполните /token/count."
    },
    "plugin_token_invalid_value_default": {
        "en": "Invalid value: {{args}}. Using default of 10.",
        "zh": "无效值: {{args}}。使用默认值10。",
        "ja": "無効な値: {{args}}。デフォルトの10を使用します。",
        "ar": "قيمة غير صحيحة: {{args}}. استخدام القيمة الافتراضية 10.",
        "ru": "Неверное значение: {{args}}. Используется значение по умолчанию 10."
    },
    "plugin_token_specify_path": {
        "en": "Please specify a file or directory path.",
        "zh": "请指定文件或目录路径。",
        "ja": "ファイルまたはディレクトリのパスを指定してください。",
        "ar": "يرجى تحديد مسار ملف أو دليل.",
        "ru": "Пожалуйста, укажите путь к файлу или директории."
    },
    "plugin_token_path_not_exist": {
        "en": "Error: Path '{{path}}' does not exist.",
        "zh": "错误: 路径 '{{path}}' 不存在。",
        "ja": "エラー: パス '{{path}}' が存在しません。",
        "ar": "خطأ: المسار '{{path}}' غير موجود.",
        "ru": "Ошибка: Путь '{{path}}' не существует."
    },
    "plugin_token_not_file_or_dir": {
        "en": "Error: '{{path}}' is neither a file nor a directory.",
        "zh": "错误: '{{path}}' 既不是文件也不是目录。",
        "ja": "エラー: '{{path}}' はファイルでもディレクトリでもありません。",
        "ar": "خطأ: '{{path}}' ليس ملفًا ولا دليلاً.",
        "ru": "Ошибка: '{{path}}' не является ни файлом, ни директорией."
    },
    "plugin_token_counting_error": {
        "en": "Error counting tokens: {{error}}",
        "zh": "统计token时出错: {{error}}",
        "ja": "トークンカウント中にエラー: {{error}}",
        "ar": "خطأ في عد الرموز: {{error}}",
        "ru": "Ошибка при подсчете токенов: {{error}}"
    },
    "plugin_token_skip_binary": {
        "en": "Warning: Skipping binary file '{{file_path}}'",
        "zh": "警告: 跳过二进制文件 '{{file_path}}'",
        "ja": "警告: バイナリファイル '{{file_path}}' をスキップします",
        "ar": "تحذير: تخطي الملف الثنائي '{{file_path}}'",
        "ru": "Предупреждение: Пропуск бинарного файла '{{file_path}}'"
    },
    "plugin_token_read_error": {
        "en": "Error reading file '{{file_path}}': {{error}}",
        "zh": "读取文件 '{{file_path}}' 时出错: {{error}}",
        "ja": "ファイル '{{file_path}}' の読み取りエラー: {{error}}",
        "ar": "خطأ في قراءة الملف '{{file_path}}': {{error}}",
        "ru": "Ошибка чтения файла '{{file_path}}': {{error}}"
    },
    "plugin_token_processing_error": {
        "en": "Warning: Error processing '{{relative_path}}': {{error}}",
        "zh": "警告: 处理 '{{relative_path}}' 时出错: {{error}}",
        "ja": "警告: '{{relative_path}}' の処理エラー: {{error}}",
        "ar": "تحذير: خطأ في معالجة '{{relative_path}}': {{error}}",
        "ru": "Предупреждение: Ошибка обработки '{{relative_path}}': {{error}}"
    },

    # 单文件统计消息
    "plugin_token_file_info": {
        "en": "File: {{file_path}}",
        "zh": "文件: {{file_path}}",
        "ja": "ファイル: {{file_path}}",
        "ar": "الملف: {{file_path}}",
        "ru": "Файл: {{file_path}}"
    },
    "plugin_token_file_tokens": {
        "en": "Tokens: {{tokens}}",
        "zh": "Token数: {{tokens}}",
        "ja": "トークン数: {{tokens}}",
        "ar": "الرموز: {{tokens}}",
        "ru": "Токены: {{tokens}}"
    },
    "plugin_token_file_size": {
        "en": "File size: {{size}} bytes",
        "zh": "文件大小: {{size}} 字节",
        "ja": "ファイルサイズ: {{size}} バイト",
        "ar": "حجم الملف: {{size}} بايت",
        "ru": "Размер файла: {{size}} байт"
    },
    "plugin_token_avg_bytes_per_token": {
        "en": "Avg bytes per token: {{avg}}",
        "zh": "平均每个token字节数: {{avg}}",
        "ja": "トークンあたりの平均バイト数: {{avg}}",
        "ar": "متوسط البايتات لكل رمز: {{avg}}",
        "ru": "Среднее байт на токен: {{avg}}"
    },

    # 目录扫描消息
    "plugin_token_scanning_directory": {
        "en": "Scanning directory: {{dir_path}}",
        "zh": "扫描目录: {{dir_path}}",
        "ja": "ディレクトリをスキャン中: {{dir_path}}",
        "ar": "فحص الدليل: {{dir_path}}",
        "ru": "Сканирование директории: {{dir_path}}"
    },
    "plugin_token_scan_complete": {
        "en": "Directory scan complete!",
        "zh": "目录扫描完成!",
        "ja": "ディレクトリスキャンが完了しました!",
        "ar": "اكتمل فحص الدليل!",
        "ru": "Сканирование директории завершено!"
    },
    "plugin_token_files_processed": {
        "en": "Total files processed: {{file_count}}",
        "zh": "处理的文件总数: {{file_count}}",
        "ja": "処理されたファイル総数: {{file_count}}",
        "ar": "إجمالي الملفات المعالجة: {{file_count}}",
        "ru": "Всего обработано файлов: {{file_count}}"
    },
    "plugin_token_avg_tokens_per_file": {
        "en": "Average tokens per file: {{avg_tokens}}",
        "zh": "平均每个文件token数: {{avg_tokens}}",
        "ja": "ファイルあたりの平均トークン数: {{avg_tokens}}",
        "ar": "متوسط الرموز لكل ملف: {{avg_tokens}}",
        "ru": "Среднее токенов на файл: {{avg_tokens}}"
    },

    # 表头和格式化
    "plugin_token_top_files_header": {
        "en": "Top {{n}} files by token count:",
        "zh": "Token数量最多的前{{n}}个文件:",
        "ja": "トークン数上位{{n}}件のファイル:",
        "ar": "أعلى {{n}} ملفات حسب عدد الرموز:",
        "ru": "Топ {{n}} файлов по количеству токенов:"
    },
    "plugin_token_table_header_tokens": {
        "en": "Tokens",
        "zh": "Token数",
        "ja": "トークン数",
        "ar": "الرموز",
        "ru": "Токены"
    },
    "plugin_token_table_header_size_bytes": {
        "en": "Size (bytes)",
        "zh": "大小(字节)",
        "ja": "サイズ(バイト)",
        "ar": "الحجم (بايت)",
        "ru": "Размер (байты)"
    },
    "plugin_token_table_header_file": {
        "en": "File",
        "zh": "文件",
        "ja": "ファイル",
        "ar": "الملف",
        "ru": "Файл"
    },
    "plugin_token_table_header_size": {
        "en": "Size",
        "zh": "大小",
        "ja": "サイズ",
        "ar": "الحجم",
        "ru": "Размер"
    },
    "plugin_token_top_files_by_count": {
        "en": "Top files by token count:",
        "zh": "按token数量排序的顶部文件:",
        "ja": "トークン数順のトップファイル:",
        "ar": "أهم الملفات حسب عدد الرموز:",
        "ru": "Топ файлов по количеству токенов:"
    },

    # Summary 相关消息
    "plugin_token_summary_header": {
        "en": "Token count summary by file type:",
        "zh": "按文件类型分组的token统计摘要:",
        "ja": "ファイルタイプ別トークン数サマリー:",
        "ar": "ملخص عدد الرموز حسب نوع الملف:",
        "ru": "Сводка по токенам по типам файлов:"
    },
    "plugin_token_table_header_extension": {
        "en": "Extension",
        "zh": "扩展名",
        "ja": "拡張子",
        "ar": "الامتداد",
        "ru": "Расширение"
    },
    "plugin_token_table_header_files": {
        "en": "Files",
        "zh": "文件数",
        "ja": "ファイル数",
        "ar": "الملفات",
        "ru": "Файлы"
    },
    "plugin_token_table_header_percent": {
        "en": "% of Total",
        "zh": "占总数%",
        "ja": "全体の%",
        "ar": "% من الإجمالي",
        "ru": "% от общего"
    },
    "plugin_token_table_header_size_kb": {
        "en": "Size (KB)",
        "zh": "大小(KB)",
        "ja": "サイズ(KB)",
        "ar": "الحجم (كيلوبايت)",
        "ru": "Размер (КБ)"
    },
    "plugin_token_total_files_summary": {
        "en": "Total Files: {{total_files}}",
        "zh": "总文件数: {{total_files}}",
        "ja": "総ファイル数: {{total_files}}",
        "ar": "إجمالي الملفات: {{total_files}}",
        "ru": "Всего файлов: {{total_files}}"
    },
    "plugin_token_total_tokens_summary": {
        "en": "Total Tokens: {{total_tokens}}",
        "zh": "总Token数: {{total_tokens}}",
        "ja": "総トークン数: {{total_tokens}}",
        "ar": "إجمالي الرموز: {{total_tokens}}",
        "ru": "Всего токенов: {{total_tokens}}"
    },
    "plugin_token_total_size": {
        "en": "Total Size: {{total_size}} MB",
        "zh": "总大小: {{total_size}} MB",
        "ja": "総サイズ: {{total_size}} MB",
        "ar": "الحجم الإجمالي: {{total_size}} ميجابايت",
        "ru": "Общий размер: {{total_size}} МБ"
    },
    "plugin_token_project_directory": {
        "en": "Project Directory: {{project_dir}}",
        "zh": "项目目录: {{project_dir}}",
        "ja": "プロジェクトディレクトリ: {{project_dir}}",
        "ar": "دليل المشروع: {{project_dir}}",
        "ru": "Директория проекта: {{project_dir}}"
    }
} 