---
title: "数据库操作场景"
description: "SQL编写、批量操作、事务管理、性能优化"
keywords:
  - SQL
  - MyBatis
  - 批量操作
  - 事务管理
  - 数据库性能
tags:
  - 数据库操作
  - SQL
  - 事务
globs:
  - "**/*Mapper.xml"
  - "**/*Dao.java"
  - "**/*Service*.java"
  - "**/mapper/**/*.xml"
  - "**/dao/**/*.java"
alwaysApply: false
priority: high
---

# 数据库操作场景规范

## 场景概述

当编写SQL语句、执行数据库操作时，遵循性能优化和安全规范，避免常见的性能陷阱和数据一致性问题。

## 核心规则

### ❌ 禁止循环操作数据库

**约束**：严禁在循环中执行数据库插入、更新、删除操作，必须使用批量操作。

```java
// ❌ 错误示例：循环插入（性能极差）
public void saveUsers(List<User> users) {
    for (User user : users) {
        userDao.insert(user);  // ❌ 每次循环都访问数据库
    }
}

// ✅ 正确示例：批量插入
public void saveUsers(List<User> users) {
    if (users != null && !users.isEmpty()) {
        userDao.batchInsert(users);  // ✅ 一次性批量插入
    }
}
```

```xml
<!-- MyBatis批量插入 -->
<insert id="batchInsert" parameterType="java.util.List">
    INSERT INTO USER_INFO (USER_ID, USER_CODE, USER_NAME, REC_VERSION, REC_CREATE_TIME)
    VALUES
    <foreach collection="list" item="item" separator=",">
        (#{item.userId}, #{item.userCode}, #{item.userName}, 0, NOW())
    </foreach>
</insert>
```

**批量操作的最佳实践**：
- 插入：使用 `INSERT INTO ... VALUES (...), (...), (...)`
- 更新：使用 `UPDATE ... SET ... WHERE id IN (...)`
- 删除：使用 `DELETE FROM ... WHERE id IN (...)`
- 批量大小：建议每批≤1000条，超大数据集分批处理

---

### ✅ SQL语句WHERE条件规范

**指令**：WHERE条件中的字段应建立索引，避免全表扫描。

```xml
<!-- ✅ 正确示例：使用索引字段 -->
<select id="queryUsers" resultType="User">
    SELECT * FROM USER_INFO
    WHERE USER_CODE = #{userCode}  <!-- USER_CODE已建立索引 -->
      AND STATUS = #{status}
      AND CREATE_TIME >= #{startTime}
</select>

<!-- ❌ 错误示例：在WHERE中使用函数，导致索引失效 -->
<select id="queryUsers" resultType="User">
    SELECT * FROM USER_INFO
    WHERE SUBSTRING(USER_CODE, 1, 4) = #{prefix}  <!-- ❌ 函数导致索引失效 -->
</select>

<!-- ✅ 正确做法：调整查询条件 -->
<select id="queryUsers" resultType="User">
    SELECT * FROM USER_INFO
    WHERE USER_CODE LIKE CONCAT(#{prefix}, '%')  <!-- ✅ 左侧匹配可使用索引 -->
</select>
```

**WHERE条件优化原则**：
- ✅ WHERE条件字段应有索引
- ✅ 避免在WHERE中对字段使用函数
- ✅ 使用参数化查询，防止SQL注入
- ❌ 避免 `SELECT *`，明确列出需要的字段
- ❌ 避免 `LIKE '%keyword%'`（全模糊匹配，索引失效）

---

### ✅ 事务管理

**指令**：合理使用事务，注意事务失效场景。

