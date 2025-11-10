---
description: "海关信息系统开发规范 - Vibecoding最佳实践指导"
alwaysApply: true
---

# 海关开发规范Rules系统

本规范基于海关信息系统开发标准，为AI代码生成提供最佳实践指导。规范覆盖164条规则（53条后端+111条前端）和完整的数据库设计规范。

## 📚 规则体系结构

### 🔴 P0级规则（总是应用）

这些规则在所有代码生成场景中自动应用：

#### 后端规则
- [backend/01-project-setup.md](./backend/01-project-setup.md) - **项目搭建场景**
  - CACP父依赖配置、目录结构、字符集统一
- [backend/06-exception-handling.md](./backend/06-exception-handling.md) - **异常处理场景**
  - BizException封装、异常日志记录、全局异常处理
- [backend/07-logging.md](./backend/07-logging.md) - **日志记录场景**
  - 日志级别、日志内容、审计日志规范
- [backend/08-security.md](./backend/08-security.md) - **安全防护场景**
  - XSS防护、SQL注入防护、敏感信息脱敏、Redis安全

#### 前端规则
- [frontend/01-project-setup.md](./frontend/01-project-setup.md) - **前端项目搭建场景**
  - Vue3+Vite+TypeScript+ElementPlus技术栈、统一入口集成
- [frontend/05-ui-styling.md](./frontend/05-ui-styling.md) - **UI样式规范场景**
  - 海关蓝/政务红主题色、字体、圆角、间距统一

---

### 🟡 P1级规则（按需应用）

这些规则根据文件路径（globs模式）自动匹配应用：

#### 后端规则
- [backend/02-api-development.md](./backend/02-api-development.md) - **API开发场景**
  - RESTful API设计、Controller开发、HTTP方法规范
  - 适用文件：`**/*Controller.java`, `**/controller/**/*.java`, `**/api/**/*.java`

- [backend/03-database-design.md](./backend/03-database-design.md) - **数据库设计场景** ⭐重点
  - 表结构设计、字段定义、索引设计、命名规范
  - 必备字段（REC_VERSION、REC_CREATE_TIME、REC_LAST_UPDATE_TIME）
  - 分区设计、数据清理、约束设计
  - 适用文件：`**/*Mapper.xml`, `**/*Dao.java`, `**/*Entity.java`, `**/sql/**/*.sql`

- [backend/04-database-operations.md](./backend/04-database-operations.md) - **数据库操作场景**
  - SQL编写、批量操作、事务管理、性能优化
  - 适用文件：`**/*Mapper.xml`, `**/*Dao.java`, `**/*Service*.java`

- [backend/05-business-logic.md](./backend/05-business-logic.md) - **业务逻辑开发场景**
  - Service层开发、单一职责、方法行数≤30行、DRY原则
  - 适用文件：`**/*Service.java`, `**/*ServiceImpl.java`, `**/service/**/*.java`

- [backend/09-code-quality.md](./backend/09-code-quality.md) - **代码质量场景**
  - 命名规范、注释规范、工具类选择、禁止使用Date类
  - 适用文件：`**/*.java`

#### 前端规则
- [frontend/02-list-page-development.md](./frontend/02-list-page-development.md) - **列表页开发场景**
  - 查询区、按钮区、表格区布局、分页组件
  - 适用文件：`**/views/**/*.vue`, `**/pages/**/*.vue`

- [frontend/03-form-page-development.md](./frontend/03-form-page-development.md) - **表单页开发场景**
  - 表单布局、验证规则、提交处理
  - 适用文件：`**/views/**/*.vue`

- [frontend/04-component-development.md](./frontend/04-component-development.md) - **组件开发场景**
  - 组件拆分、命名规范、Props类型定义
  - 适用文件：`**/components/**/*.vue`

- [frontend/06-user-interaction.md](./frontend/06-user-interaction.md) - **用户交互场景**
  - Loading状态、错误处理、消息提示
  - 适用文件：`**/*.vue`, `**/*.ts`

- [frontend/07-code-quality.md](./frontend/07-code-quality.md) - **前端代码质量场景**
  - TypeScript类型定义、模板逻辑简化、命名规范
  - 适用文件：`**/*.vue`, `**/*.ts`

---

## 🎯 快速查找指南

### 按开发场景查找

| 场景 | 规则文件 |
|------|---------|
| **初始化Spring Boot项目** | backend/01-project-setup.md |
| **开发REST接口** | backend/02-api-development.md |
| **设计数据库表** | backend/03-database-design.md ⭐ |
| **编写SQL查询** | backend/04-database-operations.md |
| **开发Service业务逻辑** | backend/05-business-logic.md |
| **处理异常** | backend/06-exception-handling.md |
| **记录日志** | backend/07-logging.md |
| **防范XSS/SQL注入** | backend/08-security.md |
| **初始化Vue3项目** | frontend/01-project-setup.md |
| **开发列表页** | frontend/02-list-page-development.md |
| **开发表单页** | frontend/03-form-page-development.md |
| **开发组件** | frontend/04-component-development.md |
| **调整UI样式** | frontend/05-ui-styling.md |
| **处理用户交互** | frontend/06-user-interaction.md |

### 按技术栈查找

