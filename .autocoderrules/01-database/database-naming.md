---
description: "数据库命名规范：表名、字段名、索引命名规则"
globs: ["**/*.sql"]
alwaysApply: false
---

# 数据库命名规范

## 命名通用规则

1. 【强制】所有数据库对象名称使用大写字母（Oracle会自动转大写）
2. 【强制】使用下划线（_）分隔单词
3. 【强制】不使用中划线（-）、空格或其他特殊字符
4. 【强制】不使用数据库保留字作为对象名称
5. 【强制】名称应具有描述性，见名知义

## 表命名规范

### 基本规则

```
T_{模块/功能}_{业务含义}
```

### 示例

```sql
-- ✅ 正确示例
CREATE TABLE T_ENTRY_HEAD (          -- 报关单表头
    ENTRY_ID VARCHAR(50) PRIMARY KEY,
    ENTRY_NO VARCHAR(50) NOT NULL
);

CREATE TABLE T_ENTRY_LIST (          -- 报关单表体
    LIST_ID VARCHAR(50) PRIMARY KEY,
    ENTRY_ID VARCHAR(50) NOT NULL,
    G_NO INT NOT NULL
);

CREATE TABLE T_SYS_USER (             -- 系统用户表
    USER_ID VARCHAR(50) PRIMARY KEY,
    USER_NAME VARCHAR(100) NOT NULL
);

CREATE TABLE T_DICT_COUNTRY (         -- 字典-国家代码表
    COUNTRY_CODE VARCHAR(10) PRIMARY KEY,
    COUNTRY_NAME VARCHAR(200) NOT NULL
);

-- ❌ 错误示例
CREATE TABLE EntryHead (              -- 错误：使用驼峰命名
    ...
);

CREATE TABLE t_entry-head (           -- 错误：使用中划线
    ...
);

CREATE TABLE ENTRY (                  -- 错误：没有T_前缀
    ...
);
```

### 表名前缀约定

| 前缀 | 说明 | 示例 |
|-----|-----|------|
| T_ | 业务表 | T_ENTRY_HEAD |
| T_DICT_ | 字典表 | T_DICT_COUNTRY |
| T_SYS_ | 系统表 | T_SYS_USER |
| T_LOG_ | 日志表 | T_LOG_OPERATION |
| T_TMP_ | 临时表 | T_TMP_CALC |
| V_ | 视图 | V_ENTRY_DETAIL |

## 字段命名规范

### 基本规则

1. 【强制】字段名全部大写
2. 【强制】使用下划线分隔单词
3. 【强制】字段名应清晰表达其含义
4. 【推荐】主键字段命名为 `{表名}_ID`
5. 【推荐】外键字段命名为 `{关联表名}_ID`

### 示例

```sql
CREATE TABLE T_ENTRY_HEAD (
    -- 主键
    ENTRY_ID VARCHAR(50) PRIMARY KEY,

    -- 业务字段
    ENTRY_NO VARCHAR(50) NOT NULL,
    CUSTOMS_CODE VARCHAR(10) NOT NULL,
    TRADE_CODE VARCHAR(20),
    I_E_FLAG VARCHAR(1) NOT NULL,           -- 进出口标志 (I/E)
    DECL_PORT VARCHAR(10),
    COUNTRY_CODE VARCHAR(10),

    -- 金额类字段
    TOTAL_AMOUNT DECIMAL(18,2),
    TAX_AMOUNT DECIMAL(18,2),

    -- 时间类字段
    DECL_DATE DATE,
    ENTRY_DATE DATE,

    -- 状态类字段
    STATUS VARCHAR(10) DEFAULT '0',
    AUDIT_STATUS VARCHAR(10),

    -- 技术字段（必需）
    REC_VERSION INT DEFAULT 0,
    REC_CREATE_TIME DATETIME2 DEFAULT GETDATE(),
    REC_LAST_UPDATE_TIME DATETIME2 DEFAULT GETDATE(),

    -- 备注类字段
    REMARK VARCHAR(500)
);

-- ❌ 错误示例
CREATE TABLE T_ENTRY_HEAD (
    entryId VARCHAR(50),              -- 错误：驼峰命名
    Entry_No VARCHAR(50),             -- 错误：混合大小写
    customs-code VARCHAR(10),         -- 错误：使用中划线
    i/e_flag VARCHAR(1)               -- 错误：使用斜杠
);
```

### 字段命名建议

| 字段类型 | 命名约定 | 示例 |
|---------|---------|------|
| 主键 | {表名}_ID | ENTRY_ID, USER_ID |
| 外键 | {关联表}_ID | COUNTRY_ID, USER_ID |
| 编号 | {业务}_NO | ENTRY_NO, ORDER_NO |
| 代码 | {业务}_CODE | CUSTOMS_CODE, COUNTRY_CODE |
| 名称 | {业务}_NAME | USER_NAME, COUNTRY_NAME |
| 日期 | {业务}_DATE | DECL_DATE, ENTRY_DATE |
| 时间 | {业务}_TIME | CREATE_TIME, UPDATE_TIME |
| 金额 | {业务}_AMOUNT | TOTAL_AMOUNT, TAX_AMOUNT |
| 数量 | {业务}_QTY | ORDER_QTY, STOCK_QTY |
| 标志 | {业务}_FLAG | DELETE_FLAG, VALID_FLAG |
| 状态 | {业务}_STATUS | AUDIT_STATUS, PAY_STATUS |
| 类型 | {业务}_TYPE | ENTRY_TYPE, USER_TYPE |

