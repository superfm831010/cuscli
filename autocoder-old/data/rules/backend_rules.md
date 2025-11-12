# 后端代码检查规则

本文档包含 63 条后端代码检查规则，适用于 Python 和 Java 后端开发。

---

## 应用开发架构使用

### 规则ID: backend_001
**标题**: 项目父依赖规范
**严重程度**: error
**描述**: 项目父依赖应为cacp-spring-boot-parent或基于该依赖的自定义项目

**说明**: 确保项目继承正确的父级依赖，以统一技术栈和依赖版本管理。

---

### 规则ID: backend_002
**标题**: 项目核心依赖规范
**严重程度**: error
**描述**: 项目核心依赖为cacp-service-spring-boot-starter或cacp-job-spring-boot-starter两者之一

**说明**: 根据项目类型选择正确的核心依赖，service类项目使用cacp-service-spring-boot-starter，job类项目使用cacp-job-spring-boot-starter。

---

### 规则ID: backend_003
**标题**: 数据源依赖规范
**严重程度**: error
**描述**: 项目如果使用数据源，则必须依赖cacp-datasource-spring-boot-starter

**说明**: 统一使用平台提供的数据源starter，确保数据源配置的一致性和可管理性。

---

### 规则ID: backend_004
**标题**: 项目目录结构规范
**严重程度**: warning
**描述**: 项目包/目录结构符合脚手架生成项目的基本结构，包路径匹配cn.customs.*，对应的功能类应该放在指定目录下：配置（config）、常量（constant）、调用服务（proxy）、接口（controller）、业务逻辑（service）、数据库Mapper接口（dao）、实体（pojo）、工具类（util）

**说明**: 遵循统一的项目结构，便于代码维护和团队协作。

---

### 规则ID: backend_005
**标题**: 项目命名规范
**严重程度**: warning
**描述**: 项目命名应用按照"应用编码-功能描述-service/job"规则，且spring.application.name跟项目名保持一致

**说明**: 统一的命名规范便于项目识别和管理。

---

## 代码结构

### 规则ID: backend_006
**标题**: 避免复杂的嵌套结构
**严重程度**: warning
**描述**: 代码中不应存在复杂的if-else和for循环嵌套（嵌套层数大于3、语句块逻辑除注释外大于20行）

**说明**: 复杂的嵌套结构会降低代码可读性和可维护性，应考虑重构为更清晰的结构。

**错误示例**:
```java
if (condition1) {
    for (int i = 0; i < n; i++) {
        if (condition2) {
            for (int j = 0; j < m; j++) {
                if (condition3) {
                    // 嵌套层数过深
                }
            }
        }
    }
}
```

**正确示例**:
```java
// 抽取内层逻辑为独立方法
if (condition1) {
    processOuterCondition();
}

private void processOuterCondition() {
    for (int i = 0; i < n; i++) {
        processItem(i);
    }
}
```

---

### 规则ID: backend_007
**标题**: 判断逻辑简洁清晰
**严重程度**: warning
**描述**: 判断逻辑应简洁清晰（尽量使用工具类判断，组合判断逻辑运算符不要超过3个）

**说明**: 过于复杂的判断条件难以理解和维护。

**错误示例**:
```java
if (a != null && b != null && (c > 0 || d < 10) && e.equals("test") && f.contains("value")) {
    // 判断条件过于复杂
}
```

**正确示例**:
```java
if (isValid(a, b) && isInRange(c, d) && hasRequiredValues(e, f)) {
    // 使用方法封装复杂判断
}
```

---

### 规则ID: backend_008
**标题**: 单一职责原则
**严重程度**: warning
**描述**: 类和方法功能应单一，多个功能需要拆分（类按面向对象定义设计、方法保证职责单一）

**说明**: 遵循单一职责原则，提高代码的可维护性和可测试性。

---

### 规则ID: backend_009
**标题**: 方法行数限制
**严重程度**: info
**描述**: 代码保持统一格式化，方法行数过多应简化或拆分（行数不应超过30行）

