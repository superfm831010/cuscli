---
title: "安全防护场景"
description: "XSS防护、SQL注入防护、敏感信息脱敏、缓存安全"
keywords:
  - 安全
  - XSS
  - SQL注入
  - 敏感信息脱敏
  - Redis安全
tags:
  - 安全
  - 防护
globs:
  - "**/*.java"
alwaysApply: true
priority: high
---

# 安全防护场景规范

## 场景概述

当开发涉及用户输入、数据存储、外部交互的功能时，遵循海关安全规范，防范XSS、SQL注入等安全威胁，保护敏感信息。

## 核心规则

### ✅ XSS防护

**指令**：对用户输入进行XSS过滤，特别是前端显示的内容。

```java
// ✅ 正确示例：使用Spring HTML工具类过滤
import org.springframework.web.util.HtmlUtils;

@Service
public class ContentService {

    public void saveContent(ContentDTO dto) {
        Content content = new Content();
        // 对用户输入进行HTML转义
        content.setTitle(HtmlUtils.htmlEscape(dto.getTitle()));
        content.setContent(HtmlUtils.htmlEscape(dto.getContent()));
        contentDao.insert(content);
    }

    public ContentVO getContent(String contentId) {
        Content content = contentDao.selectById(contentId);
        ContentVO vo = new ContentVO();
        // 显示时反转义（如果需要）
        vo.setTitle(content.getTitle());
        vo.setContent(content.getContent());
        return vo;
    }
}

// ✅ 正确示例：使用OWASP Java Encoder
import org.owasp.encoder.Encode;

public String renderHtml(String userInput) {
    return Encode.forHtml(userInput);
}

public String renderJavaScript(String userInput) {
    return Encode.forJavaScript(userInput);
}

// ❌ 错误示例：直接存储和显示用户输入
@Service
public class ContentService {
    public void saveContent(ContentDTO dto) {
        Content content = new Content();
        content.setTitle(dto.getTitle());          // ❌ 未过滤
        content.setContent(dto.getContent());      // ❌ 未过滤，可能包含<script>标签
        contentDao.insert(content);
    }
}
```

**XSS防护场景**：
- 用户输入的文本内容（标题、描述、评论）
- 富文本编辑器内容
- URL参数显示
- 用户自定义配置

---

### ✅ SQL注入防护

**指令**：使用参数化查询，禁止拼接SQL字符串。

```java
// ✅ 正确示例：使用MyBatis参数化查询
@Repository
public interface UserDao {
    User selectByCode(@Param("userCode") String userCode);

    List<User> queryUsers(@Param("dto") UserQueryDTO dto);
}
```

```xml
<!-- ✅ 正确示例：使用#{} 参数占位符 -->
<select id="selectByCode" resultType="User">
    SELECT * FROM USER_INFO
    WHERE USER_CODE = #{userCode}
</select>

<select id="queryUsers" resultType="User">
    SELECT * FROM USER_INFO
    <where>
        <if test="dto.userName != null and dto.userName != ''">
            AND USER_NAME LIKE CONCAT('%', #{dto.userName}, '%')
        </if>
        <if test="dto.orgCode != null">
            AND ORG_CODE = #{dto.orgCode}
        </if>
    </where>
</select>

<!-- ❌ 错误示例：使用${} 字符串拼接（SQL注入风险） -->
<select id="queryUsers" resultType="User">
    SELECT * FROM USER_INFO
    WHERE USER_NAME = '${userName}'  <!-- ❌ SQL注入风险 -->
</select>

<!-- ❌ 错误示例：动态表名/列名（必须使用时需白名单校验） -->
<select id="queryData" resultType="Map">
    SELECT * FROM ${tableName}  <!-- ❌ 如果必须使用，需要白名单校验 -->
    WHERE ${columnName} = #{value}
</select>
```

