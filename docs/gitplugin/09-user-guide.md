# Git 平台插件 - 用户使用指南

## 📖 简介

Git 平台插件为 Auto Coder 提供了 GitHub 和 GitLab 的配置管理和平台切换功能，让您可以在不同的代码托管平台之间无缝切换。

### 主要功能

- ✅ **GitHub 配置管理** - 支持配置多个 GitHub 账号或企业版实例
- ✅ **GitLab 配置管理** - 支持公网和私有部署的 GitLab
- ✅ **平台切换** - 一键切换 GitHub/GitLab
- ✅ **连接测试** - 验证配置是否正确
- ✅ **智能补全** - 命令和配置名自动补全

---

## 🚀 快速开始

### 第一次使用

1. **配置 GitHub**
   ```bash
   /git /github /setup
   ```

2. **配置 GitLab**
   ```bash
   /git /gitlab /setup
   ```

3. **查看当前平台**
   ```bash
   /git /platform
   ```

4. **切换平台**
   ```bash
   /git /platform /switch gitlab
   ```

---

## 📋 GitHub 配置

### 获取 GitHub Token

1. 登录 GitHub
2. 点击右上角头像 → **Settings**
3. 左侧菜单 → **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. 点击 **Generate new token**
6. 勾选权限：
   - ✅ `repo` - 仓库访问权限
   - ✅ `read:user` - 读取用户信息
7. 点击 **Generate token**
8. **复制生成的 token**（只显示一次！）

### 添加 GitHub 配置

```bash
/git /github /setup
```

按照提示输入：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 配置名称 | 便于识别的名称 | `personal-github` |
| API 地址 | GitHub API 地址 | `https://api.github.com`（默认） |
| Token | Personal Access Token | 粘贴您的 token |
| SSL 验证 | 是否验证 SSL 证书 | `y`（默认） |
| 超时 | API 请求超时（秒） | `30`（默认） |

### 管理 GitHub 配置

**查看所有配置：**
```bash
/git /github /list
```

**修改配置：**
```bash
/git /github /modify <配置名>
```

**删除配置：**
```bash
/git /github /delete <配置名>
```

**测试连接：**
```bash
/git /github /test <配置名>
```

---

## 🦊 GitLab 配置

### 获取 GitLab Token

#### 公网 GitLab (gitlab.com)

