---
title: "异常处理场景"
description: "统一异常封装、异常处理规范、错误日志记录"
keywords:
  - 异常处理
  - BizException
  - 全局异常处理
  - 错误日志
tags:
  - 异常
  - 错误处理
globs:
  - "**/*.java"
alwaysApply: true
priority: high
---

# 异常处理场景规范

## 场景概述

当处理异常和错误时，遵循海关统一的异常处理规范，使用BizException封装业务异常，合理记录异常日志，提升系统可维护性。

## 核心规则

### ✅ 使用BizException封装业务异常

**指令**：业务异常统一使用BizException（或自定义业务异常）封装，不直接抛出RuntimeException。

```java
// ✅ 正确示例：使用BizException
@Service
public class UserServiceImpl implements UserService {

    public void createUser(UserCreateDTO dto) {
        // 业务校验失败，抛出BizException
        if (userDao.existsByCode(dto.getUserCode())) {
            throw new BizException("用户编号已存在: " + dto.getUserCode());
        }

        if (!isValidOrgCode(dto.getOrgCode())) {
            throw new BizException("无效的机构代码: " + dto.getOrgCode());
        }

        userDao.insert(buildUser(dto));
    }
}

// BizException定义
public class BizException extends RuntimeException {
    private String code;
    private String message;

    public BizException(String message) {
        super(message);
        this.code = "BIZ_ERROR";
        this.message = message;
    }

    public BizException(String code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }

    public BizException(String message, Throwable cause) {
        super(message, cause);
        this.code = "BIZ_ERROR";
        this.message = message;
    }
}

// ❌ 错误示例：直接抛出RuntimeException
public void createUser(UserCreateDTO dto) {
    if (userDao.existsByCode(dto.getUserCode())) {
        throw new RuntimeException("用户编号已存在");  // ❌ 不使用统一异常
    }
}

// ❌ 错误示例：抛出检查异常
public void createUser(UserCreateDTO dto) throws Exception {  // ❌ 不使用检查异常
    if (userDao.existsByCode(dto.getUserCode())) {
        throw new Exception("用户编号已存在");
    }
}
```

**异常分类**：
- **BizException** - 业务异常（如数据校验失败、业务规则不满足）
- **SystemException** - 系统异常（如配置错误、外部服务不可用）
- **DataException** - 数据异常（如数据库操作失败）

---

### ❌ 禁止printStackTrace

**约束**：严禁使用 `printStackTrace()` 打印异常堆栈，必须使用日志框架记录。

```java
// ❌ 错误示例：使用printStackTrace
try {
    userService.createUser(dto);
} catch (Exception e) {
    e.printStackTrace();  // ❌ 禁止使用
}

// ✅ 正确示例：使用日志框架
try {
    userService.createUser(dto);
} catch (BizException e) {
    log.error("创建用户失败: {}", dto.getUserCode(), e);
} catch (Exception e) {
    log.error("创建用户时发生系统异常", e);
    throw new SystemException("系统异常，请稍后重试", e);
}
```

**原因**：
- `printStackTrace()` 输出到控制台，生产环境无法查看
- 日志框架可统一管理日志输出、格式、级别
- 日志框架支持日志持久化和集中管理

---

### ✅ 异常日志记录规范

**指令**：异常日志应包含完整的上下文信息和异常堆栈。

```java
// ✅ 正确示例：完整的异常日志
@Service
public class OrderServiceImpl implements OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderServiceImpl.class);

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void processOrder(String orderId) {
        try {
            Order order = orderDao.selectById(orderId);
            if (order == null) {
                log.warn("订单不存在: orderId={}", orderId);
                throw new BizException("订单不存在");
            }

            // 业务处理
            doProcess(order);

        } catch (BizException e) {
            // 业务异常：WARN级别，记录关键信息
            log.warn("订单处理业务异常: orderId={}, message={}", orderId, e.getMessage());
            throw e;

        } catch (Exception e) {
            // 系统异常：ERROR级别，记录完整堆栈
            log.error("订单处理系统异常: orderId={}", orderId, e);
            throw new SystemException("订单处理失败", e);
        }
    }
}

// ❌ 错误示例：日志信息不完整
try {
    doProcess(order);
} catch (Exception e) {
    log.error("处理失败");  // ❌ 缺少上下文信息和异常堆栈
    throw e;
}
```

