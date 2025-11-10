---
description: "数据库设计规范：字段类型、索引、约束设计"
globs: ["**/*.sql"]
alwaysApply: false
---

# 数据库设计规范

## 字段设计

### 字符类型选择

1. 【强制】建议采用 `VARCHAR` 或 `NVARCHAR` 数据类型
2. 【强制】在同一数据库中应保持一致（避免隐式转换）
3. 【注意】字符类型索引性能低于数字类型索引

```sql
-- Oracle
VARCHAR2(100)

-- SQL Server
VARCHAR(100)  或  NVARCHAR(100)
```

### 时间类型选择

**SQL Server**:
- `datetime`: 1753-01-01 到 9999-12-31，精度毫秒
- `datetime2`: 0001-01-01 到 9999-12-31，精度100纳秒（推荐）

**Oracle**:
- `date`: -4712-01-01 到 9999-12-31，精度秒

```sql
-- SQL Server
CREATE_TIME DATETIME2 DEFAULT GETDATE()

-- Oracle
CREATE_TIME DATE DEFAULT SYSDATE
```

### 自增字段类型

【强制】自增字段应使用容量较大的数据类型

```sql
-- SQL Server
ENTRY_ID BIGINT IDENTITY(1,1) PRIMARY KEY

-- Oracle
ENTRY_ID NUMBER(20) PRIMARY KEY
-- 配合序列使用
CREATE SEQUENCE SEQ_ENTRY_ID START WITH 1 INCREMENT BY 1;
```

### 数值类型选择

```sql
-- 整数
TINYINT      -- 0 to 255
SMALLINT     -- -32,768 to 32,767
INT          -- -2,147,483,648 to 2,147,483,647
BIGINT       -- -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807

-- 小数（金额等精确计算）
DECIMAL(18, 2)  -- 推荐用于金额
NUMERIC(18, 2)  -- 与DECIMAL相同

-- 浮点数（科学计算）
FLOAT
DOUBLE
```

### NULL 属性设计

【强制】谨慎使用 NULL 属性

1. 【强制】对于新增加的表，禁止所有字段为 NULL
2. 【推荐】对于旧表调整，允许新增字段为 NULL

#### NULL 带来的复杂性

```sql
-- 1. 任何与NULL的比较都返回False
SELECT * FROM T_ENTRY WHERE STATUS = NULL;    -- 错误！查不到任何数据
SELECT * FROM T_ENTRY WHERE STATUS IS NULL;   -- 正确

-- 2. 查找"不等于"时会遗漏NULL
SELECT * FROM T_ENTRY WHERE STATUS <> '1';    -- 不包含STATUS为NULL的记录
SELECT * FROM T_ENTRY WHERE STATUS <> '1' OR STATUS IS NULL;  -- 正确

-- 3. IS NULL无法使用索引，ISNULL/NVL函数影响性能
SELECT * FROM T_ENTRY WHERE ISNULL(STATUS, '0') = '0';  -- 性能差
```

#### 正确做法

```sql
-- ✅ 使用默认值代替NULL
CREATE TABLE T_ENTRY (
    ENTRY_ID VARCHAR(50) PRIMARY KEY,
    ENTRY_NO VARCHAR(50) NOT NULL,
    STATUS VARCHAR(10) NOT NULL DEFAULT '0',
    REMARK VARCHAR(500) NOT NULL DEFAULT '',
    AMOUNT DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    CREATE_TIME DATETIME2 NOT NULL DEFAULT GETDATE()
);
```

## 索引设计

### 主键设计

1. 【强制】每一张表必须有主键！
2. 【强制】主键应尽量选择单列
3. 【强制】主键字段应永远不需要进行更新
4. 【推荐】主键选择无业务含义的自增ID

```sql
-- ✅ 推荐：单列自增主键
CREATE TABLE T_ENTRY (
    ENTRY_ID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ENTRY_NO VARCHAR(50) NOT NULL UNIQUE,
    -- ...
);

-- ❌ 不推荐：复合主键
CREATE TABLE T_ENTRY_LIST (
    ENTRY_NO VARCHAR(50),
    G_NO INT,
    PRIMARY KEY (ENTRY_NO, G_NO)  -- 性能较差
);
```

### 索引设计准则

1. 【推荐】对经常用于 WHERE 子句的字段建索引
2. 【推荐】对经常用于 JOIN 关系的字段建索引
3. 【推荐】对经常用于 ORDER BY 子句的字段建索引
4. 【强制】单表索引数不超过6个
5. 【强制】单个索引包含的字段（包括include列）不超过5个
6. 【强制】不要给选择性低的字段建单列索引（如性别、状态0/1）
7. 【强制】不要给小型表创建索引（仅几个页的表）

### 索引设计示例

