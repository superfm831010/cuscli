---
description: "海关开发规范规则索引，提供规则体系总览和使用指南"
alwaysApply: true
---

# 海关开发规范规则索引

## 规则体系概述

本规则体系基于海关总署开发规范，来源于caps目录下的规范文档：
- backend_rules修订版.xlsx（52条后端规则）
- frontend_rules修订版.xlsx（110条前端规则）
- 海关集中式事务型数据库设计规范.docx

规则分为后端和前端两大类别，涵盖架构、安全、代码质量、UI设计等多个维度。

## 后端规则文件（7个）

### 总是应用的规则（alwaysApply: true）

#### 1. backend/customs-specific.md - 海关特定技术规范
- **用途**: CACP父依赖、核心依赖、数据源配置要求
- **规则数量**: 3条（backend_001-003）
- **适用**: 所有海关信息化应用项目
- **依据**: backend_rules修订版.xlsx 第2-4行

#### 2. backend/architecture.md - 架构和代码结构规范
- **用途**: 项目结构、代码复杂度、设计原则、编码规范
- **规则数量**: 17条（backend_004, 007-022）
- **适用**: 所有Java/Python后端代码
- **依据**: backend_rules修订版.xlsx 第5-21行

#### 3. backend/security.md - 安全规范
- **用途**: XSS防护、空指针防护、敏感信息保护、缓存安全
- **规则数量**: 15条（backend_023, 027-036, 060-063）
- **适用**: 所有后端代码
- **依据**: backend_rules修订版.xlsx 第22行, 26-36行, 50-53行

#### 4. backend/exception.md - 异常处理规范
- **用途**: 异常封装、日志记录
- **规则数量**: 3条（backend_024-026）
- **适用**: 所有异常处理场景
- **依据**: backend_rules修订版.xlsx 第23-25行

#### 5. backend/logging.md - 日志规范
- **用途**: 日志级别、内容要求
- **规则数量**: 3条（backend_037-039）
- **适用**: 所有日志记录场景
- **依据**: backend_rules修订版.xlsx 第36-38行

### 条件应用的规则（alwaysApply: false）

#### 6. backend/api.md - 接口设计规范
- **用途**: URL命名、HTTP方法、参数设计
- **规则数量**: 3条（backend_040-042）
- **适用**: Web服务接口开发
- **依据**: backend_rules修订版.xlsx 第39-41行

#### 7. backend/database.md - 数据库规范
- **用途**: 表设计、SQL编写、事务管理
- **规则数量**: 8条规则 + 数据库设计规范要点
- **适用**: 涉及数据库操作的代码
- **依据**: backend_rules修订版.xlsx 第42-49行 + 海关集中式事务型数据库设计规范.docx

## 前端规则文件（4个）

### 总是应用的规则（alwaysApply: true）

#### 1. frontend/architecture.md - 架构和代码结构规范
- **用途**: 统一入口、技术栈、组件设计、异常处理、安全规范
- **规则数量**: 38条（frontend_001-019, 087-109）
- **适用**: 所有Vue前端项目
- **依据**: frontend_rules修订版.xlsx 第2-20行, 88-109行

#### 2. frontend/ui-standards.md - UI标准规范
- **用途**: Loading效果、圆角、阴影、字体、颜色（海关蓝、政务红）
- **规则数量**: 47条（frontend_020-022, 027-070）
- **适用**: 所有前端UI开发
- **依据**: frontend_rules修订版.xlsx 第21-23行, 28-71行

### 条件应用的规则（alwaysApply: false）

#### 3. frontend/layout.md - 布局规范
- **用途**: 查询区、按钮区、表格区布局，边距规范
- **规则数量**: 13条（frontend_023-026, 071-078, 086）
- **适用**: 列表页、详情页、表单页布局
- **依据**: frontend_rules修订版.xlsx 第24-27行, 72-79行, 87行

#### 4. frontend/component.md - 组件规范
- **用途**: 按钮设计、图片资源、图标、空状态
- **规则数量**: 10条（frontend_079-086, 110-112）
- **适用**: 列表、表格、详情页组件开发
- **依据**: frontend_rules修订版.xlsx 第80-87行, 109-112行

## 规则优先级说明

### P0级（必须遵守，alwaysApply: true）

**后端：**
1. backend/customs-specific.md - 海关平台强制要求
2. backend/security.md - 安全规范
3. backend/architecture.md - 架构基础
4. backend/exception.md - 异常处理
5. backend/logging.md - 日志规范

**前端：**
1. frontend/architecture.md - 架构和代码质量基础
2. frontend/ui-standards.md - 视觉统一性

### P1级（按需应用，alwaysApply: false）

**后端：**
1. backend/api.md - 仅Web服务项目
2. backend/database.md - 仅数据库操作场景

**前端：**
1. frontend/layout.md - 仅页面布局设计
2. frontend/component.md - 仅组件开发场景

## 使用建议

### 新项目

1. **后端项目**：
   - 必须遵守：customs-specific, security, architecture, exception, logging
   - 根据类型选择：Web服务加载api.md，数据库应用加载database.md

2. **前端项目**：
   - 必须遵守：architecture, ui-standards
   - 根据开发内容选择：布局设计加载layout.md，组件开发加载component.md

### 现有项目改造

1. 优先应用P0级规则（alwaysApply: true）
2. 逐步完善P1级规则（alwaysApply: false）
3. 重点关注安全规范和海关特定规范

### Vibecoding使用提示

在使用auto-coder进行vibecoding（AI代码生成）时：

1. **后端开发**：
   - Java项目必须使用CACP平台依赖
   - 注意安全编码（SQL注入、XSS、空指针等）
   - 遵循分层架构（Controller-Service-DAO）
   - 使用统一异常处理和日志记录

2. **前端开发**：
   - 使用Vue3 + TypeScript + ElementPlus技术栈
   - 严格遵守海关蓝/政务红色系规范
   - 字体大小按标准版/关怀版区分
   - 边距遵循4的倍数（外边距）和5的倍数（内边距）

3. **数据库设计**：
   - 表名包含应用简称，遵循命名规范
   - 必备字段：REC_VERSION、REC_CREATE_TIME、REC_LAST_UPDATE_TIME
   - 主键有业务含义
   - 数据量大的表考虑分区设计

## 规则文件更新

本规则体系基于以下文档创建：
- backend_rules修订版.xlsx（52条规则）
- frontend_rules修订版.xlsx（110条规则）
- 海关集中式事务型数据库设计规范.docx

如需更新规则，请：
1. 修改caps目录下的源文档
2. 重新提取规则条款
3. 更新对应的.md规则文件
4. 更新本index.md索引

## 联系方式

规则相关问题请参考：
- 海关总署开发规范文档
- 技术中心架构组
- 项目组技术负责人