```java
// ✅ 正确示例：Service层使用@Transactional
@Service
public class UserServiceImpl implements UserService {

    @Transactional(rollbackFor = Exception.class)
    public void createUser(UserCreateDTO dto) {
        // 1. 插入用户
        User user = new User();
        // ... 设置属性
        userDao.insert(user);

        // 2. 插入用户角色关联
        userRoleDao.batchInsert(buildUserRoles(user.getUserId(), dto.getRoleIds()));

        // 3. 记录审计日志
        auditLogService.log("CREATE_USER", user.getUserId());

        // 任何步骤失败都会回滚
    }
}

// ❌ 事务失效场景1：同类方法调用
@Service
public class UserService {
    @Transactional
    public void createUser() {
        this.saveUser();  // ❌ 同类方法调用，事务失效
    }

    @Transactional
    public void saveUser() {
        userDao.insert(...);
    }
}

// ✅ 正确做法：通过Spring Bean调用
@Service
public class UserService {
    @Autowired
    private UserService self;  // 注入自身代理

    @Transactional
    public void createUser() {
        self.saveUser();  // ✅ 通过代理调用，事务生效
    }

    @Transactional
    public void saveUser() {
        userDao.insert(...);
    }
}

// ❌ 事务失效场景2：未捕获检查异常
@Transactional  // 默认只回滚RuntimeException
public void updateUser() {
    try {
        userDao.update(...);
        // 可能抛出检查异常
    } catch (Exception e) {
        // ❌ 捕获后未抛出，事务不回滚
        log.error("更新失败", e);
    }
}

// ✅ 正确做法：配置rollbackFor或重新抛出
@Transactional(rollbackFor = Exception.class)  // ✅ 回滚所有异常
public void updateUser() {
    userDao.update(...);
}
```

**事务使用原则**：
- ✅ Service层方法使用 `@Transactional`
- ✅ 配置 `rollbackFor = Exception.class` 回滚所有异常
- ✅ 事务方法应简短，避免长事务
- ❌ 避免同类方法调用导致事务失效
- ❌ 避免捕获异常后不抛出导致事务不回滚

---

### ✅ 关闭数据库资源

**指令**：使用Closeable资源时，必须在finally或try-with-resources中关闭。

```java
// ✅ 正确示例1：try-with-resources（推荐）
public List<User> queryUsers() {
    try (Connection conn = dataSource.getConnection();
         PreparedStatement ps = conn.prepareStatement(sql);
         ResultSet rs = ps.executeQuery()) {

        List<User> users = new ArrayList<>();
        while (rs.next()) {
            users.add(parseUser(rs));
        }
        return users;
    } catch (SQLException e) {
        throw new BizException("查询用户失败", e);
    }
}

// ✅ 正确示例2：finally中关闭
public List<User> queryUsers() {
    Connection conn = null;
    PreparedStatement ps = null;
    ResultSet rs = null;
    try {
        conn = dataSource.getConnection();
        ps = conn.prepareStatement(sql);
        rs = ps.executeQuery();

        List<User> users = new ArrayList<>();
        while (rs.next()) {
            users.add(parseUser(rs));
        }
        return users;
    } catch (SQLException e) {
        throw new BizException("查询用户失败", e);
    } finally {
        closeQuietly(rs);
        closeQuietly(ps);
        closeQuietly(conn);
    }
}

// ❌ 错误示例：未关闭资源
public List<User> queryUsers() {
    Connection conn = dataSource.getConnection();
    PreparedStatement ps = conn.prepareStatement(sql);
    ResultSet rs = ps.executeQuery();  // ❌ 未关闭，资源泄漏
    // ...
}
```

---

### ✅ 乐观锁实现

**指令**：修改和删除操作使用乐观锁（rec_version）防止并发冲突。

```xml
<!-- ✅ 正确示例：更新操作使用乐观锁 -->
<update id="updateUser" parameterType="User">
    UPDATE USER_INFO
    SET USER_NAME = #{userName},
        USER_CODE = #{userCode},
        REC_VERSION = REC_VERSION + 1,
        REC_LAST_UPDATE_TIME = NOW()
    WHERE USER_ID = #{userId}
      AND REC_VERSION = #{recVersion}  <!-- ✅ WHERE条件包含版本号 -->
</update>
```

```java
// Service层处理
@Transactional(rollbackFor = Exception.class)
public void updateUser(UserUpdateDTO dto) {
    int updated = userDao.updateUser(dto);
    if (updated == 0) {
        throw new BizException("数据已被修改，请刷新后重试");
    }
}
```

```xml
<!-- ✅ 正确示例：删除操作使用乐观锁 -->
<delete id="deleteUser">
    DELETE FROM USER_INFO
    WHERE USER_ID = #{userId}
      AND REC_VERSION = #{recVersion}  <!-- ✅ WHERE条件包含版本号 -->
</delete>
```

---

## 场景实战

### 场景1：批量导入用户数据

**用户需求**：从Excel导入1000条用户数据

**AI应生成**：

