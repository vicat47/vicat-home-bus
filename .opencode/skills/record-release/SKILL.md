---
name: record-release
description: >-
  Activate when the user asks to create release plans, manage version releases, track feature checklists,
  generate CHANGELOGs, or mentions 发布计划、版本发布、功能清单、release plan、semantic versioning、RC、GA、SNAPSHOT.
  Adapts document granularity based on semantic versioning (MAJOR.MINOR.PATCH).
category: documentation
tags: ["release", "versioning", "semver", "changelog", "release-plan", "feature-checklist"]
---

# Record Release — 版本发布管理

在 `doc/releases/` 中管理版本发布计划。跟踪功能清单、驱动生命周期流转（draft → proposed → in-progress → in-review → released），并生成 CHANGELOG。**Release 文档从开发前开始，它是规划工具而非事后记录。**

**依赖**: 加载 `doc-structure`（目录基础设施、渐进索引、命名规范）。

**交叉引用**（全部建议，非强制）: `record-docs`（PRD/Spec 来源）、`record-adr`、`record-c4`（C4 变更）、`record-compliance`（major 版本上线前检查）。

**输出语言**: 面向用户的输出必须使用**简体中文**。

---

## 语义化版本 → 文档颗粒度

根据版本号自动决策文档量级：

| 版本段 | 颗粒度 | 产出物 |
|--------|--------|--------|
| `x.0.0` (MAJOR) | **完整** | Release Plan + RC + GA + CHANGELOG。建议触发 `record-compliance` |
| `0.x.0` (MINOR) | **中等** | Release Plan + 功能清单 + CHANGELOG。RC 可选 |
| `0.0.x` (PATCH) | **轻量** | 仅 CHANGELOG 条目，不创建独立发布文档 |

### 决策逻辑

```
1. 解析版本号 → 判断 MAJOR / MINOR / PATCH
2. 若 PATCH → 跳过发布计划，直接进入 CHANGELOG 流程
3. 若 MINOR 或 MAJOR → 创建发布计划
4. 若 MAJOR → 询问: "是否需要执行上线前架构合规检查？(record-compliance)"
```

---

## 发布文档生命周期

```
开发前                    开发中                  发布时
  │                         │                       │
  ▼                         ▼                       ▼
draft → proposed → in-progress → in-review → released
  │       │           │             │            │
  │       │           │             │            ├→ superseded → archived
  ▼       ▼           ▼             ▼            ▼
cancelled in any state
```

| 状态 | 含义 | 阶段 | 你在做什么 |
|------|------|------|-----------|
| `draft` | 规划中 | 开发前 | 脑暴「下个版本放什么」，功能清单任意改 |
| `proposed` | 已提议 | 开发前 | 功能清单写完了，自行确认 |
| `in-progress` | 开发中 | SNAPSHOT | 写代码，更新功能状态 `planned→done` |
| `in-review` | 验证中 | RC | 功能冻结，跑测试，打勾检查清单 |
| `released` | 已发布 | GA | 正式交付，触发 CHANGELOG |

**状态映射**（到统一 Model）: `draft`→draft, `proposed`→in-review, `in-progress`→in-progress, `in-review`→in-review, `released`→complete, `superseded`→superseded, `archived`→archived, `cancelled`→cancelled。

完整状态机参见 `references/state-machine.md`。

---

## 文件命名规范

```
doc/releases/YYYYMMDD__vX.Y.Z-{SNAPSHOT|RC|GA}__short-name.md
```

| 组件 | 格式 | 示例 |
|------|------|------|
| 日期 | `YYYYMMDD`（计划发布日期） | `20260623` |
| 分隔符 | `__`（双下划线） | |
| 版本 | `v` + semver | `v0.1.0` |
| 生命周期 | `-SNAPSHOT` / `-RC` / `-GA` | `-RC` |
| 短名 | kebab-case，最多 3 词 | `multi-tenant` |

**示例**:
```
doc/releases/20260615__v0.1.0-SNAPSHOT__multi-tenant.md
doc/releases/20260623__v0.1.0-RC__multi-tenant.md
doc/releases/20260701__v0.1.0-GA__multi-tenant.md
```

---

## 核心工作流

### 创建新发布计划

