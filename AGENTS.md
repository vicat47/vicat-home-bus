# AGENTS.md — vicat-home-bus

> **前置阅读**：AGENTS.md 覆盖"怎么做"（目录结构、工作流、核心约束）。
> 设计背景和"为什么"见 [MEMORY.md](MEMORY.md)。

## 项目定位

HomeBus 是一个**家庭服务总线**，作为 Beancount（复式记账）、Grocy（消耗品库存管理）、Homebox（耐用品资产管理）之间的单一写入入口与事务协调器。AI Agent 负责意图识别和物品分类，HomeBus 负责事件的持久化、分发、调谐与对账。

## 技术栈

| 组件 | 技术 |
|------|------|
| 核心总线 | Python 3.11+ + FastAPI |
| 构建工具 | uv（依赖管理 + 虚拟环境） |
| 数据模型 | Pydantic |
| 事件日志 | SQLite (aiosqlite) |
| 后台任务 | FastAPI BackgroundTasks |
| 适配器 | Python 内嵌模块（Grocy、Beancount、Homebox API） |
| CLI | Click（入口：`homebus`） |
| 路由注册表 | TOML 文件加载（品类路由 + 渠道路由） |
| 未来集成 | Home Assistant custom_component, n8n webhook |

## 关键目录

| 路径 | 用途 | 管理方 |
|------|------|--------|
| `homebus/` | 核心 Python 包（API、调度、Saga、适配器） | 手动开发 |
| `cli/` | CLI 入口（`homebus publish/query/status`） | 手动开发 |
| `tests/` | 测试代码 | 手动开发 |
| `pyproject.toml` | 项目元数据 + 依赖声明 | uv |
| `uv.lock` | uv 依赖锁定文件 | uv |
| `apm.yml` / `apm.lock.yaml` | APM 技能清单与锁定文件 | APM CLI |
| `.opencode/skills/` | 已安装的 OpenCode 技能 | APM（有 active_owner 的文件不要手动编辑） |
| `.opencode/command/` | 自定义 `/opsx-*` 命令 | 本 repo |
| `openspec/` | OpenSpec 工作流 (schema: `spec-driven`) | `openspec-cn` CLI |
| `apm_modules/` | APM 依赖缓存 | APM（gitignored） |
| `tmp/` | 临时文件、草稿、设计讨论（gitignored） | 手动管理 |
| `doc/` | 项目文档（架构、规格、术语表等） | record-* 技能 |
| `TODO.md` | 待决策项（动态工作区） | 手动管理 |
| `ROADMAP.md` | 版本路线图 | 手动管理 |

## 命令

```bash
# Python 开发
uv sync                    # 安装/同步依赖
uv run homebus --help      # 运行 CLI
uv run uvicorn homebus.api:app --reload   # 启动 API 服务

# 配置管理
apm install                # 从 apm.yml 同步技能
openspec-cn list           # 列出活跃的 OpenSpec 变更
openspec-cn status --change "<name>" --json
```

## OpenSpec 工作流

使用 `schema: spec-driven`。自定义斜杠命令：

- `/opsx-propose <name>` — 创建变更，含 proposal、design、tasks
- `/opsx-apply <name>` — 实现变更中的任务
- `/opsx-archive <name>` — 归档已完成的变更

`openspec-cn` 是中文本地化 CLI。对用户输出使用 **简体中文**。

## TODO.md 工作流

TODO.md 是**待决策项**的临时工作区。决策完成后的生命周期：

1. 事项在 TODO.md 中讨论、形成初步决策
2. 决策稳定后，通过 record-* 技能转为 `doc/` 下的正式文档（Spec / RFC / ADR）
3. 已决策内容从 TODO.md 中**删除**，在 header 保留转向引用（如 `→ doc/specs/`）
4. TODO.md 只保留**尚未决策**的条目

## 技能归属

`apm.lock.yaml` 中有 `active_owner` 字段的技能文件由 APM 管理，来自 `home-vicat-skills` 仓库。**不要手动编辑这些文件**——下一次 `apm install` 会覆盖。本地技能（如 `openspec-*`）可自由编辑。

## 敏感数据处理

> 参考 [敏感数据处理规范](doc/specs/sensitive-data.md)。

本仓库的敏感数据处理遵循以下规则：

| 类别 | 处理方式 |
|------|---------|
| GitHub 公开信息（用户名、仓库名、URL） | **保留** — 公开元数据，fork 时自动适配 |
| 内网 IP（`192.168.x.x`、`10.x.x.x`） | **脱敏** — 示例中替换为 `localhost` 或占位符 |
| WSL 绝对路径（`/mnt/...`） | **脱敏** — 替换为 `$HOME/...` 或相对路径 |
| 真实 API Key / Token / 密码 | **永不提交** — 仅通过环境变量注入 |
| 占位符凭据（`your-key`、`<token>`） | **保留** — 显而易见的占位符，对读者有用 |

## record-* 文档规范

所有 record-* 产生的文档使用 YAML frontmatter，必需字段：`status`、`created`、`updated`、`author`、`tags`、`related`。状态值按文档类型不同（如 ADR 用 `proposed → accepted → implemented`，research 用完整的 `draft → in-progress → in-review → complete`）。权威规范见 `doc-structure/SKILL.md`。

## tmp/ 目录规范

- 临时文件、设计草稿、头脑风暴记录、外部设计讨论文档等一律放入 `tmp/`
- `tmp/` 中的文件不持久化、不纳入项目正式文档
- 当 tmp/ 中的设计内容稳定后，应按 record-* 规范转为 `doc/` 下的正式文档

## HomeBus 核心架构约束

1. **单一写入入口**：所有状态变更必须经过 HomeBus，Agent 不直接触碰任何后端
2. **不可变事件日志**：每次事件先写入日志，再分发到后端适配器
3. **路由注册表（MVP）**：品类路由（consumable/durable → 默认位置/科目）和渠道路由（京东/美团 → 负债账户）由 `~/.config/homebus/registry.toml` 管控，Dispatch Engine 分发时查询
4. **观测面（v0.2）**：跨系统语义化聚合查询，MVP 阶段 Agent 通过直连后端 Adapter 查询（`homebus query grocy stock`）
5. **Beancount**：家庭财务总账。作为一般性获物的入口（购买/工资/收入/报销），管理记账、资产账户、负债、事件支出。消耗品直接费用化，可出售物品记为资产。详见 [后端边界规范](doc/specs/backend-boundaries.md)
6. **Grocy**：消耗品生命周期管理。消耗品（食品、日化）、循环品（电池、猫砂）的入库/消耗/过期/盘点；家务（Chores）和采购清单（Shopping List）管理。不管理无实物载体的循环事项（水电用量）
7. **Homebox**：耐用品资产目录与物理位置管理。设备登记/位置追踪/状态管理（完好/维修/报废/已售）；**卖出逻辑的入口**（用户说"卖掉"→ Homebox 触发 sell 事件 + Beancount 记收入）。详见 [后端边界规范](doc/specs/backend-boundaries.md)
8. **物品分类**：由 Agent 判断消耗品 vs 资产，支持人工纠偏。HomeBus 不推测分类
9. **调谐引擎（v0.3）**：定期对比事件日志期望状态与实际状态，自动修复差异。MVP 不做
