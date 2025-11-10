---
description: "事务处理规范：使用@Transactional注解，避免XML配置"
globs: ["**/*.java"]
alwaysApply: false
---

# Java 事务处理规范

## 基本要求

【强制】避免使用XML配置事务，而是采用 **@Transactional注解** 的方式。

### XML配置的缺点

1. 可读性不强
2. 切面通常配置的比较泛滥，容易造成事务过大
3. 维护困难

## 注解方式事务

### 基本使用

```java
import org.springframework.transaction.annotation.Transactional;

@Service
public class EntryServiceImpl {

    @Transactional
    public void saveEntry(Entry entry) {
        entryRepository.save(entry);
        entryListRepository.saveAll(entry.getLists());
    }
}
```

### 指定事务管理器

【推荐】对应多数据源的项目，应明确在@Transactional注解中指明事务管理器名称。

```java
@Transactional(transactionManager = "primaryTransactionManager")
public void saveToMaster(Entry entry) {
    // ...
}

@Transactional(transactionManager = "secondaryTransactionManager")
public void saveToSlave(Entry entry) {
    // ...
}
```

### 事务回滚

【强制】在使用默认@Transactional注解时，如需回滚事务，在通过try/catch捕获异常后，须抛出RuntimeException类型异常，Exception类型异常不会回滚事务。

```java
// ✅ 正确：抛出RuntimeException会回滚
@Transactional
public void saveEntry(Entry entry) {
    try {
        entryRepository.save(entry);
    } catch (Exception e) {
        log.error("保存失败", e);
        throw new RuntimeException("保存失败", e);  // 会回滚
    }
}

// 或者指定rollbackFor
@Transactional(rollbackFor = Exception.class)
public void saveEntry(Entry entry) throws Exception {
    entryRepository.save(entry);  // 任何异常都会回滚
}
```

## 事务使用注意事项

### 不要调用同类的事务方法

【强制】在一个事务中，不要使用this关键字调用同类其他事务方法，这样将导致this方法的事务不生效。

```java
@Service
public class EntryServiceImpl {

    // ❌ 错误：this调用，事务不生效
    @Transactional
    public void saveEntry(Entry entry) {
        entryRepository.save(entry);
        this.saveLists(entry.getLists());  // 事务不生效！
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveLists(List<EntryList> lists) {
        entryListRepository.saveAll(lists);
    }

    // ✅ 正确：注入自己，通过代理调用
    @Autowired
    private EntryService self;

    @Transactional
    public void saveEntryCorrect(Entry entry) {
        entryRepository.save(entry);
        self.saveLists(entry.getLists());  // 正确
    }
}
```

### 非事务方法不要调用事务方法

【强制】不得使用非事务方法调用事务方法。

```java
// ❌ 错误：非事务方法调用事务方法
public void processEntry(Entry entry) {  // 没有@Transactional
    validateEntry(entry);
    saveEntry(entry);  // saveEntry的事务可能不生效
}

@Transactional
public void saveEntry(Entry entry) {
    entryRepository.save(entry);
}

// ✅ 正确：在事务方法中调用
@Transactional
public void processEntry(Entry entry) {
    validateEntry(entry);
    saveEntry(entry);
}
```

### 避免事务中的耗时操作

【推荐】在事务中尽量避免RPC调用、HTTP调用、消息队列操作(大数据报文)、循环查询等耗时操作。

```java
// ❌ 错误：事务中有耗时操作
@Transactional
public void processEntry(Entry entry) {
    entryRepository.save(entry);

    // 错误：HTTP调用在事务中
    httpClient.notifyCustoms(entry);  // 可能很慢

    // 错误：循环查询
    for (String code : codes) {
        dictService.getByCode(code);  // N+1问题
    }
}

// ✅ 正确：耗时操作移到事务外
public void processEntry(Entry entry) {
    // 事务内只做数据库操作
    saveEntryInTransaction(entry);

    // 事务外做HTTP调用
    httpClient.notifyCustoms(entry);
}

@Transactional
private void saveEntryInTransaction(Entry entry) {
    entryRepository.save(entry);
}
```

## 编程式事务

【推荐】尽量避免使用编程式事务，如必须使用，要在事务执行成功时显式编写commit代码，方法发生异常或事务失败时显式编写rollback代码。

```java
@Service
public class EntryServiceImpl {

    @Autowired
    private PlatformTransactionManager transactionManager;

    public void saveEntry(Entry entry) {
        DefaultTransactionDefinition def = new DefaultTransactionDefinition();
        def.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);

        TransactionStatus status = transactionManager.getTransaction(def);
        try {
            entryRepository.save(entry);
            transactionManager.commit(status);  // 显式提交
        } catch (Exception e) {
            transactionManager.rollback(status);  // 显式回滚
            throw e;
        }
    }
}
```

## 事务传播行为

```java
// REQUIRED（默认）：如果当前存在事务，则加入该事务；否则创建一个新事务
@Transactional(propagation = Propagation.REQUIRED)
public void method1() { }

// REQUIRES_NEW：创建一个新事务，如果当前存在事务，则把当前事务挂起
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void method2() { }

// NESTED：如果当前存在事务，则创建一个嵌套事务
@Transactional(propagation = Propagation.NESTED)
public void method3() { }

// SUPPORTS：如果当前存在事务，则加入该事务；否则以非事务方式执行
@Transactional(propagation = Propagation.SUPPORTS)
public void method4() { }
```

## 事务隔离级别

```java
// READ_COMMITTED（推荐）：避免脏读
@Transactional(isolation = Isolation.READ_COMMITTED)
public void method1() { }

// REPEATABLE_READ：避免脏读、不可重复读
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void method2() { }
```

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第8节
