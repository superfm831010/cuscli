---
description: "Package命名规范：cn.gov.customs+系统名+子项目名"
globs: ["**/*.java"]
alwaysApply: true
---

# Package 命名规范

## 规范说明

Package 的名字全部采用小写字母，命名规则如下：

```
"cn.gov.customs." + 工程名(可选) + "." + 项目缩写/子项目名
```

## 强制要求

1. 【强制】Package 统一以 `cn.gov.customs` 开头
2. 【强制】所有字母必须小写
3. 【强制】使用点号（.）分隔，不使用下划线或中划线
4. 【强制】项目缩写应当采用4位字母缩写

## 示例

### ✅ 正确示例

```java
package cn.gov.customs.hj2016.ems;
package cn.gov.customs.h2018.heps;
package cn.gov.customs.h2018.hrec;
package cn.gov.customs.cacp.core;
package cn.gov.customs.h2018.tmc.sample;
```

### ❌ 错误示例

```java
package com.customs.hj2016.ems;      // 错误：不是cn.gov.customs开头
package cn.gov.customs.HJ2016.EMS;   // 错误：使用了大写字母
package cn.gov.customs.hj2016_ems;   // 错误：使用了下划线
package cn.Customs.hj2016.ems;       // 错误：Customs首字母大写
```

## 组织结构建议

典型的包结构组织方式：

```
cn.gov.customs.{工程名}.{项目缩写}
    ├── config          # 配置类
    ├── constant        # 常量定义
    ├── controller      # 控制器
    ├── dao             # 数据访问层
    ├── pojo            # 实体类
    ├── service         # 服务层
    │   └── impl        # 服务实现
    ├── proxy           # 代理类
    ├── exception       # 异常类
    └── util            # 工具类
```

## 适用场景

- 所有Java项目的包命名
- 微服务项目的包结构设计
- SDK组件的包命名
- 公共库的包命名

## 相关规范

- 参见 [类命名规范](./class-naming.md)
- 参见 [微服务命名规范](./microservice-naming.md)

## 来源文档

- 《海关应用云平台开发规范》- 00-cacp-spec.md 第5.2节
- 《Java开发规范》- 05-java-spec.md 第6节
