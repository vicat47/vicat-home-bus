---
name: record-research
description: >-
  Activate when the user asks to research technologies, compare solutions, evaluate third-party
  libraries/frameworks/tools, generate research reports, or mentions 技术调研、方案对比、调研报告、
  research、选型分析、第三方库评估、开源项目调研. Supports domain-based organization, document
  lifecycle state machine, research TDD (hypothesis → validation), grill-me pre-research interview,
  and parallel multi-candidate evidence collection.
category: research
tags: ["research", "technology", "comparison", "report", "domain-organization", "lifecycle", "tdd", "state-machine", "grill-me", "parallel"]
---

# Record Research — Technology Research & Validation Reports

Document technology research and validation reports in the `doc/research/` directory. Supports domain-based organization, a 7-state document lifecycle, research TDD (hypothesis → evidence → validation), a grill-me pre-research interview phase, and parallel multi-candidate evidence collection.

**Dependencies**: Load `doc-structure` for directory infrastructure, progressive indexing, and naming conventions.

**Cross-reference**: `record-adr` — research often feeds ADRs; ADRs may cite research as evidence. `record-tech-radar` — research reports inform radar assessments. `record-aha-moments` — research may start as an aha moment.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

---

## 1. Document Lifecycle State Machine

Every research document has a `status` field in its YAML frontmatter. The agent MUST update this field as the research progresses.

```
                  ┌─────────┐
                  │  draft  │  ← Hypothesis defined, scope agreed (post grill-me),
                  └────┬────┘    no evidence collected yet
                       │
                       ▼
                 ┌───────────┐
         ┌───────│in-progress│───────┐
         │       └─────┬─────┘       │
         │             │             │
         ▼             ▼             ▼
   ┌──────────┐  ┌───────────┐  ┌───────────┐
   │cancelled │  │ in-review │  │cancelled  │  ← Abandoned mid-research
   └──────────┘  └─────┬─────┘  └───────────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
        ┌──────────┐ ┌───────────┐ ┌───────────┐
        │ complete │ │  draft    │ │cancelled  │  ← Human rejected, back to draft
        └────┬─────┘ └───────────┘ └───────────┘
             │
        ┌────┼────┐
        ▼         ▼
  ┌──────────┐ ┌───────────┐
  │superseded│ │ archived  │
  └──────────┘ └───────────┘
```

### State Definitions

| State | Meaning | Trigger | Agent Action |
|-------|---------|---------|--------------|
| `draft` | Hypothesis defined, scope agreed, no evidence collected | Post grill-me | Update frontmatter: `status: draft` |
| `in-progress` | Evidence collection active | First evidence gathered | Update frontmatter: `status: in-progress` |
| `in-review` | Report drafted, pending human validation | Report generation complete | Update frontmatter: `status: in-review`; ask user to review |
| `complete` | Human validated, conclusions accepted | User confirms conclusions | Update frontmatter: `status: complete` |
| `superseded` | Replaced by newer research on same topic | Newer research completed | Update OLD document: `status: superseded`; add link to new doc |
| `archived` | No longer relevant (tech deprecated, direction changed) | Explicit user request | Update frontmatter: `status: archived` |
| `cancelled` | Research abandoned before completion | User cancels or timeout | Update frontmatter: `status: cancelled`; add reason in note |

### State Transition Rules

1. **Only one document per topic in `in-progress` or `in-review`** — before starting new research, check that no active document on the same topic exists
2. **When a document becomes `complete`**, check if it supersedes any existing document and update accordingly
3. **When a document becomes `superseded`**, add a `superseded_by` field in its frontmatter pointing to the new document
4. **Documents in `cancelled` or `archived` state are excluded from "active" document counts**

---

## 2. Smart Loading Strategy (防上下文膨胀)

When the agent enters the `doc/research/` directory with many documents, use this **triage-first** loading strategy instead of loading everything:

