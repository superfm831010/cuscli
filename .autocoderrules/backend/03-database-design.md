---
title: "数据库设计场景"
description: "表结构设计、字段定义、索引设计、命名规范"
keywords:
  - 数据库设计
  - 表设计
  - 字段设计
  - 索引设计
  - 命名规范
  - 主键设计
tags:
  - 数据库
  - 表设计
  - 索引
globs:
  - "**/*Mapper.xml"
  - "**/*Dao.java"
  - "**/*Entity.java"
  - "**/entity/**/*.java"
  - "**/dao/**/*.java"
  - "**/mapper/**/*.xml"
  - "**/sql/**/*.sql"
alwaysApply: false
priority: high
---

# 数据库设计场景规范

## 场景概述

当设计数据库表结构、字段、索引时，遵循海关集中式事务型数据库设计规范，确保数据库设计的规范性、可维护性和可扩展性。

---

## 一、命名规范

### ✅ 表命名规范

**指令**：表名包含应用简称，体现业务含义，长度≤40字符，使用大写字母和下划线。

```sql
-- ✅ 正确示例
CREATE TABLE TIR_TRANSPORT_HEAD (...)      -- TIR运输表头
CREATE TABLE TIR_TRANSPORT_LIST (...)      -- TIR运输表体
CREATE TABLE MANIFEST_PARA_COUNTRY (...)   -- 舱单参数-国家
CREATE TABLE HEPS_EVENT_LOG (...)          -- HEPS事件日志
CREATE TABLE ENTRY_HEAD_BAK (...)          -- 报关单表头备份表

-- ❌ 错误示例
CREATE TABLE tir_transport (...)           -- ❌ 未使用大写
CREATE TABLE TransportHead (...)           -- ❌ 使用驼峰命名
CREATE TABLE 运输表头 (...)                -- ❌ 使用中文
CREATE TABLE yun_shu_biao_tou (...)        -- ❌ 使用拼音
```

**表名后缀规范**：
- `_HEAD` - 表头表
- `_LIST` - 表体表（明细表）
- `_LOG` - 日志表
- `_TMP` - 临时表
- `_BAK` - 备份表
- `_EXCEPTION` - 异常表
- `_PARA` - 参数表
- `PRE_*` - 预录入表前缀
- `CUR_*` - 执法表前缀（电子口岸专网）
- `COPY_{应用名}_*` - 来自其他系统的表

**运维备份表命名**：
```sql
-- 运维产生的备份表（应用不访问）
HEPS_EVENT_XF20230313  -- 备份人姓名缩写+备份年月日
```

---

### ✅ 字段命名规范

**指令**：字段名体现业务含义，长度≤40字符，使用大写字母和下划线。

```sql
-- ✅ 正确示例
USER_NAME VARCHAR(100)              -- 用户姓名
USER_CODE VARCHAR(20)               -- 用户编号
DECL_DATE DATE                      -- 申报日期（精确到日）
REC_CREATE_TIME DATETIME            -- 记录创建时间（精确到时间）
ORG_CODE VARCHAR(10)                -- 机构代码
IS_VALID CHAR(1)                    -- 是否有效（01/02）

-- ❌ 错误示例
userName VARCHAR(100)               -- ❌ 驼峰命名
UserCode VARCHAR(20)                -- ❌ 大小写混合
user_name VARCHAR(100)              -- ❌ 小写（应该全大写）
yhmc VARCHAR(100)                   -- ❌ 拼音首字母
```

**字段后缀规范**：
- `_DATE` - 日期字段（精确到日期）
- `_TIME` - 时间字段（精确到时间）
- `_CODE` - 编码字段
- `_NAME` - 名称字段
- `_NO` - 编号字段
- `_FLAG` - 标志字段
- `_STATUS` - 状态字段

**关联字段命名一致性**：
```sql
-- ✅ 正确：多表关联字段命名一致
-- 用户表
CREATE TABLE SYS_USER (
    USER_ID VARCHAR(20) PRIMARY KEY,
    USER_CODE VARCHAR(20),
    ...
);

-- 用户角色表
CREATE TABLE SYS_USER_ROLE (
    ID VARCHAR(20) PRIMARY KEY,
    USER_ID VARCHAR(20),  -- ✅ 与SYS_USER.USER_ID一致
    ROLE_ID VARCHAR(20),
    ...
);

-- ❌ 错误：关联字段命名不一致
CREATE TABLE SYS_USER_ROLE (
    ID VARCHAR(20) PRIMARY KEY,
    U_ID VARCHAR(20),     -- ❌ 与USER_ID不一致
    ROLE_ID VARCHAR(20),
    ...
);
```

