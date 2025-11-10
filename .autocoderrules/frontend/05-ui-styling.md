---
title: "UI样式规范场景"
description: "颜色、字体、圆角、阴影、间距规范"
keywords:
  - UI样式
  - 颜色
  - 字体
  - 主题
tags:
  - UI规范
globs:
  - "**/*.vue"
  - "**/*.scss"
alwaysApply: true
priority: high
---

# UI样式规范场景

## 核心规则

### ✅ 主题色系

**指令**：使用海关蓝或政务红主题色系。

**海关蓝主题色**：
```scss
$primary-color: #0052D9;          // 主色
$primary-hover: #366EF4;          // 悬浮色
$primary-disabled: #8DAAF4;       // 禁用色
$primary-light: #ECF2FE;          // 浅色背景
```

**政务红主题色**：
```scss
$primary-color: #D54941;          // 主色
$primary-hover: #E56A61;          // 悬浮色
$primary-disabled: #F09E99;       // 禁用色
$primary-light: #FEF0EF;          // 浅色背景
```

### ✅ 背景色

```scss
$bg-white: #FFFFFF;               // 白色背景
$bg-gray-1: #F5F5F5;              // 一级灰色背景
$bg-gray-2: #EEEEEE;              // 二级灰色背景
```

### ✅ 文字颜色

```scss
$text-primary: #000000;           // 主要文字（黑色）
$text-secondary: #666666;         // 次要文字（灰色）
$text-disabled: #BBBBBB;          // 禁用文字（浅灰）
$text-link: #0052D9;              // 链接文字（蓝色）
```

### ✅ 边框色

```scss
$border-light: #DCDCDC;           // 浅色边框
$border-medium: #BFBFBF;          // 中色边框
$border-dark: #8C8C8C;            // 深色边框
```

### ✅ 字体大小

**标准版（13-16px）**：
```scss
$font-size-small: 13px;           // 小号字体
$font-size-medium: 14px;          // 中号字体（默认）
$font-size-large: 16px;           // 大号字体
```

**关怀版（15-18px）**：
```scss
$font-size-small: 15px;
$font-size-medium: 16px;
$font-size-large: 18px;
```

### ✅ 圆角

**指令**：统一使用3px圆角。

```scss
.card {
  border-radius: 3px;             // ✅ 统一3px圆角
}
```

### ✅ 阴影

```scss
.card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);  // 卡片阴影
}
```

### ✅ Loading效果

**指令**：使用cacploading组件。

```vue
<template>
  <cacploading v-if="loading" />
  <div v-else>
    <!-- 内容 -->
  </div>
</template>
```

### ✅ 间距规范

**外边距**：4的倍数（4px、8px、12px、16px、20px、24px）
**内边距**：5的倍数（5px、10px、15px、20px、25px、30px）
**按钮间距**：10px
**模块间距**：20px

---

## 检查清单

- [ ] 使用海关蓝或政务红主题色
- [ ] 字体大小符合标准（13-16px或15-18px）
- [ ] 圆角统一使用3px
- [ ] 外边距为4的倍数
- [ ] 内边距为5的倍数
- [ ] 使用cacploading组件

