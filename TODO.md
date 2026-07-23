# HomeBus TODO — 待决策项

> 状态标记: 🔴 阻塞级 · 🟡 重要 · 🟢 优化
> 更新: 2026-07-23
> 已决策 (P0+P1+P2): 数据库Schema ✅ · 事件状态机 ✅ · SubTask模型 ✅ · Adapter Action ✅ · API契约 ✅ · CLI规范 ✅ · 幂等路径 ✅ · async集成 ✅ · Saga补偿推导 ✅ · 配置模型 ✅ · Beancount元数据 ✅ · 混合品类 ✅ · 补偿语义 ✅ · Grocy fail-fast ✅ · Homebox 幂等删除 ✅ (→ [doc/specs/](doc/specs/))

---

## 🟡 Saga 补偿的不可逆边界

补偿操作自身可能失败，需要定义边界。

**需要确定**：

- [ ] 补偿失败后的重试策略（重试次数？人工介入条件？）
- [ ] 补偿触发方式（自动执行 / 确认后执行）

**已决策**:

- [x] 补偿策略：删除 Beancount entry 行 + 新 git commit（非 git revert）。见 [beancount-integration.md](doc/specs/beancount-integration.md) FR-10
- [x] Homebox delete_asset 幂等：404=视为成功（目标已达成）。见 [adapter-interfaces.md](doc/specs/adapter-interfaces.md)
- [x] Grocy 补偿只还原量变不删除产品。见 [adapter-interfaces.md](doc/specs/adapter-interfaces.md)
- [x] Saga 补偿推导算法：COMPENSATION_MAP + lambda。见 [adapter-interfaces.md](doc/specs/adapter-interfaces.md)

---

## 🟡 Saga 回滚时的 git 冲突处理

当多个事件先后写入同一 `homebus-{MM}.bean` 后，Saga 回滚早期事件时可能产生行级冲突。

- [ ] 每个 Beancount entry 是否独立 git commit？（推荐：是）
- [ ] git commit 冲突时降级策略：标记告警日志？放弃自动回滚改为人工介入？
- [ ] 是否在 entry 之间保留空行/分隔注释以降低相邻行的冲突概率？

**参考**: [beancount-integration.md](doc/specs/beancount-integration.md) FR-10

---

## 🟡 支付方式 vs 购买渠道解耦

现有 routing registry 的 `store` 维度隐含了"一个商店=一个负债账户"，但账本中支付方式和商店是解耦的：

| 概念 | 示例 | 现状 |
|------|------|------|
| 在哪买的（store）| "京东"、"美团" | 映射到负债账户 |
| 怎么付的（payment）| `WeChatPay`、`CMB`、`MeituanEnterprise` | 未建模 |

- [ ] `store` 保留为信息标注，新增 `payment_method` 字段
- [ ] routing registry 渠道路由：`payment_method` 用于 Beancount 负债账户映射

**影响**: `event-types.md`、`routing-registry.md`

---

## 🟢 PyPI 包名确认

- [ ] 检查 `homebus-cli` 在 PyPI 是否已被占用
- [ ] 备选名（`vicat-homebus` / `homebus-toolkit`）

**参考**: RFC-002

---

## 🟢 版本号策略

- [ ] 预发布标记：`0.1.0a1` / `0.1.0rc1`？
- [ ] CLI v0.1.0 与 Server v0.1.0 版本耦合关系？

---

## 🟢 测试策略

- [ ] Adapter 测试：mock 还是 real API？
- [ ] 端到端测试：启动 HomeBus → CLI → 验证后端
- [ ] CI/CD：GitHub Actions？发布流水线？

---

## 🟡 doc-drift-hook plugin 触发 gap

`.opencode/plugins/doc-drift-hook.ts` 两个 gap：

- [ ] git commit 钩子只打 log，未调 `promptAsync` 触发 drift check
- [ ] 缺少 `file.write`/`file.edit` 事件监听

---

## 🟢 Beancount 集成 spec 剩余 gap（低优先级）

- [ ] G-6: 文件初始化行为（首次创建 `homebus-MM.bean` 的目录/文件头）
- [ ] G-7: 文件锁细节（`asyncio.Lock` 已决策，需写死细节）
- [ ] G-8: bean-check 超时行为（超时=回滚，需写死）
- [ ] G-9: UTF-8 编码约束（显式声明）
- [ ] G-10: routing-registry dispatch 伪代码补 Homebox 建模
- [ ] G-11: `Liabilities:Unknown` 兜底账户初始化要求
- [ ] G-13: `homebus.md` ✅ 已标记 Superseded
- [ ] PRD 模块清单补 `beancount_writer.py` + `registry.py` ✅
