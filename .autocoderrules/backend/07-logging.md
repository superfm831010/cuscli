---
title: "日志记录场景"
description: "日志级别、日志内容、审计日志规范"
keywords:
  - 日志
  - Logger
  - 日志级别
  - 审计日志
tags:
  - 日志
  - 审计
globs:
  - "**/*.java"
alwaysApply: true
priority: high
---

# 日志记录场景规范

## 场景概述

当记录日志时，遵循海关统一的日志规范，合理使用日志级别，记录准确精简的日志内容，确保日志可读、可追溯。

## 核心规则

### ✅ 使用SLF4J门面

**指令**：统一使用SLF4J作为日志门面，不直接使用具体的日志实现。

```java
// ✅ 正确示例：使用SLF4J
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class UserServiceImpl implements UserService {

    private static final Logger log = LoggerFactory.getLogger(UserServiceImpl.class);

    public void createUser(UserCreateDTO dto) {
        log.info("开始创建用户: userCode={}", dto.getUserCode());
        // ...
        log.info("用户创建成功: userId={}", user.getUserId());
    }
}

// ❌ 错误示例：直接使用具体实现
import org.apache.log4j.Logger;  // ❌ 不直接使用Log4j

import java.util.logging.Logger;  // ❌ 不使用JUL
```

---

### ✅ 日志级别规范

**指令**：根据日志内容重要性，正确使用日志级别。

```java
@Service
public class OrderServiceImpl implements OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderServiceImpl.class);

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void processOrder(String orderId) {
        // DEBUG：调试信息，详细的执行过程
        log.debug("开始处理订单: orderId={}", orderId);

        Order order = orderDao.selectById(orderId);
        log.debug("订单信息: order={}", order);

        // INFO：正常业务流程的关键步骤
        log.info("订单状态变更: orderId={}, oldStatus={}, newStatus={}",
            orderId, order.getStatus(), newStatus);

        // WARN：警告信息，不影响主流程但需要关注
        if (order.getAmount().compareTo(MAX_AMOUNT) > 0) {
            log.warn("订单金额超过限额: orderId={}, amount={}, limit={}",
                orderId, order.getAmount(), MAX_AMOUNT);
        }

        // ERROR：错误信息，影响业务流程
        try {
            paymentService.pay(order);
        } catch (Exception e) {
            log.error("订单支付失败: orderId={}", orderId, e);
            throw new BizException("订单支付失败", e);
        }
    }
}
```

**日志级别使用原则**：

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| **ERROR** | 系统异常、业务流程中断、需要人工介入的错误 | 数据库连接失败、外部接口调用失败、事务回滚 |
| **WARN** | 潜在问题、业务异常但可继续、需要关注的情况 | 参数校验失败、业务规则不满足、配置缺失使用默认值 |
| **INFO** | 业务流程关键节点、状态变更、重要操作 | 用户登录、订单创建、数据导入完成 |
| **DEBUG** | 详细的执行过程、变量值、调试信息 | 方法入参、SQL参数、中间计算结果 |
| **TRACE** | 非常详细的跟踪信息（一般不使用） | 框架内部调用链 |

---

### ✅ 日志内容准确精简

**指令**：日志内容应准确表达业务含义，包含必要的上下文信息，避免冗余。

```java
// ✅ 正确示例：包含关键上下文信息
log.info("用户登录成功: userId={}, userCode={}, loginTime={}, ip={}",
    user.getUserId(), user.getUserCode(), LocalDateTime.now(), request.getRemoteAddr());

log.warn("库存不足: productCode={}, requestQty={}, availableQty={}",
    product.getProductCode(), requestQty, product.getStock());

log.error("订单支付失败: orderId={}, amount={}, paymentChannel={}",
    order.getOrderId(), order.getAmount(), paymentChannel, e);

// ❌ 错误示例：信息不完整
log.info("用户登录成功");  // ❌ 缺少关键信息（哪个用户？何时登录？）

log.warn("库存不足");      // ❌ 缺少上下文（哪个商品？需要多少？）

log.error("支付失败");      // ❌ 缺少异常信息和上下文

// ❌ 错误示例：信息冗余
log.info("开始执行用户创建方法createUser，传入的参数是{}", dto);  // ❌ 冗余描述
log.info("用户创建方法createUser执行完毕，返回结果是{}", result);  // ❌ 冗余描述

// ✅ 正确做法：简洁明了
log.info("创建用户: {}", dto);
log.info("用户创建完成: userId={}", user.getUserId());
```

