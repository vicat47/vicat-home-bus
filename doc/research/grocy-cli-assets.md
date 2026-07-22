---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["research", "grocy", "cli", "homebus", "adapter"]
type: research
related:
  roadmap: "../../ROADMAP.md"
  prd: "../prd/homebus-v0.1.md"
  grocy-cli: "$HOME/codes/others/home-vicat-skills/packages/productivity/.apm/skills/grocy-cli/"
---

# Research: Grocy CLI 现有资产分析

> 发现日期: 2026-07-20
> 目的: 评估 grocy-cli skill 现有代码是否可复用为 HomeBus 的 Grocy Adapter

## 来源

| 属性 | 值 |
|------|-----|
| **路径** | `$HOME/codes/others/home-vicat-skills/packages/productivity/.apm/skills/grocy-cli/` |
| **Skill 名** | `grocy-cli` (APM managed) |
| **归属项目** | `home-vicat-skills` |
| **Grocy 实例** | `http://localhost:9283` v4.5.0 |

## 文件清单

| 文件 | 行数 | 职责 |
|------|------|------|
| `SKILL.md` | 230 | Skill 文档（命令手册 + 父/子产品关系 + 预设说明） |
| `scripts/grocy_cli.py` | 208 | CLI 入口（argparse 命令定义 + 分发） |
| `scripts/grocy_client.py` | 466 | Grocy API 纯 stdlib 客户端（curl + json） |
| `scripts/grocy_commands.py` | 805 | 所有命令处理函数（query/create/edit/stock 等） |
| `scripts/grocy_models.py` | 416 | 数据模型（Product, Cache, Preset, 校验器） |
| `references/grocy-api-reference.md` | — | Grocy REST API 参考文档 |
| `~/.hermes/scripts/grocy_client.py` | 同 | 软链/副本，供 HomeBus 外 Hermes cron 使用 |
| `~/.config/grocy/cache.yaml` | — | 位置/单位/产品组缓存 |

## 核心资产分析

### 1. GrocyClient (`grocy_client.py`)

| 特性 | 说明 |
|------|------|
| **HTTP 方式** | subprocess curl（无外部依赖，纯 stdlib） |
| **配置加载** | 优先级: 构造参数 > 环境变量 > `~/.config/grocy/config.yaml` |
| **API 覆盖** | Objects CRUD + Stock 操作 + Batteries/Chores + System |
| **查找工具** | `find_product_by_name()` 支持模糊匹配 |
| **依赖** | 无 (Python stdlib only) |

**复用策略**: 可直接 import 作为 HomeBus Grocy Adapter 的底层客户端。

### 2. 数据模型 (`grocy_models.py`)

| 类/函数 | 说明 |
|---------|------|
| `Product` | 产品实体，`to_create_dict()` `to_update_dict()` |
| `Cache` | 位置/单位/产品组缓存，YAML 持久化 |
| `Preset` | 预设系统（food/frozen/no_expire/category/hidden） |
| `find_product()` | 产品查找（精确 → 包含匹配） |
| `validate_product_data()` | 入口校验器 |

**复用策略**: Product 和 Cache 可直接复用。Preset 系统和校验逻辑参考设计但不一定直接引入 HomeBus。

### 3. CLI 入口 (`grocy_cli.py` + `grocy_commands.py`)

| 特性 | 说明 |
|------|------|
| **框架** | argparse（非 Click，HomeBus CLI 用 Click） |
| **命令** | query / create / edit / stock / shopping / battery / chore / sync |
| **预设置** | food / frozen / no_expire / category / hidden |
| **父/子产品** | `no_own_stock` 区分汇总口径 vs 实物 |

**复用策略**: 命令逻辑已成熟，可作为 HomeBus Grocy Adapter `execute()` 实现的参考。argparse 改为 HomeBus 的 Click 风格。

## 集成方案（待定）

> ⚠️ 以下为初步思路，具体方案在 HomeBus 主体框架搭好后商议。

### 方案 A: 直接 import

```
homebus/adapters/grocy.py
  ├→ from grocy_client import GrocyClient   # 直接复用
  ├→ from grocy_models import Product, Cache  # 复用数据模型
  └→ 包装为 AdapterBase 接口
```

**Pros**: 零代码重复，共享缓存文件（`~/.config/grocy/cache.yaml`）
**Cons**: 跨项目引用（`sys.path` 或 pip install -e），HomeBus 不可独立于 home-vicat-skills 仓库

### 方案 B: 提取独立库

```
home-vicat-skills/  ← 现有仓库不动
vicat-home-bus/
  └─ homebus/adapters/grocy/  ← 复刻/提取核心代码
      ├─ client.py     ← 基于 grocy_client.py 调整
      ├─ models.py     ← 基于 grocy_models.py 调整
      └─ adapter.py    ← AdapterBase 实现
```

**Pros**: 独立依赖，无仓库耦合
**Cons**: 代码重复，两个源需同步

### 方案 C: 统一包

将 GrocyClient 提取为独立 PyPI 包（如 `grocy-client`），HomeBus 和 home-vicat-skills 都依赖它。

**Pros**: 干净解耦
**Cons**: 额外维护成本，MVP 阶段过早

## 附录: Grocy API 核心端点

| 端点 | 方法 | HomeBus 用途 |
|------|------|-------------|
| `/api/stock` | GET | 查询库存（query） |
| `/api/stock/products/{id}/add` | POST | 入库（purchase） |
| `/api/stock/products/{id}/consume` | POST | 消耗（consume） |
| `/api/stock/products/{id}/inventory` | POST | 盘点校正（correct） |
| `/api/objects/products` | GET/POST/PUT | 产品 CRUD |
| `/api/system/info` | GET | 健康检查 |

## 下一步

- [ ] HomeBus 主体框架完成后评估集成方案（A/B/C）
- [ ] 确认缓存文件共享策略
- [ ] 确定是否需要统一凭证管理
