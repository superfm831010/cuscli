---
description: "海关平台特定技术规范，包括CACP父依赖、核心依赖和数据源配置要求"
globs:
  - "**/pom.xml"
  - "**/build.gradle"
  - "**/requirements.txt"
alwaysApply: true
---

# 海关特定技术规范

## 规则条款

### 1. 项目父依赖规范

- **backend_001**: 项目父依赖应为cacp-spring-boot-parent或基于该依赖的自定义项目
- 来源：backend_rules修订版.xlsx 第2行
- 说明：确保项目继承正确的父级依赖，以统一技术栈和依赖版本管理

### 2. 项目核心依赖规范

- **backend_002**: 项目核心依赖为cacp-service-spring-boot-starter或cacp-job-spring-boot-starter两者之一
- 来源：backend_rules修订版.xlsx 第3行
- 说明：根据项目类型选择正确的核心依赖，service类项目使用cacp-service-spring-boot-starter，job类项目使用cacp-job-spring-boot-starter

### 3. 数据源依赖规范

- **backend_003**: 项目如果使用数据源，则必须依赖cacp-datasource-spring-boot-starter
- 来源：backend_rules修订版.xlsx 第4行
- 说明：统一使用平台提供的数据源starter，确保数据源配置的一致性和可管理性

## 适用场景

本规则适用于所有海关信息化应用项目，是强制性规范，必须严格遵守。
