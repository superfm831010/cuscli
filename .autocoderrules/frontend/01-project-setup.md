---
title: "前端项目搭建场景"
description: "Vue3+Vite+TypeScript+ElementPlus技术栈、项目结构、统一入口"
keywords:
  - Vue3
  - Vite
  - TypeScript
  - ElementPlus
  - 项目初始化
tags:
  - 项目搭建
  - 技术栈
globs:
  - "**/package.json"
  - "**/vite.config.ts"
  - "**/tsconfig.json"
  - "**/*.vue"
alwaysApply: true
priority: high
---

# 前端项目搭建场景规范

## 场景概述

当创建新的前端项目或配置现有项目时，遵循海关统一的技术栈和项目结构规范。

## 核心规则

### ✅ 统一技术栈

**指令**：前端项目必须使用Vue3 + Vite + TypeScript + ElementPlus技术栈。

```json
// package.json
{
  "name": "customs-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.4.0",
    "@element-plus/icons-vue": "^2.1.0",
    "axios": "^1.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.3.0",
    "typescript": "^5.0.0",
    "vue-tsc": "^1.8.0",
    "vite": "^4.4.0"
  }
}
```

**技术栈要求**：
- ✅ **Vue 3** - 使用Composition API
- ✅ **Vite** - 构建工具
- ✅ **TypeScript** - 类型系统
- ✅ **ElementPlus** - UI组件库
- ✅ **Pinia** - 状态管理
- ✅ **Vue Router** - 路由管理
- ❌ 不使用Vue 2、Webpack、JavaScript、其他UI库

---

### ✅ 标准项目目录结构

**指令**：项目目录结构应符合海关规范。

```
customs-app/
├── public/              # 静态资源
├── src/
│   ├── api/            # API接口
│   ├── assets/         # 图片、样式等资源
│   ├── components/     # 公共组件
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia状态管理
│   ├── types/          # TypeScript类型定义
│   ├── utils/          # 工具函数
│   ├── views/          # 页面组件
│   ├── App.vue         # 根组件
│   └── main.ts         # 入口文件
├── .env.development    # 开发环境配置
├── .env.production     # 生产环境配置
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

### ✅ 统一入口集成

**指令**：项目应通过统一入口平台集成，不独立部署。

```typescript
// main.ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,  // 统一使用中文
  size: 'default'
})

app.mount('#app')
```

**集成要求**：
- 使用统一认证登录
- 使用统一菜单导航
- 使用统一主题样式
- 使用统一权限控制

---

### ✅ 项目命名规范

**指令**：项目名称使用小写字母和短横线。

```json
// ✅ 正确示例
{
  "name": "customs-user-management",
  "name": "customs-order-system"
}

// ❌ 错误示例
{
  "name": "CustomsUserManagement",  // ❌ 驼峰命名
  "name": "customs_user_management"  // ❌ 下划线
}
```

---

### ✅ TypeScript配置

**指令**：必须启用TypeScript严格模式。

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,              // ✅ 启用严格模式
    "noUnusedLocals": true,      // ✅ 检查未使用的局部变量
    "noUnusedParameters": true,  // ✅ 检查未使用的参数
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

### ✅ ESLint和代码规范

**指令**：配置ESLint进行代码质量检查。

```json
// package.json
{
  "devDependencies": {
    "eslint": "^8.50.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "eslint-plugin-vue": "^9.17.0"
  },
  "scripts": {
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix"
  }
}
```

---

### ✅ 环境变量配置

**指令**：使用.env文件管理环境配置。

```bash
# .env.development
VITE_APP_BASE_API=/api
VITE_APP_TITLE=海关应用系统
VITE_APP_ENV=development

# .env.production
VITE_APP_BASE_API=/prod-api
VITE_APP_TITLE=海关应用系统
VITE_APP_ENV=production
```

```typescript
// 使用环境变量
const baseURL = import.meta.env.VITE_APP_BASE_API
const appTitle = import.meta.env.VITE_APP_TITLE
```

---

## 检查清单

项目搭建完成后，检查以下事项：

- [ ] 使用Vue3 + Vite + TypeScript + ElementPlus技术栈
- [ ] 目录结构符合标准规范
- [ ] package.json中项目名称使用短横线命名
- [ ] TypeScript strict模式已启用
- [ ] 已配置ESLint
- [ ] 已配置环境变量文件
- [ ] ElementPlus使用中文语言包
- [ ] 已配置路径别名@指向src

---

## 相关规则

- 参见 [05-ui-styling.md](./05-ui-styling.md) 了解UI样式规范
- 参见 [04-component-development.md](./04-component-development.md) 了解组件开发规范
- 参见 [07-code-quality.md](./07-code-quality.md) 了解代码质量要求
