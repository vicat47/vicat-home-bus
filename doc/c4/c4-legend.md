---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["c4", "homebus", "legend"]
related:
  context: "doc/c4/context.md"
  container: "doc/c4/container.md"
---

# C4 图例说明

> C4 标记法的图例说明，用于理解所有 C4 文档中的符号。

## 元素类型

### 人员 (Person)

```
┌──────────────┐
│  角色名称     │
│  角色描述     │
│  [Person]     │
└──────────────┘
```

表示系统的使用者/外部角色，如家庭成员、AI Agent、系统管理员。

### 软件系统 (Software System)

```
┌──────────────────┐
│  系统名称          │
│  系统描述          │
│  [Software System]│
└──────────────────┘
```

表示外部与之交互的其他系统，如 Grocy、Beancount、Homebox。

### 容器 (Container)

```
┌──────────────────────┐
│  容器名称              │
│  容器描述 / 技术       │
│  [Container]          │
└──────────────────────┘
```

表示可独立部署的进程/服务边界，如 HomeBus API Server、HomeBus CLI。

### 组件 (Component)

```
┌────────────────┐
│  组件名称        │
│  组件职责        │
│  [Component]    │
└────────────────┘
```

表示容器内部的逻辑模块/类，如事件校验器、调度引擎、Saga 补偿器。

---

## 关系箭头

```
─────→    同步调用 (HTTP / Python 方法调用)
~~~~~→    异步调用 (消息/事件驱动)
─────    数据读取 (读数据库)
═════→    数据写入 (写数据库)
- - -→    未来 / 可选的调用路径
```

---

## 颜色方案

| 颜色 | 用途 | 示例 |
|------|------|------|
| **蓝色** | HomeBus 自有系统/容器/组件 | HomeBus API Server |
| **绿色** | 外部软件系统 | Grocy, Beancount, Homebox |
| **橙色** | 人员角色 | 家庭成员, AI Agent |
| **灰色** | 未来/规划中的系统 | HomeBus MCP Server (v0.2) |

---

## 元素标识

所有 C4 文档中的元素使用以下唯一标识符规则：

| 前缀 | 类型 | 示例 |
|------|------|------|
| `P-` | Person | `P-Agent` (AI Agent) |
| `S-` | Software System | `S-Grocy`, `S-Beancount` |
| `C-` | Container | `C-API` (HomeBus API Server) |
| `Cp-` | Component | `Cp-Validator` (Event Validator) |

---

## C4 模型术语表

| 术语 | 定义 |
|------|------|
| **Context (L1)** | 系统上下文，展示系统与外部角色/系统的关系 |
| **Container (L2)** | 容器视图，展示系统内部的技术边界（进程/服务） |
| **Component (L3)** | 组件视图，展示容器内部的结构化模块 |
| **Code (L4)** | 代码视图，展示组件内部的类/接口关系（本系统暂不涉及） |
