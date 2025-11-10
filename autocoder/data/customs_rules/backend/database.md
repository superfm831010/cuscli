---
description: "数据库设计和操作规范，包括表设计、SQL编写、事务管理等"
globs:
  - "**/*.java"
  - "**/*.py"
  - "**/*.xml"
  - "**/dao/**"
  - "**/mapper/**"
  - "**/repository/**"
alwaysApply: false
---

# 数据库设计和操作规范

## 规则条款

### 1. 数据操作接口规范

- **backend_043**: 删除或其它对数据库数据有操作的接口，应使用Post请求，执行语句带rec_version（版本号）条件
- 来源：backend_rules修订版.xlsx 第42行
- 说明：使用版本号实现乐观锁，防止并发更新冲突

### 2. 数据库表标准字段

- **backend_044**: 数据库表要包含以下三个字段：REC_VERSION（版本号）、REC_CREATE_TIME（创建时间）、REC_LAST_UPDATE_TIME（最后更新时间）
- 来源：backend_rules修订版.xlsx 第43行
- 说明：统一的标准字段用于乐观锁和审计

### 3. 事务管理

- **backend_045**: service中多次操作数据库要开启事务，且考虑抛出异常时数据库回滚问题
- 来源：backend_rules修订版.xlsx 第44行
- 说明：保证数据一致性，使用@Transactional注解

### 4. 主键命名规范

- **backend_046**: 数据库表设计时主键列名要有业务含义（如"USER_ID"）
- 来源：backend_rules修订版.xlsx 第45行
- 说明：有意义的列名提高可读性

### 5. SQL语句规范

- **backend_047**: mybatis的mapper.xml中编写sql注意，没有条件时不要留下where关键字
- 来源：backend_rules修订版.xlsx 第46行
- 说明：避免SQL语法错误

### 6. 配置注入方式

- **backend_048**: 读取配置文件中的配置，尽量使用@ConfigurationProperties注解类接收，减少@Value注解的使用
- 来源：backend_rules修订版.xlsx 第47行
- 说明：ConfigurationProperties提供更好的类型安全和IDE支持

### 7. 资源关闭

- **backend_049**: 在处理stream流时要有流关闭逻辑，推荐使用try-with-resources方式，或添加@Cleanup注解
- 来源：backend_rules修订版.xlsx 第48行
- 说明：确保资源被正确释放，避免资源泄漏

### 8. 依赖注入方式

- **backend_050**: 推荐使用构造器注入替换@Resource、@Autowired注入，可以使用@RequiredArgsConstructor注解简化（构造器注入指定bean时，需要手动添加构造方式并使用@Qualifier注解指定Bean）
- 来源：backend_rules修订版.xlsx 第49行
- 说明：构造器注入支持final字段，便于测试

## 数据库设计规范要点

以下规范来源：海关集中式事务型数据库设计规范.docx

### 命名规范

1. 数据库对象名应符合海关数据标准，采用常用英文或缩写，见名知义
2. 对象名由字母、数字和下划线"_"组成，以英文字母开头，单词间用下划线连接
3. 不得使用保留字、关键字（如DATE、RANK、ORDER、LIMIT、VALUE等）
4. 不得使用汉语拼音
5. 对象名统一大写
6. 字符集优先选用UTF-8

### 表命名规范

1. 表名应包含应用简称，长度40个字符以内
2. 预录入表前缀PRE，执法表CUR，参数表包含PARA
3. 表头表后缀HEAD，表体表后缀LIST
4. 日志表后缀LOG，临时表后缀TMP，异常表后缀EXCEPTION，备份表后缀BAK

### 表设计规范

1. 数据表应含有主键（技术日志表除外），主键值不得直接修改
2. 宜采用有序或趋势增长字段作为主键
3. 审慎使用数据库自增列做主键
4. 数据量超过2000万条时应设计分区
5. 分区表的主键、索引应建成本地索引

### 必备字段

1. REC_VERSION：版本号，整型，默认值0，每次更新加1
2. REC_CREATE_TIME：创建时间，时间类型，默认为入库时系统时间
3. REC_LAST_UPDATE_TIME：最后更新时间，时间类型，每次更新时修改

### 索引设计规范

1. 频繁使用的字段应建立索引（WHERE、ORDER BY、GROUP BY、JOIN字段）
2. 每张表索引数量尽量不超过5个
3. 不得使用函数索引和位图索引
4. 不得在选择性低的列建单列索引
5. 组合索引字段不超过5个

### 数据清理设计

1. 记录行数年增长大于1000万的表，应制定数据清理方案
2. 业务数据增加"可归档时间"字段，原则上不超过三年
3. 日志、中间数据、报文等非业务数据生命周期以3天、7天为宜，不超过30天

## 适用场景

本规则适用于涉及数据库操作的后端代码开发和数据库设计。
