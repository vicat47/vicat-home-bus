---
status: draft               # draft | in-progress | in-review | complete | superseded | archived | cancelled
domain: web-search          # web-search | code-verify
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: ""
tags: ["research"]
hypotheses: []              # Filled after Phase 3 — see H1/H2/H3 format below
# ---- Third-party library research ONLY ----
# library:
#   name: ""
#   latest_version: ""
#   license: ""
#   stars: 0
#   forks: 0
#   repository: ""
# related:
#   adr: ""
#   radar: ""
#   supersedes: ""
#   superseded_by: ""
---

# [Title Case Title]

> **状态**: `draft` | `in-progress` | `in-review` | `complete`
> **调研日期**: YYYY-MM-DD
> **调研领域**: web-search | code-verify

---

## 调研概要 / Research Brief

<!-- Phase 0 grill-me 的输出。用 5-10 行总结调研范围、约束、优先级和成功标准 -->

**调研问题**:
[This research aims to answer...]

**决策边界**:
- 包含: [candidates / approaches considered]
- 排除: [candidates / approaches explicitly excluded, with reason]

**约束条件**:
- 技术约束: [language, framework, protocol requirements]
- 组织约束: [team skills, maintenance cost, license compliance]
- 时间约束: [deadline, phased approach?]

**优先级排序**:
1. [highest priority dimension, e.g., 查询性能]
2. [second priority, e.g., 社区活跃度]
3. [third priority, e.g., 运维复杂度]

**成功标准**:
[What does "done" look like? What makes the conclusion actionable?]

---

## 假设 / Hypotheses

<!-- Phase 3: 在收集证据之前定义可证伪假设 -->

### H1: [Hypothesis Statement]

**主张**: We hypothesize that [specific, measurable claim]
**验证方法**: [How this will be verified — benchmark, code PoC, docs analysis, community survey]
**阈值**: [What result confirms the hypothesis vs refutes it]

### H2: [Hypothesis Statement] (if applicable)

**主张**: We hypothesize that [specific, measurable claim]
**验证方法**: [How this will be verified]
**阈值**: [What result confirms the hypothesis vs refutes it]

### H3: [Hypothesis Statement] (if applicable)

**主张**: We hypothesize that [specific, measurable claim]
**验证方法**: [How this will be verified]
**阈值**: [What result confirms the hypothesis vs refutes it]

---

## 证据与发现 / Evidence & Findings

<!-- Phase 4-5: 垂直切片结构 — 每个候选方案是自包含的完整薄片 -->

<!-- ====== 多候选方案调研（web-search）：为每个候选方案复制以下 block ====== -->
<!-- ====== 单方案验证（code-verify）：只需一个 Evidence 章节 ====== -->

### 候选方案 A: [Name]

#### 概览 / Overview
<!-- 项目简介、核心定位、适用场景 -->

#### 数据指标 / Metrics
<!-- GitHub stats, 版本历史, 社区健康度, 包管理器数据 -->

| 指标 | 数值 |
|------|------|
| ⭐ Stars | |
| 🍴 Forks | |
| 📦 Latest Version | |
| 📅 Latest Release Date | |
| 📄 License | |
| 🐛 Open Issues | |
| ⏱️ Issue Response Time | |
| 📊 Commit Frequency | |

#### 功能匹配度 / Feature Fit

| 需求 | 支持情况 | 匹配度 |
|------|----------|--------|
| [需求 1] | 原生支持 / 需适配 / 不支持 | ✅ / 🟡 / 🔴 |
| [需求 2] | 原生支持 / 需适配 / 不支持 | ✅ / 🟡 / 🔴 |
| [需求 3] | 原生支持 / 需适配 / 不支持 | ✅ / 🟡 / 🔴 |

#### Breaking Changes 与风险
<!-- 最近的 Breaking Changes、迁移成本、已知兼容性问题 -->

#### 假设验证 / Hypothesis Check

| 假设 | 结果 | 证据 |
|------|------|------|
| H1: [claim] | ✅ CONFIRMED / ❌ REFUTED / ⚠️ INCONCLUSIVE | [证据摘要] |
| H2: [claim] | ✅ / ❌ / ⚠️ | [证据摘要] |

#### 小结 / Verdict
<!-- 对该候选方案的独立判断 — 优劣势总结，是否推荐 -->

---

### 候选方案 B: [Name]

<!-- 结构同候选方案 A — 每个候选方案都是自包含的完整薄片 -->

#### 概览 / Overview

#### 数据指标 / Metrics

| 指标 | 数值 |
|------|------|

#### 功能匹配度 / Feature Fit

| 需求 | 支持情况 | 匹配度 |
|------|----------|--------|

#### Breaking Changes 与风险

#### 假设验证 / Hypothesis Check

| 假设 | 结果 | 证据 |
|------|------|------|

#### 小结 / Verdict

---

### 候选方案 C: [Name] (if applicable)

<!-- 结构同候选方案 A -->

---

## 交叉对比 / Cross-Candidate Comparison

<!-- Phase 6: 在所有候选方案独立分析之后，进行横向对比 -->

| 维度 | 权重 | 候选 A: [Name] | 候选 B: [Name] | 候选 C: [Name] |
|------|------|----------------|----------------|----------------|
| [维度 1, e.g., 查询性能] | 高 | | | |
| [维度 2, e.g., 社区活跃度] | 中 | | | |
| [维度 3, e.g., 运维复杂度] | 中 | | | |
| [维度 4, e.g., 许可证合规] | 低 | | | |
| **综合评分** | — | | | |

---

## 选型结论 / Recommendation

<!-- Phase 7: 综合所有证据、假设验证结果和交叉对比，给出最终推荐 -->

**推荐方案**: [Candidate Name]

### 推荐理由
1. [理由 1 — 引用具体证据]
2. [理由 2 — 引用假设验证结果]
3. [理由 3]

### 不契合点与适配方案

| 不契合点 | 影响 | 适配方案 |
|----------|------|----------|
| [不契合点 1] | [影响描述] | [如何适配或规避] |
| [不契合点 2] | [影响描述] | [如何适配或规避] |

### 未解决问题 / Open Questions
- [ ] [问题 1 — 需要进一步验证的内容]
- [ ] [问题 2]

---

## 决策记录 / Decisions Made

<!-- 调研过程中做出的决策及其理由 -->

| 决策 | 理由 | 日期 |
|------|------|------|
| | | |

---

## 参考资料 / References

<!-- 外部链接、文档、源代码文件 -->

- [Reference 1](url) — [为什么引用]
- [Reference 2](url) — [为什么引用]

---

## 后续行动 / Next Steps

- [ ] [Phase 7: 用户审查 — 确认/修改/拒绝调研结论]
- [ ] [若结论被采纳 → 创建或更新 ADR（record-adr）]
- [ ] [若结论被采纳 → 更新技术雷达（record-tech-radar）]
- [ ] [若发现新术语 → 更新术语表 doc/glossary.md]
- [ ] [Phase 8: 更新 doc/research/README.md 索引]