```
STEP L.1: Read doc/research/README.md first
STEP L.2: Scan the status column in the index table
STEP L.3: Prioritize loading:
          - in-progress (active research — always load)
          - in-review (pending human review — always load)
          - complete (recent 3 by date — load on demand)
STEP L.4: Skip unless explicitly referenced:
          - archived, superseded, cancelled, draft (stale)
STEP L.5: If a domain has > 10 documents, only load the 5 most recent
```

**Rationale**: Context window is finite. Loading stale documents wastes tokens and degrades reasoning quality. Clear context rather than compress — each research session starts from a stable, minimal context base.

---

## 3. 触发条件 / When to Use

- 用户要求调研某个技术、对比技术方案、评估第三方库
- User says "research X", "compare A vs B", "evaluate library Y"
- 查找开源项目、分析 GitHub 仓库、收集技术流行度数据
- 生成标准化调研报告
- 验证代码行为、调查 bug 根因（code-verify domain）

---

## 4. 完整工作流 / Workflow

### Phase 0: Grill-Me — 建立共同设计概念

**Purpose**: Before any data collection, AI interrogates the user to establish shared understanding of the research scope, constraints, and success criteria. This prevents "AI didn't research what I wanted" — the #1 failure mode.

**Trigger**: Always. This phase is mandatory for all new research.

**Interview Questions** (ask ONE at a time, wait for user response):

```
Q1. 调研的决策边界是什么？
    → 选型范围（必须考虑哪些方案？排除哪些方案？）
    → Recommended answer: [your inference based on context]

Q2. 约束条件有哪些？
    → 技术约束（语言/框架/协议限制）
    → 组织约束（团队技能、维护成本、许可证合规）
    → 时间约束（deadline、分阶段引入？）
    → Recommended answer: [your inference]

Q3. 优先级排序是什么？
    → 性能 > 社区活跃度 > 易用性 > 许可证 > ...？
    → Recommended answer: [your inference]

Q4. 成功标准是什么？
    → 调研达到什么状态可以被认为"完成"？
    → 结论被采纳的标志是什么？
    → Recommended answer: [your inference]
```

**Q5 (conditional)**: If researching 3+ candidates or the topic is complex:
```
Q5. 是否需要并行多智能体调研？
    → 如果候选方案之间独立，建议并行收集数据以提升效率
```

**Output of Phase 0**: A brief **Research Brief** (5-10 lines) summarizing the agreed scope, constraints, priorities, and success criteria. This brief is recorded at the top of the research report.

**After Phase 0**: Set document status to `draft`.

---

### Phase 1: Load Context — 加载项目上下文

```
STEP 1.1: Read doc/glossary.md to align terminology
           → Use project-defined terms consistently throughout the report
           → If new domain terms discovered during research, suggest adding to glossary

STEP 1.2: Read doc/research/README.md to understand existing research landscape
           → Check for active documents (in-progress, in-review) on related topics
           → Note the smart loading strategy (Section 2)
```

---

### Phase 2: Regression Check — 回归检查

```
STEP 2.1: Search for duplicate/overlapping topics:
          grep -rli "<keyword1>\|<keyword2>" doc/research/ 2>/dev/null

STEP 2.2: If exact match found → UPDATE existing document, do NOT duplicate

STEP 2.3: If partial overlap → reference existing document in the new report's
          "Related Research" section

STEP 2.4: If no overlap → proceed to Phase 3
```

---

### Phase 3: Define Hypotheses — Research TDD

**Purpose**: Before collecting evidence, write falsifiable hypotheses. This prevents confirmation bias and ensures research conclusions are evidence-backed.

**Rules**:
- Write 1-3 hypotheses per research topic
- Each hypothesis MUST be falsifiable (can be proven wrong by evidence)
- Define the validation method for each hypothesis BEFORE collecting data

**Hypothesis Format**:

```markdown
## Hypotheses

### H1: [Statement]
**Claim**: We hypothesize that [specific, measurable claim]
**Validation Method**: [How this will be verified — benchmark, code PoC, docs analysis, community survey]
**Threshold**: [What result confirms the hypothesis vs refutes it]

### H2: [Statement]
...
```

**Examples**:
- Good: "ClickHouse 在 1000 万行 OLAP 查询场景下比 Doris 快 30% 以上" (measurable, falsifiable)
- Bad: "ClickHouse 比 Doris 好" (vague, not falsifiable)

