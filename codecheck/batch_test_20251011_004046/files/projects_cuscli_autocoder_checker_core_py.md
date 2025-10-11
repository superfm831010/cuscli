# 📄 文件检查报告

**文件路径**: `/projects/cuscli/autocoder/checker/core.py`
**检查时间**: 2025-10-11T00:40:46.002971
**检查状态**: ✅ success
**问题总数**: 36 个

## 📊 问题统计

| 严重程度 | 数量 |
|---------|------|
| ❌ 错误 (ERROR) | 12 |
| ⚠️ 警告 (WARNING) | 12 |
| ℹ️ 提示 (INFO) | 12 |
| **总计** | **36** |

---

## ❌ 错误 (12)

以下问题必须修复，可能导致系统崩溃、安全漏洞或数据丢失：

### 问题 1

- **位置**: 第 216-475 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 2

- **位置**: 第 250-509 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 3

- **位置**: 第 284-543 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 4

- **位置**: 第 314-573 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 5

- **位置**: 第 347-606 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 6

- **位置**: 第 387-646 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 7

- **位置**: 第 421-680 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 8

- **位置**: 第 460-719 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 9

- **位置**: 第 497-756 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 10

- **位置**: 第 532-791 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 11

- **位置**: 第 566-825 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

### 问题 12

- **位置**: 第 602-861 行
- **规则**: `backend_006`
- **描述**: 存在深层嵌套的if-else判断逻辑，嵌套层数超过3层
- **建议**: 建议使用策略模式或字典映射来简化判断逻辑

---

## ⚠️ 警告 (12)

以下问题强烈建议修复，影响代码质量、性能或可维护性：

### 问题 1

- **位置**: 第 95-840 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 2

- **位置**: 第 129-874 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 3

- **位置**: 第 163-908 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 4

- **位置**: 第 193-938 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 5

- **位置**: 第 226-971 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 6

- **位置**: 第 266-1011 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 7

- **位置**: 第 300-1045 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 8

- **位置**: 第 339-1084 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 9

- **位置**: 第 376-1121 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 10

- **位置**: 第 411-1156 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 11

- **位置**: 第 445-1190 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

### 问题 12

- **位置**: 第 481-1226 行
- **规则**: `backend_006`
- **描述**: main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准
- **建议**: 建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等

**问题代码**:
```
def main(input_args: Optional[List[str]] = None):
    args, raw_args = parse_args(input_args)
    ...
```

---

## ℹ️ 提示 (12)

以下是代码改进建议：

### 问题 1

- **位置**: 第 50-56 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 2

- **位置**: 第 84-90 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 3

- **位置**: 第 118-124 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 4

- **位置**: 第 148-154 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 5

- **位置**: 第 181-187 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 6

- **位置**: 第 221-227 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 7

- **位置**: 第 255-261 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 8

- **位置**: 第 294-300 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 9

- **位置**: 第 331-337 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 10

- **位置**: 第 366-372 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 11

- **位置**: 第 400-406 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

### 问题 12

- **位置**: 第 436-442 行
- **规则**: `backend_009`
- **描述**: resolve_include_path 函数功能单一，符合规范
- **建议**: 无需修改，代码质量良好

---

