---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "backends", "domain"]
type: spec
related:
  context: "../c4/context.md"
  event-types: "event-types.md"
  routing-registry: "routing-registry.md"
  glossary: "../glossary.md"
  agents: "../../AGENTS.md"
---

# HomeBus 后端定位与领域边界

> 定义 Beancount、Grocy、Homebox 三个后端在整个家庭数字化体系中的领域职责、数据流入口、以及边界模糊地带如何处理。
>
> **核心原则**：每个后端是各自领域的**最终权威数据源**。HomeBus 不做数据副本，只做操作中介。

---

## 总纲：三个后端的分工链条

```
"钱从哪来，花到哪去"
       │
       ▼
  ┌─────────────┐
  │  Beancount  │ ← 家庭财务总账。所有"钱"的变动都落在这里
  │  (会计)     │    包括：购买支出、工资收入、报销、转账、投资
  └──────┬──────┘
         │ "买了什么？"
         ▼
  ┌─────────────┐
  │   Grocy     │ ← 消耗品生命周期。从入库→使用→消耗/补充
  │  (仓储)     │    也包括：家务待办、采购清单、循环物品管理
  └──────┬──────┘
         │ "用完了/卖掉了？"
         ▼
  ┌─────────────┐
  │  Homebox    │ ← 耐用品/资产的物理位置和状态
  │  (资产)     │    从购入→登记位置→维修/保养→报废/卖出
  └─────────────┘
```

这个链条不是产品寿命链条，而是**数据因果关系链条**：
- Beancount 决定"钱到了谁手里"（财务事实）
- Grocy 决定"东西在仓库里还是被用了"（库存事实）
- Homebox 决定"东西在物理空间的哪个地方"（位置事实）

三条事实线互相补充，任何一条独立看都不完整，放在一起才能回答"家里发生了什么"。

---

## 一、Beancount — 家庭财务总账

### 定位

家庭复式记账的**唯一权威数据源**。所有涉及金钱变动的操作（收入、支出、转账、投资、借贷）都通过 HomeBus 写入 Beancount。

### 它管什么

| 领域 | 示例 | 说明 |
|------|------|------|
| **购买支出** | 超市、京东、线下购物 | 所有消耗品和耐用品的购买；通过 `purchase` 事件触发 |
| **收入纳管** | 工资、兼职、红包、二手卖出 | 作为"一般性获物"的记账入口 |
| **出差报销** | A 出差去北京，交通费¥500，住宿¥800 | 按项目/人员归入 Expenses，生成日记账 ← **你提到的"出差"场景** |
| **事件记录** | 装修、搬家、结婚 | 大额一次性支出 + 时间线记录 |
| **资产账户** | 房产估值、股票持仓、加密货币 | Beancount 管"值多少钱"，Homebox 管"放哪里" |
| **负债管理** | 房贷、车贷、白条、信用卡 | 贷款余额跟踪，与 HomeBus 渠道路由联动 |
| **月度/年度结算** | 收支平衡表、净资产报表 | Beancount 本身就是报表引擎，HomeBus 观测面从这里拿数据 |
| **税率/优惠** | 个税专项扣除、优惠券使用 | 作为金额事实的一部分记录在分录备注中 |

### 它不管什么

- ❌ 实物库存（那是 Grocy 的事）
- ❌ 物品在物理空间的存放位置（那是 Homebox 的事）
- ❌ 物品是否被消耗/过期（那是 Grocy 的 stock 系统）
- ❌ 家务管理（Grocy 的 chores + shopping list）

### 关键约束

1. **Beancount 不存"消耗品库存"** — 消耗品（牛奶、纸巾）购买时直接费用化到 `Expenses:Groceries`，不入 `Assets:Inventory`。只有可转售的耐用品才入资产账。Grocy 的库存数据由 Grocy 自己维护。
2. **Beancount 作为"一般性获物入口"** — 不限于购买。工资、二手卖出收入、退款、赠予都通过 Beancount 记账，但 HomeBus 对非购买场景只发 `expense`/`income` 事件，不走 `purchase` 的库存/资产分发逻辑。
3. **出差/事件作为备注+科目扩展** — 不出专用事件类型。出差在 Beancount 里是 `Expenses:Travel` + `Expenses:Accommodation` 科目，备注"张三 出差北京 2026-07"。HomeBus 提供 `expense` 事件类型，字段含 `actor`、`project`、`description`。
4. **工资用 income 事件** — 不经过 Grocy/Homebox，只写 Beancount。

