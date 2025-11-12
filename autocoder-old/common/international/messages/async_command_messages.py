"""
Async command messages for internationalization
Contains all messages used by the async command functionality
"""

ASYNC_COMMAND_MESSAGES = {
    # 错误消息
    "async_task_param_error": {
        "en": "Parameter Error",
        "zh": "参数错误",
        "ja": "パラメータエラー",
        "ar": "خطأ في المعامل",
        "ru": "Ошибка параметра"
    },
    "async_provide_task_id": {
        "en": "Please provide the task ID to terminate",
        "zh": "请提供要终止的任务ID",
        "ja": "終了するタスクIDを提供してください",
        "ar": "يرجى تقديم معرف المهمة للإنهاء",
        "ru": "Пожалуйста, укажите ID задачи для завершения"
    },
    "async_task_not_found": {
        "en": "Task ID not found: {{task_id}}",
        "zh": "未找到任务ID: {{task_id}}",
        "ja": "タスクIDが見つかりません: {{task_id}}",
        "ar": "لم يتم العثور على معرف المهمة: {{task_id}}",
        "ru": "ID задачи не найден: {{task_id}}"
    },
    "async_task_not_exist": {
        "en": "Task Not Exist",
        "zh": "任务不存在",
        "ja": "タスクが存在しません",
        "ar": "المهمة غير موجودة",
        "ru": "Задача не существует"
    },
    "async_task_status_error": {
        "en": "Task Status Error",
        "zh": "任务状态错误",
        "ja": "タスクステータスエラー",
        "ar": "خطأ في حالة المهمة",
        "ru": "Ошибка статуса задачи"
    },
    "async_task_cannot_terminate": {
        "en": "Task {{task_id}} is currently in {{status}} status and cannot be terminated",
        "zh": "任务 {{task_id}} 当前状态为 {{status}}，无法终止",
        "ja": "タスク {{task_id}} は現在 {{status}} ステータスで、終了できません",
        "ar": "المهمة {{task_id}} في حالة {{status}} حالياً ولا يمكن إنهاؤها",
        "ru": "Задача {{task_id}} в настоящее время имеет статус {{status}} и не может быть завершена"
    },
    "async_missing_psutil": {
        "en": "Missing psutil dependency, cannot terminate process",
        "zh": "缺少 psutil 依赖，无法终止进程",
        "ja": "psutil の依存関係が見つからないため、プロセスを終了できません",
        "ar": "مكتبة psutil مفقودة، لا يمكن إنهاء العملية",
        "ru": "Отсутствует зависимость psutil, невозможно завершить процесс"
    },
    "async_dependency_missing": {
        "en": "Dependency Missing",
        "zh": "依赖缺失",
        "ja": "依存関係の不足",
        "ar": "التبعية مفقودة",
        "ru": "Отсутствует зависимость"
    },
    "async_process_not_exist": {
        "en": "Process {{pid}} does not exist, may have already finished",
        "zh": "进程 {{pid}} 不存在，可能已经结束",
        "ja": "プロセス {{pid}} は存在しません。既に終了している可能性があります",
        "ar": "العملية {{pid}} غير موجودة، ربما انتهت بالفعل",
        "ru": "Процесс {{pid}} не существует, возможно, уже завершён"
    },
    "async_process_not_exist_title": {
        "en": "Process Not Exist",
        "zh": "进程不存在",
        "ja": "プロセスが存在しません",
        "ar": "العملية غير موجودة",
        "ru": "Процесс не существует"
    },
    "async_terminate_process_error": {
        "en": "Error occurred while terminating process: {{error}}",
        "zh": "终止进程时发生错误: {{error}}",
        "ja": "プロセスの終了中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء إنهاء العملية: {{error}}",
        "ru": "Ошибка при завершении процесса: {{error}}"
    },
    "async_terminate_failed": {
        "en": "Terminate Failed",
        "zh": "终止失败",
        "ja": "終了失敗",
        "ar": "فشل الإنهاء",
        "ru": "Завершение не выполнено"
    },
    "async_no_valid_pid": {
        "en": "Task {{task_id}} has no valid PID information",
        "zh": "任务 {{task_id}} 没有有效的PID信息",
        "ja": "タスク {{task_id}} には有効なPID情報がありません",
        "ar": "المهمة {{task_id}} لا تحتوي على معلومات PID صالحة",
        "ru": "Задача {{task_id}} не содержит действительной информации о PID"
    },
    "async_pid_missing": {
        "en": "PID Information Missing",
        "zh": "PID信息缺失",
        "ja": "PID情報の不足",
        "ar": "معلومات PID مفقودة",
        "ru": "Отсутствует информация о PID"
    },
    "async_kill_command_error": {
        "en": "Error occurred while processing kill command: {{error}}",
        "zh": "处理kill命令时发生错误: {{error}}",
        "ja": "killコマンドの処理中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء معالجة أمر القتل: {{error}}",
        "ru": "Ошибка при обработке команды завершения: {{error}}"
    },
    "async_processing_error": {
        "en": "Processing Error",
        "zh": "处理错误",
        "ja": "処理エラー",
        "ar": "خطأ في المعالجة",
        "ru": "Ошибка обработки"
    },
    "async_task_detail_load_error": {
        "en": "Error occurred while loading task details: {{error}}",
        "zh": "加载任务详情时发生错误: {{error}}",
        "ja": "タスクの詳細の読み込み中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء تحميل تفاصيل المهمة: {{error}}",
        "ru": "Ошибка при загрузке деталей задачи: {{error}}"
    },
    "async_task_list_error": {
        "en": "Error occurred while getting task list: {{error}}",
        "zh": "获取任务列表时发生错误: {{error}}",
        "ja": "タスクリストの取得中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء الحصول على قائمة المهام: {{error}}",
        "ru": "Ошибка при получении списка задач: {{error}}"
    },
    
    # 成功消息
    "async_task_terminated_success": {
        "en": "Task {{task_id}} (PID: {{pid}}) has been successfully terminated",
        "zh": "任务 {{task_id}} (PID: {{pid}}) 已成功终止",
        "ja": "タスク {{task_id}} (PID: {{pid}}) が正常に終了されました",
        "ar": "تم إنهاء المهمة {{task_id}} (PID: {{pid}}) بنجاح",
        "ru": "Задача {{task_id}} (PID: {{pid}}) успешно завершена"
    },
    "async_terminate_success": {
        "en": "Task Terminate Success",
        "zh": "任务终止成功",
        "ja": "タスク終了成功",
        "ar": "نجح إنهاء المهمة",
        "ru": "Задача успешно завершена"
    },
    "async_task_status_updated": {
        "en": "Task status updated",
        "zh": "任务状态已更新",
        "ja": "タスクステータスが更新されました",
        "ar": "تم تحديث حالة المهمة",
        "ru": "Статус задачи обновлён"
    },
    
    # 任务状态
    "async_task_status_running": {
        "en": "[blue]Running[/blue]",
        "zh": "[blue]运行中[/blue]",
        "ja": "[blue]実行中[/blue]",
        "ar": "[blue]قيد التشغيل[/blue]",
        "ru": "[blue]Выполняется[/blue]"
    },
    "async_task_status_completed": {
        "en": "[green]Completed[/green]",
        "zh": "[green]已完成[/green]",
        "ja": "[green]完了[/green]",
        "ar": "[green]مكتمل[/green]",
        "ru": "[green]Завершено[/green]"
    },
    "async_task_status_failed": {
        "en": "[red]Failed[/red]",
        "zh": "[red]失败[/red]",
        "ja": "[red]失敗[/red]",
        "ar": "[red]فاشل[/red]",
        "ru": "[red]Неудачно[/red]"
    },
    
    # 任务列表
    "async_task_list_title": {
        "en": "Async Task List",
        "zh": "异步任务列表",
        "ja": "非同期タスクリスト",
        "ar": "قائمة المهام غير المتزامنة",
        "ru": "Список асинхронных задач"
    },
    "async_task_list_no_tasks": {
        "en": "No tasks found",
        "zh": "没有找到任务",
        "ja": "タスクが見つかりません",
        "ar": "لم يتم العثور على مهام",
        "ru": "Задачи не найдены"
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
        "en": "Query",
        "zh": "查询",
        "ja": "クエリ",
        "ar": "الاستعلام",
        "ru": "Запрос"
    },
    "async_task_table_log": {
        "en": "Log File",
        "zh": "日志文件",
        "ja": "ログファイル",
        "ar": "ملف السجل",
        "ru": "Файл журнала"
    },
    "async_task_list_summary": {
        "en": "Total: {{total}} | Completed: {{completed}} | Running: {{running}} | Failed: {{failed}}",
        "zh": "总计: {{total}} | 已完成: {{completed}} | 运行中: {{running}} | 失败: {{failed}}",
        "ja": "合計: {{total}} | 完了: {{completed}} | 実行中: {{running}} | 失敗: {{failed}}",
        "ar": "المجموع: {{total}} | مكتمل: {{completed}} | قيد التشغيل: {{running}} | فاشل: {{failed}}",
        "ru": "Всего: {{total}} | Завершено: {{completed}} | Выполняется: {{running}} | Неудачно: {{failed}}"
    },
    
    # 任务详情
    "async_task_detail_title": {
        "en": "Task Details",
        "zh": "任务详情",
        "ja": "タスクの詳細",
        "ar": "تفاصيل المهمة",
        "ru": "Детали задачи"
    },
    "async_task_detail_not_found": {
        "en": "Task ID {{task_id}} not found",
        "zh": "未找到任务ID {{task_id}}",
        "ja": "タスクID {{task_id}} が見つかりません",
        "ar": "لم يتم العثور على معرف المهمة {{task_id}}",
        "ru": "ID задачи {{task_id}} не найден"
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
        "ru": "Режим разделения"
    },
    "async_task_field_bg_mode": {
        "en": "Background Mode",
        "zh": "后台模式",
        "ja": "バックグラウンドモード",
        "ar": "وضع الخلفية",
        "ru": "Фоновый режим"
    },
    "async_task_field_pr_mode": {
        "en": "Pull Request Mode",
        "zh": "拉取请求模式",
        "ja": "プルリクエストモード",
        "ar": "وضع طلب السحب",
        "ru": "Режим запроса на слияние"
    },
    "async_task_field_created": {
        "en": "Created At",
        "zh": "创建时间",
        "ja": "作成時刻",
        "ar": "وقت الإنشاء",
        "ru": "Создано в"
    },
    "async_task_field_completed": {
        "en": "Completed At",
        "zh": "完成时间",
        "ja": "完了時刻",
        "ar": "وقت الإكمال",
        "ru": "Завершено в"
    },
    "async_task_field_duration": {
        "en": "Duration",
        "zh": "耗时",
        "ja": "所要時間",
        "ar": "المدة",
        "ru": "Длительность"
    },
    "async_task_duration_format": {
        "en": "{{duration}} seconds",
        "zh": "{{duration}} 秒",
        "ja": "{{duration}} 秒",
        "ar": "{{duration}} ثانية",
        "ru": "{{duration}} секунд"
    },
    "async_task_field_worktree_path": {
        "en": "Worktree Path",
        "zh": "工作树路径",
        "ja": "ワークツリーパス",
        "ar": "مسار شجرة العمل",
        "ru": "Путь рабочего дерева"
    },
    "async_task_field_original_path": {
        "en": "Original Path",
        "zh": "原始路径",
        "ja": "元のパス",
        "ar": "المسار الأصلي",
        "ru": "Исходный путь"
    },
    "async_task_field_log_file": {
        "en": "Log File",
        "zh": "日志文件",
        "ja": "ログファイル",
        "ar": "ملف السجل",
        "ru": "Файл журнала"
    },
    "async_task_field_success": {
        "en": "Success",
        "zh": "成功",
        "ja": "成功",
        "ar": "نجح",
        "ru": "Успех"
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
    
    # 面板标题
    "async_task_panel_query": {
        "en": "User Query",
        "zh": "用户查询",
        "ja": "ユーザークエリ",
        "ar": "استعلام المستخدم",
        "ru": "Пользовательский запрос"
    },
    "async_task_panel_paths": {
        "en": "Path Information",
        "zh": "路径信息",
        "ja": "パス情報",
        "ar": "معلومات المسار",
        "ru": "Информация о путях"
    },
    "async_task_panel_error": {
        "en": "Error Information",
        "zh": "错误信息",
        "ja": "エラー情報",
        "ar": "معلومات الخطأ",
        "ru": "Информация об ошибке"
    },
    "async_task_panel_execution": {
        "en": "Execution Result",
        "zh": "执行结果",
        "ja": "実行結果",
        "ar": "نتيجة التنفيذ",
        "ru": "Результат выполнения"
    },
    "async_task_operation_hints": {
        "en": "Available Operations",
        "zh": "可用操作",
        "ja": "利用可能な操作",
        "ar": "العمليات المتاحة",
        "ru": "Доступные операции"
    },
    
    # 操作提示
    "async_task_hint_view_log": {
        "en": "📄 View log: cat {{log_file}}",
        "zh": "📄 查看日志: cat {{log_file}}",
        "ja": "📄 ログ表示: cat {{log_file}}",
        "ar": "📄 عرض السجل: cat {{log_file}}",
        "ru": "📄 Просмотр журнала: cat {{log_file}}"
    },
    "async_task_hint_enter_worktree": {
        "en": "📁 Enter worktree: cd {{worktree_path}}",
        "zh": "📁 进入工作树: cd {{worktree_path}}",
        "ja": "📁 ワークツリーに入る: cd {{worktree_path}}",
        "ar": "📁 دخول شجرة العمل: cd {{worktree_path}}",
        "ru": "📁 Войти в рабочее дерево: cd {{worktree_path}}"
    },
    "async_task_hint_back_to_list": {
        "en": "📋 Back to list: /async /list",
        "zh": "📋 返回列表: /async /list",
        "ja": "📋 リストに戻る: /async /list",
        "ar": "📋 العودة إلى القائمة: /async /list",
        "ru": "📋 Вернуться к списку: /async /list"
    },
    
    # 异步任务启动消息
    "async_task_started_message": {
        "en": "[green]Async task has been started![/green]\n\nModel: [yellow]{{model}}[/yellow]\nQuery: [blue]{{query}}[/blue]\n\n[bold]Task details can be viewed at:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]Tip: The task is running in the background, you can continue using other features[/dim]",
        "zh": "[green]异步任务已启动！[/green]\n\n模型: [yellow]{{model}}[/yellow]\n查询: [blue]{{query}}[/blue]\n\n[bold]任务详情请查看:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]提示: 任务正在后台执行，您可以继续使用其他功能[/dim]",
        "ja": "[green]非同期タスクが開始されました！[/green]\n\nモデル: [yellow]{{model}}[/yellow]\nクエリ: [blue]{{query}}[/blue]\n\n[bold]タスクの詳細は以下で確認できます:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]ヒント: タスクはバックグラウンドで実行中です。他の機能を引き続き使用できます[/dim]",
        "ar": "[green]تم بدء المهمة غير المتزامنة![/green]\n\nالنموذج: [yellow]{{model}}[/yellow]\nالاستعلام: [blue]{{query}}[/blue]\n\n[bold]يمكن عرض تفاصيل المهمة في:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]نصيحة: المهمة تعمل في الخلفية، يمكنك الاستمرار في استخدام الميزات الأخرى[/dim]",
        "ru": "[green]Асинхронная задача запущена![/green]\n\nМодель: [yellow]{{model}}[/yellow]\nЗапрос: [blue]{{query}}[/blue]\n\n[bold]Детали задачи можно просмотреть в:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]Совет: Задача выполняется в фоновом режиме, вы можете продолжать использовать другие функции[/dim]"
    },

    # 异步任务启动消息（带名称）
    "async_task_started_message_with_name": {
        "en": "[green]Async task has been started![/green]\n\nModel: [yellow]{{model}}[/yellow]\nQuery: [blue]{{query}}[/blue]\n\n[bold]Worktree Path:[/bold]\n[cyan]~/.auto-coder/async_agent/tasks/{{name}}[/cyan]\n\n[bold]Meta Information:[/bold]\n[cyan]~/.auto-coder/async_agent/meta/{{name}}.json[/cyan]\n\n[bold]Task details can be viewed at:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]Tip: The task is running in the background, you can continue using other features[/dim]",
        "zh": "[green]异步任务已启动！[/green]\n\n模型: [yellow]{{model}}[/yellow]\n查询: [blue]{{query}}[/blue]\n\n[bold]工作目录路径:[/bold]\n[cyan]~/.auto-coder/async_agent/tasks/{{name}}[/cyan]\n\n[bold]元信息文件:[/bold]\n[cyan]~/.auto-coder/async_agent/meta/{{name}}.json[/cyan]\n\n[bold]任务详情请查看:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]提示: 任务正在后台执行，您可以继续使用其他功能[/dim]",
        "ja": "[green]非同期タスクが開始されました！[/green]\n\nモデル: [yellow]{{model}}[/yellow]\nクエリ: [blue]{{query}}[/blue]\n\n[bold]ワークツリーパス:[/bold]\n[cyan]~/.auto-coder/async_agent/tasks/{{name}}[/cyan]\n\n[bold]メタ情報:[/bold]\n[cyan]~/.auto-coder/async_agent/meta/{{name}}.json[/cyan]\n\n[bold]タスクの詳細は以下で確認できます:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]ヒント: タスクはバックグラウンドで実行中です。他の機能を引き続き使用できます[/dim]",
        "ar": "[green]تم بدء المهمة غير المتزامنة![/green]\n\nالنموذج: [yellow]{{model}}[/yellow]\nالاستعلام: [blue]{{query}}[/blue]\n\n[bold]مسار شجرة العمل:[/bold]\n[cyan]~/.auto-coder/async_agent/tasks/{{name}}[/cyan]\n\n[bold]معلومات التعريف:[/bold]\n[cyan]~/.auto-coder/async_agent/meta/{{name}}.json[/cyan]\n\n[bold]يمكن عرض تفاصيل المهمة في:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]نصيحة: المهمة تعمل في الخلفية، يمكنك الاستمرار في استخدام الميزات الأخرى[/dim]",
        "ru": "[green]Асинхронная задача запущена![/green]\n\nМодель: [yellow]{{model}}[/yellow]\nЗапрос: [blue]{{query}}[/blue]\n\n[bold]Путь рабочего дерева:[/bold]\n[cyan]~/.auto-coder/async_agent/tasks/{{name}}[/cyan]\n\n[bold]Мета информация:[/bold]\n[cyan]~/.auto-coder/async_agent/meta/{{name}}.json[/cyan]\n\n[bold]Детали задачи можно просмотреть в:[/bold]\n[cyan]{{agent_dir}}[/cyan]\n\n[dim]Совет: Задача выполняется в фоновом режиме, вы можете продолжать использовать другие функции[/dim]"
    },
    "async_task_title": {
        "en": "🚀 Async Task",
        "zh": "🚀 异步任务",
        "ja": "🚀 非同期タスク",
        "ar": "🚀 مهمة غير متزامنة",
        "ru": "🚀 Асинхронная задача"
    }
}
