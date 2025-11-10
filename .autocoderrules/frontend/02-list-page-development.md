---
title: "列表页开发场景"
description: "查询区、按钮区、表格区布局规范"
keywords:
  - 列表页
  - 表格
  - 查询
  - 布局
tags:
  - 列表页
  - 布局
globs:
  - "**/views/**/*.vue"
  - "**/pages/**/*.vue"
alwaysApply: false
priority: high
---

# 列表页开发场景规范

## 核心规则

### ✅ 页面布局结构

**指令**：列表页分为查询区、按钮区、表格区三个区域。

```vue
<template>
  <div class="list-page">
    <!-- 查询区 -->
    <el-form :model="queryForm" class="query-area">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="用户编号">
            <el-input v-model="queryForm.userCode" placeholder="请输入用户编号" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="用户姓名">
            <el-input v-model="queryForm.userName" placeholder="请输入用户姓名" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item>
            <el-button type="primary" @click="handleQuery">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 按钮区 -->
    <div class="button-area">
      <el-button type="primary" @click="handleAdd">新增</el-button>
      <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
      <el-button @click="handleExport">导出</el-button>
    </div>

    <!-- 表格区 -->
    <el-table :data="tableData" class="table-area" stripe border>
      <el-table-column type="selection" width="55" />
      <el-table-column prop="userCode" label="用户编号" width="150" />
      <el-table-column prop="userName" label="用户姓名" width="120" />
      <el-table-column prop="orgName" label="所属机构" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === '01' ? 'success' : 'danger'">
            {{ row.status === '01' ? '正常' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="queryForm.pageNum"
      v-model:page-size="queryForm.pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleQuery"
      @current-change="handleQuery"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { queryUsers, deleteUser } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

// 查询表单
const queryForm = reactive({
  userCode: '',
  userName: '',
  pageNum: 1,
  pageSize: 20
})

// 表格数据
const tableData = ref([])
const total = ref(0)

// 查询
const handleQuery = async () => {
  try {
    const { data } = await queryUsers(queryForm)
    tableData.value = data.records
    total.value = data.total
  } catch (error) {
    ElMessage.error('查询失败')
  }
}

// 重置
const handleReset = () => {
  queryForm.userCode = ''
  queryForm.userName = ''
  queryForm.pageNum = 1
  handleQuery()
}

// 新增
const handleAdd = () => {
  // 跳转到新增页面或打开弹窗
}

// 删除
const handleDelete = async (row: any) => {
  await ElMessageBox.confirm('确认删除该用户吗？', '提示', {
    type: 'warning'
  })

  try {
    await deleteUser({ id: row.userId, recVersion: row.recVersion })
    ElMessage.success('删除成功')
    handleQuery()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  handleQuery()
})
</script>

<style scoped lang="scss">
.list-page {
  padding: 20px;
}

.query-area {
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 3px;
}

.button-area {
  margin-bottom: 20px;

  .el-button {
    margin-right: 10px;
  }
}

.table-area {
  margin-bottom: 20px;
}
</style>
```

### ✅ 外边距规范

**指令**：外边距使用4的倍数（4px、8px、12px、16px、20px、24px）。

```scss
// ✅ 正确示例
.container {
  margin: 20px;           // ✅ 4的倍数
  padding: 20px;
}

.section {
  margin-bottom: 16px;    // ✅ 4的倍数
}

// ❌ 错误示例
.container {
  margin: 15px;           // ❌ 不是4的倍数
}
```

### ✅ 内边距规范

**指令**：内边距使用5的倍数（5px、10px、15px、20px、25px、30px）。

```scss
// ✅ 正确示例
.card {
  padding: 20px;          // ✅ 5的倍数
}

.input-wrapper {
  padding: 15px;          // ✅ 5的倍数
}
```

### ✅ 按钮间距

**指令**：按钮之间间距10px。

```vue
<template>
  <div class="button-group">
    <el-button type="primary">新增</el-button>
    <el-button type="danger">删除</el-button>
    <el-button>导出</el-button>
  </div>
</template>

<style scoped>
.button-group {
  .el-button {
    margin-right: 10px;  /* 按钮间距10px */
  }

  .el-button:last-child {
    margin-right: 0;
  }
}
</style>
```

### ✅ 表格操作列

**指令**：操作列固定在右侧，按钮数量≤6个。

```vue
<el-table-column label="操作" width="200" fixed="right">
  <template #default="{ row }">
    <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
    <el-button link type="primary" @click="handleView(row)">查看</el-button>
    <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
  </template>
</el-table-column>
```

---

## 检查清单

- [ ] 页面分为查询区、按钮区、表格区
- [ ] 外边距使用4的倍数
- [ ] 内边距使用5的倍数
- [ ] 按钮间距10px
- [ ] 操作列固定在右侧
- [ ] 操作列按钮≤6个
- [ ] 表格使用stripe和border属性
- [ ] 分页组件布局完整

---

## 相关规则

- 参见 [05-ui-styling.md](./05-ui-styling.md) 了解UI样式规范
- 参见 [04-component-development.md](./04-component-development.md) 了解组件开发
