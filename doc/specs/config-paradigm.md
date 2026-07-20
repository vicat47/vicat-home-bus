---
status: draft
created: 2026-07-20
updated: 2026-07-20
author: "vicat47"
tags: ["spec", "homebus", "configuration", "adapter"]
type: spec
related:
  prd: "doc/prd/homebus-v0.1.md"
  c4-core: "doc/c4/component-core.md"
  c4-cli: "doc/c4/component-cli.md"
---

# HomeBus 配置文件存储范式 — Specification

- **Version**: 0.1.0
- **Date**: 2026-07-20
- **Author**: vicat47
- **Status**: Draft

## Overview

定义 HomeBus 项目（API Server + CLI + Adapters）的配置加载分层、文件格式、目录规范、敏感信息处理、以及配置发现机制。

### 适用范围

| 消费方 | 说明 |
|--------|------|
| HomeBus API Server | FastAPI 启动时读取后端地址、数据库路径等 |
| HomeBus CLI | Click 命令需要知道 API Server 地址 |
| Grocy Adapter | API 地址 + API Key |
| Beancount Adapter | API 地址（fava）或文件路径 |
| Homebox Adapter | API 地址 + Token |

## 设计原则

| 原则 | 说明 |
|------|------|
| **12-Factor App** | 配置通过环境变量注入，配置文件是开发环境便利 |
| **分层加载** | 默认值 < 配置文件 < 环境变量 < CLI 参数（从左到右优先级递增） |
| **XDG 规范** | 配置文件目录遵循 `$XDG_CONFIG_HOME/homebus/` |
| **敏感信息分离** | API Key / Token 通过环境变量注入，不进入配置文件提交到 git |
| **单文件多节** | 一个 YAML 文件 + 多节（sections），不拆成多个文件 |

## 配置文件格式

**格式选择**: YAML

| 考虑 | YAML | TOML | JSON |
|------|------|------|------|
| 可读性 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 注释支持 | ✅ 原生 | ✅ 原生 | ❌ |
| 多行字符串 | ✅ | ✅ | ❌ |
| Python 内置 | ❌ (需 PyYAML) | ✅ (tomllib 3.11+) | ✅ |
| 常见度 | 高 (Docker Compose, K8s) | 中 (Rust 生态, pyproject) | 高 |

选 YAML 理由：分层结构直观、注释原生支持、Docker Compose/GHA 等生态通用，HomeBus 已有 PyYAML 依赖（GrocyClient 用到）。

## 目录规范

```
$XDG_CONFIG_HOME/homebus/
├── config.yaml              # 主配置文件
├── .env                     # 敏感环境变量 (可选, 不提交 git)
└── adapters/
    ├── grocy.yaml           # Grocy 适配器专用配置 (未来扩展)
    └── beancount.yaml       # Beancount 适配器专用配置 (未来扩展)
```

**XDG 回退**: `$XDG_CONFIG_HOME` 未设置时 → `~/.config/homebus/`

**MVP 阶段**: 仅使用 `config.yaml` + 环境变量。`adapters/` 目录为预留。

## 配置文件内容

### config.yaml — 完整结构

```yaml
# HomeBus 主配置文件
# 优先级: YAML < 环境变量 < CLI 参数

homebus:
  api:
    host: "0.0.0.0"           # 监听地址 (env: HOMEBUS_HOST)
    port: 8080                 # 监听端口 (env: HOMEBUS_PORT)
    debug: false               # 调试模式 (env: HOMEBUS_DEBUG)

  database:
    path: "~/.local/share/homebus/data.db"   # SQLite 路径 (env: HOMEBUS_DB_PATH)

  logging:
    level: "info"              # 日志级别 (env: HOMEBUS_LOG_LEVEL)
    format: "json"             # 输出格式: json | text

adapters:
  grocy:
    base_url: "http://192.168.31.40:9283"    # (env: GROCY_API_URL)
    # api_key 通过环境变量 GROCY_API_KEY 注入

  beancount:
    mode: "fava"               # 接入模式: fava | file
    fava_url: "http://192.168.31.40:5000"    # (env: BEANCOUNT_FAVA_URL)
    bean_file: "~/vicat/bean/main.bean"      # 文件模式路径 (env: BEANCOUNT_FILE)
    # 如无需认证可省略 token

  homebox:
    base_url: "http://192.168.31.40:7745"    # (env: HOMEBOX_API_URL)
    # token 通过环境变量 HOMEBOX_TOKEN 注入

cli:
  api_url: "http://localhost:8080"           # CLI 连接 API 地址 (env: HOMEBUS_CLI_URL)
  timeout: 30                                # CLI 请求超时 (秒)
```