```java
@Service
public class UserImportService {

    @Autowired
    private UserDao userDao;

    private static final int BATCH_SIZE = 500;  // 每批500条

    @Transactional(rollbackFor = Exception.class)
    public ImportResult importUsers(List<UserImportDTO> dtos) {
        // 1. 数据校验
        List<User> validUsers = new ArrayList<>();
        List<String> errors = new ArrayList<>();

        for (int i = 0; i < dtos.size(); i++) {
            UserImportDTO dto = dtos.get(i);
            try {
                validateUser(dto);
                validUsers.add(convertToUser(dto));
            } catch (Exception e) {
                errors.add(String.format("第%d行: %s", i + 1, e.getMessage()));
            }
        }

        // 2. 分批插入
        int total = validUsers.size();
        for (int i = 0; i < total; i += BATCH_SIZE) {
            int end = Math.min(i + BATCH_SIZE, total);
            List<User> batch = validUsers.subList(i, end);
            userDao.batchInsert(batch);  // ✅ 批量插入
        }

        return new ImportResult(total, errors.size(), errors);
    }
}
```

---

### 场景2：分页查询优化

**用户需求**：根据条件查询用户列表，支持分页

**AI应生成**：

```xml
<!-- MyBatis分页查询 -->
<select id="queryUsers" resultType="User">
    SELECT
        USER_ID,
        USER_CODE,
        USER_NAME,
        ORG_CODE,
        STATUS,
        CREATE_TIME
    FROM USER_INFO
    <where>
        <if test="userCode != null and userCode != ''">
            AND USER_CODE = #{userCode}
        </if>
        <if test="userName != null and userName != ''">
            AND USER_NAME LIKE CONCAT('%', #{userName}, '%')
        </if>
        <if test="orgCode != null and orgCode != ''">
            AND ORG_CODE = #{orgCode}
        </if>
        <if test="status != null">
            AND STATUS = #{status}
        </if>
    </where>
    ORDER BY CREATE_TIME DESC
    LIMIT #{offset}, #{pageSize}
</select>

<!-- 查询总数 -->
<select id="countUsers" resultType="int">
    SELECT COUNT(1)
    FROM USER_INFO
    <where>
        <!-- 相同的WHERE条件 -->
    </where>
</select>
```

```java
// Service层
public PageResult<User> queryUsers(UserQueryDTO dto) {
    // 1. 查询总数
    int total = userDao.countUsers(dto);
    if (total == 0) {
        return new PageResult<>(0, Collections.emptyList());
    }

    // 2. 计算偏移量
    int offset = (dto.getPageNum() - 1) * dto.getPageSize();

    // 3. 查询数据
    List<User> users = userDao.queryUsers(dto, offset, dto.getPageSize());

    return new PageResult<>(total, users);
}
```

---

### 场景3：复杂查询优化

**用户需求**：查询订单及其明细、客户信息

**AI应生成**：

```xml
<!-- ✅ 正确示例：一次查询获取所有数据 -->
<select id="queryOrderDetail" resultMap="OrderDetailMap">
    SELECT
        o.ORDER_ID,
        o.ORDER_NO,
        o.ORDER_DATE,
        c.CUSTOMER_NAME,
        c.CUSTOMER_CODE,
        d.DETAIL_ID,
        d.PRODUCT_CODE,
        d.QUANTITY,
        d.PRICE
    FROM ORDER_HEAD o
    LEFT JOIN CUSTOMER c ON o.CUSTOMER_ID = c.CUSTOMER_ID
    LEFT JOIN ORDER_DETAIL d ON o.ORDER_ID = d.ORDER_ID
    WHERE o.ORDER_ID = #{orderId}
</select>

<resultMap id="OrderDetailMap" type="OrderVO">
    <id property="orderId" column="ORDER_ID"/>
    <result property="orderNo" column="ORDER_NO"/>
    <result property="orderDate" column="ORDER_DATE"/>
    <result property="customerName" column="CUSTOMER_NAME"/>
    <collection property="details" ofType="OrderDetailVO">
        <id property="detailId" column="DETAIL_ID"/>
        <result property="productCode" column="PRODUCT_CODE"/>
        <result property="quantity" column="QUANTITY"/>
        <result property="price" column="PRICE"/>
    </collection>
</resultMap>
```

```java
// ❌ 错误示例：N+1查询问题
public OrderVO getOrderDetail(String orderId) {
    Order order = orderDao.selectById(orderId);
    OrderVO vo = new OrderVO();
    // ...

    // ❌ 循环查询明细，产生N次数据库访问
    for (OrderDetail detail : orderDetailDao.selectByOrderId(orderId)) {
        vo.addDetail(detail);
    }

    return vo;
}
```

