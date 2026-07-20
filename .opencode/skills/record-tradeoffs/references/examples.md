# Trade-Off Examples

6 complete examples covering all 4 source types and various resolution paths.

---

## Example 1: deliberate — Context Window Skipping Error Handling

**Scenario**: Agent's context window near limit. Skips comprehensive error handling in a service method.

```yaml
---
source: deliberate
severity: medium
status: resolved
created: 2026-07-17
updated: 2026-08-01
author: "Claude"
tags: ["tradeoff"]

intended_approach: "try-catch with exponential backoff retry + circuit breaker"
obstacle: "Context window at ~85%, cannot fit proper error handling scaffolding"
obstacle_type: context-window
actual_approach: "Simple try-catch with log-and-rethrow, no retry"
gap_assessment: "Transient failures (network blip, DB timeout) will propagate to caller instead of being retried. Circuit breaker absent means cascading failure risk."

revisit_by: 2026-08-01
revisit_trigger: "New session with fresh context window"

reviewed_by: "Gemini (review bot)"
review_notes: "Obstacle verified from session context window logs. Severity appropriate — this is a non-critical internal service."
confidence: high
intended_approach_verified: true

arbitration:
  type: swarm_vote
  vote_details:
    quorum: 3
    votes:
      - {agent: "Claude", vote: "accept", reasoning: "Self-evident benefit"}
      - {agent: "Gemini", vote: "accept", reasoning: "Medium severity, reasonable deferral"}
      - {agent: "GPT", vote: "accept", reasoning: "Error rates are low on this path, acceptable risk"}
    result: "accepted"

resolution:
  type: resolved
  resolved_by: "Claude (next session)"
  resolved_in: "commit a1b2c3d"
---

# 20260717__skip-error-handling-context-window

> **Source**: deliberate | **Severity**: medium | **Status**: resolved
> **Revisit by**: 2026-08-01

## 1. What Was Intended
Comprehensive error handling with exponential backoff retry (3 attempts, 1s/2s/4s delay) and a circuit breaker (5 failures in 60s → open for 30s).

## 2. What Blocked It
Context window at ~85% (170K/200K tokens). Implementing proper retry + circuit breaker + tests would consume ~8K tokens of scaffolding code. Session has 3 more features to implement.

## 3. What Was Done Instead
Basic try-catch that logs the error and rethrows. No retry logic, no circuit breaker.

## 4. Gap Assessment
- Functional: Transient failures propagate to caller
- Performance: N/A (correctness issue, not performance)
- Security: None
- Maintainability: Error handling scattered across callers instead of centralized

## 5. Revisit Plan
When entering the project in a fresh session with >50% context window remaining, implement proper error handling.

## 6. Affected Locations
| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| OrderService.java | 142-158 | @tradeoff(deliberate, medium, revisit=2026-08-01) | Missing retry + circuit breaker |

## 7. Review Notes
Gemini (review bot): Session logs confirm context window at 171K tokens. Intended approach validated against project coding standards. Severity confirmed.

## 8. Arbitration Decision
Swarm vote 3:0 accepted. revisit_by set to 2026-08-01.

## 9. Resolution
2026-08-01: Error handling implemented in fresh session. Added RetryTemplate with exponential backoff and Resilience4j CircuitBreaker. @tradeoff annotation removed. Tests pass.
```

---

## Example 2: uncertain — API Parameter Unit Ambiguity

**Scenario**: Agent uses a third-party scheduling API but is unsure whether the delay parameter is in seconds or milliseconds. Training data may be outdated.