**异常日志级别**：
- **ERROR** - 系统异常、未预期的异常（需要记录完整堆栈）
- **WARN** - 业务异常、预期内的异常（记录关键信息）
- **INFO** - 正常流程日志
- **DEBUG** - 调试信息

---

### ✅ 全局异常处理

**指令**：使用@ControllerAdvice实现全局异常处理，统一返回格式。

```java
// ✅ 正确示例：全局异常处理器
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * 业务异常处理
     */
    @ExceptionHandler(BizException.class)
    public Result handleBizException(BizException e) {
        log.warn("业务异常: code={}, message={}", e.getCode(), e.getMessage());
        return Result.error(e.getCode(), e.getMessage());
    }

    /**
     * 参数校验异常处理
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result handleValidException(MethodArgumentNotValidException e) {
        BindingResult bindingResult = e.getBindingResult();
        String message = bindingResult.getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining("; "));

        log.warn("参数校验失败: {}", message);
        return Result.error("PARAM_ERROR", message);
    }

    /**
     * 系统异常处理
     */
    @ExceptionHandler(Exception.class)
    public Result handleException(Exception e) {
        log.error("系统异常", e);
        return Result.error("SYSTEM_ERROR", "系统异常，请稍后重试");
    }

    /**
     * 数据库异常处理
     */
    @ExceptionHandler(DataAccessException.class)
    public Result handleDataAccessException(DataAccessException e) {
        log.error("数据库操作异常", e);
        return Result.error("DB_ERROR", "数据操作失败");
    }
}

// 统一响应格式
public class Result<T> {
    private String code;      // 响应码
    private String message;   // 响应消息
    private T data;           // 响应数据

    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode("SUCCESS");
        result.setMessage("操作成功");
        result.setData(data);
        return result;
    }

    public static Result error(String code, String message) {
        Result result = new Result<>();
        result.setCode(code);
        result.setMessage(message);
        return result;
    }
}
```

---

### ✅ 异常处理最佳实践

**指令**：合理处理异常，不隐藏异常，不过度捕获。

```java
// ✅ 正确示例1：不捕获异常，让全局异常处理器处理
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping("/create")
    public Result createUser(@Valid @RequestBody UserCreateDTO dto) {
        // 不捕获异常，由全局异常处理器统一处理
        userService.createUser(dto);
        return Result.success("用户创建成功");
    }
}

// ✅ 正确示例2：需要特殊处理时才捕获
@Service
public class DataImportService {

    public ImportResult importData(List<DataDTO> dataList) {
        List<String> successIds = new ArrayList<>();
        List<String> errorMessages = new ArrayList<>();

        for (DataDTO data : dataList) {
            try {
                processData(data);
                successIds.add(data.getId());
            } catch (BizException e) {
                // 捕获业务异常，继续处理下一条
                errorMessages.add(data.getId() + ": " + e.getMessage());
                log.warn("导入数据失败: id={}, error={}", data.getId(), e.getMessage());
            }
        }

        return new ImportResult(successIds.size(), errorMessages.size(), errorMessages);
    }
}

// ❌ 错误示例1：捕获后不处理（吞掉异常）
try {
    userService.createUser(dto);
} catch (Exception e) {
    // ❌ 捕获后不处理，异常被吞掉
}

// ❌ 错误示例2：捕获后仅打印日志，不抛出
try {
    orderService.processOrder(orderId);
} catch (Exception e) {
    log.error("处理订单失败", e);
    // ❌ 应该重新抛出或返回错误，让调用方感知
}

// ✅ 正确做法：捕获后重新抛出
try {
    orderService.processOrder(orderId);
} catch (BizException e) {
    log.warn("订单处理业务异常", e);
    throw e;  // ✅ 重新抛出
} catch (Exception e) {
    log.error("订单处理系统异常", e);
    throw new SystemException("订单处理失败", e);  // ✅ 包装后抛出
}
```

