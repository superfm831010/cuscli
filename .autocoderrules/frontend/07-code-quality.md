---
title: "前端代码质量场景"
description: "命名规范、TypeScript类型、注释、代码格式"
keywords:
  - 代码质量
  - TypeScript
  - 命名规范
tags:
  - 代码质量
globs:
  - "**/*.vue"
  - "**/*.ts"
alwaysApply: false
priority: medium
---

# 前端代码质量场景规范

## 核心规则

### ✅ 变量命名

**指令**：使用camelCase驼峰命名。

```typescript
// ✅ 正确示例
const userName = 'zhangsan'
const totalCount = 100
const isValid = true

// ❌ 错误示例
const user_name = 'zhangsan'  // ❌ 下划线
const UserName = 'zhangsan'   // ❌ 大驼峰（变量应用小驼峰）
```

### ✅ 常量命名

**指令**：常量使用UPPER_SNAKE_CASE。

```typescript
// ✅ 正确示例
const MAX_COUNT = 100
const API_BASE_URL = '/api'

export enum UserStatus {
  ACTIVE = '01',
  INACTIVE = '02'
}
```

### ✅ TypeScript类型定义

**指令**：必须定义接口类型，避免any。

```typescript
// ✅ 正确示例
interface User {
  userId: string
  userCode: string
  userName: string
  status: '01' | '02'
}

interface QueryForm {
  userCode?: string
  userName?: string
  pageNum: number
  pageSize: number
}

const user: User = {
  userId: '1',
  userCode: 'U001',
  userName: '张三',
  status: '01'
}

// ❌ 错误示例
const user: any = { ... }  // ❌ 避免使用any
```

### ✅ 模板中避免复杂逻辑

**指令**：复杂逻辑提取到computed或方法中。

```vue
<!-- ✅ 正确示例 -->
<template>
  <div>{{ userStatusText }}</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const userStatusText = computed(() => {
  return props.status === '01' ? '正常' : '停用'
})
</script>

<!-- ❌ 错误示例 -->
<template>
  <div>{{ status === '01' ? '正常' : status === '02' ? '停用' : '未知' }}</div>
</template>
```

### ✅ 三元运算符限制

**指令**：三元运算符嵌套不超过2层。

```typescript
// ✅ 正确示例：2层嵌套
const text = status === '01' ? '正常' : status === '02' ? '停用' : '未知'

// ❌ 错误示例：3层嵌套
const text = status === '01' ? '正常' : status === '02' ? '停用' : status === '03' ? '锁定' : '未知'

// ✅ 正确做法：使用对象映射
const STATUS_TEXT_MAP = {
  '01': '正常',
  '02': '停用',
  '03': '锁定'
}
const text = STATUS_TEXT_MAP[status] || '未知'
```

### ✅ 行长度限制

**指令**：每行代码≤120字符。

```typescript
// ✅ 正确示例：换行
const message = `用户创建成功：编号${userCode}，` +
  `姓名${userName}，机构${orgName}`

// ❌ 错误示例：单行过长
const message = `用户创建成功：编号${userCode}，姓名${userName}，机构${orgName}，电话${phone}，邮箱${email}`
```

### ✅ 注释规范

**指令**：复杂函数添加JSDoc注释。

```typescript
/**
 * 查询用户列表
 * @param params 查询参数
 * @returns 用户列表
 */
async function queryUsers(params: QueryForm): Promise<User[]> {
  const { data } = await request.post('/api/users/query', params)
  return data
}
```

### ❌ 禁止使用var

**约束**：使用const和let，不使用var。

```typescript
// ✅ 正确示例
const userName = 'zhangsan'
let count = 0

// ❌ 错误示例
var userName = 'zhangsan'  // ❌ 不使用var
```

### ❌ 禁止省略大括号

**约束**：if/for/while必须使用大括号。

```typescript
// ✅ 正确示例
if (condition) {
  doSomething()
}

// ❌ 错误示例
if (condition) doSomething()  // ❌ 缺少大括号
```

---

## 检查清单

- [ ] 变量使用camelCase命名
- [ ] 常量使用UPPER_SNAKE_CASE
- [ ] 定义TypeScript类型，避免any
- [ ] 模板中无复杂逻辑
- [ ] 三元运算符嵌套≤2层
- [ ] 代码行长度≤120字符
- [ ] 复杂函数有注释
- [ ] 不使用var
- [ ] if/for/while使用大括号