**After Phase 3**: Update document status to `in-progress`.

---

### Phase 4: Collect Evidence — 收集证据

#### 4A. Third-Party Library/Tool Research (web-search domain)

For research involving external libraries, frameworks, or tools, collect data from multiple sources in parallel:

```
GitHub API (use webfetch or gh CLI):
  - GET https://api.github.com/repos/{owner}/{repo}
  - GET https://api.github.com/repos/{owner}/{repo}/releases?per_page=5
  - GET https://api.github.com/repos/{owner}/{repo}/tags?per_page=10
  - GET https://api.github.com/repos/{owner}/{repo}/commits?per_page=10

包管理器:
  - Java/Maven: https://mvnrepository.com/artifact/{group}/{artifact}
  - Node/npm: https://www.npmjs.com/package/{package}
  - Python/PyPI: https://pypi.org/project/{package}

官方文档:
  - Use context7_query-docs for up-to-date API documentation
  - Use webfetch for README, CHANGELOG, migration guides

社区信号:
  - GitHub Issues: open/closed ratio, response time
  - Stack Overflow: question frequency and answer quality
  - Recent commits: is the project actively maintained?
```

**If no network access**: Ask user to provide the above data or confirm you should skip external data collection.

#### 4A-2: Source Code Deep Dive (源码深潜)

When hypotheses require implementation-level verification (API internals, code patterns, edge case handling, default configurations), download the project's tagged source code for direct inspection.

**When to use**:
- Hypothesis involves implementation details not covered by docs (e.g., "how does the library handle connection pooling?")
- Need to verify error handling patterns, default configurations, or thread-safety claims
- Want to inspect dependency tree or architecture patterns beyond README

##### 4A-2a: GitHub Tag Archive Download

Download source code from a specific Git tag (release version).

**Before downloading**: Try browsing the repo structure via GitHub API first (`GET /repos/{owner}/{repo}/contents/{path}`). Only download the full archive when API browsing is insufficient (e.g., need to grep across many files).

**Storage**: Extract to `./tmp/{repo}-{tag}/` inside the project workspace (no tool-approval needed for file reads). Ensure `tmp/` is in `.gitignore`.

```powershell
# 1. Determine owner, repo, tag from Phase 4A GitHub API results
$owner = "spring-projects"; $repo = "spring-boot"; $tag = "v3.3.0"

# 2. Ensure tmp/ is gitignored
if (-not (Test-Path ".gitignore")) { New-Item ".gitignore" -ItemType File }
if (-not (Select-String -Path ".gitignore" -Pattern "^tmp/$" -SimpleMatch -Quiet)) {
    Add-Content ".gitignore" "`ntmp/"
}

# 3. Download the source archive (use proxy in China for speed)
$url = "https://gh-proxy.com/https://github.com/$owner/$repo/archive/refs/tags/$tag.zip"
$zip = "$env:TEMP\$repo-$tag.zip"
Invoke-WebRequest -Uri $url -OutFile $zip

# 4. Extract to workspace tmp/ directory
$dest = "tmp\$repo-$tag"
New-Item -ItemType Directory -Path $dest -Force
# Windows: if path-too-long errors occur, ask user to enable long path support:
#   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
#   Ref: https://learn.microsoft.com/zh-cn/windows/win32/fileio/maximum-file-path-limitation
Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force

# 5. Remove the zip, keep extracted source
Remove-Item -Force $zip
```

```bash
owner="spring-projects"; repo="spring-boot"; tag="v3.3.0"

# Ensure tmp/ is gitignored
test -f .gitignore || touch .gitignore
grep -q "^tmp/$" .gitignore || echo "tmp/" >> .gitignore

