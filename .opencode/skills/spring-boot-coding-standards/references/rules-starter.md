# Spring Boot Starter 编码规则

> 适用 Spring Boot Starter 模块开发。需搭配 `rules-base.md` 使用。

---

## 0. Framework vs Starter 分层铁律

这是编写 Starter 最根本的架构原则，直接决定模块的可复用性和可测试性。

### 三层职责边界

```
project/
├── <project>-framework-<domain>/     # Framework 层：纯抽象 + 纯实现
│   ├── <project>-framework-<domain>-core/      # 核心接口、SPI、实体
│   ├── <project>-framework-<domain>-gateway/   # 传输层抽象
│   └── <project>-framework-<domain>-<impl>/    # 具体实现（仍无 Spring 依赖）
├── <project>-spring-boot-starter-<domain>/     # Starter 层：Spring Boot 粘合
│   ├── <project>-spring-boot-starter-<domain>-bom/    # 版本管理
│   ├── <project>-spring-boot-starter-<domain>-agent/  # Agent 自动配置
│   └── <project>-spring-boot-starter-<domain>-<transport>/  # 传输层自动配置
└── <project>-app/                    # 应用层（可选）
```

| 层 | 允许依赖 | 禁止依赖 | 职责 |
|----|---------|---------|------|
| **Framework** | JRE、Jackson、Reactor、Lombok、协议 SDK | **Spring Boot / Spring Framework**（编译和运行时均禁止） | 定义接口、SPI、领域实体、纯 Java 实现 |
| **Starter** | Framework 模块 + Spring Boot + Spring Framework | 应用层代码 | 自动配置、Bean 注册、properties 绑定 |
| **App** | Starter + Framework | 无 | 业务逻辑、Controller、入口 |

### 铁律

1. **Framework 层零 Spring 依赖**——编译和运行时 classpath 上不得出现 `spring-boot-*`、`spring-framework`。测试 scope 例外。
2. **Starter 层只管注册**——只做三件事：读 properties → 实例化 framework 对象 → 注册为 Bean。不放业务逻辑。
3. **父 POM 不得注入**——Framework 父 POM 的 `<dependencies>`（非 `<dependencyManagement>`）不能带任何 Spring 依赖，否则所有子模块被污染。

### 常见反例

- Framework 父 POM 中 `<dependency>` 了 `spring-boot-starter-web` → 所有子模块运行时强制带 Spring
- 在 Framework 模块中用 `@Component`、`@Service` 等 Spring 注解 → 破坏了框架的独立性
- Starter 的 AutoConfiguration 中写业务逻辑 → 应委托给 Framework 对象

### BOM 模块

在 Starter 层提供 BOM（Bill of Materials）：统一管理所有模块版本，使用方只需 import BOM 即可锁定版本，无需逐个指定。

---

## 1. Maven 多模块布局

```
<starter-name>/
├── pom.xml
├── <starter-name>-core/            # 核心抽象层（接口、抽象类、共性实体）
│   ├── pom.xml
│   └── src/main/java/<base-pkg>/
│       ├── autoconfigure/          # 自动配置类（也可用 config/）
│       └── core/
│           ├── constant/           # 常量、枚举
│           ├── entity/             # 领域实体
│           ├── exception/          # 异常定义
│           ├── event/              # 事件定义
│           │   ├── handler/        # 事件处理器
│           │   └── message/        # 事件消息体
│           ├── context/            # 上下文接口
│           ├── manager/            # 管理器
│           ├── media/              # 客户端接口
│           └── pipeline/           # 流水线/责任链
├── <starter-name>-<impl>-<vendor>/ # 具体厂商实现
│   ├── src/main/java/<base-pkg>/
│   │   ├── autoconfigure/       # 厂商自动配置（也可用 config/）
│   │   └── core/
│   │       ├── entity/
│   │       │   ├── req/            # 请求体
│   │       │   └── resp/           # 响应体
│   │       ├── service/
│   │       │   └── impl/
│   │       └── strategies/         # 策略实现
│   └── src/test/
├── <starter-name>-cloud-support/   # 云/集群支持（可选）
```

**核心原则**: `-core` 模块只放抽象，具体实现放子模块。

---

## 2. 包命名

```
<base-pkg>.<feature>
```

子包约定：

| 子包 | 用途 |
|------|------|
| `autoconfigure`（或 `config`） | 自动配置类、ConfigurationProperties |
| `core.constant` | 枚举常量、静态常量类 |
| `core.entity` | 领域实体/传输对象 |
| `core.exception` | 异常及异常结果枚举 |
| `core.event` | 事件总线、事件类型、消息 |
| `core.event.handler` | 事件处理器 |
| `core.manager` | 业务管理器（协调者） |
| `core.service` / `core.service.impl` | 服务接口与实现 |
| `core.strategies` | 策略模式接口与实现 |
| `core.pipeline` | 流水线/责任链 |
| `core.feign` | Feign 客户端 |