```
STEP 0: 确定版本号
  - 询问: "要创建哪个版本的发布计划？"
  - 若用户不确定 → ls doc/releases/ 找最新版本 → 建议 bump（MAJOR/MINOR/PATCH）
  - 执行版本颗粒度决策逻辑（见上文）

STEP 1: 确定 short-name
  - 询问: "这个版本的核心主题是什么？（2-3 个词，用作文件名）"
  - 若用户没给 → 从功能清单中提取最高频的关键词，转 kebab-case（如 "multi-tenant"）
  - 所有同版本的不同生命周期文件共享同一个 short-name

STEP 2: 冲突检查
  - 运行: ls doc/releases/ | grep "v<VERSION>"
  - 若同版本已存在 → 根据生命周期阶段提示下一步（升级 or 更新 or 弃用）
  - 若不存在 → 继续

STEP 3: 确定功能来源
  > 该版本的功能从何而来？
  > A) 从已有 PRD/Spec/RFC 汇编 — 扫描 doc/ 提取需求
  > B) 独立定义 — 逐一描述功能
  > C) 混合
  - 若用户选 A 但扫描无结果 → 告知用户并询问是否改用 B

STEP 4: 收集交叉引用（建议）
  - 功能涉及 C4 变更 → 询问关联
  - 功能涉及技术决策 → 询问是否创建 ADR

STEP 5: 生成文档
  - 读取模板: skills/record-release/templates/RELEASE.md
  - 填写全部 section，初始 status: draft
  - 确定日期: date +%Y%m%d
  - 保存: doc/releases/YYYYMMDD__vX.Y.Z-SNAPSHOT__<short-name>.md

STEP 6: 更新索引（必须）
  → 详见下方「索引维护」
```

### 同文件状态流转（draft → proposed → in-progress）

这三个阶段在同一个 SNAPSHOT 文件中完成，不需要创建新文件：

```
draft → proposed: 功能清单已定稿，自行确认后更新 status
proposed → in-progress: 确认通过，开始开发，更新 status
in-progress 期间: 持续更新功能清单中各功能的状态（planned → in-progress → done）
```

**每次都更新 `updated` 字段和 README.md 版本矩阵。**

### 跨文件生命周期推进（SNAPSHOT → RC → GA）

每个阶段创建新文件，通过 `supersedes` 串联：

**SNAPSHOT → RC**:
1. 读取 SNAPSHOT 文件
2. 确认功能清单已冻结（所有功能状态明确）
3. 生成 RC 文件：`status: in-review`，`supersedes: <SNAPSHOT 文件路径>`，新增「RC 验证清单」
4. 保存为 `YYYYMMDD__vX.Y.Z-RC__<short-name>.md`
5. 将原 SNAPSHOT 文件 `status` 改为 `superseded`

**RC → GA**:
1. 读取 RC 文件，确认验证通过
2. 生成 GA 文件：`status: released`，`supersedes: <RC 文件路径>`，新增「GA 确认」
3. 保存为 `YYYYMMDD__vX.Y.Z-GA__<short-name>.md`
4. 将 RC 文件 `status` 改为 `superseded`
5. **触发 CHANGELOG 生成**：读取 `skills/record-release/references/changelog.md`，按其中流程执行

---

## 索引维护（必须）

**每次创建或更新 release 文档后，必须执行：**

```bash
# 1. 确保基础设施存在
ls doc/releases/README.md 2>/dev/null || cp skills/doc-structure/templates/README__TEMPLATE.md doc/releases/README.md
ls doc/releases/AGENTS.md 2>/dev/null || cp skills/doc-structure/templates/AGENTS__TEMPLATE.md doc/releases/AGENTS.md

# 2. 更新 README.md 版本矩阵 — 必须添加/更新对应版本行
# 3. 更新 doc/README.md 全局索引（若 releases 为新分类）
```

**README.md 版本矩阵格式**:
```markdown
| 版本 | 生命周期 | 状态 | 计划日期 | 功能数 | 文件名 |
|------|---------|------|---------|--------|--------|
| v0.1.0 | SNAPSHOT | in-progress | 2026-06-23 | 3 | `20260623__v0.1.0-SNAPSHOT__multi-tenant.md` |
| v0.1.0 | RC | in-review | 2026-06-30 | 3 | `20260630__v0.1.0-RC__multi-tenant.md` |
```

---

## 功能清单格式

每个发布计划的必选内容：

```markdown
## 功能清单

| # | 功能 | 来源 | 状态 | 关联 ADR | 关联 C4 变更 | 备注 |
|---|------|------|------|----------|-------------|------|
| 1 | 多租户隔离 | `doc/prd/multi-tenant.md` | done | `adr/003-isolation.md` | `container-tenant-gateway` | |
| 2 | 租户切换 API | 独立录入 | in-progress | — | — | |
```

**功能状态**: `planned` → `in-progress` → `done` / `deferred` / `cancelled`

---

## 交叉引用规则

所有引用均为**建议**，有则关联：

```yaml
# 文档 frontmatter
related:
  adr: ""          # 驱动该版本的 ADR
  c4: ""           # 受影响的 C4 元素
  research: ""     # 支撑功能选型的调研
  radar: ""        # 引入的新技术雷达条目
```

---

## Agent 智能加载

进入 `doc/releases/` 时：
```
1. 读取 doc/releases/README.md（版本矩阵）
2. 定位活跃版本（status: in-progress 或 in-review）
3. 对同一版本只加载最新生命周期文件（GA > RC > SNAPSHOT）
4. 跳过 status: superseded / archived 的文件
```

---

## 目录结构

```
skills/record-release/
├── SKILL.md                    # 本文件
├── templates/
│   └── RELEASE.md              # 发布计划模板
└── references/
    ├── state-machine.md        # 完整状态机
    └── changelog.md            # CHANGELOG 生成参考
```
