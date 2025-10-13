# Git 平台插件扩展 - 总体概述

## 📋 项目目标

扩展 Git Helper 插件，支持 GitHub 和 GitLab 的配置管理、平台切换，并与现有 PR 管理模块集成。

### 核心功能

1. **GitHub 配置管理** - 支持多个 GitHub 账号/实例的配置
2. **GitLab 配置管理** - 支持公网和私有部署的 GitLab 配置
3. **平台切换** - 在 GitHub 和 GitLab 之间无缝切换
4. **连接测试** - 验证配置的有效性
5. **PR 模块集成** - 与现有 Pull Request 管理模块集成

---

## 🏗️ 架构设计

### 配置存储结构

```
.auto-coder/
└── plugins/
    └── autocoder.plugins.GitHelperPlugin/
        └── config.json
```

**配置文件格式：**
```json
{
  "current_platform": "gitlab",
  "current_config": {
    "github": "personal-github",
    "gitlab": "company-gitlab"
  },
  "platforms": {
    "github": {
      "personal-github": {
        "name": "个人 GitHub",
        "platform": "github",
        "base_url": "https://api.github.com",
        "token": "<encrypted>",
        "verify_ssl": true,
        "timeout": 30,
        "created_at": "2025-01-13T10:00:00",
        "last_tested": "2025-01-13T10:05:00"
      }
    },
    "gitlab": {
      "company-gitlab": {
        "name": "公司 GitLab",
        "platform": "gitlab",
        "base_url": "https://gitlab.example.com",
        "token": "<encrypted>",
        "verify_ssl": false,
        "timeout": 30,
        "created_at": "2025-01-13T11:00:00"
      }
    }
  }
}
```

### 核心模块

1. **GitPlatformConfig** (`autocoder/common/git_platform_config.py`)
   - 配置数据类定义
   - 配置管理器实现
   - Token 加密/解密
   - 连接测试逻辑

2. **GitHelperPlugin** (`autocoder/plugins/git_helper_plugin.py`)
   - 命令处理路由
   - 引导式配置 UI
   - 平台切换控制
   - PR 模块集成

---

## 📋 实施阶段规划

### Phase 1: 配置管理框架 (文档: 01-phase1-config-framework.md)

**目标：** 创建核心配置管理模块

- 创建 `git_platform_config.py` 模块
- 实现 `GitPlatformConfig` 数据类
- 实现 `GitPlatformManager` 配置管理器
- 实现配置的增删改查基础功能

**预估时间：** 2-3 小时

---

### Phase 2: GitHub 配置管理 (文档: 02-phase2-github-config.md)

**目标：** 实现 GitHub 配置的完整流程

- 扩展 GitHelperPlugin，添加 `/git /github` 命令组
- 实现 `/git /github /setup` 引导式配置
- 实现 `/git /github /list` 列表显示
- 实现 `/git /github /modify` 修改功能
- 实现 `/git /github /delete` 删除功能

**预估时间：** 2-3 小时

---

### Phase 3: GitLab 配置管理 (文档: 03-phase3-gitlab-config.md)

**目标：** 实现 GitLab 配置的完整流程

- 实现 `/git /gitlab /setup` 引导式配置
- 实现 `/git /gitlab /list` 列表显示
- 实现 `/git /gitlab /modify` 修改功能
- 实现 `/git /gitlab /delete` 删除功能
- 支持私有 GitLab 实例配置

**预估时间：** 2-3 小时

---

### Phase 4: 平台切换功能 (文档: 04-phase4-platform-switch.md)

**目标：** 实现 GitHub/GitLab 平台切换

- 实现 `/git /platform` 状态显示
- 实现 `/git /platform /switch` 切换命令
- 实现 `/git /platform /list` 概览显示
- 实现默认配置管理

**预估时间：** 1-2 小时

---

### Phase 5: 连接测试功能 (文档: 05-phase5-connection-test.md)

**目标：** 实现配置连接测试

- GitHub API 连接测试 (`GET /user`)
- GitLab API 连接测试 (`GET /api/v4/user`)
- 实现 `/git /github /test` 命令
- 实现 `/git /gitlab /test` 命令
- 显示测试结果（用户名、版本等）

**预估时间：** 1-2 小时

---

### Phase 6: PR 模块集成 (文档: 06-phase6-pr-integration.md)

**目标：** 与现有 PR 管理模块集成

