---
description: "方法与变量命名规范：Camel命名方式"
globs: ["**/*.java", "**/*.js", "**/*.vue"]
alwaysApply: true
---

# 方法与变量命名规范

## 规范说明

方法和变量的命名采用 **Camel** 命名方式，即首个单词首字母小写，其余单词首字母大写。

## 强制要求 - Java

### 方法命名

1. 【强制】方法名采用 Camel 命名方式
2. 【强制】建议采用动宾结构词组
3. 【强制】方法名应清晰表达其功能
4. 【强制】布尔类型的方法名，应使用 is、has、can、should 等助词开头

### 变量命名

1. 【强制】变量名采用 Camel 命名方式
2. 【强制】变量名应具有描述性，见名知义
3. 【强制】参数的命名与变量的命名规范一致
4. 【强制】避免使用单字符变量名（除循环计数器外）

### 常量命名

1. 【强制】Static Final 常量采用 Upper 命名方式
2. 【强制】全部字母大写，单词间用下划线分隔
3. 【强制】应指出完整含义

### 数组命名

1. 【强制】数组应该用 `type[] arrayName` 方式命名
2. 【强制】不使用 `type arrayName[]` 方式

## 示例 - Java

### 方法命名示例

#### ✅ 正确示例

```java
// 查询操作
public Entry getEntryById(String id) { }
public List<Entry> queryEntryList() { }
public Entry findEntryByCode(String code) { }

// 保存操作
public void saveEntry(Entry entry) { }
public void insertEntry(Entry entry) { }
public void updateEntry(Entry entry) { }
public void deleteEntry(String id) { }

// 检查操作
public boolean checkEntry(Entry entry) { }
public void validateEntry(Entry entry) { }

// 业务操作（动宾结构）
public void rejectEms(String emsNo) { }
public void approveEntry(String entryNo) { }
public void processDeclaration(Declaration decl) { }
public void sendMessage(String messageType, Map data) { }

// 布尔判断方法
public boolean isValid() { }
public boolean hasPermission(String userId) { }
public boolean canApprove(Entry entry) { }
public boolean shouldNotify() { }
```

#### ❌ 错误示例

```java
public void ProcessEntry(Entry entry) { }        // 错误：首字母大写
public void process_entry(Entry entry) { }       // 错误：使用下划线
public void pe(Entry entry) { }                  // 错误：不明确的缩写
public void getEntryAndSave() { }                // 错误：方法做了多件事
```

### 变量命名示例

#### ✅ 正确示例

```java
// 普通变量
String userName;
int fileSize;
boolean isActive;
LocalDateTime createTime;

// 集合类型
List<Entry> entryList;
Map<String, Object> paramMap;
Set<String> uniqueSet;

// 布尔类型
boolean isValid;
boolean hasPermission;
boolean canExecute;

// 对象实例
Entry currentEntry;
UserService userService;
EntryRepository entryRepository;
```

#### ❌ 错误示例

```java
String UserName;                  // 错误：首字母大写
int file_size;                    // 错误：使用下划线
boolean flag;                     // 错误：不明确的变量名
String s;                         // 错误：无意义的单字符（非循环变量）
List<Entry> list;                 // 错误：不明确是什么列表
```

### 常量命名示例

#### ✅ 正确示例

```java
public static final int MAX_UPLOAD_FILE_SIZE = 1024;
public static final String DEFAULT_CHARSET = "UTF-8";
public static final long TIMEOUT_MILLISECONDS = 30000L;
public static final String ENTRY_STATUS_PENDING = "0";
public static final String ENTRY_STATUS_APPROVED = "1";
```

#### ❌ 错误示例

```java
public static final int maxSize = 1024;          // 错误：应全部大写
public static final String DEFAULT-CHARSET = "UTF-8";  // 错误：使用中划线
public static final long TIMEOUT = 30000L;       // 错误：没有指出完整含义（单位）
```

### 数组命名示例

#### ✅ 正确示例

```java
byte[] buffer;
String[] names;
int[] scores;
Entry[] entries;
```

#### ❌ 错误示例

