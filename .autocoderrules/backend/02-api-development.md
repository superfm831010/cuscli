---
title: "API开发场景"
description: "RESTful API设计、Controller开发、接口参数规范"
keywords:
  - REST API
  - Controller
  - HTTP方法
  - URL设计
  - 接口规范
tags:
  - API设计
  - 接口开发
globs:
  - "**/*Controller.java"
  - "**/controller/**/*.java"
  - "**/api/**/*.java"
alwaysApply: false
priority: high
---

# API开发场景规范

## 场景概述

当设计和开发RESTful API接口时，遵循海关统一的API设计规范，确保接口命名、HTTP方法使用、参数传递的一致性。

## 核心规则

### ✅ URL命名规范

**指令**：API路径使用小写字母和短横线（kebab-case）连接，禁止使用驼峰命名或下划线。

```java
// ✅ 正确示例
@RestController
@RequestMapping("/api/user-management")
public class UserManagementController {

    @GetMapping("/user-list")
    public Result getUserList() { }

    @PostMapping("/import-data")
    public Result importData() { }
}

// ❌ 错误示例
@RequestMapping("/api/userManagement")  // ❌ 驼峰命名
@GetMapping("/user_list")               // ❌ 下划线
@PostMapping("/ImportData")             // ❌ 大写字母
```

**原因**：
- 符合RESTful规范
- 提升URL可读性
- 统一API风格

---

### ✅ HTTP方法规范使用

**指令**：根据操作类型正确使用HTTP方法，海关规范中仅使用GET和POST。

```java
// ✅ 正确示例
@GetMapping("/users")           // 查询列表
@GetMapping("/users/{id}")      // 查询详情
@PostMapping("/users")          // 新增数据
@PostMapping("/users/update")   // 修改数据
@PostMapping("/users/delete")   // 删除数据

// ❌ 错误示例（海关规范不使用PUT/DELETE/PATCH）
@PutMapping("/users/{id}")      // ❌ 不使用PUT
@DeleteMapping("/users/{id}")   // ❌ 不使用DELETE
@PatchMapping("/users/{id}")    // ❌ 不使用PATCH
```

**HTTP方法选择原则**：
- **GET**：用于查询操作，无副作用，幂等
- **POST**：用于新增、修改、删除等变更操作

---

### ✅ 数据操作接口版本号规范

**指令**：删除和修改操作必须使用POST方法，并在请求中携带版本号（rec_version）实现乐观锁。

```java
// ✅ 正确示例：修改操作
@PostMapping("/users/update")
public Result updateUser(@RequestBody UserUpdateDTO dto) {
    // DTO必须包含rec_version字段
    if (dto.getRecVersion() == null) {
        throw new BizException("版本号不能为空");
    }

    // SQL: UPDATE users SET ... WHERE id = ? AND rec_version = ?
    int updated = userService.updateUser(dto);
    if (updated == 0) {
        throw new BizException("数据已被修改，请刷新后重试");
    }
    return Result.success();
}

// ✅ 正确示例：删除操作
@PostMapping("/users/delete")
public Result deleteUser(@RequestBody UserDeleteDTO dto) {
    // DTO必须包含rec_version字段
    if (dto.getRecVersion() == null) {
        throw new BizException("版本号不能为空");
    }

    // SQL: DELETE FROM users WHERE id = ? AND rec_version = ?
    int deleted = userService.deleteUser(dto.getId(), dto.getRecVersion());
    if (deleted == 0) {
        throw new BizException("数据已被删除或修改，请刷新后重试");
    }
    return Result.success();
}
```

**版本号机制说明**：
- 每次修改数据时，`rec_version` 字段值加1
- 修改/删除时，WHERE条件必须包含 `rec_version`
- 如果版本号不匹配，说明数据已被其他用户修改，操作失败

---

### ✅ 接口参数简洁明了

**指令**：接口参数应简洁，避免冗余参数，使用DTO对象封装复杂参数。

```java
// ✅ 正确示例：使用DTO封装复杂参数
@PostMapping("/users/query")
public Result<PageResult<User>> queryUsers(@RequestBody UserQueryDTO dto) {
    return Result.success(userService.queryUsers(dto));
}

// DTO定义
public class UserQueryDTO {
    private String userName;
    private String userCode;
    private String orgCode;
    private Integer pageNum;
    private Integer pageSize;
}

// ❌ 错误示例：大量零散参数
@GetMapping("/users/query")
public Result queryUsers(
    String userName,
    String userCode,
    String orgCode,
    String startDate,
    String endDate,
    Integer status,
    Integer type,
    Integer pageNum,
    Integer pageSize
) { }  // ❌ 参数过多，难以维护
```

**参数数量建议**：
- 简单查询：≤3个参数时可直接使用 `@RequestParam`
- 复杂查询：>3个参数时应封装为DTO对象

---

### ✅ Controller保持轻量

**指令**：Controller层仅负责请求参数校验、调用Service、响应封装，不包含业务逻辑。

```java
// ✅ 正确示例：轻量Controller
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping("/create")
    public Result createUser(@Valid @RequestBody UserCreateDTO dto) {
        // 1. 参数校验（由@Valid自动完成）
        // 2. 调用Service
        userService.createUser(dto);
        // 3. 返回结果
        return Result.success("用户创建成功");
    }
}

// ❌ 错误示例：Controller包含业务逻辑
@PostMapping("/create")
public Result createUser(@RequestBody UserCreateDTO dto) {
    // ❌ 业务逻辑不应在Controller中
    if (userDao.existsByCode(dto.getUserCode())) {
        throw new BizException("用户编号已存在");
    }

    User user = new User();
    user.setUserName(dto.getUserName());
    user.setUserCode(dto.getUserCode());
    user.setRecCreateTime(LocalDateTime.now());
    user.setRecVersion(0);

    userDao.insert(user);

    return Result.success();
}
```