### Beancount 的状态追踪能力：三阶模型

Beancount 的日记账（`event` 指令）和复式记账机制使它有能力承载"状态追踪"的某种含义。但这个能力是**分级的、有限制的**——高估它会导致职责混淆。

#### 第 0 阶 — 事件标注（日记，人读）

```beancount
2026-06-01 event "张三出差" "北京"
2026-07-15 event "厨房装修" "进行中"
```

`event` 指令在 Beancount 的 journal 中产生一条时间线条目，Fava 渲染在 Timeline 面板。

- **本质上是一条文本注释**——没有独立 ID、不能关联到其他条目、不具备结构化查询能力（不能问"张三出差过几次"）
- **用途**：时间线回顾——"这个月家里发生了什么事"
- **不依赖 HomeBus**：用户直接在 .bean 文件中手动编写，HomeBus 不做额外处理
- ⚠️ **这不是状态追踪，这是日记。不要用来承载业务逻辑。**

#### 第 1 阶 — 余额反映状态（隐式状态机）

```beancount
; 张三出差预支 → Assets:Receivable:张三 的余额从 0 → +2000
; 张三报销归零 → Assets:Receivable:张三 的余额从 +2000 → 0
```

通过**账户余额的变化**间接推导状态：

| 账户 | 余额 > 0 含义 | 余额 = 0 含义 |
|------|--------------|--------------|
| `Assets:Receivable:张三` | 张三在出差中/欠了预支款 | 张三已报销/不欠款 |
| `Assets:Savings:装修` | 装修款正在陆续投入 | 装修已结算完毕 |
| `Liabilities:Loan:房贷` | 贷款还在还 | 已还清 |

- **本质**：复式记账的自然产物——每笔交易都会改变余额，余额本身就是状态机
- **用途**：通过资产/负债账户余额隐式推导当前状态
- **HomeBus 观测面聚合**：v0.2 可以查询这些余额，告知用户"张三当前出差中"（`homebus query beancount balance --account Assets:Receivable:张三`）
- ⚠️ **这只对"有货币等价物"的状态有效**——"人在哪"不是货币问题，不适合通过余额推断

#### 第 2 阶 — 纯量跟踪（commodity tracking）

```beancount
commodity kWh

2026-06-30 * "电费" "6月用电"
  Assets:Tracking:ElectricMeter  350 kWh
  Income:PreviousBalance         350 kWh
; 当前余额 = 350 kWh（累计用电量）
```

使用 `commodity` + `pad` 跟踪非货币纯量（用电量、水用量、里程）：

| 可跟踪的纯量 | 典型单位 | Beancount 表现 | 适合？ |
|------------|---------|---------------|-------|
| 用电量 | kWh | commodity kWh，用 pad 增量写入 | ⚠️ 可以做，但不如专用仪表盘好 |
| 水用量 | 吨 | 同上 | ⚠️ 同理 |
| 健身次数 | 次 | 硬塞 commodity | ❌ 牵强，不应放在这里 |
| 体重趋势 | kg | 同上 | ❌ 不应该 |

- **用途**：需要"当前累计值"但不在任何后端管理范围内的非货币指标
- **HomeBus 对应**：v0.3 提供 `utility` 事件类型，触发 Beancount commodity tracking 分录的增量写入
- ⚠️ **只适用于"不重要但想看长期趋势"的数据**。核心家电仪表盘走 Home Assistant，不由 Beancount 管。

#### 三阶对照表