---

## 3. 自动配置

### 3.1 配置类结构

```java
@Slf4j
@AutoConfiguration(after = {CoreAutoConfiguration.class})
public class <Module>CoreStarterAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public StreamManager streamManager() {
        return new InternalStreamManager();
    }

    @Bean
    public MediaManager mediaManager(
            ObjectProvider<CompositeClient> compositeClients,
            ObjectProvider<MediaClient> clients,
            StreamManager streamManager) {
        return new MediaManager(
            Stream.concat(
                compositeClients.stream().map(CompositeClient::clients).flatMap(Collection::stream),
                clients.stream()
            ).toList(),
            streamManager
        );
    }
}
```

> **关键规则**: 自动配置类**必须**使用 `@AutoConfiguration`，**禁止**使用 `@Configuration`。
> `@AutoConfiguration` 是 Spring Boot 3.x 引入的专用注解，支持 `before`/`after` 控制加载顺序；`@Configuration` 虽在 `.imports` 中也能工作，但无法参与 auto-configuration ordering，
> 会导致跨模块的配置加载顺序不可控。内部嵌套配置类仍可用 `@Configuration`。

### 3.2 条件装配

| 注解 | 场景 |
|------|------|
| `@ConditionalOnMissingBean` | 允许用户覆盖默认实现 |
| `@ConditionalOnProperty(prefix=..., name="enabled")` | 功能开关 |
| `@ConditionalOnClass` | 按类路径条件加载 |

### 3.3 加载注册

每个模块在 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 注册配置类（Spring Boot 3.x 新机制，弃用 `spring.factories`）。

### 3.4 ObjectProvider 多配置源装配

```java
@Bean
public EventBus eventBus(ObjectProvider<EventHandler> handlers) {
    EventBus bus = new InternalEventBus();
    handlers.stream()
        .filter(Objects::nonNull)
        .filter(h -> !h.getEventTypes().isEmpty())
        .forEach(h -> h.getEventTypes()
            .forEach(type -> bus.subscribe(type, h)));
    return bus;
}
```

---

## 4. 配置属性

### 4.1 ConfigurationProperties 定义

- 使用 `@Getter` + `@Setter`（不用 `@Data`）
- 常量类中定义 `CONFIG_PREFIX`，子模块拼接
- 前缀格式：`<root>.<module>[.<sub-module>]`
- 必含 `enabled` 开关

```java
@Getter
@Setter
@ConfigurationProperties(prefix = VendorProperties.PREFIX)
public class VendorProperties {
    public static final String PREFIX = Constant.CONFIG_PREFIX + ".vendor";

    private boolean enabled = true;
    private List<ServerConfig> configs;

    @Getter
    @Setter
    public static class ServerConfig {
        private String id;
        private String apiUrl;
    }
}
```

### 4.2 Properties 类命名

| 类 | 用途 |
|-----|------|
| `<Module>Properties` | 框架核心配置 |
| `<Vendor>ConfigurationProperties` | 厂商/实现配置 |

---

## 5. 设计模式

### 5.1 策略模式
- 接口 + 按优先级排序的工厂
- 策略实现 `Integer order()` 控制优先级（值越小越优先）

```java
public interface UrlGenerateStrategy {
    boolean isMatch(String appName, StreamKey key);
    String generate(String appName, StreamKey key);
    Integer order();
}

public class StrategyFactory {
    private final List<UrlGenerateStrategy> strategies;

    public StrategyFactory(List<UrlGenerateStrategy> strategies) {
        this.strategies = strategies.stream()
            .sorted(Comparator.comparing(UrlGenerateStrategy::order))
            .toList();
    }

    public UrlGenerateStrategy getStrategy(String appName, StreamKey key) {
        return strategies.stream()
            .filter(s -> s.isMatch(appName, key))
            .findFirst()
            .orElse(null);
    }
}
```

### 5.2 工厂模式
- 用于创建 Feign 客户端等复杂对象
- 构造函数注入 `Encoder`/`Decoder`，方法创建实例

### 5.3 责任链/流水线
- 接口定义 `chain()` 和 `process()`
- 实现类维护 `List<Pipe>` 顺序执行

### 5.4 管理器模式 (Manager)
- Manager 作为领域操作的统一入口，聚合多个 Client/Service
- 使用 `ClientSelectPolicy` 选择具体 Client 执行操作

---

## 6. 事件/消息系统

- 优先使用 Spring 内置 `ApplicationEventPublisher` + `@EventListener`
- 如需类型安全的枚举事件分发和按事件类型路由，可自建 EventBus
- 自建 EventBus 使用 `ConcurrentHashMap` + `CopyOnWriteArrayList` 保证线程安全
- 事件类型枚举绑定消息体类型：`ON_PUBLISH("onPublish", OnPublishMessage.class)`