---

### ✅ 主键和索引命名规范

**指令**：主键、索引名称长度≤40字符，遵循固定格式。

```sql
-- ✅ 主键命名：PK_表名
ALTER TABLE TIR_TRANSPORT_HEAD
    ADD CONSTRAINT PK_TIR_TRANSPORT_HEAD PRIMARY KEY (TRANSPORT_ID);

-- ✅ 唯一索引命名：UK_表名_序号
CREATE UNIQUE INDEX UK_TIR_TRANSPORT_HEAD_1
    ON TIR_TRANSPORT_HEAD (TRANSPORT_NO);

CREATE UNIQUE INDEX UK_TIR_TRANSPORT_HEAD_2
    ON TIR_TRANSPORT_HEAD (CUSTOMS_CODE, YEAR, SERIAL_NO);

-- ✅ 普通索引命名：IX_表名_序号
CREATE INDEX IX_TIR_TRANSPORT_HEAD_1
    ON TIR_TRANSPORT_HEAD (DECL_DATE);

CREATE INDEX IX_TIR_TRANSPORT_HEAD_2
    ON TIR_TRANSPORT_HEAD (ORG_CODE, STATUS);

-- ❌ 错误示例
ALTER TABLE TIR_TRANSPORT_HEAD
    ADD CONSTRAINT PRI PRIMARY KEY (TRANSPORT_ID);  -- ❌ 未使用PK_前缀

CREATE INDEX idx_transport
    ON TIR_TRANSPORT_HEAD (DECL_DATE);  -- ❌ 未使用IX_前缀且小写
```

---

### ✅ 其他数据库对象命名

**指令**：序列、函数、存储过程、视图使用固定前缀。

```sql
-- ✅ 序列命名：SEQ_开头
CREATE SEQUENCE SEQ_USER_ID START WITH 1;

-- ✅ 存储过程命名：PROC_开头
CREATE PROCEDURE PROC_SYNC_USER_DATA() ...;

-- ✅ 函数命名：FN_开头
CREATE FUNCTION FN_CALC_TAX(amount DECIMAL) RETURNS DECIMAL ...;

-- ✅ 视图命名：V_开头
CREATE VIEW V_USER_ORG_INFO AS ...;
```

---

## 二、表设计

### ✅ 主键设计

**指令**：数据表必须包含主键，主键值不可修改，优先使用有序或趋势增长的字段。

```sql
-- ✅ 正确示例1：使用有业务含义的主键
CREATE TABLE ENTRY_HEAD (
    ENTRY_ID VARCHAR(18) PRIMARY KEY,  -- 海关编号：海关代码4位+年份4位+进出口标志1位+顺序号9位
    ...
);
-- 示例：2500202311234567890

-- ✅ 正确示例2：使用趋势增长的ID
CREATE TABLE SYS_USER (
    USER_ID BIGINT PRIMARY KEY,        -- 使用雪花算法或序列生成
    USER_CODE VARCHAR(20) NOT NULL,
    ...
);

-- ⚠️ 审慎使用自增列
CREATE TABLE SYS_LOG (
    LOG_ID BIGINT AUTO_INCREMENT PRIMARY KEY,  -- 自增步长设为2（海关业务网双中心）
    ...
);

-- ❌ 禁止：单独使用时间戳作为主键
CREATE TABLE EVENT_LOG (
    EVENT_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP PRIMARY KEY,  -- ❌ 时间戳可能重复
    ...
);
```

**主键设计原则**：
- ✅ 主键应具有业务含义或使用有序ID（如雪花算法）
- ✅ 自增列需使用时，步长设为2（适配双中心架构）
- ❌ 自增列不能有业务含义（海关业务网）
- ❌ 不得单独使用 `ON UPDATE CURRENT_TIMESTAMP` 的时间戳作为主键

---

### ✅ 必备字段

**指令**：所有业务表必须包含3个必备字段：版本号、创建时间、最后更新时间。

