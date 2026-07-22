---
status: complete
created: 2026-07-20
updated: 2026-07-22
author: "vicat47"
tags: ["glossary", "homebus"]
type: glossary
related:
  adr: ""
  c4: "doc/c4/context.md"
  research: ""
  radar: ""
---

# 术语表

> **项目专用术语词典**。定义项目中使用的领域术语、缩写、技术概念，确保团队和 AI agent 对核心概念有统一理解。

## 项目专用术语

| 术语 | 缩写 | 定义 | 上下文 | 相关文档 |
|------|------|------|--------|----------|
| HomeBus | — | 家庭服务总线——Beancount/Grocy/Homebox 之间的单一写入入口与事务协调器 | 核心架构 | [specs/homebus.md](specs/homebus.md) |
| 调谐引擎 | — | Reconciliation Engine——定期对比事件日志期望状态与后端实际状态，自动修复差异的守护模块 | HomeBus 内部 | [specs/homebus.md](specs/homebus.md) |
| 观测面 | — | Observation——HomeBus 在三后端之上架设的统一抽象层。对应自然语言概念（如"零食"、"厨房"），通过 `homebus query observation <name>` 获取跨系统聚合结果。⚠️ v0.2 规划。 | HomeBus 核心 (v0.2) | [specs/routing-registry.md](specs/routing-registry.md) |
| 路由注册表 | — | Routing Registry——品类/渠道路由规则的配置中心。存储为 TOML 文件（`~/.config/homebus/registry.toml`），Dispatch Engine 事件分发时查询获取默认位置、科目、负债账户。 | HomeBus 内部 | [specs/routing-registry.md](specs/routing-registry.md) |
| 纠偏 | — | 用户对 Agent 分类结果的修正操作，触发撤销旧记录、重建正确记录 | Agent 分类 | [specs/homebus.md](specs/homebus.md) |
| 消耗品 | — | 食品、日化、电池、猫砂等日常消耗物品。**特征**：使用后消失、不能二次销售、无需精细位置追踪。购买时直接费用化，库存由 Grocy 管理。 | 物品分类 | [specs/backend-boundaries.md](specs/backend-boundaries.md) |
| 资产 | — | 耐用品——洗衣机、手机、沙发、工具等。**特征**：可多次使用、可能卖出/转赠、需要精确位置追踪。Beancount 可记为资产账户，Homebox 管理物理位置。 | 物品分类 | [specs/backend-boundaries.md](specs/backend-boundaries.md) |
| 循环品 | — | 可消耗但非食品/日化的循环物品（电池、桶装水、猫砂）。消耗逻辑同消耗品（Grocy 管理），可补充。**不含**无实物载体的循环事项（水电用量）。 | 物品分类 | [specs/backend-boundaries.md](specs/backend-boundaries.md) |

## 架构术语

| 术语 | 缩写 | 定义 | 上下文 | 相关文档 |
|------|------|------|--------|----------|
| 单一写入入口 | — | 所有状态变更必须经过 HomeBus，Agent 不直接触碰任何后端 | 架构约束 | [specs/homebus.md](specs/homebus.md) |
| 不可变事件日志 | — | 仅追加的事件记录，作为对账基准，存储每次意图事件的完整执行过程 | 数据持久化 | [specs/homebus.md](specs/homebus.md) |
| Beancount event | — | Beancount 的 `event` 指令，产生一条时间线条目。**不是 HomeBus 事件**——纯文本注释，无 ID、不可关联、不支持结构化查询。记录是给人看的日记，不是给系统恢复用的操作记录。详见 [三阶模型](specs/backend-boundaries.md#beancount-的状态追踪能力三阶模型)。 | Beancount 功能 | [specs/backend-boundaries.md](specs/backend-boundaries.md) |
| Adapter | — | 适配器插件，实现统一接口封装对特定后端（Beancount/Grocy/Homebox）的调用 | 扩展机制 | [specs/homebus.md](specs/homebus.md) |
| Saga | — | 分布式事务模式——长事务拆分为多个本地事务，失败时执行补偿操作 | 事务协调 | [specs/homebus.md](specs/homebus.md) |

## 技术栈简称

| 简称 | 全称 | 用途 | 相关文档 |
|------|------|------|----------|
| HA | Home Assistant | 家庭自动化平台，可作为 HomeBus 的触发源和通知渠道 | [specs/homebus.md](specs/homebus.md) |
| n8n | n8n | 开源工作流自动化平台，稳定流程的最终落地目标 | [specs/homebus.md](specs/homebus.md) |
| APM | Atmosphere Package Manager | OpenCode 技能包管理工具 | [AGENTS.md](../AGENTS.md) |

---

## 维护说明

**何时添加术语**：
- 在文档（ADR、Spec、RFC）中首次引入新缩写或领域术语时
- PR review 中发现术语使用不一致时

**命名规范**：
- 缩写优先使用官方英文缩写（如 HA、n8n）
- 中文术语保持一致性

**维护者**：`record-docs` skill。
