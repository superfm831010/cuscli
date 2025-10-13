# Phase 8: 完整测试指南

## 🎯 测试目标

全面测试所有功能，确保质量和稳定性。

## 📋 测试准备

### 环境准备

1. **GitHub 测试账号**
   - 账号：您的 GitHub 账号
   - Token 获取：
     1. GitHub → Settings → Developer settings
     2. Personal access tokens → Tokens (classic)
     3. Generate new token
     4. 勾选：`repo`, `read:user`
     5. 复制 token

2. **GitLab 测试账号**
   - 账号：您的 GitLab 账号（gitlab.com）
   - Token 获取：
     1. GitLab → Settings → Access Tokens
     2. Add new token
     3. 勾选：`api`
     4. 复制 token

3. **清理测试环境**
   ```bash
   # 备份现有配置（如果有）
   cp .auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json \
      config.json.backup

   # 删除配置以全新开始
   rm -f .auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json
   ```

---

## 🧪 测试用例

### 测试套件 1: GitHub 配置管理

#### 1.1 添加 GitHub 配置

```bash
/git /github /setup
```

**输入：**
- 名称：`test-github`
- API 地址：（回车，使用默认）
- Token：`<您的真实 GitHub Token>`
- SSL 验证：`y`
- 超时：（回车，使用默认 30）

**预期结果：**
- ✅ 显示确认表格
- ✅ 保存成功
- ✅ 提示可以测试连接

#### 1.2 测试连接

```bash
/git /github /test test-github
```

**预期结果：**
- ✅ 显示 "连接成功"
- ✅ 显示用户名和 ID
- ✅ 显示 API 限额信息

#### 1.3 列出配置

```bash
/git /github /list
```

**预期结果：**
- ✅ 显示配置表格
- ✅ 包含 `test-github`
- ✅ 显示最后测试时间

#### 1.4 修改配置

```bash
/git /github /modify test-github
```

**操作：**
- 超时改为 60

**预期结果：**
- ✅ 修改成功
- ✅ 再次查看配置，超时为 60

#### 1.5 添加第二个配置

```bash
/git /github /setup
```

**输入：**
- 名称：`test-github-2`
- 其他：随意

**预期结果：**
- ✅ 两个配置都显示在列表中

#### 1.6 删除配置

```bash
/git /github /delete test-github-2
```

**预期结果：**
- ✅ 确认提示
- ✅ 删除成功
- ✅ 列表中只剩一个配置

---

### 测试套件 2: GitLab 配置管理

#### 2.1 添加 GitLab 配置

```bash
/git /gitlab /setup
```

**输入：**
- 名称：`test-gitlab`
- 地址：`https://gitlab.com`
- Token：`<您的真实 GitLab Token>`
- SSL 验证：`y`
- 超时：30

**预期结果：**
- ✅ 自动添加 `/api/v4` 路径
- ✅ 保存成功

#### 2.2 测试连接

```bash
/git /gitlab /test test-gitlab
```

**预期结果：**
- ✅ 连接成功
- ✅ 显示用户名和姓名
- ✅ 显示 GitLab 版本

#### 2.3 私有 GitLab 模拟

```bash
/git /gitlab /setup
```

**输入：**
- 名称：`private-gitlab`
- 地址：`https://gitlab.example.local`
- Token：`fake-token`
- SSL 验证：`n`

**预期结果：**
- ✅ 配置保存成功
- ✅ 测试连接失败，显示连接错误

#### 2.4 列表和管理

```bash
/git /gitlab /list
/git /gitlab /modify private-gitlab
/git /gitlab /delete private-gitlab
```

**预期结果：**
- ✅ 功能正常

---

### 测试套件 3: 平台切换

#### 3.1 查看初始状态

```bash
/git /platform
```

**预期结果：**
- ✅ 显示当前平台和配置

#### 3.2 切换到 GitLab

```bash
/git /platform /switch gitlab
```

**预期结果：**
- ✅ 切换成功
- ✅ 显示 GitLab 配置信息

#### 3.3 验证切换

```bash
/git /platform
```

**预期结果：**
- ✅ 显示 GitLab 为当前平台

#### 3.4 切换回 GitHub

```bash
/git /platform /switch github
```

**预期结果：**
- ✅ 切换成功

#### 3.5 平台概览

```bash
/git /platform /list
```

**预期结果：**
- ✅ 显示所有平台的配置
- ✅ 当前平台有 ✅ 标记

#### 3.6 多配置切换

**添加第二个 GitHub 配置：**
```bash
/git /github /setup
# 名称：github-work
```

**切换并指定配置：**
```bash
/git /platform /switch github github-work
```

**预期结果：**
- ✅ 切换成功
- ✅ 使用指定的配置

---

### 测试套件 4: 错误处理

#### 4.1 无效 Token

```bash
/git /github /setup
# 输入无效 token: invalid-token-12345
/git /github /test <配置名>
```

**预期结果：**
- ✅ 显示 "401 认证失败"

#### 4.2 无效 URL

