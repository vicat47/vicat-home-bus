# Key Decisions

> **横切决策索引** — 从 ADR、tech-radar、research、compliance 等多个来源汇聚项目最关键的技术决策。
> 供 AI agent 快速建立项目上下文：这个项目选了哪些技术、做了哪些关键取舍。

## Active Decisions

<!-- 按决策域分组，每个决策一行。关联到具体 ADR 或 tech-radar 条目。 -->

| # | 决策 | 决策域 | 来源 ADR | 状态 | 日期 |
|---|------|--------|---------|------|------|
| 1 | 示例：选择 Apache Kafka 作为消息队列 | messaging | [adr/001-kafka-selection.md](adr/001-kafka-selection.md) | Active | 2025-01-15 |

## Technology Platform

<!-- 汇总当前项目使用的主要技术栈，按领域分组。
     状态沿用 tech-radar 的 Adopt / Trial / Assess / Hold。 -->

| 领域 | 技术 | 版本 | 状态 | 来源 |
|------|------|------|------|------|
| 消息队列 | Apache Kafka | 3.7.x | Adopt | [adr/001-kafka-selection.md](adr/001-kafka-selection.md), [tech-radar/apache-kafka.md](tech-radar/apache-kafka.md) |
| 数据库 | PostgreSQL | 16.x | Adopt | [tech-radar/postgresql.md](tech-radar/postgresql.md) |

## Architecture Constraints

<!-- 从 compliance-rules 中提取的最关键的架构约束。
     仅列入 Blocker 和 Critical 级别的规则。 -->

| 约束 | 级别 | 说明 | 来源 |
|------|------|------|------|
| 示例：UI 层禁止直接导入 Repository 层 | Critical | 必须通过 Service 层访问 | [compliance-rules/layer-boundary-ui-repository.md](compliance-rules/layer-boundary-ui-repository.md) |

---

## 维护说明

**何时更新**：
- 创建或变更 ADR → 评估该决策是否为"关键决策"，若是则更新 Active Decisions 表
- tech-radar 条目状态变更（如 Assess → Adopt）→ 更新 Technology Platform 表
- 新增 Blocker/Critical 级别 compliance rule → 更新 Architecture Constraints 表

**"关键决策"的判断标准**：
- 影响多个系统/服务/模块
- 引入新的核心技术栈
- 撤销或替代之前的决策
- 有显著的性能/成本/安全权衡
- 未来工程师可能质疑"为什么这么做"

**维护者**：`record-adr` skill（主责），`record-tech-radar`、`record-compliance` 提供补充。
