---
title: "业务逻辑开发场景"
description: "Service层开发、单一职责、方法行数、DRY原则"
keywords:
  - Service层
  - 业务逻辑
  - 单一职责
  - 代码复用
  - 接口简化
tags:
  - 业务开发
  - Service
  - 代码质量
globs:
  - "**/*Service.java"
  - "**/*ServiceImpl.java"
  - "**/service/**/*.java"
alwaysApply: false
priority: medium
---

# 业务逻辑开发场景规范

## 场景概述

当在Service层开发业务逻辑时，遵循单一职责、代码简洁、逻辑清晰的原则，确保业务代码可维护、可测试。

## 核心规则

### ✅ 单一职责原则

**指令**：每个类和方法应有明确的单一职责，避免职责混乱。

```java
// ✅ 正确示例：职责清晰的Service
@Service
public class UserServiceImpl implements UserService {

    @Autowired
    private UserDao userDao;
    @Autowired
    private UserValidator userValidator;
    @Autowired
    private AuditLogService auditLogService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createUser(UserCreateDTO dto) {
        // 1. 数据校验
        userValidator.validateCreate(dto);

        // 2. 业务逻辑
        User user = buildUser(dto);
        userDao.insert(user);

        // 3. 审计日志
        auditLogService.log("CREATE_USER", user.getUserId());
    }

    private User buildUser(UserCreateDTO dto) {
        User user = new User();
        user.setUserId(generateUserId());
        user.setUserCode(dto.getUserCode());
        user.setUserName(dto.getUserName());
        user.setRecVersion(0);
        user.setRecCreateTime(LocalDateTime.now());
        return user;
    }
}

// ❌ 错误示例：职责混乱
@Service
public class UserService {
    @Transactional
    public void createUser(UserCreateDTO dto) {
        // ❌ 包含数据校验、业务逻辑、日志、邮件发送等多种职责
        if (dto.getUserCode() == null) throw new BizException("用户编号不能为空");
        if (userDao.existsByCode(dto.getUserCode())) throw new BizException("用户编号已存在");

        User user = new User();
        // ... 设置属性
        userDao.insert(user);

        // ❌ Service中直接发送邮件
        emailService.sendWelcomeEmail(user.getEmail());

        // ❌ Service中直接记录日志
        log.info("创建用户: {}", user.getUserCode());
    }
}
```

**Service层职责边界**：
- ✅ 业务规则判断和执行
- ✅ 调用DAO进行数据操作
- ✅ 调用其他Service
- ✅ 事务管理
- ❌ 参数校验（应在Controller或Validator中）
- ❌ 响应封装（应在Controller中）
- ❌ 直接操作HttpServletRequest/Response

---

### ✅ 方法行数限制

**指令**：方法行数应≤30行，复杂逻辑应拆分为多个小方法。

```java
// ✅ 正确示例：方法简洁，逻辑清晰
@Service
public class OrderServiceImpl implements OrderService {

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createOrder(OrderCreateDTO dto) {
        // 1. 校验库存
        validateStock(dto.getItems());

        // 2. 创建订单
        Order order = buildOrder(dto);
        orderDao.insert(order);

        // 3. 创建订单明细
        List<OrderDetail> details = buildOrderDetails(order.getOrderId(), dto.getItems());
        orderDetailDao.batchInsert(details);

        // 4. 扣减库存
        deductStock(dto.getItems());

        // 5. 发送通知
        sendOrderNotification(order);
    }

    private void validateStock(List<OrderItemDTO> items) {
        for (OrderItemDTO item : items) {
            int stock = stockDao.getStock(item.getProductCode());
            if (stock < item.getQuantity()) {
                throw new BizException("商品库存不足: " + item.getProductCode());
            }
        }
    }

    private Order buildOrder(OrderCreateDTO dto) {
        Order order = new Order();
        order.setOrderId(generateOrderId());
        order.setCustomerId(dto.getCustomerId());
        order.setOrderDate(LocalDate.now());
        order.setTotalAmount(calculateTotalAmount(dto.getItems()));
        order.setRecVersion(0);
        order.setRecCreateTime(LocalDateTime.now());
        return order;
    }

    // ... 其他私有方法
}

// ❌ 错误示例：方法过长（>50行）
@Transactional
public void createOrder(OrderCreateDTO dto) {
    // 100多行代码混在一起
    // 库存校验、订单创建、明细创建、库存扣减、通知发送...
    // 难以理解和维护
}
```