| 维度 | 第 0 阶（event 标注） | 第 1 阶（余额反映状态） | 第 2 阶（commodity tracking） |
|------|---------------------|----------------------|------------------------------|
| **用户意图** | "记一笔发生了什么" | "知道某人/某项目当前状态" | "跟踪累计用量" |
| **数据形式** | 纯文本 event 行 | 账户余额 | commodity 余额 |
| **查询方式** | Fava Timeline / 搜索备注 | 查账户余额 | 查 commodity balance |
| **是否可推导历史** | 是（按时间线） | 是（按分录推断） | 是（逐月增量） |
| **HomeBus 是否介入** | ❌ 不需要 | ✅ 观测面聚合 | ✅ utility 事件 |
| **替代方案** | 无——这就是 Beancount 的能力范围 | 同上 | Home Assistant 仪表盘 |
| **典型误用** | 试图通过 event 做事件溯源 | 试图追踪"张三在哪" | 试图记健身次数 |

### 关键澄清：Beancount event ≠ HomeBus 事件日志

| 维度 | Beancount event | HomeBus 事件日志 |
|------|----------------|-----------------|
| **核心目的** | 证明钱去哪了（审计证据） | 确保操作可靠执行（数据一致性） |
| **操作对象** | 会计分录 | 后端 API 调用 |
| **数据格式** | 纯文本，无 ID，无法关联 | 结构化 JSON，event_id，可关联 |
| **查询能力** | 按日期 + 正则搜索备注 | 按 event_id/类型/状态/时间戳 |
| **事务相关性** | 分录之间无关联 | event_id 串联所有 sub_task |
| **生命周期** | 无——附属在分录上 | 独立（accepted → executing → success/compensated/failed） |
| **非货币事件** | 能记（event），但无法结构化查询 | 设计目标就是记录结构化事件 |
| **故障恢复** | 不支持——不是为此设计的 | 核心能力——补偿/重试/对账 |

**一句话**：Beancount event 是记给人看的日记，HomeBus 事件日志是记给系统恢复用的操作记录。两条线完全独立，互不替代。

### 数据流入口

| 触发场景 | 事件类型 | 分发目标 |
|---------|---------|---------|
| 超市买牛奶 | `purchase` (consumable) | Grocy + Beancount |
| 京东买洗衣机 | `purchase` (durable) | Grocy + Beancount + Homebox |
| 发工资 | `income` | Beancount (only) |
| 出差报销 | `expense` | Beancount (only) |
| 二手卖出 | `sell` | Beancount + Homebox (移除资产) |
| 转账/还贷 | `transfer` | Beancount (only) |
| 退款 | `refund` | Beancount + Grocy (扣库存) |
| 赠予获得 | `income` (in-kind) | Beancount + (如果是耐用品) Homebox |

---

## 二、Grocy — 消耗品生命周期的操作入口

### 定位

消耗品的**唯一操作入口**。所有"消耗"相关的操作（入库、消耗、过期处理、盘点）在 Grocy 完成。Grocy 是消耗品和循环品库存的唯一权威数据源。

同时 Grocy 的家务（Chores）和购物清单（Shopping List）模块**作为家庭日常操作管理的补充**，纳入 HomeBus。

### 它管什么

| 领域 | 示例 | 说明 |
|------|------|------|
| **消耗品库存** | 食品、日化、药品、宠物食品 | 入库（购买时）→ 消耗 → 补充的完整生命周期 |
| **过期管理** | 牛奶过期、药品有效期 | Grocy 的过期提醒功能，HomeBus 观测面聚合"即将过期"的物品 |
| **循环品管理** | 电量计费、桶装水换水、猫砂更换 | **你问的"非消耗品也在这里吗"** → 先看下方"模糊地带分析" |
| **家务待办** | 扫地、倒垃圾、换电池 | Grocy 的 Chores 模块；Chore 本身不产生库存变动，但会记录执行时间 |
| **采购清单** | 本周需要买什么 | Grocy 的 Shopping List；由消耗触发补充，或手动添加 |
| **消耗记录** | 吃了什么、用了什么 | `consume` 事件 |
| **盘点** | 过期食品清理、库存校对 | `inventory` 事件（校准账面 vs 实际） |

### 它不管什么

- ❌ 记账（Beancount 管）
- ❌ 资产位置（Homebox 管）
- ❌ 卖出逻辑（卖出是 Homebox 的入口，但卖出收入记在 Beancount）
- ❌ 单次购物的详细价格（Beancount 管单价×数量，Grocy 只管数量）

### 关键约束