| 技术 | 规则文件 |
|------|---------|
| **Spring Boot** | backend/01-project-setup.md, backend/02-api-development.md |
| **MyBatis** | backend/03-database-design.md, backend/04-database-operations.md |
| **MySQL/Oracle** | backend/03-database-design.md |
| **Redis** | backend/08-security.md（缓存安全） |
| **Vue 3** | frontend/01-project-setup.md |
| **TypeScript** | frontend/01-project-setup.md, frontend/07-code-quality.md |
| **ElementPlus** | frontend/05-ui-styling.md |

---

## 💡 使用说明

### 对于AI代码生成

1. **P0级规则自动应用**：无需指定，所有代码生成时自动遵守
2. **P1级规则按文件匹配**：根据生成的文件路径自动应用对应规则
3. **场景式引导**：描述开发场景时，AI自动加载相关规则

**示例**：
```
用户：创建一个用户管理REST接口，包括增删改查
AI：自动应用以下规则：
  - backend/01-project-setup.md（P0）
  - backend/02-api-development.md（匹配*Controller.java）
  - backend/03-database-design.md（涉及表设计）
  - backend/06-exception-handling.md（P0）
  - backend/07-logging.md（P0）
  - backend/08-security.md（P0）
```

### 对于开发者

1. **项目初始化**：先阅读对应的01-project-setup.md
2. **开发过程**：按场景查找对应规则文件
3. **代码审查**：使用规则文件中的检查清单
4. **问题排查**：参考规则文件中的错误示例和正确示例

---

## 📋 规范覆盖清单

### 后端规范（53条规则）

| 类别 | 规则数 | 覆盖文件 |
|------|--------|---------|
| 海关平台特定 | 3条 | backend/01-project-setup.md |
| 架构与代码结构 | 17条 | backend/05-business-logic.md, backend/09-code-quality.md |
| 安全规范 | 15条 | backend/08-security.md |
| 异常处理 | 3条 | backend/06-exception-handling.md |
| 日志规范 | 3条 | backend/07-logging.md |
| 接口设计 | 3条 | backend/02-api-development.md |
| 数据库规范 | 9条 | backend/03-database-design.md, backend/04-database-operations.md |

### 前端规范（111条规则）

| 类别 | 规则数 | 覆盖文件 |
|------|--------|---------|
| 架构与技术栈 | 19条 | frontend/01-project-setup.md, frontend/07-code-quality.md |
| UI标准规范 | 47条 | frontend/05-ui-styling.md |
| 布局规范 | 13条 | frontend/02-list-page-development.md, frontend/03-form-page-development.md |
| 组件规范 | 10条 | frontend/04-component-development.md |
| 代码质量与安全 | 22条 | frontend/06-user-interaction.md, frontend/07-code-quality.md |

### 数据库设计规范（完整覆盖）

backend/03-database-design.md包含：
- ✅ 命名规范（表、字段、索引、其他对象）
- ✅ 表设计（主键、分区、必备字段、范式冗余、大对象、数据清理）
- ✅ 字段设计（数据类型、NULL属性、字段注释）
- ✅ 索引设计（合理建立索引、单列索引、组合索引）
- ✅ 约束设计（性能、扩展性、安全性）
- ✅ 设计文档要求（ER图、数据字典）

---

## 🔍 规则示例

### 指令式规范

```
✅ 使用CACP父依赖和核心依赖
✅ 方法行数限制在30行以内
✅ 数据库表必须包含REC_VERSION、REC_CREATE_TIME、REC_LAST_UPDATE_TIME
❌ 禁止使用Date类，使用LocalDateTime代替
```

### 场景式规范

```
## 场景：创建用户管理REST接口

当开发CRUD接口时：
- URL命名：使用小写+短横线，如 `/api/user-management`
- HTTP方法：GET查询、POST新增/修改/删除
- 删除和修改：必须携带rec_version实现乐观锁
- Controller层：仅处理请求校验和响应封装
- Service层：实现具体业务逻辑
```

### 约束式规范

```
❌ 禁止循环操作数据库
错误示例：
  for (User user : users) {
    userDao.insert(user); // 每次循环都访问数据库
  }

正确示例：
  userDao.batchInsert(users); // 使用批量操作
```

---

## 🎨 规范特色

1. **完整性** - 164条规则全覆盖，无遗漏
2. **场景化** - 按开发场景组织，易查找
3. **实战性** - 提供正确/错误代码示例
4. **可检查** - 每个规则文件包含检查清单
5. **分级管理** - P0/P1优先级，自动/按需应用
6. **跨平台** - Windows和Linux兼容

---

## 📖 相关文档

- **数据库设计规范**：backend/03-database-design.md
- **海关开发规范源文件**：caps/backend_rules修订版.xlsx, caps/frontend_rules修订版.xlsx
- **二次开发记录**：docs/二次开发记录.md（执行后更新）

---

## 🔄 版本信息

- **创建日期**：2025-11-10
- **规则来源**：海关信息系统开发规范（后端53条+前端111条+数据库设计规范）
- **适用范围**：海关信息化应用集中式事务型系统
- **维护方式**：通过Git版本管理

---

**使用建议**：AI代码生成时，无需手动指定规则文件，系统会根据场景和文件类型自动加载适用规则。开发者可随时查阅规则文件了解规范要求。