**说明**: 短小的方法更易于理解、测试和维护。

**行数计算方式**:
- 行数计算从方法定义行到方法结束的右大括号行（包含性）
- 计算公式：实际行数 = 结束行号 - 起始行号 + 1
- 包含方法签名、方法体、空行和注释
- 例如：从第10行到第35行的方法，行数为 35 - 10 + 1 = 26 行

**判断标准**:
- ≤ 30 行：**合规**（例如：29行、30行都是合规的）
- > 30 行：**违规**（例如：31行、32行应被标记）

**错误示例**:
```java
// 第10行：方法定义
public void processData(List<Data> dataList) {
    // 方法体（省略）
    // ...
    // 第45行：方法结束
}
// 这个方法从第10行到第45行，共 45 - 10 + 1 = 36 行
// 36 > 30，违规，应被标记
```

**正确示例**:
```java
// 将长方法拆分为多个小方法
public void processData(List<Data> dataList) {
    validateData(dataList);
    transformData(dataList);
    saveData(dataList);
}

private void validateData(List<Data> dataList) {
    // 验证逻辑（不超过30行）
}

private void transformData(List<Data> dataList) {
    // 转换逻辑（不超过30行）
}
```

---

### 规则ID: backend_010
**标题**: 消除重复代码
**严重程度**: warning
**描述**: 重复或类似代码，要抽出独立的方法或类（两处相同即为重复）

**说明**: DRY（Don't Repeat Yourself）原则，避免代码重复。

---

### 规则ID: backend_011
**标题**: 接口逻辑简化
**严重程度**: warning
**描述**: 同一个接口功能不应太多，具体逻辑应该由具体类的具体方法实现（接口指对外提供的api接口，逻辑应尽量简单，业务逻辑下放到具体类的具体方法）

**说明**: 控制器应该保持轻量，业务逻辑应在服务层实现。

---

### 规则ID: backend_012
**标题**: 避免使用switch或必须包含default
**严重程度**: warning
**描述**: 尽量避免switch使用，可使用多态代替switch，如使用switch则必须包含default

**说明**: 多态可以提供更好的扩展性，使用switch时必须处理默认情况。

**正确示例**:
```java
switch (type) {
    case TYPE_A:
        handleA();
        break;
    case TYPE_B:
        handleB();
        break;
    default:
        handleDefault();
        break;
}
```

---

### 规则ID: backend_013
**标题**: 消除魔数
**严重程度**: info
**描述**: 消除"魔数"，多处相同字符串或数字，应抽取为常量

**说明**: 使用有意义的常量名替代魔数，提高代码可读性。

**错误示例**:
```java
if (status == 1) { // 魔数
    // ...
}
```

**正确示例**:
```java
private static final int STATUS_ACTIVE = 1;

if (status == STATUS_ACTIVE) {
    // ...
}
```

---

### 规则ID: backend_014
**标题**: 禁止使用Date类
**严重程度**: warning
**描述**: 代码中禁止使用Date类，应使用LocalDateTime替换

**说明**: java.util.Date是线程不安全的，且API设计不佳，应使用Java 8的时间API。

**错误示例**:
```java
Date now = new Date();
```

**正确示例**:
```java
LocalDateTime now = LocalDateTime.now();
```

---

### 规则ID: backend_015
**标题**: 禁止循环操作数据库
**严重程度**: error
**描述**: 严禁使用循环方式操作数据库，必要时使用批量操作

**说明**: 循环操作数据库会严重影响性能，应使用批量操作。

**错误示例**:
```java
for (User user : users) {
    userDao.insert(user); // 性能问题
}
```

**正确示例**:
```java
userDao.batchInsert(users);
```

---

### 规则ID: backend_016
**标题**: 避免事务失效
**严重程度**: error
**描述**: 避免在同一个service中，一个方法内部调用另一个带事务的方法（事务不生效）

