---
description: "后端安全规范，包括XSS防护、空指针防护、敏感信息保护、缓存安全等"
globs:
  - "**/*.java"
  - "**/*.py"
alwaysApply: true
---

# 后端安全规范

## 规则条款

### 1. 防止XSS攻击

- **backend_023**: 响应信息尽量避免包含前端代码，或使用ESAPI库进行输出编码以防止XSS攻击
- 来源：backend_rules修订版.xlsx 第22行
- 说明：防止跨站脚本攻击，保护用户安全

### 2. 避免空指针风险

- **backend_027**: 避免空指针风险，集合对象不返回null
- 来源：backend_rules修订版.xlsx 第26行
- 说明：返回空集合或Optional，避免调用方的空指针异常

### 3. 字符串比对NPE防护

- **backend_028**: 字符串比对应注意NPE问题，可使用ObjectUtils提供的比对方法如：ObjectUtils.equals(str1, str2)
- 来源：backend_rules修订版.xlsx 第27行
- 说明：使用工具类方法避免空指针异常

### 4. 使用SecureRandom

- **backend_029**: 应使用SecureRandom替代Random生成安全敏感的随机数，Random仅可用于非安全场景如内部分组
- 来源：backend_rules修订版.xlsx 第28行
- 说明：Random是伪随机数生成器，不适合安全场景

### 5. 敏感信息脱敏

- **backend_030**: 对用户提供数据，敏感信息需加密或脱敏展示（如：手机号、身份证、银行卡号等）
- 来源：backend_rules修订版.xlsx 第29行
- 说明：保护用户隐私，防止敏感信息泄露

### 6. Redis缓存有效期

- **backend_031**: Redis缓存数据需配置有效期
- 来源：backend_rules修订版.xlsx 第30行
- 说明：避免缓存数据无限期存储，防止内存泄漏

### 7. 禁止缓存大数据

- **backend_032**: 禁止缓存MB级以上数据
- 来源：backend_rules修订版.xlsx 第31行
- 说明：大数据缓存会影响Redis性能和内存使用

### 8. 缓存key命名规范

- **backend_033**: 避免缓存key重复，应带有独有的命名标识，如"业务模块:对象类型:ID"
- 来源：backend_rules修订版.xlsx 第32行
- 说明：统一的key命名规范，避免key冲突

### 9. 状态值使用字符串

- **backend_034**: 状态（如：未审批，已审批）不建议使用数字，建议使用有意义的字符串
- 来源：backend_rules修订版.xlsx 第33行
- 说明：使用字符串状态值更易理解和维护

### 10. 审计日志规范

- **backend_035**: 审计日志记录和调用时机要合理，如用户登录、敏感操作、数据修改等关键节点
- 来源：backend_rules修订版.xlsx 第34行
- 说明：完整的审计日志便于问题追溯和安全审计

### 11. Git忽略文件

- **backend_036**: git上传避免非代码相关内容，使用.gitignore
- 来源：backend_rules修订版.xlsx 第35行
- 说明：避免提交编译产物、IDE配置等非代码文件

### 12. 空变量判断

- **backend_060**: 空异常。变量初始值为空或曾判空，在其他逻辑分支使用变量时均应进行判空
- 来源：backend_rules修订版.xlsx 第50行
- 说明：保持空值检查的一致性，避免在不同分支中遗漏检查

### 13. Closeable资源关闭

- **backend_061**: 继承了Closeable接口的对象，在使用后必须调用close()方法关闭对象
- 来源：backend_rules修订版.xlsx 第51行
- 说明：确保资源被正确释放，推荐使用try-with-resources

### 14. String.split结果长度检查

- **backend_062**: 使用String.split方法返回的结果必须进行长度判断
- 来源：backend_rules修订版.xlsx 第52行
- 说明：split结果可能不包含预期数量的元素，使用前应检查

### 15. 单例类私有变量禁止

- **backend_063**: 在单实例类中禁止使用私有变量
- 来源：backend_rules修订版.xlsx 第53行
- 说明：单例类的私有变量可能导致并发问题，应避免使用

## 适用场景

本规则适用于所有后端代码开发，是安全编码的强制性规范，必须严格遵守。