**方法拆分原则**：
- ✅ 每个方法完成一个明确的功能
- ✅ 方法名清晰表达其功能
- ✅ 私有方法用于拆分复杂逻辑
- ✅ 方法参数≤5个，过多参数应封装为对象

---

### ✅ DRY原则（Don't Repeat Yourself）

**指令**：避免代码重复，提取公共逻辑。

```java
// ✅ 正确示例：提取公共方法
@Service
public class UserServiceImpl implements UserService {

    @Override
    public void createUser(UserCreateDTO dto) {
        validateUserCode(dto.getUserCode());
        // ...
    }

    @Override
    public void updateUser(UserUpdateDTO dto) {
        validateUserCode(dto.getUserCode());
        // ...
    }

    // 公共校验方法
    private void validateUserCode(String userCode) {
        if (StringUtils.isBlank(userCode)) {
            throw new BizException("用户编号不能为空");
        }
        if (!userCode.matches("^[A-Z0-9]{6,20}$")) {
            throw new BizException("用户编号格式不正确");
        }
    }
}

// ❌ 错误示例：重复代码
@Service
public class UserService {
    public void createUser(UserCreateDTO dto) {
        // ❌ 重复的校验逻辑
        if (StringUtils.isBlank(dto.getUserCode())) {
            throw new BizException("用户编号不能为空");
        }
        if (!dto.getUserCode().matches("^[A-Z0-9]{6,20}$")) {
            throw new BizException("用户编号格式不正确");
        }
        // ...
    }

    public void updateUser(UserUpdateDTO dto) {
        // ❌ 重复的校验逻辑
        if (StringUtils.isBlank(dto.getUserCode())) {
            throw new BizException("用户编号不能为空");
        }
        if (!dto.getUserCode().matches("^[A-Z0-9]{6,20}$")) {
            throw new BizException("用户编号格式不正确");
        }
        // ...
    }
}
```

---

### ✅ 接口简化原则

**指令**：接口方法应简洁明了，避免过多参数。

```java
// ✅ 正确示例：使用DTO封装参数
public interface UserService {
    void createUser(UserCreateDTO dto);
    void updateUser(UserUpdateDTO dto);
    PageResult<User> queryUsers(UserQueryDTO dto);
}

// ❌ 错误示例：参数过多
public interface UserService {
    void createUser(
        String userCode,
        String userName,
        String orgCode,
        String phone,
        String email,
        Integer status,
        String remark
    );  // ❌ 参数过多，难以维护
}
```

---

### ✅ 判断逻辑优化

**指令**：复杂判断逻辑应提取到独立方法或使用策略模式。

```java
// ✅ 正确示例1：提取判断方法
@Service
public class OrderServiceImpl implements OrderService {

    public void processOrder(Order order) {
        if (canProcess(order)) {
            // 处理订单
            doProcess(order);
        }
    }

    private boolean canProcess(Order order) {
        return order != null
            && order.getStatus() != null
            && order.getStatus().equals(OrderStatus.PENDING)
            && order.getAmount() != null
            && order.getAmount().compareTo(BigDecimal.ZERO) > 0
            && !isExpired(order);
    }

    private boolean isExpired(Order order) {
        LocalDateTime expireTime = order.getCreateTime().plusDays(7);
        return LocalDateTime.now().isAfter(expireTime);
    }
}

// ✅ 正确示例2：使用策略模式
public interface OrderProcessor {
    boolean support(Order order);
    void process(Order order);
}

@Service
public class NormalOrderProcessor implements OrderProcessor {
    @Override
    public boolean support(Order order) {
        return OrderType.NORMAL.equals(order.getType());
    }

    @Override
    public void process(Order order) {
        // 普通订单处理逻辑
    }
}

@Service
public class UrgentOrderProcessor implements OrderProcessor {
    @Override
    public boolean support(Order order) {
        return OrderType.URGENT.equals(order.getType());
    }

    @Override
    public void process(Order order) {
        // 紧急订单处理逻辑
    }
}

@Service
public class OrderService {
    @Autowired
    private List<OrderProcessor> processors;

    public void processOrder(Order order) {
        processors.stream()
            .filter(p -> p.support(order))
            .findFirst()
            .ifPresent(p -> p.process(order));
    }
}

// ❌ 错误示例：复杂嵌套判断
public void processOrder(Order order) {
    if (order != null) {
        if (order.getStatus() != null) {
            if (order.getStatus().equals(OrderStatus.PENDING)) {
                if (order.getAmount() != null) {
                    if (order.getAmount().compareTo(BigDecimal.ZERO) > 0) {
                        if (order.getType().equals(OrderType.NORMAL)) {
                            // 普通订单处理
                        } else if (order.getType().equals(OrderType.URGENT)) {
                            // 紧急订单处理
                        } else if (order.getType().equals(OrderType.SPECIAL)) {
                            // 特殊订单处理
                        }
                    }
                }
            }
        }
    }
}
```

