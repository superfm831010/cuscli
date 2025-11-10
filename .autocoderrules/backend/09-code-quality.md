---
title: "代码质量场景"
description: "命名规范、注释规范、代码格式、工具类选择"
keywords:
  - 代码质量
  - 命名规范
  - 注释
  - 代码格式
  - 工具类
tags:
  - 代码质量
  - 规范
globs:
  - "**/*.java"
alwaysApply: false
priority: medium
---

# 代码质量场景规范

## 场景概述

当编写代码时，遵循统一的命名、注释、格式规范，使用合适的工具类和依赖，确保代码可读、可维护。

## 核心规则

### ✅ 命名规范

**指令**：类名、方法名、变量名使用规范的驼峰命名，见名知义。

```java
// ✅ 正确示例：类名使用大驼峰（PascalCase）
public class UserManagementService {}
public class OrderProcessorImpl {}
public class DataImportException {}

// ✅ 正确示例：方法名使用小驼峰（camelCase）
public void createUser() {}
public List<Order> queryOrdersByStatus(String status) {}
public boolean isValidUser(User user) {}

// ✅ 正确示例：变量名使用小驼峰
String userName = "张三";
int totalCount = 100;
LocalDateTime createTime = LocalDateTime.now();

// ✅ 正确示例：常量使用大写下划线
public class OrderStatus {
    public static final String PENDING = "01";
    public static final String COMPLETED = "02";
    public static final int MAX_RETRY_COUNT = 3;
}

// ❌ 错误示例：使用拼音
String yongHuMing = "张三";  // ❌ 拼音
public void chaXunYongHu() {}  // ❌ 拼音

// ❌ 错误示例：命名不清晰
String s = "张三";  // ❌ 单字母变量名（循环变量除外）
public void process() {}  // ❌ 方法名不明确
public void doIt() {}  // ❌ 方法名无意义
```

**命名规范总结**：
- 类名：大驼峰（UserService、OrderDTO）
- 方法名：小驼峰（createUser、queryOrders）
- 变量名：小驼峰（userName、totalAmount）
- 常量：大写下划线（MAX_SIZE、DEFAULT_VALUE）
- 包名：小写（cn.customs.user）

---

### ✅ 注释规范

**指令**：关键类和方法应添加JavaDoc注释，复杂逻辑添加行内注释。

```java
// ✅ 正确示例：类注释
/**
 * 用户管理服务
 * <p>
 * 提供用户的创建、修改、删除、查询功能
 * </p>
 *
 * @author 张三
 * @since 2024-01-01
 */
@Service
public class UserServiceImpl implements UserService {

    /**
     * 创建用户
     *
     * @param dto 用户创建DTO
     * @return 用户VO
     * @throws BizException 用户编号已存在时抛出
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public UserVO createUser(UserCreateDTO dto) {
        // 1. 校验用户编号是否已存在
        if (userDao.existsByCode(dto.getUserCode())) {
            throw new BizException("用户编号已存在");
        }

        // 2. 创建用户实体
        User user = buildUser(dto);

        // 3. 插入数据库
        userDao.insert(user);

        // 4. 记录审计日志
        auditLogService.log("CREATE_USER", user.getUserId());

        return convertToVO(user);
    }

    /**
     * 构建用户实体
     * <p>
     * 根据DTO设置用户属性，并设置默认值
     * </p>
     */
    private User buildUser(UserCreateDTO dto) {
        User user = new User();
        user.setUserId(generateUserId());
        user.setUserCode(dto.getUserCode());
        user.setUserName(dto.getUserName());
        user.setStatus(UserStatus.ACTIVE);  // 默认状态：激活
        user.setRecVersion(0);
        user.setRecCreateTime(LocalDateTime.now());
        return user;
    }
}

// ❌ 错误示例：无注释
@Service
public class UserServiceImpl implements UserService {
    public UserVO createUser(UserCreateDTO dto) {
        if (userDao.existsByCode(dto.getUserCode())) {
            throw new BizException("用户编号已存在");
        }
        // ... 100行代码，无任何注释
    }
}

// ❌ 错误示例：注释内容无用
/**
 * 创建用户
 */
public void createUser() {}  // ❌ 注释与方法名重复，无实际信息

/**
 * 方法
 */
public void method() {}  // ❌ 无意义注释
```