**说明**: Spring事务基于AOP代理，同一类内部调用不会触发事务。

**错误示例**:
```java
@Service
public class UserService {
    public void saveUser(User user) {
        this.doSave(user); // 事务不生效
    }

    @Transactional
    public void doSave(User user) {
        userDao.insert(user);
    }
}
```

---

### 规则ID: backend_017
**标题**: 命名规范
**严重程度**: info
**描述**: 类名、变量名、方法名等命名要规范（驼峰命名，见名知意）

**说明**: 遵循Java命名约定，使用有意义的名称。

---

### 规则ID: backend_018
**标题**: 注释规范
**严重程度**: info
**描述**: 应准确编写注释内容，删除无用代码

**说明**: 保持代码整洁，删除注释掉的代码，添加必要的注释。

---

### 规则ID: backend_019
**标题**: 行长度限制
**严重程度**: info
**描述**: 避免一行代码过长（不要超过120）

**说明**: 长行代码不便于阅读，应适当换行。

---

### 规则ID: backend_020
**标题**: 清理无用导入
**严重程度**: info
**描述**: 应去掉多余的import引用

**说明**: 保持代码整洁，删除未使用的导入。

---

### 规则ID: backend_021
**标题**: 工具类选择
**严重程度**: warning
**描述**: 不使用hutool工具类包，建议使用common-lang3、guava工具集

**说明**: 使用官方推荐的工具库。

---

### 规则ID: backend_022
**标题**: 字符串拼接
**严重程度**: warning
**描述**: 字符串拼接，尤其是循环拼接，应使用StringBuilder

**说明**: String拼接会创建大量临时对象，影响性能。

**错误示例**:
```java
String result = "";
for (String s : list) {
    result += s; // 性能问题
}
```

**正确示例**:
```java
StringBuilder result = new StringBuilder();
for (String s : list) {
    result.append(s);
}
```

---

### 规则ID: backend_023
**标题**: 防止XSS攻击
**严重程度**: error
**描述**: 响应信息尽量避免包含前端代码，或使用ESAPI库进行输出编码以防止XSS攻击

**说明**: 防止跨站脚本攻击，保护用户安全。

---

## 异常处理

### 规则ID: backend_024
**标题**: 统一异常封装
**严重程度**: warning
**描述**: 异常捕获后需处理为自定义封装（BizException），使用统一错误标识（实现ExceptionCodeMessage的异常编码枚举类）

**说明**: 统一异常处理机制，便于问题排查和用户提示。

---

### 规则ID: backend_025
**标题**: 禁止printStackTrace
**严重程度**: error
**描述**: try-catch异常后禁止使用e.printStackTrace();方式输出且没有其他处理（防止异常日志丢失）

**说明**: printStackTrace输出到标准错误流，无法被日志系统捕获。

**错误示例**:
```java
try {
    // ...
} catch (Exception e) {
    e.printStackTrace(); // 错误
}
```

**正确示例**:
```java
try {
    // ...
} catch (Exception e) {
    log.error("操作失败", e);
    throw new BizException(ErrorCode.OPERATION_FAILED, e);
}
```

---

### 规则ID: backend_026
**标题**: 异常日志记录规范
**严重程度**: warning
**描述**: 异常捕获后如需重新抛出自定义业务异常，则不必额外使用log.error记录，直接throw new BizException(...)即可；如不再抛出则应使用log.error记录

**说明**: 避免重复记录日志，统一异常处理机制会记录最终的异常。

---

## 安全性

### 规则ID: backend_027
**标题**: 避免空指针风险
**严重程度**: error
**描述**: 避免空指针风险，方法尽量不返回null

**说明**: 返回空集合或Optional，避免调用方的空指针异常。

**错误示例**:
```java
public List<User> getUsers() {
    return null; // 可能导致NPE
}
```

**正确示例**:
```java
public List<User> getUsers() {
    return Collections.emptyList(); // 安全
}
```

