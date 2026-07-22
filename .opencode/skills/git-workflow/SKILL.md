---
name: git-workflow
description: Git 工作流与提交规范。当用户要求提交代码、推送、创建 PR，或提到 git、commit、提交、推送、PR、分支命名、commit message、HITL 时激活。定义 Conventional Commits 规范、分支命名、代码审查清单，以及人机协作的 HITL 切入点。
license: MIT
compatibility: 通用 Git 工作流，不依赖特定工具。
metadata:
  author: vicat
  version: "1.0"
---

Git 工作流与提交规范——涵盖 Conventional Commits、分支命名、代码提交前审查清单，以及人机协作的 HITL (Human-In-The-Loop) 切入点。

---

## 何时激活

当用户执行以下任一操作时，自动激活此 skill：
- 要求提交代码（commit、提交）
- 要求推送（push、推送）
- 要求创建 PR（pull request、合并请求）
- 询问 git 工作流、提交规范、commit message 格式

---

## OUTPUT LANGUAGE

**所有面向用户的输出必须使用简体中文。**

---

## 1. Commit Message 规范（Conventional Commits）

### 1.1 格式

```
<type>(<scope>): <description>

<body>

<footer>
```

### 1.2 Type 定义

| type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(api): 添加物品分类端点` |
| `fix` | Bug 修复 | `fix(saga): 修复调谐引擎空指针` |
| `chore` | 杂项维护，不影响功能代码 | `chore: 更新 uv 依赖` |
| `docs` | 文档变更 | `docs: 补充 API 使用说明` |
| `style` | 代码格式（不影响逻辑） | `style: 统一缩进为 4 空格` |
| `refactor` | 重构（非修复、非新功能） | `refactor: 提取 Saga 公共逻辑` |
| `perf` | 性能优化 | `perf(db): 优化事件日志查询索引` |
| `test` | 测试相关 | `test: 添加 Saga 集成测试` |
| `ci` | CI/CD 配置 | `ci: 添加 GitHub Actions 测试流水线` |
| `build` | 构建系统或外部依赖 | `build: 升级 Python 最低版本到 3.12` |
| `revert` | 回滚 | `revert: 回滚 feat(api) 提交` |

### 1.3 Scope（可选）

用括号标注影响范围，建议使用模块/目录名：
- `api` — API 路由与中间件
- `saga` — Saga 事务协调
- `dispatch` — 分发引擎
- `adapter` — 后端适配器
- `cli` — 命令行工具
- `db` — 数据库/存储
- `config` — 配置/路由注册表

### 1.4 Description（必填）

- 使用**简体中文**描述变更
- 以动词开头（如"添加""修复""重构""移除"）
- 首字母不用大写
- 末尾不加句号
- 50 字符以内为佳

### 1.5 Body（可选）

- 描述变更的**原因**和**细节**
- 使用简体中文
- 与 description 之间空一行

### 1.6 Footer（可选）

- `BREAKING CHANGE:` 标注破坏性变更
- `Closes #<issue>` 关联 Issue
- `Refs: #<issue>` 引用相关 Issue

### 1.7 示例

```
feat(api): 添加物品批量入库端点

支持一次性提交多个物品入库事件，
减少 Agent 的 API 调用次数。

Closes #42
```

---

## 2. 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能开发 | `feat/saga-retry` |
| `fix/` | Bug 修复 | `fix/dispatch-timeout` |
| `chore/` | 杂项维护 | `chore/update-deps` |
| `refactor/` | 重构 | `refactor/adapter-interface` |
| `docs/` | 文档 | `docs/api-reference` |

规则：
- 全小写，单词间用 `-` 连接
- 分支名简洁描述（3-4 词为佳）
- 避免使用中文（终端兼容性问题）

---

## 3. 代码提交前审查清单

**每次提交前，Agent 必须自查以下项目**：

- [ ] 无硬编码的密钥/Token/密码
- [ ] 无 `print()` / `console.log()` 调试语句残留
- [ ] 无大段注释掉的旧代码（可通过 git history 找回）
- [ ] 修改过的文件通过了 lint 检查
- [ ] 修改过的文件通过了 typecheck（如适用）
- [ ] 未包含不应提交的临时文件（`tmp/` 等 gitignored 目录除外）

若清单中有任何一项未通过，Agent **MUST** 先修复再提请用户审查。

---

