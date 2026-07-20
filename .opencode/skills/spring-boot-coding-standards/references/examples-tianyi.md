
# 天易 Spring Boot Starter 编码规范（实例）

> 基于 `tianyi-spring-boot-starter-streamer` 与 `tianyi-spring-boot-starter-message` 模块源码审查总结  
> 版本: 2.1.x | Java 17+

> **重要**：此文档展示的是天易 **v2.1.x 旧架构**的写法（框架与 Spring 耦合在同一模块内）。
> 天易后续项目（如 `tianyi-ai-project`）已演进为四层分离架构（Framework → Starter → App → CLI），
> 其模块拆分原则和分层铁律见 `rules-starter.md` §0，不要照搬本文档的模块布局到新项目。

---

## 目录

1. [项目结构规范](#1-项目结构规范)
2. [命名规范](#2-命名规范)
3. [接口与抽象类设计](#3-接口与抽象类设计)
4. [枚举设计规范](#4-枚举设计规范)
5. [实体设计规范](#5-实体设计规范)
6. [自动配置规范](#6-自动配置规范)
7. [配置属性规范](#7-配置属性规范)
8. [异常处理规范](#8-异常处理规范)
9. [依赖注入规范](#9-依赖注入规范)
10. [Lombok 使用规范](#10-lombok-使用规范)
11. [Javadoc 规范](#11-javadoc-规范)
12. [设计模式应用](#12-设计模式应用)
13. [消息/事件系统规范](#13-消息事件系统规范)
14. [分布式/云原生支持](#14-分布式云原生支持)
15. [测试规范](#15-测试规范)

---

## 1. 项目结构规范

### 1.1 Maven 多模块布局

```
tianyi-spring-boot-starter-<feature>/
├── pom.xml                          # 父POM
├── tianyi-spring-boot-starter-<feature>-core/        # 核心抽象层
│   ├── pom.xml
│   └── src/main/java/com/tianyi/framework/boot/starter/<feature>/
│       ├── config/
│       │   └── TianYi<Feature>CoreStarterAutoConfiguration.java
│       └── core/
│           ├── constant/            # 常量、枚举
│           ├── entity/              # 领域实体
│           ├── exception/           # 异常定义
│           ├── event/               # 事件定义
│           │   ├── handler/         # 事件处理器
│           │   └── message/         # 事件消息体
│           ├── context/             # 上下文接口
│           ├── manager/             # 管理器
│           ├── media/               # 媒体/客户端接口
│           └── pipeline/            # 流水线/责任链
├── tianyi-spring-boot-starter-<feature>-<impl>-<vendor>/  # 具体厂商实现
│   ├── src/main/java/.../
│   │   ├── config/
│   │   │   ├── TianYi<Feature>AutoConfiguration.java
│   │   │   └── <Vendor>ConfigurationProperties.java
│   │   └── core/
│   │       ├── constant/
│   │       ├── entity/              # 厂商特有实体
│   │       │   ├── req/             # 请求体
│   │       │   └── resp/            # 响应体
│   │       ├── exception/
│   │       ├── feign/               # Feign 客户端
│   │       ├── listener/            # REST 监听器
│   │       ├── service/
│   │       │   └── impl/
│   │       └── strategies/          # 策略模式实现
│   └── src/test/
├── tianyi-spring-boot-starter-<feature>-cloud-support/  # 云/集群支持
```

### 1.2 包命名规则

基础包: `com.tianyi.framework.boot.starter.<feature>`

| 子包 | 用途 | 示例 |
|------|------|------|
| `config` | 自动配置类、ConfigurationProperties | `TianYiStreamerCoreStarterAutoConfiguration` |
| `core.constant` | 枚举常量、静态常量类 | `StreamProtocol`, `StreamerConstant` |
| `core.entity` | 领域实体/数据传输对象 | `StreamInfo`, `ChannelInfo` |
| `core.exception` | 异常及异常结果枚举 | `TianYiSpringBootStarterStreamerException` |
| `core.event` | 事件总线、事件类型、事件消息 | `MediaServerEventBus` |
| `core.event.handler` | 事件处理器 | `ComponentMediaServerEventHandler` |
| `core.manager` | 业务管理器（协调者） | `MediaServerManager` |
| `core.service` | 服务接口 | `ZlMediaService` |
| `core.service.impl` | 服务实现 | `ZlMediaServerClientImpl` |
| `core.strategies` | 策略模式接口与实现 | `UrlGenerateStrategy` |
| `core.pipeline` | 流水线/责任链 | `StreamProcessPipeline` |
| `core.feign` | Feign 客户端接口及工厂 | `RemoteZlMediaKitService` |

**核心原则**: `-core` 模块只放抽象（接口、抽象类、共性实体），具体实现放子模块。

> **实例备注**: 此文档基于 `tianyi-spring-boot-starter-streamer/message`（v2.1.x）生成，该项目直接将 starter 层和实现层合并在一起。后续项目（如 `tianyi-ai-project`）已演进为更规范的四层结构：`framework`（纯 Java 抽象与实现）→ `starter`（Spring Boot 粘合）→ `app`（业务应用）→ `cli`（独立 CLI）。一个已知的待改进点：`tianyi-framework-ai` 父 POM 中 `tianyi-framework-boot` 作为 compile 依赖，导致所有 framework 子模块运行时泄漏 Spring Boot，违反了 framework 层零 Spring 依赖的铁律，建议后续降级为 `<optional>` 或仅 starter 层引用。

---

## 2. 命名规范

### 2.1 接口命名

| 模式 | 用途 | 示例 |
|------|------|------|
| 名词 (无前缀) | 行为接口 | `MediaClient`, `MediaServerClient`, `UrlGenerateStrategy` |
| `Composite` + 名词 | 组合模式接口 | `CompositeMediaServerClient` |
| 标记/事件接口 | 语义化命名 | `MediaServerEvent`, `EventMessage` |

### 2.2 抽象类与适配器命名

| 模式 | 用途 | 示例 |
|------|------|------|
| `Abstract` + 名词 | 模板方法抽象基类 | `AbstractMessageSender` |
| `名词` + `Adapter` | 提供默认实现的适配器 | `MediaServerEventHandlerAdapter`, `StreamPipelinePipeAdapter` |
| `Common` + 名词 | 公共实现 | `CommonStreamProcessPipeline` |

### 2.3 实现类命名

使用 `<Vendor>` + `<Feature>` + `<InterfaceSuffix>` 模式:
- `ZlMediaServerClientImpl` — 实现 `MediaServerClient`
- `RtspPushServiceImpl` — 实现 `RtspPushService`
- `NacosDiscoveryService` — 实现 `DiscoveryService`

### 2.4 配置类命名

| 模式 | 示例 |
|------|------|
| `TianYi<Module>StarterAutoConfiguration` | `TianYiStreamerCoreStarterAutoConfiguration` |
| `TianYi<Module>Properties` | `TianYiMessageProperties`, `ZlMediaKitConfigurationProperties` |
| `<Vendor>AutoConfiguration` | `ZlMediaKitAutoConfiguration`, `RtspClientAutoConfiguration` |

### 2.5 枚举命名

| 模式 | 示例 |
|------|------|
| 名词 (无后缀) | `StreamProtocol`, `MediaServerEventType` |
| `名词` + `Type` | `StreamConsumeType`, `StreamSourceType` |

### 2.6 常量类命名

| 模式 | 示例 |
|------|------|
| `<Module>Constant` | `StreamerConstant`, `TianYiMessageConstant`, `ZlMediaKitConstant` |

---

## 3. 接口与抽象类设计

### 3.1 接口粒度和职责

接口保持小而专注，一个接口约 3-7 个方法。

```java
// 好的示例: 聚焦单一职责
public interface MediaServerClient extends MediaClient {
    StreamIdentifier getStreamIdentifier(StreamDescriptionEntity stream);
    StreamDescriptionEntity addStreamProxy(StreamDescriptionEntity stream);
    MediaStreamStatus getStreamStatus(StreamDescriptionEntity entity);
    StreamDescriptionEntity registerPublishEndpoint(StreamProtocol protocol, ...);
}
```

### 3.2 模板方法模式 (Template Method)

抽象类定义骨架，子类实现具体逻辑。使用 `send()` -> `send0()` 模式：

```java
public abstract class AbstractMessageSender<T extends BaseMsgEntity>
    implements MessageSender<T> {

    @Override
    public EventProcessResult send(T param) {
        return this.send0(param);       // 委托给子类实现
    }

    protected abstract EventProcessResult send0(T param);
    protected abstract EventProcessResult asyncSend0(T param);
}
```

### 3.3 适配器模式 (Adapter)

为接口提供默认空实现，使用者只需覆写关心的部分：

```java
public abstract class MediaServerEventHandlerAdapter implements MediaEventHandler {
    // 提供默认实现
    @Override
    public void handlerAdded(MediaServerEventHandlerContext ctx) {
        log.info("event handler added");
    }

    // 强制子类实现
    public abstract void eventReceived(MediaServerEventHandlerContext ctx, Object msg);
    public abstract boolean acceptEventMessage(Object msg);
}
```

### 3.4 组合模式 (Composite)

将多个同类型实现组合为一个：

```java
// 声明
public interface CompositeMediaServerClient {
    List<MediaServerClient> clients();
}

// 在 AutoConfiguration 中装配
@Bean
public CompositeMediaServerClient zlMediaServerClientImpls(...) {
    return () -> properties.getConfigs().stream()
            .map(config -> new ZlMediaServerClientImpl(...))
            .collect(Collectors.toList());
}
```

### 3.5 默认方法使用

在接口中通过 `default` 方法提供常用实现：

```java
public interface ClientSelectPolicy<T> {
    default T select(final List<T> t) {
        return t.stream().findFirst()
                .orElseThrow(() -> new ServiceException(...));
    }
}
```

---

## 4. 枚举设计规范

### 4.1 统一序列化接口

所有需要在 JSON 中序列化的枚举实现 `JsonSerializable`：

```java
public interface JsonSerializable {
    @JsonValue
    String getValue();
}
```

### 4.2 枚举定义模式

```java
@Getter
@RequiredArgsConstructor
public enum StreamProtocol implements JsonSerializable {
    RTSP("rtsp", StandardSchemaPort.RTSP.getPort()),
    RTMP("rtmp", StandardSchemaPort.RTMP.getPort()),
    HLS("hls", StandardSchemaPort.HTTP.getPort()),
    ;

    private final String value;          // JSON序列化值
    private final Integer port;          // 关联数据

    // 工厂方法: 从字符串解析枚举值
    public static StreamProtocol of(String value) {
        return Arrays.stream(values())
                .filter(item -> item.getValue().equals(value))
                .findFirst()
                .orElseThrow(() -> new ServiceException(...));
    }
}
```

### 4.3 异常枚举模式

```java
@Getter
@RequiredArgsConstructor(access = AccessLevel.PRIVATE)
public enum TianYiSpringBootStarterStreamerException implements IStaticExceptionResult {
    INVALID_PROTOCOL(1001007001, "协议非法"),
    STREAM_CLIENT_NOT_FOUND(1001007002, "拉流客户端/服务端未找到，请检查相关配置"),
    ;

    final Integer code;
    final String message;

    public ExceptionResult createExceptionResult() {
        return new ExceptionResult(code, name(), message);
    }
}
```

### 4.4 枚举内嵌子枚举

```java
public enum StreamChannelType implements JsonSerializable {
    VISIBLE("1", ChannelSourceType.DEVICE),
    INFRARED("2", ChannelSourceType.DEVICE),
    ;

    public enum ChannelSourceType {
        DEVICE, NVR
    }
}
```

---

## 5. 实体设计规范

### 5.1 Record 用于不可变数据

```java
// 简单不可变数据 — 用 Record
public record DeviceInfo(String name, String code, ChannelInfo channel) {}

public record StreamIdentifier(String serverId, String streamId) {}

public record StreamAddressInfo(
    StreamProtocol protocol,
    String ip,
    Integer port,
    String path,
    MultiValueMap<String, String> param
) {
    // 紧凑构造函数用于默认值/校验
    public StreamAddressInfo(StreamProtocol protocol, String ip) {
        this(protocol, ip, null, null);
    }
}
```

### 5.2 @Data 类用于可变实体

```java
@Data
public abstract class StreamDescriptionEntity {
    private String id;
    private String serverId;
    private DeviceInfo deviceInfo;
    private StreamInfo streamInfo;
    private StreamAddressInfo addressInfo;
    private Map<String, String> expands;

    public abstract String toUrl();
    public abstract StreamDescriptionEntity fromUrl(String url);
}
```

### 5.3 Builder 模式用于复杂构造

```java
// 在 ZlMediaKit 内部使用 Builder
AddStreamProxyQuery query = AddStreamProxyQuery.builder()
    .app(ZlMediaKitConstant.LIVE)
    .stream(stream.getId())
    .url(stream.toUrl())
    .enableRtsp(EnableSymbol.ENABLE)
    .build();
```

---

## 6. 自动配置规范

### 6.1 配置类结构

```java
@Slf4j
@AutoConfiguration(after = {TianYiBootStarterAutoConfiguration.class})
public class TianYiStreamerCoreStarterAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public MediaServerStreamManager mediaServerStreamManager() {
        return new MediaServerInternalStreamManager();
    }

    @Bean
    public MediaServerManager mediaServerManager(
            ObjectProvider<CompositeMediaServerClient> compositeClients,
            ObjectProvider<MediaServerClient> clients,
            MediaServerStreamManager streamManager) {
        return new MediaServerManager(
            Stream.concat(
                compositeClients.stream().map(c -> c.clients()).flatMap(Collection::stream),
                clients.stream()
            ).toList(),
            streamManager
        );
    }
}
```

### 6.2 条件装配

| 注解 | 使用场景 |
|------|----------|
| `@ConditionalOnMissingBean` | 允许用户自定义实现进行覆盖 |
| `@ConditionalOnProperty(prefix=..., name="enabled")` | 功能开关，通过配置启用/禁用 |
| `@ConditionalOnRuntimeMode(mode = RuntimeMode.cloud)` | 按运行模式（单体/云）条件装配 |

### 6.3 多配置源装配 (ObjectProvider)

使用 `ObjectProvider` 收集所有实现，通过 Stream API 组装：

```java
@Bean
public MediaServerEventBus mediaServerEventBus(
        ObjectProvider<ComponentMediaServerEventHandler> eventHandlers) {
    MediaServerInternalEventBus eventBus = new MediaServerInternalEventBus();
    eventHandlers.stream()
        .filter(Objects::nonNull)
        .filter(h -> CollUtil.isNotEmpty(h.getEventTypeList()))
        .toList()
        .forEach(h -> h.getEventTypeList()
            .forEach(type -> eventBus.subscribe(type, h)));
    return eventBus;
}
```

### 6.4 `@AutoConfiguration` 加载文件

每个模块需在 `src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 中注册配置类：

```
com.tianyi.framework.boot.starter.streamer.config.TianYiStreamerCoreStarterAutoConfiguration
com.tianyi.framework.boot.starter.streamer.rtsp.config.RtspClientAutoConfiguration
```

### 6.5 静态内部配置类

将 Feign 相关配置内聚在配置类内部：

```java
@Configuration
@Import(FeignClientsConfiguration.class)
public static class ZlMediaKitFeignAutoConfiguration {}
```

---

## 7. 配置属性规范

### 7.1 ConfigurationProperties 定义

```java
@Getter
@Setter
@ConfigurationProperties(prefix = ZlMediaKitConfigurationProperties.PREFIX)
public class ZlMediaKitConfigurationProperties {
    public static final String PREFIX = StreamerConstant.CONFIG_PREFIX + ".zl-media-kit";

    private boolean enabled = true;
    private List<ZlMediaKitServerConfig> configs;

    @Getter
    @Setter
    public static class ZlMediaKitServerConfig {
        private String id;
        private String externalHost;
        private String apiUrl;
        private String secret;
    }
}
```

### 7.2 配置前缀规范

```
tianyi.<module>[.<sub-module>]
```

- 常量类中定义 `CONFIG_PREFIX`: `public static final String CONFIG_PREFIX = "tianyi.streamer";`
- 子模块拼接: `StreamerConstant.CONFIG_PREFIX + ".zl-media-kit"`
- enabled 开关: `StreamerConstant.ENABLED_KEY = "enabled"`

### 7.3 Properties 类命名

| 类 | 用途 |
|-----|------|
| `TianYiMessageProperties` | 框架核心配置 |
| `ZlMediaKitConfigurationProperties` | 厂商/实现配置 |
| `TianYiSeeEmitterProperties` | 功能组件配置 |

---

## 8. 异常处理规范

### 8.1 异常枚举定义

> **注意**: 使用枚举存储异常码依赖天易框架私有的 `IStaticExceptionResult` / `ServiceException` / `ExceptionResult` 机制。
> 如果模块不依赖天易框架，应使用标准 Spring Boot 做法：定义 `RuntimeException` 子类 + `@ControllerAdvice` + `@ExceptionHandler` 进行全局异常处理。

```java
@Getter
@RequiredArgsConstructor(access = AccessLevel.PRIVATE)
public enum TianYiSpringBootStarterStreamerException implements IStaticExceptionResult {
    INVALID_PROTOCOL(1001007001, "协议非法"),
    STREAM_CLIENT_NOT_FOUND(1001007002, "拉流客户端/服务端未找到");

    final Integer code;
    final String message;

    public ExceptionResult createExceptionResult() {
        return new ExceptionResult(code, name(), message);
    }
}
```

### 8.2 异常抛出方式

```java
throw new ServiceException(
    TianYiSpringBootStarterStreamerException.INVALID_PROTOCOL.createExceptionResult()
);
// 或带参数
throw new ServiceException(
    ZlMediaKitServiceExceptionResult.CONFIG_ERROR.createExceptionResult(),
    new String[]{"api-url"}
);
```

### 8.3 自定义异常类

```java
@Getter
public class TargetNotFoundException extends Exception {
    private final String targetId;
    private final String targetType;

    public TargetNotFoundException(String message, String targetId, BaseMsgEntity msgEntity) {
        super(message);
        this.targetId = targetId;
        this.targetType = msgEntity.getMsgType().getCode();
    }
}
```

---

## 9. 依赖注入规范

### 9.1 构造函数注入（唯一推荐方式）

使用 `@RequiredArgsConstructor` + `final` 字段：

```java
@Slf4j
@RequiredArgsConstructor
public class MediaServerManager {
    private final List<MediaServerClient> mediaServerClientList;
    private final MediaServerStreamManager streamManager;
    // ...
}
```

### 9.2 Bean 注册方式

| 方式 | 适用场景 |
|------|----------|
| `@Bean` 方法 | 需要显式构造逻辑的对象 |
| `@ComponentScan` | 用户自定义的 Controller/Service 等 |
| 构造函数自动注入 | 内部 Bean 间依赖 |

### 9.3 ObjectProvider vs 直接注入

- `ObjectProvider<T>` — 用于收集**可选**或**多实现**的 Bean，在 AutoConfiguration 中常用
- `List<T>` — 直接注入所有实现（当明确需要所有实现时）
- `T` 单值注入 — 当只有一个实现时

---

## 10. Lombok 使用规范

### 10.1 常用注解清单

| 注解 | 用途 | 典型场景 |
|------|------|----------|
| `@Slf4j` | 日志 | 所有非数据类 |
| `@RequiredArgsConstructor` | 构造函数注入 | Manager, Service, Configuration |
| `@Getter` | 只读访问器 | 枚举, 异常 |
| `@Data` | 全属性访问器 | Entity（非配置属性类） |
| `@Getter` + `@Setter` | 读写访问器 | ConfigurationProperties |
| `@NoArgsConstructor(access = AccessLevel.PRIVATE)` | 私有构造 | 常量类、单例 |
| `@Setter` | 部分属性写 | 需要 set 特定字段 |

### 10.2 常量类/工具类私有构造

```java
@NoArgsConstructor(access = AccessLevel.PRIVATE)
public class StreamerConstant {
    public static final String CONFIG_PREFIX = "tianyi.streamer";
}
```

### 10.3 单例模式

```java
@NoArgsConstructor(access = AccessLevel.PRIVATE)
public class AnyMediaClientType implements MediaClientType {
    private static final AnyMediaClientType INSTANCE = new AnyMediaClientType();

    public static AnyMediaClientType getInstance() {
        return INSTANCE;
    }
}
```

---

## 11. Javadoc 规范

### 11.1 类级别注释

```java
/**
 * 消息发送服务
 *
 * <p>该服务是消息发送的核心协调器，负责协调消息过滤、通道选择和实际发送过程。</p>
 *
 * <p>主要功能：</p>
 * <ul>
 *   <li>消息发送器选择：根据消息类型选择合适的发送器</li>
 *   <li>消息过滤：应用所有配置的过滤器</li>
 * </ul>
 *
 * @author tianyi
 * @since 2022/1/20 14:52
 */
```

### 11.2 方法级别注释

```java
/**
 * 批量发送消息
 *
 * <p>该方法接收消息实体列表，为每个消息选择合适的发送器。</p>
 *
 * <p>处理流程：</p>
 * <ol>
 *   <li>为每个消息选择合适的发送器</li>
 *   <li>应用所有配置的过滤器</li>
 * </ol>
 *
 * @param entities 要发送的消息实体列表
 * @return 发送结果列表
 * @see MessageFilter 消息过滤器接口
 */
```

### 11.3 字段注释

```java
/**
 * 消息发送间隔（毫秒）
 *
 * <p>控制向同一个连接发送消息的最小时间间隔。</p>
 * <ul>
 *   <li>{@code -1} - 不限制发送间隔</li>
 *   <li>{@code > 0} - 最小发送间隔（毫秒）</li>
 * </ul>
 */
private Integer messageInterval = -1;
```

### 11.4 关键点

- 使用 `{@code}`, `{@link}`, `{@literal}` 等标签
- `@param`, `@return`, `@throws`, `@see` 必须完整
- `@author` 和 `@since` 标注在类级别
- 中文为主，关键术语保留英文。如果项目可能开源或面向国际化团队协作，建议使用英文 Javadoc 或在 `@param` / `@return` 中同时提供中英双语

---

## 12. 设计模式应用

### 12.1 策略模式 (Strategy)

定义策略接口，由工厂管理多个策略实现，按优先级匹配：

```java
// 接口
public interface UrlGenerateStrategy {
    boolean isMatch(String appName, ZlMediaStreamKey streamKey, ...);
    String generate(String appName, ZlMediaStreamKey streamKey, ...);
    Integer order();    // 优先级，值越小越优先
}

// 工厂
public class ZlMediaUrlGenerateStrategiesFactory {
    private final List<UrlGenerateStrategy> strategies;

    public ZlMediaUrlGenerateStrategiesFactory(List<UrlGenerateStrategy> strategies) {
        this.strategies = strategies.stream()
            .sorted(Comparator.comparing(UrlGenerateStrategy::order))
            .toList();
    }

    public UrlGenerateStrategy getStrategy(String appName, ...) {
        for (UrlGenerateStrategy s : strategies) {
            if (s.isMatch(appName, ...)) return s;
        }
        return null;
    }
}
```

### 12.2 工厂模式 (Factory)

用于创建 Feign 客户端等复杂对象：

```java
public class ZlMediaKitServiceFactory {
    private final Encoder encoder;
    private final Decoder decoder;

    public RemoteZlMediaKitService createRemoteService(String url, String secret) {
        return Feign.builder()
            .encoder(encoder).decoder(decoder)
            .requestInterceptor(template -> template.query("secret", secret))
            .target(RemoteZlMediaKitService.class, url);
    }
}
```

### 12.3 责任链/流水线 (Pipeline/Chain of Responsibility)

```java
public interface StreamProcessPipeline {
    StreamProcessPipeline chain(StreamPipelinePipe pipeline);
    StreamDescriptionEntity process(StreamDescriptionEntity entity);
}

// 抽象实现
public abstract class CommonStreamProcessPipeline implements StreamProcessPipeline {
    private final List<StreamPipelinePipe> pipeline = new CopyOnWriteArrayList<>();

    @Override
    public StreamDescriptionEntity process(StreamDescriptionEntity entity) {
        StreamDescriptionEntity next = entity;
        for (StreamPipelinePipe pipe : pipeline) {
            next = pipe.process(next);
        }
        return next;
    }
}
```

### 12.4 发布-订阅 (Pub/Sub)

用于事件驱动架构 — 详见第13节。

### 12.5 管理器模式 (Manager)

Manager 类作为领域操作的统一入口，聚合多个 Client/Service：

```java
public class MediaServerManager {
    private final List<MediaServerClient> mediaServerClientList;
    private final MediaServerStreamManager streamManager;

    public StreamDescriptionEntity addStreamProxy(StreamDescriptionEntity stream,
            ClientSelectPolicy<MediaServerClient> selectPolicy) {
        MediaServerClient client = selectPolicy.select(mediaServerClientList);
        // 委托给 client 执行具体操作
        return client.addStreamProxy(stream);
    }
}
```

---

## 13. 消息/事件系统规范

> **注意**: Spring Boot 内置了 `ApplicationEventPublisher` + `@EventListener` / `@TransactionalEventListener` 事件机制。
> 本项目自建 `MediaServerEventBus` 的原因是需要**类型安全的枚举事件类型分发**和**按事件类型订阅的处理器路由**，
> 这在流媒体服务器 Hook 回调场景下比泛化的事件 Object 分发更精确。如果你的事件场景足够简单，优先考虑 Spring 内置机制。

### 13.1 事件总线定义

```java
public interface MediaServerEventBus {
    void subscribe(MediaServerEventType eventType, MediaEventHandler handler);
    <T extends EventMessage> void publish(MediaServerEventType eventType,
        MediaServerEventHandlerContext context, T msg);
}
```

### 13.2 事件类型枚举

```java
@Getter
@RequiredArgsConstructor(access = AccessLevel.PROTECTED)
public enum MediaServerEventType {
    ON_PUBLISH("onPublish", MediaServerOnPublishMessage.class),
    ON_STREAM_NOT_FOUND("onStreamNotFound", MediaServerOnPublishMessage.class),
    ;
    private final String eventType;
    private final Class<? extends EventMessage> messageType;
}
```

### 13.3 线程安全的发布

```java
// 使用 ConcurrentHashMap + CopyOnWriteArrayList 保证线程安全
private final Map<MediaServerEventType, CopyOnWriteArrayList<MediaEventHandler>>
    events = new ConcurrentHashMap<>();

@Override
public <T extends EventMessage> void publish(MediaServerEventType type,
        MediaServerEventHandlerContext ctx, T msg) {
    CopyOnWriteArrayList<MediaEventHandler> handlers = events.get(type);
    if (handlers == null || handlers.isEmpty()) return;
    handlers.forEach(h -> {
        try {
            if (h instanceof MediaServerEventHandlerAdapter adapter) {
                adapter.eventReceived(ctx, msg);
            }
        } catch (Exception e) {
            log.error("event handler execute error", e);
            throw new RuntimeException(e);
        }
    });
}
```

---

## 14. 分布式/云原生支持

### 14.1 运行模式区分

```java
@AutoConfiguration(after = TianYiBootStarterAutoConfiguration.class)
@ConditionalOnRuntimeMode(mode = RuntimeMode.cloud)
public class TianYiMessageCloudStarterAutoConfiguration {
    // 云模式特有配置
}
```

### 14.2 服务发现抽象

```java
public interface DiscoveryService {
    String getCurrentInstanceId();
    // ...
}

public class NacosDiscoveryService implements DiscoveryService {
    // Nacos 实现
}
```

### 14.3 Redis 连接状态管理

```java
public abstract class RedisStatefulMessageDelegateConnectionManager<C>
        extends AbstractCloudDelegateConnectionManager<C> {

    @Override
    public void refreshConnection(C connection) {
        String id = connection.connectionId();
        String redisKey = getRedisKey(id);
        TianYiMessageProperties.HealthCheck healthConfig = getHealthConfig();
        redisTemplate.expire(redisKey,
            Duration.of(Math.round(healthConfig.getInterval() * 1.5), healthConfig.getUnit()));
    }
}
```

### 14.4 Feign 客户端动态路由

```java
public class MessageRouteFeignClientFactory {
    public MessageRouteFeignClient create() {
        return Feign.builder()
            .client(new DynamicTargetByHeader(selector))
            .target(MessageRouteFeignClient.class, "http://dynamic");
    }
}
```

---

## 15. 测试规范

### 15.1 测试类结构

```
src/test/
├── java/com/tianyi/
│   ├── <Feature>TestApplication.java     # 测试启动类
│   └── .../core/
│       ├── service/impl/
│       │   └── ZlMediaServerClientImplTest.java
│       ├── manager/
│       │   └── InMemorySseConnectionManagerTest.java
│       ├── controller/
│       │   └── TestMessageController.java
│       └── provider/
│           └── TestAuthUserProvider.java
└── resources/
    ├── application.yml
    └── test/
        └── *.http                        # HTTP 测试脚本
```

### 15.2 测试启动类

```java
@SpringBootApplication
public class ZlMediaKitTestApplication {
    public static void main(String[] args) {
        SpringApplication.run(ZlMediaKitTestApplication.class, args);
    }
}
```

### 15.3 HTTP 测试文件

使用 `.http` 文件做集成测试：

```
### on_publish
POST http://localhost:8080/index/hook/on_publish
Content-Type: application/json

{
  "mediaServerId": "test",
  "app": "live",
  "stream": "test-stream"
}
```

---

## 附录: 技术栈清单

| 技术 | 用途 | 版本 |
|------|------|------|
| Java | 开发语言 | 17+ |
| Spring Boot | 应用框架 | 3.x |
| Spring Cloud OpenFeign | 远程调用 | 与 Boot 匹配 |
| Lombok | 代码简化 | 最新稳定版 |
| Hutool | 通用工具集 | 5.x |
| Netty | 网络通信 (RTSP) | 4.x |
| Redis | 分布式状态管理 | - |
| Nacos | 服务发现与配置 | - |

---

*文档基于 `tianyi-spring-boot-starter-streamer` (v2.1.7.1-SNAPSHOT) 与 `tianyi-spring-boot-starter-message` 模块的源代码审查生成。*