## 索引命名规范

### 主键索引

```
PK_{表名}
```

### 唯一索引

```
UQ_{表名}_{字段名}
或
UQ_{表名}_{字段1}_{字段2}  (复合唯一索引)
```

### 普通索引

```
IDX_{表名}_{字段名}
或
IDX_{表名}_{字段1}_{字段2}  (复合索引)
```

### 示例

```sql
-- 主键约束
ALTER TABLE T_ENTRY_HEAD
ADD CONSTRAINT PK_ENTRY_HEAD PRIMARY KEY (ENTRY_ID);

-- 唯一索引
CREATE UNIQUE INDEX UQ_ENTRY_HEAD_ENTRY_NO
ON T_ENTRY_HEAD(ENTRY_NO);

-- 普通单列索引
CREATE INDEX IDX_ENTRY_HEAD_CUSTOMS_CODE
ON T_ENTRY_HEAD(CUSTOMS_CODE);

-- 复合索引
CREATE INDEX IDX_ENTRY_HEAD_STATUS_DATE
ON T_ENTRY_HEAD(STATUS, DECL_DATE);

-- 包含列索引（SQL Server）
CREATE INDEX IDX_ENTRY_HEAD_ENTRY_NO
ON T_ENTRY_HEAD(ENTRY_NO)
INCLUDE (STATUS, DECL_DATE);
```

## 约束命名规范

### 主键约束

```
PK_{表名}
```

### 外键约束（不推荐使用）

```
FK_{表名}_{关联表名}
```

### 检查约束

```
CK_{表名}_{字段名}
```

### 默认约束

```
DF_{表名}_{字段名}
```

### 示例

```sql
-- 主键约束
CONSTRAINT PK_ENTRY_HEAD PRIMARY KEY (ENTRY_ID)

-- 检查约束
CONSTRAINT CK_ENTRY_HEAD_IE_FLAG CHECK (I_E_FLAG IN ('I', 'E'))

-- 默认约束
CONSTRAINT DF_ENTRY_HEAD_STATUS DEFAULT '0' FOR STATUS
```

## 序列命名规范（Oracle）

```
SEQ_{表名}_{字段名}
或
SEQ_{表名}
```

### 示例

```sql
-- Oracle序列
CREATE SEQUENCE SEQ_ENTRY_HEAD_ID
START WITH 1
INCREMENT BY 1
NOCACHE
NOCYCLE;

-- 使用序列
INSERT INTO T_ENTRY_HEAD (ENTRY_ID, ENTRY_NO)
VALUES (SEQ_ENTRY_HEAD_ID.NEXTVAL, 'E202401010001');
```

## 视图命名规范

```
V_{视图描述}
```

### 示例

```sql
CREATE VIEW V_ENTRY_DETAIL AS
SELECT
    H.ENTRY_ID,
    H.ENTRY_NO,
    H.CUSTOMS_CODE,
    L.G_NO,
    L.G_NAME,
    L.QTY
FROM T_ENTRY_HEAD H
INNER JOIN T_ENTRY_LIST L ON H.ENTRY_ID = L.ENTRY_ID;
```

## 存储过程命名规范

```
SP_{功能描述}
或
P_{功能描述}
```

### 示例

```sql
CREATE PROCEDURE SP_ENTRY_IMPORT
(
    @ENTRY_NO VARCHAR(50),
    @STATUS VARCHAR(10) OUTPUT
)
AS
BEGIN
    -- 存储过程逻辑
END;
```

## 函数命名规范

```
FN_{功能描述}
或
F_{功能描述}
```

### 示例

```sql
CREATE FUNCTION FN_GET_COUNTRY_NAME
(
    @COUNTRY_CODE VARCHAR(10)
)
RETURNS VARCHAR(200)
AS
BEGIN
    DECLARE @COUNTRY_NAME VARCHAR(200);

    SELECT @COUNTRY_NAME = COUNTRY_NAME
    FROM T_DICT_COUNTRY
    WHERE COUNTRY_CODE = @COUNTRY_CODE;

    RETURN @COUNTRY_NAME;
END;
```

## 数据源命名规范

数据源名称采用如下定义：
1. 对于原H2K已定义的名称，延续使用
2. 对于C系统的数据源名称以H18开头
3. 对于提供给其它系统使用的数据源：`{系统}_{权限}_{目标系统}`

### 示例

```
H18SYS_RW_MFT    -- H2018系统-读写-舱单库账号
H18_RO_DICT      -- H2018系统-只读-字典库账号
```

## 命名长度限制

| 对象类型 | Oracle | SQL Server |
|---------|--------|------------|
| 表名 | 30字符 | 128字符 |
| 字段名 | 30字符 | 128字符 |
| 索引名 | 30字符 | 128字符 |
| 约束名 | 30字符 | 128字符 |

【注意】Oracle对象名称长度限制较严格，命名时需注意。

## 相关规范

- 参见 [数据库设计规范](./database-design.md)
- 参见 [必需字段规范](./database-fields.md)

## 来源文档

- 《OLTP关系性数据库设计及应用规范》- 01-oltp-db-spec.md
- 《海关应用云平台开发规范》- 00-cacp-spec.md 第4节
