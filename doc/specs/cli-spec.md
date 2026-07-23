---
status: draft
priority: P1
blocks:
  - cli/homebus.py
created: 2026-07-23
updated: 2026-07-23
author: "vicat47"
tags: ["spec", "homebus", "cli", "mvp"]
type: spec
related:
  prd: "../prd/homebus-v0.1.md"
  api-contracts: "api-contracts.md"
  config-paradigm: "config-paradigm.md"
---

# HomeBus CLI 规范 — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-23
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus CLI（`homebus` 命令）的子命令、参数、输出格式。CLI 作为 Agent 的唯一调用入口，是 HTTP client 薄封装。

## 设计原则

| 原则 | 说明 |
|------|------|
| **透传而非解析** | CLI 不做字段级解析，JSON 原样传递到 API |
| **单一输出格式** | 所有命令输出 JSON（stdout），错误输出到 stderr |
| **退出码语义** | 0=成功，非 0=失败（Agent 可通过退出码快速判断） |
| **配置来源** | API URL 从 `--api-url` / `HOMEBUS_CLI_URL` 环境变量 / `~/.config/homebus/config.toml` 加载 |

## 子命令

### `homebus publish`

```bash
homebus publish --body '{"intent":"purchase","items":[...],"total_price":60}' --api-url http://localhost:8080
homebus publish --file ./event.json
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--body` | JSON string | 是（与 `--file` 二选一）| 完整 Event JSON |
| `--file` | path | 是（与 `--body` 二选一）| 从文件读取 Event JSON |
| `--api-url` | string | 否 | API Server 地址（默认从配置加载）|

> **决策**：使用 `--body` 单 JSON 方案（方案 B），CLI 不做 `--intent`、`--items` 等字段级解析。`--file` 作为备选用于长 JSON，行为等价于 `--body "$(cat file.json)"`。

输出：

```json
{"event_id": "evt_sess1_001", "status": "pending", "message": "事件已接收"}
```

退出码：
- 0: 事件已接收（含幂等命中）
- 1: 请求失败（4xx/5xx 或网络错误）

---

### `homebus status`

```bash
homebus status --event-id evt_sess1_001
homebus status --event-id evt_sess1_001 --watch --timeout 30
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--event-id` | string | 是 | 事件 ID |
| `--watch` | flag | 否 | 轮询直到终态 |
| `--timeout` | int | 否 | watch 模式最大等待秒数（默认 60） |
| `--api-url` | string | 否 | API Server 地址 |

输出：

```json
{"event_id": "evt_sess1_001", "status": "success", "intent": "purchase", "executions": [...]}
```

---

### `homebus query`

```bash
homebus query --target grocy --operation stock_query --params '{"product_name":"牛奶"}'
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--target` | string | 是 | `grocy` / `beancount` / `homebox` |
| `--operation` | string | 是 | 操作名称 |
| `--params` | JSON string | 是 | 查询参数 |
| `--api-url` | string | 否 | API Server 地址 |

输出：

```json
{"data": {"product_name": "牛奶", "stock": 50}, "event_id": "evt_q_001"}
```

---

### `homebus health`

```bash
homebus health
```

无参数（API URL 从配置自动加载）。

输出：

```json
{"status": "healthy", "adapters": {"grocy": "ok", "beancount": "ok", "homebox": "ok"}}
```

---

### `homebus init`

```bash
homebus init
homebus init --force
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--force` | flag | 否 | 覆盖已存在的配置文件 |

行为：
1. 创建 `~/.config/homebus/` 目录（若不存在）
2. 生成 `config.toml` 模板（含注释的占位符值）
3. 生成 `registry.toml` 模板（含品类路由和渠道路由示例）
4. 生成 `.env.example` 模板（API Key 占位符）
5. 如果文件已存在且未指定 `--force`，跳过并提示

---

## 配置发现

```
① --api-url 参数（最高优先级）
② 环境变量 HOMEBUS_CLI_URL
③ ~/.config/homebus/config.toml 中的 [cli.api_url]
④ 默认 http://localhost:8080
```

## 错误处理

| 场景 | 退出码 | stderr 输出 |
|------|--------|------------|
| API 返回 4xx | 1 | `Error: {error.code} — {error.message}` |
| API 返回 5xx | 1 | `Error: {error.code} — {error.message}` |
| 网络不可达 | 1 | `Error: 无法连接到 HomeBus API (http://localhost:8080)` |
| JSON 解析失败 | 1 | `Error: 无效的 JSON 参数` |
| --watch 超时 | 1 | `Error: 事件 evt_xxx 在 60s 内未达到终态` |

所有错误信息输出到 stderr，stdout 仅输出成功 JSON。Agent 可通过退出码 + stderr 判断错误类型并自行修正重试。