---

## 场景实战

### 场景1：用户注册异常处理

**用户需求**：实现用户注册，处理各种异常情况

**AI应生成**：

```java
@Service
public class UserRegisterService {

    private static final Logger log = LoggerFactory.getLogger(UserRegisterService.class);

    @Autowired
    private UserDao userDao;
    @Autowired
    private EmailService emailService;

    @Transactional(rollbackFor = Exception.class)
    public UserVO registerUser(UserRegisterDTO dto) {
        log.info("开始注册用户: userCode={}", dto.getUserCode());

        try {
            // 1. 校验用户是否已存在
            if (userDao.existsByCode(dto.getUserCode())) {
                throw new BizException("USER_EXISTS", "用户编号已存在");
            }

            // 2. 创建用户
            User user = buildUser(dto);
            userDao.insert(user);
            log.info("用户创建成功: userId={}, userCode={}", user.getUserId(), user.getUserCode());

            // 3. 发送欢迎邮件（失败不影响注册）
            sendWelcomeEmail(user);

            return convertToVO(user);

        } catch (BizException e) {
            log.warn("用户注册业务异常: userCode={}, error={}", dto.getUserCode(), e.getMessage());
            throw e;

        } catch (DataAccessException e) {
            log.error("用户注册数据库异常: userCode={}", dto.getUserCode(), e);
            throw new SystemException("用户注册失败，请稍后重试", e);

        } catch (Exception e) {
            log.error("用户注册系统异常: userCode={}", dto.getUserCode(), e);
            throw new SystemException("系统异常，请联系管理员", e);
        }
    }

    private void sendWelcomeEmail(User user) {
        try {
            emailService.sendWelcomeEmail(user.getEmail(), user.getUserName());
            log.info("欢迎邮件发送成功: email={}", user.getEmail());
        } catch (Exception e) {
            // 邮件发送失败不影响注册，仅记录日志
            log.error("发送欢迎邮件失败: email={}", user.getEmail(), e);
        }
    }
}
```

---

### 场景2：批量操作异常处理

**用户需求**：批量导入数据，部分失败不影响其他数据

**AI应生成**：

```java
@Service
public class DataImportService {

    private static final Logger log = LoggerFactory.getLogger(DataImportService.class);

    @Autowired
    private DataService dataService;

    public ImportResult batchImport(List<DataImportDTO> dataList) {
        log.info("开始批量导入数据: count={}", dataList.size());

        List<String> successIds = new ArrayList<>();
        List<ImportError> errors = new ArrayList<>();

        for (int i = 0; i < dataList.size(); i++) {
            DataImportDTO data = dataList.get(i);
            try {
                // 导入单条数据
                dataService.importData(data);
                successIds.add(data.getId());

            } catch (BizException e) {
                // 业务异常：记录错误，继续处理下一条
                log.warn("导入数据业务异常: row={}, id={}, error={}",
                    i + 1, data.getId(), e.getMessage());
                errors.add(new ImportError(i + 1, data.getId(), e.getMessage()));

            } catch (Exception e) {
                // 系统异常：记录错误，继续处理下一条
                log.error("导入数据系统异常: row={}, id={}",
                    i + 1, data.getId(), e);
                errors.add(new ImportError(i + 1, data.getId(), "系统异常：" + e.getMessage()));
            }
        }

        log.info("批量导入完成: total={}, success={}, failed={}",
            dataList.size(), successIds.size(), errors.size());

        return new ImportResult(successIds.size(), errors.size(), errors);
    }
}

// 导入结果
public class ImportResult {
    private int successCount;
    private int failureCount;
    private List<ImportError> errors;
}

// 导入错误
public class ImportError {
    private int rowNum;
    private String dataId;
    private String errorMessage;
}
```

---

### 场景3：外部接口调用异常处理

