---
description: "Java代码格式规范：缩进、空格、换行规则"
globs: ["**/*.java"]
alwaysApply: false
---

# Java 代码格式规范

## 缩进

【强制】采用 **4个空格** 缩进，如果使用tab必须设置1个tab为4个空格。

- IDEA: 设置tab为4个空格时，请勿勾选 Use tab character
- Eclipse: 必须勾选 insert spaces for tabs

## 大括号

【强制】如果是大括号内为空，则简洁地写成`{}`即可，大括号中间无需换行和空格；如果是非空代码块则：

1. 左大括号前不换行
2. 左大括号后换行
3. 右大括号前换行
4. 右大括号后还有else等代码则不换行；表示终止的右大括号后必须换行

```java
// ✅ 正确
public void method() {
    if (condition) {
        // ...
    } else {
        // ...
    }
}

// ❌ 错误
public void method()
{  // 错误：左大括号前换行
    if (condition)
    {  // 错误：左大括号前换行
        // ...
    }
    else {  // 错误：else前应该不换行
        // ...
    }
}
```

## 空格

【强制】任何二目、三目运算符的左右两边都需要加一个空格。

包括赋值运算符`=`、逻辑运算符`&&`、加减乘除符号等。

```java
// ✅ 正确
int result = a + b;
if (flag && isValid) {
    // ...
}
String name = flag ? "yes" : "no";

// ❌ 错误
int result=a+b;  // 缺少空格
if (flag&&isValid) {  // 缺少空格
    // ...
}
```

【强制】注释的双斜线与注释内容之间有且仅有一个空格。

```java
// ✅ 正确
// 这是一个注释

// ❌ 错误
//这是一个注释
//  这是一个注释（两个空格）
```

## 换行

【强制】单行字符数限制不超过120个，超出需要换行，换行时遵循如下原则：

1. 第二行相对第一行缩进4个空格，从第三行开始，不再继续缩进
2. 运算符与下文一起换行
3. 方法调用的点符号与下文一起换行
4. 方法调用中的多个参数需要换行时，在逗号后进行
5. 在括号前不要换行

```java
// ✅ 正确
StringBuilder sb = new StringBuilder();
// 超过120个字符的情况下，换行缩进4个空格，并且方法前的点号一起换行
sb.append("zi").append("xin")
    .append("huang")
    .append("huang")
    .append("huang");

// ❌ 错误
StringBuilder sb = new StringBuilder();
// 超过120个字符的情况下，不要在括号前换行
sb.append("you").append("are")...append
("lucky");  // 错误：括号前换行

// 参数很多的方法调用，逗号后才是换行处
method(args1, args2, args3,
    argsX);  // 正确
```

## 文件编码

【强制】IDE的text file encoding设置为 **UTF-8**；IDE中文件的换行符使用 **Unix格式**，不要使用Windows格式。

## 方法长度

【推荐】单个方法的总行数不超过80行。

说明：除注释之外的方法签名、左右大括号、方法内代码、空行、回车及任何不可见字符的总行数不超过80行。

## 空行

【推荐】不同逻辑、不同语义、不同业务的代码之间插入一个空行分隔开来以提升可读性。

说明：任何情形，没有必要插入多个空行进行隔开。

## 示例

```java
package cn.gov.customs.h2018.entry.service.impl;

import cn.gov.customs.h2018.entry.entity.Entry;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * 报关单服务实现类
 *
 * @author zhangsan
 * @date 2024-01-01
 */
@Slf4j
@Service
public class EntryServiceImpl implements EntryService {

    @Override
    public void saveEntry(Entry entry) {
        // 参数验证
        if (entry == null || entry.getEntryNo() == null) {
            log.warn("参数不完整");
            throw new ValidationException("参数不完整");
        }

        // 业务逻辑
        try {
            entryRepository.save(entry);
            log.info("保存成功: {}", entry.getEntryNo());
        } catch (Exception e) {
            log.error("保存失败", e);
            throw new BusinessException("保存失败", e);
        }
    }

    @Override
    public Entry queryById(String entryId) {
        return entryRepository.findById(entryId)
            .orElseThrow(() -> new NotFoundException("报关单不存在"));
    }
}
```

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第11.2节
