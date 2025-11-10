---
description: "异常处理规范：统一异常类，proper处理方式"
globs: ["**/*.java"]
alwaysApply: false
---

# Java 异常处理规范

## 标准异常类

1. 【强制】请在common模块中创建一个标准异常

```java
package cn.gov.customs.{工程名}.{模块名}.common.exception;

public class BaseException extends RuntimeException {
    private String errorCode;

    public BaseException(String message) {
        super(message);
    }

    public BaseException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public BaseException(String message, Throwable cause) {
        super(message, cause);
    }

    public String getErrorCode() {
        return errorCode;
    }
}
```

2. 【强制】controller的异常统一抛出标准异常或继承其的子类异常
3. 【强制】由框架统一对标准返回值或者异常进行格式化

## 异常处理原则

### 不使用异常做流程控制

【推荐】尽量不要使用异常来做流程控制。

```java
// ❌ 错误：用异常控制流程
try {
    String value = map.get(key);
    return value.toUpperCase();
} catch (NullPointerException e) {
    return "DEFAULT";
}

// ✅ 正确：用if判断
String value = map.get(key);
return value != null ? value.toUpperCase() : "DEFAULT";
```

### 捕获异常后必须处理

【强制】捕获异常之后禁止不做处理而直接抛弃，如果不想处理应该将异常抛给调用者。

```java
// ❌ 错误：吞掉异常
try {
    processEntry(entry);
} catch (Exception e) {
    // 什么也不做
}

// ✅ 正确：记录日志并抛出
try {
    processEntry(entry);
} catch (Exception e) {
    log.error("处理失败", e);
    throw new BusinessException("处理失败", e);
}
```

### 分类捕获异常

【强制】对代码进行分类，分为不同的try-catch。

```java
// ✅ 正确：分类捕获
try {
    // 数据库操作
    entry = entryRepository.findById(id);
} catch (DataAccessException e) {
    log.error("数据库查询失败", e);
    throw new DatabaseException("查询失败", e);
}

try {
    // 外部接口调用
    response = httpClient.call(url);
} catch (IOException e) {
    log.error("接口调用失败", e);
    throw new RemoteException("接口调用失败", e);
}
```

### 记录上下文信息

【强制】在抛出自定义异常时，需要记录上下文的关键信息。

```java
// ✅ 正确：包含上下文信息
try {
    // 业务逻辑
} catch (Exception e) {
    log.error("保存报关单失败, entryNo: {}, customsCode: {}",
              entry.getEntryNo(), entry.getCustomsCode(), e);
    throw new BusinessException("保存失败: " + entry.getEntryNo(), e);
}
```

## try-catch-finally规范

### finally中关闭资源

【强制】finally中必须对资源进行关闭。

```java
// ✅ 推荐：使用try-with-resources
try (InputStream in = new FileInputStream(file);
     OutputStream out = new FileOutputStream(target)) {
    // 使用资源
} catch (IOException e) {
    log.error("文件操作失败", e);
}

// 传统方式
InputStream in = null;
try {
    in = new FileInputStream(file);
    // 使用资源
} catch (IOException e) {
    log.error("文件操作失败", e);
} finally {
    if (in != null) {
        try {
            in.close();
        } catch (IOException e) {
            log.error("关闭流失败", e);
        }
    }
}
```

### finally中不要return

【强制】不要在finally中return。

```java
// ❌ 错误：finally中return
public String test() {
    try {
        return "try";
    } finally {
        return "finally";  // 错误！会覆盖try中的返回值
    }
}
```

### 事务回滚

【强制】如果事务放在了try中，必须在catch中回滚事务。

```java
@Service
public class EntryServiceImpl {

    @Transactional
    public void saveEntry(Entry entry) {
        try {
            entryRepository.save(entry);
            entryListRepository.saveAll(entry.getLists());
        } catch (Exception e) {
            log.error("保存失败", e);
            throw e;  // 抛出RuntimeException会自动回滚
        }
    }
}
```

## 异常层次设计示例

```java
// 基础异常
public class BaseException extends RuntimeException {
    private String errorCode;
    // ...
}

// 业务异常
public class BusinessException extends BaseException {
    public BusinessException(String message) {
        super(message);
    }
}

// 验证异常
public class ValidationException extends BaseException {
    public ValidationException(String message) {
        super(message);
    }
}

// 数据库异常
public class DatabaseException extends BaseException {
    public DatabaseException(String message, Throwable cause) {
        super(message, cause);
    }
}

// 远程调用异常
public class RemoteException extends BaseException {
    public RemoteException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

## 统一异常处理

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidation(ValidationException e) {
        log.warn("参数验证失败: {}", e.getMessage());
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", e.getMessage()));
    }

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusiness(BusinessException e) {
        log.error("业务异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse(e.getErrorCode(), e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneral(Exception e) {
        log.error("系统异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse("SYSTEM_ERROR", "系统异常，请稍后重试"));
    }
}
```

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第9节
