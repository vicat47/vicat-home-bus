# Tasks: HomeBus v0.1 MVP

## Phase 0: 基础设施

- [x] T-001: 数据模型 `homebus/models.py` — ErrorCode, ErrorDetail, ErrorResponse, EventItem, CreateEventRequest, EventStatusResponse, ExecutionItem, QueryRequest, QueryResponse, AdapterHealth, HealthResponse, SubTask
- [x] T-002: 数据库 `homebus/database.py` — init_db, insert_event, get_event, update_event_status, insert_executions, update_execution, get_executions; WAL mode; migration V001
- [x] T-003: 配置管理 `homebus/config.py` — ApiConfig, DatabaseConfig, GrocyConfig, BeancountConfig, HomeboxConfig, AdaptersConfig, CliConfig, HomeBusConfig; load_config分层加载; discover_config_path XDG发现

## Phase 1: 适配器层

- [x] T-004: Adapter Base `homebus/adapters/base.py` — ActionMeta dataclass; AdapterBase ABC (execute, health_check, list_actions)
- [x] T-005: Grocy Adapter `homebus/adapters/grocy.py` — GrocyAdapter(AdapterBase); add_stock(name→id resolution+cache), consume_stock, stock_query; health_check; fail-fast on unknown products
- [x] T-006: Beancount Writer `homebus/adapters/beancount_writer.py` — generate_entry(#homebus tag+meta), write_entry(按年/月), find_entry_by_event_id, delete_entry_by_event_id, run_bean_check, git_commit
- [x] T-007: Beancount Adapter `homebus/adapters/beancount.py` — BeancountAdapter(AdapterBase); record_expense(wraps writer), delete_entry; health_check(ledger_path+bean-check); 幂等检查
- [x] T-008: Homebox Adapter `homebus/adapters/homebox.py` — HomeboxAdapter(AdapterBase); create_asset, delete_asset(404→success); health_check

## Phase 2: 注册表与核心引擎

- [x] T-009: 路由注册表 `homebus/registry.py` — CategoryRoute, StoreRoute dataclasses; Registry.load(TOML), get_category_route, get_store_route; 容错(空注册表)
- [x] T-010: 调度引擎 `homebus/dispatch.py` — DispatchEngine(registry); derive_subtasks(purchase→Grocy L0+Beancount/Homebox L1, consume→Grocy L0); 注入品类/渠道路由参数
- [x] T-011: 任务执行器 `homebus/executor.py` — TaskExecutor(adapters,db); execute(event_id,subtasks)→DAG分层并发; 失败→cancel in-flight→Saga; 超时+重试
- [x] T-012: Saga 补偿器 `homebus/saga.py` — COMPENSATION_MAP{(grocy,add_stock)→consume_stock, (beancount,record_expense)→delete_entry, (homebox,create_asset)→delete_asset}; compensate顺序执行; 404幂等
- [x] T-013: 结果聚合器 `homebus/aggregator.py` — Aggregator(db); aggregate(event_id)→success/compensated/failed; 更新events状态

## Phase 3: API 层

- [x] T-014: 事件校验器 `homebus/validators.py` — validate_event(db,request)→Schema校验+幂等检查; event_id自动生成
- [x] T-015: API Server `homebus/api.py` — FastAPI app; POST /v1/events(校验→写events→BackgroundTasks调度); GET /v1/events/{id}(查询events+executions); POST /v1/query(路由到adapter); GET /v1/health(聚合adapter状态); 统一ErrorResponse
- [x] T-016: 查询路由 `homebus/query_router.py` — QueryRouter(adapters,db); route(target,operation,params)→adapter; 写events(intent=query)

## Phase 4: CLI

- [x] T-017: CLI 入口 `cli/homebus.py` — Click命令组; publish(--body/--file); status(--event-id,--watch,--timeout); query(--target,--operation,--params); health; init(--force生成config+registry+.env.example); 配置发现; JSON→stdout,错误→stderr

## Phase 5: 配置模板与部署

- [x] T-018: 迁移文件 `homebus/migrations/V001__initial_schema.sql` — DDL(events+executions表)
- [x] T-019: 部署配置 — Dockerfile(python:3.11-slim+uv); docker-compose.yml(HomeBus+mock); config.toml.example; .env.example

## Phase 6: 测试

- [x] T-020: 单元测试 `tests/test_*.py` — models, database, validators, dispatch, executor, saga, aggregator, adapters(mock HTTP), registry, CLI(mock API)
- [ ] T-021: 集成测试 `tests/test_integration.py` — 完整purchase流程; 幂等重复提交; Saga补偿流程(Grocy成功+Beancount失败→回滚); 健康检查聚合
- [ ] T-022: 端到端测试 — 启动API Server→CLI publish→status --watch→确认完成; CLI query; CLI health