- 在插件初始化时加载当前平台配置
- 调用 `set_global_config` 设置 PR 配置
- 在平台切换时更新 PR 配置
- 确保 PR 操作使用当前平台配置

**预估时间：** 1-2 小时

---

### Phase 7: 命令补全增强 (文档: 07-phase7-completion.md)

**目标：** 实现智能命令补全

- 静态补全：命令结构补全
- 动态补全：配置名称补全
- 平台类型补全
- 提升用户体验

**预估时间：** 1-2 小时

---

### Phase 8: 测试验证 (文档: 08-testing-guide.md)

**目标：** 全面测试所有功能

- GitHub 配置测试
- GitLab 配置测试
- 平台切换测试
- 错误处理测试
- 多配置管理测试

**预估时间：** 2-3 小时

---

### Phase 9: 文档编写 (文档: 09-user-guide.md)

**目标：** 编写用户使用文档

- 如何获取 GitHub Token
- 如何获取 GitLab Token
- 配置管理指南
- 常见问题解答

**预估时间：** 1-2 小时

---

## 🔄 实施流程

### 每个阶段的标准流程

1. **阅读阶段文档** 📖
   - 了解阶段目标
   - 检查前置条件
   - 熟悉实施步骤

2. **代码实现** 💻
   - 按照文档中的代码示例实现
   - 遵循现有代码风格
   - 添加必要的注释

3. **功能测试** 🧪
   - 运行测试用例
   - 验证功能正常
   - 检查错误处理

4. **提交代码** 📝
   - 提交到 git
   - 更新二次开发记录

5. **进入下一阶段** ➡️
   - 阅读下一阶段文档
   - 重复上述流程

---

## 📊 总体进度跟踪

| 阶段 | 文档 | 状态 | 预估时间 |
|------|------|------|----------|
| Phase 1 | 01-phase1-config-framework.md | ⏳ 待开始 | 2-3 小时 |
| Phase 2 | 02-phase2-github-config.md | ⏳ 待开始 | 2-3 小时 |
| Phase 3 | 03-phase3-gitlab-config.md | ⏳ 待开始 | 2-3 小时 |
| Phase 4 | 04-phase4-platform-switch.md | ⏳ 待开始 | 1-2 小时 |
| Phase 5 | 05-phase5-connection-test.md | ⏳ 待开始 | 1-2 小时 |
| Phase 6 | 06-phase6-pr-integration.md | ⏳ 待开始 | 1-2 小时 |
| Phase 7 | 07-phase7-completion.md | ⏳ 待开始 | 1-2 小时 |
| Phase 8 | 08-testing-guide.md | ⏳ 待开始 | 2-3 小时 |
| Phase 9 | 09-user-guide.md | ⏳ 待开始 | 1-2 小时 |

**总计预估时间：** 约 13-21 小时

---

## 🎯 成功标准

### 功能完整性
- ✅ 可以配置 GitHub
- ✅ 可以配置 GitLab（公网和私有）
- ✅ 可以在平台间切换
- ✅ 可以测试连接
- ✅ PR 操作使用当前平台配置

### 用户体验
- ✅ 引导式配置友好易用
- ✅ 命令补全智能准确
- ✅ 错误提示清晰明确
- ✅ 文档完整详细

### 代码质量
- ✅ 代码结构清晰
- ✅ 注释完整
- ✅ 错误处理完善
- ✅ 测试覆盖充分

---

## 📞 测试准备

### GitHub 测试所需
- GitHub 账号
- Personal Access Token (权限: `repo`, `read:user`)
- 获取方式：GitHub → Settings → Developer settings → Personal access tokens

### GitLab 测试所需
- GitLab 账号 (gitlab.com)
- Personal Access Token (权限: `api`)
- 获取方式：GitLab → Settings → Access Tokens

**请提前准备好测试账号和 Token！**

---

## 📚 相关资源

### 项目内参考代码
- `autocoder/common/llms/guided_setup.py` - 引导式配置参考
- `autocoder/plugins/code_checker_plugin.py` - 插件实现参考
- `autocoder/common/pull_requests/` - PR 模块参考

### API 文档
- [GitHub API](https://docs.github.com/en/rest)
- [GitLab API](https://docs.gitlab.com/ee/api/)

---

## 🚀 开始实施

准备好后，请从 **Phase 1** 开始：

👉 **下一步：** 阅读 `01-phase1-config-framework.md`
