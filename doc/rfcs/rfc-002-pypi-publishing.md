---
status: approved
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["rfc", "homebus", "pypi", "publishing"]
type: rfc
related:
  adr: ""
  c4: "../c4/component-cli.md"
  research: ""
  radar: ""
---

# RFC-002: CLI 通过 PyPI 发布供 Agent 使用

## Summary

HomeBus CLI 作为独立包发布到 PyPI，Agent 通过 `pipx install homebus` 安装后直接调用。API Server 作为可选 extra 分离发布。

## Motivation

Agent 在每次启动时运行在隔离的 shell 环境中，不能依赖本地源码路径。CLI 必须是一个可独立安装、全局可用的命令行工具，才能被 Agent 的 terminal tool 可靠调用。PyPI 发布是满足这一需求最直接的方式：

1. **零路径依赖** — `pipx install homebus` 后 `homebus` 命令全局可用，Agent 直接调用
2. **版本化管理** — `pipx upgrade homebus` 升级，不用拉源码配路径
3. **与 MCP 路线衔接** — v0.1 CLI via pipx/pip → v0.2 MCP Server 作为 optional extra 同一包发布，底层代码复用

## Proposed Changes

### pyproject.toml 发布配置

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "homebus-cli"
version = "0.1.0"
description = "HomeBus — Family Service Bus CLI for Agent interactions"
requires-python = ">=3.11"
dependencies = [
    "click>=8.4",
    "httpx>=0.28",
    "pydantic>=2.13",
    "pyyaml>=6.0",       # Grocy adapter 解析 Grocy API 返回
]
optional-dependencies.server = [
    "fastapi>=0.139",
    "uvicorn>=0.51",
    "aiosqlite>=0.22",
]

[project.scripts]
homebus = "cli.homebus:main"

[project.urls]
Homepage = "https://github.com/vicat47/vicat-home-bus"
```

**关键点**:
- 包名 `homebus-cli`，CLI 命令名 `homebus`
- `server` extra 安装 API Server 组件（FastAPI + uvicorn + aiosqlite）
- PyYAML 保留为硬依赖（Grocy adapter 解析 Grocy API 的 cache.yaml），不作为配置格式使用

### Agent 调用方式

```bash
# 安装
pipx install homebus-cli

# 提交购买事件
homebus publish --intent purchase --items '[{"name":"牛奶","quantity":3,"category":"consumable"}]' --total-price 60

# 查询事件状态
homebus status --event-id <event-id>

# 查询后端状态
homebus query --target grocy --operation stock_level --params '{"item":"牛奶"}'

# 健康检查
homebus health
```

### Impact

- **Scope**: pyproject.toml 发布元数据、CLI 入口实现、README 安装说明
- **Breaking Changes**: 无（全新组件）
- **Migration Required**: 无

## Alternatives Considered

### Alternative 1: 不发布，依赖源码路径

**Cons:**
- Agent 每次需要 `cd /path/to/homebus && pip install -e .`
- 多机器/容器环境不可行
- 与 Agent 的"无状态执行"原则冲突

### Alternative 2: Docker 镜像

**Pros:**
- 环境完全隔离
- 配置可通过卷注入

**Cons:**
- Agent 调用 CLI 的开销增大（docker run 每次启动容器）
- CLI 本身是轻量操作，Docker 太重
- 适合 API Server 部署，不适合 Agent CLI 调用

## Implementation Plan

- [x] 决策：PyPI 发布
- [ ] 完善 `pyproject.toml` 发布元数据
- [ ] 创建 CLI 命令框架
- [ ] 添加 `README.md` 安装说明
- [ ] 发布 v0.1.0a1 测试包

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 包名 `homebus-cli` 已被占用 | 高 | 中 | 检查 PyPI，准备备选名 `vicat-homebus-cli` |
| 用户忘记安装/升级 | 中 | 中 | Agent 启动时检查版本，提示安装命令 |
| 敏感信息通过 CLI 参数泄露 | 高 | 低 | API Key 通过环境变量传递，不进入命令行历史 |

## Rollback Plan

从 PyPI 撤销版本，退回 pip install -e . 本地安装。

## References

- [pipx 文档](https://pipx.pypa.io/)
- [Python Packaging User Guide](https://packaging.python.org/)
