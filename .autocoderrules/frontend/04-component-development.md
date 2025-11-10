---
title: "组件开发场景"
description: "组件拆分、命名、注释规范"
keywords:
  - 组件
  - 拆分
  - 命名
tags:
  - 组件开发
globs:
  - "**/components/**/*.vue"
alwaysApply: false
priority: medium
---

# 组件开发场景规范

## 核心规则

### ✅ 组件拆分

**指令**：单个组件代码不超过300行，复杂组件应拆分。

```vue
<!-- ✅ 正确示例：拆分为多个子组件 -->
<template>
  <div class="user-management">
    <UserQueryForm @query="handleQuery" />
    <UserTable :data="tableData" @edit="handleEdit" />
    <UserDialog v-model="dialogVisible" :user="currentUser" />
  </div>
</template>
```

### ✅ 组件命名

**指令**：组件使用PascalCase命名，至少两个单词。

```vue
// ✅ 正确示例
UserList.vue
OrderTable.vue
DataImportDialog.vue

// ❌ 错误示例
user.vue          // ❌ 单个单词
user_list.vue     // ❌ 下划线
userList.vue      // ❌ 驼峰命名
```

### ✅ Props类型定义

**指令**：Props必须定义TypeScript类型。

```vue
<script setup lang="ts">
interface Props {
  userId: string
  userName: string
  status?: '01' | '02'  // 可选属性
}

const props = defineProps<Props>()
</script>
```

### ✅ 组件注释

**指令**：组件顶部添加注释说明功能。

```vue
<!--
/**
 * 用户列表组件
 * 显示用户列表并支持编辑、删除操作
 */
-->
<template>
  <!-- 组件内容 -->
</template>
```

---

## 检查清单

- [ ] 组件代码≤300行
- [ ] 组件名使用PascalCase
- [ ] Props定义TypeScript类型
- [ ] 组件有功能注释

