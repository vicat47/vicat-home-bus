# INDEX: HomeBus 文档索引

> 最后更新: 2026-07-23
> `doc/` 下非索引文档总数: 22

本文档提供项目资产的分层索引，支持 agent 渐进式上下文加载。

## Level 0: 全局概览

| 类别 | 路径 | 文档数 | 状态 |
|------|------|--------|------|
| 规格说明 | `doc/specs/` | 11 | homebus.md + config-paradigm.md + event-types.md + routing-registry.md + backend-boundaries.md + sensitive-data.md + beancount-integration.md + database-schema.md + adapter-interfaces.md + api-contracts.md + cli-spec.md ✅ |
| 术语表 | `doc/glossary.md` | — | 固定文件 |
| ADR | `doc/adr/` | 0 | 目录暂未初始化，按需 `mkdir doc/adr` |
| C4 模型 | `doc/c4/` | 5 + 图例 | 文字描述 ✅ |
| PRD | `doc/prd/` | 1 | Draft |
| Roadmap | `/ROADMAP.md` | — | v0.1 → v1.0 路线图 |
| 调研 | `doc/research/` | 1 | Grocy CLI 资产分析 ✅ |
| RFC | `doc/rfcs/` | 2 | 配置格式变更 + PyPI 发布 |

## Level 1: 类别索引

| 目录 | README | 最后更新 |
|------|--------|----------|
| Specs | `doc/specs/README.md` | 2026-07-23 |
| RFCs | `doc/rfcs/` | 2026-07-20 (rfc-001, rfc-002) |

## Agent 渐进式加载指南

| 场景 | 加载目标 | 预计大小 |
|------|----------|----------|
| 首次进入项目 | 全局索引 + `glossary.md` | <100 行 |
| 需要核心架构上下文 | `doc/specs/homebus.md` | ~150 行 |
| 需要术语定义 | `doc/glossary.md` | <80 行 |
| 完整架构回顾 | 全局索引 + specs + glossary | <360 行 |