### .env — 敏感信息

```bash
# ~/.config/homebus/.env
# 从不超过 git，通过 env_file 加载

GROCY_API_KEY=xxx
HOMEBOX_TOKEN=xxx
```

## 环境变量映射

| 配置路径 | 环境变量 | 说明 |
|----------|---------|------|
| `homebus.api.host` | `HOMEBUS_HOST` | API 监听地址 |
| `homebus.api.port` | `HOMEBUS_PORT` | API 监听端口 |
| `homebus.api.debug` | `HOMEBUS_DEBUG` | 调试模式 |
| `homebus.database.path` | `HOMEBUS_DB_PATH` | SQLite 路径 |
| `homebus.logging.level` | `HOMEBUS_LOG_LEVEL` | 日志级别 |
| `homebus.logging.format` | `HOMEBUS_LOG_FORMAT` | 日志格式 |
| — | `GROCY_API_KEY` | **敏感** Grocy API Key |
| `adapters.grocy.base_url` | `GROCY_API_URL` | Grocy 地址 |
| — | `HOMEBOX_TOKEN` | **敏感** Homebox Token |
| `adapters.homebox.base_url` | `HOMEBOX_API_URL` | Homebox 地址 |
| `adapters.beancount.fava_url` | `BEANCOUNT_FAVA_URL` | Fava 地址 |
| `adapters.beancount.bean_file` | `BEANCOUNT_FILE` | Bean 文件路径 |
| `cli.api_url` | `HOMEBUS_CLI_URL` | CLI 连接地址 |
| `cli.timeout` | `HOMEBUS_CLI_TIMEOUT` | CLI 超时 |

**原则**: 非敏感字段的 YAML 路径与环境变量名一一映射（`homebus.api.port` → `HOMEBUS_PORT`）。敏感字段仅通过环境变量注入，不出现在 config.yaml 中（YAML 中以注释标明 env 来源）。

## 配置分层加载

```
① 默认值硬编码
    ↓ (配置项未在文件中找到)
② 读取 config.yaml
    ↓ (配置项未在文件中找到)
③ 读取 .env
    ↓ (配置项未在 .env 或非敏感)
④ 检查环境变量
    ↓ (优先级最高)
⑤ CLI 参数覆盖 (仅 CLI 场景)
    ↓
最终配置值
```

### 加载顺序伪代码

```python
def load_config(cli_overrides: dict = None) -> Config:
    # 1. 默认值
    config = default_config()
    
    # 2. 配置文件覆盖
    config_file = find_config_file()  # XDG discovery
    if config_file:
        merge(config, yaml.safe_load(config_file))
    
    # 3. 环境变量覆盖
    merge_env_overrides(config, ENV_MAP)  # 非敏感字段
    
    # 4. CLI 参数覆盖 (最高优先级)
    if cli_overrides:
        merge(config, cli_overrides)
    
    return config
```

## 配置发现机制

### API Server 启动配置发现

```
① 环境变量 HOMEBUS_CONFIG_PATH
    ↓ (有值)
   → 读取指定路径
    ↓ (无值)
② XDG 规范: $XDG_CONFIG_HOME/homebus/config.yaml
    ↓ (有值)
   → 读取
    ↓ (无文件)
③ 回退: ~/.config/homebus/config.yaml
    ↓ (仍无文件)
④ 仅用默认值 + 环境变量
```

### CLI 配置发现

CLI 不需要找 config.yaml——它只需要知道 API Server 地址：

```
① --api-url 参数 (最高)
② 环境变量 HOMEBUS_CLI_URL
③ ~/.config/homebus/config.yaml 中的 cli.api_url
④ 默认 http://localhost:8080
```

### Adapter 配置发现

Adapter 不单独发现配置，由 API Server 启动时将配置注入：

```python
# API Server 启动时
config = load_config()
grocy_adapter = GrocyAdapter(
    base_url=config.adapters.grocy.base_url,
    api_key=os.environ["GROCY_API_KEY"],  # 敏感字段环境变量
)
```

## 敏感信息策略

