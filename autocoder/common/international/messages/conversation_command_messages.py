"""
Conversation command messages for internationalization
Contains all messages used by the conversation command functionality
"""

CONVERSATION_COMMAND_MESSAGES = {
    # 错误消息
    "conversation_param_error": {
        "en": "Parameter Error",
        "zh": "参数错误",
        "ja": "パラメータエラー",
        "ar": "خطأ في المعامل",
        "ru": "Ошибка параметра"
    },
    "conversation_provide_id": {
        "en": "Please provide the conversation ID to resume",
        "zh": "请提供要恢复的对话ID",
        "ja": "再開する会話IDを提供してください",
        "ar": "يرجى تقديم معرف المحادثة للاستئناف",
        "ru": "Пожалуйста, укажите ID беседы для продолжения"
    },
    "conversation_provide_id_or_name": {
        "en": "Please provide the conversation ID or name to resume",
        "zh": "请提供要恢复的对话ID或名称",
        "ja": "再開する会話IDまたは名前を提供してください",
        "ar": "يرجى تقديم معرف المحادثة أو الاسم للاستئناف",
        "ru": "Пожалуйста, укажите ID или название беседы для продолжения"
    },
    "conversation_not_found": {
        "en": "Conversation not found: {{conversation_id}}",
        "zh": "未找到对话: {{conversation_id}}",
        "ja": "会話が見つかりません: {{conversation_id}}",
        "ar": "لم يتم العثور على المحادثة: {{conversation_id}}",
        "ru": "Беседа не найдена: {{conversation_id}}"
    },
    "conversation_error": {
        "en": "Conversation Error",
        "zh": "对话错误",
        "ja": "会話エラー",
        "ar": "خطأ في المحادثة",
        "ru": "Ошибка беседы"
    },
    
    # 列表相关消息
    "conversation_list_no_conversations": {
        "en": "No conversations found",
        "zh": "未找到任何对话",
        "ja": "会話が見つかりません",
        "ar": "لم يتم العثور على محادثات",
        "ru": "Беседы не найдены"
    },
    "conversation_list_title": {
        "en": "Conversation List",
        "zh": "对话列表",
        "ja": "会話リスト",
        "ar": "قائمة المحادثات",
        "ru": "Список бесед"
    },
    "conversation_table_id": {
        "en": "ID",
        "zh": "ID",
        "ja": "ID",
        "ar": "المعرف",
        "ru": "ID"
    },
    "conversation_table_name": {
        "en": "Name",
        "zh": "名称",
        "ja": "名前",
        "ar": "الاسم",
        "ru": "Название"
    },
    "conversation_table_status": {
        "en": "Status",
        "zh": "状态",
        "ja": "状態",
        "ar": "الحالة",
        "ru": "Статус"
    },
    "conversation_table_time": {
        "en": "Time",
        "zh": "会话时间",
        "ja": "会話時間",
        "ar": "وقت المحادثة",
        "ru": "Время"
    },
    "conversation_table_created_at": {
        "en": "Created At",
        "zh": "创建时间",
        "ja": "作成日時",
        "ar": "وقت الإنشاء",
        "ru": "Создано"
    },
    "conversation_table_updated_at": {
        "en": "Updated At",
        "zh": "更新时间",
        "ja": "更新日時",
        "ar": "وقت التحديث",
        "ru": "Обновлено"
    },
    "conversation_status_current": {
        "en": "✓",
        "zh": "✓",
        "ja": "✓",
        "ar": "✓",
        "ru": "✓"
    },
    "conversation_list_summary": {
        "en": "Total conversations: {{total}}",
        "zh": "对话总数: {{total}}",
        "ja": "会話の総数: {{total}}",
        "ar": "إجمالي المحادثات: {{total}}",
        "ru": "Всего бесед: {{total}}"
    },
    "conversation_list_error": {
        "en": "Error loading conversation list: {{error}}",
        "zh": "加载对话列表时出错: {{error}}",
        "ja": "会話リストの読み込みエラー: {{error}}",
        "ar": "خطأ في تحميل قائمة المحادثات: {{error}}",
        "ru": "Ошибка загрузки списка бесед: {{error}}"
    },
    "conversation_current_info": {
        "en": "Current conversation: {{name}} ({{id}})",
        "zh": "当前对话: {{name}} ({{id}})",
        "ja": "現在の会話: {{name}} ({{id}})",
        "ar": "المحادثة الحالية: {{name}} ({{id}})",
        "ru": "Текущая беседа: {{name}} ({{id}})"
    },
    
    # 名字重复相关消息
    "conversation_duplicate_name": {
        "en": "Found {{count}} conversations with the name '{{name}}'. Please use the conversation ID instead.",
        "zh": "找到 {{count}} 个名为 '{{name}}' 的对话。请使用对话ID。",
        "ja": "'{{name}}' という名前の会話が {{count}} 個見つかりました。会話IDを使用してください。",
        "ar": "تم العثور على {{count}} محادثة باسم '{{name}}'. يرجى استخدام معرف المحادثة بدلاً من ذلك.",
        "ru": "Найдено {{count}} бесед с названием '{{name}}'. Пожалуйста, используйте ID беседы."
    },
    "conversation_duplicate_list": {
        "en": "Conversations with name '{{name}}'",
        "zh": "名为 '{{name}}' 的对话",
        "ja": "'{{name}}' という名前の会話",
        "ar": "المحادثات باسم '{{name}}'",
        "ru": "Беседы с названием '{{name}}'"
    },
    "conversation_use_id_instead": {
        "en": "Please use the conversation ID from the list above to resume the specific conversation.",
        "zh": "请使用上面列表中的对话ID来恢复特定对话。",
        "ja": "特定の会話を再開するには、上記のリストから会話IDを使用してください。",
        "ar": "يرجى استخدام معرف المحادثة من القائمة أعلاه لاستئناف المحادثة المحددة.",
        "ru": "Пожалуйста, используйте ID беседы из списка выше для продолжения конкретной беседы."
    },
    "conversation_not_found_by_name_or_id": {
        "en": "Conversation not found with ID or name: {{name_or_id}}",
        "zh": "未找到ID或名称为 {{name_or_id}} 的对话",
        "ja": "IDまたは名前 {{name_or_id}} の会話が見つかりません",
        "ar": "لم يتم العثور على محادثة بالمعرف أو الاسم: {{name_or_id}}",
        "ru": "Беседа с ID или названием {{name_or_id}} не найдена"
    },
    
    # 重命名相关消息
    "conversation_provide_new_name": {
        "en": "Please provide a new name for the conversation",
        "zh": "请提供对话的新名称",
        "ja": "会話の新しい名前を提供してください",
        "ar": "يرجى تقديم اسم جديد للمحادثة",
        "ru": "Пожалуйста, укажите новое название беседы"
    },
    "conversation_no_current": {
        "en": "No current conversation. Please create a new conversation or resume an existing one first.",
        "zh": "没有当前对话。请先创建新对话或恢复已有对话。",
        "ja": "現在の会話がありません。まず新しい会話を作成するか、既存の会話を再開してください。",
        "ar": "لا توجد محادثة حالية. يرجى إنشاء محادثة جديدة أو استئناف محادثة موجودة أولاً.",
        "ru": "Нет текущей беседы. Пожалуйста, сначала создайте новую беседу или продолжите существующую."
    },
    "conversation_rename_success": {
        "en": "Successfully renamed conversation {{old_id}} to '{{new_name}}'",
        "zh": "成功将对话 {{old_id}} 重命名为 '{{new_name}}'",
        "ja": "会話 {{old_id}} を '{{new_name}}' に正常に名前変更しました",
        "ar": "تم إعادة تسمية المحادثة {{old_id}} إلى '{{new_name}}' بنجاح",
        "ru": "Беседа {{old_id}} успешно переименована в '{{new_name}}'"
    },
    "conversation_rename_title": {
        "en": "Rename Conversation",
        "zh": "重命名对话",
        "ja": "会話の名前変更",
        "ar": "إعادة تسمية المحادثة",
        "ru": "Переименовать беседу"
    },
    "conversation_rename_failed": {
        "en": "Failed to rename conversation",
        "zh": "重命名对话失败",
        "ja": "会話の名前変更に失敗しました",
        "ar": "فشل في إعادة تسمية المحادثة",
        "ru": "Не удалось переименовать беседу"
    },
    "conversation_rename_error": {
        "en": "Error renaming conversation: {{error}}",
        "zh": "重命名对话时出错: {{error}}",
        "ja": "会話の名前変更エラー: {{error}}",
        "ar": "خطأ في إعادة تسمية المحادثة: {{error}}",
        "ru": "Ошибка переименования беседы: {{error}}"
    },
    
    # Command 指令相关消息
    "conversation_command_render_error": {
        "en": "Error rendering command file: {{error}}",
        "zh": "渲染命令文件时出错: {{error}}",
        "ja": "コマンドファイルのレンダリングエラー: {{error}}",
        "ar": "خطأ في عرض ملف الأمر: {{error}}",
        "ru": "Ошибка рендеринга файла команды: {{error}}"
    }
}
