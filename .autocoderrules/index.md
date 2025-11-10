---
description: "海关应用云平台开发规范规则索引"
alwaysApply: true
---

# 海关应用云平台开发规范规则索引

本目录包含海关应用云平台的全套开发规范规则，基于《海关应用云平台开发规范文档集合》整理。

## 规则分类概览

### 00-命名规范类（Always Applied）

这些规则总是生效，确保代码命名的一致性：

1. [Package命名规范](./00-naming/package-naming.md) - Package统一采用"cn.gov.customs."+系统名格式
2. [URL命名规范](./00-naming/url-naming.md) - URL统一使用小写字母和中划线
3. [微服务命名规范](./00-naming/microservice-naming.md) - 格式为"项目缩写-主要功能-服务类型"
4. [类命名规范](./00-naming/class-naming.md) - Pascal命名方式
5. [方法与变量命名规范](./00-naming/method-variable-naming.md) - Camel命名方式

### 01-数据库规范类（Mixed）

适用于数据库相关开发：

6. [数据库禁止事项](./01-database/database-constraints.md) ⭐ **Always Applied** - **禁止外键、触发器、DBLINK**
7. [数据库设计规范](./01-database/database-design.md) - 字段类型、索引、约束设计
8. [数据库命名规范](./01-database/database-naming.md) - 表名、字段名、索引命名规则
9. [必需字段规范](./01-database/database-fields.md) - REC_VERSION, REC_CREATE_TIME等必需字段

### 02-Java开发规范类（Mixed）

Java开发的核心规范：

10. [Java基础规范](./02-java/java-basic.md) ⭐ **Always Applied** - JDK8+, 禁止Date类等基础要求
11. [Java代码格式规范](./02-java/java-formatting.md) - 缩进、空格、换行规则
12. [异常处理规范](./02-java/java-exception.md) - 异常抛出和捕获规则
13. [事务处理规范](./02-java/java-transaction.md) - 使用注解，避免XML配置
14. [日志记录规范](./02-java/java-logging.md) - 使用Slf4j，@Slf4j注解

### 03-前端开发规范类（Conditional）

前端开发规范：

15. [JavaScript基础规范](./03-frontend/js-basic.md) - ES6+, 驼峰命名等
16. [Vue开发规范](./03-frontend/vue-spec.md) - 组件、指令使用规则
17. [UI界面规范](./03-frontend/ui-spec.md) - ElementUI栅格、图标使用

### 04-平台集成规范类（Conditional）

海关平台系统集成规范：

18. [H4A集成规范](./04-platform/h4a-integration.md) - 身份认证、授权管理
19. [HEPS事件通知规范](./04-platform/heps-usage.md) - 事件通知场景和限制
20. [HEAI数据交换规范](./04-platform/heai-exchange.md) - 结构化/非结构化数据交换
21. [统一门户集成规范](./04-platform/portal-integration.md) - 署级应用须集成统一门户

### 05-数据存储规范类（Conditional）

文件和数据交换规范：

22. [文件存储规范](./05-data/file-storage.md) - SMB/NFS协议，文件命名，目录划分
23. [结构化报文规范](./05-data/structural-exchange.md) - W3C报文设计规范
24. [非结构化报文规范](./05-data/unstructural-exchange.md) - 非结构化数据交换格式

### 06-项目管理规范类（Conditional）

应用项目管理规范：

25. [应用备案规范](./06-management/application-registration.md) - 4位项目缩写规则
26. [YML配置规范](./06-management/yml-config.md) - 自定义配置统一在项目短编码下
27. [jar包发布规范](./06-management/jar-deploy.md) - jar包发布流程和要求

## 快速使用指南

### 对于新项目

1. 首先阅读 **Always Applied** 标记的规则（必须遵守）
2. 根据技术栈选择对应的规范类别
3. 关注数据库、平台集成等特定场景的规范

### 对于现有项目

1. 优先检查命名规范和Java基础规范
2. 逐步迁移到符合规范的实现
3. 特别注意禁止事项（外键、触发器等）

## 重要禁止事项速查

### 数据库

- ❌ **禁止外键**
- ❌ **禁止触发器**
- ❌ **禁止DBLINK**
- ❌ **禁止程序执行DDL**
- ❌ **禁止使用BLOB/CLOB/TEXT大字段**（除非严格评估）

### Java

- ❌ **禁止使用 java.util.Date**（使用LocalDate/LocalDateTime）
- ❌ **禁止随意引入第三方库**
- ❌ **禁止完全不规范的缩写**
- ❌ **禁止使用游标**
- ❌ **禁止直接使用System.out输出日志**

### 前端

- ❌ **禁止提交node_modules和dist目录**
- ❌ **禁止使用ElementUI图标组件**（使用Font Awesome）

## 开发基础要求

### 技术栈

- **后端**: Java (JDK8+) + Spring Boot + 平台SDK
- **前端**: Vue2 + ElementUI + axios + 平台脚手架
- **数据库**: Oracle/SQL Server
- **架构**: 前后端分离 + 微服务

### 命名约定

- **Package**: `cn.gov.customs.系统名.子项目名`
- **URL**: 小写字母+中划线分割
- **微服务**: `项目缩写-功能描述-服务类型`
- **类**: Pascal命名（DataFile, InfoParser）
- **方法/变量**: Camel命名（checkEntry, inputFileSize）

### 必需技术字段

所有数据表必须包含以下字段：

- **REC_VERSION**: 整数，默认0，记录版本号
- **REC_CREATE_TIME**: 带时间的日期，记录创建时间
- **REC_LAST_UPDATE_TIME**: 带时间的日期，最后更新时间

## 规范优先级说明

- **【强制】**: 必须满足，违反是原则性错误
- **【推荐】**: 在特定条件下可忽视，但需双方约定
- **【参考】**: 可选，需项目管理人员约定

## 更新日志

- **2025-11-10**: 基于 cacp-docs 初始化规则文件
