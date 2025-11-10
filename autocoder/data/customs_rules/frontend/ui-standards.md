---
description: "前端UI标准规范，包括Loading效果、圆角、阴影、字体、颜色等视觉设计规范"
globs:
  - "**/*.vue"
  - "**/*.css"
  - "**/*.scss"
  - "**/*.less"
alwaysApply: true
---

# 前端UI标准规范

## 规则条款

### 1. Loading效果规范

- **frontend_020**: loading应使用cacploading效果（即组件库内cacploading组件，该组件的展示效果为一个动态的关徽加载效果，通常使用v-cacploading='true'设置）
- 来源：frontend_rules修订版.xlsx 第21行
- 说明：统一的Loading效果提供一致的用户体验

### 2. 圆角规范

- **frontend_021**: 小圆角:3px
- 来源：frontend_rules修订版.xlsx 第22行
- 说明：统一的圆角尺寸符合设计规范

### 3. 阴影规范

- **frontend_022**: 阴影:0px 0px 12px rgba(0, 0, 0, 0.12)
- 来源：frontend_rules修订版.xlsx 第23行
- 说明：统一的阴影效果符合设计规范

### 4. 字体系列设置

- **frontend_027**: 字体设置：body{font-family:Arial, system-ui, -apple-system, "BlinkMacSystemFont", "Helvetica Neue", "Segoe UI", "Helvetica", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;}
- 来源：frontend_rules修订版.xlsx 第28行
- 说明：统一的字体系列确保跨平台显示一致性

## 标准版字体大小规范

### 5. 正文内容字体大小

- **frontend_028**: 正文内容、小标题:13px
- 来源：frontend_rules修订版.xlsx 第29行

### 6. 弹出框标题字体大小

- **frontend_029**: 弹出框标题:15px
- 来源：frontend_rules修订版.xlsx 第30行

### 7. Message提示字体大小

- **frontend_030**: Message、Alert 提示文字:14px
- 来源：frontend_rules修订版.xlsx 第31行

### 8. Popover标题字体大小

- **frontend_031**: Popover 提示标题:16px
- 来源：frontend_rules修订版.xlsx 第32行

### 9. 辅助信息字体大小

- **frontend_032**: 辅助信息、错误提示:12px
- 来源：frontend_rules修订版.xlsx 第33行

## 关怀版字体大小规范

### 10. 正文内容字体大小（关怀版）

- **frontend_033**: 正文内容、小标题:15px
- 来源：frontend_rules修订版.xlsx 第34行
- 说明：关怀版字体大小规范，适合视力较弱的用户

### 11. 弹出框标题字体大小（关怀版）

- **frontend_034**: 弹出框标题:17px
- 来源：frontend_rules修订版.xlsx 第35行

### 12. Message提示字体大小（关怀版）

- **frontend_035**: Message、Alert 提示文字:16px
- 来源：frontend_rules修订版.xlsx 第36行

### 13. Popover标题字体大小（关怀版）

- **frontend_036**: Popover 提示标题:18px
- 来源：frontend_rules修订版.xlsx 第37行

### 14. 辅助信息字体大小（关怀版）

- **frontend_037**: 辅助信息、错误提示:14px
- 来源：frontend_rules修订版.xlsx 第38行

## 海关蓝主题颜色规范

### 15. 主色

- **frontend_038**: 主色:#0f7edf
- 来源：frontend_rules修订版.xlsx 第39行

### 16. 辅助色-成功

- **frontend_039**: 辅助色成功:#1ebcaf
- 来源：frontend_rules修订版.xlsx 第40行

### 17. 辅助色-警告

- **frontend_040**: 辅助色警告:#fa5e45
- 来源：frontend_rules修订版.xlsx 第41行

### 18. 辅助色-信息

- **frontend_041**: 辅助色信息:#999999
- 来源：frontend_rules修订版.xlsx 第42行

### 19. 输入框禁用背景色

- **frontend_042**: 输入框禁用/下拉浮层/表格列悬停背景颜色:#f5f7fa
- 来源：frontend_rules修订版.xlsx 第43行

### 20. 选中背景色

- **frontend_043**: 下拉浮层选中、表格列选中背景颜色:#e7f2fc
- 来源：frontend_rules修订版.xlsx 第44行

### 21. 表格灰色表头背景色

- **frontend_044**: 表格灰色表头背景颜色:#f1f2f7
- 来源：frontend_rules修订版.xlsx 第45行

### 22. 表格灰色内容区背景色

