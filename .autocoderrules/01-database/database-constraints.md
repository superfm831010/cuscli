---
description: "数据库禁止事项：禁止外键、触发器、DBLINK等"
globs: ["**/*.sql", "**/*.java", "**/*.xml"]
alwaysApply: true
---

# 数据库禁止事项

## 核心禁止规范

### ❌ 禁止使用外键

**绝对禁止在数据库中使用外键约束！**

#### 禁止原因

1. 数据库需要维护外键的内部管理，消耗性能
2. 外键把数据一致性事务实现全部交给数据库服务器完成
3. 涉及外键字段的增、删、更新操作需要触发相关检查，消耗资源
4. 外键容易因请求对其他表加锁而出现死锁情况
5. 外键导致数据操作时逻辑复杂
6. 外键对数据同步存在影响，必须按父子顺序同步
7. 外键增加了表结构变更及数据迁移的复杂性

#### 替代方案

**数据的完整性应该从应用层面进行控制。**

```java
// ✅ 正确做法：在应用层控制数据完整性
@Service
public class EntryServiceImpl {
    public void saveEntry(Entry entry) {
        // 检查关联数据是否存在
        if (!countryService.existsByCode(entry.getCountryCode())) {
            throw new ValidationException("国家代码不存在");
        }

        // 保存数据
        entryRepository.save(entry);
    }
}
```

### ❌ 禁止使用触发器

**不建议使用触发器！必要时应谨慎使用。**

#### 禁止原因

1. 触发器对应用不透明（应用层不知道何时触发，发生了什么）
2. 过多使用触发器会导致复杂的内部依赖关系
3. 触发器可能产生级联触发，导致预料之外的后果
4. 触发器的全局性影响所有用户和程序，实施时需特别谨慎
5. 调试和维护困难

#### 如必须使用的规范

如果必须使用触发器，需遵循：

1. 【强制】保持触发器的简单性，一个触发器只完成一个任务
2. 【强制】不要在触发器中加入事务控制语句（Commit、Rollback、SavePoint）
3. 【强制】不要使用 Long 或 Long Raw 类型的变量
4. 【强制】首先在触发器之外测试触发器程序逻辑
5. 【强制】避免同一表上创建多个同类型的DML触发器（触发顺序不确定）

### ❌ 禁止使用DBLINK

**禁止在应用中使用DBLINK进行跨库访问。**

#### 禁止原因

1. DBLINK会导致性能问题
2. 增加数据库之间的耦合
3. 不利于数据库迁移和扩展
4. 难以进行权限控制和审计

#### 替代方案

使用应用层服务调用或数据同步机制。

### ❌ 禁止程序执行DDL

**禁止在应用程序中执行DDL语句（CREATE、ALTER、DROP等）。**

#### 禁止原因

1. DDL操作会锁表，影响正常业务
2. 容易导致数据结构不一致
3. 不利于版本管理和回滚
4. 可能产生安全隐患

#### 正确做法

所有表结构变更应通过：
- 标准的数据库变更流程
- DBA审核后执行
- 使用版本化的SQL脚本管理

### ❌ 谨慎使用大值字段

**禁止随意使用BLOB、CLOB、TEXT、IMAGE等大值字段类型。**

#### 限制原因

1. 导致数据表存储空间过大，影响IO性能
2. 操作性能较差
3. 无法参与大部分比较和运算
4. SQL Server中的text、ntext、image已被淘汰

#### 使用原则

1. 【强制】只有长度确实会超过8000/4000，才考虑使用大值字段
2. 【强制】带有大值字段的数据，尽量放在单独的表中
3. 【强制】作为变长字段，必须结合应用实际需要控制大小
4. 【推荐】优先考虑将大文件存储在文件系统，数据库只保存路径

```java
// ❌ 错误：直接在主表中存储大对象
CREATE TABLE T_ENTRY (
    ENTRY_ID VARCHAR(50) PRIMARY KEY,
    ENTRY_NO VARCHAR(50),
    ATTACHMENT BLOB  -- 错误：大对象在主表中
);

// ✅ 正确：将大对象放在单独的表中
CREATE TABLE T_ENTRY (
    ENTRY_ID VARCHAR(50) PRIMARY KEY,
    ENTRY_NO VARCHAR(50)
);

CREATE TABLE T_ENTRY_ATTACHMENT (
    ATTACHMENT_ID VARCHAR(50) PRIMARY KEY,
    ENTRY_ID VARCHAR(50),  -- 通过应用层维护关联
    ATTACHMENT_DATA BLOB
);
```