**日志内容要求**：
- ✅ 包含关键业务标识（如userId、orderId）
- ✅ 包含操作结果和状态
- ✅ 错误日志包含异常堆栈
- ✅ 使用占位符 `{}` 而非字符串拼接
- ❌ 避免记录敏感信息（密码、身份证号、银行卡号）
- ❌ 避免记录大对象（如整个List、大文本）

---

### ✅ 使用占位符而非字符串拼接

**指令**：日志内容使用SLF4J占位符 `{}`，不使用字符串拼接。

```java
// ✅ 正确示例：使用占位符
log.info("用户登录: userCode={}, ip={}", userCode, ip);

log.error("订单处理失败: orderId={}", orderId, exception);

log.debug("查询参数: startDate={}, endDate={}, status={}",
    startDate, endDate, status);

// ❌ 错误示例：字符串拼接
log.info("用户登录: userCode=" + userCode + ", ip=" + ip);  // ❌ 字符串拼接

log.error("订单处理失败: orderId=" + orderId + ", error=" + exception.getMessage());

// ❌ 错误示例：先判断日志级别（不必要）
if (log.isDebugEnabled()) {  // ❌ 使用占位符时不需要判断
    log.debug("查询参数: startDate={}, endDate={}", startDate, endDate);
}
```

**原因**：
- 占位符方式性能更好（日志级别不满足时不会执行字符串拼接）
- 代码更简洁易读
- 避免空指针异常

**例外情况**（需要先判断日志级别）：
```java
// ✅ 复杂计算或大对象序列化时，先判断日志级别
if (log.isDebugEnabled()) {
    log.debug("复杂对象: {}", JSON.toJSONString(complexObject));  // ✅ 避免不必要的序列化
}
```

---

### ✅ DEBUG日志补充

**指令**：在关键业务逻辑中添加DEBUG日志，便于问题排查。

```java
@Service
public class OrderCalculationService {

    private static final Logger log = LoggerFactory.getLogger(OrderCalculationService.class);

    public BigDecimal calculateTotalAmount(Order order) {
        log.debug("开始计算订单金额: orderId={}", order.getOrderId());

        // 计算商品总价
        BigDecimal goodsAmount = order.getItems().stream()
            .map(item -> item.getPrice().multiply(new BigDecimal(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
        log.debug("商品总价: orderId={}, goodsAmount={}", order.getOrderId(), goodsAmount);

        // 计算折扣
        BigDecimal discount = calculateDiscount(order);
        log.debug("折扣金额: orderId={}, discount={}", order.getOrderId(), discount);

        // 计算运费
        BigDecimal freight = calculateFreight(order);
        log.debug("运费: orderId={}, freight={}", order.getOrderId(), freight);

        // 计算总金额
        BigDecimal totalAmount = goodsAmount.subtract(discount).add(freight);
        log.debug("订单总金额: orderId={}, totalAmount={}", order.getOrderId(), totalAmount);

        log.info("订单金额计算完成: orderId={}, totalAmount={}", order.getOrderId(), totalAmount);

        return totalAmount;
    }
}
```

**DEBUG日志使用场景**：
- 方法入参和返回值
- 复杂计算的中间结果
- 条件判断的分支
- 循环迭代的关键节点
- SQL执行的参数

---

### ✅ 审计日志记录

**指令**：重要的业务操作应记录审计日志，便于追溯。

