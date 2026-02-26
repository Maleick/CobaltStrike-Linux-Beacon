# Phase 1: Baseline Validation Harness - Research

**Researched:** 2026-02-25
**Domain:** C-based protocol regression harness design for fixture-driven validation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Protocol encode/decode validation passes on **semantic equivalence**, not unconditional byte-for-byte equality.
- Any mismatch against approved fixture expectations is treated as a regression by default (**fail by default**) unless an intentional fixture update is explicitly reviewed and approved.
- Malformed task payload tests must validate **reject + continue loop** behavior (no crash, no uncontrolled termination).
- Regression failures should emit **minimal deterministic diagnostics** (fixture ID, assertion target, stable diff summary).
- Regression suite is expected to run **locally before PR** and in **CI**.
- Suite strategy is **fast local gate + full CI suite**.
- Merge policy is **blocked on regression failure** until fixed or explicitly approved with fixture rationale.
- Default developer output should be **actionable summary first** (deep dump is optional, not default).
- Canonical protocol fixtures are **versioned in repository**.
- Fixture updates require **explicit reviewer approval + rationale** for behavior change.
- Intentional behavior shifts are tracked via **versioned fixture sets**, not silent overwrite of history.
- Fixture inventory must maintain **REQ/success-criteria traceability** (fixture set mapped to REL-01/REL-02 and phase outcomes).

### Claude's Discretion
- Exact local command UX for quick vs full suite entry points.
- Exact fixture file/directory naming conventions and index file layout.
- Optional verbose diagnostics toggle design, provided default output remains compact and deterministic.

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REL-01 | Automated tests validate metadata/packet encoding and decoding against known-good fixtures. | Fixture index schema, semantic comparator strategy, quick/full runner split, and baseline protocol fixtures. |
| REL-02 | Automated tests cover malformed task payload handling and verify no crash conditions. | Malformed task corpus design, parser hardening test matrix, and reject-with-continue assertions. |

</phase_requirements>

<research_summary>
## Summary

Phase 1 should use a fixture-first harness layered on top of existing build/runtime assets in `implant/src/beacon.c`, `implant/src/commands.c`, and `implant/src/crypto.c`. The existing codebase already contains the protocol logic to be exercised; the missing capability is repeatable deterministic validation organized into canonical fixtures and executable test commands.

A practical standard for this repo is to keep harness orchestration lightweight (Python entrypoint + shell wrapper + Makefile targets), with fixture truth stored as versioned artifacts in git. The key architectural requirement is separation of fixture data from assertion logic: fixtures should represent expected semantic fields and parser outcomes, while comparator code enforces semantic equivalence and deterministic fail output.

For malformed task behavior, testing should focus on parser safety invariants rather than output formatting details: no crash, controlled rejection path, and loop continuity assumptions preserved. The strongest risk in this phase is accidental fixture drift; strict review workflow and requirement-traceable fixture indexing mitigates this.

**Primary recommendation:** Build a versioned fixture corpus plus a two-tier regression runner (`quick` local, `full` CI) that enforces semantic-equality protocol checks and reject-with-continue parser guarantees.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GCC + existing Makefile | repo current | Build and compile validation dependencies | Already authoritative build path in `implant/Makefile` |
| Python 3 (stdlib + argparse/json/subprocess) | system current | Deterministic test orchestration and fixture parsing | Already used in repo tooling (`generate-payload/*.py`) and avoids introducing heavy deps |
| POSIX shell wrapper | repo current | Stable quick/full command entrypoint | Simple bridge for local/CI parity and developer ergonomics |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest (optional) | current stable | Structured assertions and test discovery | Use if richer per-case output/reporting is needed |
| jq (optional) | current stable | Fixture sanity checks in CI | Use for JSON lint/validation in pipeline stages |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python stdlib runner | Full pytest-only harness | Better ecosystem tooling but introduces stricter dependency bootstrapping |
| Semantic comparator | Byte-exact golden output | Stronger binary locking but conflicts with explicit semantic-equivalence decision |

**Installation:**
```bash
# Base stack already present in current project setup
# Optional supporting dependency:
python3 -m pip install pytest
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
implant/
├── tests/
│   ├── fixtures/
│   │   └── protocol/
│   │       └── v1/
│   ├── cases/
│   ├── fixture_index.json
│   ├── run_regression.py
│   └── run_regression.sh
└── src/
    ├── beacon.c
    └── commands.c
```

### Pattern 1: Versioned Fixture Contract
**What:** Store protocol fixtures under explicit version directories (`v1`, future `v2`) with index metadata linking fixture IDs to requirements.
**When to use:** Always for regression contract data that must survive implementation refactors.
**Example:**
```json
{
  "fixture_id": "meta_default_http_001",
  "version": "v1",
  "requirements": ["REL-01"],
  "assertion_mode": "semantic"
}
```

### Pattern 2: Two-Tier Execution
**What:** Quick deterministic local suite and expanded CI suite sharing same harness engine.
**When to use:** Always when balancing fast iteration and full confidence.
**Example:**
```bash
bash implant/tests/run_regression.sh --mode quick
bash implant/tests/run_regression.sh --mode full
```