**注释规范总结**：
- 类注释：说明类的职责和功能
- 方法注释：说明方法用途、参数、返回值、异常
- 行内注释：解释复杂逻辑、业务规则、关键步骤
- 避免无用注释（与代码重复）
- 使用中文注释

---

### ✅ 代码行长度限制

**指令**：每行代码长度应≤120字符，过长代码应换行。

```java
// ✅ 正确示例：代码换行
log.info("订单处理完成: orderId={}, customerId={}, amount={}, status={}",
    order.getOrderId(),
    order.getCustomerId(),
    order.getAmount(),
    order.getStatus());

User user = User.builder()
    .userId(generateUserId())
    .userCode(dto.getUserCode())
    .userName(dto.getUserName())
    .status(UserStatus.ACTIVE)
    .build();

// ❌ 错误示例：单行过长
log.info("订单处理完成: orderId=" + order.getOrderId() + ", customerId=" + order.getCustomerId() + ", amount=" + order.getAmount() + ", status=" + order.getStatus());
```

---

### ✅ 清理无用导入

**指令**：删除未使用的import语句。

```java
// ✅ 正确示例：只导入使用的类
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class UserService {
    // ...
}

// ❌ 错误示例：导入未使用的类
import java.util.Map;        // ❌ 未使用
import java.util.Set;        // ❌ 未使用
import java.util.HashMap;    // ❌ 未使用
import org.apache.commons.lang3.StringUtils;  // ❌ 未使用

@Service
public class UserService {
    // ...
}
```

---

### ✅ 工具类选择

**指令**：优先使用成熟的工具类库，避免重复造轮子。

```java
// ✅ 正确示例：使用Apache Commons Lang
import org.apache.commons.lang3.StringUtils;

if (StringUtils.isBlank(userName)) {
    // ...
}

String result = StringUtils.trimToEmpty(input);

// ✅ 正确示例：使用Spring工具类
import org.springframework.util.CollectionUtils;

if (CollectionUtils.isEmpty(userList)) {
    // ...
}

// ✅ 正确示例：使用Hutool工具类
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.date.DateUtil;

String uuid = IdUtil.simpleUUID();
String dateStr = DateUtil.format(LocalDateTime.now(), "yyyy-MM-dd HH:mm:ss");

// ❌ 错误示例：自己实现已有的工具方法
public boolean isEmpty(String str) {
    return str == null || str.length() == 0;  // ❌ 使用StringUtils.isEmpty()
}

public boolean isEmpty(List list) {
    return list == null || list.size() == 0;  // ❌ 使用CollectionUtils.isEmpty()
}
```

**推荐工具类库**：
- **Apache Commons Lang3** - 字符串、数组、日期工具
- **Spring Framework** - 集合、反射、文件工具
- **Hutool** - 国产全面工具库
- **Google Guava** - 集合、缓存、并发工具

---

### ✅ 字符串拼接

**指令**：大量字符串拼接使用StringBuilder，少量拼接可使用+。

```java
// ✅ 正确示例：大量拼接使用StringBuilder
public String buildSql(List<String> columns, String tableName, List<String> conditions) {
    StringBuilder sql = new StringBuilder();
    sql.append("SELECT ");
    sql.append(String.join(", ", columns));
    sql.append(" FROM ");
    sql.append(tableName);

    if (!conditions.isEmpty()) {
        sql.append(" WHERE ");
        sql.append(String.join(" AND ", conditions));
    }

    return sql.toString();
}

// ✅ 正确示例：少量拼接使用+
String fullName = user.getFirstName() + " " + user.getLastName();
String message = "用户创建成功: " + user.getUserCode();

// ❌ 错误示例：循环中使用+拼接
String result = "";
for (String item : items) {
    result += item + ",";  // ❌ 性能差
}

// ✅ 正确做法：使用StringBuilder或String.join
String result = String.join(",", items);
```

---

