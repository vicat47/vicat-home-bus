# vicat-home-bus

HomeBus 家庭服务总线——Beancount、Grocy、Homebox 之间的单一写入入口与事务协调器。

## 架构概览

```
用户输入 → Router/Gateway → AI Agent → HomeBus → Beancount / Grocy / Homebox
                                              ├─ 不可变事件日志
                                              └─ 调谐引擎
```

## 核心职责

- **单一写入入口**：所有状态变更必经 HomeBus
- **事件日志**：不可变追加日志，作为对账基准
- **后端分发**：根据意图和物品分类，调度 Beancount、Grocy、Homebox 适配器
- **调谐对账**：定期对比期望状态与实际状态，自动修复差异

## 技术栈

Python + FastAPI + Pydantic + SQLite (aiosqlite)

## 文档

| 文档 | 说明 |
|------|------|
| [架构规格](doc/specs/homebus.md) | 完整技术规格、数据模型、API 设计 |
| [术语表](doc/glossary.md) | 项目专用术语定义 |
| [AGENTS.md](AGENTS.md) | AI Agent 工作指南 |