### Anti-Patterns to Avoid
- **Fixture mutability in test code:** embedding expected values directly in assertion code hides contract changes and weakens reviewability.
- **Parser safety checks without loop-continuity assertions:** passing “no crash” alone can still miss control-flow regressions.
- **Verbose-by-default failure logs:** non-deterministic dumps reduce CI signal quality.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Protocol expectation storage | Ad-hoc inline literals per test | Versioned JSON/BIN fixtures + index | Keeps contract reviewable and traceable to requirements |
| Regression command choreography | Manual command sequences in docs only | `run_regression.sh` + `run_regression.py` | Ensures repeatable local/CI behavior |
| Fixture drift decisions | Implicit fixture overwrites | Explicit fixture versioning + review rationale | Prevents accidental baseline redefinition |

**Key insight:** Hand-rolled one-off scripts increase ambiguity; a small explicit harness surface gives deterministic behavior with low maintenance cost.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Fixture Drift Without Intent Tracking
**What goes wrong:** Fixture updates mask regressions as expected behavior.
**Why it happens:** No review gate or requirement mapping for fixture changes.
**How to avoid:** Require fixture update rationale and reviewer sign-off.
**Warning signs:** Frequent fixture-only commits with vague messages.

### Pitfall 2: Semantic vs Byte Assertions Mixed Implicitly
**What goes wrong:** Tests fail/noise due non-critical representation changes.
**Why it happens:** Assertion mode not encoded per fixture.
**How to avoid:** Explicit `assertion_mode` metadata and semantic comparator for REL-01 path.
**Warning signs:** Intermittent failures on equivalent packet semantics.

### Pitfall 3: Parser Tests Ignore Runtime Continuation
**What goes wrong:** Invalid payload rejection appears correct but loop/progress behavior regresses.
**Why it happens:** Tests only assert error code and skip continuity checks.
**How to avoid:** Add continuation invariants to malformed-task cases.
**Warning signs:** Parser tests pass while runtime tasking intermittently stalls.
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from project sources:

### Existing parser layout validation anchor
```c
// Source: implant/src/commands.c
static int validate_task_layout(const uint8_t *task_buffer, size_t task_len, size_t task_header_len, size_t *task_count_out)
{
    // validates header layout and bounds before execution
}
```

### Existing protocol metadata generation anchor
```c
// Source: implant/src/beacon.c
uint8_t* beacon_generate_metadata(beacon_state_t *state, size_t *out_len)
{
    // metadata serialization and field construction
}
```

### Existing build-entry pattern
```makefile
# Source: implant/Makefile
all: directories $(TARGET)
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single monolithic manual regression run | Tiered quick/full deterministic suites | mature current practice | Faster local loops while preserving CI confidence |
| Unstructured fixture blobs | Indexed versioned fixture contracts | mature current practice | Better auditability and safer baseline updates |
| Crash-only parser checks | Safety + continuation invariants | mature current practice | Better detection of control-flow regressions |

**New tools/patterns to consider:**
- Requirement-linked fixture indexing for auditability.
- Mode-specific output (`summary` default, `verbose` opt-in) for reliable CI signal.

**Deprecated/outdated:**
- “Update fixture whenever tests fail” workflows without change rationale.
</sota_updates>

<open_questions>
## Open Questions

1. **How much protocol fixture coverage should be mandatory in Phase 1 vs Phase 2?**
   - What we know: REL-01/REL-02 require core metadata/packet and malformed-task coverage now.
   - What's unclear: exact breadth of command-level packet permutations to include initially.
   - Recommendation: Phase 1 should enforce high-value baseline fixtures; expand breadth in later phases with profile/transport changes.

2. **Should optional pytest dependency be introduced immediately?**
   - What we know: Python stdlib runner is sufficient for deterministic orchestration.
   - What's unclear: whether team prefers richer assertion/reporting from day one.
   - Recommendation: implement stdlib baseline first; add pytest only if signal/reporting needs exceed baseline.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Repository source files: `implant/src/beacon.c`, `implant/src/commands.c`, `implant/Makefile`, `.planning/phases/01-baseline-validation-harness/01-CONTEXT.md`
- Repository planning context: `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/codebase/TESTING.md`

### Secondary (MEDIUM confidence)
- Established fixture-driven and tiered-regression engineering patterns (industry common practice)

### Tertiary (LOW confidence - needs validation)
- None.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: C protocol/task parsing + harness orchestration
- Ecosystem: local build/test orchestration patterns
- Patterns: fixture contracts, quick/full execution tiers, deterministic diagnostics
- Pitfalls: fixture drift, assertion ambiguity, parser continuation gaps

**Confidence breakdown:**
- Standard stack: HIGH - grounded in existing repository tooling
- Architecture: HIGH - directly aligned to phase scope and current code paths
- Pitfalls: HIGH - tied to known concerns in mapped codebase
- Code examples: HIGH - sourced from repository files

**Research date:** 2026-02-25
**Valid until:** 2026-03-27
</metadata>

---

*Phase: 01-baseline-validation-harness*
*Research completed: 2026-02-25*
*Ready for planning: yes*
