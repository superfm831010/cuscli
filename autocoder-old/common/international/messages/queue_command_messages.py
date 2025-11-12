"""
Queue command messages for internationalization
Contains all messages used by the queue command functionality
"""

QUEUE_COMMAND_MESSAGES = {
    # 错误消息
    "queue_invalid_status_filter": {
        "en": "Invalid status filter: {{status}}. Valid values: pending, running, completed, failed, cancelled",
        "zh": "无效的状态过滤器: {{status}}。有效值: pending, running, completed, failed, cancelled",
        "ja": "無効なステータスフィルタ: {{status}}。有効な値: pending, running, completed, failed, cancelled",
        "ar": "مرشح الحالة غير صالح: {{status}}. القيم الصالحة: pending, running, completed, failed, cancelled",
        "ru": "Неверный фильтр статуса: {{status}}. Допустимые значения: pending, running, completed, failed, cancelled"
    },
    "queue_param_error": {
        "en": "Parameter Error",
        "zh": "参数错误",
        "ja": "パラメータエラー",
        "ar": "خطأ في المعامل",
        "ru": "Ошибка параметра"
    },
    "queue_provide_task_id": {
        "en": "Please provide the task ID to remove",
        "zh": "请提供要移除的任务ID",
        "ja": "削除するタスクIDを提供してください",
        "ar": "يرجى تقديم معرف المهمة للإزالة",
        "ru": "Пожалуйста, укажите ID задачи для удаления"
    },
    "queue_task_not_found": {
        "en": "Task ID not found: {{task_id}}",
        "zh": "未找到任务ID: {{task_id}}",
        "ja": "タスクIDが見つかりません: {{task_id}}",
        "ar": "لم يتم العثور على معرف المهمة: {{task_id}}",
        "ru": "ID задачи не найден: {{task_id}}"
    },
    "queue_task_not_exist": {
        "en": "Task Not Exist",
        "zh": "任务不存在",
        "ja": "タスクが存在しません",
        "ar": "المهمة غير موجودة",
        "ru": "Задача не существует"
    },
    "queue_task_running_cannot_remove": {
        "en": "Task {{task_id}} is running and cannot be removed. Please stop the task first.",
        "zh": "任务 {{task_id}} 正在运行中，无法移除。请先停止任务。",
        "ja": "タスク {{task_id}} は実行中のため削除できません。まずタスクを停止してください。",
        "ar": "المهمة {{task_id}} قيد التشغيل ولا يمكن إزالتها. يرجى إيقاف المهمة أولاً.",
        "ru": "Задача {{task_id}} выполняется и не может быть удалена. Пожалуйста, сначала остановите задачу."
    },
    "queue_task_status_error": {
        "en": "Task Status Error",
        "zh": "任务状态错误",
        "ja": "タスクステータスエラー",
        "ar": "خطأ في حالة المهمة",
        "ru": "Ошибка статуса задачи"
    },
    "queue_error": {
        "en": "Error",
        "zh": "错误",
        "ja": "エラー",
        "ar": "خطأ",
        "ru": "Ошибка"
    },
    "queue_get_tasks_error": {
        "en": "Error occurred while getting task list: {{error}}",
        "zh": "获取任务列表时发生错误: {{error}}",
        "ja": "タスクリストの取得中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء الحصول على قائمة المهام: {{error}}",
        "ru": "Ошибка при получении списка задач: {{error}}"
    },
    "queue_remove_task_error": {
        "en": "Error occurred while removing task: {{error}}",
        "zh": "移除任务时发生错误: {{error}}",
        "ja": "タスクの削除中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء إزالة المهمة: {{error}}",
        "ru": "Ошибка при удалении задачи: {{error}}"
    },
    "queue_add_task_error": {
        "en": "Error occurred while adding task: {{error}}",
        "zh": "添加任务时发生错误: {{error}}",
        "ja": "タスクの追加中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء إضافة المهمة: {{error}}",
        "ru": "Ошибка при добавлении задачи: {{error}}"
    },
    "queue_clear_tasks_error": {
        "en": "Error occurred while clearing tasks: {{error}}",
        "zh": "清理任务时发生错误: {{error}}",
        "ja": "タスクのクリア中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء مسح المهام: {{error}}",
        "ru": "Ошибка при очистке задач: {{error}}"
    },
    "queue_get_stats_error": {
        "en": "Error occurred while getting statistics: {{error}}",
        "zh": "获取统计信息时发生错误: {{error}}",
        "ja": "統計情報の取得中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء الحصول على الإحصائيات: {{error}}",
        "ru": "Ошибка при получении статистики: {{error}}"
    },
    "queue_start_executor_error": {
        "en": "Error occurred while starting queue executor: {{error}}",
        "zh": "启动队列执行器时发生错误: {{error}}",
        "ja": "キュー実行器の開始中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء بدء تشغيل منفذ القائمة: {{error}}",
        "ru": "Ошибка при запуске исполнителя очереди: {{error}}"
    },
    "queue_stop_executor_error": {
        "en": "Error occurred while stopping queue executor: {{error}}",
        "zh": "停止队列执行器时发生错误: {{error}}",
        "ja": "キュー実行器の停止中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء إيقاف منفذ القائمة: {{error}}",
        "ru": "Ошибка при остановке исполнителя очереди: {{error}}"
    },
    "queue_get_status_error": {
        "en": "Error occurred while getting status information: {{error}}",
        "zh": "获取状态信息时发生错误: {{error}}",
        "ja": "ステータス情報の取得中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء الحصول على معلومات الحالة: {{error}}",
        "ru": "Ошибка при получении информации о статусе: {{error}}"
    },
    
    # 成功消息
    "queue_task_removed_success": {
        "en": "Task {{task_id}} has been successfully removed",
        "zh": "任务 {{task_id}} 已成功移除",
        "ja": "タスク {{task_id}} が正常に削除されました",
        "ar": "تم حذف المهمة {{task_id}} بنجاح",
        "ru": "Задача {{task_id}} успешно удалена"
    },
    "queue_remove_success": {
        "en": "Remove Success",
        "zh": "移除成功",
        "ja": "削除成功",
        "ar": "نجح الحذف",
        "ru": "Удаление выполнено"
    },
    "queue_remove_failed": {
        "en": "Failed to remove task {{task_id}}",
        "zh": "移除任务 {{task_id}} 失败",
        "ja": "タスク {{task_id}} の削除に失敗しました",
        "ar": "فشل في حذف المهمة {{task_id}}",
        "ru": "Не удалось удалить задачу {{task_id}}"
    },
    "queue_remove_failed_title": {
        "en": "Remove Failed",
        "zh": "移除失败",
        "ja": "削除失敗",
        "ar": "فشل الحذف",
        "ru": "Удаление не выполнено"
    },
    "queue_task_added_success": {
        "en": "Task has been added to queue\nTask ID: {{task_id}}\nQuery: {{query}}\nModel: {{model}}\n\nUse /queue /list to view queue\nUse /queue /start to start executor",
        "zh": "任务已添加到队列\n任务ID: {{task_id}}\n需求: {{query}}\n模型: {{model}}\n\n使用 /queue /list 查看队列\n使用 /queue /start 启动执行器",
        "ja": "タスクがキューに追加されました\nタスクID: {{task_id}}\nクエリ: {{query}}\nモデル: {{model}}\n\n/queue /list でキューを表示\n/queue /start で実行器を開始",
        "ar": "تم إضافة المهمة إلى القائمة\nمعرف المهمة: {{task_id}}\nالاستعلام: {{query}}\nالنموذج: {{model}}\n\nاستخدم /queue /list لعرض القائمة\nاستخدم /queue /start لبدء المنفذ",
        "ru": "Задача добавлена в очередь\nID задачи: {{task_id}}\nЗапрос: {{query}}\nМодель: {{model}}\n\nИспользуйте /queue /list для просмотра очереди\nИспользуйте /queue /start для запуска исполнителя"
    },
    "queue_add_success": {
        "en": "✅ Add Success",
        "zh": "✅ 添加成功",
        "ja": "✅ 追加成功",
        "ar": "✅ نجحت الإضافة",
        "ru": "✅ Добавление выполнено"
    },
    "queue_executor_auto_started": {
        "en": "Queue executor has been automatically started",
        "zh": "队列执行器已自动启动",
        "ja": "キュー実行器が自動的に開始されました",
        "ar": "تم تشغيل منفذ القائمة تلقائياً",
        "ru": "Исполнитель очереди запущен автоматически"
    },
    "queue_executor_status": {
        "en": "🚀 Executor Status",
        "zh": "🚀 执行器状态",
        "ja": "🚀 実行器ステータス",
        "ar": "🚀 حالة المنفذ",
        "ru": "🚀 Статус исполнителя"
    },
    "queue_cleared_count": {
        "en": "Cleared {{count}} completed tasks",
        "zh": "已清理 {{count}} 个已完成的任务",
        "ja": "{{count}} 個の完了したタスクをクリアしました",
        "ar": "تم مسح {{count}} مهام مكتملة",
        "ru": "Очищено {{count}} завершенных задач"
    },
    "queue_clear_success": {
        "en": "Clear Success",
        "zh": "清理成功",
        "ja": "クリア成功",
        "ar": "نجح المسح",
        "ru": "Очистка выполнена"
    },
    "queue_no_completed_tasks": {
        "en": "No completed tasks to clear",
        "zh": "没有需要清理的已完成任务",
        "ja": "クリアする完了したタスクはありません",
        "ar": "لا توجد مهام مكتملة للمسح",
        "ru": "Нет завершенных задач для очистки"
    },
    "queue_clear_completed": {
        "en": "Clear Completed",
        "zh": "清理完成",
        "ja": "クリア完了",
        "ar": "مسح مكتمل",
        "ru": "Очистка завершена"
    },
    "queue_executor_already_running": {
        "en": "Queue executor is already running",
        "zh": "队列执行器已经在运行中",
        "ja": "キュー実行器は既に実行中です",
        "ar": "منفذ القائمة يعمل بالفعل",
        "ru": "Исполнитель очереди уже запущен"
    },
    "queue_status_info": {
        "en": "Status Information",
        "zh": "状态信息",
        "ja": "ステータス情報",
        "ar": "معلومات الحالة",
        "ru": "Информация о статусе"
    },
    "queue_executor_started": {
        "en": "Queue executor has been started and will automatically execute tasks in the queue",
        "zh": "队列执行器已启动，将自动执行队列中的任务",
        "ja": "キュー実行器が開始され、キュー内のタスクを自動実行します",
        "ar": "تم تشغيل منفذ القائمة وسيقوم بتنفيذ المهام في القائمة تلقائياً",
        "ru": "Исполнитель очереди запущен и будет автоматически выполнять задачи в очереди"
    },
    "queue_start_success": {
        "en": "Start Success",
        "zh": "启动成功",
        "ja": "開始成功",
        "ar": "نجح التشغيل",
        "ru": "Запуск выполнен"
    },
    "queue_executor_not_running": {
        "en": "Queue executor is not running",
        "zh": "队列执行器未在运行",
        "ja": "キュー実行器は実行されていません",
        "ar": "منفذ القائمة لا يعمل",
        "ru": "Исполнитель очереди не запущен"
    },
    "queue_executor_stopped": {
        "en": "Queue executor has been stopped",
        "zh": "队列执行器已停止",
        "ja": "キュー実行器が停止されました",
        "ar": "تم إيقاف منفذ القائمة",
        "ru": "Исполнитель очереди остановлен"
    },
    "queue_stop_success": {
        "en": "Stop Success",
        "zh": "停止成功",
        "ja": "停止成功",
        "ar": "نجح الإيقاف",
        "ru": "Остановка выполнена"
    },
    
    # 列表和状态消息
    "queue_no_tasks_found": {
        "en": "No tasks found{{filter}}",
        "zh": "没有找到任务{{filter}}",
        "ja": "タスクが見つかりません{{filter}}",
        "ar": "لم يتم العثور على مهام{{filter}}",
        "ru": "Задачи не найдены{{filter}}"
    },
    "queue_status_filter": {
        "en": " (status: {{status}})",
        "zh": " (状态: {{status}})",
        "ja": " (ステータス: {{status}})",
        "ar": " (الحالة: {{status}})",
        "ru": " (статус: {{status}})"
    },
    "queue_task_list": {
        "en": "Queue Task List",
        "zh": "队列任务列表",
        "ja": "キュータスクリスト",
        "ar": "قائمة مهام القائمة",
        "ru": "Список задач очереди"
    },
    "queue_task_id": {
        "en": "Task ID",
        "zh": "任务ID",
        "ja": "タスクID",
        "ar": "معرف المهمة",
        "ru": "ID задачи"
    },
    "queue_status": {
        "en": "Status",
        "zh": "状态",
        "ja": "ステータス",
        "ar": "الحالة",
        "ru": "Статус"
    },
    "queue_priority": {
        "en": "Priority",
        "zh": "优先级",
        "ja": "優先度",
        "ar": "الأولوية",
        "ru": "Приоритет"
    },
    "queue_created_time": {
        "en": "Created Time",
        "zh": "创建时间",
        "ja": "作成時刻",
        "ar": "وقت الإنشاء",
        "ru": "Время создания"
    },
    "queue_started_time": {
        "en": "Started Time",
        "zh": "开始时间",
        "ja": "開始時刻",
        "ar": "وقت البدء",
        "ru": "Время запуска"
    },
    "queue_completed_time": {
        "en": "Completed Time",
        "zh": "完成时间",
        "ja": "完了時刻",
        "ar": "وقت الإكمال",
        "ru": "Время завершения"
    },
    "queue_query": {
        "en": "Query",
        "zh": "需求",
        "ja": "クエリ",
        "ar": "الاستعلام",
        "ru": "Запрос"
    },
    "queue_result_error": {
        "en": "Result/Error",
        "zh": "结果/错误",
        "ja": "結果/エラー",
        "ar": "النتيجة/الخطأ",
        "ru": "Результат/Ошибка"
    },
    "queue_statistics": {
        "en": "📊 Statistics",
        "zh": "📊 统计信息",
        "ja": "📊 統計",
        "ar": "📊 الإحصائيات",
        "ru": "📊 Статистика"
    },
    "queue_stats_total": {
        "en": "Total: {{total}} | Pending: {{pending}} | Running: {{running}} | Completed: {{completed}} | Failed: {{failed}} | Cancelled: {{cancelled}}",
        "zh": "总计: {{total}} | 等待: {{pending}} | 运行: {{running}} | 完成: {{completed}} | 失败: {{failed}} | 取消: {{cancelled}}",
        "ja": "合計: {{total}} | 保留中: {{pending}} | 実行中: {{running}} | 完了: {{completed}} | 失敗: {{failed}} | キャンセル: {{cancelled}}",
        "ar": "المجموع: {{total}} | في الانتظار: {{pending}} | قيد التشغيل: {{running}} | مكتمل: {{completed}} | فاشل: {{failed}} | ملغى: {{cancelled}}",
        "ru": "Всего: {{total}} | Ожидает: {{pending}} | Выполняется: {{running}} | Завершено: {{completed}} | Неудачно: {{failed}} | Отменено: {{cancelled}}"
    },
    
    # 状态值
    "queue_status_pending": {
        "en": "[yellow]Pending[/yellow]",
        "zh": "[yellow]等待中[/yellow]",
        "ja": "[yellow]保留中[/yellow]",
        "ar": "[yellow]في الانتظار[/yellow]",
        "ru": "[yellow]Ожидает[/yellow]"
    },
    "queue_status_running": {
        "en": "[blue]Running[/blue]",
        "zh": "[blue]运行中[/blue]",
        "ja": "[blue]実行中[/blue]",
        "ar": "[blue]قيد التشغيل[/blue]",
        "ru": "[blue]Выполняется[/blue]"
    },
    "queue_status_completed": {
        "en": "[green]Completed[/green]",
        "zh": "[green]已完成[/green]",
        "ja": "[green]完了[/green]",
        "ar": "[green]مكتمل[/green]",
        "ru": "[green]Завершено[/green]"
    },
    "queue_status_failed": {
        "en": "[red]Failed[/red]",
        "zh": "[red]失败[/red]",
        "ja": "[red]失敗[/red]",
        "ar": "[red]فاشل[/red]",
        "ru": "[red]Неудачно[/red]"
    },
    "queue_status_cancelled": {
        "en": "[dim]Cancelled[/dim]",
        "zh": "[dim]已取消[/dim]",
        "ja": "[dim]キャンセル[/dim]",
        "ar": "[dim]ملغى[/dim]",
        "ru": "[dim]Отменено[/dim]"
    },
    "queue_error_prefix": {
        "en": "[red]Error: {{error}}[/red]",
        "zh": "[red]错误: {{error}}[/red]",
        "ja": "[red]エラー: {{error}}[/red]",
        "ar": "[red]خطأ: {{error}}[/red]",
        "ru": "[red]Ошибка: {{error}}[/red]"
    },
    
    # 统计信息
    "queue_stats_info": {
        "en": "Queue Statistics",
        "zh": "队列统计信息",
        "ja": "キュー統計",
        "ar": "إحصائيات القائمة",
        "ru": "Статистика очереди"
    },
    "queue_stats_status_column": {
        "en": "Status",
        "zh": "状态",
        "ja": "ステータス",
        "ar": "الحالة",
        "ru": "Статус"
    },
    "queue_stats_count_column": {
        "en": "Count",
        "zh": "数量",
        "ja": "数",
        "ar": "العدد",
        "ru": "Количество"
    },
    "queue_stats_percentage_column": {
        "en": "Percentage",
        "zh": "百分比",
        "ja": "パーセンテージ",
        "ar": "النسبة المئوية",
        "ru": "Процент"
    },
    "queue_stats_pending_display": {
        "en": "Pending",
        "zh": "等待中",
        "ja": "保留中",
        "ar": "في الانتظار",
        "ru": "Ожидает"
    },
    "queue_stats_running_display": {
        "en": "Running",
        "zh": "运行中",
        "ja": "実行中",
        "ar": "قيد التشغيل",
        "ru": "Выполняется"
    },
    "queue_stats_completed_display": {
        "en": "Completed",
        "zh": "已完成",
        "ja": "完了",
        "ar": "مكتمل",
        "ru": "Завершено"
    },
    "queue_stats_failed_display": {
        "en": "Failed",
        "zh": "失败",
        "ja": "失敗",
        "ar": "فاشل",
        "ru": "Неудачно"
    },
    "queue_stats_cancelled_display": {
        "en": "Cancelled",
        "zh": "已取消",
        "ja": "キャンセル",
        "ar": "ملغى",
        "ru": "Отменено"
    },
    "queue_stats_total_bold": {
        "en": "[bold]Total[/bold]",
        "zh": "[bold]总计[/bold]",
        "ja": "[bold]合計[/bold]",
        "ar": "[bold]المجموع[/bold]",
        "ru": "[bold]Всего[/bold]"
    },
    "queue_stats_no_tasks": {
        "en": "No Tasks",
        "zh": "无任务",
        "ja": "タスクなし",
        "ar": "لا توجد مهام",
        "ru": "Нет задач"
    },
    
    # 状态显示
    "queue_executor_status_text": {
        "en": "\n[bold]Queue Executor Status:[/bold] {{status}}\n[bold]Current Running Tasks:[/bold] {{running_count}}\n[bold]Pending Tasks in Queue:[/bold] {{pending_count}}\n\n[bold]Queue Statistics:[/bold]\n• Total Tasks: {{total}}\n• Pending: {{pending}}\n• Running: {{running}}\n• Completed: {{completed}}\n• Failed: {{failed}}\n• Cancelled: {{cancelled}}\n            ",
        "zh": "\n[bold]队列执行器状态:[/bold] {{status}}\n[bold]当前执行任务数:[/bold] {{running_count}}\n[bold]队列中等待任务数:[/bold] {{pending_count}}\n\n[bold]队列统计:[/bold]\n• 总任务数: {{total}}\n• 等待中: {{pending}}\n• 运行中: {{running}}\n• 已完成: {{completed}}\n• 失败: {{failed}}\n• 已取消: {{cancelled}}\n            ",
        "ja": "\n[bold]キュー実行器ステータス:[/bold] {{status}}\n[bold]現在実行中のタスク数:[/bold] {{running_count}}\n[bold]キュー内の待機タスク数:[/bold] {{pending_count}}\n\n[bold]キュー統計:[/bold]\n• 総タスク数: {{total}}\n• 保留中: {{pending}}\n• 実行中: {{running}}\n• 完了: {{completed}}\n• 失敗: {{failed}}\n• キャンセル: {{cancelled}}\n            ",
        "ar": "\n[bold]حالة منفذ القائمة:[/bold] {{status}}\n[bold]عدد المهام قيد التشغيل حالياً:[/bold] {{running_count}}\n[bold]عدد المهام في انتظار القائمة:[/bold] {{pending_count}}\n\n[bold]إحصائيات القائمة:[/bold]\n• إجمالي المهام: {{total}}\n• في الانتظار: {{pending}}\n• قيد التشغيل: {{running}}\n• مكتملة: {{completed}}\n• فاشلة: {{failed}}\n• ملغية: {{cancelled}}\n            ",
        "ru": "\n[bold]Статус исполнителя очереди:[/bold] {{status}}\n[bold]Текущих выполняющихся задач:[/bold] {{running_count}}\n[bold]Ожидающих задач в очереди:[/bold] {{pending_count}}\n\n[bold]Статистика очереди:[/bold]\n• Всего задач: {{total}}\n• Ожидает: {{pending}}\n• Выполняется: {{running}}\n• Завершено: {{completed}}\n• Неудачно: {{failed}}\n• Отменено: {{cancelled}}\n            "
    },
    "queue_status_running_icon": {
        "en": "🟢 Running",
        "zh": "🟢 运行中",
        "ja": "🟢 実行中",
        "ar": "🟢 قيد التشغيل",
        "ru": "🟢 Запущен"
    },
    "queue_status_stopped_icon": {
        "en": "🔴 Stopped",
        "zh": "🔴 已停止",
        "ja": "🔴 停止",
        "ar": "🔴 متوقف",
        "ru": "🔴 Остановлен"
    },
    "queue_status_title": {
        "en": "📊 Queue Status",
        "zh": "📊 队列状态",
        "ja": "📊 キューステータス",
        "ar": "📊 حالة القائمة",
        "ru": "📊 Статус очереди"
    },
    
    # /name 命令相关消息
    "queue_name_command_usage": {
        "en": "Usage: /queue /name <worktree_name> <user_query>\n\nExample: /queue /name auth_module Add user authentication",
        "zh": "用法: /queue /name <worktree名称> <用户需求>\n\n示例: /queue /name auth_module 添加用户身份验证",
        "ja": "使用方法: /queue /name <worktree名> <ユーザークエリ>\n\n例: /queue /name auth_module ユーザー認証を追加",
        "ar": "الاستخدام: /queue /name <اسم_شجرة_العمل> <استعلام_المستخدم>\n\nمثال: /queue /name auth_module إضافة مصادقة المستخدم",
        "ru": "Использование: /queue /name <имя_worktree> <запрос_пользователя>\n\nПример: /queue /name auth_module Добавить аутентификацию пользователя"
    },
    "queue_invalid_worktree_name": {
        "en": "Invalid worktree name '{{name}}'. Worktree names can only contain letters, numbers, underscores and hyphens.",
        "zh": "无效的 worktree 名称 '{{name}}'。Worktree 名称只能包含字母、数字、下划线和连字符。",
        "ja": "無効なworktree名 '{{name}}'。worktree名には文字、数字、アンダースコア、ハイフンのみ使用できます。",
        "ar": "اسم شجرة عمل غير صالح '{{name}}'. يمكن أن تحتوي أسماء أشجار العمل على أحرف وأرقام وشرطة سفلية وشرطة فقط.",
        "ru": "Недействительное имя worktree '{{name}}'. Имена worktree могут содержать только буквы, цифры, подчёркивания и дефисы."
    },
    "queue_custom_worktree_info": {
        "en": "Worktree: {{worktree_name}}",
        "zh": "Worktree: {{worktree_name}}",
        "ja": "Worktree: {{worktree_name}}",
        "ar": "شجرة العمل: {{worktree_name}}",
        "ru": "Worktree: {{worktree_name}}"
    },
    
    # 帮助信息
    "queue_help_title": {
        "en": "📋 Queue Management Help",
        "zh": "📋 队列管理帮助",
        "ja": "📋 キュー管理ヘルプ",
        "ar": "📋 مساعدة إدارة القائمة",
        "ru": "📋 Справка по управлению очередью"
    },
    "queue_help_basic_usage": {
        "en": "[bold]Basic Usage:[/bold]",
        "zh": "[bold]基本用法:[/bold]",
        "ja": "[bold]基本的な使い方:[/bold]",
        "ar": "[bold]الاستخدام الأساسي:[/bold]",
        "ru": "[bold]Основное использование:[/bold]"
    },
    "queue_help_status_filters": {
        "en": "[bold]Status Filter Options:[/bold]",
        "zh": "[bold]状态过滤选项:[/bold]",
        "ja": "[bold]ステータスフィルタオプション:[/bold]",
        "ar": "[bold]خيارات مرشح الحالة:[/bold]",
        "ru": "[bold]Опции фильтра статуса:[/bold]"
    },
    "queue_help_examples": {
        "en": "[bold]Examples:[/bold]",
        "zh": "[bold]示例:[/bold]",
        "ja": "[bold]例:[/bold]",
        "ar": "[bold]أمثلة:[/bold]",
        "ru": "[bold]Примеры:[/bold]"
    },
    "queue_help_notes": {
        "en": "[bold yellow]Notes:[/bold yellow]",
        "zh": "[bold yellow]注意:[/bold yellow]",
        "ja": "[bold yellow]注意:[/bold yellow]",
        "ar": "[bold yellow]ملاحظات:[/bold yellow]",
        "ru": "[bold yellow]Примечания:[/bold yellow]"
    },
    "queue_help_content_with_name": {
        "en": """[bold cyan]Queue Management Command Help[/bold cyan]

[bold]Basic Usage:[/bold]
  /queue <user_query>              - Add query to queue
  /queue /name <name> <query>      - Add query with custom worktree name
  /queue /list [status]            - List tasks in queue, with optional status filter
  /queue /remove <task_id>         - Remove specified task
  /queue /clear                    - Clear completed tasks
  /queue /stats                    - Show queue statistics
  /queue /start                    - Start queue executor
  /queue /stop                     - Stop queue executor
  /queue /status                   - Show executor and queue status

[bold]Status Filter Options:[/bold]
  pending    - Tasks waiting for execution
  running    - Tasks currently executing
  completed  - Tasks that have completed
  failed     - Tasks that failed execution
  cancelled  - Tasks that were cancelled

[bold]Examples:[/bold]
  /queue Implement user login feature           - Add query to queue
  /queue /name auth_module Add authentication  - Add query with custom worktree name
  /queue /list                                 - List all tasks
  /queue /list pending                         - List only pending tasks
  /queue /remove abc123                        - Remove task with ID abc123
  /queue /clear                                - Clear all completed tasks
  /queue /stats                                - View queue statistics
  /queue /start                                - Start queue executor to process tasks
  /queue /stop                                 - Stop queue executor
  /queue /status                               - View executor running status

[bold yellow]Notes:[/bold yellow]
- Task IDs are 8-character unique identifiers
- Running tasks cannot be removed
- Clear operation only removes completed, failed or cancelled tasks
- Queue executor needs to be manually started to begin executing tasks
- After stopping the executor, running tasks will continue to completion
- Custom worktree names allow multiple parallel task environments
- Worktree names must contain only letters, numbers, underscores and hyphens""",
        "zh": """[bold cyan]队列管理命令帮助[/bold cyan]

[bold]基本用法:[/bold]
  /queue <用户需求>              - 添加需求到队列
  /queue /name <名称> <需求>      - 使用自定义 worktree 名称添加需求
  /queue /list [status]            - 列出队列中的任务，可选择状态过滤
  /queue /remove <task_id>         - 移除指定任务
  /queue /clear                    - 清理已完成的任务
  /queue /stats                    - 显示队列统计信息
  /queue /start                    - 启动队列执行器
  /queue /stop                     - 停止队列执行器
  /queue /status                   - 显示执行器和队列状态

[bold]状态过滤选项:[/bold]
  pending    - 等待执行的任务
  running    - 正在执行的任务
  completed  - 已完成的任务
  failed     - 执行失败的任务
  cancelled  - 已取消的任务

[bold]示例:[/bold]
  /queue 实现用户登录功能           - 添加需求到队列
  /queue /name auth_module 添加身份验证  - 使用自定义 worktree 名称添加需求
  /queue /list                    - 列出所有任务
  /queue /list pending            - 只列出等待中的任务
  /queue /remove abc123           - 移除任务ID为abc123的任务
  /queue /clear                   - 清理所有已完成的任务
  /queue /stats                   - 查看队列统计信息
  /queue /start                   - 启动队列执行器开始处理任务
  /queue /stop                    - 停止队列执行器
  /queue /status                  - 查看执行器运行状态

[bold yellow]注意:[/bold yellow]
- 任务ID是8位字符的唯一标识符
- 正在运行的任务无法被移除
- 清理操作只会移除已完成、失败或取消的任务
- 队列执行器需要手动启动才会开始执行任务
- 执行器停止后，正在运行的任务会继续完成
- 自定义 worktree 名称允许多个并行任务环境
- Worktree 名称只能包含字母、数字、下划线和连字符""",
        "ja": """[bold cyan]キュー管理コマンドヘルプ[/bold cyan]

[bold]基本的な使い方:[/bold]
  /queue <ユーザークエリ>        - クエリをキューに追加
  /queue /list [status]         - キュー内のタスクをリスト、オプションでステータスフィルタ
  /queue /remove <task_id>      - 指定されたタスクを削除
  /queue /clear                 - 完了したタスクをクリア
  /queue /stats                 - キューの統計を表示
  /queue /start                 - キュー実行器を開始
  /queue /stop                  - キュー実行器を停止
  /queue /status                - 実行器とキューのステータスを表示

[bold]ステータスフィルタオプション:[/bold]
  pending    - 実行待ちのタスク
  running    - 現在実行中のタスク
  completed  - 完了したタスク
  failed     - 実行に失敗したタスク
  cancelled  - キャンセルされたタスク

[bold]例:[/bold]
  /queue ユーザーログイン機能を実装           - クエリをキューに追加
  /queue /list                              - 全てのタスクをリスト
  /queue /list pending                      - 保留中のタスクのみをリスト
  /queue /remove abc123                     - ID abc123のタスクを削除
  /queue /clear                             - 全ての完了したタスクをクリア
  /queue /stats                             - キューの統計を表示
  /queue /start                             - キュー実行器を開始してタスクを処理
  /queue /stop                              - キュー実行器を停止
  /queue /status                            - 実行器の実行ステータスを表示

[bold yellow]注意:[/bold yellow]
- タスクIDは8文字のユニークな識別子です
- 実行中のタスクは削除できません
- クリア操作は完了、失敗またはキャンセルされたタスクのみを削除します
- キュー実行器はタスクの実行を開始するために手動で開始する必要があります
- 実行器を停止した後、実行中のタスクは完了まで継続されます""",
        "ar": """[bold cyan]مساعدة أوامر إدارة القائمة[/bold cyan]

[bold]الاستخدام الأساسي:[/bold]
  /queue <استعلام المستخدم>        - إضافة استعلام إلى القائمة
  /queue /list [status]           - سرد المهام في القائمة، مع مرشح حالة اختياري
  /queue /remove <task_id>        - إزالة المهمة المحددة
  /queue /clear                   - مسح المهام المكتملة
  /queue /stats                   - إظهار إحصائيات القائمة
  /queue /start                   - بدء تشغيل منفذ القائمة
  /queue /stop                    - إيقاف منفذ القائمة
  /queue /status                  - إظهار حالة المنفذ والقائمة

[bold]خيارات مرشح الحالة:[/bold]
  pending    - المهام في انتظار التنفيذ
  running    - المهام قيد التنفيذ حالياً
  completed  - المهام التي اكتملت
  failed     - المهام التي فشل تنفيذها
  cancelled  - المهام التي تم إلغاؤها

[bold]أمثلة:[/bold]
  /queue تنفيذ ميزة تسجيل دخول المستخدم           - إضافة استعلام إلى القائمة
  /queue /list                                 - سرد جميع المهام
  /queue /list pending                         - سرد المهام في الانتظار فقط
  /queue /remove abc123                        - إزالة المهمة بالمعرف abc123
  /queue /clear                                - مسح جميع المهام المكتملة
  /queue /stats                                - عرض إحصائيات القائمة
  /queue /start                                - بدء تشغيل منفذ القائمة لمعالجة المهام
  /queue /stop                                 - إيقاف منفذ القائمة
  /queue /status                               - عرض حالة تشغيل المنفذ

[bold yellow]ملاحظات:[/bold yellow]
- معرفات المهام هي معرفات فريدة من 8 أحرف
- المهام قيد التشغيل لا يمكن إزالتها
- عملية المسح تزيل فقط المهام المكتملة أو الفاشلة أو الملغية
- منفذ القائمة يحتاج إلى بدء تشغيل يدوي لبدء تنفيذ المهام
- بعد إيقاف المنفذ، ستستمر المهام قيد التشغيل حتى الإكمال""",
        "ru": """[bold cyan]Справка по командам управления очередью[/bold cyan]

[bold]Основное использование:[/bold]
  /queue <пользовательский_запрос>   - Добавить запрос в очередь
  /queue /list [status]             - Список задач в очереди, с опциональным фильтром статуса
  /queue /remove <task_id>          - Удалить указанную задачу
  /queue /clear                     - Очистить завершенные задачи
  /queue /stats                     - Показать статистику очереди
  /queue /start                     - Запустить исполнитель очереди
  /queue /stop                      - Остановить исполнитель очереди
  /queue /status                    - Показать статус исполнителя и очереди

[bold]Опции фильтра статуса:[/bold]
  pending    - Задачи, ожидающие выполнения
  running    - Задачи, выполняющиеся в данный момент
  completed  - Задачи, которые завершились
  failed     - Задачи, выполнение которых не удалось
  cancelled  - Задачи, которые были отменены

[bold]Примеры:[/bold]
  /queue Реализовать функцию входа пользователя           - Добавить запрос в очередь
  /queue /list                                           - Список всех задач
  /queue /list pending                                   - Список только ожидающих задач
  /queue /remove abc123                                  - Удалить задачу с ID abc123
  /queue /clear                                          - Очистить все завершенные задачи
  /queue /stats                                          - Просмотр статистики очереди
  /queue /start                                          - Запуск исполнителя очереди для обработки задач
  /queue /stop                                           - Остановка исполнителя очереди
  /queue /status                                         - Просмотр статуса работы исполнителя

[bold yellow]Примечания:[/bold yellow]
- ID задач - это 8-символьные уникальные идентификаторы
- Выполняющиеся задачи не могут быть удалены
- Операция очистки удаляет только завершенные, неудачные или отмененные задачи
- Исполнитель очереди нужно запускать вручную для начала выполнения задач
- После остановки исполнителя, выполняющиеся задачи продолжат работу до завершения"""
    }
}