- **frontend_045**: 表格灰色内容区背景颜色:#f7f8fb
- 来源：frontend_rules修订版.xlsx 第46行

### 23. 表格黄色表头背景色

- **frontend_046**: 表格黄色表头背景颜色:#fef9e5
- 来源：frontend_rules修订版.xlsx 第47行

### 24. 表格黄色内容区背景色

- **frontend_047**: 表格黄色内容区背景颜色:#fefbef
- 来源：frontend_rules修订版.xlsx 第48行

### 25. 按钮加载中背景色

- **frontend_048**: 按钮加载中背景颜色:#ffffff4d
- 来源：frontend_rules修订版.xlsx 第49行
- 说明：半透明白色

### 26. 必填项背景色

- **frontend_049**: 表单元素的必填背景颜色:#fef7de
- 来源：frontend_rules修订版.xlsx 第50行

### 27. 输入框边框颜色

- **frontend_050**: 输入框、下拉浮层边框颜色:#dcdfe6
- 来源：frontend_rules修订版.xlsx 第51行

### 28. 输入框悬停边框颜色

- **frontend_051**: 输入框边框悬停边框颜色:#c0c4cc
- 来源：frontend_rules修订版.xlsx 第52行

### 29. 滑块边框颜色

- **frontend_052**: 滑块默认边框颜色:#e4e7ed
- 来源：frontend_rules修订版.xlsx 第53行

### 30. 进度条边框颜色

- **frontend_053**: 进度条默认边框颜色:#ebeef5
- 来源：frontend_rules修订版.xlsx 第54行

### 31. 按钮禁用边框颜色

- **frontend_054**: 按钮禁用边框颜色:#cfe5f9
- 来源：frontend_rules修订版.xlsx 第55行

### 32. 小标题文字颜色

- **frontend_055**: 小标题、输入框输入后文字颜色:#000000
- 来源：frontend_rules修订版.xlsx 第56行

### 33. 主按钮文字颜色

- **frontend_056**: 主按钮文字颜色:#ffffff
- 来源：frontend_rules修订版.xlsx 第57行

### 34. 弹出框标题文字颜色

- **frontend_057**: 弹出框标题文字颜色:#333333
- 来源：frontend_rules修订版.xlsx 第58行

### 35. 表格文字颜色

- **frontend_058**: 表格标题、表格内容区文字颜色:#666666
- 来源：frontend_rules修订版.xlsx 第59行

### 36. 提示文字颜色

- **frontend_059**: 提示文字颜色:#999999
- 来源：frontend_rules修订版.xlsx 第60行

### 37. 辅助信息文字颜色

- **frontend_060**: 辅助信息文字颜色:#a8abb2
- 来源：frontend_rules修订版.xlsx 第61行

### 38. 图标颜色

- **frontend_061**: 输入框、表格之上图标颜色:#999999
- 来源：frontend_rules修订版.xlsx 第62行

## 政务红主题颜色规范

### 39. 主题色（政务红）

- **frontend_062**: 主题色:#e6261a
- 来源：frontend_rules修订版.xlsx 第63行

### 40. 文字按钮悬浮背景色

- **frontend_063**: 文字按钮悬浮背景色:#e6281a0f
- 来源：frontend_rules修订版.xlsx 第64行
- 说明：半透明红色

### 41. 输入框边框颜色（政务红）

- **frontend_064**: 输入框边框颜色:#c0c4cc
- 来源：frontend_rules修订版.xlsx 第65行

### 42. 下拉选中背景色

- **frontend_065**: 下拉选中背景色:#0f7edf1a
- 来源：frontend_rules修订版.xlsx 第66行
- 说明：半透明蓝色

### 43. 下拉选中字体颜色

- **frontend_066**: 下拉选中字体颜色:#0f7edf
- 来源：frontend_rules修订版.xlsx 第67行

### 44. Message背景颜色

- **frontend_067**: 提示Message背景颜色:#edf6ff
- 来源：frontend_rules修订版.xlsx 第68行

### 45. Message边框颜色

- **frontend_068**: 提示Message边框颜色:#cfe5f9
- 来源：frontend_rules修订版.xlsx 第69行

### 46. Message字体颜色

- **frontend_069**: 提示Message字体颜色:#0f7edf
- 来源：frontend_rules修订版.xlsx 第70行

### 47. Alert字体颜色

- **frontend_070**: 提示alert字体颜色:#0f7edf
- 来源：frontend_rules修订版.xlsx 第71行

## 适用场景

本规则适用于所有前端UI开发，是视觉设计的强制性规范，确保界面风格统一。