# Download and extract
url="https://gh-proxy.com/https://github.com/${owner}/${repo}/archive/refs/tags/${tag}.zip"
zipf="/tmp/${repo}-${tag}.zip"; dest="tmp/${repo}-${tag}"
mkdir -p "$dest"
curl -sSL -o "$zipf" "$url"
unzip -q "$zipf" -d "$dest"
rm -f "$zipf"
# Note: extracted dir is nested — actual sources under $dest/$repo-$tag/
```

Then use `Read` or `glob` to explore key source files.

**After extraction**: Update `tmp/AGENTS.md` index (see Section 4A-2d).

##### 4A-2b: Maven Source JAR Download

For Java/Maven projects, download `-sources.jar` directly from Maven Central. **Prefer direct URL download** — it works everywhere without a local pom.xml. Reserve `mvn dependency:sources` for when you are inside the target Maven project and already have its pom.xml configured.

```powershell
# 1. Determine groupId, artifactId, version from Phase 4A package manager data
$groupPath = "com/alibaba"; $artifact = "fastjson2"; $version = "2.0.53"
$groupSlash = $groupPath -replace '\.', '/'

# 2. Ensure tmp/ is gitignored (skip if already done)
if (-not (Test-Path ".gitignore")) { New-Item ".gitignore" -ItemType File }
if (-not (Select-String -Path ".gitignore" -Pattern "^tmp/$" -SimpleMatch -Quiet)) {
    Add-Content ".gitignore" "`ntmp/"
}

# 3. Fetch sources jar from Maven Central
$srcUrl = "https://repo1.maven.org/maven2/$groupSlash/$artifact/$version/$artifact-$version-sources.jar"
$srcJar = "$env:TEMP\$artifact-$version-sources.jar"
Invoke-WebRequest -Uri $srcUrl -OutFile $srcJar

# 4. Extract to workspace tmp/ (jar is a zip archive)
$dest = "tmp\$artifact-$version"
New-Item -ItemType Directory -Path $dest -Force
Expand-Archive -LiteralPath $srcJar -DestinationPath $dest -Force
Remove-Item -Force $srcJar
```

```bash
groupPath="com/alibaba"; artifact="fastjson2"; version="2.0.53"
groupSlash="${groupPath//.//}"

test -f .gitignore || touch .gitignore
grep -q "^tmp/$" .gitignore || echo "tmp/" >> .gitignore

srcUrl="https://repo1.maven.org/maven2/${groupSlash}/${artifact}/${version}/${artifact}-${version}-sources.jar"
srcJar="/tmp/${artifact}-${version}-sources.jar"
mkdir -p "tmp/${artifact}-${version}"
curl -sSL -o "$srcJar" "$srcUrl"
unzip -q "$srcJar" -d "tmp/${artifact}-${version}"
rm -f "$srcJar"
```

Then use `Read` or `glob` to explore Java source files.

**Alternative via Maven CLI** (only when inside the target Maven project):
```bash
mvn dependency:sources -DincludeGroupIds={group} -DincludeArtifactIds={artifact}
# Sources downloaded to local .m2 repository
```

**After extraction**: Update `tmp/AGENTS.md` index (see Section 4A-2d).

##### 4A-2c: Search Downloaded Source (源码搜索引导)

After extracting source, use targeted searches to find hypothesis-relevant code. Do NOT read files randomly — search first, then read the hits.

**Important**: On Windows, `**\*.java` glob may silently fail on deep directory trees. Narrow the search scope to a specific module directory (e.g., `$dest\agentscope-core\src\main\java\` instead of `$dest\**\*.java`).

```bash
# In the extracted source directory, search for:
# - Key classes / interfaces related to the research question
grep -rn "class.*ConnectionPool" --include="*.java" "$dest"
# - Configuration constants and defaults
grep -rn "DEFAULT_\|default.*=" --include="*.java" "$dest"
# - Annotations indicating entry points
grep -rn "@ConfigurationProperties\|@AutoConfiguration\|@Bean" --include="*.java" "$dest"
# - Error handling patterns
grep -rn "catch\|throw new\|handleError\|onError" --include="*.java" "$dest"
# - Thread safety primitives
grep -rn "synchronized\|volatile\|AtomicReference\|Lock\|ReentrantLock" --include="*.java" "$dest"
```

```powershell
# PowerShell equivalents — narrow to a module subdirectory to avoid glob failures:
$module = "$dest\agentscope-core\src\main\java"
Select-String -Path "$module\*\*.java" -Pattern "class.*ConnectionPool"
Select-String -Path "$module\*\*.java" -Pattern "DEFAULT_|default.*="
Select-String -Path "$module\*\*.java" -Pattern "@ConfigurationProperties|@AutoConfiguration|@Bean"
# For broader searches, iterate over first-level subdirs:
Get-ChildItem -LiteralPath $dest -Directory | ForEach-Object {
    Select-String -Path "$($_.FullName)\src\main\java\**\*.java" -Pattern "synchronized|AtomicReference" 2>$null
}
```

Then `Read` only the files with matching hits to verify evidence.

**Integration with evidence collection**: After downloading and searching source, read key files matching the hypotheses being validated. Focus on:
- Entry-point classes (e.g., auto-configuration, `@SpringBootApplication`, `main()`)
- Configuration classes and property binding
- Core algorithm implementations relevant to the research question
- Default constants and fallback behavior

##### 4A-2d: Maintain `tmp/AGENTS.md` Index

After every download, append a row to `tmp/AGENTS.md` so all temporary resources are traceable.

**On first download** — create the file with the header structure:

```markdown
# tmp/ — Project Temporary Files