```sql
-- ✅ 正确示例：海关业务网
CREATE TABLE TIR_TRANSPORT_HEAD (
    TRANSPORT_ID VARCHAR(20) PRIMARY KEY,
    TRANSPORT_NO VARCHAR(30) NOT NULL,
    -- ... 业务字段 ...
    REC_VERSION INT DEFAULT 0 NOT NULL,                          -- 版本号
    REC_CREATE_TIME DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, -- 创建时间
    REC_LAST_UPDATE_TIME DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP NOT NULL                     -- 最后更新时间
);

-- ✅ 正确示例：电子口岸专网
CREATE TABLE MANIFEST_HEAD (
    MANIFEST_ID VARCHAR(20) PRIMARY KEY,
    -- ... 业务字段 ...
    REC_VERSION INT DEFAULT 0 NOT NULL,
    INDB_TIME DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,       -- 入库时间
    UPDATE_TIME DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP NOT NULL                     -- 更新时间
);
```

**必备字段说明**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `REC_VERSION` | INT | 0 | 版本号，每次更新时+1，用于乐观锁 |
| `REC_CREATE_TIME` (业务网) / `INDB_TIME` (口岸网) | DATETIME | CURRENT_TIMESTAMP | 数据入库时间 |
| `REC_LAST_UPDATE_TIME` (业务网) / `UPDATE_TIME` (口岸网) | DATETIME | CURRENT_TIMESTAMP ON UPDATE | 最后更新时间 |

**例外情况**：
- 不涉及业务的技术日志表
- 不做双中心数据同步的表

---

### ✅ 分区设计

**指令**：数据量增长较快的表应分区，表数据量超过2000万条时设计分区。

```sql
-- ✅ 正确示例：按日期分区
CREATE TABLE EVENT_LOG (
    LOG_ID BIGINT PRIMARY KEY,
    EVENT_TIME DATETIME NOT NULL,
    EVENT_TYPE VARCHAR(20),
    ARCHIVE_TIME DATETIME,  -- 可归档时间
    ...
) PARTITION BY RANGE (TO_DAYS(EVENT_TIME)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    PARTITION p202403 VALUES LESS THAN (TO_DAYS('2024-04-01'))
);

-- ✅ 分区表的索引应建成本地索引
CREATE INDEX IX_EVENT_LOG_1 LOCAL
    ON EVENT_LOG (EVENT_TYPE, EVENT_TIME);
```

**分区策略**：
- 按时间分区（常用）
- 按归档时间分区（便于数据清理）
- 分区表主键和索引必须建成本地索引

---

### ✅ 范式与冗余原则

**指令**：表设计原则上遵循第三范式，但允许适度冗余提升查询性能。

```sql
-- ✅ 正确示例：适度冗余提升性能
CREATE TABLE ORDER_HEAD (
    ORDER_ID VARCHAR(20) PRIMARY KEY,
    CUSTOMER_ID VARCHAR(20),
    CUSTOMER_NAME VARCHAR(100),     -- 冗余字段，避免频繁JOIN客户表
    PRODUCT_ID VARCHAR(20),
    PRODUCT_NAME VARCHAR(200),      -- 冗余字段，避免频繁JOIN产品表
    ...
);
```

**冗余字段选择原则**：
- ✅ 冗余字段应为非频繁修改字段（如客户名称、产品名称）
- ✅ 冗余字段应为关联查询常用字段
- ❌ 频繁变化的字段不应冗余（如价格、库存）

---

### ✅ 大对象存储

**指令**：视频、音频、图片等多媒体文件不得存入数据库。

```sql
-- ✅ 正确示例：仅存储文件元数据和路径
CREATE TABLE ATTACHMENT_INFO (
    ATTACHMENT_ID VARCHAR(20) PRIMARY KEY,
    FILE_NAME VARCHAR(200),
    FILE_TYPE VARCHAR(10),           -- 文件类型：jpg/png/pdf/mp4
    FILE_SIZE BIGINT,                -- 文件大小（字节）
    FILE_PATH VARCHAR(500),          -- 文件存储路径：/storage/2024/01/xxxx.jpg
    STORAGE_TYPE VARCHAR(10),        -- 存储类型：OSS/NAS/S3
    ...
);

-- ❌ 错误示例：存储大对象
CREATE TABLE ATTACHMENT_INFO (
    ATTACHMENT_ID VARCHAR(20) PRIMARY KEY,
    FILE_CONTENT BLOB,               -- ❌ 禁止将文件内容存入数据库
    ...
);
```

