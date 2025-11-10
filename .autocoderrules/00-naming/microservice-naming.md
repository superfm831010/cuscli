---
description: "微服务命名规范：项目缩写-功能描述-服务类型"
globs: ["**/pom.xml", "**/package.json", "**/Dockerfile"]
alwaysApply: true
---

# 微服务命名规范

## 规范说明

微服务命名分为三段，格式为：`项目缩写` + `-` + `主要功能描述` + `-` + `服务类型`

## 强制要求

1. 【强制】微服务名称采用三段式命名
2. 【强制】使用中划线（-）分隔，不使用下划线（_）
3. 【强制】全部使用小写字母
4. 【强制】项目缩写应当采用4位字母缩写
5. 【强制】功能描述应简明扼要
6. 【强制】服务类型必须是：web、service、job 之一

## 服务类型说明

- **web**: 前端网页项目
- **service**: 后台服务，为前端或其他服务提供业务处理逻辑
- **job**: 后台任务，通过定时驱动进行工作，不能被其他服务或前端网页调用，独立运行

## 示例

### ✅ 正确示例

```
heps-api-service          # HEPS系统的API服务
hrec-main-service         # 放行系统的主服务
heai-process-job          # 数据交换系统的处理任务
hace-audit-service        # 电子审单系统的审核服务
hj2016-ems-web            # HJ2016工程的EMS前端
h2018-dict-service        # H2018工程的字典服务
cacp-core-service         # 应用云平台核心服务
hgis-map-web              # 地理信息系统的地图前端
```

### ❌ 错误示例

```
HEPS_API_SERVICE          # 错误：使用了大写和下划线
hrec.main.service         # 错误：使用了点号分隔
HeaiProcessJob            # 错误：使用了驼峰命名
heps-service              # 错误：缺少功能描述
api-service               # 错误：缺少项目缩写
hrec-main                 # 错误：缺少服务类型
```

## 项目缩写规则

项目缩写应当采用4位字母缩写，在海关系统内部应唯一：

```
H2018  -> h2018
HREC   -> hrec  (放行)
HACE   -> hace  (电子审)
HEPS   -> heps  (事件通知)
HEAI   -> heai  (数据交换)
HJ2016 -> hj2016
HB2020 -> hb2020
CACP   -> cacp  (应用云平台)
```

对于H2010系统内相关系统升级时，子项目采用`H`+原3位系统缩写的形式：

```
原系统缩写：MFT
新项目缩写：HMFT -> hmft
```

## 微服务划分建议

1. 【推荐】一个中型应用项目建立微服务在5个之内
2. 【推荐】一般1个前端页面(web)，3-4个后端服务(service)
3. 【推荐】可根据情况建立1-2个后台job服务
4. 【推荐】微服务应功能相对独立和完整，与其他微服务边界清晰
5. 【强制】禁止微服务之间产生循环依赖

### 典型微服务结构示例

一个标准的应用项目微服务组成：

```
hrec-main-web             # 前端页面
hrec-core-service         # 核心业务服务
hrec-dict-service         # 字典服务
hrec-workflow-service     # 工作流服务
hrec-sync-job             # 数据同步任务
```

## 适用场景

- 微服务项目命名
- Docker镜像命名
- Git仓库命名
- 服务注册发现标识

## 目录结构示例

```
hrec-main-service/
├── pom.xml                           # artifactId应为 hrec-main-service
├── Dockerfile
├── src/
│   └── main/
│       ├── java/
│       │   └── cn/gov/customs/h2018/hrec/
│       └── resources/
│           └── application.yml       # spring.application.name: hrec-main-service
```

## 相关规范

- 参见 [Package命名规范](./package-naming.md)
- 参见 [URL命名规范](./url-naming.md)
- 参见 [应用备案规范](../06-management/application-registration.md)

## 来源文档

- 《海关应用云平台开发规范》- 00-cacp-spec.md 第2.1节、第3节