```java
// ✅ 正确示例：动态表名使用白名单校验
private static final Set<String> ALLOWED_TABLES = new HashSet<>(Arrays.asList(
    "USER_INFO", "ORDER_HEAD", "PRODUCT_INFO"
));

public List<Map<String, Object>> queryData(String tableName, String columnName, Object value) {
    // 白名单校验
    if (!ALLOWED_TABLES.contains(tableName)) {
        throw new BizException("非法的表名");
    }

    if (!ALLOWED_COLUMNS.contains(columnName)) {
        throw new BizException("非法的列名");
    }

    // 使用白名单验证后的参数
    return dataDao.queryData(tableName, columnName, value);
}
```

---

### ✅ 空指针防护

**指令**：对可能为null的对象进行判空，避免空指针异常。

```java
// ✅ 正确示例：判空处理
@Service
public class UserServiceImpl implements UserService {

    public UserVO getUser(String userId) {
        User user = userDao.selectById(userId);
        if (user == null) {
            throw new BizException("用户不存在");
        }

        // 安全访问
        String orgName = user.getOrg() != null ? user.getOrg().getOrgName() : "";
        return buildUserVO(user, orgName);
    }

    public void updateUser(UserUpdateDTO dto) {
        // Optional处理
        Optional.ofNullable(dto.getPhone())
            .filter(StringUtils::isNotBlank)
            .ifPresent(phone -> user.setPhone(phone));
    }
}

// ✅ 正确示例：使用Objects工具类
import java.util.Objects;

public void processUser(User user) {
    Objects.requireNonNull(user, "用户对象不能为空");
    Objects.requireNonNull(user.getUserCode(), "用户编号不能为空");

    // 安全处理
    String userName = Objects.toString(user.getUserName(), "");
}

// ❌ 错误示例：未判空
public UserVO getUser(String userId) {
    User user = userDao.selectById(userId);
    return new UserVO(user.getUserCode(), user.getUserName());  // ❌ user可能为null
}
```

---

### ✅ 字符串比对规范

**指令**：字符串比对时，常量或确定有值的字符串放在equals前面。

```java
// ✅ 正确示例：常量在前
if ("ACTIVE".equals(user.getStatus())) {
    // ...
}

if (UserStatus.ACTIVE.equals(user.getStatus())) {
    // ...
}

// ❌ 错误示例：变量在前（可能空指针）
if (user.getStatus().equals("ACTIVE")) {  // ❌ user.getStatus()可能为null
    // ...
}
```

---

### ✅ 使用SecureRandom

**指令**：需要随机数时，使用SecureRandom而非Random。

```java
// ✅ 正确示例：使用SecureRandom
import java.security.SecureRandom;

public class TokenGenerator {
    private static final SecureRandom RANDOM = new SecureRandom();

    public String generateToken() {
        byte[] bytes = new byte[32];
        RANDOM.nextBytes(bytes);
        return Base64.getEncoder().encodeToString(bytes);
    }

    public String generateVerifyCode() {
        return String.format("%06d", RANDOM.nextInt(1000000));
    }
}

// ❌ 错误示例：使用Random
import java.util.Random;

public class TokenGenerator {
    private static final Random RANDOM = new Random();  // ❌ 不安全

    public String generateToken() {
        return String.valueOf(RANDOM.nextLong());
    }
}
```

**原因**：Random使用可预测的种子，SecureRandom使用密码学强随机数生成器。

**使用场景**：
- Token生成
- 验证码生成
- 密钥生成
- 会话ID生成

---

### ✅ 敏感信息脱敏

**指令**：敏感信息存储加密，日志和显示时脱敏。

