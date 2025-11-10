---
description: "类命名规范：Pascal命名方式"
globs: ["**/*.java"]
alwaysApply: true
---

# 类命名规范

## 规范说明

Java 类的命名采用 **Pascal** 命名方式，即每个单词的首字母都大写。

## 强制要求

1. 【强制】类名采用 Pascal 命名方式（每个单词首字母大写）
2. 【强制】类名使用名词或名词短语
3. 【强制】接口命名与类命名一致，采用 Pascal 命名方式
4. 【强制】抽象类命名使用 Abstract 或 Base 开头
5. 【强制】异常类命名使用 Exception 结尾
6. 【强制】测试类命名以它要测试的类的名称开始，以 Test 结尾
7. 【强制】枚举类名带上 Enum 后缀

## 命名模式

### 普通类

```
{业务含义}{类型}
```

示例：
```java
DataFile          // 数据文件类
InfoParser        // 信息解析器类
EntryHead         // 报关单表头类
UserService       // 用户服务类
CountryRepository // 国家仓储类
```

### 接口与实现类

**接口命名**：
```java
public interface EntryService {
    // ...
}
```

**实现类命名**（两种方式）：
```java
// 方式1：接口名 + Impl
public class EntryServiceImpl implements EntryService {
    // ...
}

// 方式2：有意义的类名称
public class DefaultEntryService implements EntryService {
    // ...
}
```

### 抽象类

```java
public abstract class AbstractEntity {
    // ...
}

public abstract class BaseController {
    // ...
}
```

### 异常类

```java
public class ValidationException extends RuntimeException {
    // ...
}

public class BusinessException extends Exception {
    // ...
}
```

### 测试类

```java
// 被测试的类
public class ArticleService {
    // ...
}

// 测试类
public class ArticleServiceTest {
    // ...
}
```

### 枚举类

```java
public enum StatusEnum {
    PENDING,
    APPROVED,
    REJECTED;
}

public enum OrderTypeEnum {
    IMPORT,
    EXPORT,
    TRANSIT;
}
```

## 设计模式体现

【推荐】如果使用了设计模式，在命名时需体现出具体模式：

```java
public class OrderFactory {          // 工厂模式
    // ...
}

public class LoginProxy {            // 代理模式
    // ...
}

public class ResourceObserver {      // 观察者模式
    // ...
}

public class SingletonManager {      // 单例模式
    // ...
}

public class StrategyContext {       // 策略模式
    // ...
}
```

## 示例

### ✅ 正确示例

```java
// 实体类
public class Entry {
    // ...
}

public class EntryList {
    // ...
}

// 控制器
public class CountryController {
    // ...
}

// 服务接口
public interface CountryService {
    // ...
}

// 服务实现
public class CountryServiceImpl implements CountryService {
    // ...
}

// 数据访问层
public class EntryHeadRepository {
    // ...
}

// 抽象类
public abstract class BaseEntity {
    // ...
}

// 异常类
public class ValidationException extends RuntimeException {
    // ...
}

// 工具类
public class DateUtils {
    // ...
}

// 常量类
public class CacheConsts {
    // ...
}

// 枚举类
public enum EntryStatusEnum {
    PENDING,
    APPROVED,
    REJECTED;
}
```

### ❌ 错误示例

```java
public class entryHead {              // 错误：首字母小写
    // ...
}

public class Entry_List {             // 错误：使用了下划线
    // ...
}

public class getCountry {             // 错误：使用了动词开头，应该用于方法命名
    // ...
}

public class CE {                     // 错误：完全不规范的缩写，望文不知义
    // ...
}

public class condi {                  // 错误：随意缩写，应为 Condition
    // ...
}
```

## 常用类名后缀

| 后缀 | 含义 | 示例 |
|-----|-----|------|
| Controller | 控制器 | EntryController |
| Service | 服务层 | EntryService |
| ServiceImpl | 服务实现 | EntryServiceImpl |
| Repository | 数据访问层 | EntryRepository |
| Dao | 数据访问对象 | EntryDao |
| VO | 视图对象 | EntryVO |
| DTO | 数据传输对象 | EntryDTO |
| PO | 持久化对象 | EntryPO |
| Entity | 实体 | EntryEntity |
| Exception | 异常 | ValidationException |
| Enum | 枚举 | StatusEnum |
| Utils | 工具类 | DateUtils |
| Consts | 常量类 | CacheConsts |
| Factory | 工厂 | EntryFactory |
| Builder | 建造者 | EntryBuilder |
| Manager | 管理器 | CacheManager |

## 注意事项

1. 【强制】杜绝完全不规范的缩写，避免望文不知义
   - 反例：`AbstractClass` 缩写成 `AbsClass`
   - 反例：`condition` 缩写成 `condi`

2. 【推荐】类名应该清晰表达其职责和用途
   - 好例：`UserAuthenticationService`
   - 差例：`UserAS`

3. 【推荐】避免使用过长的类名（建议不超过30个字符）
   - 好例：`EntryDeclarationService`
   - 差例：`EntryHeadAndListDeclarationValidationService`

## 适用场景

- 所有Java类的命名
- 接口定义
- 抽象类定义
- 异常类定义
- 枚举类定义
- 测试类定义

## 相关规范

- 参见 [方法与变量命名规范](./method-variable-naming.md)
- 参见 [Package命名规范](./package-naming.md)

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第6节
- 《海关应用云平台开发规范》- 00-cacp-spec.md 第5.2节