> **NOT tracked in git.** Already listed in `.gitignore`.

## Source Archives

| Source | Version | Downloaded | Research Report | Status |
|--------|---------|------------|-----------------|--------|
```

**On each subsequent download** — append one row (agent does this automatically):

```markdown
| agentscope-java | v2.0.0-RC3 | 2026-06-14 | doc/research/web-search/20260614-agentscope.md | active |
```

**When research completes** (Phase 8) — update the row's status:

```markdown
| agentscope-java | v2.0.0-RC3 | 2026-06-14 | doc/research/web-search/20260614-agentscope.md | completed |
```

**Status values**: `active` (research in progress) → `completed` (research done, sources preserved as evidence) → `cleaned` (user manually deleted).

**Manual cleanup** (user-triggered only — never auto-delete):

```powershell
# User runs when a topic is fully archived and source is no longer needed:
Remove-Item -Recurse -Force "tmp/agentscope-java-2.0.0-RC3"
# Then update tmp/AGENTS.md: change status to "cleaned"
```

**Rationale for no-auto-clean**: Research conclusions, ADRs, and tech radar assessments all reference findings from these sources. Deleting sources breaks the evidence chain. Sources persist alongside research documents until the user explicitly decides they are no longer needed.

#### 4B. Code Verification Research (code-verify domain)

For code behavior validation, bug investigation, or existing implementation analysis:

```
STEP 4B.1: Reproduce the behavior → capture logs, metrics, screenshots
STEP 4B.2: Narrow the scope → isolate the minimal reproduction case
STEP 4B.3: Instrument → add logging/tracing to understand the behavior
STEP 4B.4: Document exact commands, configs, and outputs
```

#### 4C. Parallel Multi-Candidate Research (并行多智能体)

When comparing 3+ independent candidate solutions, use parallel sub-agents:

```
For each candidate, spawn a librarian agent in background:

task(
  subagent_type="librarian",
  run_in_background=true,
  load_skills=[],
  description="Research candidate: {name}",
  prompt="Collect evidence for candidate {name} in the context of {research topic}.
          TASK: Gather GitHub stats, version history, community health, key features, known limitations.
          EXPECTED OUTCOME: Structured markdown section with metrics table, pros/cons, and match against hypotheses.
          MUST DO: Only collect verifiable data — no speculation. Cite sources for every claim.
          MUST NOT DO: Make recommendations. This is evidence collection only.
          CONTEXT: Hypotheses to validate: [list H1, H2, H3]. Priority dimensions: [list from grill-me]."
)

// After all agents complete, merge results in Phase 6
```

---

### Phase 5: Validate Hypotheses — 验证假设

For each hypothesis defined in Phase 3:

```
STEP 5.1: Compare collected evidence against the hypothesis threshold
STEP 5.2: Mark each hypothesis as:
          ✅ CONFIRMED — evidence supports the claim
          ❌ REFUTED — evidence contradicts the claim
          ⚠️ INCONCLUSIVE — insufficient evidence to decide