```java
// ✅ 正确示例：密码加密存储
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

@Service
public class UserService {
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public void createUser(UserCreateDTO dto) {
        User user = new User();
        user.setUserCode(dto.getUserCode());
        // 密码加密存储
        user.setPassword(passwordEncoder.encode(dto.getPassword()));
        userDao.insert(user);
    }

    public boolean login(String userCode, String password) {
        User user = userDao.selectByCode(userCode);
        if (user == null) {
            return false;
        }
        // 密码比对
        return passwordEncoder.matches(password, user.getPassword());
    }
}

// ✅ 正确示例：敏感信息脱敏显示
public class SensitiveDataUtil {

    /**
     * 手机号脱敏：保留前3位和后4位
     */
    public static String maskPhone(String phone) {
        if (StringUtils.isBlank(phone) || phone.length() < 11) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(7);
    }

    /**
     * 身份证号脱敏：保留前4位和后4位
     */
    public static String maskIdCard(String idCard) {
        if (StringUtils.isBlank(idCard) || idCard.length() < 8) {
            return idCard;
        }
        return idCard.substring(0, 4) + "**********" + idCard.substring(idCard.length() - 4);
    }

    /**
     * 银行卡号脱敏：保留前4位和后4位
     */
    public static String maskBankCard(String cardNo) {
        if (StringUtils.isBlank(cardNo) || cardNo.length() < 8) {
            return cardNo;
        }
        return cardNo.substring(0, 4) + " **** **** " + cardNo.substring(cardNo.length() - 4);
    }
}

// 使用示例
@Service
public class UserServiceImpl implements UserService {

    public UserVO getUserDetail(String userId) {
        User user = userDao.selectById(userId);
        UserVO vo = new UserVO();
        vo.setUserId(user.getUserId());
        vo.setUserName(user.getUserName());
        // 脱敏处理
        vo.setPhone(SensitiveDataUtil.maskPhone(user.getPhone()));
        vo.setIdCard(SensitiveDataUtil.maskIdCard(user.getIdCard()));
        return vo;
    }
}
```

**敏感信息类型**：
- 密码（加密存储，不可逆）
- 手机号（显示脱敏：138****5678）
- 身份证号（显示脱敏：3201**********1234）
- 银行卡号（显示脱敏：6225 **** **** 1234）
- 邮箱（显示脱敏：abc***@example.com）

---

### ✅ Redis缓存安全

**指令**：Redis缓存必须设置有效期，禁止缓存大数据，key命名规范。

```java
// ✅ 正确示例：设置缓存有效期
@Service
public class CacheService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    // 缓存用户信息，30分钟过期
    public void cacheUser(User user) {
        String key = buildUserCacheKey(user.getUserId());
        redisTemplate.opsForValue().set(key, user, 30, TimeUnit.MINUTES);
    }

    // 缓存验证码，5分钟过期
    public void cacheVerifyCode(String phone, String code) {
        String key = "verify:code:" + phone;
        redisTemplate.opsForValue().set(key, code, 5, TimeUnit.MINUTES);
    }

    private String buildUserCacheKey(String userId) {
        return "user:info:" + userId;  // 规范的key命名
    }
}

// ❌ 错误示例：未设置有效期
redisTemplate.opsForValue().set("user:123", user);  // ❌ 未设置过期时间，永久存在

// ❌ 错误示例：缓存大数据
List<Order> allOrders = orderDao.selectAll();  // 100万条数据
redisTemplate.opsForValue().set("all:orders", allOrders);  // ❌ 数据量过大

// ✅ 正确做法：分页缓存或缓存ID列表
List<String> orderIds = orderDao.selectAllIds();
redisTemplate.opsForValue().set("order:ids", orderIds, 1, TimeUnit.HOURS);
```

**Redis缓存规范**：
- ✅ 所有缓存必须设置有效期
- ✅ key命名规范：`业务模块:功能:唯一标识`（如 `user:info:123`）
- ✅ 避免缓存大对象（单个value ≤ 10MB）
- ❌ 禁止缓存敏感信息原文（密码、银行卡号）
- ❌ 禁止使用简单key名（如 `user`、`data`）

**缓存有效期建议**：
- 验证码：5分钟
- 用户会话：30分钟
- 用户信息：1小时
- 配置信息：1天
- 字典数据：1天

---

### ✅ 状态值使用字符串

**指令**：数据库状态字段使用字符串类型（如"01"、"02"），不使用数字。

```java
// ✅ 正确示例：状态值使用字符串常量
public class OrderStatus {
    public static final String PENDING = "01";      // 待处理
    public static final String PROCESSING = "02";   // 处理中
    public static final String COMPLETED = "03";    // 已完成
    public static final String CANCELLED = "04";    // 已取消
}

@Service
public class OrderService {
    public void processOrder(String orderId) {
        Order order = orderDao.selectById(orderId);
        if (OrderStatus.PENDING.equals(order.getStatus())) {
            // 处理订单
            order.setStatus(OrderStatus.PROCESSING);
            orderDao.updateStatus(order);
        }
    }
}

// ❌ 错误示例：使用数字状态值
if (order.getStatus() == 1) {  // ❌ 数字状态值，难以理解
    // ...
}
```

