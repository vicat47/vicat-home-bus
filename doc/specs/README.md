# Specs (规格说明)

本目录包含 HomeBus 的模块/功能级技术规格说明。

## 目录结构

```
specs/
├── homebus.md              # HomeBus 核心架构规格
├── event-types.md          # 事件类型定义与推导规则
├── routing-registry.md     # 路由注册表
├── config-paradigm.md      # 配置范式
├── backend-boundaries.md   # 后端边界规范
├── sensitive-data.md       # 敏感数据处理规范
├── beancount-integration.md # Beancount 集成方案
├── database-schema.md       # 数据库 Schema
├── adapter-interfaces.md    # Adapter 接口规范
├── api-contracts.md         # API 契约
├── cli-spec.md              # CLI 规范
└── README.md               # 本文件
```

## 快速导航

| 文档 | 标题 | 状态 | 日期 |
|------|------|------|------|
| [homebus.md](homebus.md) | HomeBus 家庭服务总线规格说明 | draft | 2026-07-20 |
| [event-types.md](event-types.md) | 事件类型定义与推导规则 | approved | 2026-07-20 |
| [routing-registry.md](routing-registry.md) | 路由注册表 | draft | 2026-07-20 |
| [config-paradigm.md](config-paradigm.md) | 配置范式 | draft | 2026-07-20 |
| [backend-boundaries.md](backend-boundaries.md) | 后端边界规范 | draft | 2026-07-20 |
| [sensitive-data.md](sensitive-data.md) | 敏感数据处理规范 | draft | 2026-07-21 |
| [beancount-integration.md](beancount-integration.md) | Beancount 集成方案 | draft | 2026-07-23 |
| [database-schema.md](database-schema.md) | 数据库 Schema | draft | 2026-07-23 |
| [adapter-interfaces.md](adapter-interfaces.md) | Adapter 接口规范 | draft | 2026-07-23 |
| [api-contracts.md](api-contracts.md) | API 契约 | draft | 2026-07-23 |
| [cli-spec.md](cli-spec.md) | CLI 规范 | draft | 2026-07-23 |

## 如何创建新规格

1. 确定模块/功能名称（kebab-case）
2. 按模板结构创建 `specs/<module-name>.md`
3. 更新本文件的导航表
4. 更新 `doc/README.md` 的文档计数

## 状态生命周期

- `draft` → `in-review` → `approved`