---

### ✅ Switch语句必须有default

**指令**：所有switch语句必须包含default分支。

```java
// ✅ 正确示例
public String getOrderStatusDesc(String status) {
    switch (status) {
        case "01":
            return "待审核";
        case "02":
            return "审核中";
        case "03":
            return "已通过";
        case "04":
            return "已退回";
        default:
            throw new BizException("未知订单状态: " + status);
    }
}

// ❌ 错误示例：缺少default
public String getOrderStatusDesc(String status) {
    switch (status) {
        case "01":
            return "待审核";
        case "02":
            return "审核中";
        case "03":
            return "已通过";
    }  // ❌ 缺少default，可能返回null
    return null;
}
```

---

## 场景实战

### 场景1：用户注册业务

**用户需求**：实现用户注册功能，包括数据校验、创建用户、分配默认角色、发送欢迎邮件

**AI应生成**：

```java
@Service
public class UserRegisterService {

    @Autowired
    private UserDao userDao;
    @Autowired
    private UserRoleDao userRoleDao;
    @Autowired
    private EmailService emailService;
    @Autowired
    private UserValidator userValidator;

    @Transactional(rollbackFor = Exception.class)
    public UserVO registerUser(UserRegisterDTO dto) {
        // 1. 数据校验
        userValidator.validateRegister(dto);

        // 2. 检查用户是否已存在
        checkUserExists(dto.getUserCode());

        // 3. 创建用户
        User user = buildUser(dto);
        userDao.insert(user);

        // 4. 分配默认角色
        assignDefaultRoles(user.getUserId());

        // 5. 发送欢迎邮件（异步）
        sendWelcomeEmailAsync(user);

        return convertToVO(user);
    }

    private void checkUserExists(String userCode) {
        if (userDao.existsByCode(userCode)) {
            throw new BizException("用户编号已存在");
        }
    }

    private User buildUser(UserRegisterDTO dto) {
        User user = new User();
        user.setUserId(generateUserId());
        user.setUserCode(dto.getUserCode());
        user.setUserName(dto.getUserName());
        user.setPassword(encryptPassword(dto.getPassword()));
        user.setEmail(dto.getEmail());
        user.setStatus(UserStatus.ACTIVE);
        user.setRecVersion(0);
        user.setRecCreateTime(LocalDateTime.now());
        return user;
    }

    private void assignDefaultRoles(String userId) {
        List<String> defaultRoleIds = Arrays.asList("ROLE_USER");
        List<UserRole> userRoles = defaultRoleIds.stream()
            .map(roleId -> new UserRole(userId, roleId))
            .collect(Collectors.toList());
        userRoleDao.batchInsert(userRoles);
    }

    @Async
    private void sendWelcomeEmailAsync(User user) {
        try {
            emailService.sendWelcomeEmail(user.getEmail(), user.getUserName());
        } catch (Exception e) {
            log.error("发送欢迎邮件失败: {}", user.getEmail(), e);
        }
    }
}
```

---

### 场景2：订单状态流转

**用户需求**：实现订单状态流转，不同状态有不同的处理逻辑

**AI应生成**：