### ❌ 禁止使用Date类

**约束**：使用Java 8的LocalDateTime/LocalDate，不使用Date类。

```java
// ✅ 正确示例：使用LocalDateTime
import java.time.LocalDateTime;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

LocalDateTime now = LocalDateTime.now();
LocalDate today = LocalDate.now();

String dateStr = now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

// 日期计算
LocalDateTime tomorrow = now.plusDays(1);
LocalDateTime lastMonth = now.minusMonths(1);

// ❌ 错误示例：使用Date
import java.util.Date;

Date now = new Date();  // ❌ 不使用Date

// ❌ 错误示例：使用SimpleDateFormat（线程不安全）
SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");  // ❌ 线程不安全
String dateStr = sdf.format(new Date());
```

**原因**：
- Date类设计不良，可变且线程不安全
- LocalDateTime/LocalDate不可变，线程安全
- LocalDateTime提供更丰富的日期操作API

---

### ❌ 禁止使用魔数

**约束**：数字常量应定义为常量，不直接使用魔数。

```java
// ✅ 正确示例：定义常量
public class OrderService {
    private static final int MAX_RETRY_COUNT = 3;
    private static final long TIMEOUT_MILLIS = 5000L;
    private static final BigDecimal MAX_AMOUNT = new BigDecimal("999999.99");

    public void processOrder(Order order) {
        if (order.getAmount().compareTo(MAX_AMOUNT) > 0) {
            throw new BizException("订单金额超过限额");
        }

        for (int i = 0; i < MAX_RETRY_COUNT; i++) {
            try {
                callExternalApi(order);
                break;
            } catch (Exception e) {
                if (i == MAX_RETRY_COUNT - 1) {
                    throw new BizException("API调用失败", e);
                }
            }
        }
    }
}

// ❌ 错误示例：使用魔数
public void processOrder(Order order) {
    if (order.getAmount().compareTo(new BigDecimal("999999.99")) > 0) {  // ❌ 魔数
        throw new BizException("订单金额超过限额");
    }

    for (int i = 0; i < 3; i++) {  // ❌ 魔数3
        // ...
    }
}
```

---

### ✅ 单例类私有变量禁止

**约束**：单例Service中不使用非final的私有成员变量。

```java
// ✅ 正确示例：无状态Service
@Service
public class UserService {
    @Autowired
    private UserDao userDao;  // ✅ 依赖注入的Bean

    private static final int MAX_COUNT = 100;  // ✅ final常量

    public void createUser(UserCreateDTO dto) {
        // 使用局部变量
        String userId = generateUserId();
        User user = buildUser(dto, userId);
        userDao.insert(user);
    }
}

// ❌ 错误示例：单例中使用实例变量
@Service
public class UserService {
    private int count;  // ❌ 非final实例变量（线程不安全）
    private User currentUser;  // ❌ 非final实例变量（线程不安全）

    public void processUser(User user) {
        this.currentUser = user;  // ❌ 多线程环境下有问题
        this.count++;  // ❌ 线程不安全
    }
}
```

**原因**：
- Spring的Service是单例
- 实例变量在多线程环境下不安全
- 应使用局部变量或ThreadLocal

---

### ✅ String.split检查结果

**约束**：使用String.split后检查数组长度。

```java
// ✅ 正确示例：检查split结果
public void parseAddress(String address) {
    String[] parts = address.split(",");
    if (parts.length < 3) {
        throw new BizException("地址格式不正确");
    }

    String province = parts[0];
    String city = parts[1];
    String district = parts[2];
    // ...
}

// ❌ 错误示例：未检查split结果
public void parseAddress(String address) {
    String[] parts = address.split(",");
    String province = parts[0];  // ❌ 可能IndexOutOfBoundsException
    String city = parts[1];
    String district = parts[2];
}
```

---

### ✅ 配置注入方式

**约束**：配置参数使用@Value或@ConfigurationProperties注入。

