# Spring Boot 通用编码规则

> 适用任何 Spring Boot / Java 17+ 项目。

---

## 1. 命名规范

### 1.1 接口
- 使用裸名词，**不加 `I` 前缀**。例：`MediaClient`、`UrlGenerateStrategy`
- 组合模式接口以 `Composite` + 名词命名
- **框架兼容**：如果项目依赖的框架本身使用 `I` 前缀（如 `IBaseService`），则新接口也应跟随框架风格以保持一致性，或制定全项目迁移计划统一去掉

### 1.2 抽象类
- 模板方法基类：`Abstract` + 名词
- 提供默认实现的适配器：名词 + `Adapter`
- 公共实现：`Common` + 名词

### 1.3 实现类
- 模式：`<Vendor/Impl>` + `<Feature>` + `<InterfaceName>`，如 `ZlMediaServerClient` 实现 `MediaServerClient`
- 或使用 `Impl` 后缀：`<InterfaceName>Impl`

### 1.4 枚举
- 使用裸名词，**不加 `Enum` 后缀**。例：`StreamProtocol`、`MediaServerEventType`
- 分类枚举使用 `Type` 结尾：`StreamConsumeType`、`ChannelSourceType`

### 1.5 常量类
- 模式：`<Module>Constant`

---

## 2. 接口与抽象类设计

### 2.1 接口粒度
- 保持小而专注，一个接口约 **3-7 个方法**

### 2.2 模板方法模式
- 抽象类定义骨架，公开方法委托给 `protected abstract` 子类实现
- 命名模式：`doXxx()` → `doXxx0()`

```java
public abstract class AbstractMessageSender<T> implements MessageSender<T> {
    @Override
    public Result send(T param) {
        return this.send0(param);
    }
    protected abstract Result send0(T param);
}
```

### 2.3 适配器模式
- 抽象类为接口提供默认空实现，使用者只需覆写关心的方法
- 被覆写的方法声明为 `abstract` 强制子类实现

### 2.4 default 方法
- 在接口中用 `default` 提供常用实现，减少子类重复代码

```java
public interface ClientSelectPolicy<T> {
    default T select(List<T> list) {
        return list.stream().findFirst()
                .orElseThrow(() -> new ServiceException("no client available"));
    }
}
```

---

## 3. 枚举设计

### 3.1 统一序列化
- 需要 JSON 序列化的枚举实现统一接口，用 `@JsonValue` 标注序列化值

```java
public interface JsonSerializable {
    @JsonValue
    String getValue();
}
```

### 3.2 字段与工厂方法
- 使用 `@Getter` + `@RequiredArgsConstructor` + `private final` 字段
- 提供 `of(String)` 静态工厂方法从字符串解析枚举值

```java
@Getter
@RequiredArgsConstructor
public enum StreamProtocol implements JsonSerializable {
    RTSP("rtsp"),
    RTMP("rtmp");

    private final String value;

    public static StreamProtocol of(String value) {
        return Arrays.stream(values())
                .filter(item -> item.getValue().equals(value))
                .findFirst()
                .orElseThrow(() -> new ServiceException("unknown protocol: " + value));
    }
}
```

### 3.3 枚举内嵌子枚举
- 允许枚举内部定义用于分类的子枚举

---

## 4. 实体设计

### 4.1 选择边界

| 类型 | 适用场景 | 工具 |
|------|----------|------|
| **Record** | 不可变数据载体 | Java `record` |
| **@Data 类** | 可变数据传输对象 | Lombok `@Data` |
| **Builder** | 复杂构造、多可选参数 | Lombok `@Builder` |

### 4.2 Record 使用
- 紧凑构造函数用于默认值和校验
- 仅包含不可变字段

```java
public record StreamIdentifier(String serverId, String streamId) {}

public record StreamAddress(ProtocolEnum protocol, String ip, Integer port) {
    public StreamAddress(ProtocolEnum protocol, String ip) {
        this(protocol, ip, null);
    }
}
```

### 4.3 @Data 类
- 用于需要 getter/setter 的可变实体
- **不要**用于 JPA Entity（equals/hashCode 问题）

---

## 5. 依赖注入

### 5.1 构造函数注入（唯一推荐）
- 使用 `@RequiredArgsConstructor` + `final` 字段

```java
@Slf4j
@RequiredArgsConstructor
public class MediaManager {
    private final List<MediaClient> clients;
    private final StreamManager streamManager;
}
```

### 5.2 Bean 注册方式

| 方式 | 场景 |
|------|------|
| `@Bean` 方法 | 需要显式构造逻辑 |
| `@ComponentScan` | 用户自定义组件 |
| 构造函数自动注入 | Bean 间依赖 |

### 5.3 ObjectProvider
- `ObjectProvider<T>` — 用于注入**可选**或**多实现**的 Bean，优先于 `@Autowired(required = false)`
- 直接注入 `List<T>` — 当明确需要所有实现时
- 单值注入 `T` — 当只有一个实现时
- **禁止** `@Autowired(required = false)` 用于可选依赖——语义不如 `ObjectProvider` 清晰，且在构造函数注入中不优雅

---

## 6. Lombok 使用

| 注解 | 场景 |
|------|------|
| `@Slf4j` | 所有非数据类 |
| `@RequiredArgsConstructor` | 构造函数注入 |
| `@Getter` | 只读（枚举、异常） |
| `@Getter` + `@Setter` | 读写（**ConfigurationProperties 必须用此，不用 @Data**） |
| `@Data` | 实体 DTO |
| `@NoArgsConstructor(access = PRIVATE)` | 常量类 / 单例 |

- 常量类/工具类必须用 `@NoArgsConstructor(access = PRIVATE)` 私有化构造器
- **为什么 ConfigurationProperties 不用 `@Data`**：`@Data` 额外生成 `equals()`/`hashCode()`/`toString()`，配置属性类几乎不需要这些方法，且 `equals`/`hashCode` 若被意外调用（如放入 Set/Map）可能产生非预期行为。Spring Boot 官方推荐 `@Getter` + `@Setter`

---

## 7. Javadoc

- 类/方法/字段级别均需 Javadoc
- 使用 `{@code}`、`{@link}`、`{@literal}` 标签
- `@param`、`@return`、`@throws`、`@see` 必须完整
- `@author` 和 `@since` 标注在类级别
- 语言选择：中文为主 + 关键术语保留英文。若项目可能开源或国际化，用英文

```java
/**
 * 消息发送服务。
 *
 * <p>协调消息过滤、通道选择和实际发送过程。</p>
 *
 * @author xxx
 * @since 2022/1/20
 */
public class MessageSendService { }
```

---

## 8. 测试

### 8.1 目录结构
```
src/test/
├── java/<package>/
│   ├── <Feature>TestApplication.java
│   └── ...
└── resources/
    ├── application.yml
    └── test/*.http
```

### 8.2 测试启动类
- 使用 `@SpringBootApplication` 标注

### 8.3 HTTP 测试
- 使用 `.http` 文件做集成测试（IDEA 原生支持）

---

## 9. 异常处理

- 业务异常继承 `RuntimeException`
- 使用 `@ControllerAdvice` + `@ExceptionHandler` 做全局异常处理
- 错误码集中管理（常量类或枚举），保证唯一性
