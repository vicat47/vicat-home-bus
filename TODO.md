# HomeBus TODO — 待决策项

> 状态标记: 🔴 阻塞级 · 🟡 重要 · 🟢 优化
> 更新: 2026-07-20
> 已决策: 事件类型模型 ✅ · 规则表 ✅ · 位置归类策略 ✅

---

## ✅ 已决策 — 事件类型与子任务推导规则表

**决策日期**: 2026-07-20

### MVP 事件类型

| 事件类型 | 描述 | 涉及后端 |
|---------|------|---------|
| `purchase` | 购买物品（京东/超市等） | Grocy(+库存) + Beancount(记账) + Homebox(仅 durable) |
| `consume` | 消耗/使用物品 | Grocy(-库存) |

> MVP 仅此两种。`discard` / `transfer` 后续加。

### 字段模型

```python
# purchase event
{
    "intent": "purchase",
    "items": [
        {
            "name": str,              # 物品名称
            "category": str,          # "consumable" | "durable"
            "quantity": float,        # 数量
            "unit": str,              # 单位 (盒/个/瓶)
            "price": float,           # 单价
            "grocy_product_id": str | None,  # 可选，指定 Grocy 产品 ID
            # 扩展预留：homebox_location_id, beancount_account
        }
    ],
    "total_price": float,            # 总价
    "store": str | None,             # 购买渠道
    "purchased_at": datetime | None, # 购买时间
    "note": str | None,              # 备注
    # 扩展预留：actor (家庭成员), tags, reference
}

# consume event
{
    "intent": "consume",
    "items": [
        {
            "name": str,
            "quantity": float,
            "unit": str,
            "grocy_product_id": str | None,
        }
    ],
    "consumed_at": datetime | None,
    "note": str | None,
    # 扩展预留：actor, tags
}
```

### 子任务推导规则

**purchase** (串行 → 并行):

```
① Grocy 加库存 (所有 items)        ← 必须先成功
    ↓ 成功
② ╠═ Beancount 记支出 (所有 items)  ← 并行
   ╚═ Homebox 创建资产 (仅 durable)  ← 并行
```

- Grocy 失败 → 不执行任何子任务，事件标记失败（无需补偿）
- Beancount / Homebox 失败 → 自动补偿（回滚 Grocy 库存变动）
- Homebox 位置归类：Agent 通过 query 接口获取位置列表后推断，在 publish 时不传入，Agent 在 purchase 成功后二次调用 Homebox 的资产创建接口（或通过另一个事件）补全位置

**consume** (单项):

```
① Grocy 减库存                    ← 单项，无依赖
```

- 失败 → 事件标记失败，无需补偿

### 位置归类策略

HomeBus 不负责智能归类。位置归类是 **Agent 层责任**：

1. Agent 通过 `homebus query homebox/locations` 获取可用位置列表 + 用户历史偏好
2. Agent 结合用户输入上下文、查询历史、物品名称推断位置
3. Agent 在 publish 事件中携带位置字段（或 publish 成功后通过补全事件指定）
4. 用户默认确认 Agent 推断，用户说"不对"再由 Agent 重新查询并更新

---

## 🟡 Beancount 接入方式

Beancount 的写入路径。Fava（目前 PRD 推荐的接入方式）是只读的。

**需要确定**：

- [ ] 写入方式：直接追加 `.bean` 文件？通过 `bean-extract` 管道？其他方式？
- [ ] 读取方式：Fava API 只读查询？还是也解析 `.bean` 文件？
- [ ] 文件路径如何传递给 HomeBus（配置项 `adapters.beancount.bean_file`）

**影响**: `homebus/adapters/beancount.py` 实现方案

---

## 🟡 Saga 补偿的不可逆边界

补偿操作自身可能失败（如删除一个已不存在的物品），需要定义边界。

**需要确定**：

- [ ] 哪些操作类型可安全补偿（幂等、可逆）
- [ ] 哪些操作类型不可撤销（仅记录日志 + 告警人工介入）
- [ ] 补偿失败后的重试策略（重试次数？人工介入条件？）
- [ ] 补偿触发方式（自动执行 / 确认后执行）

**影响**: `homebus/saga.py` 实现方案

---

## 🟡 CLI JSON 参数传递

嵌套 JSON 在 shell 命令行的引号处理易出错。

**需要确定**：

- [ ] 方案 A: 标准 `--body '{"key": "val"}'`（Agent 可控引号）
- [ ] 方案 B: `--body-file <json-path>` 从文件读取
- [ ] 方案 C: 从 stdin 读取 JSON
- [ ] 方案 D: 混合支持（优先 `--body`，后备 `--body-file`）

**参考**: PRD v0.1 US-3 的 Open Questions #3

---

## 🟡 PyPI 包名确认

`homebus-cli` 在 PyPI 上是否可用。

**需要确定**：

- [ ] 检查 `homebus-cli` 在 PyPI 是否已被占用
- [ ] 备选名（如 `vicat-homebus` / `homebus-toolkit`）
- [ ] 确定发布作用域：只发 CLI，还是 API Server 也作为 extra 发布

**参考**: RFC-002

---

## 🟢 版本号策略

PyPI 发布用版本号规则。

**需要确定**：

- [ ] 预发布标记：`0.1.0a1` / `0.1.0rc1`？
- [ ] 版本间依赖关系（CLI v0.1.0 是否必须对应 Server v0.1.0？）

---

## 🟢 测试策略

MVP 测试方案。

**需要确定**：

- [ ] 单元测试框架：pytest
- [ ] Adapter 测试：mock 还是 real API？
- [ ] 端到端测试：启动 HomeBus → 调用 CLI → 验证后端？
- [ ] CI/CD：GitHub Actions ？发布流水线？
