---
description: "必需字段规范：REC_VERSION、REC_CREATE_TIME等"
globs: ["**/*.sql"]
alwaysApply: false
---

# 数据库必需字段规范

## 技术字段要求

【强制】在技术层面，进行表结构设计时，每个表应当设计如下三个必需字段：

| 字段名 | 类型 | 字段说明 | 字段含义及说明 |
|-------|-----|---------|--------------|
| REC_VERSION | 整数 | 版本号 | 代表该条数据的版本号，每次更新时加1，默认值为0 |
| REC_CREATE_TIME | 带时间的日期 | 记录创建时间 | 记录第一次插入数据库时的系统时间 |
| REC_LAST_UPDATE_TIME | 带时间的日期 | 最后更新时间 | 每次数据更新时修改为当时的系统时间 |

## 字段定义

### REC_VERSION（版本号）

**作用**:
- 实现乐观锁机制
- 防止并发更新时的数据丢失
- 记录数据变更次数

**定义方式**:

```sql
-- MySQL
REC_VERSION INTEGER DEFAULT 0

-- Oracle
REC_VERSION NUMBER(20) DEFAULT 0

-- SQL Server
REC_VERSION INT DEFAULT 0
```

**使用示例**:

```java
// 乐观锁更新示例
@Service
public class EntryServiceImpl {

    public void updateEntry(Entry entry) {
        // 查询当前版本
        Entry currentEntry = entryRepository.findById(entry.getEntryId());
        int currentVersion = currentEntry.getRecVersion();

        // 更新时检查版本号
        int affectedRows = entryRepository.updateWithVersion(
            entry.getEntryId(),
            entry,
            currentVersion  // WHERE REC_VERSION = currentVersion
        );

        if (affectedRows == 0) {
            throw new OptimisticLockException("数据已被其他用户修改，请刷新后重试");
        }
    }
}
```

```sql
-- SQL示例：带版本号的更新
UPDATE T_ENTRY_HEAD
SET
    STATUS = '1',
    REC_VERSION = REC_VERSION + 1,  -- 版本号加1
    REC_LAST_UPDATE_TIME = GETDATE()
WHERE ENTRY_ID = 'xxx'
  AND REC_VERSION = 0;  -- 检查版本号

-- 如果 @@ROWCOUNT = 0 说明版本冲突
```

### REC_CREATE_TIME（记录创建时间）

**作用**:
- 记录数据首次创建的时间
- 用于数据审计
- 用于数据归档和清理

**定义方式**:

```sql
-- SQL Server
REC_CREATE_TIME DATETIME2 DEFAULT GETDATE()
REC_CREATE_TIME DATETIME2 NOT NULL DEFAULT GETDATE()

-- Oracle
REC_CREATE_TIME DATE DEFAULT SYSDATE
REC_CREATE_TIME TIMESTAMP DEFAULT SYSTIMESTAMP

-- MySQL
REC_CREATE_TIME DATETIME DEFAULT CURRENT_TIMESTAMP
REC_CREATE_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**使用示例**:

```sql
-- 插入时自动填充
INSERT INTO T_ENTRY_HEAD (ENTRY_ID, ENTRY_NO, REC_VERSION, REC_CREATE_TIME, REC_LAST_UPDATE_TIME)
VALUES ('E001', 'E202401010001', 0, GETDATE(), GETDATE());

-- 或者依赖默认值
INSERT INTO T_ENTRY_HEAD (ENTRY_ID, ENTRY_NO)
VALUES ('E001', 'E202401010001');  -- REC_CREATE_TIME自动填充为当前时间
```

### REC_LAST_UPDATE_TIME（最后更新时间）

**作用**:
- 记录数据最后一次修改的时间
- 用于数据同步和增量更新
- 用于数据审计

**定义方式**:

```sql
-- SQL Server
REC_LAST_UPDATE_TIME DATETIME2 DEFAULT GETDATE()
REC_LAST_UPDATE_TIME DATETIME2 NOT NULL DEFAULT GETDATE()

-- Oracle
REC_LAST_UPDATE_TIME DATE DEFAULT SYSDATE
REC_LAST_UPDATE_TIME TIMESTAMP DEFAULT SYSTIMESTAMP

