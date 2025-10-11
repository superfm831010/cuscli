# 📊 代码检查汇总报告

**检查 ID**: `batch_test_20251011_004046`
**开始时间**: 2025-10-11T00:40:46.005981
**结束时间**: 2025-10-11T00:40:46.005985
**总耗时**: 0.00 秒

## 📈 检查概览

| 统计项 | 数量 |
|--------|------|
| 总文件数 | 7 |
| 已检查文件 | 7 |
| 完成率 | 100.0% |
| **总问题数** | **81** |

## 🔍 问题分布

| 严重程度 | 数量 | 占比 |
|---------|------|------|
| ❌ 错误 (ERROR) | 27 | 33.3% |
| ⚠️ 警告 (WARNING) | 27 | 33.3% |
| ℹ️ 提示 (INFO) | 27 | 33.3% |

---

## 📋 文件检查详情

| 文件路径 | 状态 | 错误 | 警告 | 提示 | 总计 |
|---------|------|------|------|------|------|
| `/projects/cuscli/autocoder/checker/core.py` | ✅ | 12 | 12 | 12 | **36** |
| `...ts/cuscli/autocoder/checker/report_generator.py` | ✅ | 10 | 10 | 10 | **30** |
| `...ects/cuscli/autocoder/checker/file_processor.py` | ✅ | 1 | 1 | 1 | **3** |
| `...ts/cuscli/autocoder/checker/progress_tracker.py` | ✅ | 1 | 1 | 1 | **3** |
| `/projects/cuscli/autocoder/checker/__init__.py` | ✅ | 1 | 1 | 1 | **3** |
| `/projects/cuscli/autocoder/checker/rules_loader.py` | ✅ | 1 | 1 | 1 | **3** |
| `/projects/cuscli/autocoder/checker/types.py` | ✅ | 1 | 1 | 1 | **3** |

---

## 🔴 问题详情 (共 7 个文件有问题)

### 📄 /projects/cuscli/autocoder/checker/core.py

**问题数**: 36 个 (❌ 12 ⚠️ 12 ℹ️ 12)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ❌ **第 250 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ❌ **第 284 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
  _... 还有 9 个错误_
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ⚠️ **第 129 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
  _... 还有 10 个警告_
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范
  _... 还有 11 个提示_

### 📄 /projects/cuscli/autocoder/checker/report_generator.py

**问题数**: 30 个 (❌ 10 ⚠️ 10 ℹ️ 10)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ❌ **第 261 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ❌ **第 298 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
  _... 还有 7 个错误_
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ⚠️ **第 140 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
  _... 还有 8 个警告_
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范
  _... 还有 9 个提示_

### 📄 /projects/cuscli/autocoder/checker/file_processor.py

**问题数**: 3 个 (❌ 1 ⚠️ 1 ℹ️ 1)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范

### 📄 /projects/cuscli/autocoder/checker/progress_tracker.py

**问题数**: 3 个 (❌ 1 ⚠️ 1 ℹ️ 1)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范

### 📄 /projects/cuscli/autocoder/checker/__init__.py

**问题数**: 3 个 (❌ 1 ⚠️ 1 ℹ️ 1)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范

### 📄 /projects/cuscli/autocoder/checker/rules_loader.py

**问题数**: 3 个 (❌ 1 ⚠️ 1 ℹ️ 1)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范

### 📄 /projects/cuscli/autocoder/checker/types.py

**问题数**: 3 个 (❌ 1 ⚠️ 1 ℹ️ 1)

- ❌ **第 216 行**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- ⚠️ **第 95 行**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- ℹ️ **第 50 行**: resolve_include_path 函数功能单一，符合规范

---

## 📝 建议

- ❌ 发现 **27** 个错误，请优先修复
- ⚠️ 发现 **27** 个警告，建议修复以提高代码质量
- ℹ️ 发现 **27** 个改进建议，可考虑优化

详细的单文件报告请查看 `files/` 目录。