**大对象处理方案**：
- 文件存储到非结构化数据库（如MinIO、OSS）或文件系统
- 数据库仅存储文件元数据（文件名、大小、路径、类型）

---

### ✅ 数据清理设计

**指令**：年增长>1000万行的表，设计时应制定数据清理方案。

```sql
-- ✅ 正确示例：业务数据清理设计
CREATE TABLE CUSTOMS_DECL_HISTORY (
    DECL_ID VARCHAR(20) PRIMARY KEY,
    DECL_NO VARCHAR(30),
    ARCHIVE_TIME DATETIME,           -- 可归档时间（初始为空）
    ...
) PARTITION BY RANGE (TO_DAYS(ARCHIVE_TIME)) (
    PARTITION p_null VALUES LESS THAN (0),           -- 未归档数据
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01'))
);

-- 业务逻辑：满足归档条件时，写入ARCHIVE_TIME（如申报后3年）
-- 运维操作：按ARCHIVE_TIME分区删除历史数据
```

**数据生命周期管理**：

| 数据类型 | 生命周期建议 | 清理方式 |
|----------|-------------|---------|
| 业务数据 | 可归档时间字段（≤3年） | 按ARCHIVE_TIME分区清理 |
| 日志数据 | 3天/7天/30天 | 技术部门定期清理 |
| 报文数据 | 7天/30天 | 技术部门定期清理 |
| 中间数据 | 3天/7天 | 技术部门定期清理 |
| 等保要求数据 | 按等保要求 | 按等保策略执行 |

---

### ✅ 其他表设计要求

**指令**：表设计应遵循以下约束。

```sql
-- ✅ 每张表应有中文注释
CREATE TABLE TIR_TRANSPORT_HEAD (
    ...
) COMMENT='TIR运输业务表头，存储TIR运输单主要信息';

-- ✅ 审慎使用预留字段
-- ❌ 不推荐：RESERVED_FIELD1, RESERVED_FIELD2, ...

-- ✅ 单表字段数<200个
-- ✅ 单表字符型字段累加<8092字节（大字段除外）

-- ✅ 数据和索引不共用表空间
CREATE TABLE USER_DATA (...) TABLESPACE TS_DATA;
CREATE INDEX IX_USER_DATA_1 ON USER_DATA (...) TABLESPACE TS_INDEX;

-- ✅ 大对象使用单独表空间
CREATE TABLE REPORT_CONTENT (
    REPORT_ID VARCHAR(20),
    CONTENT TEXT,  -- 大字段
    ...
) TABLESPACE TS_LOB;
```

---

## 三、字段设计

### ✅ 数据类型和长度

**指令**：根据业务含义选择正确的数据类型。

```sql
-- ✅ 数值类型：业务含义是数值的，使用数值类型
CREATE TABLE PRODUCT_INFO (
    PRODUCT_ID VARCHAR(20) PRIMARY KEY,
    PRICE DECIMAL(10, 2),             -- 价格：使用DECIMAL，指定精度
    QUANTITY INT,                     -- 数量：整数用INT
    WEIGHT DECIMAL(12, 4),            -- 重量：使用DECIMAL(12,4)
    ...
);

-- ❌ 错误示例
CREATE TABLE PRODUCT_INFO (
    PRICE VARCHAR(20),                -- ❌ 价格应用DECIMAL
    QUANTITY DECIMAL(10, 2),          -- ❌ 整数不应用DECIMAL
    ...
);

-- ✅ 字符类型：使用VARCHAR，不使用CHAR
CREATE TABLE USER_INFO (
    USER_NAME VARCHAR(100),           -- ✅ 使用VARCHAR
    USER_CODE VARCHAR(20),
    ...
);

-- ❌ 错误示例
CREATE TABLE USER_INFO (
    USER_NAME CHAR(100),              -- ❌ 不使用CHAR（空间浪费）
    USER_DESC VARCHAR(MAX),           -- ❌ 不大量使用VARCHAR(MAX)
    ...
);

-- ✅ 日期时间类型：使用DATE/DATETIME
CREATE TABLE ORDER_HEAD (
    ORDER_DATE DATE,                  -- 精确到日期
    ORDER_TIME DATETIME,              -- 精确到时间
    ...
);

-- ❌ 错误示例
CREATE TABLE ORDER_HEAD (
    ORDER_DATE VARCHAR(10),           -- ❌ 日期字段应用DATE类型
    ORDER_TIME VARCHAR(20),           -- ❌ 时间字段应用DATETIME类型
    ...
);

-- ❌ 禁止使用LONG类型
-- ⚠️ 审慎使用TEXT/BLOB类型（如需使用，应分离到单独表）
CREATE TABLE REPORT_MASTER (
    REPORT_ID VARCHAR(20) PRIMARY KEY,
    REPORT_NAME VARCHAR(200),
    ...
);

CREATE TABLE REPORT_CONTENT (        -- TEXT字段分离存储
    REPORT_ID VARCHAR(20) PRIMARY KEY,
    CONTENT TEXT,
    ...
);
```

