---
description: "JavaScript基础规范：ES6+、驼峰命名、禁止node_modules提交"
globs: ["**/*.js", "**/*.vue"]
alwaysApply: false
---

# JavaScript 开发规范

## 基本要求

1. 【强制】JS风格使用 **JavaScript Standard Style**
2. 【强制】前端项目必须采用平台组提供脚手架进行开发
3. 【强制】运用框架：**Vue2 + vue-router + ElementUI + axios**
4. 【推荐】推荐使用 **ES6.0** 定义变量（let, const），尽量少用 var

## 命名规范

### 文件命名

1. 【强制】创建新的文件夹或CSS文件时，遵循**小驼峰**标识，文件名首字母小写
2. 【强制】创建JS或Vue文件时，遵循**大驼峰**标识，文件名首字母大写

```
src/
├── components/
│   ├── EntryList.vue      # 大驼峰
│   └── UserDialog.vue     # 大驼峰
├── views/
│   ├── entry/
│   │   ├── EntryManagement.vue
│   │   └── EntryDetail.vue
│   └── user/
├── assets/
│   └── css/
│       └── commonStyle.css   # 小驼峰
├── api/
│   ├── entryApi.js          # 小驼峰
│   └── userApi.js
```

### 变量命名

【强制】变量命名使用驼峰命名（camelCase）

```javascript
// ✅ 正确
let userName = '张三';
let entryList = [];
const maxCount = 100;

// ❌ 错误
let UserName = '张三';     // 首字母不应大写
let entry_list = [];       // 不应使用下划线
```

### 组件命名

【强制】Vue组件引入时，import定义的组件名及components名需要遵循大驼峰标识

```javascript
// ✅ 正确
import EntryList from '@/components/EntryList.vue';
import UserDialog from '@/components/UserDialog.vue';

export default {
    components: {
        EntryList,
        UserDialog
    }
}

// ❌ 错误
import entryList from '@/components/entryList.vue';  // 小驼峰
```

## 代码规范

### 路径引用

【强制】框架引入@，相对路径(../)使用@代替

```javascript
// ✅ 正确
import EntryApi from '@/api/entry/entryApi';
import CommonUtils from '@/utils/commonUtils';

// ❌ 错误
import EntryApi from '../../api/entry/entryApi';  // 避免使用相对路径
```

### 数据赋值

【强制】在JS中每次给data中定义的值赋值时，首先要将该值清空

```javascript
export default {
    data() {
        return {
            entryList: [],
            userInfo: {}
        }
    },
    methods: {
        loadData() {
            // ✅ 正确：先清空
            this.entryList = [];
            this.entryList = response.data;

            // ❌ 错误：直接赋值可能导致数据累加
            this.entryList = response.data;
        }
    }
}
```

### 条件语句

1. 【强制】如果有if及else if，最后必须要以else为结尾
2. 【强制】禁止使用三个及以上三目运算符嵌套使用

```javascript
// ✅ 正确
if (status === '0') {
    // ...
} else if (status === '1') {
    // ...
} else {
    // ...
}

// ❌ 错误：缺少else
if (status === '0') {
    // ...
} else if (status === '1') {
    // ...
}

// ❌ 错误：三目运算符嵌套过多
let result = a ? (b ? (c ? 'd' : 'e') : 'f') : 'g';  // 不要这样写！
```

## Vue 规范

### Prop 定义

【强制】Prop 定义应该尽量详细，至少需要指定其类型

```javascript
// ✅ 正确
props: {
    status: {
        type: String,
        required: true,
        default: '0'
    },
    entryList: {
        type: Array,
        default: () => []
    }
}

// ❌ 错误
props: ['status', 'entryList']  // 缺少类型定义
```

### v-for 必须有 key

【强制】在组件上必须用key配合v-for

```vue
<!-- ✅ 正确 -->
<div v-for="item in items" :key="item.id">
    {{ item.name }}
</div>

<!-- ❌ 错误 -->
<div v-for="item in items">
    {{ item.name }}
</div>
```

### 避免 v-if 和 v-for 一起使用

【强制】避免 v-if 和 v-for 用在一起

```vue
<!-- ❌ 错误 -->
<div v-for="user in users" v-if="user.isActive" :key="user.id">
    {{ user.name }}
</div>

<!-- ✅ 正确：使用计算属性 -->
<div v-for="user in activeUsers" :key="user.id">
    {{ user.name }}
</div>

<script>
export default {
    computed: {
        activeUsers() {
            return this.users.filter(user => user.isActive);
        }
    }
}
</script>
```

### 指令缩写

【强制】指令缩写（用:表示v-bind:和用@表示v-on:）应该要么都用要么都不用

```vue
<!-- ✅ 正确：统一使用缩写 -->
<input :value="name" @input="handleInput">

<!-- ❌ 错误：混用 -->
<input v-bind:value="name" @input="handleInput">
```

## 样式规范

### CSS 作用域

【强制】如果在vue文件中写css样式，需要在style内加scoped

```vue
<style scoped>
.entry-list {
    /* 样式只作用于当前组件 */
}
</style>
```

### 公共样式

【推荐】公共样式直接写在src/assets/css/index.css中，或者单独写一个css文件在index.html引入

### 样式分离

【推荐】如果vue文件中css样式超过约100行，需提取成css文件，文件放在同级路径下

## 禁止事项

### ❌ 禁止提交node_modules和dist目录

【强制】不允许提交node_modules和dist目录到配置管理工具

```
# .gitignore
node_modules/
dist/
*.log
```

### ❌ 禁止使用ElementUI图标组件

【强制】不要使用ElementUI提供的图标组件，使用Font Awesome图标

```vue
<!-- ❌ 错误：ElementUI图标 -->
<i class="el-icon-edit"></i>

<!-- ✅ 正确：Font Awesome图标 -->
<i class="fa fa-edit"></i>
```

## 项目结构

```
src/
├── main.js              # 入口文件
├── App.vue              # 根组件
├── router/              # 路由配置
├── store/               # 状态管理
├── views/               # 页面视图
│   ├── entry/
│   │   ├── EntryList.vue
│   │   ├── EntryDetail.vue
│   │   └── api/         # 该功能模块的API
│   │       └── entryApi.js
├── components/          # 公共组件
├── assets/              # 静态资源
│   ├── css/
│   ├── images/
│   └── fonts/
├── utils/               # 工具函数
├── api/                 # 全局API（如果按功能模块分则在views下）
└── config/              # 配置文件
```

## 来源文档

- 《JavaScript开发规范》- 06-js-spec.md
- 《海关应用云平台开发规范》- 00-cacp-spec.md 第6节