1. **Grocy 的"采购"是库存接收，不是财务采购** — `purchase` 事件在 Grocy 端的含义是"收到货、入库"。财务采购（花了多少钱）是 Beancount 的事。两件事通过同一个 `purchase` 事件触发，但语义不同。
2. **Grocy 管数量（+ 父产品聚合口径），不管金额** — Grocy 的 stock 系统以数量为核心。金额（单价×数量）在 Beancount，不在 Grocy。
3. **Grocy 的消耗记录不是财务损耗** — 消耗牛奶是物理行为，不是账目行为。Beancount 的 `Expenses:Groceries` 已经在购买时一次性扣除了。

### 关于循环品（你问的"非消耗品也在这里吗"）

循环品（batteries、chores、recurring items）的归属存在模糊地带。分析如下：

| 物品类型 | 典型例子 | 推荐归属 | 理由 |
|---------|---------|---------|------|
| **可消耗的循环品** | 电池、猫砂、桶装水 | ✅ **Grocy** | 本质上是消耗品——被用完了需要补充。Grocy 已有 stock 系统 |
| **不可消耗的循环事项** | 扫地、除草、换空调滤网 | ✅ **Grocy Chores** | Chores 的设计意图就是这类周期任务。不产生库存变动，但需要记录执行频次和提醒 |
| **电/水/燃气用量** | 月度电费 | ❌ **不要放在 Grocy** | 用量记录在 Beancount（utility tracking accounts），缴费是账单支付。Grocy 的用量跟踪（Batteries）是为有实物载体的场景设计的（如热水器用了多少度） |
| **桶装水换水** | 桶本身是资产（Homebox），水是消耗品（Grocy） | ✅ **分拆处理** | 桶（空桶）如果是可回收的 → Homebox 资产；水（液体）→ Grocy 消耗品。换水动作：消耗 Grocy 水 + 更新 Homebox 空桶状态 |

**结论**：Grocy 确实管理"消耗品"范围超出了传统食品/日化，包括可消耗的循环品和周期性家务。但**电水气用量这种"无实物载体的消耗"不应该进入 Grocy**——它们走 Beancount 跟踪账户。

### 数据流入口

| 触发场景 | 事件类型 | 其他分发 |
|---------|---------|---------|
| 购买消耗品 | `purchase` (consumable) | Grocy 入库 |
| 消耗物品 | `consume` | Grocy 减库存 (only) |
| 过期/丢弃 | `discard` | Grocy 减库存 + Beancount (记损耗，可选) |
| 盘点校正 | `inventory` | Grocy 重设库存 (only) |
| 完成家务 | `chore` | Grocy 记录 Chore 执行 (only) |
| 添加采购项 | `shopping-list-add` | Grocy 添加商品 (only) |
| 循环品补充 | `purchase` (consumable) | 同消耗品逻辑 |

---

## 三、Homebox — 耐用品资产的位置与状态管理

### 定位

耐用品的**资产目录与物理位置管理**。Homebox 记录"家里有什么东西、在哪个房间、现在什么状态"——这些信息 Beancount 和 Grocy 都不管。

同时，**卖出逻辑的入口在 Homebox**——当你要卖掉某个资产时，Homebus 发给 Homebox 的 `sell` 事件触发 Homebox 上的"标记为已售出"操作（对应 Homebox 的 `asset_status: sold`），然后向 Beancount 写二手收入。

### 它管什么

| 领域 | 示例 | 说明 |
|------|------|------|
| **资产登记** | 购入洗衣机、收到赠品音箱 | 入账到 Homebox：名称、位置、购入日期、购入价格（从 Beancount 同步）、照片 |
| **位置管理** | "洗衣机在阳台"、"充电器在客厅抽屉" | Homebox 的核心功能——多级位置组织、二维码扫码定位 |
| **状态管理** | 完好、需维修、已报废、已售出、出租中 | 生命周期状态 |
| **卖出入口** | 二手卖掉手机 | `sell` 事件触发 Homebox 标记已售 + Beancount 记收入 + Grocy 减库存（如果该物品也在 Grocy 中跟踪） |
| **报废/清理** | 扔掉坏了的电器 | `dispose` 事件触发 Homebox 标记报废 + Beancount 记资产处置损失 |
| **资产查询** | "我的蓝牙音箱在哪" | Homebox 的 QR 码或 HomeBus query |
| **维修保养记录** | 空调 2026-06 加氟 | 在 Homebox 的资产上附加事件记录 |

