"""
Rules command messages for internationalization
Contains all messages used by the rules command functionality
"""

RULES_COMMAND_MESSAGES = {
    "rule_cmd_analyzing_project": {
        "en": "Using subagent mechanism to analyze project structure and generate initialization rules...",
        "zh": "正在使用 subagent 机制分析项目结构并生成初始化规则...",
        "ja": "サブエージェント機構を使用してプロジェクト構造を分析し、初期化ルールを生成しています...",
        "ar": "استخدام آلية الوكيل الفرعي لتحليل هيكل المشروع وإنشاء قواعد التهيئة...",
        "ru": "Использование механизма подагента для анализа структуры проекта и генерации правил инициализации..."
    },
    "rule_cmd_init_failed": {
        "en": "Initialization rules generation failed, please check project directory and model configuration",
        "zh": "初始化规则生成失败，请检查项目目录和模型配置",
        "ja": "初期化ルールの生成に失敗しました。プロジェクトディレクトリとモデル設定を確認してください",
        "ar": "فشل في إنشاء قواعد التهيئة، يرجى التحقق من دليل المشروع وتكوين النموذج",
        "ru": "Не удалось сгенерировать правила инициализации, проверьте директорию проекта и конфигурацию модели"
    },
    "rule_cmd_init_success": {
        "en": "Initialization rules generated successfully!",
        "zh": "初始化规则生成成功！",
        "ja": "初期化ルールが正常に生成されました！",
        "ar": "تم إنشاء قواعد التهيئة بنجاح！",
        "ru": "Правила инициализации успешно сгенерированы!"
    },
    "rule_cmd_project_type": {
        "en": "Project type",
        "zh": "项目类型",
        "ja": "プロジェクトタイプ",
        "ar": "نوع المشروع",
        "ru": "Тип проекта"
    },
    "rule_cmd_rules_file": {
        "en": "Rules file",
        "zh": "规则文件",
        "ja": "ルールファイル",
        "ar": "ملف القواعد",
        "ru": "Файл правил"
    },
    "rule_cmd_detected_technologies": {
        "en": "Detected technologies",
        "zh": "检测到的技术栈",
        "ja": "検出された技術",
        "ar": "التقنيات المكتشفة",
        "ru": "Обнаруженные технологии"
    },
    "rule_cmd_detected_commands": {
        "en": "Detected commands",
        "zh": "检测到的命令",
        "ja": "検出されたコマンド",
        "ar": "الأوامر المكتشفة",
        "ru": "Обнаруженные команды"
    },
    "rule_cmd_rules_content_preview": {
        "en": "Rules content preview",
        "zh": "规则内容预览",
        "ja": "ルール内容プレビュー",
        "ar": "معاينة محتوى القواعد",
        "ru": "Предпросмотр содержимого правил"
    },
    "rule_cmd_edit_rules_note": {
        "en": "You can edit the generated rules file to customize project development standards.",
        "zh": "您可以编辑生成的规则文件来自定义项目开发规范。",
        "ja": "生成されたルールファイルを編集して、プロジェクト開発標準をカスタマイズできます。",
        "ar": "يمكنك تحرير ملف القواعد المُنشأ لتخصيص معايير تطوير المشروع.",
        "ru": "Вы можете отредактировать сгенерированный файл правил для настройки стандартов разработки проекта."
    },
    "rule_cmd_init_error": {
        "en": "Error occurred during initialization rules generation: {{error}}",
        "zh": "初始化规则生成时出错: {{error}}",
        "ja": "初期化ルール生成中にエラーが発生しました: {{error}}",
        "ar": "حدث خطأ أثناء إنشاء قواعد التهيئة: {{error}}",
        "ru": "Произошла ошибка при генерации правил инициализации: {{error}}"
    }
}