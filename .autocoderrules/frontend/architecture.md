---
description: "前端架构和代码结构规范，包括统一入口、技术栈、目录结构、组件设计、异常处理等"
globs:
  - "**/*.vue"
  - "**/*.js"
  - "**/*.ts"
  - "**/*.jsx"
  - "**/*.tsx"
alwaysApply: true
---

# 前端架构和代码结构规范

## 规则条款

### 1. 统一入口集成

- **frontend_001**: 项目必须集成到统一入口（主要采用"大中台+微应用"的技术架构，建设基于岗位的应用协同平台、基于微应用的应用管理平台、基于服务聚合的数据展示平台）
- 来源：frontend_rules修订版.xlsx 第2行
- 说明：确保项目符合平台整体架构规范，实现微应用集成

### 2. 技术栈规范

- **frontend_002**: 项目应使用平台提供的技术栈进行开发（基于NodeJS开发，采用Vue、Vite、TypeScript、ElementPlus、Pinia、Axios、VueRouter、JavaScript作为技术栈）
- 来源：frontend_rules修订版.xlsx 第3行
- 说明：统一技术栈确保团队协作和代码可维护性

### 3. 目录结构规范

- **frontend_003**: 项目包/目录结构符合脚手架生成项目的基本结构（根据业务模块命名与/views/*一一对应）
- 来源：frontend_rules修订版.xlsx 第4行
- 说明：遵循统一的项目结构，便于代码组织和查找

### 4. 项目命名规范

- **frontend_004**: 项目应用按照"应用编码-功能描述-web"规则命名
- 来源：frontend_rules修订版.xlsx 第5行
- 说明：统一的命名规范便于项目识别和管理

### 5. 慎用!important

- **frontend_005**: 慎用css中的!important关键字（禁止需要根据框架切换主题样式地方使用）
- 来源：frontend_rules修订版.xlsx 第6行
- 说明：!important会破坏样式层叠规则，影响主题切换功能

### 6. 禁止三元运算符嵌套

- **frontend_006**: 禁止使用三个及以上三元运算符嵌套使用
- 来源：frontend_rules修订版.xlsx 第7行
- 说明：嵌套的三元运算符难以理解和维护

### 7. 组件拆分

- **frontend_007**: 合理拆分大型组件为可复用的子组件（组件行数超过300行，应进行拆分）
- 来源：frontend_rules修订版.xlsx 第8行
- 说明：小组件更易于理解、测试和复用

### 8. 模板逻辑简化

- **frontend_008**: 避免在模板中编写复杂逻辑，应抽离到计算属性或方法中（方法行数超过50行，应抽离到计算属性或方法中）
- 来源：frontend_rules修订版.xlsx 第9行
- 说明：模板应保持简洁，复杂逻辑应在脚本中处理

### 9. 单一职责原则

- **frontend_009**: 组件遵循单一职责原则，避免功能冗余
- 来源：frontend_rules修订版.xlsx 第10行
- 说明：每个组件应只负责一个功能，提高可维护性

### 10. TypeScript类型定义

- **frontend_010**: 使用TypeScript时，需明确定义组件Props、状态和方法的类型
- 来源：frontend_rules修订版.xlsx 第11行
- 说明：完整的类型定义提供更好的IDE支持和类型安全

### 11. 避免修改Vue原型

- **frontend_011**: 避免在全局作用域中直接修改Vue原型
- 来源：frontend_rules修订版.xlsx 第12行
- 说明：修改Vue原型可能导致不可预期的副作用，应使用插件机制

### 12. 消除魔数

- **frontend_012**: 消除"魔数"，多处相同字符串或数字，应抽取为常量
- 来源：frontend_rules修订版.xlsx 第13行
- 说明：使用常量提高代码可读性和可维护性

### 13. 命名规范

- **frontend_013**: 类名、变量名、方法名等命名要规范（驼峰命名，见名知意）
- 来源：frontend_rules修订版.xlsx 第14行
- 说明：遵循JavaScript/TypeScript命名约定

### 14. 注释规范

- **frontend_014**: 注释，准确编写注释内容，无用代码删除
- 来源：frontend_rules修订版.xlsx 第15行
- 说明：保持代码整洁，删除注释掉的代码，添加必要的注释

### 15. 行长度限制

- **frontend_015**: 一行代码不超过100字符
- 来源：frontend_rules修订版.xlsx 第16行
- 说明：长行代码不便于阅读，应适当换行

### 16. 统一错误处理

- **frontend_016**: API请求需统一错误处理，避免裸抛异常：1. 禁止直接使用原生axios或fetch；2. 避免硬编码错误信息，提示文案应与接口错误码映射表一致
- 来源：frontend_rules修订版.xlsx 第17行
- 说明：统一的错误处理机制提供一致的用户体验

### 17. 异步操作Loading状态

- **frontend_017**: 异步操作需添加Loading状态，防止重复提交
- 来源：frontend_rules修订版.xlsx 第18行
- 说明：提供良好的用户反馈，防止重复操作

### 18. ESLint规则遵守

- **frontend_018**: 遵循ESLint规则，禁止提交存在警告或错误的代码
- 来源：frontend_rules修订版.xlsx 第19行
- 说明：保证代码质量，遵循团队代码规范

### 19. 组件注释规范

- **frontend_019**: 注释需清晰描述组件功能、Props和事件
- 来源：frontend_rules修订版.xlsx 第20行
- 说明：完整的组件文档便于使用和维护

### 20. 变量先定义后使用

- **frontend_087**: 使用之前应定义变量
- 来源：frontend_rules修订版.xlsx 第88行
- 说明：避免使用未定义的变量

### 21. 版权和许可标头

- **frontend_088**: 跟踪版权和许可标头的缺失
- 来源：frontend_rules修订版.xlsx 第89行
- 说明：文件应包含适当的版权和许可信息

### 22. 变量明确声明

- **frontend_089**: 变量应明确声明
- 来源：frontend_rules修订版.xlsx 第90行
- 说明：使用let、const明确声明变量

### 23. Switch case break语句

- **frontend_091**: Switch case 应该以无条件的"break"语句结束
- 来源：frontend_rules修订版.xlsx 第92行
- 说明：避免case穿透导致的bug

### 24. 数组方法回调返回值

- **frontend_092**: 数组方法的回调应该有返回语句
- 来源：frontend_rules修订版.xlsx 第93行
- 说明：map、filter等方法的回调应返回值

### 25. 禁止八进制值

- **frontend_094**: 不应使用八进制值
- 来源：frontend_rules修订版.xlsx 第95行
- 说明：八进制字面量容易引起混淆，应使用十进制或十六进制

### 26. 函数返回一致性

- **frontend_103**: 函数返回不应该是不变的
- 来源：frontend_rules修订版.xlsx 第103行
- 说明：函数应根据输入返回不同的值，否则应改为常量

### 27. 避免无限循环

- **frontend_104**: 循环不应该是无限的
- 来源：frontend_rules修订版.xlsx 第104行
- 说明：while(true)等无限循环应有明确的退出条件

### 28. 依赖安全漏洞扫描

- **frontend_106**: 定期扫描项目依赖的安全漏洞，禁止使用已知存在高危漏洞的第三方库
- 来源：frontend_rules修订版.xlsx 第105行
- 说明：防止供应链攻击，确保依赖安全性

### 29. 敏感信息泄漏防护

- **frontend_107**: 禁止在客户端代码、错误信息、日志中暴露敏感信息（数据库连接、密钥、内部IP等）
- 来源：frontend_rules修订版.xlsx 第106行
- 说明：防止信息泄露导致的安全风险

### 30. CSP内容安全策略

- **frontend_108**: 正确配置Content Security Policy，防止XSS攻击
- 来源：frontend_rules修订版.xlsx 第107行
- 说明：重要的前端安全防护措施

### 31. 内存泄漏防护

- **frontend_109**: 组件销毁时清理定时器、事件监听器、全局状态引用
- 来源：frontend_rules修订版.xlsx 第108行
- 说明：防止单页应用内存泄漏

### 32. XML解析器XXE防护

- **frontend_093**: XML 解析器不应容易受到 XXE 攻击
- 来源：frontend_rules修订版.xlsx 第94行
- 说明：配置XML解析器防止外部实体攻击

### 33. 禁止Web SQL

- **frontend_096**: 不应使用Web SQL数据库
- 来源：frontend_rules修订版.xlsx 第96行
- 说明：Web SQL已被废弃，应使用IndexedDB

### 34. 测试断言

- **frontend_097**: 测试应包括断言
- 来源：frontend_rules修订版.xlsx 第97行
- 说明：测试用例应包含expect等断言语句

### 35. 断言完整性

- **frontend_099**: 断言应完成
- 来源：frontend_rules修订版.xlsx 第99行
- 说明：expect语句应包含匹配器（toBe、toEqual等）

### 36. 禁止硬编码凭据

- **frontend_100**: 硬编码的凭据对安全敏感
- 来源：frontend_rules修订版.xlsx 第100行
- 说明：不要在代码中硬编码密码、API密钥等敏感信息

### 37. Future保留字

- **frontend_101**: "future reserved words"不应用作标识符
- 来源：frontend_rules修订版.xlsx 第101行
- 说明：避免使用JavaScript保留字作为变量名

### 38. Vue内置逃脱

- **frontend_102**: 禁用vue.JavaScript内置逃脱是对安全敏感的
- 来源：frontend_rules修订版.xlsx 第102行
- 说明：保持Vue的XSS防护机制启用

## 适用场景

本规则适用于所有Vue前端项目开发，是代码质量和安全的基础规范。
