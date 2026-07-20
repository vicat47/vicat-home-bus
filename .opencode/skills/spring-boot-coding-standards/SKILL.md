---
name: spring-boot-coding-standards
description: >-
  Activate when the user asks to write / review Spring Boot code, create a starter,
  初始化项目编码规范, 注入编码规则, or mentions 编码规范、coding standards.
category: documentation
tags: ["spring-boot", "coding-standards", "编码规范", "starter"]
---

# Spring Boot 编码规范

将个人认可的 Spring Boot 编码偏好**分层注入**到目标项目中，避免把不需要的规则污染 agent 上下文。

## 触发条件

- "写 Spring Boot 代码" / "review Spring Boot 项目"
- "创建/写一个 starter"
- "初始化项目编码规范" / "注入编码规则"
- "coding standards" / "编码规范"
- 需要按编码偏好生成或审查 Java/Spring Boot 代码

## 分层规则结构

```
references/
├── rules-base.md        # 通用规则：任何 Spring Boot 项目都适用
├── rules-starter.md     # Starter 专属规则：自动配置、工厂模式、事件系统
└── examples-tianyi.md   # 天易 starter 项目的具体写法实例
```

## 工作流

### 1. 识别场景

根据用户输入判断应注入哪个规则集：

| 场景 | 注入规则 | 覆盖项 |
|------|----------|--------|
| 写"天易"项目 / 写 tianyi starter | `rules-base` + `rules-starter` + `examples-tianyi` | 异常处理用天易枚举模式替代 rules-base §9；接口命名跟随天易框架 `I` 前缀 |
| 写一个新的 starter（非天易） | `rules-base` + `rules-starter` | — |
| 写普通 Spring Boot 项目 | `rules-base` | — |

### 2. 确认目标项目和 Agent

必须向用户确认两项：

1. **目标项目根目录**（有 `pom.xml` / `build.gradle` 的位置）
2. **使用的 Agent 类型**，以确定 rules 注入路径：

| Agent | Rules 目录 |
|-------|-----------|
| OpenCode | `.opencode/rules/` |
| Cursor | `.cursor/rules/` |
| Cline / Roo Code | `.clinerules/` |
| Windsurf | `.windsurf/rules/` |
| GitHub Copilot | `.github/copilot-instructions.md`（单文件追加） |
| 其他 / 不确定 | `.agent/rules/`（fallback） |

### 3. 注入规则

按步骤 1 的场景 + 步骤 2 的 agent，将选定规则写入对应目录：

```bash
# Unix (Linux/macOS) 示例：OpenCode + base + starter
mkdir -p <target>/.opencode/rules/
cp references/rules-base.md <target>/.opencode/rules/spring-boot-base.md
cp references/rules-starter.md <target>/.opencode/rules/spring-boot-starter.md
```

```powershell
# Windows (PowerShell) 示例：OpenCode + base + starter
New-Item -ItemType Directory -Path "<target>/.opencode/rules/" -Force
Copy-Item -LiteralPath "references/rules-base.md" -Destination "<target>/.opencode/rules/spring-boot-base.md"
Copy-Item -LiteralPath "references/rules-starter.md" -Destination "<target>/.opencode/rules/spring-boot-starter.md"
```

或直接使用 agent 自带的文件写入工具将 rules 内容写入目标路径。

通用规则注入为 `spring-boot-base.md`，starter 规则注入为 `spring-boot-starter.md`。

### 4. 确认注入结果

列出目标项目中已写入的规则文件。

### 5. 注入后动作

规则注入完成不代表结束。必须向用户确认后续模式：

| 模式 | 说明 |
|------|------|
| **合规扫描** | 以注入的规则为基准，扫描目标项目中已有代码的违规项，输出报告（不改代码） |
| **仅约束新代码** | 规则仅对后续新写/新 review 的代码生效，不对已有代码追溯 |
| **继续原请求** | 用户原始请求另有任务（如"写一个 controller"），注入完直接执行原始任务 |

默认选择"仅约束新代码"。若用户要求扫描，执行合规检查并输出违规清单。

### 6. 加载规则并执行

按步骤 5 选定的模式继续后续动作。**agent 应自行读取目标项目的 rules 文件**作为编码依据。

## 注意事项

- 规则文件在目标项目中由 agent 自行按需读取，不在本 skill 中预先加载全部内容
- 注入路径依赖步骤 2 确认的 agent 类型，不假设固定目录
- 如果目标项目已有同名 rules 文件，注入前先确认是否覆盖
- `examples-tianyi.md` 不注入到目标项目，仅在需要时参考
