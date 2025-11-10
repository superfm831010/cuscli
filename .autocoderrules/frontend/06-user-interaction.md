---
title: "用户交互场景"
description: "Loading状态、错误处理、消息提示规范"
keywords:
  - Loading
  - 错误处理
  - 消息提示
tags:
  - 用户交互
globs:
  - "**/*.vue"
  - "**/*.ts"
alwaysApply: false
priority: medium
---

# 用户交互场景规范

## 核心规则

### ✅ Loading状态

**指令**：异步操作显示Loading状态。

```vue
<script setup lang="ts">
import { ref } from 'vue'

const loading = ref(false)

const handleQuery = async () => {
  loading.value = true
  try {
    const { data } = await queryUsers()
    tableData.value = data
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <cacploading v-if="loading" />
  <el-table v-else :data="tableData" />
</template>
```

### ✅ 错误处理

**指令**：统一捕获异常并提示用户。

```typescript
import { ElMessage } from 'element-plus'

const handleSubmit = async () => {
  try {
    await saveUser(form)
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败，请重试')
    console.error('保存用户失败:', error)
  }
}
```

### ✅ 确认对话框

**指令**：删除操作需要二次确认。

```typescript
import { ElMessageBox, ElMessage } from 'element-plus'

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认删除该用户吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })

    await deleteUser({ id: row.userId, recVersion: row.recVersion })
    ElMessage.success('删除成功')
    handleQuery()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error('删除失败')
  }
}
```

### ✅ 表单验证提示

**指令**：表单验证失败显示明确提示。

```vue
<el-form :model="form" :rules="rules">
  <el-form-item label="用户编号" prop="userCode">
    <el-input v-model="form.userCode" />
  </el-form-item>
</el-form>

<script setup lang="ts">
const rules = {
  userCode: [
    { required: true, message: '请输入用户编号', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在6到20个字符', trigger: 'blur' }
  ]
}
</script>
```

---

## 检查清单

- [ ] 异步操作显示Loading
- [ ] 异常统一捕获并提示
- [ ] 删除操作二次确认
- [ ] 表单验证提示明确