STEP 5.3: If INCONCLUSIVE → document what additional evidence is needed
STEP 5.4: If REFUTED → update the research direction; do NOT cherry-pick evidence
```

---

### Phase 6: Generate Report — 生成调研报告

**Structure**: Use **vertical slices** for multi-candidate research. Each candidate gets its own **complete thin slice** (overview → metrics → hypothesis validation → verdict) within that candidate's section. This allows reading one candidate and making a partial decision even without reading others.

**Template**: Read `skills/record-research/templates/RESEARCH.md` for the full structure.

**Key principles**:
- Each candidate section is self-contained
- Cross-candidate comparison table comes AFTER individual slices
- Final recommendation synthesizes across all candidates
- Every claim links to evidence source

**Report frontmatter requirements**:

```yaml
---
status: in-review        # ← MUST update from in-progress
domain: web-search       # web-search | code-verify
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: [author-name]
tags: ["tag1", "tag2"]
hypotheses:              # Summary of Phase 3 hypotheses
  - id: H1
    claim: "..."
    result: CONFIRMED|REFUTED|INCONCLUSIVE
# ---- Third-party library research ONLY ----
library:                 # Optional — only for third-party lib research
  name: "library-name"
  latest_version: "x.y.z"
  license: "MIT"
  stars: 0
  forks: 0
related:
  adr: "ADR-xxx"
  radar: "tech-name"
  supersedes: "YYYYMMDD-prior-research.md"  # If this doc supersedes another
  superseded_by: "YYYYMMDD-newer-research.md"  # If this doc was superseded
---
```

---

### Phase 7: Human Review — 人在环路质量门

```
STEP 7.1: Present the research report to user
STEP 7.2: Highlight:
          - Hypotheses validation results (confirmed/refuted/inconclusive)
          - Recommendation with rationale
          - Any remaining uncertainties or open questions
STEP 7.3: Ask user:
          1. 结论是否采纳？(Accept / Revise / Reject)
          2. 是否需要补充其他调研维度？
          3. 是否需要基于此调研创建 ADR？
STEP 7.4: On user acceptance → set status to complete
STEP 7.5: On user revision request → set status to draft, return to Phase 0 or Phase 4
STEP 7.6: On user rejection → set status to cancelled, document reason
```

---

### Phase 8: Update Indices & Cross-Reference

```
STEP 8.1: Update doc/research/README.md
          → Add row to the correct domain section with status column
          → Format: | Status | Date | Report | Domain | Description |

STEP 8.2: Update doc/README.md or doc/index.md
          → Increment research document count in global index