---

### 规则ID: backend_028
**标题**: 字符串比对NPE防护
**严重程度**: error
**描述**: 字符串比对应注意NPE问题，可使用ObjectUtils提供的比对方法如：ObjectUtils.equals(str1, str2)

**说明**: 使用工具类方法避免空指针异常。

---

### 规则ID: backend_029
**标题**: 使用SecureRandom
**严重程度**: error
**描述**: 应使用SecureRandom替代Random生成安全敏感的随机数，Random仅可用于非安全场景如内部分组

**说明**: Random是伪随机数生成器，不适合安全场景。

**错误示例**:
```java
Random random = new Random();
String token = String.valueOf(random.nextLong()); // 不安全
```

**正确示例**:
```java
SecureRandom secureRandom = new SecureRandom();
String token = String.valueOf(secureRandom.nextLong()); // 安全
```

---

### 规则ID: backend_030
**标题**: 敏感信息脱敏
**严重程度**: error
**描述**: 对用户提供数据，敏感信息需加密或脱敏展示（如：手机号、身份证、银行卡号等）

**说明**: 保护用户隐私，防止敏感信息泄露。

---

### 规则ID: backend_031
**标题**: Redis缓存有效期
**严重程度**: warning
**描述**: Redis缓存数据需配置有效期

**说明**: 避免缓存数据无限期存储，防止内存泄漏。

---

### 规则ID: backend_032
**标题**: 禁止缓存大数据
**严重程度**: error
**描述**: 禁止缓存MB级以上数据

**说明**: 大数据缓存会影响Redis性能和内存使用。

---

### 规则ID: backend_033
**标题**: 缓存key命名规范
**严重程度**: warning
**描述**: 避免缓存key重复，应带有独有的命名标识，如"业务模块:对象类型:ID"

**说明**: 统一的key命名规范，避免key冲突。

**正确示例**:
```java
String cacheKey = "user:profile:" + userId;
```

---

## 其他

### 规则ID: backend_034
**标题**: 状态值使用字符串
**严重程度**: info
**描述**: 状态（如：未审批，已审批）不建议使用数字，建议使用有意义的字符串

**说明**: 使用字符串状态值更易理解和维护。

**错误示例**:
```java
int status = 1; // 1代表什么？
```

**正确示例**:
```java
String status = "APPROVED"; // 清晰明了
```

---

### 规则ID: backend_035
**标题**: 审计日志规范
**严重程度**: warning
**描述**: 审计日志记录和调用时机要合理，如用户登录、敏感操作、数据修改等关键节点

**说明**: 完整的审计日志便于问题追溯和安全审计。

---

### 规则ID: backend_036
**标题**: Git忽略文件
**严重程度**: info
**描述**: git上传避免非代码相关内容，使用.gitignore

**说明**: 避免提交编译产物、IDE配置等非代码文件。

---

## 日志输出

### 规则ID: backend_037
**标题**: 日志级别规范
**严重程度**: warning
**描述**: 注意日志输出级别，区分INFO\WARN\DEBUG\ERROR

**说明**: 正确使用日志级别，便于问题定位和日志过滤。

---

### 规则ID: backend_038
**标题**: 日志内容准确精简
**严重程度**: info
**描述**: 日志输出信息要准确、精简，方便定位，避免输出过多无用内容

**说明**: 有效的日志应包含关键信息，避免冗余。

---

### 规则ID: backend_039
**标题**: DEBUG日志补充
**严重程度**: info
**描述**: 复杂业务逻辑处理要为排查问题补充debug级别日志

**说明**: 调试日志有助于开发和测试阶段的问题排查。

---

## 接口定义

### 规则ID: backend_040
**标题**: URL命名规范
**严重程度**: warning
**描述**: url路径名称要求：全小写、不使用驼峰、使用"-"连接（/get-user）

**说明**: 统一的URL命名风格，符合RESTful规范。