**原因**：
- 字符串状态值可读性更好
- 便于扩展（如"01A"、"01B"）
- 避免数字类型的隐式转换问题

---

### ✅ 审计日志记录

**指令**：重要操作必须记录审计日志，便于追溯。

```java
// ✅ 正确示例：记录审计日志
@Service
public class DataDeleteService {

    @Autowired
    private AuditLogDao auditLogDao;

    @Transactional(rollbackFor = Exception.class)
    public void deleteData(String dataId) {
        Data data = dataDao.selectById(dataId);
        if (data == null) {
            throw new BizException("数据不存在");
        }

        // 删除数据
        dataDao.deleteById(dataId);

        // 记录审计日志
        AuditLog auditLog = new AuditLog();
        auditLog.setOperation("DELETE_DATA");
        auditLog.setBusinessId(dataId);
        auditLog.setBusinessType("DATA");
        auditLog.setOperatorId(getCurrentUserId());
        auditLog.setOperatorName(getCurrentUserName());
        auditLog.setOperateTime(LocalDateTime.now());
        auditLog.setIpAddress(getClientIp());
        auditLog.setDetail("删除数据: " + data.getDataCode());
        auditLogDao.insert(auditLog);
    }
}
```

**审计日志记录场景**：
- 用户登录/登出
- 数据增删改操作
- 权限变更
- 配置修改
- 文件上传/下载
- 敏感操作（审批、发布）

---

### ✅ Git忽略敏感文件

**指令**：配置.gitignore，避免敏感信息提交到Git。

```gitignore
# ✅ 正确的.gitignore配置

# 配置文件（包含数据库密码、API密钥）
application-dev.properties
application-test.properties
application-prod.properties
*.env

# 密钥文件
*.key
*.pem
*.p12
*.jks

# IDE配置
.idea/
*.iml
.vscode/
.eclipse/

# 构建产物
target/
build/
*.jar
*.war

# 日志文件
*.log
logs/

# 临时文件
*.tmp
*.temp
```

---

## 场景实战

### 场景1：用户密码修改

**用户需求**：实现用户修改密码功能

**AI应生成**：

```java
@Service
public class PasswordService {

    private static final Logger log = LoggerFactory.getLogger(PasswordService.class);

    @Autowired
    private UserDao userDao;
    @Autowired
    private AuditLogService auditLogService;

    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @Transactional(rollbackFor = Exception.class)
    public void changePassword(PasswordChangeDTO dto) {
        String userId = getCurrentUserId();
        log.info("用户修改密码: userId={}", userId);

        // 1. 查询用户
        User user = userDao.selectById(userId);
        if (user == null) {
            throw new BizException("用户不存在");
        }

        // 2. 校验旧密码
        if (!passwordEncoder.matches(dto.getOldPassword(), user.getPassword())) {
            log.warn("旧密码错误: userId={}", userId);
            throw new BizException("旧密码错误");
        }

        // 3. 校验新密码强度
        validatePasswordStrength(dto.getNewPassword());

        // 4. 更新密码（加密存储）
        String encryptedPassword = passwordEncoder.encode(dto.getNewPassword());
        userDao.updatePassword(userId, encryptedPassword);

        // 5. 记录审计日志
        auditLogService.log("CHANGE_PASSWORD", userId, userId,
            user.getUserName(), "修改密码");

        log.info("密码修改成功: userId={}", userId);
    }

    private void validatePasswordStrength(String password) {
        if (password.length() < 8) {
            throw new BizException("密码长度不能少于8位");
        }
        if (!password.matches(".*[A-Z].*")) {
            throw new BizException("密码必须包含大写字母");
        }
        if (!password.matches(".*[a-z].*")) {
            throw new BizException("密码必须包含小写字母");
        }
        if (!password.matches(".*[0-9].*")) {
            throw new BizException("密码必须包含数字");
        }
    }
}
```

---

### 场景2：文件上传安全

