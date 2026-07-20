# AGENTS.md — vicat-home-bus

## 项目定位

HomeBus 是一个**家庭服务总线**，作为 Beancount（复式记账）、Grocy（消耗品库存管理）、Homebox（耐用品资产管理）之间的单一写入入口与事务协调器。AI Agent 负责意图识别和物品分类，HomeBus 负责事件的持久化、分发、调谐与对账。

## 技术栈

| 组件 | 技术 |
|------|------|
| 核心总线 | Python + FastAPI |
| 数据模型 | Pydantic |
| 事件日志 | SQLite (aiosqlite) |
| 后台任务 | FastAPI BackgroundTasks / ARQ |
| 适配器 | Python 内嵌模块（Grocy、Beancount、Homebox API） |
| 未来集成 | Home Assistant custom_component, n8n webhook |

## 关键目录

| 路径 | 用途 | 管理方 |
|------|------|--------|
| `apm.yml` / `apm.lock.yaml` | APM 依赖清单与锁定文件 | APM CLI |
| `.opencode/skills/` | 已安装的 OpenCode 技能 | APM（有 active_owner 的文件不要手动编辑） |
| `.opencode/command/` | 自定义 `/opsx-*` 命令 | 本 repo |
| `openspec/` | OpenSpec 工作流 (schema: `spec-driven`) | `openspec-cn` CLI |
| `apm_modules/` | APM 依赖缓存 | APM（gitignored） |
| `tmp/` | 临时文件、草稿、设计讨论 | 手动管理 |
| `doc/` | 项目文档（架构、规格、术语表等） | record-* 技能 |

## 命令

```bash
apm install          # 从 apm.yml 同步技能
openspec-cn list     # 列出活跃的 OpenSpec 变更
openspec-cn status --change "<name>" --json
```

## OpenSpec 工作流

使用 `schema: spec-driven`。自定义斜杠命令：

- `/opsx-propose <name>` — 创建变更，含 proposal、design、tasks
- `/opsx-apply <name>` — 实现变更中的任务
- `/opsx-archive <name>` — 归档已完成的变更

`openspec-cn` 是中文本地化 CLI。对用户输出使用 **简体中文**。

## 技能归属

`apm.lock.yaml` 中有 `active_owner` 字段的技能文件由 APM 管理，来自 `home-vicat-skills` 仓库。**不要手动编辑这些文件**——下一次 `apm install` 会覆盖。本地技能（如 `openspec-*`）可自由编辑。

## record-* 文档规范

所有 record-* 产生的文档使用 YAML frontmatter，必需字段：`status`、`created`、`updated`、`author`、`tags`、`related`。状态值按文档类型不同（如 ADR 用 `proposed → accepted → implemented`，research 用完整的 `draft → in-progress → in-review → complete`）。权威规范见 `doc-structure/SKILL.md`。

## tmp/ 目录规范

- 临时文件、设计草稿、头脑风暴记录、外部设计讨论文档等一律放入 `tmp/`
- `tmp/` 中的文件不持久化、不纳入项目正式文档
- 当 tmp/ 中的设计内容稳定后，应按 record-* 规范转为 `doc/` 下的正式文档

## HomeBus 核心架构约束

1. **单一写入入口**：所有状态变更必须经过 HomeBus，Agent 不直接触碰任何后端
2. **不可变事件日志**：每次事件先写入日志，再分发到后端适配器
3. **Beancount 规则**：消耗品直接费用化（`Expenses`），可出售物品记为资产（`Assets:Inventory`）
4. **Grocy**：管理消耗品（食品、日化）库存，Beancount 不跟踪消耗品库存
5. **Homebox**：管理耐用品/资产（工具、电器、收藏品）的位置和状态
6. **物品分类**：由 Agent 判断消耗品 vs 资产，支持人工纠偏
7. **调谐引擎**：定期对比事件日志期望状态与实际状态，自动修复差异

## 无构建/测试/Lint

本 repo 为配置仓库，不含需构建、测试或 lint 的代码。
