---
description: "后端接口设计规范，包括URL命名、HTTP方法、参数设计等"
globs:
  - "**/*.java"
  - "**/*.py"
  - "**/controller/**"
  - "**/api/**"
alwaysApply: false
---

# 后端接口设计规范

## 规则条款

### 1. URL命名规范

- **backend_040**: url路径名称要求：全小写、不使用驼峰、使用"-"连接（/get-user）
- 来源：backend_rules修订版.xlsx 第39行
- 说明：统一的URL命名风格，符合RESTful规范

### 2. HTTP方法规范

- **backend_041**: Controller接口中推荐使用GET和POST请求方式，尽量不用PUT和DELETE
- 来源：backend_rules修订版.xlsx 第40行
- 说明：简化接口设计，提高兼容性

### 3. 接口参数简洁

- **backend_042**: 接口请求参数只定义业务所需的字段，避免冗余参数
- 来源：backend_rules修订版.xlsx 第41行
- 说明：精简的接口参数便于理解和使用

## 适用场景

本规则适用于Web服务接口开发，特别是RESTful API设计。
