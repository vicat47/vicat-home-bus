# Release 状态机参考

## 完整状态转换图

```
                         ┌──────────┐
                         │  draft   │  ← 规划中：功能清单未定
                         └────┬─────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐  ┌──────────┐    ┌───────────┐
        │ proposed │  │  draft   │    │ cancelled │  ← 放弃
        └────┬─────┘  └──────────┘    └───────────┘
             │         (返回修改)
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌──────────┐ ┌──────────┐ ┌───────────┐
│in-progress│ │ proposed │ │ cancelled │  ← 确认不通过
└────┬─────┘ └──────────┘ └───────────┘
     │        (重新确认)
     │
     ├───→ 功能清单中 `planned → in-progress → done`
     │     (持续更新，状态保持 in-progress)
     │
     ▼
┌──────────┐
│ in-review│  ← 功能冻结，切 RC
└────┬─────┘
     │
      ├───→ 创建 RC 文件，`status: in-review`
      │     原 SNAPSHOT 文件 `status` 改为 `superseded`
     │
┌────┼────┐
▼    ▼    ▼
┌──────────┐ ┌──────────┐ ┌───────────┐
│ released │ │in-progress│ │ cancelled │
└────┬─────┘ └──────────┘ └───────────┘
     │       (问题太多，打回)
     │
     ├───→ 创建 GA 文件，`status: released`
     │     原 RC 文件改为 `status: superseded`
     │
     ▼
┌────────────┐
│ superseded │  ← 更新版本发布
└────┬───────┘
     ▼
┌──────────┐
│ archived │  ← 版本不再维护
└──────────┘
```

## 状态定义

| 状态 | 含义 | 对应阶段 | 谁触发的 |
|------|------|---------|---------|
| `draft` | 规划中 | 开发前 | 你在脑暴「下个版本放什么」，功能清单可随意改 |
| `proposed` | 已提议 | 开发前 | 功能清单写完了，自己 check 一遍确认 |
| `in-progress` | 开发中 | 开发中 | 确认通过，开始写代码，功能逐个 `done` |
| `in-review` | 验证中 | RC | 功能冻结，跑测试/验证，打勾检查清单 |
| `released` | 已发布 | GA | 正式交付，触发 CHANGELOG |
| `cancelled` | 已取消 | 任意时刻 | 版本放弃，记录原因 |
| `superseded` | 被取代 | 发布后 | 新版本覆盖，保留历史 |
| `archived` | 已归档 | 发布后 | 不再维护 |

## 状态转换规则

| 从 | 到 | 触发条件 |
|----|-----|---------|
| `draft` | `proposed` | 功能清单定稿，自行确认 |
| `draft` | `cancelled` | 放弃该版本计划 |
| `proposed` | `in-progress` | 确认通过，开始开发 |
| `proposed` | `draft` | 需要修改计划 |
| `proposed` | `cancelled` | 功能评估后放弃 |
| `in-progress` | `in-review` | 功能冻结，切 RC |
| `in-progress` | `cancelled` | 开发中放弃 |
| `in-review` | `released` | RC 验证通过，发布 GA |
| `in-review` | `in-progress` | RC 阻塞，打回继续开发 |
| `in-review` | `cancelled` | RC 阶段放弃 |
| `released` | `superseded` | 被下一个版本取代 |
| `released` | `archived` | 不再维护 |

## 与统一前言的映射

| record-release `status` | 映射到 Base |
|--------------------------|------------|
| `draft` | draft |
| `proposed` | in-review |
| `in-progress` | in-progress |
| `in-review` | in-review |
| `released` | complete |
| `superseded` | superseded |
| `archived` | archived |
| `cancelled` | cancelled |