**错误示例**:
```java
@GetMapping("/getUser") // 错误
@GetMapping("/get_user") // 不推荐
```

**正确示例**:
```java
@GetMapping("/get-user") // 正确
```

---

### 规则ID: backend_041
**标题**: HTTP方法规范
**严重程度**: info
**描述**: Controller接口中推荐使用GET和POST请求方式，尽量不用PUT和DELETE

**说明**: 简化接口设计，提高兼容性。

---

### 规则ID: backend_042
**标题**: 接口参数简洁
**严重程度**: info
**描述**: 接口请求参数只定义业务所需的字段，避免冗余参数

**说明**: 精简的接口参数便于理解和使用。

---

### 规则ID: backend_043
**标题**: 数据操作接口规范
**严重程度**: warning
**描述**: 删除或其它对数据库数据有操作的接口，应使用Post请求，执行语句带rec_version（版本号）条件

**说明**: 使用版本号实现乐观锁，防止并发更新冲突。

---

## 数据库

### 规则ID: backend_044
**标题**: 数据库表标准字段
**严重程度**: error
**描述**: 数据库表要包含以下三个字段：REC_VERSION（版本号）、REC_CREATE_TIME（创建时间）、REC_LAST_UPDATE_TIME（最后更新时间）

**说明**: 统一的标准字段用于乐观锁和审计。

---

### 规则ID: backend_045
**标题**: 事务管理
**严重程度**: error
**描述**: service中多次操作数据库要开启事务，且考虑抛出异常时数据库回滚问题

**说明**: 保证数据一致性，使用@Transactional注解。

---

### 规则ID: backend_046
**标题**: 主键命名规范
**严重程度**: info
**描述**: 数据库表设计时主键列名要有业务含义（如"USER_ID"）

**说明**: 有意义的列名提高可读性。

---

### 规则ID: backend_047
**标题**: SQL语句规范
**严重程度**: warning
**描述**: mybatis的mapper.xml中编写sql注意，没有条件时不要留下where关键字

**说明**: 避免SQL语法错误。

**错误示例**:
```xml
<select id="getUsers">
    SELECT * FROM users
    WHERE
    <if test="name != null">
        name = #{name}
    </if>
</select>
```

**正确示例**:
```xml
<select id="getUsers">
    SELECT * FROM users
    <where>
        <if test="name != null">
            AND name = #{name}
        </if>
    </where>
</select>
```

---

## 配置_工具

### 规则ID: backend_048
**标题**: 配置注入方式
**严重程度**: info
**描述**: 读取配置文件中的配置，尽量使用@ConfigurationProperties注解类接收，减少@Value注解的使用

**说明**: ConfigurationProperties提供更好的类型安全和IDE支持。

---

### 规则ID: backend_049
**标题**: 资源关闭
**严重程度**: error
**描述**: 在处理stream流时要有流关闭逻辑，推荐使用try-with-resources方式，或添加@Cleanup注解

**说明**: 确保资源被正确释放，避免资源泄漏。

**正确示例**:
```java
try (InputStream is = new FileInputStream(file)) {
    // 使用流
} // 自动关闭
```

---

### 规则ID: backend_050
**标题**: 依赖注入方式
**严重程度**: info
**描述**: 推荐使用构造器注入替换@Resource、@Autowired注入，可以使用@RequiredArgsConstructor注解简化（构造器注入指定bean时，需要手动添加构造方式并使用@Qualifier注解指定Bean）

**说明**: 构造器注入支持final字段，便于测试。

---

## 海关定制

### 规则ID: backend_051
**标题**: 项目父依赖规范（海关定制）
**严重程度**: error
**描述**: 项目父依赖应为cacp-spring-boot-parent或基于该依赖的自定义项目

**说明**: 与backend_001相同，海关特别强调的规则。

---

### 规则ID: backend_052
**标题**: 项目命名规范（海关定制）
**严重程度**: warning
**描述**: 项目目录命名应用按照"{string}-{string}-service/job"规则，且spring.application.name跟项目名保持一致