**用户需求**：调用外部API，处理超时、网络异常等

**AI应生成**：

```java
@Service
public class ExternalApiService {

    private static final Logger log = LoggerFactory.getLogger(ExternalApiService.class);

    @Autowired
    private RestTemplate restTemplate;

    public ApiResponse callExternalApi(ApiRequest request) {
        log.info("调用外部API: url={}, requestId={}", request.getUrl(), request.getRequestId());

        try {
            ResponseEntity<ApiResponse> response = restTemplate.postForEntity(
                request.getUrl(),
                request,
                ApiResponse.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("外部API调用成功: requestId={}", request.getRequestId());
                return response.getBody();
            } else {
                log.error("外部API调用失败: requestId={}, statusCode={}",
                    request.getRequestId(), response.getStatusCode());
                throw new SystemException("外部API调用失败");
            }

        } catch (ResourceAccessException e) {
            // 超时或网络异常
            log.error("外部API调用超时: requestId={}", request.getRequestId(), e);
            throw new SystemException("外部API调用超时，请稍后重试", e);

        } catch (HttpClientErrorException e) {
            // 4xx客户端错误
            log.error("外部API参数错误: requestId={}, statusCode={}",
                request.getRequestId(), e.getStatusCode(), e);
            throw new BizException("API_PARAM_ERROR", "API参数错误");

        } catch (HttpServerErrorException e) {
            // 5xx服务端错误
            log.error("外部API服务异常: requestId={}, statusCode={}",
                request.getRequestId(), e.getStatusCode(), e);
            throw new SystemException("外部API服务异常", e);

        } catch (Exception e) {
            // 其他异常
            log.error("外部API调用异常: requestId={}", request.getRequestId(), e);
            throw new SystemException("外部API调用失败", e);
        }
    }
}
```

---

## 严格禁止的做法

### ❌ 禁止空catch块

```java
// ❌ 错误示例：空catch块
try {
    userService.createUser(dto);
} catch (Exception e) {
    // ❌ 空catch块，异常被吞掉
}

// ✅ 正确做法：至少记录日志
try {
    userService.createUser(dto);
} catch (Exception e) {
    log.error("创建用户失败", e);
    throw new SystemException("创建用户失败", e);
}
```

---

### ❌ 禁止捕获Throwable

```java
// ❌ 错误示例：捕获Throwable
try {
    doSomething();
} catch (Throwable t) {  // ❌ 不应捕获Throwable
    log.error("异常", t);
}

// ✅ 正确做法：捕获Exception
try {
    doSomething();
} catch (Exception e) {  // ✅ 捕获Exception
    log.error("异常", e);
}
```

**原因**：Throwable包括Error（如OutOfMemoryError），不应被应用代码捕获。

---

### ❌ 禁止在finally块中抛出异常

```java
// ❌ 错误示例：finally中抛出异常
try {
    doSomething();
} finally {
    cleanup();  // ❌ 如果cleanup()抛出异常，会覆盖try中的异常
}

// ✅ 正确做法：finally中捕获异常
try {
    doSomething();
} finally {
    try {
        cleanup();
    } catch (Exception e) {
        log.error("清理资源失败", e);
    }
}
```

---

## 检查清单

异常处理代码完成后，检查以下事项：

- [ ] 业务异常使用BizException封装
- [ ] 无printStackTrace()调用
- [ ] 异常日志包含完整上下文信息
- [ ] 使用全局异常处理器统一处理异常
- [ ] 无空catch块
- [ ] 不捕获Throwable
- [ ] finally块中不抛出异常
- [ ] @Transactional配置rollbackFor = Exception.class
- [ ] 异常不被吞掉（捕获后重新抛出或返回错误）
- [ ] 日志级别使用正确（ERROR/WARN/INFO/DEBUG）

---

## 相关规则

- 参见 [07-logging.md](./07-logging.md) 了解日志记录规范
- 参见 [02-api-development.md](./02-api-development.md) 了解API响应封装
- 参见 [04-database-operations.md](./04-database-operations.md) 了解事务管理