**数据类型选择原则**：
- 数值：INT / BIGINT / DECIMAL(precision, scale)
- 字符：VARCHAR（不使用CHAR / NCHAR / VARCHAR(MAX)）
- 日期时间：DATE / DATETIME（不使用VARCHAR）
- 禁止：LONG
- 审慎：TEXT / BLOB（需分离到单独表）

---

### ✅ 多表联查字段类型一致

**指令**：关联字段的数据类型必须相同。

```sql
-- ✅ 正确示例
CREATE TABLE ORDER_HEAD (
    ORDER_ID VARCHAR(20) PRIMARY KEY,
    CUSTOMER_ID VARCHAR(20),  -- VARCHAR(20)
    ...
);

CREATE TABLE ORDER_LIST (
    LIST_ID VARCHAR(20) PRIMARY KEY,
    ORDER_ID VARCHAR(20),     -- VARCHAR(20)，与ORDER_HEAD.ORDER_ID一致
    ...
);

-- ❌ 错误示例
CREATE TABLE ORDER_HEAD (
    ORDER_ID VARCHAR(20) PRIMARY KEY,
    ...
);

CREATE TABLE ORDER_LIST (
    ORDER_ID BIGINT,          -- ❌ 类型不一致，JOIN性能差
    ...
);
```

---

### ✅ NULL属性

**指令**：新增表所有字段不得同时为NULL；旧表新增字段尽量为NULL。

```sql
-- ✅ 正确示例：新建表，至少有部分字段NOT NULL
CREATE TABLE USER_INFO (
    USER_ID VARCHAR(20) PRIMARY KEY,
    USER_CODE VARCHAR(20) NOT NULL,
    USER_NAME VARCHAR(100) NOT NULL,
    PHONE VARCHAR(20),                -- 允许NULL
    EMAIL VARCHAR(100),               -- 允许NULL
    ...
);

-- ❌ 错误示例：所有字段都允许NULL
CREATE TABLE USER_INFO (
    USER_ID VARCHAR(20) PRIMARY KEY,
    USER_CODE VARCHAR(20),            -- ❌ 关键字段应NOT NULL
    USER_NAME VARCHAR(100),           -- ❌ 关键字段应NOT NULL
    ...
);

-- ✅ 旧表新增字段：尽量为NULL
ALTER TABLE USER_INFO ADD COLUMN ORG_CODE VARCHAR(20);  -- NULL，避免影响现有数据
```

---

### ✅ 字段注释

**指令**：每个字段必须有中文注释，说明字段含义、枚举值、编码规则。

```sql
-- ✅ 正确示例
CREATE TABLE CUSTOMS_DECL (
    DECL_ID VARCHAR(18) PRIMARY KEY COMMENT '海关编号：海关代码4位+年份4位+进出口标志1位+顺序号9位',
    DECL_TYPE CHAR(2) COMMENT '申报类型：01-进口 02-出口 03-转关 04-退运',
    TRADE_MODE VARCHAR(4) COMMENT '贸易方式代码，参见参数表SYS_PARA_TRADE_MODE',
    STATUS CHAR(2) COMMENT '状态：01-暂存 02-申报 03-审核中 04-通过 05-退单',
    REC_VERSION INT DEFAULT 0 COMMENT '版本号',
    REC_CREATE_TIME DATETIME COMMENT '记录创建时间',
    ...
);

-- ❌ 错误示例
CREATE TABLE CUSTOMS_DECL (
    DECL_ID VARCHAR(18) PRIMARY KEY COMMENT '申报ID',  -- ❌ 注释与字段名重复，无实际信息
    DECL_TYPE CHAR(2) COMMENT '类型',                  -- ❌ 未说明枚举值含义
    TRADE_MODE VARCHAR(4),                             -- ❌ 未添加注释
    ...
);
```

