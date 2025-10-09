"""
Auto-coder core messages for internationalization
Contains all messages used by the auto-coder core functionality
"""

AUTO_CODER_MESSAGES = {
    "file_scored_message": {
        "en": "File scored: {{file_path}} - Score: {{score}}",
        "zh": "文件评分: {{file_path}} - 分数: {{score}}",
        "ja": "ファイルスコア: {{file_path}} - スコア: {{score}}",
        "ar": "تقييم الملف: {{file_path}} - النتيجة: {{score}}",
        "ru": "Оценка файла: {{file_path}} - Баллы: {{score}}"
    },
    "invalid_file_pattern": {
        "en": "Invalid file pattern: {{file_pattern}}. e.g. regex://.*/package-lock\\.json",
        "zh": "无效的文件模式: {{file_pattern}}. 例如: regex://.*/package-lock\\.json",
        "ja": "無効なファイルパターン: {{file_pattern}}. 例: regex://.*/package-lock\\.json",
        "ar": "نمط ملف غير صحيح: {{file_pattern}}. مثال: regex://.*/package-lock\\.json",
        "ru": "Неверный шаблон файла: {{file_pattern}}. Например: regex://.*/package-lock\\.json"
    },
    "config_validation_error": {
        "en": "Config validation error: {{error}}",
        "zh": "配置验证错误: {{error}}",
        "ja": "設定検証エラー: {{error}}",
        "ar": "خطأ في التحقق من التكوين: {{error}}",
        "ru": "Ошибка валидации конфигурации: {{error}}"
    },
    "invalid_boolean_value": {
        "en": "Value '{{value}}' is not a valid boolean(true/false)",
        "zh": "值 '{{value}}' 不是有效的布尔值(true/false)",
        "ja": "値 '{{value}}' は有効なブール値(true/false)ではありません",
        "ar": "القيمة '{{value}}' ليست قيمة منطقية صحيحة(true/false)",
        "ru": "Значение '{{value}}' не является допустимым булевым значением(true/false)"
    },
    "invalid_integer_value": {
        "en": "Value '{{value}}' is not a valid integer",
        "zh": "值 '{{value}}' 不是有效的整数",
        "ja": "値 '{{value}}' は有効な整数ではありません",
        "ar": "القيمة '{{value}}' ليست عددًا صحيحًا صالحًا",
        "ru": "Значение '{{value}}' не является допустимым целым числом"
    },
    "invalid_float_value": {
        "en": "Value '{{value}}' is not a valid float",
        "zh": "值 '{{value}}' 不是有效的浮点数",
        "ja": "値 '{{value}}' は有効な浮動小数点数ではありません",
        "ar": "القيمة '{{value}}' ليست رقمًا عشريًا صالحًا",
        "ru": "Значение '{{value}}' не является допустимым числом с плавающей точкой"
    },
    "invalid_type_value": {
        "en": "Value '{{value}}' is not a valid type (expected: {{types}})",
        "zh": "值 '{{value}}' 不是有效的类型 (期望: {{types}})",
        "ja": "値 '{{value}}' は有効な型ではありません (期待値: {{types}})",
        "ar": "القيمة '{{value}}' ليست نوعًا صالحًا (متوقع: {{types}})",
        "ru": "Значение '{{value}}' не является допустимым типом (ожидается: {{types}})"
    },
    "value_out_of_range": {
        "en": "Value {{value}} is out of allowed range({{min}}~{{max}})",
        "zh": "值 {value} 超出允许范围({min}~{max})",
        "ja": "値 {{value}} は許可された範囲({{min}}~{{max}})を超えています",
        "ar": "القيمة {{value}} خارج النطاق المسموح({{min}}~{{max}})",
        "ru": "Значение {{value}} выходит за допустимый диапазон({{min}}~{{max}})"
    },
    "invalid_choice": {
        "en": "Value '{{value}}' is not in allowed options({{allowed}})",
        "zh": "值 '{value}' 不在允许选项中({allowed})",
        "ja": "値 '{{value}}' は許可されたオプション({{allowed}})にありません",
        "ar": "القيمة '{{value}}' ليست في الخيارات المسموحة({{allowed}})",
        "ru": "Значение '{{value}}' не входит в разрешенные параметры({{allowed}})"
    },
    "unknown_config_key": {
        "en": "Unknown config key '{{key}}'",
        "zh": "未知的配置项 '{key}'",
        "ja": "不明な設定キー '{{key}}'",
        "ar": "مفتاح التكوين غير معروف '{{key}}'",
        "ru": "Неизвестный ключ конфигурации '{{key}}'"
    },
    "model_not_found": {
        "en": "Model {{model_name}} not found",
        "zh": "未找到模型: {{model_name}}",
        "ja": "モデル {{model_name}} が見つかりません",
        "ar": "لم يتم العثور على النموذج {{model_name}}",
        "ru": "Модель {{model_name}} не найдена"
    },
    "model_info_not_found": {
        "en": "Model information not found for '{{model_name}}' in {{product_mode}} mode. Please check your model configuration in ~/.auto-coder/keys/models.json or verify the model name is correct.",
        "zh": "在 {{product_mode}} 模式下未找到模型 '{{model_name}}' 的信息。请检查 ~/.auto-coder/keys/models.json 中的模型配置或验证模型名称是否正确。",
        "ja": "{{product_mode}} モードでモデル '{{model_name}}' の情報が見つかりません。~/.auto-coder/keys/models.json のモデル設定を確認するか、モデル名が正しいことを確認してください。",
        "ar": "لم يتم العثور على معلومات النموذج '{{model_name}}' في وضع {{product_mode}}. يرجى التحقق من تكوين النموذج في ~/.auto-coder/keys/models.json أو التحقق من صحة اسم النموذج.",
        "ru": "Информация о модели '{{model_name}}' не найдена в режиме {{product_mode}}. Пожалуйста, проверьте конфигурацию модели в ~/.auto-coder/keys/models.json или убедитесь, что имя модели правильное."
    },
    "required_without_default": {
        "en": "Config key '{{key}}' requires explicit value",
        "zh": "配置项 '{key}' 需要明确设置值",
        "ja": "設定キー '{{key}}' には明示的な値が必要です",
        "ar": "مفتاح التكوين '{{key}}' يتطلب قيمة صريحة",
        "ru": "Ключ конфигурации '{{key}}' требует явного значения"
    },
    "auto_command_action_break": {
        "en": "Command {{command}} execution failed (got {{action}} result), no result can be obtained, please try again",
        "zh": "命令 {{command}} 执行失败（获取到了 {{action}} 的结果），无法获得任何结果,请重试",
        "ja": "コマンド {{command}} の実行に失敗しました（{{action}} の結果を取得）、結果を取得できません、再試行してください",
        "ar": "فشل تنفيذ الأمر {{command}} (تم الحصول على نتيجة {{action}})، لا يمكن الحصول على أي نتيجة، يرجى المحاولة مرة أخرى",
        "ru": "Выполнение команды {{command}} не удалось (получен результат {{action}}), невозможно получить результат, попробуйте снова"
    },
    "auto_command_break": {
        "en": "Auto command execution failed to execute command: {{command}}",
        "zh": "自动命令执行失败: {{command}}",
        "ja": "自動コマンドの実行に失敗しました: {{command}}",
        "ar": "فشل تنفيذ الأمر التلقائي: {{command}}",
        "ru": "Не удалось выполнить автоматическую команду: {{command}}"
    },
    "auto_command_executing": {
        "en": "\n\n============= Executing command: {{command}} =============\n\n",
        "zh": "\n\n============= 正在执行指令: {{command}} =============\n\n",
        "ja": "\n\n============= コマンドを実行中: {{command}} =============\n\n",
        "ar": "\n\n============= تنفيذ الأمر: {{command}} =============\n\n",
        "ru": "\n\n============= Выполнение команды: {{command}} =============\n\n"
    },
    "model_provider_select_title": {
        "en": "Select Model Provider",
        "zh": "选择模型供应商",
        "ja": "モデルプロバイダーを選択",
        "ar": "اختيار مزود النموذج",
        "ru": "Выберите провайдера модели"
    },
    "auto_config_analyzing": {
        "en": "Analyzing configuration...",
        "zh": "正在分析配置...",
        "ja": "設定を分析中...",
        "ar": "تحليل التكوين...",
        "ru": "Анализ конфигурации..."
    },
    "config_delete_success": {
        "en": "Successfully deleted configuration: {{key}}",
        "zh": "成功删除配置: {{key}}",
        "ja": "設定を正常に削除しました: {{key}}",
        "ar": "تم حذف التكوين بنجاح: {{key}}",
        "ru": "Конфигурация успешно удалена: {{key}}"
    },
    "config_not_found": {
        "en": "Configuration not found: {{key}}",
        "zh": "未找到配置: {{key}}",
        "ja": "設定が見つかりません: {{key}}",
        "ar": "لم يتم العثور على التكوين: {{key}}",
        "ru": "Конфигурация не найдена: {{key}}"
    },
    "config_invalid_format": {
        "en": "Invalid configuration format. Expected 'key:value'",
        "zh": "配置格式无效，应为'key:value'格式",
        "ja": "無効な設定形式です。'key:value'形式が期待されます",
        "ar": "تنسيق التكوين غير صحيح. متوقع 'key:value'",
        "ru": "Неверный формат конфигурации. Ожидается 'key:value'"
    },
    "config_value_empty": {
        "en": "Configuration value cannot be empty",
        "zh": "配置值不能为空",
        "ja": "設定値は空にできません",
        "ar": "قيمة التكوين لا يمكن أن تكون فارغة",
        "ru": "Значение конфигурации не может быть пустым"
    },
    "config_set_success": {
        "en": "Successfully set configuration: {{key}} = {{value}}",
        "zh": "成功设置配置: {{key}} = {{value}}",
        "ja": "設定を正常に設定しました: {{key}} = {{value}}",
        "ar": "تم تعيين التكوين بنجاح: {{key}} = {{value}}",
        "ru": "Конфигурация успешно установлена: {{key}} = {{value}}"
    },
    "model_provider_select_text": {
        "en": "Please select your model provider:",
        "zh": "请选择您的模型供应商：",
        "ja": "モデルプロバイダーを選択してください：",
        "ar": "يرجى اختيار مزود النموذج الخاص بك：",
        "ru": "Пожалуйста, выберите вашего провайдера модели："
    },
    "model_provider_volcano": {
        "en": "Volcano Engine",
        "zh": "火山方舟",
        "ja": "Volcano Engine",
        "ar": "محرك البركان",
        "ru": "Volcano Engine"
    },
    "model_provider_siliconflow": {
        "en": "SiliconFlow AI",
        "zh": "硅基流动",
        "ja": "SiliconFlow AI",
        "ar": "SiliconFlow AI",
        "ru": "SiliconFlow AI"
    },
    "model_provider_deepseek": {
        "en": "DeepSeek Official",
        "zh": "DeepSeek官方",
        "ja": "DeepSeek公式",
        "ar": "DeepSeek الرسمي",
        "ru": "DeepSeek Официальный"
    },
    "model_provider_openrouter": {
        "en": "OpenRouter",
        "zh": "OpenRouter",
        "ja": "OpenRouter",
        "ar": "OpenRouter",
        "ru": "OpenRouter"
    },
    "model_provider_api_key_title": {
        "en": "API Key",
        "zh": "API密钥",
        "ja": "APIキー",
        "ar": "مفتاح API",
        "ru": "API ключ"
    },
    "model_provider_volcano_api_key_text": {
        "en": "Please enter your Volcano Engine API key:",
        "zh": "请输入您的火山方舟API密钥：",
        "ja": "Volcano Engine APIキーを入力してください：",
        "ar": "يرجى إدخال مفتاح API الخاص بـ Volcano Engine:",
        "ru": "Пожалуйста, введите ваш API ключ Volcano Engine:"
    },
    "model_provider_openrouter_api_key_text": {
        "en": "Please enter your OpenRouter API key:",
        "zh": "请输入您的OpenRouter API密钥：",
        "ja": "OpenRouter APIキーを入力してください：",
        "ar": "يرجى إدخال مفتاح API الخاص بـ OpenRouter:",
        "ru": "Пожалуйста, введите ваш API ключ OpenRouter:"
    },
    "model_provider_volcano_r1_text": {
        "en": "Please enter your Volcano Engine R1 endpoint (format: ep-20250204215011-vzbsg):",
        "zh": "请输入您的火山方舟 R1 推理点(格式如: ep-20250204215011-vzbsg)：",
        "ja": "Volcano Engine R1エンドポイントを入力してください (形式: ep-20250204215011-vzbsg)：",
        "ar": "يرجى إدخال نقطة النهاية R1 الخاصة بـ Volcano Engine (التنسيق: ep-20250204215011-vzbsg):",
        "ru": "Пожалуйста, введите ваш R1 эндпойнт Volcano Engine (формат: ep-20250204215011-vzbsg):"
    },
    "model_provider_volcano_v3_text": {
        "en": "Please enter your Volcano Engine V3 endpoint (format: ep-20250204215011-vzbsg):",
        "zh": "请输入您的火山方舟 V3 推理点(格式如: ep-20250204215011-vzbsg)：",
        "ja": "Volcano Engine V3エンドポイントを入力してください (形式: ep-20250204215011-vzbsg)：",
        "ar": "يرجى إدخال نقطة النهاية V3 الخاصة بـ Volcano Engine (التنسيق: ep-20250204215011-vzbsg):",
        "ru": "Пожалуйста, введите ваш V3 эндпойнт Volcano Engine (формат: ep-20250204215011-vzbsg):"
    },
    "model_provider_siliconflow_api_key_text": {
        "en": "Please enter your SiliconFlow AI API key:",
        "zh": "请输入您的硅基流动API密钥：",
        "ja": "SiliconFlow AI APIキーを入力してください：",
        "ar": "يرجى إدخال مفتاح API الخاص بـ SiliconFlow AI:",
        "ru": "Пожалуйста, введите ваш API ключ SiliconFlow AI:"
    },
    "model_provider_deepseek_api_key_text": {
        "en": "Please enter your DeepSeek API key:",
        "zh": "请输入您的DeepSeek API密钥：",
        "ja": "DeepSeek APIキーを入力してください：",
        "ar": "يرجى إدخال مفتاح API الخاص بـ DeepSeek:",
        "ru": "Пожалуйста, введите ваш API ключ DeepSeek:"
    },    
    "model_provider_selected": {
        "en": "Provider configuration completed successfully! You can use /models command to view, add and modify all models later.",
        "zh": "供应商配置已成功完成！后续你可以使用 /models 命令，查看，新增和修改所有模型",
        "ja": "プロバイダー設定が正常に完了しました！後で /models コマンドを使用してすべてのモデルを表示、追加、変更できます。",
        "ar": "تم إكمال تكوين المزود بنجاح! يمكنك استخدام أمر /models لعرض وإضافة وتعديل جميع النماذج لاحقاً.",
        "ru": "Конфигурация провайдера успешно завершена! Вы можете использовать команду /models для просмотра, добавления и изменения всех моделей позже."
    },
    "model_provider_success_title": {
        "en": "Success",
        "zh": "成功",
        "ja": "成功",
        "ar": "نجح",
        "ru": "Успех"
    },
    "index_file_filtered": {
        "en": "File {{file_path}} is filtered by model {{model_name}} restrictions",
        "zh": "文件 {{file_path}} 被模型 {{model_name}} 的访问限制过滤",
        "ja": "ファイル {{file_path}} はモデル {{model_name}} の制限によってフィルタリングされています",
        "ar": "تم تصفية الملف {{file_path}} بواسطة قيود النموذج {{model_name}}",
        "ru": "Файл {{file_path}} отфильтрован ограничениями модели {{model_name}}"
    },
    "models_no_active": {
        "en": "No active models found",
        "zh": "未找到激活的模型",
        "ja": "アクティブなモデルが見つかりません",
        "ar": "لم يتم العثور على نماذج نشطة",
        "ru": "Активные модели не найдены"
    },
    "models_speed_test_results": {
        "en": "Model Speed Test Results",
        "zh": "模型速度测试结果",
        "ja": "モデル速度テスト結果",
        "ar": "نتائج اختبار سرعة النموذج",
        "ru": "Результаты теста скорости модели"
    },
    "models_testing": {
        "en": "Testing model: {{name}}...",
        "zh": "正在测试模型: {{name}}...",
        "ja": "モデルをテスト中: {{name}}...",
        "ar": "اختبار النموذج: {{name}}...",
        "ru": "Тестирование модели: {{name}}..."
    },
    "models_testing_start": {
        "en": "Starting speed test for all active models...",
        "zh": "开始对所有激活的模型进行速度测试...",
        "ja": "すべてのアクティブモデルの速度テストを開始しています...",
        "ar": "بدء اختبار السرعة لجميع النماذج النشطة...",
        "ru": "Запуск теста скорости для всех активных моделей..."
    },
    "models_testing_progress": {
        "en": "Testing progress: {{ completed }}/{{ total }} models",
        "zh": "测试进度: {{ completed }}/{{ total }} 个模型",
        "ja": "テスト進行状況: {{ completed }}/{{ total }} モデル",
        "ar": "تقدم الاختبار: {{ completed }}/{{ total }} نموذج",
        "ru": "Прогресс тестирования: {{ completed }}/{{ total }} моделей"
    },
    "generation_cancelled": {
        "en": "[Interrupted] Generation cancelled",
        "zh": "[已中断] 生成已取消",
        "ja": "[中断] 生成がキャンセルされました",
        "ar": "[مقاطع] تم إلغاء التوليد",
        "ru": "[Прервано] Генерация отменена"
    },
    "model_not_found": {
        "en": "Model {{model_name}} not found",
        "zh": "未找到模型: {{model_name}}",
        "ja": "モデル {{model_name}} が見つかりません",
        "ar": "لم يتم العثور على النموذج {{model_name}}",
        "ru": "Модель {{model_name}} не найдена"
    },
    "generating_shell_script": {
        "en": "Generating Shell Script",
        "zh": "正在生成 Shell 脚本",
        "ja": "シェルスクリプトを生成中",
        "ar": "توليد نص شل",
        "ru": "Генерация Shell скрипта"
    },
    "new_session_started": {
        "en": "New session started. Previous chat history has been archived.",
        "zh": "新会话已开始。之前的聊天历史已存档。",
        "ja": "新しいセッションが開始されました。以前のチャット履歴はアーカイブされました。",
        "ar": "بدأت جلسة جديدة. تم أرشفة تاريخ المحادثة السابق.",
        "ru": "Новая сессия началась. Предыдущая история чата была заархивирована."
    },
    "memory_save_success": {
        "en": "✅ Saved to your memory(path: {{path}})",
        "zh": "✅ 已保存到您的记忆中(路径: {{path}})",
        "ja": "✅ メモリに保存されました(パス: {{path}})",
        "ar": "✅ تم الحفظ في ذاكرتك (المسار: {{path}})",
        "ru": "✅ Сохранено в вашей памяти (путь: {{path}})"
    },
    "file_decode_error": {
        "en": "Failed to decode file: {{file_path}}. Tried encodings: {{encodings}}",
        "zh": "无法解码文件: {{file_path}}。尝试的编码: {{encodings}}",
        "ja": "ファイルのデコードに失敗しました: {{file_path}}。試行したエンコーディング: {{encodings}}",
        "ar": "فشل في فك تشفير الملف: {{file_path}}. الترميزات المجربة: {{encodings}}",
        "ru": "Не удалось декодировать файл: {{file_path}}. Испробованные кодировки: {{encodings}}"
    },
    "file_write_error": {
        "en": "Failed to write file: {{file_path}}. Error: {{error}}",
        "zh": "无法写入文件: {{file_path}}. 错误: {{error}}",
        "ja": "ファイルの書き込みに失敗しました: {{file_path}}. エラー: {{error}}",
        "ar": "فشل في كتابة الملف: {{file_path}}. خطأ: {{error}}",
        "ru": "Не удалось записать файл: {{file_path}}. Ошибка: {{error}}"
    },
    "yaml_load_error": {
        "en": "Error loading yaml file {{yaml_file}}: {{error}}",
        "zh": "加载YAML文件出错 {{yaml_file}}: {{error}}",
        "ja": "YAMLファイルの読み込みエラー {{yaml_file}}: {{error}}",
        "ar": "خطأ في تحميل ملف yaml {{yaml_file}}: {{error}}",
        "ru": "Ошибка загрузки YAML файла {{yaml_file}}: {{error}}"
    },
    "git_command_error": {
        "en": "Git command execution error: {{error}}",
        "zh": "Git命令执行错误: {{error}}",
        "ja": "Gitコマンド実行エラー: {{error}}",
        "ar": "خطأ في تنفيذ أمر Git: {{error}}",
        "ru": "Ошибка выполнения Git команды: {{error}}"
    },
    "get_commit_diff_error": {
        "en": "Error getting commit diff: {{error}}",
        "zh": "获取commit diff时出错: {{error}}",
        "ja": "コミット差分の取得エラー: {{error}}",
        "ar": "خطأ في الحصول على فرق الكوميت: {{error}}",
        "ru": "Ошибка получения разности коммитов: {{error}}"
    },
    "no_latest_commit": {
        "en": "Unable to get latest commit information",
        "zh": "无法获取最新的提交信息",
        "ja": "最新のコミット情報を取得できません",
        "ar": "غير قادر على الحصول على معلومات أحدث كوميت",
        "ru": "Невозможно получить информацию о последнем коммите"
    },
    "code_review_error": {
        "en": "Code review process error: {{error}}",
        "zh": "代码审查过程出错: {{error}}",
        "ja": "コードレビュープロセスエラー: {{error}}",
        "ar": "خطأ في عملية مراجعة الكود: {{error}}",
        "ru": "Ошибка процесса ревью кода: {{error}}"
    },
    "index_file_too_large": {
        "en": "⚠️ File {{ file_path }} is too large ({{ file_size }} > {{ max_length }}), splitting into chunks...",
        "zh": "⚠️ 文件 {{ file_path }} 过大 ({{ file_size }} > {{ max_length }}), 正在分块处理...",
        "ja": "⚠️ ファイル {{ file_path }} が大きすぎます ({{ file_size }} > {{ max_length }})、チャンクに分割中...",
        "ar": "⚠️ الملف {{ file_path }} كبير جداً ({{ file_size }} > {{ max_length }})، جاري التقسيم إلى أجزاء...",
        "ru": "⚠️ Файл {{ file_path }} слишком большой ({{ file_size }} > {{ max_length }}), разделение на части..."
    },
    "index_update_success": {
        "en": "✅ {{ model_name }} Successfully updated index for {{ file_path }} (md5: {{ md5 }}) in {{ duration }}s, input_tokens: {{ input_tokens }}, output_tokens: {{ output_tokens }}, input_cost: {{ input_cost }}, output_cost: {{ output_cost }}",
        "zh": "✅ {{ model_name }} 成功更新 {{ file_path }} 的索引 (md5: {{ md5 }}), 耗时 {{ duration }} 秒, 输入token数: {{ input_tokens }}, 输出token数: {{ output_tokens }}, 输入成本: {{ input_cost }}, 输出成本: {{ output_cost }}",
        "ja": "✅ {{ model_name }} {{ file_path }} のインデックスを正常に更新しました (md5: {{ md5 }}) {{ duration }}秒で完了, 入力トークン数: {{ input_tokens }}, 出力トークン数: {{ output_tokens }}, 入力コスト: {{ input_cost }}, 出力コスト: {{ output_cost }}",
        "ar": "✅ {{ model_name }} تم تحديث فهرس {{ file_path }} بنجاح (md5: {{ md5 }}) في {{ duration }} ثانية, رموز الإدخال: {{ input_tokens }}, رموز الإخراج: {{ output_tokens }}, تكلفة الإدخال: {{ input_cost }}, تكلفة الإخراج: {{ output_cost }}",
        "ru": "✅ {{ model_name }} Успешно обновлен индекс для {{ file_path }} (md5: {{ md5 }}) за {{ duration }}с, входные токены: {{ input_tokens }}, выходные токены: {{ output_tokens }}, стоимость входа: {{ input_cost }}, стоимость выхода: {{ output_cost }}"
    },
    "index_build_error": {
        "en": "❌ {{ model_name }} Error building index for {{ file_path }}: {{ error }}",
        "zh": "❌ {{ model_name }} 构建 {{ file_path }} 索引时出错: {{ error }}",
        "ja": "❌ {{ model_name }} {{ file_path }} のインデックス構築エラー: {{ error }}",
        "ar": "❌ {{ model_name }} خطأ في بناء فهرس {{ file_path }}: {{ error }}",
        "ru": "❌ {{ model_name }} Ошибка построения индекса для {{ file_path }}: {{ error }}"
    },
    "index_build_summary": {
        "en": "📊 Total Files: {{ total_files }}, Need to Build Index: {{ num_files }}",
        "zh": "📊 总文件数: {{ total_files }}, 需要构建索引: {{ num_files }}",
        "ja": "📊 総ファイル数: {{ total_files }}, インデックス構築が必要: {{ num_files }}",
        "ar": "📊 إجمالي الملفات: {{ total_files }}, يحتاج لبناء فهرس: {{ num_files }}",
        "ru": "📊 Всего файлов: {{ total_files }}, Нужно построить индекс: {{ num_files }}"
    },
    "building_index_progress": {
        "en": "⏳ Building Index: {{ counter }}/{{ num_files }}...",
        "zh": "⏳ 正在构建索引: {{ counter }}/{{ num_files }}...",
        "ja": "⏳ インデックス構築中: {{ counter }}/{{ num_files }}...",
        "ar": "⏳ بناء الفهرس: {{ counter }}/{{ num_files }}...",
        "ru": "⏳ Построение индекса: {{ counter }}/{{ num_files }}..."
    },
    "index_source_dir_mismatch": {
        "en": "⚠️ Source directory mismatch (file_path: {{ file_path }}, source_dir: {{ source_dir }})",
        "zh": "⚠️ 源目录不匹配 (文件路径: {{ file_path }}, 源目录: {{ source_dir }})",
        "ja": "⚠️ ソースディレクトリの不一致 (ファイルパス: {{ file_path }}, ソースディレクトリ: {{ source_dir }})",
        "ar": "⚠️ عدم تطابق مجلد المصدر (مسار الملف: {{ file_path }}, مجلد المصدر: {{ source_dir }})",
        "ru": "⚠️ Несоответствие исходной директории (путь файла: {{ file_path }}, исходная директория: {{ source_dir }})"
    },
    "index_related_files_fail": {
        "en": "⚠️ Failed to find related files for chunk {{ chunk_count }}",
        "zh": "⚠️ 无法为块 {{ chunk_count }} 找到相关文件",
        "ja": "⚠️ チャンク {{ chunk_count }} の関連ファイルの検索に失敗しました",
        "ar": "⚠️ فشل في العثور على الملفات ذات الصلة للجزء {{ chunk_count }}",
        "ru": "⚠️ Не удалось найти связанные файлы для части {{ chunk_count }}"
    },
    "index_threads_completed": {
        "en": "✅ Completed {{ completed_threads }}/{{ total_threads }} threads",
        "zh": "✅ 已完成 {{ completed_threads }}/{{ total_threads }} 个线程",
        "ja": "✅ {{ completed_threads }}/{{ total_threads }} スレッドが完了しました",
        "ar": "✅ تم إكمال {{ completed_threads }}/{{ total_threads }} خيوط",
        "ru": "✅ Завершено {{ completed_threads }}/{{ total_threads }} потоков"
    },
    "index_file_removed": {
        "en": "🗑️ Removed non-existent file index: {{ file_path }}",
        "zh": "🗑️ 已移除不存在的文件索引：{{ file_path }}",
        "ja": "🗑️ 存在しないファイルのインデックスを削除しました：{{ file_path }}",
        "ar": "🗑️ تم إزالة فهرس الملف غير الموجود: {{ file_path }}",
        "ru": "🗑️ Удален индекс несуществующего файла: {{ file_path }}"
    },
    "index_file_saved": {
        "en": "💾 Saved index file, updated {{ updated_files }} files, removed {{ removed_files }} files, input_tokens: {{ input_tokens }}, output_tokens: {{ output_tokens }}, input_cost: {{ input_cost }}, output_cost: {{ output_cost }}",
        "zh": "💾 已保存索引文件，更新了 {{ updated_files }} 个文件，移除了 {{ removed_files }} 个文件，输入token数: {{ input_tokens }}, 输出token数: {{ output_tokens }}, 输入成本: {{ input_cost }}, 输出成本: {{ output_cost }}",
        "ja": "💾 インデックスファイルを保存しました、{{ updated_files }} ファイルを更新、{{ removed_files }} ファイルを削除、入力トークン数: {{ input_tokens }}, 出力トークン数: {{ output_tokens }}, 入力コスト: {{ input_cost }}, 出力コスト: {{ output_cost }}",
        "ar": "💾 تم حفظ ملف الفهرس، تم تحديث {{ updated_files }} ملف، تم إزالة {{ removed_files }} ملف، رموز الإدخال: {{ input_tokens }}, رموز الإخراج: {{ output_tokens }}, تكلفة الإدخال: {{ input_cost }}, تكلفة الإخراج: {{ output_cost }}",
        "ru": "💾 Индексный файл сохранен, обновлено {{ updated_files }} файлов, удалено {{ removed_files }} файлов, входные токены: {{ input_tokens }}, выходные токены: {{ output_tokens }}, стоимость входа: {{ input_cost }}, стоимость выхода: {{ output_cost }}"
    },
    "manual_file_saved": {
        "en": "📄 Manual file saved: {{ file_path }}",
        "zh": "📄 手册文件已保存: {{ file_path }}",
        "ja": "📄 マニュアルファイルが保存されました: {{ file_path }}",
        "ar": "📄 تم حفظ ملف الدليل: {{ file_path }}",
        "ru": "📄 Файл руководства сохранен: {{ file_path }}"
    },
    "conversations_saved": {
        "en": "💬 Conversations saved to {{ directory }} directory",
        "zh": "💬 对话内容已保存到 {{ directory }} 目录",
        "ja": "💬 会話が {{ directory }} ディレクトリに保存されました",
        "ar": "💬 تم حفظ المحادثات في دليل {{ directory }}",
        "ru": "💬 Разговоры сохранены в директории {{ directory }}"
    },
    "conversations_save_failed": {
        "en": "❌ Failed to save conversations: {{ error }}",
        "zh": "❌ 保存对话内容失败: {{ error }}",
        "ja": "❌ 会話の保存に失敗しました: {{ error }}",
        "ar": "❌ فشل في حفظ المحادثات: {{ error }}",
        "ru": "❌ Не удалось сохранить разговоры: {{ error }}"
    },
    "task_cancelled_by_user": {
        "en": "Task was cancelled by user",
        "zh": "任务被用户取消",
        "ja": "タスクがユーザーによってキャンセルされました",
        "ar": "تم إلغاء المهمة من قبل المستخدم",
        "ru": "Задача была отменена пользователем"
    },
    "cancellation_requested": {
        "en": "Cancellation requested, waiting for thread to terminate...",
        "zh": "已请求取消，正在等待线程终止...",
        "ja": "キャンセルが要求されました、スレッドの終了を待機中...",
        "ar": "تم طلب الإلغاء، في انتظار إنهاء الخيط...",
        "ru": "Запрошена отмена, ожидание завершения потока..."
    },
    "force_terminating_thread": {
        "en": "Force terminating thread after timeout",
        "zh": "线程超时强制终止",
        "ja": "タイムアウト後にスレッドを強制終了",
        "ar": "إنهاء الخيط بالقوة بعد انتهاء المهلة",
        "ru": "Принудительное завершение потока после таймаута"
    },
    "force_raising_keyboard_interrupt": {
        "en": "Force raising KeyboardInterrupt after timeout",
        "zh": "超时强制抛出键盘中断异常",
        "ja": "タイムアウト後にKeyboardInterruptを強制発生",
        "ar": "فرض رفع KeyboardInterrupt بعد انتهاء المهلة",
        "ru": "Принудительное вызов KeyboardInterrupt после таймаута"
    },
    "thread_terminated": {
        "en": "Thread terminated",
        "zh": "线程已终止",
        "ja": "スレッドが終了しました",
        "ar": "تم إنهاء الخيط",
        "ru": "Поток завершен"
    },
    "human_as_model_instructions": {
        "en": "You are now in Human as Model mode. The content has been copied to your clipboard.\nThe system is waiting for your input. When finished, enter 'EOF' on a new line to submit.\nUse '/break' to exit this mode. If you have issues with copy-paste, use '/clear' to clean and paste again.",
        "zh": "您现在处于人类作为模型模式。内容已复制到您的剪贴板。\n系统正在等待您的输入。完成后，在新行输入'EOF'提交。\n使用'/break'退出此模式。如果复制粘贴有问题，使用'/clear'清理并重新粘贴。",
        "ja": "人間モデルモードになりました。内容はクリップボードにコピーされました。\nシステムはあなたの入力を待っています。完了したら、新しい行に'EOF'を入力して送信してください。\nこのモードを終了するには'/break'を使用してください。コピー&ペーストに問題がある場合は、'/clear'を使用してクリアしてから再度ペーストしてください。",
        "ar": "أنت الآن في وضع الإنسان كنموذج. تم نسخ المحتوى إلى الحافظة الخاصة بك.\nالنظام ينتظر إدخالك. عند الانتهاء، أدخل 'EOF' في سطر جديد للإرسال.\nاستخدم '/break' للخروج من هذا الوضع. إذا كانت لديك مشاكل مع النسخ واللصق، استخدم '/clear' للتنظيف واللصق مرة أخرى.",
        "ru": "Вы находитесь в режиме \"Человек как модель\". Содержимое скопировано в ваш буфер обмена.\nСистема ожидает ваш ввод. После завершения введите 'EOF' на новой строке для отправки.\nИспользуйте '/break' для выхода из этого режима. Если у вас проблемы с копированием и вставкой, используйте '/clear' для очистки и повторной вставки."
    },
    "clipboard_not_supported": {
        "en": "pyperclip not installed or clipboard is not supported, instruction will not be copied to clipboard.",
        "zh": "未安装pyperclip或不支持剪贴板，指令将不会被复制到剪贴板。",
        "ja": "pyperclipがインストールされていないか、クリップボードがサポートされていません。指示はクリップボードにコピーされません。",
        "ar": "pyperclip غير مثبت أو الحافظة غير مدعومة، لن يتم نسخ التعليمات إلى الحافظة.",
        "ru": "pyperclip не установлен или буфер обмена не поддерживается, инструкция не будет скопирована в буфер обмена."
    },
    "human_as_model_instructions_no_clipboard": {
        "en": "You are now in Human as Model mode. [bold red]The content could not be copied to your clipboard.[/bold red]\nbut you can copy prompt from output.txt file.\nThe system is waiting for your input. When finished, enter 'EOF' on a new line to submit.\nUse '/break' to exit this mode. If you have issues with copy-paste, use '/clear' to clean and paste again.",
        "zh": "您现在处于人类作为模型模式。[bold red]内容无法复制到您的剪贴板。[/bold red]\n但您可以从output.txt文件复制提示。\n系统正在等待您的输入。完成后，在新行输入'EOF'提交。\n使用'/break'退出此模式。如果复制粘贴有问题，使用'/clear'清理并重新粘贴。",
        "ja": "人間モデルモードになりました。[bold red]内容をクリップボードにコピーできませんでした。[/bold red]\nただし、output.txtファイルからプロンプトをコピーできます。\nシステムはあなたの入力を待っています。完了したら、新しい行に'EOF'を入力して送信してください。\nこのモードを終了するには'/break'を使用してください。コピー&ペーストに問題がある場合は、'/clear'を使用してクリアしてから再度ペーストしてください。",
        "ar": "أنت الآن في وضع الإنسان كنموذج. [bold red]لا يمكن نسخ المحتوى إلى الحافظة الخاصة بك.[/bold red]\nولكن يمكنك نسخ المطالبة من ملف output.txt.\nالنظام ينتظر إدخالك. عند الانتهاء، أدخل 'EOF' في سطر جديد للإرسال.\nاستخدم '/break' للخروج من هذا الوضع. إذا كانت لديك مشاكل مع النسخ واللصق، استخدم '/clear' للتنظيف واللصق مرة أخرى.",
        "ru": "Вы находитесь в режиме \"Человек как модель\". [bold red]Содержимое не может быть скопировано в ваш буфер обмена.[/bold red]\nно вы можете скопировать запрос из файла output.txt.\nСистема ожидает ваш ввод. После завершения введите 'EOF' на новой строке для отправки.\nИспользуйте '/break' для выхода из этого режима. Если у вас проблемы с копированием и вставкой, используйте '/clear' для очистки и повторной вставки."
    },
    "phase1_processing_sources": {
        "en": "Phase 1: Processing REST/RAG/Search sources...",
        "zh": "阶段 1: 正在处理 REST/RAG/Search 源...",
        "ja": "フェーズ 1: REST/RAG/Search ソースを処理中...",
        "ar": "المرحلة 1: معالجة مصادر REST/RAG/Search...",
        "ru": "Фаза 1: Обработка источников REST/RAG/Search..."
    },
    "phase2_building_index": {
        "en": "Phase 2: Building index for all files...",
        "zh": "阶段 2: 正在为所有文件构建索引...",
        "ja": "フェーズ 2: すべてのファイルのインデックスを構築中...",
        "ar": "المرحلة 2: بناء فهرس لجميع الملفات...",
        "ru": "Фаза 2: Построение индекса для всех файлов..."
    },
    "phase6_file_selection": {
        "en": "Phase 6: Processing file selection and limits...",
        "zh": "阶段 6: 正在处理文件选择和限制...",
        "ja": "フェーズ 6: ファイル選択と制限を処理中...",
        "ar": "المرحلة 6: معالجة اختيار الملفات والحدود...",
        "ru": "Фаза 6: Обработка выбора файлов и ограничений..."
    },
    "phase7_preparing_output": {
        "en": "Phase 7: Preparing final output...",
        "zh": "阶段 7: 正在准备最终输出...",
        "ja": "フェーズ 7: 最終出力を準備中...",
        "ar": "المرحلة 7: إعداد الإخراج النهائي...",
        "ru": "Фаза 7: Подготовка финального вывода..."
    },
    "chat_human_as_model_instructions": {
        "en": "Chat is now in Human as Model mode.\nThe question has been copied to your clipboard.\nPlease use Web version model to get the answer.\nOr use /conf human_as_model:false to close this mode and get the answer in terminal directlyPaste the answer to the input box below, use '/break' to exit, '/clear' to clear the screen, '/eof' to submit.",
        "zh": "\n============= Chat 处于 Human as Model 模式 =============\n问题已复制到剪贴板\n请使用Web版本模型获取答案\n或者使用 /conf human_as_model:false 关闭该模式直接在终端获得答案。将获得答案黏贴到下面的输入框，换行后，使用 '/break' 退出，'/clear' 清屏，'/eof' 提交。",
        "ja": "チャットは人間モデルモードになりました。\n質問はクリップボードにコピーされました。\nWeb版モデルを使用して回答を取得してください。\nまたは /conf human_as_model:false を使用してこのモードを閉じ、ターミナルで直接回答を取得してください。下の入力ボックスに回答をペーストし、'/break'で終了、'/clear'で画面クリア、'/eof'で送信してください。",
        "ar": "المحادثة الآن في وضع الإنسان كنموذج.\nتم نسخ السؤال إلى الحافظة الخاصة بك.\nيرجى استخدام النموذج الإصدار الويب للحصول على الإجابة.\nأو استخدم /conf human_as_model:false لإغلاق هذا الوضع والحصول على الإجابة في المحطة مباشرة. الصق الإجابة في مربع الإدخال أدناه، استخدم '/break' للخروج، '/clear' لمسح الشاشة، '/eof' للإرسال.",
        "ru": "Чат находится в режиме \"Человек как модель\".\nВопрос скопирован в ваш буфер обмена.\nПожалуйста, используйте веб-версию модели для получения ответа.\nИли используйте /conf human_as_model:false для закрытия этого режима и получения ответа прямо в терминале. Вставьте ответ в поле ввода ниже, используйте '/break' для выхода, '/clear' для очистки экрана, '/eof' для отправки."
    },
    "code_generation_start": {
        "en": "Auto generate the code...",
        "zh": "正在自动生成代码...",
        "ja": "コードを自動生成中...",
        "ar": "توليد الكود تلقائياً...",
        "ru": "Автоматическая генерация кода..."
    },
    "code_generation_complete": {
        "en": "{{ model_names}} Code generation completed in {{ duration }} seconds (sampling_count: {{ sampling_count }}), input_tokens_count: {{ input_tokens }}, generated_tokens_count: {{ output_tokens }}, input_cost: {{ input_cost }}, output_cost: {{ output_cost }}, speed: {{ speed }} tokens/s",
        "zh": "{{ model_names}} 代码生成完成，耗时 {{ duration }} 秒 (采样数: {{ sampling_count }}), 输入token数: {{ input_tokens }}, 输出token数: {{ output_tokens }}, 输入成本: {{ input_cost }}, 输出成本: {{ output_cost }}, 速度: {{ speed }} tokens/秒",
        "ja": "{{ model_names}} コード生成が完了しました {{ duration }} 秒 (サンプリング数: {{ sampling_count }})、入力トークン数: {{ input_tokens }}、出力トークン数: {{ output_tokens }}、入力コスト: {{ input_cost }}、出力コスト: {{ output_cost }}、速度: {{ speed }} tokens/秒",
        "ar": "{{ model_names}} اكتمل توليد الكود في {{ duration }} ثانية (عدد العينات: {{ sampling_count }})، عدد رموز الإدخال: {{ input_tokens }}، عدد رموز الإخراج: {{ output_tokens }}، تكلفة الإدخال: {{ input_cost }}، تكلفة الإخراج: {{ output_cost }}، السرعة: {{ speed }} رمز/ثانية",
        "ru": "{{ model_names}} Генерация кода завершена за {{ duration }} секунд (количество выборок: {{ sampling_count }}), входных токенов: {{ input_tokens }}, выходных токенов: {{ output_tokens }}, стоимость входа: {{ input_cost }}, стоимость выхода: {{ output_cost }}, скорость: {{ speed }} токенов/с"
    },
    "generate_max_rounds_reached": {
        "en": "⚠️ Generation stopped after reaching the maximum allowed rounds ({{ count }}/{{ max_rounds }}). Current generated content length: {{ generated_tokens }}. If the output is incomplete, consider increasing 'generate_max_rounds' in configuration.",
        "zh": "⚠️ 生成已停止，因为达到了最大允许轮数 ({{ count }}/{{ max_rounds }})。当前生成内容长度: {{ generated_tokens }} tokens。如果输出不完整，请考虑在配置中增加 'generate_max_rounds'。",
        "ja": "⚠️ 最大許可ラウンド数に達したため生成が停止しました ({{ count }}/{{ max_rounds }})。現在の生成コンテンツ長: {{ generated_tokens }} トークン。出力が不完全な場合は、設定で 'generate_max_rounds' を増やすことを検討してください。",
        "ar": "⚠️ توقف التوليد بعد الوصول إلى أقصى عدد جولات مسموح ({{ count }}/{{ max_rounds }})। طول المحتوى المولد الحالي: {{ generated_tokens }} رمز。إذا كان الإخراج غير مكتمل، فكر في زيادة 'generate_max_rounds' في التكوين.",
        "ru": "⚠️ Генерация остановлена после достижения максимального количества раундов ({{ count }}/{{ max_rounds }}). Текущая длина сгенерированного контента: {{ generated_tokens }} токенов. Если вывод неполный, рассмотрите увеличение 'generate_max_rounds' в конфигурации."
    },
    "code_merge_start": {
        "en": "Auto merge the code...",
        "zh": "正在自动合并代码...",
        "ja": "コードを自動マージ中...",
        "ar": "دمج الكود تلقائياً...",
        "ru": "Автоматическое слияние кода..."
    },
    "code_execution_warning": {
        "en": "Content(send to model) is {{ content_length }} tokens (you may collect too much files), which is larger than the maximum input length {{ max_length }}",
        "zh": "发送给模型的内容长度为 {{ content_length }} tokens（您可能收集了太多文件），超过了最大输入长度 {{ max_length }}",
        "ja": "モデルに送信されるコンテンツは {{ content_length }} トークンです（ファイルを集めすぎている可能性があります）、最大入力長 {{ max_length }} を超えています",
        "ar": "المحتوى (المرسل إلى النموذج) هو {{ content_length }} رمز (قد تكون جمعت ملفات كثيرة جداً)، وهو أكبر من الطول الأقصى للإدخال {{ max_length }}",
        "ru": "Содержимое (отправляемое в модель) составляет {{ content_length }} токенов (возможно, вы собрали слишком много файлов), что больше максимальной длины ввода {{ max_length }}"
    },
    "quick_filter_start": {
        "en": "{{ model_name }} Starting filter context(quick_filter)...",
        "zh": "{{ model_name }} 开始查找上下文(quick_filter)...",
        "ja": "{{ model_name }} コンテキストのフィルタリングを開始(quick_filter)...",
        "ar": "{{ model_name }} بدء تصفية السياق(quick_filter)...",
        "ru": "{{ model_name }} Начинаем фильтрацию контекста(quick_filter)..."
    },
    "normal_filter_start": {
        "en": "{{ model_name }} Starting filter context(normal_filter)...",
        "zh": "{{ model_name }} 开始查找上下文(normal_filter)...",
        "ja": "{{ model_name }} コンテキストのフィルタリングを開始(normal_filter)...",
        "ar": "{{ model_name }} بدء تصفية السياق(normal_filter)...",
        "ru": "{{ model_name }} Начинаем фильтрацию контекста(normal_filter)..."
    },
    "pylint_check_failed": {
        "en": "⚠️ Pylint check failed: {{ error_message }}",
        "zh": "⚠️ Pylint 检查失败: {{ error_message }}",
        "ja": "⚠️ Pylint チェックが失敗しました: {{ error_message }}",
        "ar": "⚠️ فشل فحص Pylint: {{ error_message }}",
        "ru": "⚠️ Проверка Pylint не удалась: {{ error_message }}"
    },
    "pylint_error": {
        "en": "❌ Error running pylint: {{ error_message }}",
        "zh": "❌ 运行 Pylint 时出错: {{ error_message }}",
        "ja": "❌ Pylint の実行エラー: {{ error_message }}",
        "ar": "❌ خطأ في تشغيل pylint: {{ error_message }}",
        "ru": "❌ Ошибка запуска pylint: {{ error_message }}"
    },
    "unmerged_blocks_warning": {
        "en": "⚠️ Found {{ num_blocks }} unmerged blocks, the changes will not be applied. Please review them manually then try again.",
        "zh": "⚠️ 发现 {{ num_blocks }} 个未合并的代码块，更改将不会被应用。请手动检查后重试。",
        "ja": "⚠️ {{ num_blocks }} 個のマージされていないブロックが見つかりました、変更は適用されません。手動で確認してから再試行してください。",
        "ar": "⚠️ تم العثور على {{ num_blocks }} كتل غير مدموجة، لن يتم تطبيق التغييرات. يرجى مراجعتها يدوياً ثم المحاولة مرة أخرى.",
        "ru": "⚠️ Найдено {{ num_blocks }} неслитых блоков, изменения не будут применены. Пожалуйста, проверьте их вручную и попробуйте снова."
    },
    "pylint_file_check_failed": {
        "en": "⚠️ Pylint check failed for {{ file_path }}. Changes not applied. Error: {{ error_message }}",
        "zh": "⚠️ {{ file_path }} 的 Pylint 检查失败。更改未应用。错误: {{ error_message }}",
        "ja": "⚠️ {{ file_path }} の Pylint チェックが失敗しました。変更は適用されませんでした。エラー: {{ error_message }}",
        "ar": "⚠️ فشل فحص Pylint لـ {{ file_path }}. لم يتم تطبيق التغييرات. خطأ: {{ error_message }}",
        "ru": "⚠️ Проверка Pylint не удалась для {{ file_path }}. Изменения не применены. Ошибка: {{ error_message }}"
    },
    "merge_success": {
        "en": "✅ Merged changes in {{ num_files }} files {{ num_changes }}/{{ total_blocks }} blocks.",
        "zh": "✅ 成功合并了 {{ num_files }} 个文件中的更改 {{ num_changes }}/{{ total_blocks }} 个代码块。",
        "ja": "✅ {{ num_files }} ファイルの変更をマージしました {{ num_changes }}/{{ total_blocks }} ブロック。",
        "ar": "✅ تم دمج التغييرات في {{ num_files }} ملف {{ num_changes }}/{{ total_blocks }} كتلة.",
        "ru": "✅ Слияние изменений в {{ num_files }} файлах {{ num_changes }}/{{ total_blocks }} блоков."
    },
    "no_changes_made": {
        "en": "⚠️ No changes were made to any files.",
        "zh": "⚠️ 未对任何文件进行更改。这个原因可能是因为coding函数生成的文本块格式有问题，导致无法合并进项目",
        "ja": "⚠️ どのファイルも変更されませんでした。",
        "ar": "⚠️ لم يتم إجراء أي تغييرات على أي ملفات.",
        "ru": "⚠️ Никаких изменений в файлах не было внесено."
    },
    "files_merged": {
        "en": "✅ Merged {{ total }} files into the project.",
        "zh": "✅ 成功合并了 {{ total }} 个文件到项目中。",
        "ja": "✅ {{ total }} ファイルをプロジェクトにマージしました。",
        "ar": "✅ تم دمج {{ total }} ملف في المشروع.",
        "ru": "✅ Слито {{ total }} файлов в проект."
    },
    "merge_failed": {
        "en": "❌ Merge file {{ path }} failed: {{ error }}",
        "zh": "❌ 合并文件 {{ path }} 失败: {{ error }}",
        "ja": "❌ ファイル {{ path }} のマージに失敗しました: {{ error }}",
        "ar": "❌ فشل دمج الملف {{ path }}: {{ error }}",
        "ru": "❌ Слияние файла {{ path }} не удалось: {{ error }}"
    },
    "files_merged_total": {
        "en": "✅ Merged {{ total }} files into the project.",
        "zh": "✅ 合并了 {{ total }} 个文件到项目中。",
        "ja": "✅ {{ total }} ファイルをプロジェクトにマージしました。",
        "ar": "✅ تم دمج {{ total }} ملف في المشروع.",
        "ru": "✅ Слито {{ total }} файлов в проект."
    },
    "ranking_skip": {
        "en": "Only 1 candidate, skip ranking",
        "zh": "只有1个候选项，跳过排序",
        "ja": "候補が1つのみ、ランキングをスキップ",
        "ar": "مرشح واحد فقط، تخطي الترتيب",
        "ru": "Только 1 кандидат, пропускаем ранжирование"
    },
    "ranking_start": {
        "en": "Start ranking {{ count }} candidates using model {{ model_name }}",
        "zh": "开始对 {{ count }} 个候选项进行排序,使用模型 {{ model_name }} 打分",
        "ja": "モデル {{ model_name }} を使用して {{ count }} 個の候補のランキングを開始",
        "ar": "بدء ترتيب {{ count }} مرشحين باستخدام النموذج {{ model_name }}",
        "ru": "Начинаем ранжирование {{ count }} кандидатов с использованием модели {{ model_name }}"
    },
    "ranking_failed_request": {
        "en": "Ranking request failed: {{ error }}",
        "zh": "排序请求失败: {{ error }}",
        "ja": "ランキングリクエストが失敗しました: {{ error }}",
        "ar": "فشل طلب الترتيب: {{ error }}",
        "ru": "Запрос ранжирования не удался: {{ error }}"
    },
    "ranking_all_failed": {
        "en": "All ranking requests failed",
        "zh": "所有排序请求都失败",
        "ja": "すべてのランキングリクエストが失敗しました",
        "ar": "فشلت جميع طلبات الترتيب",
        "ru": "Все запросы ранжирования не удались"
    },
    "ranking_complete": {
        "en": "{{ model_names }} Ranking completed in {{ elapsed }}s, total voters: {{ total_tasks }}, best candidate index: {{ best_candidate }}, scores: {{ scores }}, input_tokens: {{ input_tokens }}, output_tokens: {{ output_tokens }}, input_cost: {{ input_cost }}, output_cost: {{ output_cost }}, speed: {{ speed }} tokens/s",
        "zh": "{{ model_names }} 排序完成，耗时 {{ elapsed }} 秒，总投票数: {{ total_tasks }}，最佳候选索引: {{ best_candidate }}，得分: {{ scores }}，输入token数: {{ input_tokens }}，输出token数: {{ output_tokens }}，输入成本: {{ input_cost }}, 输出成本: {{ output_cost }}，速度: {{ speed }} tokens/秒",
        "ja": "{{ model_names }} ランキング完了 {{ elapsed }}秒、総投票者数: {{ total_tasks }}、最適候補インデックス: {{ best_candidate }}、スコア: {{ scores }}、入力トークン数: {{ input_tokens }}、出力トークン数: {{ output_tokens }}、入力コスト: {{ input_cost }}, 出力コスト: {{ output_cost }}、速度: {{ speed }} tokens/秒",
        "ar": "{{ model_names }} اكتمل الترتيب في {{ elapsed }} ثانية، إجمالي المصوتين: {{ total_tasks }}، أفضل فهرس مرشح: {{ best_candidate }}، النقاط: {{ scores }}، رموز الإدخال: {{ input_tokens }}، رموز الإخراج: {{ output_tokens }}، تكلفة الإدخال: {{ input_cost }}، تكلفة الإخراج: {{ output_cost }}، السرعة: {{ speed }} رمز/ثانية",
        "ru": "{{ model_names }} Ранжирование завершено за {{ elapsed }}с, всего голосующих: {{ total_tasks }}, индекс лучшего кандидата: {{ best_candidate }}, баллы: {{ scores }}, входных токенов: {{ input_tokens }}, выходных токенов: {{ output_tokens }}, стоимость входа: {{ input_cost }}, стоимость выхода: {{ output_cost }}, скорость: {{ speed }} токенов/с"
    },
    "ranking_process_failed": {
        "en": "Ranking process failed: {{ error }}",
        "zh": "排序过程失败: {{ error }}",
        "ja": "ランキングプロセスが失敗しました: {{ error }}",
        "ar": "فشل عملية الترتيب: {{ error }}",
        "ru": "Процесс ранжирования не удался: {{ error }}"
    },
    "ranking_failed": {
        "en": "Ranking failed in {{ elapsed }}s, using original order",
        "zh": "排序失败，耗时 {{ elapsed }} 秒，使用原始顺序",
        "ja": "ランキングが {{ elapsed }}秒で失敗しました、元の順序を使用します",
        "ar": "فشل الترتيب في {{ elapsed }} ثانية، استخدام الترتيب الأصلي",
        "ru": "Ранжирование не удалось за {{ elapsed }}с, используем исходный порядок"
    },
    "begin_index_source_code": {
        "en": "🚀 Begin to index source code in {{ source_dir }}",
        "zh": "🚀 开始为 {{ source_dir }} 中的源代码建立索引",
        "ja": "🚀 {{ source_dir }} のソースコードのインデックス作成を開始",
        "ar": "🚀 بدء فهرسة الكود المصدري في {{ source_dir }}",
        "ru": "🚀 Начинаем индексацию исходного кода в {{ source_dir }}"
    },
    "stream_out_stats": {
        "en": "Model: {{ model_name }}, Total time: {{ elapsed_time }} seconds, First token time: {{ first_token_time }} seconds, Speed: {{ speed }} tokens/s, Input tokens: {{ input_tokens }}, Output tokens: {{ output_tokens }}, Input cost: {{ input_cost }}, Output cost: {{ output_cost }}",
        "zh": "模型: {{ model_name }},总耗时 {{ elapsed_time }} 秒,首token时间: {{ first_token_time }} 秒, 速度: {{ speed }} tokens/秒, 输入token数: {{ input_tokens }}, 输出token数: {{ output_tokens }}, 输入成本: {{ input_cost }}, 输出成本: {{ output_cost }}",
        "ja": "モデル: {{ model_name }}、総時間: {{ elapsed_time }} 秒、最初のトークン時間: {{ first_token_time }} 秒、速度: {{ speed }} tokens/秒、入力トークン数: {{ input_tokens }}、出力トークン数: {{ output_tokens }}、入力コスト: {{ input_cost }}、出力コスト: {{ output_cost }}",
        "ar": "النموذج: {{ model_name }}، إجمالي الوقت: {{ elapsed_time }} ثانية، وقت أول رمز: {{ first_token_time }} ثانية، السرعة: {{ speed }} رمز/ثانية، رموز الإدخال: {{ input_tokens }}، رموز الإخراج: {{ output_tokens }}، تكلفة الإدخال: {{ input_cost }}، تكلفة الإخراج: {{ output_cost }}",
        "ru": "Модель: {{ model_name }}, Общее время: {{ elapsed_time }} секунд, Время первого токена: {{ first_token_time }} секунд, Скорость: {{ speed }} токенов/с, Входных токенов: {{ input_tokens }}, Выходных токенов: {{ output_tokens }}, Стоимость входа: {{ input_cost }}, Стоимость выхода: {{ output_cost }}"
    },
    "quick_filter_stats": {
        "en": "{{ model_names }} Quick filter completed in {{ elapsed_time }} seconds, input tokens: {{ input_tokens }}, output tokens: {{ output_tokens }}, input cost: {{ input_cost }}, output cost: {{ output_cost }} speed: {{ speed }} tokens/s",
        "zh": "{{ model_names }} Quick Filter 完成耗时 {{ elapsed_time }} 秒，输入token数: {{ input_tokens }}, 输出token数: {{ output_tokens }}, 输入成本: {{ input_cost }}, 输出成本: {{ output_cost }} 速度: {{ speed }} tokens/秒",
        "ja": "{{ model_names }} クイックフィルター完了 {{ elapsed_time }} 秒、入力トークン数: {{ input_tokens }}、出力トークン数: {{ output_tokens }}、入力コスト: {{ input_cost }}、出力コスト: {{ output_cost }} 速度: {{ speed }} tokens/秒",
        "ar": "{{ model_names }} اكتمل التصفية السريعة في {{ elapsed_time }} ثانية، رموز الإدخال: {{ input_tokens }}، رموز الإخراج: {{ output_tokens }}، تكلفة الإدخال: {{ input_cost }}، تكلفة الإخراج: {{ output_cost }} السرعة: {{ speed }} رمز/ثانية",
        "ru": "{{ model_names }} Быстрая фильтрация завершена за {{ elapsed_time }} секунд, входных токенов: {{ input_tokens }}, выходных токенов: {{ output_tokens }}, стоимость входа: {{ input_cost }}, стоимость выхода: {{ output_cost }} скорость: {{ speed }} токенов/с"
    },
    "upsert_file": {
        "en": "✅ Updated file: {{ file_path }}",
        "zh": "✅ 更新文件: {{ file_path }}",
        "ja": "✅ ファイルを更新しました: {{ file_path }}",
        "ar": "✅ تم تحديث الملف: {{ file_path }}",
        "ru": "✅ Обновлен файл: {{ file_path }}"
    },
    "unmerged_blocks_title": {
        "en": "Unmerged Blocks",
        "zh": "未合并代码块",
        "ja": "マージされていないブロック",
        "ar": "الكتل غير المدموجة",
        "ru": "Неслитые блоки"
    },
    "merged_blocks_title": {
        "en": "Merged Changes",
        "zh": "合并的更改",
        "ja": "マージされた変更",
        "ar": "التغييرات المدموجة",
        "ru": "Слитые изменения"
    },
    "quick_filter_title": {
        "en": "{{ model_name }} is analyzing how to filter context...",
        "zh": "{{ model_name }} 正在分析如何筛选上下文...",
        "ja": "{{ model_name }} がコンテキストをフィルタリングする方法を分析中...",
        "ar": "{{ model_name }} يحلل كيفية تصفية السياق...",
        "ru": "{{ model_name }} анализирует как фильтровать контекст..."
    },
    "quick_filter_failed": {
        "en": "❌ Quick filter failed: {{ error }}. ",
        "zh": "❌ 快速过滤器失败: {{ error }}. ",
        "ja": "❌ クイックフィルターが失敗しました: {{ error }}. ",
        "ar": "❌ فشل التصفية السريعة: {{ error }}. ",
        "ru": "❌ Быстрая фильтрация не удалась: {{ error }}. "
    },
    "unmerged_file_path": {
        "en": "File: {{file_path}}",
        "zh": "文件: {{file_path}}",
        "ja": "ファイル: {{file_path}}",
        "ar": "الملف: {{file_path}}",
        "ru": "Файл: {{file_path}}"
    },
    "unmerged_search_block": {
        "en": "Search Block({{similarity}}):",
        "zh": "Search Block({{similarity}}):",
        "ja": "検索ブロック({{similarity}}):",
        "ar": "كتلة البحث({{similarity}}):",
        "ru": "Блок поиска({{similarity}}):"
    },
    "unmerged_replace_block": {
        "en": "Replace Block:",
        "zh": "Replace Block:",
        "ja": "置換ブロック:",
        "ar": "كتلة الاستبدال:",
        "ru": "Блок замены:"
    },
    "unmerged_blocks_total": {
        "en": "Total unmerged blocks: {{num_blocks}}",
        "zh": "未合并代码块数量: {{num_blocks}}",
        "ja": "マージされていないブロック総数: {{num_blocks}}",
        "ar": "إجمالي الكتل غير المدموجة: {{num_blocks}}",
        "ru": "Общее количество неслитых блоков: {{num_blocks}}"
    },
    "git_init_required": {
        "en": "⚠️ auto_merge only applies to git repositories.\n\nPlease try using git init in the source directory:\n\n```shell\ncd {{ source_dir }}\ngit init.\n```\n\nThen run auto - coder again.\nError: {{ error }}",
        "zh": "⚠️ auto_merge 仅适用于 git 仓库。\n\n请尝试在源目录中使用 git init:\n\n```shell\ncd {{ source_dir }}\ngit init.\n```\n\n然后再次运行 auto-coder。\n错误: {{ error }}",
        "ja": "⚠️ auto_merge は git リポジトリにのみ適用されます。\n\nソースディレクトリで git init を試してください:\n\n```shell\ncd {{ source_dir }}\ngit init.\n```\n\nその後、auto-coder を再実行してください。\nエラー: {{ error }}",
        "ar": "⚠️ auto_merge ينطبق فقط على مستودعات git.\n\nيرجى محاولة استخدام git init في مجلد المصدر:\n\n```shell\ncd {{ source_dir }}\ngit init.\n```\n\nثم قم بتشغيل auto-coder مرة أخرى.\nخطأ: {{ error }}",
        "ru": "⚠️ auto_merge применяется только к git репозиториям.\n\nПожалуйста, попробуйте использовать git init в исходной директории:\n\n```shell\ncd {{ source_dir }}\ngit init.\n```\n\nЗатем запустите auto-coder снова.\nОшибка: {{ error }}"
    },
    "quick_filter_reason": {
        "en": "Auto get(quick_filter mode)",
        "zh": "自动获取(quick_filter模式)",
        "ja": "自動取得(quick_filterモード)",
        "ar": "الحصول التلقائي(وضع quick_filter)",
        "ru": "Автоматическое получение(режим quick_filter)"
    },
    "quick_filter_too_long": {
        "en": "⚠️ index file is too large ({{ tokens_len }}/{{ max_tokens }}). The query will be split into {{ split_size }} chunks.",
        "zh": "⚠️ 索引文件过大 ({{ tokens_len }}/{{ max_tokens }})。查询将被分成 {{ split_size }} 个部分执行。",
        "ja": "⚠️ インデックスファイルが大きすぎます ({{ tokens_len }}/{{ max_tokens }})。クエリは {{ split_size }} 個のチャンクに分割されます。",
        "ar": "⚠️ ملف الفهرس كبير جداً ({{ tokens_len }}/{{ max_tokens }})。سيتم تقسيم الاستعلام إلى {{ split_size }} أجزاء.",
        "ru": "⚠️ Индексный файл слишком большой ({{ tokens_len }}/{{ max_tokens }}). Запрос будет разделен на {{ split_size }} частей."
    },
    "quick_filter_tokens_len": {
        "en": "📊 Current index size: {{ tokens_len }} tokens",
        "zh": "📊 当前索引大小: {{ tokens_len }} tokens",
        "ja": "📊 現在のインデックスサイズ: {{ tokens_len }} トークン",
        "ar": "📊 حجم الفهرس الحالي: {{ tokens_len }} رمز",
        "ru": "📊 Текущий размер индекса: {{ tokens_len }} токенов"
    },
    "estimated_chat_input_tokens": {
        "en": "Estimated chat input tokens: {{ estimated_input_tokens }}",
        "zh": "对话输入token预估为: {{ estimated_input_tokens }}",
        "ja": "推定チャット入力トークン数: {{ estimated_input_tokens }}",
        "ar": "رموز إدخال المحادثة المقدرة: {{ estimated_input_tokens }}",
        "ru": "Ожидаемое количество входных токенов чата: {{ estimated_input_tokens }}"
    },
    "estimated_input_tokens_in_generate": {
        "en": "Estimated input tokens in generate ({{ generate_mode }}): {{ estimated_input_tokens_in_generate }}",
        "zh": "生成代码({{ generate_mode }})预计输入token数: {{ estimated_input_tokens_in_generate }}",
        "ja": "生成時の推定入力トークン数 ({{ generate_mode }}): {{ estimated_input_tokens_in_generate }}",
        "ar": "رموز الإدخال المقدرة في التوليد ({{ generate_mode }}): {{ estimated_input_tokens_in_generate }}",
        "ru": "Ожидаемое количество входных токенов при генерации ({{ generate_mode }}): {{ estimated_input_tokens_in_generate }}"
    },
    "model_has_access_restrictions": {
        "en": "{{model_name}} has access restrictions, cannot use the current function",
        "zh": "{{model_name}} 有访问限制，无法使用当前功能",
        "ja": "{{model_name}} にはアクセス制限があり、現在の機能を使用できません",
        "ar": "{{model_name}} لديه قيود الوصول، لا يمكن استخدام الوظيفة الحالية",
        "ru": "{{model_name}} имеет ограничения доступа, невозможно использовать текущую функцию"
    },
    "auto_command_not_found": {
        "en": "Auto command not found: {{command}}. Please check your input and try again.",
        "zh": "未找到自动命令: {{command}}。请检查您的输入并重试。",
        "ja": "自動コマンドが見つかりません: {{command}}。入力を確認して再試行してください。",
        "ar": "لم يتم العثور على الأمر التلقائي: {{command}}. يرجى التحقق من إدخالك والمحاولة مرة أخرى.",
        "ru": "Автоматическая команда не найдена: {{command}}. Пожалуйста, проверьте ваш ввод и попробуйте снова."
    },
    "auto_command_failed": {
        "en": "Auto command failed: {{error}}. Please check your input and try again.",
        "zh": "自动命令执行失败: {{error}}。请检查您的输入并重试。",
        "ja": "自動コマンドが失敗しました: {{error}}。入力を確認して再試行してください。",
        "ar": "فشل الأمر التلقائي: {{error}}. يرجى التحقق من إدخالك والمحاولة مرة أخرى.",
        "ru": "Автоматическая команда не удалась: {{error}}. Пожалуйста, проверьте ваш ввод и попробуйте снова."
    },
    "command_execution_result": {
        "en": "{{action}} execution result",
        "zh": "{{action}} 执行结果",
        "ja": "{{action}} 実行結果",
        "ar": "نتيجة تنفيذ {{action}}",
        "ru": "Результат выполнения {{action}}"
    },
    "satisfied_prompt": {
        "en": "Requirements satisfied, no further action needed",
        "zh": "已满足需求，无需进一步操作",
        "ja": "要件が満たされました、さらなるアクションは不要です",
        "ar": "تم تلبية المتطلبات، لا حاجة لإجراء إضافي",
        "ru": "Требования выполнены, дополнительных действий не требуется"
    },
    "auto_command_analyzed": {
        "en": "Selected command",
        "zh": "被选择指令",
        "ja": "選択されたコマンド",
        "ar": "الأمر المحدد",
        "ru": "Выбранная команда"
    },
    "invalid_enum_value": {
        "en": "Value '{{value}}' is not in allowed values ({{allowed}})",
        "zh": "值 '{{value}}' 不在允许的值列表中 ({{allowed}})",
        "ja": "値 '{{value}}' は許可された値 ({{allowed}}) にありません",
        "ar": "القيمة '{{value}}' ليست في القيم المسموحة ({{allowed}})",
        "ru": "Значение '{{value}}' не входит в разрешенные значения ({{allowed}})"
    },
    "conversation_pruning_start": {
        "en": "⚠️ Conversation pruning started, total tokens: {{total_tokens}}, safe zone: {{safe_zone}}",
        "zh": "⚠️ 对话长度 {{total_tokens}} tokens 超过安全阈值 {{safe_zone}}，开始修剪对话。",
        "ja": "⚠️ 会話の剪定を開始しました、総トークン数: {{total_tokens}}、安全ゾーン: {{safe_zone}}",
        "ar": "⚠️ بدأت عملية تقليم المحادثة، إجمالي الرموز: {{total_tokens}}، المنطقة الآمنة: {{safe_zone}}",
        "ru": "⚠️ Начата обрезка разговора, общее количество токенов: {{total_tokens}}, безопасная зона: {{safe_zone}}"
    },
    "invalid_file_number": {
        "en": "⚠️ Invalid file number {{file_number}}, total files: {{total_files}}",
        "zh": "⚠️ 无效的文件编号 {{file_number}}，总文件数为 {{total_files}}",
        "ja": "⚠️ 無効なファイル番号 {{file_number}}、総ファイル数: {{total_files}}",
        "ar": "⚠️ رقم الملف غير صحيح {{file_number}}، إجمالي الملفات: {{total_files}}",
        "ru": "⚠️ Неверный номер файла {{file_number}}, общее количество файлов: {{total_files}}"
    },
    "all_merge_results_failed": {
        "en": "⚠️ All merge attempts failed, returning first candidate",
        "zh": "⚠️ 所有合并尝试都失败，返回第一个候选",
        "ja": "⚠️ すべてのマージ試行が失敗しました、最初の候補を返します",
        "ar": "⚠️ فشلت جميع محاولات الدمج، إرجاع المرشح الأول",
        "ru": "⚠️ Все попытки слияния не удались, возвращаем первого кандидата"
    },
    "only_one_merge_result_success": {
        "en": "✅ Only one merge result succeeded, returning that candidate",
        "zh": "✅ 只有一个合并结果成功，返回该候选",
        "ja": "✅ 1つのマージ結果のみが成功しました、その候補を返します",
        "ar": "✅ نجح نتيجة دمج واحدة فقط، إرجاع ذلك المرشح",
        "ru": "✅ Только один результат слияния был успешным, возвращаем этого кандидата"
    },
    "conf_import_success": {
        "en": "Successfully imported configuration: {{path}}",
        "zh": "成功导入配置: {{path}}",
        "ja": "設定のインポートが成功しました: {{path}}",
        "ar": "تم استيراد التكوين بنجاح: {{path}}",
        "ru": "Конфигурация успешно импортирована: {{path}}"
    },
    "conf_export_success": {
        "en": "Successfully exported configuration: {{path}}",
        "zh": "成功导出配置: {{path}}",
        "ja": "設定のエクスポートが成功しました: {{path}}",
        "ar": "تم تصدير التكوين بنجاح: {{path}}",
        "ru": "Конфигурация успешно экспортирована: {{path}}"
    },
    "conf_import_error": {
        "en": "Error importing configuration: {{error}}",
        "zh": "导入配置出错: {{error}}",
        "ja": "設定のインポートエラー: {{error}}",
        "ar": "خطأ في استيراد التكوين: {{error}}",
        "ru": "Ошибка импорта конфигурации: {{error}}"
    },
    "conf_export_error": {
        "en": "Error exporting configuration: {{error}}",
        "zh": "导出配置出错: {{error}}",
        "ja": "設定のエクスポートエラー: {{error}}",
        "ar": "خطأ في تصدير التكوين: {{error}}",
        "ru": "Ошибка экспорта конфигурации: {{error}}"
    },
    "conf_import_invalid_format": {
        "en": "Invalid import configuration format, expected 'key:value'",
        "zh": "导入配置格式无效, 应为 'key:value' 格式",
        "ja": "無効なインポート設定形式です、'key:value'形式が期待されます",
        "ar": "تنسيق تكوين الاستيراد غير صحيح، متوقع 'key:value'",
        "ru": "Неверный формат импорта конфигурации, ожидается 'key:value'"
    },
    "conf_export_invalid_format": {
        "en": "Invalid export configuration format, expected 'key:value'",
        "zh": "导出配置格式无效, 应为 'key:value' 格式",
        "ja": "無効なエクスポート設定形式です、'key:value'形式が期待されます",
        "ar": "تنسيق تكوين التصدير غير صحيح، متوقع 'key:value'",
        "ru": "Неверный формат экспорта конфигурации, ожидается 'key:value'"
    },
    "conf_import_file_not_found": {
        "en": "Import configuration file not found: {{file_path}}",
        "zh": "未找到导入配置文件: {{file_path}}",
        "ja": "インポート設定ファイルが見つかりません: {{file_path}}",
        "ar": "لم يتم العثور على ملف تكوين الاستيراد: {{file_path}}",
        "ru": "Файл импорта конфигурации не найден: {{file_path}}"
    },
    "conf_export_file_not_found": {
        "en": "Export configuration file not found: {{file_path}}",
        "zh": "未找到导出配置文件: {{file_path}}",
        "ja": "エクスポート設定ファイルが見つかりません: {{file_path}}",
        "ar": "لم يتم العثور على ملف تكوين التصدير: {{file_path}}",
        "ru": "Файл экспорта конфигурации не найден: {{file_path}}"
    },
    "conf_import_file_empty": {
        "en": "Import configuration file is empty: {{file_path}}",
        "zh": "导入配置文件为空: {{file_path}}",
        "ja": "インポート設定ファイルが空です: {{file_path}}",
        "ar": "ملف تكوين الاستيراد فارغ: {{file_path}}",
        "ru": "Файл импорта конфигурации пуст: {{file_path}}"
    },
    "conf_export_file_empty": {
        "en": "Export configuration file is empty: {{file_path}}",
        "zh": "导出配置文件为空: {{file_path}}",
        "ja": "エクスポート設定ファイルが空です: {{file_path}}",
        "ar": "ملف تكوين التصدير فارغ: {{file_path}}",
        "ru": "Файл экспорта конфигурации пуст: {{file_path}}"
    },
    "generated_shell_script": {
        "en": "Generated Shell Script",
        "zh": "生成的 Shell 脚本",
        "ja": "生成されたシェルスクリプト",
        "ar": "نص الشل المولد",
        "ru": "Сгенерированный Shell скрипт"
    },
    "confirm_execute_shell_script": {
        "en": "Do you want to execute this shell script?",
        "zh": "您要执行此 shell 脚本吗？",
        "ja": "このシェルスクリプトを実行しますか？",
        "ar": "هل تريد تنفيذ نص الشل هذا؟",
        "ru": "Хотите ли вы выполнить этот shell скрипт?"
    },
    "shell_script_not_executed": {
        "en": "Shell script was not executed",
        "zh": "Shell 脚本未执行",
        "ja": "シェルスクリプトは実行されませんでした",
        "ar": "لم يتم تنفيذ نص الشل",
        "ru": "Shell скрипт не был выполнен"
    },
    "index_export_success": {
        "en": "Index exported successfully: {{path}}",
        "zh": "索引导出成功: {{path}}",
        "ja": "インデックスのエクスポートが成功しました: {{path}}",
        "ar": "تم تصدير الفهرس بنجاح: {{path}}",
        "ru": "Индекс успешно экспортирован: {{path}}"
    },
    "index_import_success": {
        "en": "Index imported successfully: {{path}}",
        "zh": "索引导入成功: {{path}}",
        "ja": "インデックスのインポートが成功しました: {{path}}",
        "ar": "تم استيراد الفهرس بنجاح: {{path}}",
        "ru": "Индекс успешно импортирован: {{path}}"
    },
    "edits_title": {
        "en": "edits",
        "zh": "编辑块",
        "ja": "編集",
        "ar": "التعديلات",
        "ru": "редактирования"
    },
    "diff_blocks_title": {
        "en": "diff blocks",
        "zh": "差异块",
        "ja": "差分ブロック",
        "ar": "كتل الاختلاف",
        "ru": "блоки различий"
    },
    "index_exclude_files_error": {
        "en": "index filter exclude files fail: {{ error }}",
        "zh": "索引排除文件时出错: {{error}}",
        "ja": "インデックスフィルターでファイル除外に失敗: {{ error }}",
        "ar": "فشل في استبعاد الملفات من مرشح الفهرس: {{ error }}",
        "ru": "Ошибка исключения файлов индексного фильтра: {{ error }}"
    },
    "file_sliding_window_processing": {
        "en": "File {{ file_path }} is too large ({{ tokens }} tokens), processing with sliding window...",
        "zh": "文件 {{ file_path }} 过大 ({{ tokens }} tokens)，正在使用滑动窗口处理...",
        "ja": "ファイル {{ file_path }} が大きすぎます ({{ tokens }} トークン)、スライディングウィンドウで処理中...",
        "ar": "الملف {{ file_path }} كبير جداً ({{ tokens }} رمز)، معالجة بنافذة منزلقة...",
        "ru": "Файл {{ file_path }} слишком большой ({{ tokens }} токенов), обработка с использованием скользящего окна..."
    },
    "file_snippet_processing": {
        "en": "Processing file {{ file_path }} with code snippet extraction...",
        "zh": "正在对文件 {{ file_path }} 进行代码片段提取...",
        "ja": "ファイル {{ file_path }} のコードスニペット抽出を処理中...",
        "ar": "معالجة الملف {{ file_path }} مع استخراج مقتطفات الكود...",
        "ru": "Обработка файла {{ file_path }} с извлечением фрагментов кода..."
    },
    "context_pruning_start": {
        "en": "⚠️ Context pruning started. Total tokens: {{ total_tokens }} (max allowed: {{ max_tokens }}). Applying strategy: {{ strategy }}.",
        "zh": "⚠️ 开始上下文剪枝。总token数: {{ total_tokens }} (最大允许: {{ max_tokens }})。正在应用策略: {{ strategy }}。",
        "ja": "⚠️ コンテキストの剪定を開始しました。総トークン数: {{ total_tokens }} (最大許可: {{ max_tokens }})。戦略を適用中: {{ strategy }}。",
        "ar": "⚠️ بدأت عملية تقليم السياق. إجمالي الرموز: {{ total_tokens }} (الحد الأقصى المسموح: {{ max_tokens }})。تطبيق الاستراتيجية: {{ strategy }}。",
        "ru": "⚠️ Начата обрезка контекста. Общее количество токенов: {{ total_tokens }} (максимально разрешено: {{ max_tokens }}). Применяется стратегия: {{ strategy }}."
    },
    "context_pruning_reason": {
        "en": "Context length exceeds maximum limit ({{ total_tokens }} > {{ max_tokens }}). Pruning is required to fit within the model's context window.",
        "zh": "上下文长度超过最大限制 ({{ total_tokens }} > {{ max_tokens }})。需要进行剪枝以适配模型的上下文窗口。",
        "ja": "コンテキスト長が最大制限を超えています ({{ total_tokens }} > {{ max_tokens }})。モデルのコンテキストウィンドウに収めるために剪定が必要です。",
        "ar": "طول السياق يتجاوز الحد الأقصى ({{ total_tokens }} > {{ max_tokens }})。التقليم مطلوب للتناسب مع نافذة سياق النموذج。",
        "ru": "Длина контекста превышает максимальный лимит ({{ total_tokens }} > {{ max_tokens }}). Требуется обрезка для размещения в контекстном окне модели."
    },
    "rank_code_modification_title": {
        "en": "{{model_name}} ranking codes",
        "zh": "模型{{model_name}}对代码打分",
        "ja": "{{model_name}} コードランキング",
        "ar": "{{model_name}} ترتيب الأكواد",
        "ru": "{{model_name}} ранжирование кода"
    },
    "sorted_files_message": {
        "en": "Reordered files:\n{% for file in files %}- {{ file }}\n{% endfor %}",
        "zh": "重新排序后的文件路径:\n{% for file in files %}- {{ file }}\n{% endfor %}",
        "ja": "並び替えられたファイル:\n{% for file in files %}- {{ file }}\n{% endfor %}",
        "ar": "الملفات المعاد ترتيبها:\n{% for file in files %}- {{ file }}\n{% endfor %}",
        "ru": "Переупорядоченные файлы:\n{% for file in files %}- {{ file }}\n{% endfor %}"
    },
    "estimated_input_tokens_in_ranking": {
        "en": "estimate input token {{ estimated_input_tokens }} when ranking",
        "zh": "排序预计输入token数: {{ estimated_input_tokens }}",
        "ja": "ランキング時の推定入力トークン数: {{ estimated_input_tokens }}",
        "ar": "تقدير رموز الإدخال {{ estimated_input_tokens }} عند الترتيب",
        "ru": "Ожидаемое количество входных токенов при ранжировании: {{ estimated_input_tokens }}"
    },
    "file_snippet_procesed": {
        "en": "{{ file_path }} processed with tokens: {{ tokens }} => {{ snippet_tokens }}. Current total tokens: {{ total_tokens }}",
        "zh": "文件 {{ file_path }} 处理后token数: {{ tokens }} => {{ snippet_tokens }} 当前总token数: {{ total_tokens }}",
        "ja": "{{ file_path }} 処理済みトークン数: {{ tokens }} => {{ snippet_tokens }} 現在の総トークン数: {{ total_tokens }}",
        "ar": "{{ file_path }} معالج برموز: {{ tokens }} => {{ snippet_tokens }} إجمالي الرموز الحالي: {{ total_tokens }}",
        "ru": "{{ file_path }} обработан с токенами: {{ tokens }} => {{ snippet_tokens }} Текущее общее количество токенов: {{ total_tokens }}"
    },
    "tool_ask_user": {
        "en": "Your Reply: ",
        "zh": "您的回复: ",
        "ja": "あなたの返信: ",
        "ar": "ردك: ",
        "ru": "Ваш ответ: "
    },
    "tool_ask_user_accept": {
        "en": "Your Response received",
        "zh": "收到您的回复",
        "ja": "あなたの回答を受信しました",
        "ar": "تم استلام ردك",
        "ru": "Ваш ответ получен"
    },
    "auto_web_analyzing": {
        "en": "Analyzing web automation task...",
        "zh": "正在分析网页自动化任务...",
        "ja": "ウェブ自動化タスクを分析中...",
        "ar": "تحليل مهمة أتمتة الويب...",
        "ru": "Анализ задачи веб-автоматизации..."
    },
    "auto_web_analyzed": {
        "en": "Web automation task analysis completed",
        "zh": "网页自动化任务分析完成",
        "ja": "ウェブ自動化タスクの分析が完了しました",
        "ar": "اكتمل تحليل مهمة أتمتة الويب",
        "ru": "Анализ задачи веб-автоматизации завершен"
    },
    "executing_web_action": {
        "en": "Executing action: {{action}} - {{description}}",
        "zh": "执行操作: {{action}} - {{description}}",
        "ja": "アクションを実行中: {{action}} - {{description}}",
        "ar": "تنفيذ الإجراء: {{action}} - {{description}}",
        "ru": "Выполнение действия: {{action}} - {{description}}"
    },
    "executing_step": {
        "en": "Executing step {{step}}: {{description}}",
        "zh": "执行步骤 {{step}}: {{description}}",
        "ja": "ステップ {{step}} を実行中: {{description}}",
        "ar": "تنفيذ الخطوة {{step}}: {{description}}",
        "ru": "Выполнение шага {{step}}: {{description}}"
    },
    "operation_cancelled": {
        "en": "Operation cancelled",
        "zh": "操作已取消",
        "ja": "操作がキャンセルされました",
        "ar": "تم إلغاء العملية",
        "ru": "Операция отменена"
    },
    "element_not_found": {
        "en": "Element not found: {{element}}",
        "zh": "未找到元素: {{element}}",
        "ja": "要素が見つかりません: {{element}}",
        "ar": "لم يتم العثور على العنصر: {{element}}",
        "ru": "Элемент не найден: {{element}}"
    },
    "analyzing_results": {
        "en": "Analyzing execution results...",
        "zh": "分析执行结果...",
        "ja": "実行結果を分析中...",
        "ar": "تحليل نتائج التنفيذ...",
        "ru": "Анализ результатов выполнения..."
    },
    "next_steps_determined": {
        "en": "Next steps determined",
        "zh": "已确定下一步操作",
        "ja": "次のステップが決定されました",
        "ar": "تم تحديد الخطوات التالية",
        "ru": "Следующие шаги определены"
    },
    "max_iterations_reached": {
        "en": "Max iterations reached ({max_iterations})",
        "zh": "已达到最大迭代次数 {{max_iterations}}",
        "ja": "最大反復回数に達しました ({{max_iterations}})",
        "ar": "تم الوصول إلى أقصى عدد تكرارات ({{max_iterations}})",
        "ru": "Достигнуто максимальное количество итераций ({{max_iterations}})"
    },
    "action_verification_failed": {
        "en": "Action verification failed: {{action}} - {{reason}}",
        "zh": "操作验证失败: {{action}} - {{reason}}",
        "ja": "アクションの検証に失敗しました: {{action}} - {{reason}}",
        "ar": "فشل التحقق من الإجراء: {{action}} - {{reason}}",
        "ru": "Проверка действия не удалась: {{action}} - {{reason}}"
    },
    "action_succeeded": {
        "en": "Action succeeded: {{action}}",
        "zh": "操作成功: {{action}}",
        "ja": "アクションが成功しました: {{action}}",
        "ar": "نجح الإجراء: {{action}}",
        "ru": "Действие выполнено успешно: {{action}}"
    },
    "replanned_actions": {
        "en": "Replanned {{count}} actions",
        "zh": "已重新规划 {{count}} 个操作",
        "ja": "{{count}} 個のアクションを再計画しました",
        "ar": "تم إعادة التخطيط لـ {{count}} إجراءات",
        "ru": "Перепланировано {{count}} действий"
    },
    "web_automation_ask_user": {
        "en": "Your answer: ",
        "zh": "您的回答: ",
        "ja": "あなたの回答: ",
        "ar": "إجابتك: ",
        "ru": "Ваш ответ: "
    },
    "filter_mode_normal": {
        "en": "Using normal filter mode for index processing...",
        "zh": "正在使用普通过滤模式处理索引...",
        "ja": "インデックス処理に通常フィルターモードを使用中...",
        "ar": "استخدام وضع التصفية العادي لمعالجة الفهرس...",
        "ru": "Использование обычного режима фильтрации для обработки индекса..."
    },
    "filter_mode_big": {
        "en": "Index file is large ({{ tokens_len }} tokens), using big_filter mode for processing...",
        "zh": "索引文件较大 ({{ tokens_len }} tokens)，正在使用 big_filter 模式处理...",
        "ja": "インデックスファイルが大きいです ({{ tokens_len }} トークン)、big_filter モードで処理中...",
        "ar": "ملف الفهرس كبير ({{ tokens_len }} رمز)، استخدام وضع big_filter للمعالجة...",
        "ru": "Индексный файл большой ({{ tokens_len }} токенов), используется режим big_filter для обработки..."
    },
    "filter_mode_super_big": {
        "en": "Index file is very large ({{ tokens_len }} tokens), using super_big_filter mode for processing...",
        "zh": "索引文件非常大 ({{ tokens_len }} tokens)，正在使用 super_big_filter 模式处理...",
        "ja": "インデックスファイルが非常に大きいです ({{ tokens_len }} トークン)、super_big_filter モードで処理中...",
        "ar": "ملف الفهرس كبير جداً ({{ tokens_len }} رمز)، استخدام وضع super_big_filter للمعالجة...",
        "ru": "Индексный файл очень большой ({{ tokens_len }} токенов), используется режим super_big_filter для обработки..."
    },
    "super_big_filter_failed": {
        "en": "❌ Super big filter failed: {{ error }}.",
        "zh": "❌ 超大过滤器失败: {{ error }}.",
        "ja": "❌ スーパー大容量フィルターが失敗しました: {{ error }}.",
        "ar": "❌ فشل المرشح الفائق الكبر: {{ error }}.",
        "ru": "❌ Сверхбольшой фильтр не удался: {{ error }}."
    },
    "super_big_filter_stats": {
        "en": "{{ model_names }} Super big filter completed in {{ elapsed_time }} seconds, input tokens: {{ input_tokens }}, output tokens: {{ output_tokens }}, input cost: {{ input_cost }}, output cost: {{ output_cost }}, speed: {{ speed }} tokens/s, chunk_index: {{ chunk_index }}",
        "zh": "{{ model_names }} 超大过滤器完成耗时 {{ elapsed_time }} 秒，输入token数: {{ input_tokens }}, 输出token数: {{ output_tokens }}, 输入成本: {{ input_cost }}, 输出成本: {{ output_cost }}, 速度: {{ speed }} tokens/秒, 块索引: {{ chunk_index }}",
        "ja": "{{ model_names }} スーパー大容量フィルター完了 {{ elapsed_time }} 秒、入力トークン数: {{ input_tokens }}、出力トークン数: {{ output_tokens }}、入力コスト: {{ input_cost }}、出力コスト: {{ output_cost }}、速度: {{ speed }} tokens/秒、チャンクインデックス: {{ chunk_index }}",
        "ar": "{{ model_names }} اكتمل المرشح الفائق الكبر في {{ elapsed_time }} ثانية، رموز الإدخال: {{ input_tokens }}، رموز الإخراج: {{ output_tokens }}، تكلفة الإدخال: {{ input_cost }}، تكلفة الإخراج: {{ output_cost }}، السرعة: {{ speed }} رمز/ثانية، فهرس الجزء: {{ chunk_index }}",
        "ru": "{{ model_names }} Сверхбольшой фильтр завершен за {{ elapsed_time }} секунд, входных токенов: {{ input_tokens }}, выходных токенов: {{ output_tokens }}, стоимость входа: {{ input_cost }}, стоимость выхода: {{ output_cost }}, скорость: {{ speed }} токенов/с, индекс части: {{ chunk_index }}"
    },
    "super_big_filter_splitting": {
        "en": "⚠️ Index file is extremely large ({{ tokens_len }}/{{ max_tokens }}). The query will be split into {{ split_size }} chunks for processing.",
        "zh": "⚠️ 索引文件极其庞大 ({{ tokens_len }}/{{ max_tokens }})。查询将被分成 {{ split_size }} 个部分进行处理。",
        "ja": "⚠️ インデックスファイルが極めて大きいです ({{ tokens_len }}/{{ max_tokens }})。クエリは処理のために {{ split_size }} 個のチャンクに分割されます。",
        "ar": "⚠️ ملف الفهرس كبير بشكل استثنائي ({{ tokens_len }}/{{ max_tokens }})。سيتم تقسيم الاستعلام إلى {{ split_size }} أجزاء للمعالجة。",
        "ru": "⚠️ Индексный файл чрезвычайно большой ({{ tokens_len }}/{{ max_tokens }}). Запрос будет разделен на {{ split_size }} частей для обработки."
    },
    "super_big_filter_title": {
        "en": "{{ model_name }} is analyzing how to filter extremely large context...",
        "zh": "{{ model_name }} 正在分析如何过滤极大规模上下文...",
        "ja": "{{ model_name }} が極めて大きなコンテキストをフィルタリングする方法を分析中...",
        "ar": "{{ model_name }} يحلل كيفية تصفية السياق الكبير للغاية...",
        "ru": "{{ model_name }} анализирует как фильтровать чрезвычайно большой контекст..."
    },
    "mcp_server_info_error": {
        "en": "Error getting MCP server info: {{ error }}",
        "zh": "获取MCP服务器信息时出错: {{ error }}",
        "ja": "MCPサーバー情報の取得エラー: {{ error }}",
        "ar": "خطأ في الحصول على معلومات خادم MCP: {{ error }}",
        "ru": "Ошибка получения информации о MCP сервере: {{ error }}"
    },
    "mcp_server_info_title": {
        "en": "Connected MCP Server Info",
        "zh": "已连接的MCP服务器信息",
        "ja": "接続されたMCPサーバー情報",
        "ar": "معلومات خادم MCP المتصل",
        "ru": "Информация о подключенном MCP сервере"
    },
    "no_commit_file_name": {
        "en": "Cannot get the file name of the commit_id in the actions directory: {{commit_id}}",
        "zh": "无法获取commit_id关联的actions 目录下的文件名: {{commit_id}}",
        "ja": "actionsディレクトリ内のcommit_idのファイル名を取得できません: {{commit_id}}",
        "ar": "لا يمكن الحصول على اسم الملف للcommit_id في مجلد الإجراءات: {{commit_id}}",
        "ru": "Невозможно получить имя файла commit_id в директории actions: {{commit_id}}"
    },
    "yaml_update_success": {
        "en": "✅ Successfully updated YAML file: {{yaml_file}}",
        "zh": "✅ 成功更新YAML文件: {{yaml_file}}",
        "ja": "✅ YAMLファイルの更新が成功しました: {{yaml_file}}",
        "ar": "✅ تم تحديث ملف YAML بنجاح: {{yaml_file}}",
        "ru": "✅ YAML файл успешно обновлен: {{yaml_file}}"
    },
    "yaml_save_error": {
        "en": "❌ Error saving YAML file {{yaml_file}}: {{error}}",
        "zh": "❌ 保存YAML文件出错 {{yaml_file}}: {{error}}",
        "ja": "❌ YAMLファイル {{yaml_file}} の保存エラー: {{error}}",
        "ar": "❌ خطأ في حفظ ملف YAML {{yaml_file}}: {{error}}",
        "ru": "❌ Ошибка сохранения YAML файла {{yaml_file}}: {{error}}"
    },
    "active_context_background_task": {
        "en": "🔄 Active context generation started in background (task ID: {{task_id}})",
        "zh": "🔄 正在后台生成活动上下文 (任务ID: {{task_id}})",
        "ja": "🔄 アクティブコンテキストの生成をバックグラウンドで開始しました (タスクID: {{task_id}})",
        "ar": "🔄 بدأ توليد السياق النشط في الخلفية (معرف المهمة: {{task_id}})",
        "ru": "🔄 Генерация активного контекста запущена в фоне (ID задачи: {{task_id}})"
    },
    "conf_not_found": {
        "en": "Configuration not found: {{path}}",
        "zh": "未找到配置文件: {{path}}",
        "ja": "設定が見つかりません: {{path}}",
        "ar": "لم يتم العثور على التكوين: {{path}}",
        "ru": "Конфигурация не найдена: {{path}}"
    },
    "code_generate_title": {
        "en": "{{model_name}} is generating code",
        "zh": "{{model_name}}正在生成代码",
        "ja": "{{model_name}}がコードを生成中",
        "ar": "{{model_name}} يولد الكود",
        "ru": "{{model_name}} генерирует код"
    },
    "generating_initial_code": {
        "en": "Generating initial code...",
        "zh": "正在生成初始代码...",
        "ja": "初期コードを生成中...",
        "ar": "توليد الكود الأولي...",
        "ru": "Генерация начального кода..."
    },
    "generation_failed": {
        "en": "Code generation failed",
        "zh": "代码生成失败",
        "ja": "コード生成が失敗しました",
        "ar": "فشل توليد الكود",
        "ru": "Генерация кода не удалась"
    },
    "no_files_to_lint": {
        "en": "No files to lint",
        "zh": "没有需要检查的文件",
        "ja": "Lintするファイルがありません",
        "ar": "لا توجد ملفات للفحص",
        "ru": "Нет файлов для проверки"
    },
    "no_lint_errors_found": {
        "en": "No lint errors found",
        "zh": "未发现代码质量问题",
        "ja": "Lintエラーは見つかりませんでした",
        "ar": "لم يتم العثور على أخطاء فحص الكود",
        "ru": "Ошибки линтинга не найдены"
    },
    "lint_attempt_status": {
        "en": "Lint attempt {{attempt}}/{{max_correction_attempts}}: {{error_count}} errors found. {{ formatted_issues }}",
        "zh": "代码质量检查尝试 {{attempt}}/{{max_correction_attempts}}: 发现 {{error_count}} 个错误. {{ formatted_issues }}",
        "ja": "Lint試行 {{attempt}}/{{max_correction_attempts}}: {{error_count}} 個のエラーが見つかりました. {{ formatted_issues }}",
        "ar": "محاولة فحص الكود {{attempt}}/{{max_correction_attempts}}: تم العثور على {{error_count}} أخطاء. {{ formatted_issues }}",
        "ru": "Попытка линтинга {{attempt}}/{{max_correction_attempts}}: найдено {{error_count}} ошибок. {{ formatted_issues }}"
    },
    "max_attempts_reached": {
        "en": "Maximum correction attempts reached",
        "zh": "已达到最大修复尝试次数",
        "ja": "最大修正試行回数に達しました",
        "ar": "تم الوصول إلى أقصى عدد محاولات التصحيح",
        "ru": "Достигнуто максимальное количество попыток исправления"
    },
    "compile_success": {
        "en": "Compile success",
        "zh": "编译成功",
        "ja": "コンパイル成功",
        "ar": "نجح التجميع",
        "ru": "Компиляция успешна"
    },
    "compile_failed": {
        "en": "Compile failed",
        "zh": "编译失败",
        "ja": "コンパイル失敗",
        "ar": "فشل التجميع",
        "ru": "Компиляция не удалась"
    },
    "compile_attempt_status": {
        "en": "Compile attempt {{attempt}}/{{max_correction_attempts}}: {{error_count}} errors found. {{ formatted_issues }}",
        "zh": "编译尝试 {{attempt}}/{{max_correction_attempts}}: 发现 {{error_count}} 个错误. {{ formatted_issues }}",
        "ja": "コンパイル試行 {{attempt}}/{{max_correction_attempts}}: {{error_count}} 個のエラーが見つかりました. {{ formatted_issues }}",
        "ar": "محاولة التجميع {{attempt}}/{{max_correction_attempts}}: تم العثور على {{error_count}} أخطاء. {{ formatted_issues }}",
        "ru": "Попытка компиляции {{attempt}}/{{max_correction_attempts}}: найдено {{error_count}} ошибок. {{ formatted_issues }}"
    },
    "max_compile_attempts_reached": {
        "en": "Maximum compilation attempts reached",
        "zh": "已达到最大编译尝试次数",
        "ja": "最大コンパイル試行回数に達しました",
        "ar": "تم الوصول إلى أقصى عدد محاولات التجميع",
        "ru": "Достигнуто максимальное количество попыток компиляции"
    },
    "unmerged_blocks_fixed": {
        "en": "Unmerged blocks fixed successfully",
        "zh": "未合并代码块已成功修复",
        "ja": "マージされていないブロックが正常に修正されました",
        "ar": "تم إصلاح الكتل غير المدموجة بنجاح",
        "ru": "Неслитые блоки успешно исправлены"
    },
    "unmerged_blocks_attempt_status": {
        "en": "Fixing unmerged blocks attempt {{attempt}}/{{max_correction_attempts}}",
        "zh": "正在尝试修复未合并代码块 {{attempt}}/{{max_correction_attempts}}",
        "ja": "マージされていないブロックの修正試行 {{attempt}}/{{max_correction_attempts}}",
        "ar": "محاولة إصلاح الكتل غير المدموجة {{attempt}}/{{max_correction_attempts}}",
        "ru": "Попытка исправления неслитых блоков {{attempt}}/{{max_correction_attempts}}"
    },
    "max_unmerged_blocks_attempts_reached": {
        "en": "Maximum unmerged blocks fix attempts reached",
        "zh": "已达到最大未合并代码块修复尝试次数",
        "ja": "マージされていないブロックの修正の最大試行回数に達しました",
        "ar": "تم الوصول إلى أقصى عدد محاولات إصلاح الكتل غير المدموجة",
        "ru": "Достигнуто максимальное количество попыток исправления неслитых блоков"
    },
    "agenticFilterContext": {
        "en": "Start to find context...",
        "zh": "开始智能查找上下文....",
        "ja": "コンテキストの検索を開始...",
        "ar": "بدء البحث عن السياق...",
        "ru": "Начинаем поиск контекста..."
    },
    "agenticFilterContextFinished": {
        "en": "End to find context...",
        "zh": "结束智能查找上下文....",
        "ja": "コンテキストの検索を終了...",
        "ar": "انتهاء البحث عن السياق...",
        "ru": "Завершение поиска контекста..."
    },
    "/context/check/start": {
        "en": "Starting missing context checking process.",
        "zh": "开始缺失上下文检查过程.",
        "ja": "不足しているコンテキストの確認プロセスを開始します。",
        "ar": "بدء عملية فحص السياق المفقود.",
        "ru": "Начинается процесс проверки отсутствующего контекста."
    },
    "/context/check/end": {
        "en": "Finished missing context checking process.",
        "zh": "结束缺失上下文检查过程.",
        "ja": "不足しているコンテキストの確認プロセスが完了しました。",
        "ar": "انتهت عملية فحص السياق المفقود.",
        "ru": "Процесс проверки отсутствующего контекста завершен."
    },
    "/unmerged_blocks/check/start": {
        "en": "Starting unmerged blocks checking process.",
        "zh": "开始未合并代码检查过程.",
        "ja": "マージされていないブロックの確認プロセスを開始します。",
        "ar": "بدء عملية فحص الكتل غير المدموجة.",
        "ru": "Начинается процесс проверки неслитых блоков."
    },
    "/unmerged_blocks/check/end": {
        "en": "Finished unmerged blocks checking process.",
        "zh": "结束未合并代码检查过程.",
        "ja": "マージされていないブロックの確認プロセスが完了しました。",
        "ar": "انتهت عملية فحص الكتل غير المدموجة.",
        "ru": "Процесс проверки неслитых блоков завершен."
    },
    "/lint/check/start": {
        "en": "Starting lint error checking process.",
        "zh": "开始代码质量检查过程.",
        "ja": "Lintエラーの確認プロセスを開始します。",
        "ar": "بدء عملية فحص أخطاء الكود.",
        "ru": "Начинается процесс проверки ошибок линтинга."
    },
    "/lint/check/end": {
        "en": "Finished lint error checking process.",
        "zh": "结束代码质量检查过程.",
        "ja": "Lintエラーの確認プロセスが完了しました。",
        "ar": "انتهت عملية فحص أخطاء الكود.",
        "ru": "Процесс проверки ошибок линтинга завершен."
    },
    "/compile/check/start": {
        "en": "Starting compile error checking process.",
        "zh": "开始编译错误检查过程.",
        "ja": "コンパイルエラーの確認プロセスを開始します。",
        "ar": "بدء عملية فحص أخطاء التجميع.",
        "ru": "Начинается процесс проверки ошибок компиляции."
    },
    "/compile/check/end": {
        "en": "Finished compile error checking process.",
        "zh": "结束编译错误检查过程.",
        "ja": "コンパイルエラーの確認プロセスが完了しました。",
        "ar": "انتهت عملية فحص أخطاء التجميع.",
        "ru": "Процесс проверки ошибок компиляции завершен."
    },
    "/agent/edit/objective": {
        "en": "Objective",
        "zh": "目标",
        "ja": "目的",
        "ar": "الهدف",
        "ru": "Цель"
    },
    "/agent/edit/user_query": {
        "en": "User Query",
        "zh": "用户查询",
        "ja": "ユーザークエリ",
        "ar": "استعلام المستخدم",
        "ru": "Запрос пользователя"
    },
    "/agent/edit/apply_pre_changes": {
        "en": "Commit user changes",
        "zh": "检查用户是否有手动修改(如有，会自动提交)...",
        "ja": "ユーザーの変更をコミット",
        "ar": "تأكيد تغييرات المستخدم",
        "ru": "Подтверждение изменений пользователя"
    },
    "/agent/edit/apply_changes": {
        "en": "Commit the changes in preview steps",
        "zh": "提交前面步骤的修改",
        "ja": "プレビューステップの変更をコミット",
        "ar": "تأكيد التغييرات في خطوات المعاينة",
        "ru": "Подтверждение изменений на этапах предварительного просмотра"
    },
    "/agent/edit/pull_request/branch_name_failed": {
        "en": "Unable to get current branch name, skipping PR creation",
        "zh": "无法获取当前分支名，跳过 PR 创建",
        "ja": "現在のブランチ名を取得できません、PR作成をスキップします",
        "ar": "غير قادر على الحصول على اسم الفرع الحالي، تخطي إنشاء PR",
        "ru": "Невозможно получить имя текущей ветки, пропускаем создание PR"
    },
    "/agent/edit/pull_request/title": {
        "en": "AutoCoder: {{query}}",
        "zh": "AutoCoder: {{query}}",
        "ja": "AutoCoder: {{query}}",
        "ar": "AutoCoder: {{query}}",
        "ru": "AutoCoder: {{query}}"
    },
    "/agent/edit/pull_request/default_query": {
        "en": "Code auto generation",
        "zh": "代码自动生成",
        "ja": "コード自動生成",
        "ar": "توليد الكود التلقائي",
        "ru": "Автоматическая генерация кода"
    },
    "/agent/edit/pull_request/description": {
        "en": """## 🤖 AutoCoder Generated Pull Request

**Task Description**: {{query}}

### 📝 Change Summary
- Modified {{file_count}} files
- Commit Hash: `{{commit_hash}}`

### 📂 Changed Files List
{{file_list}}

### ⚙️ Generation Configuration
- Source Branch: `{{source_branch}}`
- Target Branch: `{{target_branch}}`
- Auto-generated Time: {{timestamp}}

### 🔍 Next Steps
- [ ] Code Review
- [ ] Test Verification
- [ ] Merge to Main Branch

---
*This PR was automatically created by AutoCoder*
""",
        "zh": """## 🤖 AutoCoder 自动生成的 Pull Request

**任务描述**: {{query}}

### 📝 变更摘要
- 共修改 {{file_count}} 个文件
- 提交哈希: `{{commit_hash}}`

### 📂 变更文件列表
{{file_list}}

### ⚙️ 生成配置
- 源分支: `{{source_branch}}`
- 目标分支: `{{target_branch}}`
- 自动生成时间: {{timestamp}}

### 🔍 下一步
- [ ] 代码审查
- [ ] 测试验证
- [ ] 合并到主分支

---
*此 PR 由 AutoCoder 自动创建*
""",
        "ja": """## 🤖 AutoCoder 生成プルリクエスト

**タスク説明**: {{query}}

### 📝 変更概要
- {{file_count}} ファイルを変更
- コミットハッシュ: `{{commit_hash}}`

### 📂 変更ファイルリスト
{{file_list}}

### ⚙️ 生成設定
- ソースブランチ: `{{source_branch}}`
- ターゲットブランチ: `{{target_branch}}`
- 自動生成時間: {{timestamp}}

### 🔍 次のステップ
- [ ] コードレビュー
- [ ] テスト検証
- [ ] メインブランチにマージ

---
*このPRはAutoCoderによって自動作成されました*
""",
        "ar": """## 🤖 طلب سحب تم إنشاؤه بواسطة AutoCoder

**وصف المهمة**: {{query}}

### 📝 ملخص التغييرات
- تم تعديل {{file_count}} ملف
- هاش الكوميت: `{{commit_hash}}`

### 📂 قائمة الملفات المتغيرة
{{file_list}}

### ⚙️ تكوين التوليد
- الفرع المصدر: `{{source_branch}}`
- الفرع الهدف: `{{target_branch}}`
- وقت التوليد التلقائي: {{timestamp}}

### 🔍 الخطوات التالية
- [ ] مراجعة الكود
- [ ] التحقق من الاختبار
- [ ] الدمج في الفرع الرئيسي

---
*تم إنشاء هذا PR تلقائياً بواسطة AutoCoder*
""",
        "ru": """## 🤖 Pull Request, созданный AutoCoder

**Описание задачи**: {{query}}

### 📝 Сводка изменений
- Изменено {{file_count}} файлов
- Хеш коммита: `{{commit_hash}}`

### 📂 Список измененных файлов
{{file_list}}

### ⚙️ Конфигурация генерации
- Исходная ветка: `{{source_branch}}`
- Целевая ветка: `{{target_branch}}`
- Время автогенерации: {{timestamp}}

### 🔍 Следующие шаги
- [ ] Ревью кода
- [ ] Проверка тестов
- [ ] Слияние в основную ветку

---
*Этот PR был автоматически создан AutoCoder*
"""
    },
    "/agent/edit/pull_request/creating": {
        "en": "Creating Pull Request: {{title}}",
        "zh": "正在创建 Pull Request: {{title}}",
        "ja": "プルリクエストを作成中: {{title}}",
        "ar": "إنشاء طلب السحب: {{title}}",
        "ru": "Создание Pull Request: {{title}}"
    },
    "/agent/edit/pull_request/success": {
        "en": "✅ Pull Request created successfully",
        "zh": "✅ Pull Request 创建成功",
        "ja": "✅ プルリクエストが正常に作成されました",
        "ar": "✅ تم إنشاء طلب السحب بنجاح",
        "ru": "✅ Pull Request успешно создан"
    },
    "/agent/edit/pull_request/failed": {
        "en": "❌ Pull Request creation failed: {{error}}",
        "zh": "❌ Pull Request 创建失败: {{error}}",
        "ja": "❌ プルリクエストの作成に失敗しました: {{error}}",
        "ar": "❌ فشل إنشاء طلب السحب: {{error}}",
        "ru": "❌ Создание Pull Request не удалось: {{error}}"
    },
    "/agent/edit/pull_request/exception": {
        "en": "❌ Exception occurred while creating Pull Request: {{error}}",
        "zh": "❌ 创建 Pull Request 时发生异常: {{error}}",
        "ja": "❌ プルリクエスト作成中に例外が発生しました: {{error}}",
        "ar": "❌ حدث استثناء أثناء إنشاء طلب السحب: {{error}}",
        "ru": "❌ Исключение при создании Pull Request: {{error}}"
    },
    "replace_in_file.access_denied": {
        "en": "Error: Access denied. Attempted to modify file outside the project directory: {{file_path}}",
        "zh": "错误：拒绝访问。尝试修改项目目录之外的文件：{{file_path}}",
        "ja": "エラー：アクセス拒否。プロジェクトディレクトリ外のファイルを変更しようとしました：{{file_path}}",
        "ar": "خطأ: تم رفض الوصول. محاولة تعديل ملف خارج مجلد المشروع: {{file_path}}",
        "ru": "Ошибка: Доступ запрещен. Попытка изменить файл вне директории проекта: {{file_path}}"
    },
    "replace_in_file.file_not_found": {
        "en": "Error: File not found at path: {{file_path}}",
        "zh": "错误：未找到文件路径：{{file_path}}",
        "ja": "エラー：パス {{file_path}} でファイルが見つかりません",
        "ar": "خطأ: لم يتم العثور على الملف في المسار: {{file_path}}",
        "ru": "Ошибка: Файл не найден по пути: {{file_path}}"
    },
    "replace_in_file.read_error": {
        "en": "An error occurred while reading the file for replacement: {{error}}",
        "zh": "读取待替换文件时发生错误：{{error}}",
        "ja": "置換用ファイルの読み取り中にエラーが発生しました：{{error}}",
        "ar": "حدث خطأ أثناء قراءة الملف للاستبدال: {{error}}",
        "ru": "Ошибка при чтении файла для замены: {{error}}"
    },
    "replace_in_file.no_valid_blocks": {
        "en": "Error: No valid SEARCH/REPLACE blocks found in the provided diff.",
        "zh": "错误：在提供的diff中未找到有效的SEARCH/REPLACE代码块。",
        "ja": "エラー：提供されたdiffで有効なSEARCH/REPLACEブロックが見つかりません。",
        "ar": "خطأ: لم يتم العثور على كتل SEARCH/REPLACE صالحة في الفرق المقدم.",
        "ru": "Ошибка: В предоставленном diff не найдены действительные блоки SEARCH/REPLACE."
    },
    "replace_in_file.apply_failed": {
        "en": "Failed to apply any changes. Errors:\n{{errors}}",
        "zh": "未能应用任何更改。错误信息：\n{{errors}}",
        "ja": "変更の適用に失敗しました。エラー：\n{{errors}}",
        "ar": "فشل في تطبيق أي تغييرات. الأخطاء:\n{{errors}}",
        "ru": "Не удалось применить изменения. Ошибки:\n{{errors}}"
    },
    "replace_in_file.apply_success": {
        "en": "Successfully applied {{applied}}/{{total}} changes to file: {{file_path}}.",
        "zh": "成功应用了 {{applied}}/{{total}} 个更改到文件：{{file_path}}。",
        "ja": "ファイル {{file_path}} に {{applied}}/{{total}} 個の変更を正常に適用しました。",
        "ar": "تم تطبيق {{applied}}/{{total}} تغييرات بنجاح على الملف: {{file_path}}。",
        "ru": "Успешно применено {{applied}}/{{total}} изменений к файлу: {{file_path}}."
    },
    "replace_in_file.apply_success_with_warnings": {
        "en": "Successfully applied {{applied}}/{{total}} changes to file: {{file_path}}.\nWarnings:\n{{errors}}",
        "zh": "成功应用了 {{applied}}/{{total}} 个更改到文件：{{file_path}}。\n警告信息：\n{{errors}}",
        "ja": "ファイル {{file_path}} に {{applied}}/{{total}} 個の変更を正常に適用しました。\n警告：\n{{errors}}",
        "ar": "تم تطبيق {{applied}}/{{total}} تغييرات بنجاح على الملف: {{file_path}}。\nتحذيرات:\n{{errors}}",
        "ru": "Успешно применено {{applied}}/{{total}} изменений к файлу: {{file_path}}.\nПредупреждения:\n{{errors}}"
    },
    "replace_in_file.write_error": {
        "en": "An error occurred while writing the modified file: {{error}}",
        "zh": "写入修改后的文件时发生错误：{{error}}",
        "ja": "変更されたファイルの書き込み中にエラーが発生しました：{{error}}",
        "ar": "حدث خطأ أثناء كتابة الملف المعدل: {{error}}",
        "ru": "Ошибка при записи измененного файла: {{error}}"
    },
    "mcp_install_success": {
        "en": "✅ MCP server installed successfully: {{result}}",
        "zh": "✅ MCP 服务器安装成功: {{result}}",
        "ja": "✅ MCPサーバーのインストールが成功しました: {{result}}",
        "ar": "✅ تم تثبيت خادم MCP بنجاح: {{result}}",
        "ru": "✅ MCP сервер успешно установлен: {{result}}"
    },
    "mcp_install_error": {
        "en": "❌ MCP server installation failed: {{error}}",
        "zh": "❌ MCP 服务器安装失败: {{error}}",
        "ja": "❌ MCPサーバーのインストールに失敗しました: {{error}}",
        "ar": "❌ فشل تثبيت خادم MCP: {{error}}",
        "ru": "❌ Установка MCP сервера не удалась: {{error}}"
    },
    "mcp_remove_success": {
        "en": "✅ MCP server removed successfully: {{result}}",
        "zh": "✅ MCP 服务器移除成功: {{result}}",
        "ja": "✅ MCPサーバーの削除が成功しました: {{result}}",
        "ar": "✅ تم إزالة خادم MCP بنجاح: {{result}}",
        "ru": "✅ MCP сервер успешно удален: {{result}}"
    },
    "mcp_remove_error": {
        "en": "❌ MCP server removal failed: {{error}}",
        "zh": "❌ MCP 服务器移除失败: {{error}}",
        "ja": "❌ MCPサーバーの削除に失敗しました: {{error}}",
        "ar": "❌ فشل إزالة خادم MCP: {{error}}",
        "ru": "❌ Удаление MCP сервера не удалось: {{error}}"
    },
    "mcp_list_builtin_title": {
        "en": "📦 Built-in MCP Servers:",
        "zh": "📦 内置 MCP 服务器:",
        "ja": "📦 内蔵MCPサーバー:",
        "ar": "📦 خوادم MCP المدمجة:",
        "ru": "📦 Встроенные MCP серверы:"
    },
    "mcp_list_external_title": {
        "en": "🌐 External MCP Servers:",
        "zh": "🌐 外部 MCP 服务器:",
        "ja": "🌐 外部MCPサーバー:",
        "ar": "🌐 خوادم MCP الخارجية:",
        "ru": "🌐 Внешние MCP серверы:"
    },
    "mcp_list_marketplace_title": {
        "en": "🛍️ Marketplace MCP Servers:",
        "zh": "🛍️ 市场 MCP 服务器:",
        "ja": "🛍️ マーケットプレイスMCPサーバー:",
        "ar": "🛍️ خوادم MCP في السوق:",
        "ru": "🛍️ MCP серверы из маркетплейса:"
    },
    "mcp_list_builtin_error": {
        "en": "❌ Failed to list MCP servers: {{error}}",
        "zh": "❌ 获取 MCP 服务器列表失败: {{error}}",
        "ja": "❌ MCPサーバーのリスト取得に失敗しました: {{error}}",
        "ar": "❌ فشل في إدراج خوادم MCP: {{error}}",
        "ru": "❌ Не удалось получить список MCP серверов: {{error}}"
    },
    "mcp_list_running_error": {
        "en": "❌ Failed to list running MCP servers: {{error}}",
        "zh": "❌ 获取运行中的 MCP 服务器列表失败: {{error}}",
        "ja": "❌ 実行中のMCPサーバーのリスト取得に失敗しました: {{error}}",
        "ar": "❌ فشل في إدراج خوادم MCP قيد التشغيل: {{error}}",
        "ru": "❌ Не удалось получить список работающих MCP серверов: {{error}}"
    },
    "mcp_refresh_success": {
        "en": "✅ MCP servers refreshed successfully",
        "zh": "✅ MCP 服务器刷新成功",
        "ja": "✅ MCPサーバーの更新が成功しました",
        "ar": "✅ تم تحديث خوادم MCP بنجاح",
        "ru": "✅ MCP серверы успешно обновлены"
    },
    "mcp_refresh_error": {
        "en": "❌ MCP servers refresh failed: {{error}}",
        "zh": "❌ MCP 服务器刷新失败: {{error}}",
        "ja": "❌ MCPサーバーの更新に失敗しました: {{error}}",
        "ar": "❌ فشل تحديث خوادم MCP: {{error}}",
        "ru": "❌ Обновление MCP серверов не удалось: {{error}}"
    },
    "mcp_query_empty": {
        "en": "⚠️ Query cannot be empty",
        "zh": "⚠️ 查询不能为空",
        "ja": "⚠️ クエリは空にできません",
        "ar": "⚠️ لا يمكن أن يكون الاستعلام فارغاً",
        "ru": "⚠️ Запрос не может быть пустым"
    },
    "mcp_error_title": {
        "en": "❌ MCP Error",
        "zh": "❌ MCP 错误",
        "ja": "❌ MCPエラー",
        "ar": "❌ خطأ MCP",
        "ru": "❌ Ошибка MCP"
    },
    "mcp_response_title": {
        "en": "✅ MCP Response:",
        "zh": "✅ MCP 响应:",
        "ja": "✅ MCP レスポンス:",
        "ar": "✅ استجابة MCP:",
        "ru": "✅ Ответ MCP:"
    },
    "marketplace_add_success": {
        "en": "✅ Marketplace item added successfully: {{name}}",
        "zh": "✅ 市场项目添加成功: {{name}}",
        "ja": "✅ マーケットプレイスアイテムが正常に追加されました: {{name}}",
        "ar": "✅ تم إضافة عنصر السوق بنجاح: {{name}}",
        "ru": "✅ Элемент маркетплейса успешно добавлен: {{name}}"
    },
    "marketplace_add_error": {
        "en": "❌ Failed to add marketplace item {{name}}: {{error}}",
        "zh": "❌ 添加市场项目 {{name}} 失败: {{error}}",
        "ja": "❌ マーケットプレイスアイテム {{name}} の追加に失敗しました: {{error}}",
        "ar": "❌ فشل في إضافة عنصر السوق {{name}}: {{error}}",
        "ru": "❌ Не удалось добавить элемент маркетплейса {{name}}: {{error}}"
    },
    "marketplace_update_success": {
        "en": "✅ Marketplace item updated successfully: {{name}}",
        "zh": "✅ 市场项目更新成功: {{name}}",
        "ja": "✅ マーケットプレイスアイテムが正常に更新されました: {{name}}",
        "ar": "✅ تم تحديث عنصر السوق بنجاح: {{name}}",
        "ru": "✅ Элемент маркетплейса успешно обновлен: {{name}}"
    },
    "marketplace_update_error": {
        "en": "❌ Failed to update marketplace item {{name}}: {{error}}",
        "zh": "❌ 更新市场项目 {{name}} 失败: {{error}}",
        "ja": "❌ マーケットプレイスアイテム {{name}} の更新に失敗しました: {{error}}",
        "ar": "❌ فشل في تحديث عنصر السوق {{name}}: {{error}}",
        "ru": "❌ Не удалось обновить элемент маркетплейса {{name}}: {{error}}"
    },
    "conversation_message_ids_invalid_action": {
        "en": "Invalid action type: {{action}}",
        "zh": "无效的操作类型: {{action}}",
        "ja": "無効なアクションタイプ: {{action}}",
        "ar": "نوع إجراء غير صحيح: {{action}}",
        "ru": "Неверный тип действия: {{action}}"
    },
    "conversation_message_ids_no_conversation": {
        "en": "Unable to get current conversation ID",
        "zh": "无法获取当前会话ID",
        "ja": "現在の会話IDを取得できません",
        "ar": "غير قادر على الحصول على معرف المحادثة الحالي",
        "ru": "Невозможно получить ID текущего разговора"
    },
    "conversation_message_ids_create_success": {
        "en": "Conversation message IDs configuration has been created",
        "zh": "会话消息ID配置已创建",
        "ja": "会話メッセージID設定が作成されました",
        "ar": "تم إنشاء تكوين معرفات رسائل المحادثة",
        "ru": "Конфигурация ID сообщений разговора создана"
    },
    "conversation_message_ids_create_failed": {
        "en": "Failed to create conversation message IDs configuration: {{error}}",
        "zh": "创建会话消息ID配置失败: {{error}}",
        "ja": "会話メッセージID設定の作成に失敗しました: {{error}}",
        "ar": "فشل في إنشاء تكوين معرفات رسائل المحادثة: {{error}}",
        "ru": "Не удалось создать конфигурацию ID сообщений разговора: {{error}}"
    },
    "conversation_message_ids_append_success": {
        "en": "Conversation message IDs configuration has been appended",
        "zh": "会话消息ID配置已追加",
        "ja": "会話メッセージID設定が追加されました",
        "ar": "تم إلحاق تكوين معرفات رسائل المحادثة",
        "ru": "Конфигурация ID сообщений разговора добавлена"
    },
    "conversation_message_ids_append_failed": {
        "en": "Failed to append conversation message IDs configuration: {{error}}",
        "zh": "追加会话消息ID配置失败: {{error}}",
        "ja": "会話メッセージID設定の追加に失敗しました: {{error}}",
        "ar": "فشل في إلحاق تكوين معرفات رسائل المحادثة: {{error}}",
        "ru": "Не удалось добавить конфигурацию ID сообщений разговора: {{error}}"
    },
    "conversation_message_ids_no_existing_config": {
        "en": "No existing message IDs configuration found",
        "zh": "没有找到现有的消息ID配置",
        "ja": "既存のメッセージID設定が見つかりません",
        "ar": "لم يتم العثور على تكوين معرفات الرسائل الموجود",
        "ru": "Не найдена существующая конфигурация ID сообщений"
    },
    "conversation_message_ids_delete_success": {
        "en": "Conversation message IDs configuration has been completely deleted",
        "zh": "会话消息ID配置已完全删除",
        "ja": "会話メッセージID設定が完全に削除されました",
        "ar": "تم حذف تكوين معرفات رسائل المحادثة بالكامل",
        "ru": "Конфигурация ID сообщений разговора полностью удалена"
    },
    "conversation_message_ids_delete_failed": {
        "en": "Failed to delete conversation message IDs configuration: {{error}}",
        "zh": "删除会话消息ID配置失败: {{error}}",
        "ja": "会話メッセージID設定の削除に失敗しました: {{error}}",
        "ar": "فشل في حذف تكوين معرفات رسائل المحادثة: {{error}}",
        "ru": "Не удалось удалить конфигурацию ID сообщений разговора: {{error}}"
    },
    "conversation_message_ids_update_success": {
        "en": "Conversation message IDs configuration has been updated",
        "zh": "会话消息ID配置已更新",
        "ja": "会話メッセージID設定が更新されました",
        "ar": "تم تحديث تكوين معرفات رسائل المحادثة",
        "ru": "Конфигурация ID сообщений разговора обновлена"
    },
    "conversation_message_ids_update_failed": {
        "en": "Failed to update conversation message IDs configuration: {{error}}",
        "zh": "更新会话消息ID配置失败: {{error}}",
        "ja": "会話メッセージID設定の更新に失敗しました: {{error}}",
        "ar": "فشل في تحديث تكوين معرفات رسائل المحادثة: {{error}}",
        "ru": "Не удалось обновить конфигурацию ID сообщений разговора: {{error}}"
    },
    "conversation_message_ids_operation_exception": {
        "en": "Exception occurred while operating conversation message IDs configuration: {{error}}",
        "zh": "操作会话消息ID配置时发生异常: {{error}}",
        "ja": "会話メッセージID設定の操作中に例外が発生しました: {{error}}",
        "ar": "حدث استثناء أثناء تشغيل تكوين معرفات رسائل المحادثة: {{error}}",
        "ru": "Исключение при работе с конфигурацией ID сообщений разговора: {{error}}"
    },
    "conversation_message_ids_invalid_format": {
        "en": "Invalid message ID format: {{message_id}}",
        "zh": "消息ID格式无效: {{message_id}}",
        "ja": "無効なメッセージID形式: {{message_id}}",
        "ar": "تنسيق معرف الرسالة غير صحيح: {{message_id}}",
        "ru": "Неверный формат ID сообщения: {{message_id}}"
    },
    "conf_key": {
        "en": "Key",
        "zh": "配置项",
        "ja": "キー",
        "ar": "المفتاح",
        "ru": "Ключ"
    },
    "conf_value": {
        "en": "Value",
        "zh": "值",
        "ja": "値",
        "ar": "القيمة",
        "ru": "Значение"
    },
    "conf_subtitle": {
        "en": "Configuration Management",
        "zh": "配置管理",
        "ja": "設定管理",
        "ar": "إدارة التكوين",
        "ru": "Управление конфигурацией"
    },
    "conf_title": {
        "en": "Configuration Settings",
        "zh": "配置设置",
        "ja": "設定",
        "ar": "إعدادات التكوين",
        "ru": "Настройки конфигурации"
    },
    "conf_get_error_args": {
        "en": "Error: 'get' command requires exactly one argument (the key). Usage: /conf get <key>",
        "zh": "错误：'get' 命令需要一个参数（配置项名称）。用法：/conf get <key>",
        "ja": "エラー：'get' コマンドには引数が1つ必要です（キー）。使用法：/conf get <key>",
        "ar": "خطأ: يتطلب أمر 'get' معاملاً واحداً بالضبط (المفتاح). الاستخدام: /conf get <key>",
        "ru": "Ошибка: команда 'get' требует ровно один аргумент (ключ). Использование: /conf get <key>"
    },
    "conf_get_error_not_found": {
        "en": "Error: Configuration key '{{key}}' not found.",
        "zh": "错误：未找到配置项 '{{key}}'。",
        "ja": "エラー：設定キー '{{key}}' が見つかりません。",
        "ar": "خطأ: لم يتم العثور على مفتاح التكوين '{{key}}'.",
        "ru": "Ошибка: Ключ конфигурации '{{key}}' не найден."
    },
    "conf_set_error_args": {
        "en": "Error: 'set' command requires at least two arguments (key and value). Usage: /conf set <key> <value>",
        "zh": "错误：'set' 命令需要至少两个参数（配置项名称和值）。用法：/conf set <key> <value>",
        "ja": "エラー：'set' コマンドには少なくとも2つの引数が必要です（キーと値）。使用法：/conf set <key> <value>",
        "ar": "خطأ: يتطلب أمر 'set' معاملين على الأقل (المفتاح والقيمة). الاستخدام: /conf set <key> <value>",
        "ru": "Ошибка: команда 'set' требует по крайней мере два аргумента (ключ и значение). Использование: /conf set <key> <value>"
    },
    "conf_set_success": {
        "en": "Configuration updated: {{key}} = {{value}}",
        "zh": "配置已更新：{{key}} = {{value}}",
        "ja": "設定が更新されました：{{key}} = {{value}}",
        "ar": "تم تحديث التكوين: {{key}} = {{value}}",
        "ru": "Конфигурация обновлена: {{key}} = {{value}}"
    },
    "conf_set_error": {
        "en": "Error setting configuration for key '{{key}}': {{error}}",
        "zh": "设置配置项 '{{key}}' 时出错：{{error}}",
        "ja": "キー '{{key}}' の設定エラー：{{error}}",
        "ar": "خطأ في تعيين التكوين للمفتاح '{{key}}': {{error}}",
        "ru": "Ошибка установки конфигурации для ключа '{{key}}': {{error}}"
    },
    "conf_delete_error_args": {
        "en": "Error: 'delete' command requires exactly one argument (the key). Usage: /conf delete <key>",
        "zh": "错误：'delete' 命令需要一个参数（配置项名称）。用法：/conf delete <key>",
        "ja": "エラー：'delete' コマンドには引数が1つ必要です（キー）。使用法：/conf delete <key>",
        "ar": "خطأ: يتطلب أمر 'delete' معاملاً واحداً بالضبط (المفتاح). الاستخدام: /conf delete <key>",
        "ru": "Ошибка: команда 'delete' требует ровно один аргумент (ключ). Использование: /conf delete <key>"
    },
    "conf_delete_success": {
        "en": "Configuration deleted: {{key}}",
        "zh": "配置已删除：{{key}}",
        "ja": "設定が削除されました：{{key}}",
        "ar": "تم حذف التكوين: {{key}}",
        "ru": "Конфигурация удалена: {{key}}"
    },
    "conf_delete_error": {
        "en": "Error deleting key '{{key}}': {{error}}",
        "zh": "删除配置项 '{{key}}' 时出错：{{error}}",
        "ja": "キー '{{key}}' の削除エラー：{{error}}",
        "ar": "خطأ في حذف المفتاح '{{key}}': {{error}}",
        "ru": "Ошибка удаления ключа '{{key}}': {{error}}"
    },
    "conf_delete_not_found": {
        "en": "Error: Configuration key '{{key}}' not found.",
        "zh": "错误：未找到配置项 '{{key}}'。",
        "ja": "エラー：設定キー '{{key}}' が見つかりません。",
        "ar": "خطأ: لم يتم العثور على مفتاح التكوين '{{key}}'.",
        "ru": "Ошибка: Ключ конфигурации '{{key}}' не найден."
    },
    "conf_help_args_error": {
        "en": "Error: 'help' command takes no arguments. Usage: /conf help",
        "zh": "错误：'help' 命令不需要参数。用法：/conf help",
        "ja": "エラー：'help' コマンドには引数は不要です。使用法：/conf help",
        "ar": "خطأ: أمر 'help' لا يأخذ معاملات. الاستخدام: /conf help",
        "ru": "Ошибка: команда 'help' не принимает аргументы. Использование: /conf help"
    },
    "conf_help_text": {
        "en": """/conf command usage:
  /conf [pattern]    - Show configurations. Optional wildcard pattern (e.g., *_model, api*).  
  /conf get <key>    - Get the value of a specific configuration key.
  /conf set <key>:<value> - Set or update a configuration key.
                       Value parsed (bool, int, float, None) or treated as string.
                       Use quotes ("value with spaces") for explicit strings.
  /conf drop <key> - Delete a configuration key.
  /conf export <path> - Export current configuration to a file.
  /conf import <path> - Import configuration from a file.
  /conf help         - Show this help message.""",
        "zh": """/conf 命令用法:
  /conf [pattern]    - 显示配置。可选通配符模式 (例如: *_model, api*).  
  /conf get <key>    - 获取指定配置项的值.
  /conf set <key>:<value> - 设置或更新配置项.
                       值会被解析为 (bool, int, float, None) 或字符串.
                       使用引号 ("带空格的值") 表示明确的字符串.
  /conf drop <key> - 删除配置项.
  /conf export <path> - 将当前配置导出到文件.
  /conf import <path> - 从文件导入配置.
  /conf help         - 显示此帮助信息.""",
        "ja": """/conf コマンド使用法:
  /conf [pattern]    - 設定を表示. オプションのワイルドカードパターン (例: *_model, api*).  
  /conf get <key>    - 特定の設定キーの値を取得.
  /conf set <key>:<value> - 設定キーを設定または更新.
                       値は (bool, int, float, None) として解析されるか文字列として扱われます.
                       明示的な文字列には引用符 ("スペースを含む値") を使用.
  /conf drop <key> - 設定キーを削除.
  /conf export <path> - 現在の設定をファイルにエクスポート.
  /conf import <path> - ファイルから設定をインポート.
  /conf help         - このヘルプメッセージを表示.""",
        "ar": """استخدام أمر /conf:
  /conf [pattern]    - إظهار التكوينات. نمط أحرف البدل الاختياري (مثل: *_model, api*).  
  /conf get <key>    - الحصول على قيمة مفتاح تكوين محدد.
  /conf set <key>:<value> - تعيين أو تحديث مفتاح التكوين.
                       يتم تحليل القيمة كـ (bool, int, float, None) أو التعامل معها كسلسلة نصية.
                       استخدم علامات الاقتباس ("قيمة بمسافات") للسلاسل النصية الصريحة.
  /conf drop <key> - حذف مفتاح التكوين.
  /conf export <path> - تصدير التكوين الحالي إلى ملف.
  /conf import <path> - استيراد التكوين من ملف.
  /conf help         - إظهار رسالة المساعدة هذه.""",
        "ru": """Использование команды /conf:
  /conf [pattern]    - Показать конфигурации. Необязательный шаблон с подстановочными знаками (например: *_model, api*).  
  /conf get <key>    - Получить значение определенного ключа конфигурации.
  /conf set <key>:<value> - Установить или обновить ключ конфигурации.
                       Значение парсится как (bool, int, float, None) или обрабатывается как строка.
                       Используйте кавычки ("значение с пробелами") для явных строк.
  /conf drop <key> - Удалить ключ конфигурации.
  /conf export <path> - Экспортировать текущую конфигурацию в файл.
  /conf import <path> - Импортировать конфигурацию из файла.
  /conf help         - Показать это сообщение справки."""
    },
    "conf_export_path_required": {
        "en": "Error: Please specify a path for export. Usage: /conf /export <path>",
        "zh": "错误：请指定导出路径。用法：/conf /export <path>",
        "ja": "エラー：エクスポートのパスを指定してください。使用法：/conf /export <path>",
        "ar": "خطأ: يرجى تحديد مسار للتصدير. الاستخدام: /conf /export <path>",
        "ru": "Ошибка: Пожалуйста, укажите путь для экспорта. Использование: /conf /export <path>"
    },
    "conf_export_success": {
        "en": "Configuration exported successfully to {{path}}",
        "zh": "配置已成功导出到 {{path}}",
        "ja": "設定が {{path}} に正常にエクスポートされました",
        "ar": "تم تصدير التكوين بنجاح إلى {{path}}",
        "ru": "Конфигурация успешно экспортирована в {{path}}"
    },
    "conf_export_error": {
        "en": "Error exporting configuration: {{error}}",
        "zh": "导出配置时出错：{{error}}",
        "ja": "設定のエクスポートエラー：{{error}}",
        "ar": "خطأ في تصدير التكوين: {{error}}",
        "ru": "Ошибка экспорта конфигурации: {{error}}"
    },
    "conf_import_path_required": {
        "en": "Error: Please specify a path for import. Usage: /conf /import <path>",
        "zh": "错误：请指定导入路径。用法：/conf /import <path>",
        "ja": "エラー：インポートのパスを指定してください。使用法：/conf /import <path>",
        "ar": "خطأ: يرجى تحديد مسار للاستيراد. الاستخدام: /conf /import <path>",
        "ru": "Ошибка: Пожалуйста, укажите путь для импорта. Использование: /conf /import <path>"
    },
    "conf_import_success": {
        "en": "Configuration imported successfully from {{path}}. Use '/conf' to see changes.",
        "zh": "配置已成功从 {{path}} 导入。使用 '/conf' 查看更改。",
        "ja": "設定が {{path}} から正常にインポートされました。'/conf' で変更を確認してください。",
        "ar": "تم استيراد التكوين بنجاح من {{path}}. استخدم '/conf' لرؤية التغييرات.",
        "ru": "Конфигурация успешно импортирована из {{path}}. Используйте '/conf' для просмотра изменений."
    },
    "conf_import_error": {
        "en": "Error importing configuration: {{error}}",
        "zh": "导入配置时出错：{{error}}",
        "ja": "設定のインポートエラー：{{error}}",
        "ar": "خطأ في استيراد التكوين: {{error}}",
        "ru": "Ошибка импорта конфигурации: {{error}}"
    },
    "conf_no_configs_found": {
        "en": "No configurations set.",
        "zh": "未设置任何配置。",
        "ja": "設定されていません。",
        "ar": "لم يتم تعيين أي تكوينات.",
        "ru": "Конфигурации не заданы."
    },
    "conf_no_pattern_matches": {
        "en": "No configuration keys found matching pattern: {{pattern}}",
        "zh": "未找到匹配模式的配置项：{{pattern}}",
        "ja": "パターンに一致する設定キーが見つかりません：{{pattern}}",
        "ar": "لم يتم العثور على مفاتيح تكوين تطابق النمط: {{pattern}}",
        "ru": "Не найдены ключи конфигурации, соответствующие шаблону: {{pattern}}"
    },
    "conf_filtered_title": {
        "en": "Filtered Configuration (Pattern: {{pattern}})",
        "zh": "过滤后的配置（模式：{{pattern}}）",
        "ja": "フィルタされた設定（パターン：{{pattern}}）",
        "ar": "التكوين المصفى (النمط: {{pattern}})",
        "ru": "Отфильтрованная конфигурация (Шаблон: {{pattern}})"
    },
    "conf_unknown_command": {
        "en": "Error: Unknown command '/conf {{command}}'. Type '/conf help' for available commands.",
        "zh": "错误：未知命令 '/conf {{command}}'。输入 '/conf help' 查看可用命令。",
        "ja": "エラー：不明なコマンド '/conf {{command}}'。利用可能なコマンドについては '/conf help' を入力してください。",
        "ar": "خطأ: أمر غير معروف '/conf {{command}}'. اكتب '/conf help' للأوامر المتاحة.",
        "ru": "Ошибка: Неизвестная команда '/conf {{command}}'. Введите '/conf help' для доступных команд."
    },
    "conf_invalid_key_value_format": {
        "en": "Error: Invalid key:value format in '{{input}}'. Use '/conf set {{key}} {{value}}' or '/conf help'.",
        "zh": "错误：'{{input}}' 中的 key:value 格式无效。使用 '/conf set {{key}} {{value}}' 或 '/conf help'。",
        "ja": "エラー：'{{input}}' の key:value 形式が無効です。'/conf set {{key}} {{value}}' または '/conf help' を使用してください。",
        "ar": "خطأ: تنسيق key:value غير صحيح في '{{input}}'. استخدم '/conf set {{key}} {{value}}' أو '/conf help'.",
        "ru": "Ошибка: Неверный формат key:value в '{{input}}'. Используйте '/conf set {{key}} {{value}}' или '/conf help'."
    },
    "conf_unknown_format": {
        "en": "Error: Unknown command or invalid format '{{input}}'. Type '/conf help' for available commands.",
        "zh": "错误：未知命令或无效格式 '{{input}}'。输入 '/conf help' 查看可用命令。",
        "ja": "エラー：不明なコマンドまたは無効な形式 '{{input}}'。利用可能なコマンドについては '/conf help' を入力してください。",
        "ar": "خطأ: أمر غير معروف أو تنسيق غير صحيح '{{input}}'. اكتب '/conf help' للأوامر المتاحة.",
        "ru": "Ошибка: Неизвестная команда или неверный формат '{{input}}'. Введите '/conf help' для доступных команд."
    },
    "conf_unexpected_error": {
        "en": "An unexpected error occurred while executing '/conf {{command}}': {{error}}",
        "zh": "执行 '/conf {{command}}' 时发生意外错误：{{error}}",
        "ja": "'/conf {{command}}' の実行中に予期しないエラーが発生しました：{{error}}",
        "ar": "حدث خطأ غير متوقع أثناء تنفيذ '/conf {{command}}': {{error}}",
        "ru": "Произошла неожиданная ошибка при выполнении '/conf {{command}}': {{error}}"
    },
    "async_task_started": {
        "en": "Async task started!",
        "zh": "异步任务已启动！",
        "ja": "非同期タスクが開始されました！",
        "ar": "تم بدء المهمة غير المتزامنة!",
        "ru": "Асинхронная задача запущена!"
    },
    "async_task_model": {
        "en": "Model:",
        "zh": "模型:",
        "ja": "モデル:",
        "ar": "النموذج:",
        "ru": "Модель:"
    },
    "async_task_query": {
        "en": "Query:",
        "zh": "查询:",
        "ja": "クエリ:",
        "ar": "الاستعلام:",
        "ru": "Запрос:"
    },
    "async_task_details_location": {
        "en": "View task details at:",
        "zh": "任务详情请查看:",
        "ja": "タスクの詳細はこちらで確認:",
        "ar": "عرض تفاصيل المهمة في:",
        "ru": "Подробности задачи смотрите в:"
    },
    "async_task_background_tip": {
        "en": "Tip: Task is running in the background, you can continue using other features",
        "zh": "提示: 任务正在后台执行，您可以继续使用其他功能",
        "ja": "ヒント: タスクはバックグラウンドで実行中です。他の機能も引き続き使用できます",
        "ar": "تلميح: المهمة تعمل في الخلفية، يمكنك الاستمرار في استخدام الميزات الأخرى",
        "ru": "Подсказка: Задача выполняется в фоне, вы можете продолжать использовать другие функции"
    },
    "async_task_title": {
        "en": "🚀 Async Task",
        "zh": "🚀 异步任务",
        "ja": "🚀 非同期タスク",
        "ar": "🚀 مهمة غير متزامنة",
        "ru": "🚀 Асинхронная задача"
    }
}