```sql
-- 单列索引
CREATE INDEX IDX_ENTRY_NO ON T_ENTRY(ENTRY_NO);
CREATE INDEX IDX_CREATE_TIME ON T_ENTRY(CREATE_TIME);

-- 复合索引（过滤性好的字段在前）
CREATE INDEX IDX_STATUS_TIME ON T_ENTRY(STATUS, CREATE_TIME);

-- 唯一索引
CREATE UNIQUE INDEX UQ_ENTRY_NO ON T_ENTRY(ENTRY_NO);

-- 包含列索引（SQL Server）
CREATE INDEX IDX_ENTRY_NO ON T_ENTRY(ENTRY_NO)
INCLUDE (STATUS, CREATE_TIME);
```

### 聚集索引与非聚集索引（SQL Server）

**聚集索引**（一个表只能有一个）:
- 数据按索引顺序存储
- 检索效率高，但更新影响大
- 默认主键为聚集索引

```sql
-- 指定聚集索引
CREATE CLUSTERED INDEX IX_ENTRY_NO ON T_ENTRY(ENTRY_NO);

-- 主键非聚集索引，另建聚集索引
CREATE TABLE T_ENTRY (
    ENTRY_ID BIGINT PRIMARY KEY NONCLUSTERED,
    ENTRY_NO VARCHAR(50) NOT NULL
);
CREATE CLUSTERED INDEX IX_ENTRY_NO ON T_ENTRY(ENTRY_NO);
```

| 操作 | 聚集索引 | 非聚集索引 |
|-----|---------|-----------|
| 列经常被分组排序 | √ | √ |
| 返回某范围内的数据 | √ | × |
| 小数目的不同值 | √ | × |
| 大数目的不同值 | × | √ |
| 频繁更新的列 | × | √ |
| 频繁修改索引列 | × | √ |

## 表结构设计

### 表大小建议

【推荐】当表满足以下条件时，应考虑分区：
1. 表的大小超过 1.5GB-2GB
2. OLTP系统中，记录超过1000万
3. 按时间段删除成批数据
4. 经常执行并行操作

### 分区表设计原则

```sql
-- SQL Server 范围分区示例
-- 1. 创建分区函数
CREATE PARTITION FUNCTION PF_ENTRY_TIME (DATETIME2)
AS RANGE RIGHT FOR VALUES (
    '2024-01-01', '2024-02-01', '2024-03-01'
);

-- 2. 创建分区方案
CREATE PARTITION SCHEME PS_ENTRY_TIME
AS PARTITION PF_ENTRY_TIME
TO (FG1, FG2, FG3, FG4);

-- 3. 在分区方案上创建表
CREATE TABLE T_ENTRY (
    ENTRY_ID BIGINT IDENTITY(1,1),
    ENTRY_NO VARCHAR(50),
    CREATE_TIME DATETIME2,
    PRIMARY KEY (ENTRY_ID, CREATE_TIME)
) ON PS_ENTRY_TIME(CREATE_TIME);
```

### 临时表使用

【推荐】对于复杂计算，使用系统临时表而非应用临时表

```sql
-- Oracle 系统临时表
CREATE GLOBAL TEMPORARY TABLE TMP_ENTRY_CALC (
    ENTRY_ID VARCHAR(50),
    CALC_AMOUNT DECIMAL(18,2)
) ON COMMIT DELETE ROWS;  -- 事务级
-- 或
ON COMMIT PRESERVE ROWS;  -- 会话级

-- SQL Server 临时表
CREATE TABLE #TMP_ENTRY_CALC (  -- 会话级
    ENTRY_ID VARCHAR(50),
    CALC_AMOUNT DECIMAL(18,2)
);

CREATE TABLE ##TMP_ENTRY_CALC (  -- 全局临时表
    ENTRY_ID VARCHAR(50),
    CALC_AMOUNT DECIMAL(18,2)
);
```

**系统临时表 vs 应用临时表**:

| 特性 | 应用临时表 | 系统临时表 |
|-----|-----------|-----------|
| 清除方式 | 应用DELETE | 系统自动TRUNCATE |
| DML锁 | 有 | 没有 |
| REDO信息 | 产生 | 不产生 |
| 事务/会话级 | 没有 | 提供 |

## 字符集设计

### SQL Server

【强制】保持 Instances、Databases、Columns 三层字符集设置一致

常用字符集：
- `Chinese_PRC_BIN`: 二进制排序，大小写敏感
- `Chinese_PRC_CI_AS`: 不区分大小写，音调不敏感

### Oracle

【强制】同一应用访问的Oracle数据库字符集应保持一致

推荐字符集：
- `SIMPLIFIED CHINESE_CHINA.ZHS16GBK`（推荐）
- `american_america.AL32UTF8`

## 相关规范

- 参见 [数据库禁止事项](./database-constraints.md)
- 参见 [数据库命名规范](./database-naming.md)
- 参见 [必需字段规范](./database-fields.md)

## 来源文档

- 《OLTP关系性数据库设计及应用规范》- 01-oltp-db-spec.md