## 4. HITL 切入点（Human-In-The-Loop Gates）

HITL 是 Agent 必须停下、向用户展示信息并**等待用户明确确认**的检查点。
Agent **不得**在未获得用户确认的情况下越过任何 GATE。

### 4.1 GATE 1: 提交前审查（Pre-commit Review）

**触发时机**：Agent 准备 `git add` 时。

**Agent 必须展示**：
```
## GATE 1 - 提交前审查

### 待提交文件：
  M  homebus/saga.py        (+12, -3)
  M  homebus/dispatch.py    (+8, -0)
  A  tests/test_saga.py     (+45, -0)

### 代码审查清单：
  [√] 无密钥泄漏
  [√] 无调试语句
  [√] 无注释旧代码
  [√] lint 通过
  [√] typecheck 通过

请确认是否继续提交？(yes/no)
```

**用户回应前 Agent 不得执行 `git commit`**。

### 4.2 GATE 2: 提交信息确认（Commit Message Validation）

**触发时机**：Agent 已准备好 commit message 时。

**Agent 必须展示**：
```
## GATE 2 - 提交信息确认

  feat(saga): 添加失败重试机制

  当适配器返回临时错误时，自动执行最多 3 次退避重试。
  重试间隔：1s / 2s / 4s。

  Closes #38

是否符合规范？是否确认提交？(yes/no)
```

**用户回应前 Agent 不得执行 `git commit`**。

### 4.3 GATE 3: 推送前审查（Pre-push Review）

**触发时机**：Agent 准备 `git push` 时。

**Agent 必须展示**：
```
## GATE 3 - 推送前审查

### 待推送分支：feat/saga-retry

### 待推送提交：
  abc1234 feat(saga): 添加失败重试机制
  def5678 chore: 更新 uv 依赖

### 远程状态：
  origin/main: 已同步
  origin/feat/saga-retry: 尚未创建（将新建远程分支）

请确认是否推送到远程？(yes/no)
```

**用户回应前 Agent 不得执行 `git push`**。

### 4.4 GATE 4: PR 创建确认（PR Creation Review）

**触发时机**：Agent 准备创建 Pull Request 时。

**Agent 必须展示**：
```
## GATE 4 - PR 创建确认

### PR 信息：
  Title: feat: 添加 Saga 失败重试机制
  Base:  main
  Head:  feat/saga-retry
  Body:
    当适配器返回临时错误时，自动执行最多 3 次退避重试。
    重试间隔：1s / 2s / 4s。
    Closes #38

### 变更摘要：
  3 files changed, 65 insertions(+), 3 deletions(-)

请确认是否创建 PR？(yes/no)
```

**用户回应前 Agent 不得执行 `gh pr create`**。

---

## 5. SQLite 数据库文件特别说明

本项目使用 SQLite (aiosqlite)，需特别注意：

- 数据库文件（`*.db`、`*.sqlite`、`*.sqlite3`）应在 `.gitignore` 中
- **绝不**提交数据库文件，因其可能包含生产数据
- 迁移/种子脚本（`migrations/`、`seeds/`）属于代码，应正常提交
- `git diff` 时注意检查是否误包含了 `.db` 文件

---

## 6. 工作流总览

```
[编码完成]
    |
    v
GATE 1: 提交前审查 ── 用户确认? ──否──> [返回修改]
    |是
    v
[git add]
    |
    v
GATE 2: 提交信息确认 ── 用户确认? ──否──> [修改 message / 返回修改]
    |是
    v
[git commit]
    |
    v
GATE 3: 推送前审查 ── 用户确认? ──否──> [返回检查]
    |是
    v
[git push]
    |
    v
GATE 4: PR 创建确认 ── 用户确认? ──否──> [返回修改]
    |是
    v
[gh pr create]
```

---

## 护栏

- **绝对不要**在用户未明确确认的情况下越过任何 HITL GATE
- **绝对不要**提交密钥、Token、密码或数据库文件
- **绝对不要**使用 `--force` 或 `--force-with-lease` 推送，除非用户明确要求
- **绝对不要**修改 git 历史（rebase、squash、amend）除非用户明确要求
- Commit message 的 description **必须**使用简体中文
- 每次提交前**必须**先执行 lint 和 typecheck
- 如果 lint/typecheck 失败，**必须**先修复，然后重新走 GATE 1 流程
- 不回滚、不强制推送已发布的分支，除非用户明确说明