```yaml
---
source: uncertain
severity: high
status: accepted
created: 2026-07-17
updated: 2026-07-18
author: "GPT"
tags: ["tradeoff"]

intended_approach: "Verified API behavior — confirm units via live docs or testing"
obstacle: "API documentation inaccessible (vendor portal down). Could not verify at runtime."
obstacle_type: missing-info
actual_approach: "Assumed milliseconds based on similar APIs, wrapped with explicit conversion"
gap_assessment: "If the assumption is wrong, all scheduled tasks will fire at wrong times — potentially minutes/hours off. Business impact: high (time-sensitive order processing)."

revisit_by: 2026-07-20
revisit_trigger: "Verify API docs when vendor portal is accessible OR write an integration test"

reviewed_by: "Claude (review bot)"
review_notes: "Checked vendor documentation cache — parameter IS in seconds, not milliseconds. The code is WRONG."
confidence: high
intended_approach_verified: true

arbitration:
  type: swarm_vote
  vote_details:
    quorum: 3
    votes:
      - {agent: "Claude", vote: "reject", reasoning: "This is wrong. Unit is seconds. Must fix immediately."}
      - {agent: "Gemini", vote: "reject", reasoning: "HIGH severity with confirmed wrong implementation. Cannot defer."}
      - {agent: "GPT", vote: "accept", reasoning: "I implemented it defensively — the conversion wrapper handles either unit"}
    result: "rejected"  # 2:1 reject
---

# 20260717__schedule-api-units-uncertain

> **Source**: uncertain | **Severity**: high | **Status**: rejected
> **Revisit by**: N/A (rejected — must fix now)

## 1. What Was Intended
Call `scheduler.schedule(delay)` with confirmed unit type (seconds vs milliseconds).

## 2. What Blocked It
Vendor API portal was down during implementation. Training data ambiguous — different versions of the SDK used different units.

## 3. What Was Done Instead
Assumed milliseconds. Wrapped with `delay * 1000` conversion. Added defensive comment.

## 4. Gap Assessment
Review bot (Claude) checked vendor docs cache — the API accepts SECONDS. Current code multiplies by 1000, making delays 1000x too long. A 5-second task would fire after 5000 seconds (83 minutes).

## 5. Revisit Plan
N/A — Rejected by Arbiter. Must fix immediately.

## 6. Affected Locations
| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| TaskScheduler.java | 56-60 | @tradeoff(uncertain, high, revisit=2026-07-20) | Delay values 1000x wrong |

## 7. Review Notes
Claude (review bot): Vendor docs confirm seconds. Implementation is wrong. Severity should be high — order processing timing is business-critical.

## 8. Arbitration Decision
Swarm vote 2:1 rejected. Converted to blocking issue. Must fix before merge.

## 9. Resolution
(pending — fix in progress)
```

---

## Example 3: divergence — ReentrantLock Degraded to synchronized

**Scenario**: Agent planned to use ReentrantLock with timeout, but Maven central was unreachable from the CI environment.

```yaml
---
source: divergence
severity: high
status: resolved
created: 2026-07-17
updated: 2026-07-24
author: "Claude"
tags: ["tradeoff"]

intended_approach: "java.util.concurrent.locks.ReentrantLock with tryLock(500ms)"
obstacle: "Maven Central unreachable from CI environment. Cannot resolve concurrent-locks dependency."
obstacle_type: dependency-missing
actual_approach: "synchronized block — no timeout support, indefinite blocking"
gap_assessment: >
  Performance: No timeout means a stalled thread holding the lock blocks
  all other threads indefinitely. Risk of thread starvation under load.
  Functionality: Correct under normal operation, degraded under failure.

revisit_by: 2026-07-24
revisit_trigger: "Maven dependency resolution restored in CI OR alternative lock library available"

reviewed_by: "Gemini (review bot)"
review_notes: "Maven error logs confirm: 'Could not resolve: concurrent-locks:1.2.0'. ReentrantLock is the correct intended approach."
confidence: high
intended_approach_verified: true

arbitration:
  type: human
  vote_details: {}

resolution:
  type: resolved
  resolved_by: "GPT (resolver session)"
  resolved_in: "commit d4e5f6g"
---

# 20260717__synchronized-fallback-maven-unreachable

> **Source**: divergence | **Severity**: high | **Status**: resolved
> **Revisit by**: 2026-07-24

## 1. What Was Intended
```java
private final Lock lock = new ReentrantLock();
// ...
if (lock.tryLock(500, TimeUnit.MILLISECONDS)) {
    try { /* critical section */ }
    finally { lock.unlock(); }
}
```

## 2. What Blocked It
Maven build failed:
```
Could not resolve dependency: com.example:concurrent-locks:1.2.0
```
CI environment has restricted network access. Maven Central not in allowlist.

## 3. What Was Done Instead
```java
synchronized (this) {
    // critical section — no timeout, blocks indefinitely
}
```

## 4. Gap Assessment
- Performance: No timeout → one stalled thread blocks all others indefinitely
- Functionality: Correct under normal operation; degraded under lock contention
- Risk: Thread starvation under concurrent load scenarios >50 TPS

## 5. Revisit Plan
When Maven Central access is restored in CI (estimated 2026-07-24 per infra team).

## 6. Affected Locations
| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| CounterService.java | 42-52 | @tradeoff(divergence) | Thread safety downgrade |
| CacheManager.java | 108-120 | @tradeoff(divergence) | Thread safety downgrade |

## 7. Review Notes
Gemini (review bot): Maven error confirmed. ReentrantLock is correct intended approach. Severity high — but acceptable given the constraint is external and timeframe is short.

## 8. Arbitration Decision
Human reviewed 2026-07-17. Accepted with revisit_by 2026-07-24 (1 week).

## 9. Resolution
2026-07-22: Maven access restored. GPT (resolver session) replaced synchronized blocks with ReentrantLock in both files. Tests pass. @tradeoff annotations removed.
```