**用户需求**：实现安全的文件上传功能

**AI应生成**：

```java
@Service
public class FileUploadService {

    private static final Logger log = LoggerFactory.getLogger(FileUploadService.class);

    private static final Set<String> ALLOWED_EXTENSIONS = new HashSet<>(Arrays.asList(
        "jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "xls", "xlsx"
    ));

    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024;  // 10MB

    @Autowired
    private FileStorageService fileStorageService;
    @Autowired
    private AuditLogService auditLogService;

    public FileUploadResult uploadFile(MultipartFile file) {
        log.info("文件上传: fileName={}, size={}, operator={}",
            file.getOriginalFilename(), file.getSize(), getCurrentUserId());

        // 1. 校验文件不为空
        if (file.isEmpty()) {
            throw new BizException("文件不能为空");
        }

        // 2. 校验文件大小
        if (file.getSize() > MAX_FILE_SIZE) {
            throw new BizException("文件大小不能超过10MB");
        }

        // 3. 校验文件类型（白名单）
        String originalFilename = file.getOriginalFilename();
        String extension = getFileExtension(originalFilename);
        if (!ALLOWED_EXTENSIONS.contains(extension.toLowerCase())) {
            log.warn("不允许的文件类型: fileName={}, extension={}",
                originalFilename, extension);
            throw new BizException("不支持的文件类型: " + extension);
        }

        // 4. 生成安全的文件名（避免路径穿越）
        String safeFileName = generateSafeFileName(originalFilename);

        // 5. 存储文件
        String filePath = fileStorageService.store(file, safeFileName);

        // 6. 记录审计日志
        auditLogService.log("UPLOAD_FILE", safeFileName, getCurrentUserId(),
            getCurrentUserName(), "上传文件: " + originalFilename);

        log.info("文件上传成功: originalName={}, safeName={}, path={}",
            originalFilename, safeFileName, filePath);

        return new FileUploadResult(safeFileName, filePath);
    }

    private String getFileExtension(String filename) {
        if (StringUtils.isBlank(filename)) {
            return "";
        }
        int lastDot = filename.lastIndexOf('.');
        return lastDot > 0 ? filename.substring(lastDot + 1) : "";
    }

    private String generateSafeFileName(String originalFilename) {
        String extension = getFileExtension(originalFilename);
        String timestamp = String.valueOf(System.currentTimeMillis());
        String randomStr = UUID.randomUUID().toString().substring(0, 8);
        return timestamp + "_" + randomStr + "." + extension;
    }
}
```

---

## 严格禁止的做法

### ❌ 禁止明文存储密码

```java
// ❌ 错误示例
user.setPassword(dto.getPassword());  // ❌ 明文存储密码

// ✅ 正确做法
user.setPassword(passwordEncoder.encode(dto.getPassword()));
```

---

### ❌ 禁止在日志中记录敏感信息

```java
// ❌ 错误示例
log.info("用户登录: userCode={}, password={}", userCode, password);  // ❌ 记录密码

// ✅ 正确做法
log.info("用户登录: userCode={}", userCode);
```

---

### ❌ 禁止SQL拼接

```java
// ❌ 错误示例
String sql = "SELECT * FROM USER_INFO WHERE USER_CODE = '" + userCode + "'";

// ✅ 正确做法
使用MyBatis参数化查询
```

---

## 检查清单

安全防护代码完成后，检查以下事项：

- [ ] 用户输入进行XSS过滤
- [ ] 使用参数化查询，无SQL拼接
- [ ] 对可能为null的对象进行判空
- [ ] 字符串比对时常量在前
- [ ] 使用SecureRandom生成随机数
- [ ] 密码加密存储（BCrypt）
- [ ] 敏感信息显示时脱敏
- [ ] Redis缓存设置有效期
- [ ] Redis key命名规范
- [ ] 重要操作记录审计日志
- [ ] .gitignore配置敏感文件

---

## 相关规则

- 参见 [04-database-operations.md](./04-database-operations.md) 了解SQL规范
- 参见 [07-logging.md](./07-logging.md) 了解日志记录规范
- 参见 [06-exception-handling.md](./06-exception-handling.md) 了解异常处理
