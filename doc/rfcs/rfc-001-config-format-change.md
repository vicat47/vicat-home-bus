# RFC-001: 配置格式从 YAML 变更为 TOML

- **Status**: Approved
- **Date**: 2026-07-20
- **Author**: vicat47
- **Related Documents**:
  - [配置存储范式规格](../specs/config-paradigm.md) (v0.1.0 → v0.2.0)
  - [C4 CLI 组件](../c4/component-cli.md)
  - [MVP PRD](../../doc/prd/homebus-v0.1.md)
  - [PyPI 发布策略讨论](rfc-002-pypi-publishing.md)

## Summary

将 HomeBus 配置文件的格式从 YAML 变更为 TOML，同时确认 CLI 将通过 PyPI 发布供 Agent 通过 pipx 安装使用。

## Motivation

### 配置格式变更

最初的配置规格选择了 YAML，理由是其生态通用性和 PyYAML 已在依赖中。但经过实施前评估，两个关键因素促成了变更：

1. **Python 3.11 标准库已原生支持 TOML** — `tomllib` 是 Python 3.11+ 的内置模块，HomeBus 目标 Python 版本正是 3.11，无需任何外部依赖即可解析配置。PyYAML 保留在依赖中是因为 Grocy Adapter 需要解析 Grocy API 返回的 YAML 格式缓存，不应作为配置格式的依赖因素。

2. **Agent 写入可靠性** — TOML 语法确定性高，没有 YAML 的多行缩进歧义、制表符问题、引号推断陷阱。Agent 通过 `tomllib` 写入配置时，可以生成确定性输出，减少解析错误。

3. **项目理念一致** — `pyproject.toml` 已是项目元数据的标准格式，用户只接触一种配置语法，降低认知负担。

### PyPI 发布

CLI 通过 PyPI 发布是 Agent 工具链的自然要求：Agent 在隔离环境中运行，不能依赖源码路径。`pipx install homebus` 后，CLI 作为系统级命令可用，Agent 通过终端工具直接调用。

## Proposed Changes

### 变更 1：配置格式 YAML → TOML

| 项目 | 旧值 | 新值 |
|------|------|------|
| 配置文件扩展名 | `config.yaml` | `config.toml` |
| 默认配置文件名 | `defaults.yaml` | `defaults.toml` |
| 示例文件名 | `config.yaml.example` | `config.toml.example` |
| 解析库 | PyYAML (`yaml.safe_load`) | `tomllib` (stdlib, 零依赖) |
| 配置加载代码 | `yaml.safe_load(f)` | `tomllib.load(f)` |
| 版本号 | v0.1.0 | v0.2.0 |

**不变项**:
- 目录结构（`$XDG_CONFIG_HOME/homebus/`）
- 分层加载顺序（默认值 < 配置文件 < 环境变量 < CLI 参数）
- 环境变量映射（所有变量名不变）
- 敏感信息分离策略

### 变更 2：PyPI 发布配置

在 `pyproject.toml` 中补充发布元数据：

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "homebus-cli"
...
```

CLI 作为独立入口点发布，API Server 是可选 extra。

### Impact

- **Scope**: 配置加载模块 (`homebus/config.py`)、文档、示例文件
- **Breaking Changes**: 是 — 已有 `config.yaml` 的用户需要迁移到 `config.toml`
- **Migration Required**: 是 — 提供迁移脚本或手动转换指南

## Alternatives Considered

### Alternative 1: 保持 YAML

**Pros:**
- 无需修改已有文档和代码
- Docker Compose / GitHub Actions 等生态仍用 YAML，配置格式对齐

**Cons:**
- 依赖 PyYAML（非标准库）
- Agent 写入时 YAML 缩进问题可能导致解析失败
- 与 `pyproject.toml` 格式不统一

### Alternative 2: 纯环境变量，无配置文件

**Pros:**
- 零配置加载开销
- 12-Factor 最严格实现

**Cons:**
- 开发环境每次输入冗长的环境变量
- Agent 调用时需要注入大量环境变量，CLI 调用链复杂化
- 无本地持久化，不适配 MVP 的本地运行模式

### Alternative 3: JSON 配置

**Pros:**
- 标准库支持，无注释问题
- Agent 生成 JSON 可靠

**Cons:**
- 无注释支持，无法在配置文件中写说明
- 可读性差（无逗号拖尾宽容，无多行友好）
- JSON 适合机器间通信，不适合人写配置

## Implementation Plan

本 RFC 与 RFC-002 (PyPI 发布) 同时实施，共享 code changes。

- [x] 决策：配置格式 TOML，CLI 发 PyPI
- [x] 更新配置规格文档 (`doc/specs/config-paradigm.md`)
- [x] 创建配置示例文件 (`config.toml.example`)
- [ ] 实现 `homebus/config.py` — TOML 配置加载器
- [ ] 创建 `homebus/defaults.toml` — 默认配置
- [ ] 更新 `.gitignore` — 排除 `config.toml` / `.env`
- [ ] 补充 `pyproject.toml` — PyPI 发布元数据
- [ ] 提交并推送

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 用户已有 `config.yaml` 需要迁移 | 中 | 低 (MVP 阶段用户数 ≈ 1) | 提供手动迁移指南 |
| `tomllib` 不支持日期时间以外的复杂类型 | 低 | 低 | 配置仅含字符串/整数/布尔，TOML 完全覆盖 |
| Agent 生成 TOML 不标准 | 中 | 低 | 提供 `tomllib.dumps` 序列化工具函数 |

## Rollback Plan

退回 YAML：还原 config-paradigm.md、config.py 改用 `yaml.safe_load`，版本号回退 v0.1.0。

## References

- [TOML 规范 v1.0.0](https://toml.io/en/v1.0.0)
- [Python tomllib 文档](https://docs.python.org/3/library/tomllib.html)
- [12-Factor App — Config](https://12factor.net/config)
