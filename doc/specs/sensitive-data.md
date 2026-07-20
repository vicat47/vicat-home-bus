---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "security", "publishing"]
type: spec
related:
  agents: "AGENTS.md"
  memory: "MEMORY.md"
---

# HomeBus 敏感数据处理规范

> 定义本仓库哪些信息应脱敏、哪些可保留，以及发布/分叉前的检查清单。

## 核心原则

**"别人 fork 了能直接用"的信息就是安全的。**
**"fork 了还要手动改"的信息才是要脱敏的。**

也就是说：公开信息不需要脱敏，但个人/本地环境细节需要。

---

## 敏感度分类

### 🔴 必须脱敏（个人/本地环境细节）

| 类别 | 示例 | 理由 |
|------|------|------|
| **内网 IP / 域名** | `192.168.31.40` | 家庭网络精确拓扑，接收者无法使用同一个 IP |
| **WSL / 本地绝对路径** | `/mnt/g/codes/...` | 开发机文件系统布局，接收者的环境不同 |
| **本地仓库间相对路径** | `../home-vicat-skills/` | 同一机器上的项目间引用，外部 fork 不成立 |
| **真实 API Key / Token** | `sk-xxx...` | 明文凭据，必须永不上 git |
| **SSH 私钥 / 密码** | `-----BEGIN OPENSSH PRIVATE KEY-----` | 必不提交 |

### 🟡 上下文敏感（视场景决定）

| 类别 | 示例 | 处理策略 |
|------|------|----------|
| **本地 shell 变量示例** | `export GROCY_API_KEY=your-key` | 保持占位符即可，不暴露真实值 |
| **Docker Compose 示例** | `image: homebus:latest` | 用通用名，不用本地 tag |
| **开发环境说明** | Python 3.11.15 | 版本信息可保留（有用），路径部分脱敏 |

### ✅ 无需脱敏（公开/项目元数据）

| 类别 | 示例 | 理由 |
|------|------|------|
| **GitHub 用户名** | `vicat47` | 公开社交身份，README/CONTRIBUTING 里本该出现 |
| **GitHub 仓库名** | `vicat-home-bus` | 公开项目名，PyPI 包名、代码 import、文档引用都依赖它 |
| **GitHub 仓库 URL** | `github.com/vicat47/vicat-home-bus` | README 安装链接必需 |
| **项目内作者标识** | `author: "vicat47"` | 文档元数据，与 git log 一致，无额外信息 |
| **其他公开仓库名** | `home-vicat-skills` | 公开仓库，外部可见 |
| **外部服务 URL 示例** | `http://grocy:9283` | Docker 网络示例，通用占位符 |
| **占位符 API Key** | `your-key`, `<your-token>` | 显而易见非真实凭据 |
| **版本号/日期** | `v0.1.0`, `2026-07-20` | 项目元数据，无安全含义 |

---

## 发布前检查清单

在公开仓库、发布 PyPI 包、或分享给他人前，逐项确认：

- [ ] 无真实 API Key / Token / 密码出现在任何文件中
- [ ] 无内网 IP 地址（如 `192.168.x.x`、`10.x.x.x`）
- [ ] 无 WSL 绝对路径（`/mnt/...`、`/root/...`）
- [ ] 无本地项目间绝对引用路径
- [ ] `.env` / `config.toml` 在 `.gitignore` 中
- [ ] `.env.example` / `config.toml.example` 只包含占位符
- [ ] 示例代码中的凭据用 `<...>` 或 `your-*` 占位
- [ ] 无 SSH 私钥、GPG 密钥、证书文件

---

## MEMORY.md 中的特殊处理

`MEMORY.md` 包含"开发环境"一节展示了本地路径。按本规范：
- GitHub 仓库 URL 可保留（公开信息）
- WSL 绝对路径应替换为 `$HOME/...` 相对形式或通用占位符
- 原始路径可以 HTML 注释保留在原文中（对接收者无影响，仅供原始作者参考），但发布前应剥离

---

## 这个规范本身

`doc/specs/sensitive-data.md` 不含任何敏感信息。它定义的就是规则本身，可以公开。