-- MySQL
REC_LAST_UPDATE_TIME DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

**使用示例**:

```sql
-- 每次更新时必须更新此字段
UPDATE T_ENTRY_HEAD
SET
    STATUS = '1',
    REC_VERSION = REC_VERSION + 1,
    REC_LAST_UPDATE_TIME = GETDATE()  -- 更新为当前时间
WHERE ENTRY_ID = 'E001';
```

## 完整建表示例

### SQL Server 示例

```sql
CREATE TABLE T_ENTRY_HEAD (
    -- 主键
    ENTRY_ID VARCHAR(50) NOT NULL,

    -- 业务字段
    ENTRY_NO VARCHAR(50) NOT NULL,
    CUSTOMS_CODE VARCHAR(10) NOT NULL,
    TRADE_CODE VARCHAR(20),
    I_E_FLAG VARCHAR(1) NOT NULL,
    STATUS VARCHAR(10) NOT NULL DEFAULT '0',
    TOTAL_AMOUNT DECIMAL(18,2) DEFAULT 0.00,
    DECL_DATE DATE,

    -- 必需的技术字段
    REC_VERSION INT NOT NULL DEFAULT 0,
    REC_CREATE_TIME DATETIME2 NOT NULL DEFAULT GETDATE(),
    REC_LAST_UPDATE_TIME DATETIME2 NOT NULL DEFAULT GETDATE(),

    -- 可选备注字段
    REMARK VARCHAR(500),

    -- 主键约束
    CONSTRAINT PK_ENTRY_HEAD PRIMARY KEY (ENTRY_ID)
);

-- 创建索引
CREATE UNIQUE INDEX UQ_ENTRY_HEAD_ENTRY_NO ON T_ENTRY_HEAD(ENTRY_NO);
CREATE INDEX IDX_ENTRY_HEAD_STATUS ON T_ENTRY_HEAD(STATUS);
CREATE INDEX IDX_ENTRY_HEAD_UPDATE_TIME ON T_ENTRY_HEAD(REC_LAST_UPDATE_TIME);
```

### Oracle 示例

```sql
CREATE TABLE T_ENTRY_HEAD (
    -- 主键
    ENTRY_ID VARCHAR2(50) NOT NULL,

    -- 业务字段
    ENTRY_NO VARCHAR2(50) NOT NULL,
    CUSTOMS_CODE VARCHAR2(10) NOT NULL,
    TRADE_CODE VARCHAR2(20),
    I_E_FLAG VARCHAR2(1) NOT NULL,
    STATUS VARCHAR2(10) DEFAULT '0' NOT NULL,
    TOTAL_AMOUNT NUMBER(18,2) DEFAULT 0.00,
    DECL_DATE DATE,

    -- 必需的技术字段
    REC_VERSION NUMBER(20) DEFAULT 0 NOT NULL,
    REC_CREATE_TIME DATE DEFAULT SYSDATE NOT NULL,
    REC_LAST_UPDATE_TIME DATE DEFAULT SYSDATE NOT NULL,

    -- 可选备注字段
    REMARK VARCHAR2(500),

    -- 主键约束
    CONSTRAINT PK_ENTRY_HEAD PRIMARY KEY (ENTRY_ID)
);

-- 创建索引
CREATE UNIQUE INDEX UQ_ENTRY_HEAD_ENTRY_NO ON T_ENTRY_HEAD(ENTRY_NO);
CREATE INDEX IDX_ENTRY_HEAD_STATUS ON T_ENTRY_HEAD(STATUS);
CREATE INDEX IDX_ENTRY_HEAD_UPDATE_TIME ON T_ENTRY_HEAD(REC_LAST_UPDATE_TIME);

-- 创建序列
CREATE SEQUENCE SEQ_ENTRY_HEAD_ID
START WITH 1
INCREMENT BY 1
NOCACHE
NOCYCLE;
```

## Java实体类映射

### JPA实体类示例