```java
// 使用策略模式处理不同状态
public interface OrderStateHandler {
    OrderStatus currentState();
    OrderStatus nextState();
    void handle(Order order);
}

@Service
public class PendingOrderHandler implements OrderStateHandler {
    @Override
    public OrderStatus currentState() {
        return OrderStatus.PENDING;
    }

    @Override
    public OrderStatus nextState() {
        return OrderStatus.PROCESSING;
    }

    @Override
    public void handle(Order order) {
        // 待处理订单逻辑：校验库存
        validateStock(order);
    }
}

@Service
public class ProcessingOrderHandler implements OrderStateHandler {
    @Override
    public OrderStatus currentState() {
        return OrderStatus.PROCESSING;
    }

    @Override
    public OrderStatus nextState() {
        return OrderStatus.COMPLETED;
    }

    @Override
    public void handle(Order order) {
        // 处理中订单逻辑：扣减库存、生成出库单
        deductStock(order);
        createDeliveryNote(order);
    }
}

@Service
public class OrderStateService {
    @Autowired
    private List<OrderStateHandler> handlers;
    @Autowired
    private OrderDao orderDao;

    @Transactional(rollbackFor = Exception.class)
    public void processOrder(String orderId) {
        Order order = orderDao.selectById(orderId);

        // 查找当前状态的处理器
        OrderStateHandler handler = handlers.stream()
            .filter(h -> h.currentState().equals(order.getStatus()))
            .findFirst()
            .orElseThrow(() -> new BizException("未找到状态处理器"));

        // 执行业务逻辑
        handler.handle(order);

        // 更新状态
        order.setStatus(handler.nextState());
        orderDao.updateStatus(order);
    }
}
```

---

## 严格禁止的做法

### ❌ 禁止方法过长

```java
// ❌ 错误示例：方法超过100行
@Transactional
public void processOrder(OrderDTO dto) {
    // 数据校验：20行
    // 库存检查：15行
    // 价格计算：25行
    // 订单创建：20行
    // 明细创建：30行
    // 库存扣减：20行
    // 通知发送：15行
    // ... 超过150行
}

// ✅ 正确做法：拆分为多个方法
```

---

### ❌ 禁止God Class

```java
// ❌ 错误示例：万能类（包含所有业务）
@Service
public class BusinessService {
    public void createUser() {}
    public void createOrder() {}
    public void createProduct() {}
    public void processPayment() {}
    public void generateReport() {}
    // ... 包含100+个方法
}

// ✅ 正确做法：按业务领域拆分
@Service
public class UserService {}

@Service
public class OrderService {}

@Service
public class ProductService {}

@Service
public class PaymentService {}
```

---

### ❌ 禁止硬编码魔数和字符串

```java
// ❌ 错误示例
if (user.getStatus() == 1) {  // 1代表什么？
    // ...
}

if ("01".equals(order.getType())) {  // "01"代表什么？
    // ...
}

// ✅ 正确示例：使用常量或枚举
public class UserStatus {
    public static final Integer ACTIVE = 1;
    public static final Integer INACTIVE = 0;
    public static final Integer LOCKED = 2;
}

if (UserStatus.ACTIVE.equals(user.getStatus())) {
    // ...
}

// 或使用枚举
public enum OrderType {
    NORMAL("01", "普通订单"),
    URGENT("02", "紧急订单"),
    SPECIAL("03", "特殊订单");

    private String code;
    private String desc;

    // getter, constructor
}

if (OrderType.NORMAL.getCode().equals(order.getType())) {
    // ...
}
```

---

## 检查清单

业务逻辑开发完成后，检查以下事项：

- [ ] 每个类有明确的单一职责
- [ ] 方法行数≤30行
- [ ] 无重复代码（遵循DRY原则）
- [ ] 接口方法参数≤5个，复杂参数使用DTO
- [ ] 复杂判断逻辑已提取
- [ ] 所有switch语句有default分支
- [ ] 无魔数，状态值使用常量或枚举
- [ ] Service层不包含Controller职责
- [ ] Service层不直接操作HttpServletRequest/Response
- [ ] 事务管理合理（@Transactional配置正确）

---

## 相关规则

- 参见 [02-api-development.md](./02-api-development.md) 了解Controller层规范
- 参见 [04-database-operations.md](./04-database-operations.md) 了解数据库操作规范
- 参见 [06-exception-handling.md](./06-exception-handling.md) 了解异常处理
- 参见 [09-code-quality.md](./09-code-quality.md) 了解代码质量要求