```java
@Service
public class AuditLogService {

    @Autowired
    private AuditLogDao auditLogDao;

    /**
     * 记录审计日志
     *
     * @param operation 操作类型（CREATE_USER, UPDATE_ORDER, DELETE_DATA等）
     * @param businessId 业务对象ID
     * @param operatorId 操作人ID
     * @param operatorName 操作人姓名
     * @param detail 操作详情
     */
    public void log(String operation, String businessId, String operatorId,
                    String operatorName, String detail) {
        AuditLog auditLog = new AuditLog();
        auditLog.setLogId(generateLogId());
        auditLog.setOperation(operation);
        auditLog.setBusinessId(businessId);
        auditLog.setOperatorId(operatorId);
        auditLog.setOperatorName(operatorName);
        auditLog.setDetail(detail);
        auditLog.setOperateTime(LocalDateTime.now());
        auditLog.setIpAddress(getClientIp());

        auditLogDao.insert(auditLog);
    }
}

// 使用示例
@Service
public class UserServiceImpl implements UserService {

    @Autowired
    private AuditLogService auditLogService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteUser(String userId) {
        User user = userDao.selectById(userId);
        if (user == null) {
            throw new BizException("用户不存在");
        }

        // 删除用户
        userDao.deleteById(userId);

        // 记录审计日志
        auditLogService.log(
            "DELETE_USER",
            userId,
            getCurrentUserId(),
            getCurrentUserName(),
            "删除用户: " + user.getUserCode() + " - " + user.getUserName()
        );

        log.info("删除用户: userId={}, operator={}", userId, getCurrentUserName());
    }
}
```

**审计日志记录场景**：
- 用户登录/登出
- 数据的增删改操作
- 权限变更
- 敏感配置修改
- 重要业务操作（如审批、发布）

**审计日志内容**：
- 操作类型
- 业务对象ID
- 操作人信息（ID、姓名）
- 操作时间
- 操作详情
- IP地址

---

## 场景实战

### 场景1：用户登录日志

**用户需求**：记录用户登录过程日志

**AI应生成**：

```java
@Service
public class LoginService {

    private static final Logger log = LoggerFactory.getLogger(LoginService.class);

    @Autowired
    private UserDao userDao;
    @Autowired
    private AuditLogService auditLogService;

    public LoginResult login(LoginDTO dto, HttpServletRequest request) {
        String userCode = dto.getUserCode();
        String ip = request.getRemoteAddr();

        log.info("用户登录请求: userCode={}, ip={}", userCode, ip);

        try {
            // 1. 查询用户
            User user = userDao.selectByCode(userCode);
            if (user == null) {
                log.warn("用户不存在: userCode={}, ip={}", userCode, ip);
                throw new BizException("用户名或密码错误");
            }

            // 2. 校验密码
            if (!passwordEncoder.matches(dto.getPassword(), user.getPassword())) {
                log.warn("密码错误: userCode={}, ip={}", userCode, ip);
                // 增加失败次数
                increaseFailCount(user);
                throw new BizException("用户名或密码错误");
            }

            // 3. 检查用户状态
            if (!UserStatus.ACTIVE.equals(user.getStatus())) {
                log.warn("用户状态异常: userCode={}, status={}, ip={}",
                    userCode, user.getStatus(), ip);
                throw new BizException("用户已被禁用");
            }

            // 4. 生成token
            String token = generateToken(user);
            log.debug("生成token: userCode={}, token={}", userCode, token);

            // 5. 记录登录信息
            recordLoginInfo(user, ip);

            // 6. 记录审计日志
            auditLogService.log("USER_LOGIN", user.getUserId(), user.getUserId(),
                user.getUserName(), "用户登录成功，IP: " + ip);

            log.info("用户登录成功: userId={}, userCode={}, userName={}, ip={}",
                user.getUserId(), user.getUserCode(), user.getUserName(), ip);

            return new LoginResult(token, user);

        } catch (BizException e) {
            log.warn("用户登录失败: userCode={}, ip={}, reason={}",
                userCode, ip, e.getMessage());
            throw e;

        } catch (Exception e) {
            log.error("用户登录异常: userCode={}, ip={}", userCode, ip, e);
            throw new SystemException("登录失败，请稍后重试", e);
        }
    }
}
```

---

### 场景2：数据导入日志

**用户需求**：记录批量数据导入过程

**AI应生成**：

