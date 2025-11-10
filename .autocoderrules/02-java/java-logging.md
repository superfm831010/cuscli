---
description: "日志记录规范：使用Slf4j，@Slf4j注解"
globs: ["**/*.java"]
alwaysApply: false
---

# Java 日志记录规范

## 日志框架

【强制】程序中不可以直接使用日志系统(Log4j、Logback)中的API，而应依赖使用日志框架 **SLF4J** 中的API。

### 使用Lombok注解

在使用了Lombok的情况下，只需要添加 `@Slf4j` 注解后直接使用：

```java
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class EntryServiceImpl {
    public void processEntry(Entry entry) {
        log.debug("开始处理报关单: {}", entry.getEntryNo());
        log.info("报关单状态更新为: {}", entry.getStatus());

        try {
            // 业务逻辑
        } catch (Exception e) {
            log.error("处理报关单失败: {}", entry.getEntryNo(), e);
        }
    }
}
```

### 不使用Lombok

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EntryServiceImpl {
    private static final Logger log = LoggerFactory.getLogger(EntryServiceImpl.class);

    public void processEntry(Entry entry) {
        log.info("处理报关单: {}", entry.getEntryNo());
    }
}
```

## 日志级别

目前只记录如下4种级别，具体使用场景见描述：

### DEBUG

**在需要时打开，可以定位应用系统出现问题的位置**

```java
log.debug("查询参数: entryNo={}, status={}", entryNo, status);
log.debug("方法执行结果: {}", result);
```

### INFO

**一般记录项目活动状态，不能每个请求都记录info日志**

```java
log.info("应用启动成功");
log.info("开始执行定时任务: {}", taskName);
log.info("处理报关单完成, 耗时: {}ms", duration);
```

### WARN

**警告信息，与预期的正常情况不一样，需要引起注意**

```java
log.warn("未找到国家代码: {}", countryCode);
log.warn("用户{}没有操作权限", userId);
```

### ERROR

**错误，程序已经无法处理，要记录错误堆栈**

```java
log.error("保存报关单失败", exception);
log.error("调用外部接口异常: {}", apiUrl, exception);
```

## 日志输出规范

### 使用占位符

【强制】日志输出时，采用条件输出形式或者使用占位符的方式。

```java
// ✅ 正确：使用占位符
log.info("处理报关单: {}, 状态: {}", entryNo, status);

// ❌ 错误：字符串拼接
log.info("处理报关单: " + entryNo + ", 状态: " + status);
```

### 记录异常堆栈

【强制】在记录异常日志时，必须包含异常堆栈、错误上下文关键信息。

```java
// ✅ 正确：记录完整异常信息
try {
    entryService.save(entry);
} catch (Exception e) {
    log.error("保存报关单失败, entryNo: {}", entry.getEntryNo(), e);
    throw e;  // 或者处理异常
}

// ❌ 错误：只记录错误消息
catch (Exception e) {
    log.error("保存失败: " + e.getMessage());  // 缺少堆栈信息
}
```

## 禁止事项

### ❌ 禁止重新设置日志格式和目录

【强制】不允许重新设置日志的输出格式、日志文件目录，将会影响日志系统对日志的采集。

### ❌ 禁止使用System.out

【强制】生产环境禁止直接使用 System.out 或 System.err 输出日志。

```java
// ❌ 错误
System.out.println("处理报关单: " + entryNo);
System.err.println("发生错误: " + error);

// ✅ 正确
log.info("处理报关单: {}", entryNo);
log.error("发生错误", error);
```

## 日志输出示例

```java
@Slf4j
@Service
public class EntryServiceImpl {

    public void importEntry(Entry entry) {
        log.debug("开始导入报关单, 参数: {}", entry);

        try {
            // 检查参数
            if (entry == null || entry.getEntryNo() == null) {
                log.warn("报关单参数不完整");
                throw new ValidationException("报关单参数不完整");
            }

            // 业务处理
            entryRepository.save(entry);
            log.info("报关单导入成功: {}", entry.getEntryNo());

        } catch (ValidationException e) {
            log.error("报关单验证失败: {}", entry.getEntryNo(), e);
            throw e;
        } catch (Exception e) {
            log.error("报关单导入异常, entryNo: {}", entry.getEntryNo(), e);
            throw new BusinessException("报关单导入失败", e);
        }
    }
}
```

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第10节
- 《海关应用云平台开发规范》- 00-cacp-spec.md 第5.4节