**字段注释要求**：
1. 注释内容不得与字段名称一样
2. 枚举值≤5个：在注释中列出所有枚举值含义
3. 枚举值>5个或可能追加：参数化，设计为单独参数表
4. 包含编码规则的字段：在注释中标明编码规则
5. 来自其他系统的数据，字段名称/值/含义发生变化：在注释中体现

---

## 四、索引设计

### ✅ 合理建立索引

**指令**：频繁使用的字段应建立索引，但每张表索引数量≤5个（大量多维度查询可适度增加）。

```sql
-- ✅ 正确示例
CREATE TABLE ORDER_HEAD (
    ORDER_ID VARCHAR(20) PRIMARY KEY,
    ORDER_NO VARCHAR(30),
    CUSTOMER_ID VARCHAR(20),
    ORDER_DATE DATE,
    STATUS CHAR(2),
    CREATE_TIME DATETIME,
    ...
);

-- 索引1：唯一索引（业务唯一键）
CREATE UNIQUE INDEX UK_ORDER_HEAD_1 ON ORDER_HEAD (ORDER_NO);

-- 索引2：组合索引（常用查询条件）
CREATE INDEX IX_ORDER_HEAD_1 ON ORDER_HEAD (CUSTOMER_ID, ORDER_DATE);

-- 索引3：状态查询索引
CREATE INDEX IX_ORDER_HEAD_2 ON ORDER_HEAD (STATUS, CREATE_TIME);

-- ❌ 错误：每个字段都建索引
CREATE INDEX IX_ORDER_HEAD_3 ON ORDER_HEAD (ORDER_ID);     -- ❌ 主键已有索引
CREATE INDEX IX_ORDER_HEAD_4 ON ORDER_HEAD (CUSTOMER_ID);  -- ❌ 已在组合索引中
CREATE INDEX IX_ORDER_HEAD_5 ON ORDER_HEAD (ORDER_DATE);   -- ❌ 已在组合索引中
```

**建立索引的原则**：
- ✅ SELECT/UPDATE/DELETE的WHERE条件列
- ✅ ORDER BY / GROUP BY / DISTINCT的字段
- ✅ 多表JOIN ON的关联字段
- ❌ 不使用函数索引
- ❌ 不使用位图索引

---

### ✅ 单列索引设计

**指令**：选择性低的列、大字段不建单列索引。

```sql
-- ✅ 正确示例：选择性高的列建索引
CREATE INDEX IX_USER_INFO_1 ON USER_INFO (USER_CODE);      -- 用户编号，选择性高
CREATE INDEX IX_USER_INFO_2 ON USER_INFO (ID_CARD_NO);     -- 身份证号，选择性高

-- ❌ 错误示例：选择性低的列不建索引
CREATE INDEX IX_USER_INFO_3 ON USER_INFO (GENDER);         -- ❌ 性别（男/女），选择性低
CREATE INDEX IX_USER_INFO_4 ON USER_INFO (STATUS);         -- ❌ 状态（01/02/03），选择性低

-- ❌ 错误示例：大字段不建索引
CREATE INDEX IX_REPORT_1 ON REPORT_INFO (CONTENT);         -- ❌ TEXT类型，不建索引
CREATE INDEX IX_ATTACHMENT_1 ON ATTACHMENT (FILE_PATH);    -- ❌ VARCHAR(4000)，过长
```

---

### ✅ 组合索引设计

**指令**：组合索引遵循"等值在左、范围在右、排序紧跟"原则。