---

## 严格禁止的做法

### ❌ 禁止拼接SQL字符串

```java
// ❌ 错误示例：SQL注入风险
public List<User> queryUsers(String userName) {
    String sql = "SELECT * FROM USER_INFO WHERE USER_NAME = '" + userName + "'";
    return jdbcTemplate.query(sql, new UserRowMapper());  // ❌ SQL注入风险
}

// ✅ 正确示例：参数化查询
public List<User> queryUsers(String userName) {
    String sql = "SELECT * FROM USER_INFO WHERE USER_NAME = ?";
    return jdbcTemplate.query(sql, new Object[]{userName}, new UserRowMapper());
}
```

---

### ❌ 禁止在事务中执行耗时操作

```java
// ❌ 错误示例：事务中调用外部接口
@Transactional
public void createOrder(OrderDTO dto) {
    orderDao.insert(order);

    // ❌ 调用外部支付接口（耗时操作）
    paymentClient.createPayment(order.getOrderId());  // 可能超时，导致长事务

    orderDao.updateStatus(order.getOrderId(), "PAID");
}

// ✅ 正确示例：事务外调用外部接口
public void createOrder(OrderDTO dto) {
    // 1. 事务内创建订单
    createOrderInTransaction(dto);

    // 2. 事务外调用支付
    try {
        paymentClient.createPayment(order.getOrderId());
        updateOrderStatus(order.getOrderId(), "PAID");
    } catch (Exception e) {
        updateOrderStatus(order.getOrderId(), "FAILED");
    }
}

@Transactional(rollbackFor = Exception.class)
public void createOrderInTransaction(OrderDTO dto) {
    orderDao.insert(order);
}
```

---

### ❌ 禁止使用SELECT *

```xml
<!-- ❌ 错误示例 -->
<select id="queryUsers" resultType="User">
    SELECT * FROM USER_INFO  <!-- ❌ 查询所有字段 -->
    WHERE USER_CODE = #{userCode}
</select>

<!-- ✅ 正确示例 -->
<select id="queryUsers" resultType="User">
    SELECT
        USER_ID,
        USER_CODE,
        USER_NAME,
        ORG_CODE,
        STATUS
    FROM USER_INFO  <!-- ✅ 明确列出字段 -->
    WHERE USER_CODE = #{userCode}
</select>
```

**原因**：
- 减少网络传输数据量
- 避免查询不需要的字段
- 提高查询性能

---

### ❌ 禁止使用游标

```java
// ❌ 错误示例：使用数据库游标
Statement stmt = conn.createStatement(
    ResultSet.TYPE_SCROLL_INSENSITIVE,
    ResultSet.CONCUR_READ_ONLY
);
ResultSet rs = stmt.executeQuery("SELECT * FROM USER_INFO");
while (rs.next()) {
    // 逐行处理
}

// ✅ 正确示例：批量查询+内存处理
List<User> users = userDao.queryAll();
for (User user : users) {
    // 业务处理
}

// ✅ 大数据量场景：分批查询
int pageSize = 1000;
int pageNum = 1;
while (true) {
    List<User> users = userDao.queryByPage(pageNum, pageSize);
    if (users.isEmpty()) break;

    for (User user : users) {
        // 业务处理
    }
    pageNum++;
}
```

---

## 检查清单

数据库操作代码完成后，检查以下事项：

- [ ] 无循环操作数据库，使用批量操作
- [ ] WHERE条件字段已建立索引
- [ ] 使用参数化查询，无SQL拼接
- [ ] 使用@Transactional管理事务
- [ ] 配置rollbackFor = Exception.class
- [ ] 无同类方法调用导致事务失效
- [ ] 修改/删除操作使用乐观锁（rec_version）
- [ ] Closeable资源已关闭
- [ ] 无SELECT *，明确列出字段
- [ ] 分页查询使用LIMIT
- [ ] 无长事务（事务中无耗时操作）
- [ ] 批量操作每批≤1000条

---

## 相关规则

- 参见 [03-database-design.md](./03-database-design.md) 了解数据库设计规范
- 参见 [06-exception-handling.md](./06-exception-handling.md) 了解异常处理
- 参见 [09-code-quality.md](./09-code-quality.md) 了解代码质量要求