```java
byte buffer[];                    // 错误：不推荐的数组声明方式
String names   [];                // 错误：格式不规范
```

## 命名建议 - Java

### 表示类型的名词放在词尾

【推荐】在常量与变量的命名时，表示类型的名词放在词尾，以提升辨识度。

```java
// ✅ 正例
LocalDateTime startTime;
Queue<Task> workQueue;
List<String> nameList;
int terminatedThreadCount;

// ❌ 反例
LocalDateTime startedAt;
Queue<Task> queueOfWork;
List<String> listName;
int countTerminatedThread;
```

### 常用动词约定

| 动词 | 含义 | 示例 |
|-----|-----|------|
| get | 获取 | getUser |
| set | 设置 | setName |
| query | 查询 | queryEntryList |
| find | 查找 | findByCode |
| search | 搜索 | searchEntries |
| save | 保存 | saveEntry |
| insert | 插入 | insertEntry |
| update | 更新 | updateEntry |
| delete | 删除 | deleteEntry |
| add | 添加 | addItem |
| remove | 移除 | removeItem |
| create | 创建 | createOrder |
| build | 构建 | buildRequest |
| validate | 验证 | validateForm |
| check | 检查 | checkPermission |
| is | 是否 | isValid |
| has | 拥有 | hasPermission |
| can | 能否 | canExecute |
| should | 应该 | shouldRetry |
| process | 处理 | processData |
| handle | 处理 | handleRequest |
| calculate | 计算 | calculateTotal |
| convert | 转换 | convertToDTO |
| parse | 解析 | parseJson |
| format | 格式化 | formatDate |
| send | 发送 | sendMessage |
| receive | 接收 | receiveMessage |

## 前端命名规范

### JavaScript/Vue 变量命名

```javascript
// ✅ 正确示例 - 驼峰命名
let userName = '张三';
let fileSize = 1024;
let isActive = true;
let entryList = [];

// 对象属性也使用驼峰
const userInfo = {
  userId: '001',
  userName: '张三',
  createTime: new Date()
};

// ❌ 错误示例
let UserName = '张三';          // 错误：首字母大写
let user_name = '张三';         // 错误：下划线命名
let un = '张三';                // 错误：不明确的缩写
```

### JavaScript/Vue 方法命名

```javascript
// ✅ 正确示例
methods: {
  // 获取数据
  getEntryList() { },
  fetchUserInfo() { },

  // 保存操作
  saveEntry() { },
  updateEntry() { },
  deleteEntry() { },

  // 事件处理
  handleSubmit() { },
  handleClick() { },

  // 布尔判断
  isValid() { },
  hasPermission() { },
  canSubmit() { }
}

// ❌ 错误示例
methods: {
  GetEntryList() { },          // 错误：首字母大写
  get_entry_list() { },        // 错误：下划线命名
}
```

### Vue 组件命名

```javascript
// ✅ 正确示例 - 大驼峰（PascalCase）
import EntryList from '@/components/EntryList.vue';
import UserDialog from '@/components/UserDialog.vue';

components: {
  EntryList,
  UserDialog
}

// ❌ 错误示例
import entryList from '@/components/entryList.vue';  // 错误：小驼峰
import entry_list from '@/components/entry-list.vue'; // 错误：下划线
```

### CSS 类名

```css
/* ✅ 正确示例 - 中划线连接 */
.entry-list { }
.user-dialog-header { }
.btn-primary { }

/* ❌ 错误示例 */
.entryList { }              /* 错误：驼峰命名 */
.entry_list { }             /* 错误：下划线命名 */
```

## 适用场景

- Java 方法定义
- Java 变量声明
- Java 常量定义
- JavaScript 函数和变量
- Vue 组件方法和数据

## 相关规范

- 参见 [类命名规范](./class-naming.md)
- 参见 [Package命名规范](./package-naming.md)
- 参见 [JavaScript基础规范](../03-frontend/js-basic.md)

## 来源文档

- 《Java开发规范》- 05-java-spec.md 第6节
- 《JavaScript开发规范》- 06-js-spec.md
- 《海关应用云平台开发规范》- 00-cacp-spec.md 第5.2节
