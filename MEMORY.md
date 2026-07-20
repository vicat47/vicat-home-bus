# MEMORY.md — vicat-home-bus 项目记忆

> 本文档记录 HomeBus 项目的关键设计决策、已知约束和开发约定，确保进入本仓库的 AI Agent 能快速理解上下文。
> 对 Agent 而言：**优先级 = AGENTS.md > MEMORY.md > 具体 doc/ 文档**。AGENTS.md 讲"怎么做"，MEMORY.md 讲"为什么这么设计"。

---

## 项目本质

HomeBus 是一个**家庭服务总线**——位于 AI Agent 与三个后端（Grocy、Beancount、Homebox）之间的单一写入入口与事务协调器。不是微服务框架，不是消息队列，就是一个 Python FastAPI 单体 + Click CLI。

**一句话定位**：Agent 说人话 → HomeBus 分发到三个后端。

### 核心哲学

- **写操作**：事件→持久化→调度→Saga 兜底（先写日志再执行，不丢事件）
- **读操作**：查询代理（MVP 直连后端，v0.2 加观测面聚合）
- **HomeBus 无状态**：所有上下文由 Agent memory 维护
- **后端仍是权威数据源**：HomeBus 不做数据副本，只做操作中介

---

## 设计决策树（为什么要做成这样）

### D1: 为什么是 Bus 不是 Mesh？
最初的设想是让三个后端互相感知（Grocy 知道 Beancount 的存在），但复杂度爆炸。改为 Bus 模式：HomeBus 是唯一知道所有后端的组件，后端之间彼此不知。

### D2: 为什么事件先写再响应？
Agent 超时重试的场景下，先持久化再确认能保证事件不丢。代价是写操作的延迟多一次 SQLite INSERT（~1ms），可接受。

### D3: 为什么 events 和 executions 分表？
- events 表：不可变、仅追加、可重放（审计/调谐的基础）
- executions 表：可变、可重试、可看执行轨迹
- 两表通过 event_id 关联

### D4: 为什么 CLI 先行，MCP 后加？
参考 Claude Code 和 OpenCode 的模式：先 CLI（`terminal("homebus publish ...")`）快速验证闭环，再 MCP Server 做深度集成。同时也是克制——不为了"更智能"而增加复杂性。

### D5: 为什么用 TOML 不用 YAML？
上次尝试在项目中使用 YAML 配置时遇到了 Agent 写 YAML 格式不一致的问题（缩进错、引号乱）。TOML 结构更刚性，`tomllib` 是 Python 3.11 标准库，Agent 生成 TOML 的成功率远高于 YAML。

### D6: 为什么观测面（Observation）不在 MVP？
MVP 的 Agent 知道自己在查哪个后端——观测面的语义聚合本质上是"查 Grocy 零食库存 + 查 Beancount 零食支出"的合并操作，合并逻辑应在 Agent 层，而不是 HomeBus 层。观测面真正的价值只有结合调谐引擎（v0.3）才能发挥。

### D7: 为什么注册表路由规则无内置默认值？
张三家的"零食"在 Grocy 的父产品叫"零食"，李四家的叫"零食类"。HomeBus 不可能猜对。用户必须通过 `homebus init` 生成模板后按自己习惯配置。

---

## 已确认但未完成的设计

这些是已明确方向但还没写进代码/文档的决策，Agent 接手后可以直接推进：

| 项目 | 状态 | 备注 |
|------|------|------|
| Homebox 位置智能分配 | 策略已定 | Agent 通过 query 获取可用位置列表，结合上下文推断，用户确认。HomeBus 提供资源，Agent 做决策 |
| 补偿操作可推导 | 策略已定 | 根据原始 event_type + 已成功的 sub_task 自动生成逆向操作。不需要硬编码补偿清单 |
| Beancount 接入方式 | 待定 | MVP 建议用 fava REST API，不排除直接读写 .bean 文件。各有优劣 |
| Saga 不可撤销场景 | 待分析 | 如 Homebox 删除物品时已被手动删除，补偿怎么处理？记录日志 + 人工介入是兜底方案 |
| 产品级覆盖（override） | v0.2+ | `[routing.overrides]"蒙牛纯牛奶"` 允许 SKU 级别的路由定制，预留 TOML 结构 |

---

## 已知的设计矛盾与权衡

1. **"单一入口" vs "Agent 直查后端"** — 写操作严格单一入口，读操作也走总线但 MVP 不做聚合。这是原则与实际之间的权衡
2. **"无状态" vs "事件日志"** — HomeBus 本身无状态，但 events 表本身就是状态。准确说：HomeBus 不维护会话状态（session），但维护持久操作日志
3. **"Saga 补偿" vs "幂等重试"** — 两者都重要，但优先级：先保证幂等（避免重复操作），再用 Saga 兜底（处理不可重试的失败）
4. **"先写日志再响应" vs "响应延迟"** — MVP 阶段接受 +1ms 的延迟换取持久化保证。未来如果性能敏感可以优化为先回 accepted 再异步持久化，但会增加复杂度

---

## 版本边界速查

| 功能 | 版本 |
|------|------|
| 核心引擎 + CLI + Saga | v0.1 (MVP) |
| 路由注册表（品类/渠道映射） | v0.1 (MVP) |
| 查询代理（直连后端） | v0.1 (MVP) |
| MCP Server | v0.2 |
| 观测面引擎（语义聚合） | v0.2 |
| Webhook 回调 | v0.2 |
| 调谐引擎（定期对账） | v0.3 |
| 查询物化视图 / 缓存 | v0.4 |
| HA / 多用户 / n8n | v1.0 |

---

## 开发环境

- **工作区**：`$HOME/codes/python/homebus`（开发机实际路径因宿主而异）
- **Python**：3.11.15（uv 管理虚拟环境，非 pip）
- **依赖**：fastapi / uvicorn / aiosqlite / pydantic / click / httpx
- **远程**：`git@github.com:vicat47/vicat-home-bus.git`
- **文档索引**：`doc/README.md` — 13 个文档，含 C4 模型、PRD、Specs、RFCs

---

## 语言策略

对用户输出使用**简体中文**。代码、注释、commit message 使用**英文**。文档标题和 frontmatter 使用英文，正文按需（中文为主）。