```bash
/git /gitlab /setup
# 地址：https://invalid-url-that-does-not-exist.com
/git /gitlab /test <配置名>
```

**预期结果：**
- ✅ 显示连接错误

#### 4.3 SSL 错误（仅限有 SSL 问题的环境）

```bash
/git /gitlab /setup
# 地址：https://self-signed-ssl.example.com
# SSL：y
/git /gitlab /test <配置名>
```

**预期结果：**
- ✅ 显示 SSL 验证失败
- ✅ 提供修复建议

#### 4.4 超时测试

```bash
/git /github /modify <配置名>
# 超时改为 1 秒

# 然后在慢速网络下测试
/git /github /test <配置名>
```

**预期结果：**
- ✅ 显示超时错误

#### 4.5 删除不存在的配置

```bash
/git /github /delete non-existent-config
```

**预期结果：**
- ✅ 提示配置不存在

#### 4.6 切换到未配置的平台

**删除所有 GitLab 配置后：**
```bash
/git /platform /switch gitlab
```

**预期结果：**
- ✅ 提示需要先配置

---

### 测试套件 5: 命令补全

#### 5.1 静态补全

**测试所有级别：**
- `/git /` + Tab → 显示所有子命令
- `/git /github /` + Tab → 显示 GitHub 子命令
- `/git /gitlab /` + Tab → 显示 GitLab 子命令
- `/git /platform /` + Tab → 显示 `/switch`, `/list`

#### 5.2 动态补全

**配置名补全：**
- `/git /github /modify ` + Tab → 显示所有 GitHub 配置
- `/git /gitlab /test ` + Tab → 显示所有 GitLab 配置

**平台切换补全：**
- `/git /platform /switch ` + Tab → 显示 `github`, `gitlab`
- `/git /platform /switch github ` + Tab → 显示 GitHub 配置列表

**过滤补全：**
- 输入部分配置名 + Tab → 只显示匹配的

---

### 测试套件 6: PR 模块集成

#### 6.1 验证初始同步

```bash
# 启动应用
python -m autocoder.chat_auto_coder

# 检查日志
tail -f .auto-coder/logs/auto-coder.log | grep "PR 配置"
```

**预期结果：**
- ✅ 看到配置同步日志

#### 6.2 切换后同步

```bash
/git /platform /switch gitlab
# 检查日志
```

**预期结果：**
- ✅ 看到 "平台切换后已同步 PR 配置"

#### 6.3 验证 PR 配置

**创建测试脚本：**
```python
from autocoder.common.pull_requests import get_global_manager

manager = get_global_manager()
if manager.config:
    print(f"平台: {manager.config.platform}")
    print(f"地址: {manager.config.base_url}")
else:
    print("未配置")
```

**预期结果：**
- ✅ 显示当前激活平台的配置

---

### 测试套件 7: 配置持久化

#### 7.1 重启后配置保留

```bash
# 配置平台
/git /github /setup
/git /platform /switch github

# 退出应用
/exit

# 重新启动
python -m autocoder.chat_auto_coder

# 检查配置
/git /platform
/git /github /list
```

**预期结果：**
- ✅ 配置全部保留
- ✅ 当前平台保持不变

#### 7.2 配置文件格式

```bash
cat .auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json | jq
```

**预期结果：**
- ✅ JSON 格式正确
- ✅ Token 已加密（不是明文）
- ✅ 包含所有必要字段

---

## ✅ 测试检查清单

### 功能完整性
- [ ] GitHub 配置管理（增删改查）
- [ ] GitLab 配置管理（增删改查）
- [ ] 平台切换功能
- [ ] 连接测试功能
- [ ] 命令补全（静态+动态）
- [ ] PR 模块集成
- [ ] 配置持久化

### 用户体验
- [ ] 引导式配置友好易用
- [ ] 错误提示清晰明确
- [ ] 成功/失败状态显示明确
- [ ] 帮助信息完整
- [ ] 补全智能准确

### 健壮性
- [ ] 无效输入处理正常
- [ ] 网络错误处理正常
- [ ] SSL 错误处理正常
- [ ] 超时处理正常
- [ ] 边界条件处理正常

### 性能
- [ ] 配置加载快速
- [ ] 补全响应及时
- [ ] 连接测试有进度指示

---

## 📝 测试报告模板

```markdown
# Git 平台插件测试报告

## 测试环境
- 操作系统：
- Python 版本：
- 项目版本：

## 测试结果

### GitHub 配置管理
- [ ] 通过
- 问题：

### GitLab 配置管理
- [ ] 通过
- 问题：

### 平台切换
- [ ] 通过
- 问题：

### 命令补全
- [ ] 通过
- 问题：

### PR 集成
- [ ] 通过
- 问题：

## 发现的 Bug
1. ...

## 改进建议
1. ...

## 测试结论
- [ ] 通过，可以发布
- [ ] 部分通过，需要修复
- [ ] 未通过，需要重大修改
```

---

## 🎉 测试完成！

所有测试通过后：

➡️ **下一步**: 阅读 `09-user-guide.md`，编写用户文档
