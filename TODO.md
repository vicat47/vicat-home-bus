# HomeBus TODO — 待决策项

> 状态标记: 🔴 阻塞级 · 🟡 重要 · 🟢 优化
> 更新: 2026-07-22
> 已决策: 事件类型模型 ✅ · 规则表 ✅ · 位置归类策略 ✅ · Routing Registry ✅ (→ [doc/specs/](doc/specs/))

---

## 🟡 Beancount 接入方式

Beancount 的写入路径。

**已决策** (→ [doc/specs/beancount-integration.md](doc/specs/beancount-integration.md))：

- [x] 写入方式：CLI 命令 `homebus beancount write`，生成 `.bean` 分录文本
- [x] 文件隔离：HomeBus 写入 `{ledger}/{YYYY}/homebus-{MM}.bean`，不碰用户手写文件
- [x] Git 同步：写入后自动 `git add` + `git commit`
- [x] 幂等：扫描已有 `event:` meta 字段去重
- [x] 校验：写入后 `bean-check`，失败回滚

---

## 🟡 Saga 补偿的不可逆边界

补偿操作自身可能失败（如删除一个已不存在的物品），需要定义边界。

**需要确定**：

- [ ] 哪些操作类型可安全补偿（幂等、可逆）
- [ ] 哪些操作类型不可撤销（仅记录日志 + 告警人工介入）
- [ ] 补偿失败后的重试策略（重试次数？人工介入条件？）
- [ ] 补偿触发方式（自动执行 / 确认后执行）

**影响**: `homebus/saga.py` 实现方案

- [x] 补偿策略：删除 Beancount entry 行 + 新 git commit（非 git revert）。见 [beancount-integration.md](doc/specs/beancount-integration.md) FR-10

### 🟡 Saga 回滚时的 git 冲突处理

当多个事件先后写入同一 `homebus-{MM}.bean` 后，Saga 回滚早期事件的 commit 时，可能与后续 commit 产生行级冲突。

**需要确定**：

- [ ] 每个 Beancount entry 是否独立 git commit？（推荐：是，减小冲突面）
- [ ] git commit 冲突时降级策略：标记告警日志？放弃自动回滚改为人工介入？
- [ ] 是否在 entry 之间保留空行/分隔注释以降低相邻行的冲突概率？

**参考**: [beancount-integration.md](doc/specs/beancount-integration.md) FR-10

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

---

## 🟡 doc-drift-hook plugin 触发 gap

`.opencode/plugins/doc-drift-hook.ts` 存在两个 gap：

- [ ] **git commit 钩子空转**：`tool.execute.before` 检测到 git commit 后只打 log，未调用 `client.session.promptAsync` 触发 drift check（与 `session.idle` 里的逻辑脱节）
- [ ] **缺少文档写入事件监听**：当前只监听 `session.idle`（每 5 次空闲触发），缺少 `file.write` / `file.edit` 事件钩子。文档变更后无法立即感知，只能等 periodic 检查
