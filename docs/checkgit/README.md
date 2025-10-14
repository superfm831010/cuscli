# Git 提交代码检查功能 - 设计文档

## 文档导航

本目录包含了 Git 提交代码检查功能的完整设计文档，分为 6 个阶段。

### 📘 [00-overview.md](00-overview.md) - 总体设计概述
**阅读时间**: 10 分钟

- 功能目标和核心价值
- 命令设计和架构设计
- 技术方案和实施路线图
- 关键风险和缓解措施
- 成功标准

**适合**: 项目经理、技术负责人、新加入的开发者

---

### 🔧 [01-git-helper.md](01-git-helper.md) - Git 文件获取模块设计
**阅读时间**: 15 分钟
**预计实施**: 1 天

- `GitFileHelper` 类完整设计
- 核心方法详细实现
  - 暂存区文件获取
  - 工作区文件获取
  - Commit 文件获取
  - Diff 文件获取
- 边界情况处理
- 单元测试设计

**适合**: 后端开发者、测试工程师

---

### 🎛️ [02-plugin-extension.md](02-plugin-extension.md) - 插件命令扩展设计
**阅读时间**: 20 分钟
**预计实施**: 1 天

- 命令结构和路由设计
- 插件修改点详细说明
- 各子命令实现方案
  - `/check /git /staged`
  - `/check /git /unstaged`
  - `/check /git /commit`
  - `/check /git /diff`
- 选项解析和批量检查集成

**适合**: 插件开发者、全栈开发者

---

### 📁 [03-file-handling.md](03-file-handling.md) - 特殊文件处理策略
**阅读时间**: 15 分钟
**预计实施**: 0.5 天

- 文件来源分类
- 临时文件管理器设计
- 文件准备流程
- 边界情况处理
  - 删除的文件
  - 二进制文件
  - 编码错误
  - 大文件
- Windows/Linux 兼容性

**适合**: 系统开发者、DevOps 工程师

---

### 📊 [04-report-enhancement.md](04-report-enhancement.md) - 报告增强设计
**阅读时间**: 12 分钟
**预计实施**: 0.5 天

- 报告类型扩展
  - Git 暂存区报告
  - Git 工作区报告
  - Git Commit 报告
  - Git Diff 报告
- 数据模型扩展 (`GitInfo`)
- 报告生成器修改方案
- 控制台输出增强

**适合**: 前端开发者、UI/UX 设计师

---

### 🧪 [05-testing-plan.md](05-testing-plan.md) - 测试计划
**阅读时间**: 15 分钟
**预计实施**: 1 天

- 测试环境配置
- 单元测试设计
- 集成测试场景
- 边界情况测试
- 跨平台测试
- 性能测试
- 手工测试清单

**适合**: 测试工程师、QA 工程师

---

### ✅ [06-implementation-checklist.md](06-implementation-checklist.md) - 实施清单
**阅读时间**: 10 分钟
**持续跟踪**: 整个开发过程

- 总体进度跟踪
- 各 Phase 详细任务清单
- 验收标准
- 风险和缓解措施
- 发布计划
- 时间估算

**适合**: 项目经理、开发负责人、全体开发者

---

## 快速开始

### 新加入的开发者
1. 阅读 [00-overview.md](00-overview.md) 了解整体架构
2. 根据分工阅读对应的详细设计文档
3. 参考 [06-implementation-checklist.md](06-implementation-checklist.md) 跟踪进度

### 实施开发
1. 按照 Phase 1 → Phase 5 的顺序实施
2. 每个 Phase 完成后运行对应测试
3. 在 [06-implementation-checklist.md](06-implementation-checklist.md) 中勾选完成的任务

### 测试验证
1. 阅读 [05-testing-plan.md](05-testing-plan.md)
2. 运行单元测试和集成测试
3. 执行手工测试清单

---

## 文档使用建议

### 第一次阅读
```
00-overview.md (必读)
    ↓
根据角色选择:
    ├─ 后端开发 → 01, 03
    ├─ 插件开发 → 02
    ├─ 报告功能 → 04
    └─ 测试工程 → 05
    ↓
06-implementation-checklist.md (必读)
```

### 实施过程中
- 开发时参考对应 Phase 的详细设计
- 遇到问题查阅边界情况处理章节
- 完成任务后更新清单

### 测试阶段
- 参考测试计划执行测试
- 按照清单验证功能完整性

---

## 总体时间规划

| 阶段 | 工作量 | 起止时间 |
|------|--------|----------|
| Phase 1 | 1 天 | Day 1 |
| Phase 2 | 1 天 | Day 2 |
| Phase 3 | 0.5 天 | Day 2 下午 |
| Phase 4 | 0.5 天 | Day 3 上午 |
| Phase 5 | 1 天 | Day 3 下午 - Day 4 |
| **总计** | **4 天** | |

---

## 核心功能预览

### 命令示例

```bash
# 检查暂存区文件
/check /git /staged

# 检查工作区修改
/check /git /unstaged

# 检查某个 commit
/check /git /commit abc1234

# 检查两个 commit 间差异
/check /git /diff main dev

# 带参数的检查
/check /git /staged /repeat 3 /consensus 0.8 /workers 5
```

### 报告示例

```markdown
# 代码检查报告 - Git Commit

**检查类型**: Git Commit 检查
**Commit**: `abc1234` - feat: add new feature
**作者**: John Doe <john@example.com>
**日期**: 2025-01-10 10:30:00
**变更文件**: 5 个

---

## 检查统计
- **总问题数**: 12 个
  - ❌ 错误: 3 个
  - ⚠️ 警告: 7 个
  - ℹ️ 提示: 2 个
```

---

## 技术栈

- **Python**: 3.8+
- **GitPython**: Git 操作库
- **loguru**: 日志记录
- **pydantic**: 数据验证
- **pytest**: 单元测试
- **tempfile**: 临时文件管理

---

## 关键设计原则

1. **复用现有架构**: 最大化复用现有 checker 模块
2. **无侵入式**: 不修改核心检查逻辑
3. **跨平台兼容**: Windows 和 Linux 都能运行
4. **用户友好**: 清晰的命令、进度提示、错误处理

---

## 联系方式

如有问题或建议，请：
1. 提 Issue
2. 联系项目负责人
3. 参考 `docs/code_checker_usage.md`

---

## 更新历史

- 2025-01-10: 创建初始设计文档
- (后续更新记录在此)

---

**祝开发顺利！** 🚀
