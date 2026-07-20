# CHANGELOG 生成参考

CHANGELOG 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式，存储在 `doc/releases/CHANGELOG.md`。

## 生成时机

仅当 release 状态变为 `released`（GA 发布）时触发。

## 生成流程

```
STEP C1: 检查 CHANGELOG 是否存在
  - 运行: ls doc/releases/CHANGELOG.md 2>/dev/null
  - 如果不存在 → 使用下方模板创建

STEP C2: 读取 GA 文档
  - 读取最新的 GA 文件（`YYYYMMDD__vX.Y.Z-GA__<name>.md`）
  - 从功能清单中提取所有 `done` 的功能

STEP C3: 分类功能
  - 向用户确认每条功能的分类:
    - Added — 新增功能（`done` 的功能默认归入此类）
    - Changed — 对已有功能的修改
    - Deprecated — 即将移除的功能
    - Removed — 已移除的功能
    - Fixed — Bug 修复
    - Security — 安全修复

STEP C4: 更新 CHANGELOG
  - 如果存在 `[Unreleased]` 条目 → 移除对应版本的行
  - 新增版本条目，含发布日期
  - 格式见下方示例
```

## CHANGELOG.md 模板

```markdown
# Changelog

本文件遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

## [Unreleased]

### Added
- (无)

### Changed
- (无)

---

## [vX.Y.Z] - YYYY-MM-DD

### Added
- 功能描述

### Changed
- 变更描述

### Fixed
- 修复描述
```

## 示例条目

```markdown
## [v0.2.0] - 2026-06-23

### Added
- 多租户数据隔离（#1）
- 租户切换 API（#2）

### Fixed
- 修复租户 ID 为空时的 NPE 问题

## [v0.1.0] - 2026-06-01

### Added
- 初始项目搭建
- 基础认证模块
```