```java
// ✅ 正确示例1：使用@Value注入
@Service
public class FileUploadService {
    @Value("${file.upload.path}")
    private String uploadPath;

    @Value("${file.upload.max-size:10485760}")  // 默认值10MB
    private long maxFileSize;
}

// ✅ 正确示例2：使用@ConfigurationProperties
@Configuration
@ConfigurationProperties(prefix = "app.config")
@Data
public class AppConfig {
    private String uploadPath;
    private long maxFileSize;
    private List<String> allowedExtensions;
}

@Service
public class FileUploadService {
    @Autowired
    private AppConfig appConfig;
}

// ❌ 错误示例：硬编码配置
public class FileUploadService {
    private String uploadPath = "/data/upload";  // ❌ 硬编码
    private long maxFileSize = 10485760;  // ❌ 硬编码
}
```

---

### ✅ 依赖注入方式

**约束**：优先使用构造器注入，避免字段注入。

```java
// ✅ 正确示例1：构造器注入（推荐）
@Service
public class UserService {
    private final UserDao userDao;
    private final AuditLogService auditLogService;

    public UserService(UserDao userDao, AuditLogService auditLogService) {
        this.userDao = userDao;
        this.auditLogService = auditLogService;
    }
}

// ✅ 正确示例2：使用Lombok简化构造器注入
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserDao userDao;
    private final AuditLogService auditLogService;
}

// ⚠️ 可接受：字段注入（但不推荐）
@Service
public class UserService {
    @Autowired
    private UserDao userDao;
    @Autowired
    private AuditLogService auditLogService;
}
```

**构造器注入优点**：
- 依赖关系明确
- 便于单元测试
- 强制依赖不可变（final）

---

## 场景实战

### 场景1：重构低质量代码

**用户需求**：重构以下代码，提升代码质量

**原代码**：
```java
@Service
public class OrderService {
    @Autowired
    private OrderDao orderDao;

    public void process(Order o) {
        if (o.getAmount().compareTo(new BigDecimal("10000")) > 0) {
            String s = o.getCustomerId();
            Customer c = customerDao.selectById(s);
            if (c != null) {
                String n = c.getCustomerName();
                o.setCustomerName(n);
            }
        }
        orderDao.update(o);
    }
}
```

**AI应重构为**：
```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private static final BigDecimal HIGH_VALUE_THRESHOLD = new BigDecimal("10000");

    private final OrderDao orderDao;
    private final CustomerDao customerDao;

    /**
     * 处理订单
     * <p>
     * 高价值订单（>10000元）需要填充客户名称
     * </p>
     *
     * @param order 订单对象
     */
    @Transactional(rollbackFor = Exception.class)
    public void processOrder(Order order) {
        // 高价值订单：填充客户名称
        if (isHighValueOrder(order)) {
            fillCustomerName(order);
        }

        // 更新订单
        orderDao.update(order);
    }

    /**
     * 判断是否为高价值订单
     */
    private boolean isHighValueOrder(Order order) {
        return order.getAmount().compareTo(HIGH_VALUE_THRESHOLD) > 0;
    }

    /**
     * 填充客户名称
     */
    private void fillCustomerName(Order order) {
        Customer customer = customerDao.selectById(order.getCustomerId());
        if (customer != null) {
            order.setCustomerName(customer.getCustomerName());
        }
    }
}
```

---

## 检查清单

代码编写完成后，检查以下事项：

- [ ] 类名、方法名、变量名符合命名规范
- [ ] 无拼音命名
- [ ] 关键类和方法有JavaDoc注释
- [ ] 复杂逻辑有行内注释
- [ ] 代码行长度≤120字符
- [ ] 无未使用的import
- [ ] 优先使用工具类（不重复造轮子）
- [ ] 使用LocalDateTime/LocalDate，不使用Date
- [ ] 无魔数，数字常量已定义
- [ ] 单例Service无非final实例变量
- [ ] String.split后检查数组长度
- [ ] 配置参数使用@Value注入
- [ ] 优先使用构造器注入

---

## 相关规则

- 参见 [05-business-logic.md](./05-business-logic.md) 了解业务逻辑开发规范
- 参见 [07-logging.md](./07-logging.md) 了解日志记录规范
- 参见 [06-exception-handling.md](./06-exception-handling.md) 了解异常处理