1. 登录 [GitLab.com](https://gitlab.com)
2. 点击右上角头像 → **Preferences**
3. 左侧菜单 → **Access Tokens**
4. 点击 **Add new token**
5. 填写信息：
   - Token name: `auto-coder`
   - Expiration date: 选择过期时间
   - Select scopes: ✅ `api`
6. 点击 **Create personal access token**
7. **复制生成的 token**

#### 私有 GitLab

步骤相同，只需要在您的私有 GitLab 实例上操作。

### 添加 GitLab 配置

```bash
/git /gitlab /setup
```

按照提示输入：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 配置名称 | 便于识别的名称 | `company-gitlab` |
| GitLab 地址 | GitLab 实例地址 | `https://gitlab.com` 或 `https://gitlab.example.com` |
| Token | Personal Access Token | 粘贴您的 token |
| SSL 验证 | 是否验证 SSL 证书 | 公网：`y`，私有：可能需要 `n` |
| 超时 | API 请求超时（秒） | `30`（默认） |

**注意：**
- 插件会自动在 GitLab 地址后添加 `/api/v4`
- 私有部署的 GitLab 如果使用自签名证书，需要禁用 SSL 验证

### 管理 GitLab 配置

**查看所有配置：**
```bash
/git /gitlab /list
```

**修改配置：**
```bash
/git /gitlab /modify <配置名>
```

**删除配置：**
```bash
/git /gitlab /delete <配置名>
```

**测试连接：**
```bash
/git /gitlab /test <配置名>
```

---

## 🔄 平台切换

### 查看当前平台

```bash
/git /platform
```

显示：
- 当前激活的平台（GitHub/GitLab）
- 使用的配置名称
- API 地址
- SSL 状态
- 最后测试时间

### 切换平台

**切换到 GitLab：**
```bash
/git /platform /switch gitlab
```

**切换到 GitHub：**
```bash
/git /platform /switch github
```

**切换并指定配置：**
```bash
/git /platform /switch github work-github
```

### 查看所有配置概览

```bash
/git /platform /list
```

显示所有平台的配置，当前激活的有 ✅ 标记。

---

## 🧪 连接测试

### 为什么要测试连接？

- ✅ 验证 Token 是否有效
- ✅ 检查网络连接
- ✅ 确认 API 地址正确
- ✅ 测试 SSL 配置

### 测试 GitHub

```bash
/git /github /test <配置名>
```

成功时显示：
- ✅ 连接成功
- 用户名
- 用户 ID
- API 限额

### 测试 GitLab

```bash
/git /gitlab /test <配置名>
```

成功时显示：
- ✅ 连接成功
- 用户名
- 姓名
- 用户 ID
- GitLab 版本

---

## 💡 常见场景

### 场景 1: 个人开源项目 + 公司项目

**配置：**
```bash
# 配置个人 GitHub
/git /github /setup
# 名称：personal-github

# 配置公司 GitLab
/git /gitlab /setup
# 名称：company-gitlab
```

**使用：**
```bash
# 开发开源项目时
/git /platform /switch github personal-github

# 开发公司项目时
/git /platform /switch gitlab company-gitlab
```

### 场景 2: 多个 GitHub 账号

**配置：**
```bash
# 个人账号
/git /github /setup
# 名称：github-personal

# 工作账号
/git /github /setup
# 名称：github-work
```

**切换：**
```bash
/git /platform /switch github github-work
```

### 场景 3: 私有 GitLab 实例

**配置：**
```bash
/git /gitlab /setup
```

**输入：**
- 地址：`https://gitlab.internal.company.com`
- SSL 验证：`n`（如果使用自签名证书）

---

## ❓ 常见问题

### Q1: Token 无效怎么办？

**症状：** 测试连接时显示 "401 认证失败"

**解决：**
1. 检查 Token 是否复制完整
2. 检查 Token 是否过期
3. 检查 Token 权限是否正确
4. 重新生成 Token 并修改配置：
   ```bash
   /git /github /modify <配置名>
   ```

### Q2: SSL 证书验证失败怎么办？

**症状：** 测试连接时显示 "SSL 证书验证失败"

**解决：**
1. 如果是私有 GitLab，禁用 SSL 验证：
   ```bash
   /git /gitlab /modify <配置名>
   # 选择不验证 SSL
   ```
2. 或者在服务器上安装正确的 SSL 证书

### Q3: 连接超时怎么办？

**症状：** 测试连接时显示 "连接超时"

**解决：**
1. 检查网络连接
2. 检查 API 地址是否正确
3. 增加超时时间：
   ```bash
   /git /github /modify <配置名>
   # 超时改为 60
   ```

### Q4: 如何查看配置文件？

**位置：**
```
.auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json
```

**查看：**
```bash
cat .auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json | jq
```

**注意：** Token 是加密的，不会以明文显示。

### Q5: 配置丢失了怎么办？

**备份配置：**
```bash
cp .auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json \
   config.json.backup
```

**恢复配置：**
```bash
cp config.json.backup \
   .auto-coder/plugins/autocoder.plugins.GitHelperPlugin/config.json
```

### Q6: 如何使用企业版 GitHub？

**配置时：**
- API 地址：`https://github.example.com/api/v3`
- 其他步骤与公网 GitHub 相同

### Q7: GitLab 提示 API 版本不支持？

**解决：**
- 确保 GitLab 版本 >= 11.0
- 检查 API 地址是否包含 `/api/v4`
- 尝试手动指定完整地址

---

## 🔒 安全建议

### Token 安全

1. **不要分享 Token** - Token 相当于您的密码
2. **定期更换 Token** - 建议每 3-6 个月更换一次
3. **最小权限原则** - 只勾选必要的权限
4. **使用有效期** - 为 Token 设置过期时间

### 配置安全

1. **加密存储** - Token 已自动加密存储
2. **备份密钥** - 备份 `~/.auto-coder/keys/.platform_key`
3. **权限控制** - 确保配置文件权限为 600

---

## 🎯 最佳实践

### 命名规范

**推荐的配置命名：**
- `personal-github` - 个人 GitHub
- `work-github` - 工作 GitHub
- `company-gitlab` - 公司 GitLab
- `personal-gitlab` - 个人 GitLab

**避免：**
- 太短的名称（如 `gh`）
- 难以区分的名称

### 定期测试

**建议：**
- 配置后立即测试
- Token 更换后测试
- 长时间未用后测试

**自动测试（配置后）：**
插件会在配置成功后提示是否测试，建议选择 "是"。

### 多环境管理

**开发环境：**
```bash
/git /platform /switch github dev-github
```

**生产环境：**
```bash
/git /platform /switch gitlab prod-gitlab
```

---

## 📞 获取帮助

### 命令帮助

```bash
/git /github /help      # GitHub 命令帮助
/git /gitlab /help      # GitLab 命令帮助
/git /platform          # 平台状态
```

### 查看日志

```bash
tail -f .auto-coder/logs/auto-coder.log | grep "Git Plugin"
```

### 问题反馈

如果遇到问题，请提供：
1. 错误信息截图
2. 相关日志
3. 配置信息（隐藏 Token）
4. 操作步骤

---

## 🎉 开始使用

现在您已经了解了所有功能，开始配置您的第一个平台吧！

```bash
/git /github /setup
```

或

```bash
/git /gitlab /setup
```

祝使用愉快！🚀