```java
import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "T_ENTRY_HEAD")
public class EntryHead {

    @Id
    @Column(name = "ENTRY_ID", length = 50)
    private String entryId;

    @Column(name = "ENTRY_NO", length = 50, nullable = false)
    private String entryNo;

    @Column(name = "CUSTOMS_CODE", length = 10)
    private String customsCode;

    @Column(name = "STATUS", length = 10)
    private String status;

    // 必需的技术字段
    @Version  // JPA乐观锁注解
    @Column(name = "REC_VERSION", nullable = false)
    private Integer recVersion = 0;

    @Column(name = "REC_CREATE_TIME", nullable = false, updatable = false)
    private LocalDateTime recCreateTime;

    @Column(name = "REC_LAST_UPDATE_TIME", nullable = false)
    private LocalDateTime recLastUpdateTime;

    @PrePersist
    protected void onCreate() {
        recCreateTime = LocalDateTime.now();
        recLastUpdateTime = LocalDateTime.now();
        if (recVersion == null) {
            recVersion = 0;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        recLastUpdateTime = LocalDateTime.now();
    }

    // Getters and Setters...
}
```

### MyBatis映射示例

```xml
<mapper namespace="cn.gov.customs.h2018.entry.dao.EntryHeadMapper">

    <resultMap id="BaseResultMap" type="cn.gov.customs.h2018.entry.entity.EntryHead">
        <id column="ENTRY_ID" property="entryId"/>
        <result column="ENTRY_NO" property="entryNo"/>
        <result column="CUSTOMS_CODE" property="customsCode"/>
        <result column="STATUS" property="status"/>
        <result column="REC_VERSION" property="recVersion"/>
        <result column="REC_CREATE_TIME" property="recCreateTime"/>
        <result column="REC_LAST_UPDATE_TIME" property="recLastUpdateTime"/>
    </resultMap>

    <insert id="insert">
        INSERT INTO T_ENTRY_HEAD (
            ENTRY_ID,
            ENTRY_NO,
            CUSTOMS_CODE,
            STATUS,
            REC_VERSION,
            REC_CREATE_TIME,
            REC_LAST_UPDATE_TIME
        ) VALUES (
            #{entryId},
            #{entryNo},
            #{customsCode},
            #{status},
            0,
            #{recCreateTime},
            #{recLastUpdateTime}
        )
    </insert>

    <update id="update">
        UPDATE T_ENTRY_HEAD
        SET ENTRY_NO = #{entryNo},
            CUSTOMS_CODE = #{customsCode},
            STATUS = #{status},
            REC_VERSION = REC_VERSION + 1,
            REC_LAST_UPDATE_TIME = #{recLastUpdateTime}
        WHERE ENTRY_ID = #{entryId}
          AND REC_VERSION = #{recVersion}
    </update>

</mapper>
```

## 数据迁移和同步

### 增量同步示例

```sql
-- 查询增量数据（根据最后更新时间）
SELECT *
FROM T_ENTRY_HEAD
WHERE REC_LAST_UPDATE_TIME > @LAST_SYNC_TIME
ORDER BY REC_LAST_UPDATE_TIME;

-- 或者使用版本号
SELECT *
FROM T_ENTRY_HEAD
WHERE REC_VERSION > @LAST_SYNC_VERSION
ORDER BY REC_VERSION;
```

## 注意事项

1. 【强制】这三个技术字段在所有业务表中都必须存在
2. 【强制】应用程序不应该直接修改 REC_VERSION 字段（除了更新时加1）
3. 【强制】REC_CREATE_TIME 只在插入时设置一次，之后不应修改
4. 【强制】每次更新操作都必须更新 REC_LAST_UPDATE_TIME
5. 【推荐】使用数据库默认值或触发器自动维护这些字段
6. 【推荐】在ORM框架中使用相应的注解或拦截器自动处理

## 数据字典管理

在设计好数据结构后，【强制】必须整理符合海关规范的数据字典：

1. 使用数据字典EXCEL模板（`\\10.200.15.37\software\develop\hg-tools\dbtools\test.xls`）
2. 使用 ExcelToText.exe 工具生成建表脚本
3. 生成的脚本包含索引创建语句

## 相关规范

- 参见 [数据库设计规范](./database-design.md)
- 参见 [数据库命名规范](./database-naming.md)

## 来源文档

- 《海关应用云平台开发规范》- 00-cacp-spec.md 第4.2节
