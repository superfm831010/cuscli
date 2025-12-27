"""
Git Helper Plugin 国际化消息
定义 Git Helper Plugin 中使用的所有国际化消息
"""

# Git Helper Plugin 消息
GIT_HELPER_PLUGIN_MESSAGES = {
    # 插件初始化相关消息
    "git_not_available_warning": {
        "en": "Warning: Git is not available, some functionality will be limited",
        "zh": "警告: Git不可用，某些功能受限",
        "ja": "警告: Gitが利用できません。一部の機能が制限されます",
        "ar": "تحذير: Git غير متوفر، بعض الوظائف ستكون محدودة",
        "ru": "Предупреждение: Git недоступен, некоторые функции будут ограничены"
    },
    "git_helper_initialized": {
        "en": "Git helper plugin initialized",
        "zh": "Git助手插件已初始化", 
        "ja": "Gitヘルパープラグインが初期化されました",
        "ar": "تم تهيئة مكون Git المساعد",
        "ru": "Плагин помощника Git инициализирован"
    },
    "git_helper_shutdown": {
        "en": "Git helper plugin shutdown",
        "zh": "Git助手插件已关闭",
        "ja": "Gitヘルパープラグインがシャットダウンされました", 
        "ar": "تم إغلاق مكون Git المساعد",
        "ru": "Плагин помощника Git выключен"
    },
    
    # 命令描述
    "cmd_git_status_desc": {
        "en": "Show Git repository status",
        "zh": "显示Git仓库状态",
        "ja": "Gitリポジトリのステータスを表示",
        "ar": "عرض حالة مستودع Git",
        "ru": "Показать статус Git-репозитория"
    },
    "cmd_git_commit_desc": {
        "en": "Commit changes",
        "zh": "提交更改",
        "ja": "変更をコミット",
        "ar": "تأكيد التغييرات",
        "ru": "Зафиксировать изменения"
    },
    "cmd_git_branch_desc": {
        "en": "Show or create branches",
        "zh": "显示或创建分支",
        "ja": "ブランチを表示または作成",
        "ar": "عرض أو إنشاء الفروع",
        "ru": "Показать или создать ветки"
    },
    "cmd_git_checkout_desc": {
        "en": "Switch branches",
        "zh": "切换分支",
        "ja": "ブランチを切り替え",
        "ar": "تبديل الفروع", 
        "ru": "Переключить ветки"
    },
    "cmd_git_diff_desc": {
        "en": "Show change differences",
        "zh": "显示更改差异",
        "ja": "変更の差分を表示",
        "ar": "عرض اختلافات التغييرات",
        "ru": "Показать различия изменений"
    },
    "cmd_git_log_desc": {
        "en": "Show commit history", 
        "zh": "显示提交历史",
        "ja": "コミット履歴を表示",
        "ar": "عرض تاريخ التأكيدات",
        "ru": "Показать историю коммитов"
    },
    "cmd_git_pull_desc": {
        "en": "Pull remote changes",
        "zh": "拉取远程更改",
        "ja": "リモートの変更をプル",
        "ar": "سحب التغييرات البعيدة",
        "ru": "Получить удаленные изменения"
    },
    "cmd_git_push_desc": {
        "en": "Push local changes to remote",
        "zh": "推送本地更改到远程",
        "ja": "ローカルの変更をリモートにプッシュ", 
        "ar": "دفع التغييرات المحلية إلى البعيد",
        "ru": "Отправить локальные изменения на удаленный сервер"
    },
    "cmd_git_reset_desc": {
        "en": "Reset current branch to specified state (hard/soft/mixed)",
        "zh": "重置当前分支到指定状态 (hard/soft/mixed)",
        "ja": "現在のブランチを指定した状態にリセット (hard/soft/mixed)",
        "ar": "إعادة تعيين الفرع الحالي إلى الحالة المحددة (hard/soft/mixed)",
        "ru": "Сбросить текущую ветку до указанного состояния (hard/soft/mixed)"
    },

    # 错误和警告消息
    "git_not_available": {
        "en": "Git is not available",
        "zh": "Git不可用",
        "ja": "Gitが利用できません",
        "ar": "Git غير متوفر",
        "ru": "Git недоступен"
    },
    "error_prefix": {
        "en": "Error:",
        "zh": "错误:",
        "ja": "エラー:",
        "ar": "خطأ:",
        "ru": "Ошибка:"
    },
    "no_differences": {
        "en": "No differences",
        "zh": "没有差异",
        "ja": "差分なし",
        "ar": "لا توجد اختلافات",
        "ru": "Нет различий"
    },

    # Git commit 相关消息
    "commit_message_required": {
        "en": "Please provide a commit message, for example: /git/commit 'Fix bug in login'",
        "zh": "请提供提交信息，例如: /git/commit 'Fix bug in login'",
        "ja": "コミットメッセージを提供してください。例: /git/commit 'Fix bug in login'",
        "ar": "يرجى تقديم رسالة التأكيد، على سبيل المثال: /git/commit 'Fix bug in login'", 
        "ru": "Пожалуйста, укажите сообщение коммита, например: /git/commit 'Fix bug in login'"
    },

    # Git checkout 相关消息  
    "checkout_branch_required": {
        "en": "Please provide a branch name, for example: /git/checkout main",
        "zh": "请提供分支名称，例如: /git/checkout main",
        "ja": "ブランチ名を提供してください。例: /git/checkout main",
        "ar": "يرجى تقديم اسم الفرع، على سبيل المثال: /git/checkout main",
        "ru": "Пожалуйста, укажите имя ветки, например: /git/checkout main"
    },

    # Git reset 相关消息
    "reset_mode_required": {
        "en": "Please provide reset mode (hard/soft/mixed) and optional commit hash",
        "zh": "请提供重置模式 (hard/soft/mixed) 和可选的提交哈希",
        "ja": "リセットモード (hard/soft/mixed) と任意のコミットハッシュを提供してください",
        "ar": "يرجى تقديم وضع الإعادة التعيين (hard/soft/mixed) ورمز التأكيد الاختياري",
        "ru": "Пожалуйста, укажите режим сброса (hard/soft/mixed) и необязательный хеш коммита"
    },
    "invalid_reset_mode": {
        "en": "Error: Invalid reset mode '{{mode}}', must be one of hard/soft/mixed",
        "zh": "错误: 无效的重置模式 '{{mode}}'，必须是 hard/soft/mixed 之一",
        "ja": "エラー: 無効なリセットモード '{{mode}}'、hard/soft/mixed のいずれかである必要があります",
        "ar": "خطأ: وضع إعادة التعيين غير صحيح '{{mode}}'، يجب أن يكون أحد hard/soft/mixed",
        "ru": "Ошибка: Неверный режим сброса '{{mode}}', должен быть один из hard/soft/mixed"
    },
    "reset_success": {
        "en": "Successfully reset repository to {{mode}} mode to {{commit}}",
        "zh": "成功将仓库重置为 {{mode}} 模式到 {{commit}}",
        "ja": "リポジトリを{{mode}}モードで{{commit}}に正常にリセットしました",
        "ar": "تم إعادة تعيين المستودع بنجاح إلى وضع {{mode}} إلى {{commit}}",
        "ru": "Успешно сброшен репозиторий в режиме {{mode}} до {{commit}}"
    }
} 