**Controller职责边界**：
- ✅ 参数校验（Bean Validation）
- ✅ 调用Service方法
- ✅ 统一响应封装
- ❌ 业务规则判断
- ❌ 数据库操作
- ❌ 复杂计算逻辑

---

## 场景实战

### 场景1：开发用户管理CRUD接口

**用户需求**：实现用户的增删改查功能

**AI应生成**：

```java
@RestController
@RequestMapping("/api/user-management")
public class UserManagementController {

    @Autowired
    private UserService userService;

    // 查询用户列表
    @PostMapping("/query")
    public Result<PageResult<User>> queryUsers(@RequestBody UserQueryDTO dto) {
        return Result.success(userService.queryUsers(dto));
    }

    // 查询用户详情
    @GetMapping("/{id}")
    public Result<User> getUser(@PathVariable Long id) {
        return Result.success(userService.getUser(id));
    }

    // 新增用户
    @PostMapping("/create")
    public Result createUser(@Valid @RequestBody UserCreateDTO dto) {
        userService.createUser(dto);
        return Result.success("用户创建成功");
    }

    // 修改用户（携带版本号）
    @PostMapping("/update")
    public Result updateUser(@Valid @RequestBody UserUpdateDTO dto) {
        if (dto.getRecVersion() == null) {
            throw new BizException("版本号不能为空");
        }
        userService.updateUser(dto);
        return Result.success("用户修改成功");
    }

    // 删除用户（携带版本号）
    @PostMapping("/delete")
    public Result deleteUser(@RequestBody UserDeleteDTO dto) {
        if (dto.getRecVersion() == null) {
            throw new BizException("版本号不能为空");
        }
        userService.deleteUser(dto.getId(), dto.getRecVersion());
        return Result.success("用户删除成功");
    }
}
```

---

### 场景2：开发带条件查询的列表接口

**用户需求**：根据用户名、机构、状态查询用户列表，支持分页

**AI应生成**：

```java
// DTO定义
@Data
public class UserQueryDTO {
    private String userName;
    private String orgCode;
    private Integer status;
    private Integer pageNum = 1;
    private Integer pageSize = 20;
}

// Controller方法
@PostMapping("/query")
public Result<PageResult<UserVO>> queryUsers(@RequestBody UserQueryDTO dto) {
    // 参数校验
    if (dto.getPageNum() != null && dto.getPageNum() < 1) {
        throw new BizException("页码必须大于0");
    }
    if (dto.getPageSize() != null && dto.getPageSize() > 1000) {
        throw new BizException("每页最多查询1000条");
    }

    // 调用Service
    PageResult<UserVO> result = userService.queryUsers(dto);
    return Result.success(result);
}
```

---

## 严格禁止的做法

### ❌ 禁止在Controller中直接操作DAO

```java
// ❌ 错误示例
@RestController
public class UserController {
    @Autowired
    private UserDao userDao;  // ❌ Controller不应依赖DAO

    @GetMapping("/users/{id}")
    public Result getUser(@PathVariable Long id) {
        User user = userDao.selectById(id);  // ❌ 跳过Service层
        return Result.success(user);
    }
}

// ✅ 正确示例
@RestController
public class UserController {
    @Autowired
    private UserService userService;  // ✅ 依赖Service接口

    @GetMapping("/users/{id}")
    public Result getUser(@PathVariable Long id) {
        User user = userService.getUser(id);  // ✅ 通过Service获取
        return Result.success(user);
    }
}
```

---

### ❌ 禁止返回Entity实体

```java
// ❌ 错误示例：直接返回Entity
@GetMapping("/users/{id}")
public Result<User> getUser(@PathVariable Long id) {
    User user = userService.getUser(id);
    return Result.success(user);  // ❌ 暴露Entity
}

// ✅ 正确示例：返回VO对象
@GetMapping("/users/{id}")
public Result<UserVO> getUser(@PathVariable Long id) {
    UserVO userVO = userService.getUserVO(id);
    return Result.success(userVO);  // ✅ 使用VO封装
}
```

**原因**：
- Entity可能包含敏感字段（密码、内部标识）
- Entity字段变更会影响API稳定性
- VO可以按需组装数据，减少冗余字段

---

### ❌ 禁止使用魔数作为状态值

```java
// ❌ 错误示例
if (user.getStatus() == 1) {  // 1代表什么？
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
public enum UserStatus {
    ACTIVE(1, "正常"),
    INACTIVE(0, "停用"),
    LOCKED(2, "锁定");

    private Integer code;
    private String desc;
}
```

---

## 检查清单

API接口开发完成后，检查以下事项：

- [ ] URL使用小写+短横线命名
- [ ] 仅使用GET和POST方法
- [ ] 修改/删除操作携带rec_version版本号
- [ ] 复杂参数使用DTO封装
- [ ] Controller层保持轻量，无业务逻辑
- [ ] 不直接返回Entity，使用VO对象
- [ ] 参数使用Bean Validation校验
- [ ] 响应统一使用Result封装
- [ ] 无魔数，状态值使用常量/枚举
- [ ] 添加了接口注释（@ApiOperation等）

---

## 相关规则

- 参见 [05-business-logic.md](./05-business-logic.md) 了解Service层开发规范
- 参见 [06-exception-handling.md](./06-exception-handling.md) 了解异常处理规范
- 参见 [09-code-quality.md](./09-code-quality.md) 了解代码质量要求
