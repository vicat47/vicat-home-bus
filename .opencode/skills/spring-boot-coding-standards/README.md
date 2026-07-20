# spring-boot-coding-standards

将个人认可的 Spring Boot 编码偏好分层注入到目标项目中。

## 快速使用

```
apm install spring-boot-coding-standards
```

加载后，在目标项目中说"按编码规范写"/"注入编码规则"，skill 会自动识别场景并注入对应规则。

## 规则分层

| 规则文件 | 适用场景 |
|----------|----------|
| `rules-base.md` | 任何 Spring Boot 项目 |
| `rules-starter.md` | Starter 模块开发 |
| `examples-tianyi.md` | 天易项目（仅参考，不注入） |