**说明**: 海关特定的项目命名规范。

---

### 规则ID: backend_053
**标题**: 避免复杂嵌套（海关定制）
**严重程度**: warning
**描述**: 代码中不应存在复杂的if-else和for循环嵌套（嵌套层数大于3）

**说明**: 与backend_006相同，海关特别强调的规则。

---

### 规则ID: backend_054
**标题**: 禁止使用Date类（海关定制）
**严重程度**: warning
**描述**: 代码中禁止使用Date类，应使用LocalDateTime替换

**说明**: 与backend_014相同，海关特别强调的规则。

---

### 规则ID: backend_055
**标题**: 字符串拼接（海关定制）
**严重程度**: warning
**描述**: 字符串拼接，尤其是循环拼接，应使用StringBuilder或StringBuffer

**说明**: 与backend_022相同，海关特别强调的规则。

---

### 规则ID: backend_056
**标题**: 异常日志记录（海关定制）
**严重程度**: warning
**描述**: 异常捕获后如需重新抛出自定义业务异常，则不必额外使用log.error记录，直接throw new BizException(...)即可；如不再抛出则应使用log.error记录

**说明**: 与backend_026相同，海关特别强调的规则。

---

### 规则ID: backend_057
**标题**: URL命名规范（海关定制）
**严重程度**: warning
**描述**: url路径名称要求：全小写、不使用驼峰、使用"-"连接（/get-user）

**说明**: 与backend_040相同，海关特别强调的规则。

---

### 规则ID: backend_058
**标题**: 数据库标准字段（海关定制）
**严重程度**: error
**描述**: 数据库表要包含以下三个字段：REC_VERSION（版本号）、REC_CREATE_TIME（创建时间）、REC_LAST_UPDATE_TIME（最后更新时间）

**说明**: 与backend_044相同，海关特别强调的规则。

---

### 规则ID: backend_059
**标题**: 空指针调用防护
**严重程度**: error
**描述**: 空指针调用。调用对象如果可能为空时，应在使用前进行判断。

**说明**: 使用前检查对象是否为null，避免NPE。

**错误示例**:
```java
String result = user.getName(); // user可能为null
```

**正确示例**:
```java
String result = user != null ? user.getName() : null;
// 或
String result = Optional.ofNullable(user)
    .map(User::getName)
    .orElse(null);
```

---

### 规则ID: backend_060
**标题**: 空变量判断
**严重程度**: error
**描述**: 空异常。变量初始值为空或曾判空，在其他逻辑分支使用变量时均应进行判空。

**说明**: 保持空值检查的一致性，避免在不同分支中遗漏检查。

---

### 规则ID: backend_061
**标题**: Closeable资源关闭
**严重程度**: error
**描述**: 继承了Closeable接口的对象，在使用后必须调用close()方法关闭对象。

**说明**: 确保资源被正确释放，推荐使用try-with-resources。

**正确示例**:
```java
try (Connection conn = dataSource.getConnection()) {
    // 使用连接
} // 自动关闭
```

---

### 规则ID: backend_062
**标题**: String.split结果长度检查
**严重程度**: error
**描述**: 使用String.split方法返回的结果必须进行长度判断。

**说明**: split结果可能不包含预期数量的元素，使用前应检查。

**错误示例**:
```java
String[] parts = str.split(",");
String first = parts[0]; // 可能抛出ArrayIndexOutOfBoundsException
```

**正确示例**:
```java
String[] parts = str.split(",");
if (parts.length > 0) {
    String first = parts[0];
}
```

---

### 规则ID: backend_063
**标题**: 单例类私有变量禁止
**严重程度**: error
**描述**: 在单实例类中禁止使用私有变量。

**说明**: 单例类的私有变量可能导致并发问题，应避免使用。

---

**文档版本**: 1.0
**最后更新**: 2025-10-10
**规则总数**: 63条