STEP 8.3: Cross-reference checks:
          # Does this research justify creating/updating an ADR?
          → If the research recommends a technology choice → suggest record-adr

          # Does this research affect any tech radar assessment?
          grep -rl "<tech-name>" doc/tech-radar/*.md

          # Are there related aha moments?
          grep -rl "<topic>" doc/aha-moments/*.md 2>/dev/null

STEP 8.4: If the research involves a third-party library and a related ADR exists:
          → Update ADR: candidate comparison table, decision status, selection rationale
          → Update ADR revision history

STEP 8.5: If the research involves a third-party library and a related OpenSpec spec exists:
          → Update spec: add technology constraint section with library name, version, dependency config
```

---

## 5. Research Organization — Two Modes

### Mode 1: Flat (no research domains)

Use when the number of research reports is small (< 5) and topics are centralized.

```
doc/research/
├── README.md
├── 20260518-flink-cdc-duplicate-key-verify.md
├── 20260519-mysql-charset-fix.md
└── 20260520-clickhouse-vs-doris-comparison.md
```

### Mode 2: Research Domains (subdirectory structure)

Create a research domain when a topic accumulates **3+ reports** or clearly needs categorization. Domain-internal files still use date-based naming.

```
doc/research/
├── README.md
├── web-search/
│   ├── README.md
│   ├── 20260520-clickhouse-vs-doris-comparison.md
│   ├── 20260520-02-streaming-benchmarks.md
│   └── 20260521-serverless-platform-evaluation.md
└── code-verify/
    ├── README.md
    └── 20260518-flink-cdc-duplicate-key-verify.md
```

**Common domain categories**:
- `web-search` — Internet research, third-party library comparison, external info gathering, technology evaluation
- `code-verify` — Code behavior verification, bug investigation, existing implementation analysis

**Domain creation commands**:
```bash
mkdir -p doc/research/<domain>/
cp skills/doc-structure/templates/README__TEMPLATE.md doc/research/<domain>/README.md
# Then update doc/research/README.md to list the new domain
```

---

## 6. Naming Conventions

**Primary key**: Date (`YYYYMMDD`), extracted from the session date via `date +%Y%m%d`

**Format**: `[domain/]YYYYMMDD[-NN]-kebab-title.md`

| Scenario | Example |
|----------|---------|
| First report of the day (flat) | `20260601-clickhouse-vs-doris-comparison.md` |
| Second report of the day (flat) | `20260601-02-streaming-benchmarks.md` |
| First report of the day (domain) | `web-search/20260601-clickhouse-vs-doris-comparison.md` |
| Second report of the day (domain) | `web-search/20260601-02-streaming-benchmarks.md` |

**Intra-day numbering rule**:
- Without domain: Global intra-day numbering across `doc/research/` root
- With domain: Domain-local intra-day numbering within `doc/research/<domain>/`
- NN only appears when ≥2 reports on same date in the same scope

**Find next intra-day number**:
```bash
# Flat mode
ls doc/research/$(date +%Y%m%d)*.md 2>/dev/null | wc -l
# If count ≥ 1 → next NN = count + 1 (zero-padded to 2 digits)

# Domain mode
ls doc/research/<domain>/$(date +%Y%m%d)*.md 2>/dev/null | wc -l
```

---

## 7. Directory Structure

```
skills/record-research/
├── SKILL.md            # This file
└── templates/
    └── RESEARCH.md     # Research report template
```

---

## 8. Pitfalls / 注意事项

- **Never skip Phase 0 (grill-me)** — the #1 cause of research misalignment is scope ambiguity
- **Never skip Phase 2 (regression check)** — duplicate research wastes time and fragments knowledge
- **Every hypothesis must be falsifiable** — vague claims like "X is better than Y" are not valid hypotheses
- **Prefer vertical slices over horizontal** — each candidate section should be self-contained
- **Clear context, don't compress** — use smart loading (Section 2); don't try to cram all historical research into one context window
- **Human is the quality gate** — Phase 7 is mandatory. Do not auto-accept research conclusions
- **Status field is mandatory** — every research document must have a `status` in its YAML frontmatter
- **Only one active document per topic** — before creating a new report, check for existing `in-progress` or `in-review` documents on the same topic
- **Archive politely** — when a document is `superseded` or `archived`, add a note explaining why
- **Source code download is on-demand, not default** — only download source archives (GitHub zip / Maven sources jar) when hypotheses require implementation-level verification. Prefer API-based directory browsing for initial exploration
- **Always clean up temp downloads** — delete the downloaded zip after extraction. Extracted source in `tmp/` persists as evidence; DON'T auto-delete after research completes. User manually cleans up via `Remove-Item -Recurse -Force tmp/<name>/`
- **Tag over branch** — use Git tags (release versions) for reproducible research. Branches change; tags are immutable
- **Windows path length limit (260 chars)** — Java Maven projects have deep directory trees. Ask user to enable long path support: `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force` (admin required, restart may be needed). Reference: https://learn.microsoft.com/zh-cn/windows/win32/fileio/maximum-file-path-limitation. If user declines, fall back to `C:\tmp\`
- **`**\*.java` glob caveat** — on Windows PowerShell, `Select-String -Path "deep\**\*.java"` may silently return nothing on very deep trees. Narrow scope to module-level directories or iterate over subdirs
- **GitHub download is slow in China** — prepend `https://gh-proxy.com/` to the download URL for faster transfer. Direct GitHub downloads may time out on large repos