---

## Example 4: divergence — Security-Related Fallback Rejected

**Scenario**: Agent skipped XSS filtering due to time pressure. Swarm vote accepted 2:1, but human overrode due to security domain.

```yaml
---
source: divergence
severity: critical
status: rejected
created: 2026-07-17
updated: 2026-07-17
author: "Claude"
tags: ["tradeoff", "security"]

intended_approach: "OWASP HTML sanitizer on all user-generated content input"
obstacle: "Time pressure — session time limit approaching, sanitizer integration requires config"
obstacle_type: time-pressure
actual_approach: "No XSS filtering — raw user input passed to response"
gap_assessment: "CRITICAL: Unfiltered user input in response = XSS vulnerability. Attackers can inject arbitrary JavaScript."

revisit_by: 2026-07-18
revisit_trigger: "Immediately in next session"

reviewed_by: "GPT (review bot)"
review_notes: "This is an XSS vulnerability. Cannot be a trade-off — must be fixed before ANY deployment."
confidence: high
intended_approach_verified: true

arbitration:
  type: human
  vote_details: {}
  # Swarm vote was bypassed due to security domain override.
  # Human directly reviewed and rejected — must fix now.

resolution: {}
---

# 20260717__skip-xss-filtering-time-pressure

> **Source**: divergence | **Severity**: critical | **Status**: rejected
> **Revisit by**: N/A (rejected)

## 1. What Was Intended
Integrate OWASP HTML Sanitizer to filter all user-generated content before rendering in response pages.

## 2. What Blocked It
Session time limit (~5 min remaining). Sanitizer configuration requires reading OWASP policy files + wiring into Spring filter chain. Estimated 15 min to implement properly.

## 3. What Was Done Instead
User input rendered unsanitized:
```java
model.addAttribute("userContent", request.getParameter("comment"));
```

## 4. Gap Assessment
**CRITICAL**: XSS vulnerability. Any user can inject `<script>` tags into comment field. Will execute in other users' browsers when viewing the page.

## 5. Revisit Plan
N/A — Rejected.

## 6. Affected Locations
| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| CommentController.java | 34-37 | @tradeoff(divergence) | XSS vulnerability |

## 7. Review Notes
GPT (review bot): Confirmed XSS vector. This MUST be blocked. Flagged for immediate human review with security domain override.

## 8. Arbitration Decision
**HUMAN OVERRIDE (security domain)**. Rejected. Cannot defer. Must implement XSS filtering before merge. PR blocked.

## 9. Resolution
(pending — blocking issue created, must fix before PR can merge)
```

---

## Example 5: discovered — Long Parameter List Detected by Review Bot

**Scenario**: Review bot detects a method with 8 parameters, suggesting a Builder pattern should have been used.