```sql
-- ✅ 正确示例：等值查询列在左，范围查询列在右
CREATE INDEX IX_ORDER_HEAD_1
    ON ORDER_HEAD (CUSTOMER_ID, STATUS, ORDER_DATE);

-- 该索引可覆盖以下查询：
-- 1. WHERE CUSTOMER_ID = ? AND STATUS = ? AND ORDER_DATE = ?
-- 2. WHERE CUSTOMER_ID = ? AND STATUS = ?
-- 3. WHERE CUSTOMER_ID = ?
-- 4. WHERE CUSTOMER_ID = ? AND STATUS = ? AND ORDER_DATE >= ?

-- ❌ 错误示例：范围查询列在左侧
CREATE INDEX IX_ORDER_HEAD_2
    ON ORDER_HEAD (ORDER_DATE, CUSTOMER_ID, STATUS);  -- ❌ 范围查询列应在右侧

-- ✅ 正确示例：排序字段紧跟等值条件
CREATE INDEX IX_ORDER_HEAD_3
    ON ORDER_HEAD (CUSTOMER_ID, ORDER_DATE);  -- 支持 ORDER BY ORDER_DATE

-- ❌ 错误示例：组合索引与单列索引重复
CREATE INDEX IX_ORDER_HEAD_1 ON ORDER_HEAD (CUSTOMER_ID, ORDER_DATE);
CREATE INDEX IX_ORDER_HEAD_2 ON ORDER_HEAD (CUSTOMER_ID);  -- ❌ 重复，应删除

-- ❌ 错误示例：OR连接的列不建组合索引
SELECT * FROM ORDER_HEAD WHERE CUSTOMER_ID = ? OR ORDER_DATE = ?;
-- ❌ (CUSTOMER_ID, ORDER_DATE)组合索引无法生效
```

**组合索引设计原则**：
- ✅ 查询频繁、选择性好、等值查询的列放在左侧
- ✅ 范围查询列（>、<、>=、<=、BETWEEN）放在右侧
- ✅ ORDER BY列紧跟等值条件列
- ✅ 组合索引字段数≤5个
- ❌ 组合索引与单列索引不重复建设
- ❌ OR连接的查询列不建组合索引

---

## 五、数据库约束设计

### ❌ 禁止使用外键

**约束**：不得使用外键约束。

```sql
-- ❌ 错误示例：使用外键
CREATE TABLE ORDER_HEAD (
    ORDER_ID VARCHAR(20) PRIMARY KEY,
    CUSTOMER_ID VARCHAR(20),
    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID)  -- ❌ 禁止外键
);

-- ✅ 正确示例：在应用层保证数据完整性
CREATE TABLE ORDER_HEAD (
    ORDER_ID VARCHAR(20) PRIMARY KEY,
    CUSTOMER_ID VARCHAR(20)  -- ✅ 无外键约束
);

// Java代码中检查
if (!customerService.exists(dto.getCustomerId())) {
    throw new BizException("客户不存在");
}
```

**原因**：
- 影响分库分表扩展性
- 增加数据库负载
- 级联操作可能导致意外删除

---

### ❌ 禁止使用触发器

**约束**：不得使用数据库触发器。

```sql
-- ❌ 错误示例
CREATE TRIGGER trg_user_audit
AFTER UPDATE ON USER_INFO
FOR EACH ROW
BEGIN
    INSERT INTO AUDIT_LOG (...) VALUES (...);  -- ❌ 禁止触发器
END;

-- ✅ 正确示例：在应用代码中记录审计日志
@Transactional
public void updateUser(User user) {
    userDao.update(user);
    auditLogService.log("UPDATE", "USER_INFO", user.getUserId());  -- ✅ 应用层处理
}
```

---

### ⚠️ 审慎使用视图、存储过程、函数

**约束**：审慎使用视图、存储过程、自定义函数。

```sql
-- ⚠️ 审慎使用视图
CREATE VIEW V_USER_ORG AS
SELECT u.*, o.ORG_NAME
FROM USER_INFO u
LEFT JOIN ORG_INFO o ON u.ORG_CODE = o.ORG_CODE;

-- ⚠️ 审慎使用存储过程
CREATE PROCEDURE PROC_BATCH_UPDATE_STATUS(...)
BEGIN
    ...
END;
```

**原因**：
- 难以调试和维护
- 版本控制困难
- 业务逻辑分散

---

### ❌ 禁止使用DBLINK

**约束**：不得使用DBLINK跨数据库访问。

```sql
-- ❌ 错误示例
SELECT * FROM USER_INFO@REMOTE_DB;  -- ❌ 禁止DBLINK

-- ✅ 正确示例：通过API或消息队列获取远程数据
// Java代码
RemoteData data = remoteApiClient.fetchData();
```

