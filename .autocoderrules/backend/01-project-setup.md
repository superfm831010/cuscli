---
title: "项目搭建场景"
description: "Spring Boot项目初始化、依赖配置、目录结构规范"
keywords:
  - Spring Boot
  - Maven
  - 项目初始化
  - CACP
  - 依赖管理
tags:
  - 项目搭建
  - 初始化配置
globs:
  - "**/pom.xml"
  - "**/build.gradle"
  - "**/application.yml"
  - "**/application.properties"
alwaysApply: true
priority: high
---

# 项目搭建场景规范

## 场景概述

当创建新的Spring Boot项目或配置现有项目时，遵循海关统一的项目结构和依赖管理规范。

## 核心规则

### ✅ 强制使用CACP父依赖

**指令**：所有海关Spring Boot项目必须使用CACP（海关应用统一平台）父依赖。

```xml
<parent>
    <groupId>cn.gov.customs.cacp</groupId>
    <artifactId>cacp-spring-boot-parent</artifactId>
    <version>${cacp.version}</version>
</parent>
```

**原因**：
- 统一技术栈版本，避免版本冲突
- 集成海关标准组件和配置
- 简化依赖管理

---

### ✅ 使用CACP核心依赖

**指令**：根据项目需求引入CACP核心依赖模块。

```xml
<dependency>
    <groupId>cn.gov.customs.cacp</groupId>
    <artifactId>cacp-spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>cn.gov.customs.cacp</groupId>
    <artifactId>cacp-spring-boot-starter-data</artifactId>
</dependency>
```

**常用模块**：
- `cacp-spring-boot-starter-web` - Web开发基础
- `cacp-spring-boot-starter-data` - 数据访问
- `cacp-spring-boot-starter-security` - 安全认证
- `cacp-spring-boot-starter-redis` - Redis缓存

---

### ✅ 配置数据源依赖

**指令**：使用CACP提供的数据源管理组件。

```xml
<dependency>
    <groupId>cn.gov.customs.cacp</groupId>
    <artifactId>cacp-datasource</artifactId>
</dependency>
```

**场景示例**：
- 多数据源配置时，使用CACP提供的动态数据源路由
- 数据库连接池统一使用HikariCP
- 事务管理由CACP统一配置

---

### ✅ 遵循标准目录结构

**指令**：项目包路径必须以 `cn.gov.customs.` 开头，后跟业务域或应用简称。

```
cn.gov.customs.{应用简称}
├── controller      # 控制器层
├── service         # 服务层
│   └── impl       # 服务实现
├── dao            # 数据访问层（MyBatis Mapper接口）
├── entity         # 实体类
├── dto            # 数据传输对象
├── vo             # 视图对象
├── config         # 配置类
├── exception      # 自定义异常
├── util           # 工具类
└── constant       # 常量定义
```

**示例**：
- TIR运输系统：`cn.gov.customs.tir.*`
- 舱单管理系统：`cn.gov.customs.manifest.*`

---

### ✅ 配置文件规范

**指令**：使用YAML格式配置文件，环境配置分离。

```yaml
# application.yml - 主配置文件
spring:
  profiles:
    active: @profileActive@  # Maven profile变量注入
  application:
    name: ${APP_NAME:customs-app}

# application-dev.yml - 开发环境
# application-test.yml - 测试环境
# application-prod.yml - 生产环境
```

**约束**：
- ❌ 禁止在代码中硬编码环境相关配置
- ❌ 禁止将敏感信息（密码、密钥）明文存储在配置文件中
- ✅ 使用环境变量 `ENV {{VARIABLE_NAME}}` 注入敏感配置

---

### ✅ 字符集统一UTF-8

**指令**：项目字符集统一使用UTF-8编码。

```xml
<properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
    <java.version>1.8</java.version>
</properties>
```

---

## 场景实战

### 场景1：初始化新项目

**用户需求**：创建一个用户管理服务

**AI应生成**：
1. 使用CACP父依赖的pom.xml
2. 标准目录结构：`cn.gov.customs.usermgmt.*`
3. 引入web、data、security starter
4. 创建application.yml with profiles
5. 配置HikariCP数据源

### 场景2：多模块项目搭建

**用户需求**：创建包含API、Service、DAO三个模块的项目

**AI应生成**：
```
customs-app-parent/
├── pom.xml (parent)
├── customs-app-api/       # 对外接口模块
├── customs-app-service/   # 业务逻辑模块
└── customs-app-dao/       # 数据访问模块
```

每个模块都遵循 `cn.gov.customs.app.*` 包结构。

---

## 严格禁止的做法

### ❌ 禁止使用非标准父依赖

```xml
<!-- 错误示例 -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
</parent>
```

**原因**：绕过海关统一技术管控，导致版本不一致和潜在安全风险。

---

### ❌ 禁止使用汉语拼音命名

```java
// 错误示例
package cn.gov.customs.yonghu;  // ❌ 拼音
package cn.gov.customs.yhgl;    // ❌ 拼音首字母

// 正确示例
package cn.gov.customs.user;         // ✅ 标准英文
package cn.gov.customs.usermgmt;     // ✅ 标准英文缩写
```

---

### ❌ 禁止混乱的包结构

```java
// 错误示例：包名不以cn.gov.customs开头
package com.example.myapp;  // ❌

// 错误示例：包名包含特殊字符
package cn.gov.customs.user-mgmt;  // ❌ 包名不能有短横线

// 正确示例
package cn.gov.customs.usermgmt;   // ✅
```

---

## 检查清单

项目搭建完成后，检查以下事项：

- [ ] pom.xml中已配置CACP父依赖
- [ ] 引入了必要的CACP核心依赖
- [ ] 包路径以 `cn.gov.customs.` 开头
- [ ] 目录结构符合标准规范
- [ ] 配置文件使用YAML格式
- [ ] 字符集设置为UTF-8
- [ ] 环境配置已分离（dev/test/prod）
- [ ] 敏感信息使用环境变量注入
- [ ] 项目名称符合命名规范（小写+短横线）

---

## 相关规则

- 参见 [02-api-development.md](./02-api-development.md) 了解API接口开发规范
- 参见 [03-database-design.md](./03-database-design.md) 了解数据库设计规范
- 参见 [08-security.md](./08-security.md) 了解安全配置要求