| 信息 | 注入方式 | 示例 |
|------|---------|------|
| Grocy API Key | 环境变量 | `GROCY_API_KEY` |
| Homebox Token | 环境变量 | `HOMEBOX_TOKEN` |
| Beancount 认证 | 环境变量（如有需要） | `BEANCOUNT_TOKEN` |
| 数据库路径 | 配置文件或环境变量 | `HOMEBUS_DB_PATH` |
| 后端地址 | 配置文件或环境变量 | `GROCY_API_URL` |

**安全性原则**:
- 敏感信息永不出现在 config.yaml 中
- 环境变量可通过 Docker secret 或 `.env` 文件管理
- `.env` 文件加入 `.gitignore`
- API Server 不应在日志中输出敏感字段

## 配置验证

加载配置后执行校验：

| 校验项 | 规则 | 失败处理 |
|--------|------|---------|
| `homebus.api.port` | 1024-65535 | 启动报错 |
| `adapters.grocy.base_url` | 必须为有效 URL | 启动警告 + health check 时失败 |
| `GROCY_API_KEY` | 必须已设置 | 启动警告 |
| `adapters.beancount.mode` | 必须为 `fava` 或 `file` | 启动报错 |
| `homebus.database.path` | 父目录必须可写 | 启动报错 |

## 配置文件示例

### 最小配置（开发环境）

```yaml
# ~/.config/homebus/config.yaml
# 开发环境最小配置，其余用默认值

adapters:
  grocy:
    base_url: "http://localhost:9283"
  homebox:
    base_url: "http://localhost:7745"
```

配合 `.env`：

```bash
# ~/.config/homebus/.env
GROCY_API_KEY=dev-key-123
HOMEBOX_TOKEN=dev-token-456
```

### 生产配置（Docker Compose）

```yaml
# 通过环境变量注入，无需 config.yaml
# docker-compose.yml:

services:
  homebus:
    image: homebus:latest
    ports:
      - "8080:8080"
    environment:
      HOMEBUS_DB_PATH: /data/homebus.db
      GROCY_API_URL: http://grocy:9283
      GROCY_API_KEY: ${GROCY_API_KEY}
      HOMEBOX_API_URL: http://homebox:7745
      HOMEBOX_TOKEN: ${HOMEBOX_TOKEN}
    volumes:
      - homebus-data:/data
```

## 与 Grocy CLI 缓存共享

现有 grocy-cli skill 使用 `~/.config/grocy/cache.yaml`（位置/单位/产品组缓存）。

**策略**: HomeBus 的 Grocy Adapter 不重新创建缓存，直接读取 `~/.config/grocy/cache.yaml`。
如需写入，写入同一个文件（双方共用）。具体决策见 [doc/research/grocy-cli-assets.md](../research/grocy-cli-assets.md)。

## 实现清单

| 文件 | 职责 |
|------|------|
| `homebus/config.py` | 配置模型（Pydantic BaseSettings）、加载器、校验器 |
| `homebus/defaults.yaml` | 默认配置（嵌入包中，运行时不可修改） |
| `config.yaml.example` | 注释完整的示例配置文件（提交到 git） |
| `.env.example` | 敏感字段模板（提交到 git，占位符） |
| `.gitignore` | 确保 `.env` / `config.yaml` 不被提交 |

### 模块接口

```python
# homebus/config.py

class HomeBusConfig(BaseModel):
    """全局配置模型，Pydantic 校验"""
    ...

def load_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "HOMEBUS_",
    cli_overrides: Optional[dict] = None,
) -> HomeBusConfig:
    """分层加载配置：默认值 < YAML < 环境变量 < CLI"""
    ...

def discover_config_path() -> Path:
    """XDG 配置发现"""
    ...

def find_config() -> Optional[Path]:
    """按优先级搜索配置文件"""
    ...

def validate_config(config: HomeBusConfig) -> list[str]:
    """校验配置合规性，返回错误列表"""
    ...
```

## Open Questions

1. **是否需要支持配置热加载？** 当前设计为启动时一次性加载。热加载增加复杂度，MVP 不做。
2. **Beancount `file` 模式是否需要密码？** If using fava，可能需要 basic auth。预留 `BEANCOUNT_USER` / `BEANCOUNT_PASS` 环境变量空间。
3. **多 HomeBus 实例场景？** 目前是单实例设计，配置为单实例视角。多实例按 12-Factor 用环境变量完全配置。