## 其他禁止事项

### ❌ 禁止使用游标

**禁止使用数据库游标！**

#### 原因

1. 游标对数据库资源（内存和锁）消耗非常大
2. 游标是逐行处理，性能远低于集合操作
3. 游标实现的功能往往可以用集合操作替代

```sql
-- ❌ 错误：使用游标
DECLARE cursor1 CURSOR FOR SELECT * FROM T_ENTRY;
OPEN cursor1;
FETCH NEXT FROM cursor1 INTO @var1, @var2;
WHILE @@FETCH_STATUS = 0
BEGIN
    -- 处理逻辑
    FETCH NEXT FROM cursor1 INTO @var1, @var2;
END
CLOSE cursor1;
DEALLOCATE cursor1;

-- ✅ 正确：使用集合操作
UPDATE T_ENTRY
SET STATUS = '1'
WHERE CREATE_TIME < '2024-01-01';
```

### ❌ 禁止在查询里指定索引

**禁止使用 WITH(INDEX=XXX) 指定索引。**

#### 原因

1. 随着数据变化，指定的索引性能可能并不最佳
2. 索引对应用应是透明的
3. 指定的索引被删除将导致查询报错
4. 新建的索引无法被应用立即使用

让数据库优化器自动选择最优索引。

### ❌ 禁止使用SELECT *

**禁止使用 SELECT * 查询数据。**

#### 原因

1. 减少内存消耗和网络带宽
2. 让查询优化器有机会从索引读取所需列
3. 表结构变化时容易引起查询出错

```sql
-- ❌ 错误
SELECT * FROM T_ENTRY WHERE ENTRY_NO = 'xxx';

-- ✅ 正确：明确指定需要的列
SELECT ENTRY_ID, ENTRY_NO, STATUS, CREATE_TIME
FROM T_ENTRY
WHERE ENTRY_NO = 'xxx';
```

### ❌ 禁止在索引列上使用函数或计算

**禁止在WHERE子句的索引列上使用函数或计算。**

#### 原因

索引列作为函数参数或参与计算，将导致索引失效，引起全表扫描。

```sql
-- ❌ 错误：索引列使用了函数
SELECT * FROM T_ENTRY WHERE ABS(AMOUNT) = 100;
SELECT * FROM T_ENTRY WHERE AMOUNT + 10 > 100;
SELECT * FROM T_ENTRY WHERE TO_CHAR(CREATE_TIME, 'YYYY-MM-DD') = '2024-01-01';

-- ✅ 正确：将函数/计算移到等号右侧
SELECT * FROM T_ENTRY WHERE AMOUNT = 100;
SELECT * FROM T_ENTRY WHERE AMOUNT > 90;
SELECT * FROM T_ENTRY WHERE CREATE_TIME >= TO_DATE('2024-01-01', 'YYYY-MM-DD')
    AND CREATE_TIME < TO_DATE('2024-01-02', 'YYYY-MM-DD');
```

### ❌ 禁止在数据库做复杂运算

**禁止在数据库中进行复杂运算，复杂运算应在应用程序端完成。**

禁止的操作包括：
- XML解析
- 字符串相似性比较
- 复杂的字符串搜索（Charindex）
- 复杂的数学运算

## 总结

| 禁止项 | 替代方案 | 重要性 |
|-------|---------|--------|
| 外键 | 应用层控制 | ⭐⭐⭐ |
| 触发器 | 应用层逻辑 | ⭐⭐⭐ |
| DBLINK | 服务调用/数据同步 | ⭐⭐⭐ |
| 程序执行DDL | DBA审核流程 | ⭐⭐⭐ |
| 大值字段 | 文件系统存储 | ⭐⭐ |
| 游标 | 集合操作 | ⭐⭐⭐ |
| SELECT * | 明确列名 | ⭐⭐ |
| 索引列函数 | 函数移到等号右侧 | ⭐⭐⭐ |
| 指定索引 | 优化器自动选择 | ⭐⭐ |
| 数据库复杂运算 | 应用层处理 | ⭐⭐ |

## 相关规范

- 参见 [数据库设计规范](./database-design.md)
- 参见 [数据库命名规范](./database-naming.md)

## 来源文档

- 《OLTP关系性数据库设计及应用规范》- 01-oltp-db-spec.md
