---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["c4", "homebus", "component", "cli"]
related:
  container: "container.md"
  core: "component-core.md"
---

# C4 Level 3: Components — HomeBus CLI

> HomeBus CLI 的内部组件分解。Agent 通过 terminal 命令调用 CLI，CLI 封装参数后调 HomeBus API。

## 组件结构

```
┌───────────────────────────────────────────────────────┐
│  HomeBus CLI                                           │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │  Click CLI Entry Point                         │    │
│  │  ┌──────────┐ ┌─────────┐ ┌────────┐        │    │
│  │  │ publish  │ │  query  │ │ status │        │    │
│  │  │ command  │ │ command │ │command │        │    │
│  │  └────┬─────┘ └───┬─────┘ └───┬────┘        │    │
│  └───────┼───────────┼───────────┼──────────────┘    │
│          │           │           │                     │
│          ▼           ▼           ▼                     │
│  ┌──────────────────────────────────────────────┐    │
│  │  参数校验器 (Argument Validator)                │    │
│  │  - Click 内置类型校验                           │    │
│  │  - 自定义校验（枚举值、范围、依赖关系）             │    │
│  └──────────────────┬───────────────────────────┘    │
│                     │                                 │
│                     ▼                                 │
│  ┌──────────────────────────────────────────────┐    │
│  │  HTTP 客户端 (HTTP Client)                     │    │
│  │  - 构造请求体 (JSON)                           │    │
│  │  - 发送 HTTP 请求 (httpx/aiohttp)              │    │
│  │  - 解析响应                                    │    │
│  │  - 格式化输出                                  │    │
│  └──────────────────┬───────────────────────────┘    │
│                     │                                 │
│                     ▼                                 │
│  ┌──────────────────────────────────────────────┐    │
│  │  配置管理 (Config Manager)                     │    │
│  │  - HomeBus API URL（默认 localhost:8080）      │    │
│  │  - 超时配置                                    │    │
│  │  - 认证 token（未来扩展）                       │    │
│  └──────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

## 命令详情

### publish 命令

```
Usage: homebus publish [OPTIONS]

提交一个家庭事务事件。

Options:
  --body TEXT    完整 Event JSON                                   [required]
  --file PATH    从文件读取 Event JSON（与 --body 二选一）
  --api-url TEXT API Server 地址（默认从配置加载）
  --help         显示帮助信息
```

**Agent 调用示例：**
```bash
homebus publish --body '{"intent":"purchase","items":[{"name":"牛奶","quantity":3,"category":"consumable","price":20}],"total_price":60}'
```

### query 命令

```
Usage: homebus query [OPTIONS]

查询后端服务状态。

Options:
  --target TEXT     目标后端 (grocy/homebox/beancount)  [required]
  --operation TEXT  查询操作名                            [required]
  --params TEXT     查询参数 (JSON 格式)
  --help            显示帮助信息
```

**Agent 调用示例：**
```bash
homebus query --target grocy --operation stock_level --params '{"item":"牛奶"}'
```

### status 命令

```
Usage: homebus status [OPTIONS]

查询事件执行状态。

Options:
  --event-id TEXT   事件 ID  [required]
  --watch          持续等待直到事件完成 (可选)
  --help           显示帮助信息
```

### health 命令

```
Usage: homebus health [OPTIONS]

检查 HomeBus 健康状态。

Options:
  --help  显示帮助信息
```

## CLI 与 API 的映射

| CLI 命令 | API 端点 | 说明 |
|----------|----------|------|
| `homebus publish` | POST /v1/events | 参数校验 + 序列化 JSON → 发送 |
| `homebus query` | POST /v1/query | 同上 |
| `homebus status --event-id xxx` | GET /v1/events/xxx | 直接映射 |
| `homebus health` | GET /v1/health | 直接映射 |

## Agent 使用模式

Agent 在 Hermes 中这样使用 CLI：

```
Agent 的逻辑流程:

1. 解析用户自然语言 → 构建结构化参数
2. 调用 terminal("homebus publish --intent purchase ...")
3. 读取 CLI 返回 (stdout / exit code)
4. 如果 exit code = 0 → 告诉用户结果
5. 如果 exit code != 0 → 解析错误信息，修正后重试
```