### 它不管什么

- ❌ 消耗品的库存（Grocy 管）
- ❌ 物品的价值变动/折旧（Beancount 可跟踪，Homebox 只记录购入价格）
- ❌ 采购下单（purchase 事件由 HomeBus 分发到 Grocy 入库，Homebox 只收 durable 的资产登记）
- ❌ 记账（Beancount 管收入/支出）

### 关键约束

1. **Homebox 是卖出的决策入口，Beancount 是卖出的记账出口** — 用户说"卖掉手机" → `sell` 事件 → Homebox 标记已售 + Beancount 写二手收入。不先经过 Beancount。
2. **Homebox 不关心采购金额的记账细节** — 它只存"购入价格"作为资产元数据。Beancount 的分录细节（支付方式、优惠券、分期）Homebox 不管。
3. **位置信息是 Homebox 的排他性数据** — Beancount 和 Grocy 都无位置字段。这是 Homebox 在整个链条中的唯一性价值。
4. **耐用品和消耗品的边界是模糊的** — 见下方"模糊地带分析"。

### 数据流入口

| 触发场景 | 事件类型 | 其他分发 |
|---------|---------|---------|
| 购买耐用品 | `purchase` (durable) | Grocy + Beancount + Homebox |
| 卖出资产 | `sell` | Homebox (标记已售) + Beancount (收入) |
| 报废资产 | `dispose` | Homebox (标记报废) + Beancount (处置损失) |
| 移动位置 | `transfer` | Homebox (only) |
| 赠予获得耐用品 | `income` (in-kind durable) | Homebox + Beancount |
| 租借/借出 | `lend` / `borrow` | Homebox (状态变更) + Beancount (押金/跟踪) |

---

## 四、模糊地带分析与判定规则

### 4.1 消耗品 vs 耐用品 —— 物品归属判断

| 判定标准 | 消耗品 (Grocy) | 耐用品 (Homebox) |
|---------|--------------|----------------|
| **使用后消失？** | 是。吃了/用了就没了 | 否。使用后仍然存在 |
| **是否需要位置追踪？** | 否。位置只是冰箱/柜子这种大分类 | 是。需要精确位置（哪个抽屉、哪个架子） |
| **是否需要折旧/卖出？** | 否。不能二次销售 | 可能会卖出、转赠、报废 |
| **是否独立管理生命周期？** | 批次/过期日期管理 | 维修/保养/状态记录 |
| **示例** | 牛奶、纸巾、洗发水、电池、猫砂 | 洗衣机、手机、沙发、装饰品、工具 |

**边界案例**：
- **桶装水**：桶本身（可回收资产）→ Homebox；里面的水 → Grocy
- **咖啡机**：机器本身 → Homebox；咖啡豆/胶囊 → Grocy
- **电动牙刷**：牙刷主体 → Homebox；刷头（消耗品）→ Grocy
- **书籍**：收藏级精装书 → Homebox（有卖出价值）；用完了的教辅 → Grocy（可处理）

**判定责任**：Agent 负责分类，用户确认或纠偏。HomeBus 不推测。

### 4.2 "非消耗品也在 Grocy 采购吗？"

回到你提的问题。非消耗品有两类：

**A. 可消耗的循环品（电池、桶装水）**
→ 在 Grocy 正常采购。它们在被"用完"时需要补充，符合 Grocy 的库存逻辑。

**B. 不可消耗的循环事项（家务、电量）**
→ 分为两种：
- 家务（扫地、除草） → Grocy Chores，不产生库存变动
- 电/水/气用量 → 不进入 Grocy。HomeBus 应通过 Beancount 的 commodity/unit tracking 记录用量（比如 `commodity kWh`），或预留 `utility` 事件类型在 v0.3+

**结论**：Grocy 是你家庭中"消耗品和循环品"的采购入口。但**非消耗品（洗衣机、手机）的采购不经过 Grocy——直接 Beancount 记账 + Homebox 资产登记**。

### 4.3 "卖出的入口是 Homebox 吗？"

**是的**。

