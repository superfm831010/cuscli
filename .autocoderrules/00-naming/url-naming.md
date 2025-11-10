---
description: "URL命名规范：全部小写字母+中划线分隔"
globs: ["**/*.java", "**/*.vue", "**/*.js"]
alwaysApply: true
---

# URL 命名规范

## 规范说明

网页及Controller地址，统一使用小写字母、数字、中划线，不使用大写字母及下划线，多个单词之间采用中划线（-）进行分割。

## 强制要求

1. 【强制】URL 全部采用小写字母
2. 【强制】单词间使用中划线（-）做为分隔符
3. 【强制】不使用大写字母
4. 【强制】不使用下划线（_）
5. 【强制】不使用驼峰命名

## 示例

### ✅ 正确示例

```
http://www.h2018.hg.cn/parameter-service/dict/get-name?key=country&code=502
http://api.customs.gov.cn/hrec-main-service/entry/query-list
http://portal.hg.cn/user-management/get-user-info
http://www.h2018.hg.cn/entry-head/update-status
```

**前端路由示例**：
```javascript
// Vue Router 配置
{
  path: '/entry-management',
  children: [
    { path: 'entry-list', component: EntryList },
    { path: 'entry-detail/:id', component: EntryDetail },
    { path: 'entry-create', component: EntryCreate }
  ]
}
```

**后端Controller示例**：
```java
@RestController
@RequestMapping("/parameter-service/dict")
public class DictController {

    @GetMapping("/get-name")
    public String getDictName(@RequestParam String key, @RequestParam String code) {
        // ...
    }

    @PostMapping("/update-value")
    public void updateDictValue(@RequestBody DictVO dict) {
        // ...
    }
}
```

### ❌ 错误示例

```
http://www.h2018.hg.cn/ParameterService/Dict/GetName         // 错误：使用了大写和驼峰
http://api.customs.gov.cn/hrec_main_service/entry/queryList  // 错误：使用了下划线和驼峰
http://portal.hg.cn/UserManagement/getUserInfo               // 错误：使用了驼峰命名
http://www.h2018.hg.cn/entry_head/UpdateStatus               // 错误：同时使用了下划线和大写
```

## 命名建议

### URL 路径设计原则

1. **资源名词化**：使用名词而非动词
   ```
   ✅ /users/{id}
   ❌ /get-user/{id}
   ```

2. **复数形式**：集合资源使用复数
   ```
   ✅ /entries/list
   ❌ /entry/list
   ```

3. **层级清晰**：反映资源的层级关系
   ```
   ✅ /entries/{id}/lists
   ❌ /entry-lists?entryId={id}
   ```

4. **简洁明了**：避免过长的URL
   ```
   ✅ /dict/get-name
   ❌ /dictionary/get-dictionary-name-by-key
   ```

### RESTful API 规范

```
GET    /entries          # 查询列表
GET    /entries/{id}     # 查询详情
POST   /entries          # 创建
PUT    /entries/{id}     # 更新
DELETE /entries/{id}     # 删除
PATCH  /entries/{id}     # 部分更新
```

## 适用场景

- 所有HTTP接口URL
- 前端路由路径
- RESTful API设计
- 微服务接口路径

## 相关规范

- 参见 [微服务命名规范](./microservice-naming.md)
- 参见 [方法与变量命名规范](./method-variable-naming.md)

## 来源文档

- 《海关应用云平台开发规范》- 00-cacp-spec.md 第2.5节
- 《Java开发规范》- 05-java-spec.md 第6.16节
