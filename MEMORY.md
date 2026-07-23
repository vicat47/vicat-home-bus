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
参考 Claude Code 和 OpenCode 的模式：先 CLI（`terminal("homebus publish ...")`）快速验证闭环，再 MCP Server 做深度集成。

### D5: 为什么用 TOML 不用 YAML？
上次尝试在项目中使用 YAML 配置时遇到了 Agent 写 YAML 格式不一致的问题（缩进错、引号乱）。TOML 结构更刚性，`tomllib` 是 Python 3.11 标准库。

### D6: 为什么观测面（Observation）不在 MVP？
MVP 的 Agent 知道自己在查哪个后端——观测面的语义聚合在 Agent 层即可。观测面真正的价值只有结合调谐引擎（v0.3）才能发挥。

### D7: 为什么注册表路由规则无内置默认值？
张三家的"零食"在 Grocy 叫"零食"，李四家的叫"零食类"。HomeBus 不可能猜对。用户必须通过 `homebus init` 生成模板后按自己习惯配置。

### D8: 为什么 Beancount 写入走共享库而非 CLI subprocess？
API Server 调自己提供的 CLI 是循环依赖。`beancount_writer.py` 作为共享库，API Server Executor 直接 import，CLI（未来需要时）再做 thin wrapper。YAGNI——MVP 不需要 `homebus beancount write` 子命令。

### D9: 为什么 Beancount 元数据用 `#homebus` tag 而非 meta？
现有的 bot.bean 已使用 `#costflow` tag 标记来源。延续同一范式：`#homebus` tag 标记来源，`homebus_event:` meta 做幂等标识，`homebus_time:` 记录生成时间。`bean-query` 可原生过滤 `tag('homebus')`。

### D10: 为什么事件状态用 `accepted` 而非 `pending`？
两个词在不同层级有不同语义：`accepted` 是 API 层面的承诺（"我收下了"），`pending` 归 execution 级别使用（"子任务待执行"）。分层命名避免混淆。

### D11: 为什么允许混合品类 purchase？
用户的现有记账习惯是单笔交易可含多 posting（如午餐+饮料）。延续此范式：一次 purchase 事件含混合 category items，Beancount 生成一条含多 posting 的分录（consumable→费用化，durable→资产化）。

### D12: 为什么 Saga 补偿语义按后端分化？
三个后端的本质属性不同：Beancount undo（删除行）、Grocy reverse（新增反向记录）、Homebox undo（DELETE 资产）。Saga 的 COMPENSATION_MAP 每种 action 独立 lambda，复用同一个 `adapter.execute()` 接口。

### D13: Grocy fail-fast
产品名称在 Grocy 中不存在时直接报错阻塞事件——不静默跳过。Silent data loss 比报错更危险。Agent 收到 error 后可以先创建产品再重试 publish。

### D14: Homebox 补偿幂等
Saga 补偿 `delete_asset` 当 Homebox 返回 404（资产已手动删除）视为成功——补偿语义的目标是"该资产不应存在"，状态已达成。

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

## 已知的设计矛盾与权衡

1. **"单一入口" vs "Agent 直查后端"** — 写操作严格单一入口，读操作也走总线但 MVP 不做聚合。这是原则与实际之间的权衡
2. **"无状态" vs "事件日志"** — HomeBus 本身无状态，但 events 表本身就是状态。准确说：HomeBus 不维护会话状态（session），但维护持久操作日志
3. **"Saga 补偿" vs "幂等重试"** — 两者都重要，但优先级：先保证幂等（避免重复操作），再用 Saga 兜底（处理不可重试的失败）
4. **"先写日志再响应" vs "响应延迟"** — MVP 阶段接受 +1ms 的延迟换取持久化保证
5. **"会计冲销" vs "物理删除"** — Beancount 补偿用物理删除行（undo 式，非冲销分录）。原因：purchase 是一个事务边界，失败了整个 purchase 没发生过，不应留下半条记录

---

## 现有账本兼容性

用户的 Beancount 仓库使用按年/按领域组织，git 管理：

```
~/ledger/
├── main.bean                    ← include accounts/* + YYYY/YYYY.bean
├── accounts/ (5 个账户文件)
├── 2025/
│   ├── 2025.bean                ← include "0-default/*" 等
│   └── 0-default/
│       ├── 07.bean ~ 11.bean    ← 用户手写当月
│       └── homebus-07.bean      ← HomeBus 写入（glob 自动纳入）
└── 2024/2021/2022/ ...
```

关键兼容点：
- **零侵入**：`include "0-default/*"` glob 自动覆盖 HomeBus 文件，无需改任何现有文件
- **元数据对齐**：现有 `#costflow` tag + `tgbot_uuid/time` meta → HomeBus 的 `#homebus` tag + `homebus_event/time` meta
- **item: 元数据**：你已在用 `item:` meta 做分量级标注，HomeBus 延续此范式
- **bot.bean 先例**：2021-2024 已有机器记账文件

---

## 开发环境

- **工作区**：`$HOME/develop/python/vicat-home-bus`（开发机实际路径因宿主而异）
- **Python**：3.11+（uv 管理虚拟环境，非 pip）
- **依赖**：fastapi / uvicorn / aiosqlite / pydantic / click / httpx / pyyaml
- **远程**：`git@github.com:vicat47/vicat-home-bus.git`
- **文档索引**：`doc/README.md`（11 specs + 6 C4 + 1 PRD + 2 RFC = 24 文档）

---

## 语言策略

对用户输出使用**简体中文**。代码、注释、commit message 使用**英文**。文档标题和 frontmatter 使用英文，正文按需（中文为主）。