流程：
1. 用户说"把那个手机卖掉"
2. Agent 解析为 `sell` 事件，**先向 Homebox 查询该资产信息**（名称、位置、购入价）
3. HomeBus 分发：
   - Homebox：标记该资产为 `sold`
   - Beancount：写入二手收入到 `Income:Sales`
   - Grocy：如果该物品同时在 Grocy 中有库存跟踪，同步扣减
4. Agent 将 Homebox 返回的信息整合给用户确认

为什么入口是 Homebox 不是 Beancount？因为卖出是一个**物理资产操作**优先——卖的是什么、在哪、买家是谁、怎么交接，这些信息由 Homebox 管理。Beancount 只管"收到了多少钱"。

---

## 五、事件类型与后端映射总表

| 事件类型 | 触发场景 | Grocy | Beancount | Homebox | MVP? |
|---------|---------|-------|----------|---------|------|
| `purchase` (consumable) | 买消耗品 | 入库 ✅ | 记支出 ✅ | — | ✅ |
| `purchase` (durable) | 买耐用品 | 入库 ✅ | 记支出 ✅ | 登记资产 ✅ | ✅ |
| `consume` | 使用消耗品 | 减库存 ✅ | — | — | ✅ |
| `income` (cash) | 工资/红包 | — | 记收入 ✅ | — | ❌ v0.2+ |
| `income` (in-kind consumable) | 收到赠予消耗品 | 入库 ✅ | 记收入 ✅ | — | ❌ v0.2+ |
| `income` (in-kind durable) | 收到赠予耐用品 | — | 记收入 ✅ | 登记资产 ✅ | ❌ v0.2+ |
| `expense` | 出差/报销/单次支出 | — | 记支出 ✅ | — | ❌ v0.2+ |
| `sell` | 二手卖出 | 扣库存（如有） | 记收入 ✅ | 标记已售 ✅ | ❌ v0.2+ |
| `dispose` | 报废资产 | 扣库存（如有） | 记损失 ✅ | 标记已报废 ✅ | ❌ v0.2+ |
| `discard` | 丢弃消耗品 | 减库存 ✅ | — | — | ❌ v0.2+ |
| `transfer` (fund) | 转账/还贷 | — | 记账 ✅ | — | ❌ v0.3+ |
| `transfer` (asset) | 移动资产位置 | — | — | 更新位置 ✅ | ❌ v0.3+ |
| `chore` | 完成家务 | 记录 Chore ✅ | — | — | ❌ v0.3+ |
| `inventory` | 盘点校正 | 重设库存 ✅ | — | — | ❌ v0.3+ |
| `refund` | 退货退款 | 扣库存 ✅ | 记冲销 ✅ | 删除资产（如有） | ❌ v0.3+ |
| `utility` | 水电燃气用量 | — | 记录用量 ✅ | — | ❌ v0.3+ |

---

## 六、对现有文档的更新指引

基于以上分析，以下文档需要更新：

1. **doc/c4/context.md** — 系统关系表中的描述更新为本文的精确定位
2. **doc/specs/event-types.md** — 新增 `income`、`expense`、`sell`、`dispose`、`discard` 的事件模型设计（v0.2+）
3. **doc/glossary.md** — "消耗品"和"资产"的定义扩展，补充"循环品"术语
4. **AGENTS.md** — 核心架构约束第 5/6/7 条扩展为本文的前后文描述
5. **doc/specs/homebus.md** — 功能性需求补充非购买事件的预留接口说明

---

## 附录：与 HomeBus 核心原则的关系

| HomeBus 原则 | 在后端定位中的体现 |
|-------------|------------------|
| 单一写入入口 | 所有事件类型统一走 HomeBus 分发；Agent 不直连任何后端 |
| 不可变事件日志 | 所有分发记录不可变存储，包括非购买场景（income/expense/sell） |
| Saga 补偿 | sell 事件中 Homebox 标记已售成功但 Beancount 收入写入失败 → 自动回滚 Homebox 状态 |
| 幂等重试 | 重复的 consume 事件 → HomeBus 去重，不会双倍减库存 |
| CQRS 分离 | 查询路径（"手机在哪"→ Homebox query）和写路径（sell 事件）分离 |
