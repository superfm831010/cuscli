---
title: "表单页开发场景"
description: "表单布局、验证、提交规范"
keywords:
  - 表单
  - 验证
  - 提交
tags:
  - 表单页
globs:
  - "**/views/**/*.vue"
alwaysApply: false
priority: medium
---

# 表单页开发场景规范

## 核心规则

### ✅ 表单布局

**指令**：表单使用el-form，label宽度120px。

```vue
<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
    <el-form-item label="用户编号" prop="userCode">
      <el-input v-model="form.userCode" placeholder="请输入用户编号" />
    </el-form-item>
    <el-form-item label="用户姓名" prop="userName">
      <el-input v-model="form.userName" placeholder="请输入用户姓名" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSubmit">提交</el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

const formRef = ref<FormInstance>()
const form = reactive({
  userCode: '',
  userName: ''
})

const rules: FormRules = {
  userCode: [
    { required: true, message: '请输入用户编号', trigger: 'blur' }
  ],
  userName: [
    { required: true, message: '请输入用户姓名', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  // 提交逻辑
}
</script>
```

### ✅ 必填项标识

**指令**：必填项自动显示红色*号。

```vue
<el-form-item label="用户编号" prop="userCode">  <!-- 自动显示*号 -->
  <el-input v-model="form.userCode" />
</el-form-item>
```

---

## 检查清单

- [ ] 表单label宽度120px
- [ ] 必填项配置rules
- [ ] 提交前进行表单验证
- [ ] 按钮使用primary和default类型

