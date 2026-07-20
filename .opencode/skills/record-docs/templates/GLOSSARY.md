# 术语表

> **项目专用术语词典**。定义项目中使用的领域术语、缩写、技术概念，确保团队和 AI agent 对核心概念有统一理解。

## 项目专用术语

<!-- 项目和业务领域特有的术语和缩写 -->

| 术语 | 缩写 | 定义 | 上下文 | 相关文档 |
|------|------|------|--------|----------|
| ACP | — | Agent Client Protocol — AI Agent 与客户端之间的通信协议 | Agent 开发 | [rfcs/001-agent-protocol.md](rfcs/001-agent-protocol.md) |

## 架构术语

<!-- 架构设计中使用的技术术语 -->

| 术语 | 缩写 | 定义 | 上下文 | 相关 C4 / ADR |
|------|------|------|--------|---------------|
| CQRS | — | Command Query Responsibility Segregation — 命令查询职责分离 | 架构模式 | [adr/002-cqrs-adoption.md](adr/002-cqrs-adoption.md) |

## 技术栈简称

<!-- 项目中使用的技术栈的简称和全称对照 -->

| 简称 | 全称 | 用途 | 相关文档 |
|------|------|------|----------|
| K8s | Kubernetes | 容器编排 | [c4/container-api-service.md](c4/container-api-service.md) |

---

## 维护说明

**何时添加术语**：
- 在文档（ADR、Spec、RFC）中首次引入新缩写或领域术语时
- PR review 中发现术语使用不一致时
- 新成员 onboarding 时发现需要解释的概念

**命名规范**：
- 缩写优先使用官方英文缩写（如 CQRS、gRPC）
- 中文术语保持一致性（同一概念全项目使用同一中文译名）

**维护者**：`record-docs` skill。任何 record-* skill 在创建文档时若引入新术语，应同时更新本表。