```java
@Service
public class DataImportService {

    private static final Logger log = LoggerFactory.getLogger(DataImportService.class);

    public ImportResult importData(List<DataDTO> dataList, String operatorId) {
        log.info("开始导入数据: count={}, operator={}", dataList.size(), operatorId);

        int successCount = 0;
        int failureCount = 0;
        List<String> errors = new ArrayList<>();

        for (int i = 0; i < dataList.size(); i++) {
            DataDTO data = dataList.get(i);
            log.debug("导入第{}条数据: {}", i + 1, data.getId());

            try {
                processData(data);
                successCount++;
                log.debug("第{}条数据导入成功: {}", i + 1, data.getId());

            } catch (BizException e) {
                failureCount++;
                String error = String.format("第%d条数据导入失败: %s - %s",
                    i + 1, data.getId(), e.getMessage());
                errors.add(error);
                log.warn(error);

            } catch (Exception e) {
                failureCount++;
                String error = String.format("第%d条数据导入异常: %s", i + 1, data.getId());
                errors.add(error);
                log.error(error, e);
            }
        }

        log.info("数据导入完成: total={}, success={}, failure={}, operator={}",
            dataList.size(), successCount, failureCount, operatorId);

        return new ImportResult(successCount, failureCount, errors);
    }
}
```

---

## 严格禁止的做法

### ❌ 禁止记录敏感信息

```java
// ❌ 错误示例：记录敏感信息
log.info("用户登录: userCode={}, password={}", userCode, password);  // ❌ 密码

log.info("用户信息: {}", user);  // ❌ user对象可能包含密码、身份证号等

log.debug("银行卡信息: cardNo={}", cardNo);  // ❌ 银行卡号

// ✅ 正确示例：脱敏处理
log.info("用户登录: userCode={}", userCode);  // ✅ 不记录密码

log.info("用户信息: userId={}, userCode={}", user.getUserId(), user.getUserCode());

log.debug("银行卡信息: cardNo={}", maskCardNo(cardNo));  // ✅ 脱敏：6225***1234
```

---

### ❌ 禁止在循环中打印INFO日志

```java
// ❌ 错误示例：循环中打印INFO日志
for (Order order : orders) {
    log.info("处理订单: {}", order.getOrderId());  // ❌ 大量INFO日志
    processOrder(order);
}

// ✅ 正确示例：使用DEBUG或汇总INFO
log.info("开始批量处理订单: count={}", orders.size());
for (Order order : orders) {
    log.debug("处理订单: {}", order.getOrderId());  // ✅ 使用DEBUG
    processOrder(order);
}
log.info("订单批量处理完成: count={}", orders.size());
```

---

### ❌ 禁止日志内容包含无用信息

```java
// ❌ 错误示例：无用信息
log.info("===================开始执行===================");  // ❌ 无用分隔符
log.info("进入createUser方法");                              // ❌ 冗余
log.info("现在开始创建用户");                                // ❌ 冗余
log.info("用户创建成功！！！");                              // ❌ 多余的感叹号

// ✅ 正确示例：简洁有效
log.info("创建用户: {}", dto);
log.info("用户创建完成: userId={}", user.getUserId());
```

---

## 检查清单

日志记录代码完成后，检查以下事项：

- [ ] 使用SLF4J门面（org.slf4j.Logger）
- [ ] 日志级别使用正确（ERROR/WARN/INFO/DEBUG）
- [ ] 日志内容包含必要的上下文信息
- [ ] 使用占位符 `{}`，不使用字符串拼接
- [ ] 错误日志包含异常堆栈
- [ ] 未记录敏感信息（密码、身份证号、银行卡号）
- [ ] 未在循环中打印INFO日志
- [ ] DEBUG日志覆盖关键业务逻辑
- [ ] 重要操作记录审计日志
- [ ] 日志内容简洁明了，无冗余信息

---

## 相关规则

- 参见 [06-exception-handling.md](./06-exception-handling.md) 了解异常日志记录
- 参见 [08-security.md](./08-security.md) 了解敏感信息脱敏
- 参见 [09-code-quality.md](./09-code-quality.md) 了解代码质量要求