---

### ❌ 禁止跨主用户授权

**约束**：A系统主用户不应直接授权给B系统主用户。

```sql
-- ❌ 错误示例
GRANT SELECT ON A_SYSTEM.USER_INFO TO B_SYSTEM;  -- ❌ 跨系统直接授权

-- ✅ 正确示例：A系统授权给B系统的专用账号B_A
CREATE USER B_A IDENTIFIED BY '...';
GRANT SELECT ON A_SYSTEM.USER_INFO TO B_A;  -- ✅ 授权给专用账号
```

---

## 六、设计文档要求

### ✅ 提供ER关系图

**指令**：数据库设计应提供ER图，明确实体关系。

ER图要求：
- 每个实体对应一个物理表
- 实体名为英文表名
- 包含主键和关联字段
- 明确标注关系（1:1、1:N、N:M）
- 逻辑分组（不同业务模块使用不同颜色）

**关联关系表**（如无ER图，应填写）：

| 父表表名 | 父表字段 | 子表表名 | 子表字段 | 关系类型 | 关系基数 |
|---------|---------|---------|---------|---------|---------|
| ENTRY_HEAD | ENTRY_ID | ENTRY_LIST | ENTRY_ID | 标识关系 | 1:N |
| USER_INFO | USER_ID | USER_ROLE | USER_ID | 非标识关系 | 1:N |

---

### ✅ 提供数据字典

**指令**：提供应用基本信息、表清单、字段清单。

**应用基本信息**：
- 应用名称、主管部门
- 实施单位联系人
- 业务联系人

**表清单**：
- 业务模块名称
- 数据表性质（主数据/业务数据/参数数据/日志数据等）
- 数据表中英文名称
- 数据来源（自产/调用）

**字段清单**：
- 数据库类型（Oracle/MySQL）
- 表名、字段名（中英文）
- 字段说明（含枚举值、编码规则）
- 字段类型、长度、精度
- 是否主键、是否可空

---

## 检查清单

数据库设计完成后，检查以下事项：

### 命名规范
- [ ] 表名符合规范（大写、包含应用简称、≤40字符）
- [ ] 字段名符合规范（大写、业务含义明确、≤40字符）
- [ ] 日期字段以_DATE结尾，时间字段以_TIME结尾
- [ ] 主键命名为PK_表名
- [ ] 索引命名为UK_表名_N或IX_表名_N

### 表设计
- [ ] 所有表包含主键
- [ ] 所有表包含必备字段（REC_VERSION、REC_CREATE_TIME、REC_LAST_UPDATE_TIME）
- [ ] 大表（>2000万行）已设计分区
- [ ] 每张表有中文注释
- [ ] 单表字段数<200个
- [ ] 大对象未存入数据库
- [ ] 年增长>1000万行的表已设计数据清理方案

### 字段设计
- [ ] 数值类型字段使用INT/BIGINT/DECIMAL
- [ ] 字符类型字段使用VARCHAR（非CHAR）
- [ ] 日期时间字段使用DATE/DATETIME（非VARCHAR）
- [ ] 多表关联字段类型一致
- [ ] 每个字段有中文注释
- [ ] 枚举字段在注释中说明枚举值
- [ ] 编码字段在注释中说明编码规则

### 索引设计
- [ ] 频繁查询字段已建索引
- [ ] 每张表索引数≤5个（或适度增加）
- [ ] 未在选择性低的列建索引
- [ ] 未在大字段建索引
- [ ] 组合索引遵循"等值在左、范围在右"原则
- [ ] 组合索引字段数≤5个
- [ ] 未建重复索引

### 约束设计
- [ ] 未使用外键
- [ ] 未使用触发器
- [ ] 未使用DBLINK
- [ ] 审慎使用视图、存储过程、函数

### 文档
- [ ] 提供ER图或关联关系表
- [ ] 提供应用基本信息
- [ ] 提供表清单
- [ ] 提供字段清单

---

## 相关规则

- 参见 [04-database-operations.md](./04-database-operations.md) 了解数据库操作规范
- 参见 [01-project-setup.md](./01-project-setup.md) 了解数据源配置
- 参见 [09-code-quality.md](./09-code-quality.md) 了解代码质量要求
