---
description: "后端异常处理规范，包括异常封装、日志记录等"
globs:
  - "**/*.java"
  - "**/*.py"
alwaysApply: true
---

# 后端异常处理规范

## 规则条款

### 1. 统一异常封装

- **backend_024**: 异常捕获后需处理为自定义封装（BizException），使用统一错误标识（实现ExceptionCodeMessage的异常编码枚举类）
- 来源：backend_rules修订版.xlsx 第23行
- 说明：统一异常处理机制，便于问题排查和用户提示

### 2. 禁止printStackTrace

- **backend_025**: try-catch异常后禁止使用e.printStackTrace();方式输出且没有其他处理（防止异常日志丢失）
- 来源：backend_rules修订版.xlsx 第24行
- 说明：printStackTrace输出到标准错误流，无法被日志系统捕获

### 3. 异常日志记录规范

- **backend_026**: 异常捕获后如需重新抛出自定义业务异常，则不必额外使用log.error记录（关级系统除外），直接throw new BizException(...)即可；如不再抛出则应使用log.error记录
- 来源：backend_rules修订版.xlsx 第25行
- 说明：避免重复记录日志，统一异常处理机制会记录最终的异常

## 适用场景

本规则适用于所有后端异常处理场景，确保异常信息完整记录和统一处理。