```yaml
---
source: discovered
severity: medium
status: absorbed
created: 2026-07-17
updated: 2026-08-15
author: "review-bot-gemini"
tags: ["tradeoff"]

intended_approach: "Builder pattern or parameter object"
obstacle: "Not specified by original creator (no @tradeoff annotation was present)"
obstacle_type: other
actual_approach: "8-parameter constructor — positional, error-prone"
gap_assessment: "Readability degraded. Risk of positional argument swap bugs. Medium maintainability impact."

revisit_by: 2026-08-15
revisit_trigger: "Next refactoring session for this module"

detected_by: "Gemini (review bot)"
detected_in: "PR #142, diff src/main/java/OrderRequest.java:12-19"

reviewed_by: "Claude (follow-up review)"
review_notes: "8 params confirmed. 3 of them are optional defaults. Builder pattern would be better."
confidence: high
intended_approach_verified: true

arbitration:
  type: human

resolution:
  type: absorbed
  resolved_by: "human (vicat)"
  target:
    type: agents
    path: "doc/AGENTS.md"
    summary: "Added to AGENTS.md coding standards: methods with >5 parameters should use Builder pattern. Agent must prompt user before creating parameter-heavy constructors."
---

# 20260717__long-param-list-builder-pattern

> **Source**: discovered | **Severity**: medium | **Status**: absorbed → AGENTS.md
> **Revisit by**: N/A (absorbed)

## 1. What Was Intended
Builder pattern for constructing OrderRequest objects with optional fields.

## 2. What Blocked It
Original agent did not mark this as a trade-off. Detected by review bot heuristic scan.

## 3. What Was Done Instead
```java
public OrderRequest(String customerId, String productId, int quantity,
                     String couponCode, String shippingMethod,
                     boolean giftWrap, String notes, String promoCode) {
    // positional — 3 of these are optional defaults
}
```

## 4. Gap Assessment
Medium readability/maintainability impact. 3 optional parameters at the end make call sites confusing. Risk: giftWrap boolean and notes String could be swapped positionally.

## 5. Revisit Plan
N/A — absorbed into AGENTS.md coding standards.

## 6. Affected Locations
| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| OrderRequest.java | 12-19 | (none — discovered) | Parameter-heavy constructor |

## 7. Review Notes
Gemini detected. Claude confirmed. Human agreed with severity.

## 8. Arbitration Decision
Human decided: "Not worth refactoring this specific class (it's an internal DTO). But this pattern should be prevented going forward."

## 9. Resolution
Absorbed into `doc/AGENTS.md`:
> Methods with >5 parameters MUST use Builder pattern or parameter object. Agent must flag parameter-heavy signatures and suggest refactoring before committing.
```

---

## Example 6: deliberate — Hardcoded Config Values, Promoted to ADR

**Scenario**: Agent hardcodes configuration values because the config center is not yet deployed. Over time, this becomes the de facto pattern across the codebase. Arbiter decides to formalize it as an architecture decision.

```yaml
---
source: deliberate
severity: medium
status: promoted
created: 2026-07-17
updated: 2026-09-01
author: "Claude"
tags: ["tradeoff"]

intended_approach: "Spring Cloud Config for centralized configuration management"
obstacle: "Config center service not yet deployed in staging environment"
obstacle_type: env-incompatible
actual_approach: "Configuration values hardcoded in application.yml, duplicated across 8 microservices"
gap_assessment: "Any config change requires 8 PRs + 8 deployments. Risk of drift between services."

revisit_by: 2026-09-01
revisit_trigger: "Config center GA deployment"

reviewed_by: "GPT (review bot)"
review_notes: "Config center deployment is delayed (Q4 2026). This is becoming a long-term pattern."
confidence: high
intended_approach_verified: true

arbitration:
  type: human

resolution:
  type: promoted
  target:
    type: adr
    path: "doc/adr/004-centralized-config-strategy.md"
    summary: "ADR-004: Centralized Configuration Strategy — documents the decision to use Spring Cloud Config, the migration plan from hardcoded values, and the interim duplication pattern as accepted technical debt."
---

# 20260717__hardcoded-config-pending-config-center

> **Source**: deliberate | **Severity**: medium | **Status**: promoted → ADR-004
> **Revisit by**: N/A (now tracked by ADR lifecycle)

## 1. What Was Intended
Spring Cloud Config server with Git backend. All microservices pull configuration at startup.

## 2. What Blocked It
Config center service has not passed staging certification. Not available for integration.

## 3. What Was Done Instead
Configuration values hardcoded in each service's application.yml. Duplicated across 8 services.

## 4. Gap Assessment
- Operational: Config change = 8 PRs + 8 deployments
- Reliability: Risk of config drift between services
- Audit: No change history for configuration values

## 5. Revisit Plan
N/A — Promoted to ADR. Tracked by ADR lifecycle.

## 6. Affected Locations
| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| */application.yml | various | @tradeoff(deliberate) | 8 services use duplicated config |

## 7. Review Notes
GPT (review bot): Config center delayed to Q4. This is becoming permanent. Suggest promote to ADR.

## 8. Arbitration Decision
Human decided: "Config center won't be ready for 6+ months. This is now an architecture decision, not a temporary trade-off. Promote to ADR."

## 9. Resolution
Promoted to [ADR-004: Centralized Configuration Strategy](../adr/004-centralized-config-strategy.md). ADR documents: current duplication as accepted debt, migration timeline when config center is GA-ready, interim governance for config changes.
```
