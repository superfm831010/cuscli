---
description: "Java基础规范：JDK8+、禁止Date类、优先JDK函数"
globs: ["**/*.java"]
alwaysApply: true
---

# Java 基础规范

## JDK 版本要求

1. 【强制】除历史项目外，新建项目应采用 **JDK8** 及以上版本
2. 【推荐】Java项目推荐遵循阿里Java开发规范

## 核心禁止事项

### ❌ 禁止使用 java.util.Date

【强制】java项目中，日期类型使用java8的 **LocalDate**、**LocalDateTime** 等进行定义，**不允许使用 java.util.Date 类**。

```java
// ❌ 错误：使用java.util.Date
import java.util.Date;

public class Entry {
    private Date declDate;     // 错误
    private Date createTime;   // 错误
}

// ✅ 正确：使用java.time包
import java.time.LocalDate;
import java.time.LocalDateTime;

public class Entry {
    private LocalDate declDate;          // 正确
    private LocalDateTime createTime;    // 正确
}
```

#### Java 8 时间API使用

```java
import java.time.*;
import java.time.format.DateTimeFormatter;

// 日期
LocalDate today = LocalDate.now();
LocalDate birthday = LocalDate.of(1990, 1, 1);
LocalDate tomorrow = today.plusDays(1);

// 日期时间
LocalDateTime now = LocalDateTime.now();
LocalDateTime dateTime = LocalDateTime.of(2024, 1, 1, 10, 30, 0);

// 时间
LocalTime time = LocalTime.now();
LocalTime lunchTime = LocalTime.of(12, 0);

// 格式化
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
String formatted = now.format(formatter);
LocalDateTime parsed = LocalDateTime.parse("2024-01-01 10:30:00", formatter);

// 计算
long daysBetween = ChronoUnit.DAYS.between(birthday, today);
LocalDateTime nextHour = now.plusHours(1);

// 时区
ZonedDateTime zonedDateTime = ZonedDateTime.now(ZoneId.of("Asia/Shanghai"));

// 时间戳
Instant instant = Instant.now();
long epochMilli = instant.toEpochMilli();  // 毫秒时间戳
```

### ❌ 禁止随意引入第三方库

【强制】不允许随意引入第三方库。

1. 【强制】公共函数首选 **JDK自带函数**
2. 【强制】在JDK不能满足要求的情况下，优先使用 **google guava、apache commons** 等成熟库
3. 【强制】最后才考虑自行封装公共函数
4. 【强制】确实有必要引入新库时，应经海关应用云平台组进行评估

```java
// ✅ 正确：优先使用JDK
import java.util.Objects;
import java.util.Arrays;
import java.util.stream.Collectors;

// 字符串判空
if (str == null || str.isEmpty()) { }

// 对象判空
Objects.requireNonNull(obj, "对象不能为空");

// 集合操作
List<String> list = Arrays.asList("a", "b", "c");
String joined = String.join(",", list);

// ✅ 次选：使用成熟库
import com.google.common.base.Strings;
import org.apache.commons.lang3.StringUtils;

// Guava
if (Strings.isNullOrEmpty(str)) { }

// Apache Commons
if (StringUtils.isBlank(str)) { }
```

### 使用平台SDK

1. 【强制】java项目**必须**采用平台组提供脚手架进行开发
2. 【强制】**必须**引用平台组提供的SDK，基于平台SDK进行开发
3. 【强制】pom的parent里统一使用云平台基础框架 **h2018.framework** 作为父依赖

```xml
<!-- pom.xml -->
<parent>
    <groupId>cn.gov.customs.h2018</groupId>
    <artifactId>h2018-framework</artifactId>
    <version>2.0.0</version>
</parent>

<dependencies>
    <!-- 平台SDK -->
    <dependency>
        <groupId>cn.gov.customs.h2018</groupId>
        <artifactId>h2018-sdk-core</artifactId>
    </dependency>
</dependencies>
```

## 日期时间规范

### 日期格式化

1. 【强制】日期格式化时，传入pattern中表示年份统一使用小写的 **y**（不是大写Y）

```java
// ✅ 正确
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

// ❌ 错误：使用大写Y
DateTimeFormatter wrongFormatter = DateTimeFormatter.ofPattern("YYYY-MM-dd HH:mm:ss");
// YYYY代表week in which year，可能导致年份错误
```

2. 【强制】分清楚大写的 M 和小写的 m，大写的 H 和小写的 h
   - **M**: 月份（Month）
   - **m**: 分钟（minute）
   - **H**: 24小时制（Hour）
   - **h**: 12小时制（hour）

```java
// 正确的格式
"yyyy-MM-dd HH:mm:ss"  // 2024-01-01 14:30:45
"yyyy-MM-dd hh:mm:ss a"  // 2024-01-01 02:30:45 PM
```

### 获取当前时间

【强制】获取当前毫秒数：**System.currentTimeMillis()**，而不是 new Date().getTime()

```java
// ✅ 正确
long now = System.currentTimeMillis();

// ❌ 错误
long now = new Date().getTime();

// 获取纳秒级时间
long nanoTime = System.nanoTime();

// JDK8推荐：统计时间使用Instant
Instant start = Instant.now();
// ... 业务逻辑
Instant end = Instant.now();
Duration duration = Duration.between(start, end);
long millis = duration.toMillis();
```

### 避免硬编码一年天数

【强制】不要在程序中写死一年为365天

```java
// ✅ 正确：获取今年的天数
int daysOfThisYear = LocalDate.now().lengthOfYear();

// 获取指定年份的天数
int daysOf2024 = LocalDate.of(2024, 1, 1).lengthOfYear();  // 366（闰年）

// 日期计算
LocalDate today = LocalDate.now();
LocalDate nextYear = today.plusYears(1);  // 使用API而非硬编码365

// ❌ 错误：硬编码365天
int[] dayArray = new int[365];  // 闰年会数组越界

Calendar calendar = Calendar.getInstance();
calendar.set(2020, 1, 26);
calendar.add(Calendar.DATE, 365);  // 闰年计算错误
```

## 常用库函数选择优先级

### 字符串操作

```java
// 1. 优先JDK
String.isEmpty()
String.isBlank()  // JDK 11+
String.join(",", list)
String.format("Hello %s", name)

// 2. 次选Apache Commons或Guava
StringUtils.isBlank(str)
StringUtils.defaultIfBlank(str, "default")
Strings.nullToEmpty(str)
```

### 集合操作

```java
// 1. 优先JDK Stream API
List<String> result = list.stream()
    .filter(s -> s.startsWith("A"))
    .map(String::toUpperCase)
    .collect(Collectors.toList());

// 2. 次选Guava
Lists.newArrayList()
Sets.newHashSet()
Maps.newHashMap()
```

### 对象操作

```java
// 1. 优先JDK
Objects.requireNonNull(obj)
Objects.equals(obj1, obj2)
Objects.hash(field1, field2)

// 2. 次选Apache Commons
ObjectUtils.defaultIfNull(obj, defaultObj)
```

## 适用场景

- 所有Java项目
- Spring Boot应用
- 微服务开发

## 相关规范

- 参见 [Java代码格式规范](./java-formatting.md)
- 参见 [日志记录规范](./java-logging.md)

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第5节
- 《海关应用云平台开发规范》- 00-cacp-spec.md 第5节
