---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "core"]
type: spec
related:
  adr: ""
  c4-core: "../c4/component-core.md"
  research: ""
  radar: ""
---

# HomeBus — 家庭服务总线规格说明

- **版本**: 0.1.0
- **日期**: 2026-07-20
- **作者**: vicat47
- **状态**: Draft

## 概述

HomeBus 是一个家庭服务总线，作为 Beancount（复式记账）、Grocy（消耗品库存管理）、Homebox（耐用品资产管理）之间的**单一写入入口**与**事务协调器**。用户通过 Router/Gateway 层输入指令，AI Agent 负责意图识别和物品分类，生成标准意图事件发送到 HomeBus，由 HomeBus 统一写入不可变事件日志并分发到各后端适配器。

## 架构分层

```
用户输入（语音/文本/快捷指令）
  │
Router / Gateway（认证、格式化、标准化消息体）
  │
AI Agent（意图识别、物品分类、实体提取、不确定性确认）
  │  publish_event
  ▼
HomeBus 核心
  ├─ 不可变事件日志（SQLite）
  ├─ 事件调度引擎（串/并行控制）
  ├─ 适配器层（Beancount Adapter / Grocy Adapter / Homebox Adapter）
  └─ 调谐引擎（定期对账、自动修复）
```

## 功能性需求

- **FR-1**：HomeBus 接收 Agent 发出的标准意图事件，写入不可变事件日志
- **FR-2**：根据事件类型和物品分类，调度对应的后端适配器执行操作
- **FR-3**：多个无依赖关系的外观调用应支持并行执行（如购买消耗品时 Beancount 记账与 Grocy 加库存并行）
- **FR-4**：支持纠偏/修正意图——撤销旧记录后再重建新记录
- **FR-5**：调谐引擎定期对比事件日志期望状态与后端实际状态
- **FR-6**：调谐引擎对可幂等操作自动重试修复，不可修复项报警
- **FR-7**：降级模式——后端服务不可用时，HomeBus 仅写事件日志暂存，待恢复后由调谐引擎补发
- **FR-8**：物品分类由 Agent 判断（消耗品 vs 资产），支持人工纠偏
- **FR-9**：每个后端适配器实现统一插件接口（execute、query_status、health_check）

## 非功能性需求

- **NFR-1**：事件日志不可变，仅追加
- **NFR-2**：后端 API 调用需实现幂等性（通过 event_id 去重）
- **NFR-3**：调谐引擎支持定时触发（cron）和事件驱动触发（子任务失败时）
- **NFR-4**：核心服务支持 Docker 部署

## 数据模型

### 标准意图事件

```json
{
  "event_id": "evt_<timestamp>_<seq>",
  "timestamp": "ISO8601",
  "session_id": "",
  "channel": "telegram | webui | shortcut",
  "intent": "purchase | consume | sell | query | correct",
  "raw_text": "用户原始输入",
  "entities": {
    "item": "物品名",
    "quantity": 2,
    "total_price": 15.00,
    "currency": "CNY",
    "account": "Assets:Alipay",
    "category": "consumable | asset",
    "location": ""
  },
  "subtasks": [
    {
      "service": "beancount | grocy | homebox",
      "action": "record_transaction | add_stock | consume_stock | create_item | update_item",
      "status": "pending | success | failed",
      "detail": "",
      "timestamp": ""
    }
  ]
}
```

### 事件日志表（SQLite）

| 字段 | 类型 | 说明 |
|------|------|------|
| event_id | TEXT PK | 事件唯一 ID |
| timestamp | TEXT | 事件时间 |
| intent | TEXT | 意图类型 |
| raw_text | TEXT | 原始输入 |
| entities_json | TEXT | 实体 JSON |
| subtasks_json | TEXT | 子任务执行记录 JSON |
| status | TEXT | pending / partial / success / failed / compensated |

## 后端调用规则

### 购买消耗品

- Beancount：`Expenses:<类别> CNY` / `Assets:<账户> -CNY`（费用化）
- Grocy：产品库存 +数量
- Homebox：无操作
- **并行**：Beancount ∥ Grocy

### 购买资产

- Beancount：`Assets:Inventory:<类别> CNY` / `Assets:<账户> -CNY`（资产增加）
- Homebox：创建物品，含价格、位置
- Grocy：无操作
- **并行**：Beancount ∥ Homebox

### 消耗品消耗

- Grocy：产品库存 -数量
- Beancount：不记账（购买时已费用化）
- Homebox：无操作
- **串行**：仅 Grocy

### 卖出资产

- Beancount：资产减少 + 收入确认
- Homebox：标记物品为"已售出"
- Grocy：无操作
- **并行**：Beancount ∥ Homebox

### 纠偏/修正

- **先串行撤销**（Grocy 回滚 + Beancount 冲销）
- **再并行重建**（Beancount 新分录 + Homebox 新物品）

## 物品分类与纠偏

Agent 按以下策略判断物品类别：

1. 优先遵循用户显式指令（"放到车库" → 资产、"记到冰箱" → 消耗品）
2. 无显式指令时，使用 LLM 常识判断
3. 信心不足时发起确认卡，阻塞等待用户回复
4. 用户可随时发出纠偏指令撤回错误分类并重建正确记录

## 调谐引擎

### 触发方式

- 定时 cron（轻量对账每 5 分钟，全量核对每天一次）
- 事件驱动（子任务返回失败时立即触发）

### 对账流程

1. 从事件日志提取自上次对账后的所有事件，计算期望状态
2. 查询各后端实际状态（Beancount 余额、Grocy 库存、Homebox 物品列表）
3. 计算差异向量，追溯根源事件
4. 可幂等操作 → 自动重试；不可修复 → 生成异常报告并报警

## 适配器接口

```python
class AdapterProtocol:
    async def execute(self, action: str, params: dict) -> dict: ...
    async def query_status(self, query: str) -> dict: ...
    async def health_check(self) -> bool: ...
```

初始版本内嵌 Python 模块实现，后续可按需拆分为独立进程插件。

## 未来迁移路径

- **HA 集成**：核心逻辑可抽出为 Home Assistant 的 `custom_component`，HA 作为触发源和通知渠道
- **n8n 落地**：稳定流程迁移到 n8n 工作流，HomeBus 退化为执行引擎，n8n 负责可视化编排
