# Phase 2: HTTP/S Profile Abstraction - Research

**Researched:** 2026-02-25
**Domain:** Externalized HTTP/S profile configuration for generation/runtime compatibility
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Profile configuration must be versioned JSON artifacts in-repo and validated before build.
- Generation-time profile selection must use existing Aggressor/Python flow (no manual source edits).
- Default profile must preserve baseline behavior; non-default profile must also pass compatibility checks.
- Invalid profile input must fail fast with deterministic diagnostics.
- Runtime remains HTTP/S only in this phase.
- Compatibility policy is fail-by-default unless explicitly approved updates.

### Claude's Discretion
- Exact profile directory/file naming.
- Exact selection UX text in Aggressor workflow.
- Exact validation implementation approach in Python.
- Exact generated artifact path and naming convention.

### Deferred Ideas (OUT OF SCOPE)
- TCP transport/profile support (Phase 3).
- TLS verification hardening (Phase 4).
- Full profile DSL parity beyond high-value knobs.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| C2P-01 | Operator defines HTTP/S profile values without editing tracked source files. | Replace in-place source/header rewrites with profile artifact + generated build artifact path. |
| C2P-02 | Metadata/task packet behavior remains valid when profile values are customized. | Add protocol/profile compatibility fixtures + semantic regression checks for default and non-default profiles. |
| C2P-03 | Payload generation flow selects profile configuration per build target. | Extend Aggressor/Python generation path with explicit profile selection and validation gates. |

</phase_requirements>

<research_summary>
## Summary

Current implementation hard-codes transport/profile values in `implant/headers/config.h` and mutates tracked files at generation time via `generate-payload/InsertListenerInfo.py`. This directly conflicts with C2P-01 and creates drift risk (tracked source modified per build).

A robust Phase 2 pattern is: **versioned JSON profile artifact -> validator -> generated profile header/artifact -> compile/runtime consumers**. This preserves current tooling while removing manual edits and keeping deterministic build inputs.

`CustomBeacon.cna` already controls listener selection and build orchestration, making it the correct integration point for profile selection input and script invocation. `implant/src/http.c` currently reads macros (`C2_SERVER`, `C2_PORT`, `HTTP_GET_URI`, `HTTP_POST_URI`, `USER_AGENT`), so the runtime abstraction should center on replacing direct macro dependence with profile-backed accessors/struct values.

Phase 1 already introduced deterministic regression harnesses and semantic checks. Phase 2 should extend those fixtures with profile matrix coverage so default profile behavior is protected and at least one non-default variant is validated.

**Primary recommendation:** Implement a generated profile artifact pipeline with strict validation and regression-backed default/non-default compatibility checks, while preserving existing Aggressor-driven operator workflow.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| C + existing implant code | repo current | Runtime HTTP/S protocol behavior | Current production baseline |
| GNU Make | repo current | Build integration for generated profile artifact | Already authoritative build path |
| Python 3 stdlib (`json`, `argparse`, `pathlib`) | system current | Profile validation and artifact rendering | Already used in generation scripts |
| Aggressor Script (`CustomBeacon.cna`) | repo current | Operator profile selection integration | Existing operator entrypoint |

### Supporting
| Library/Tool | Purpose | When to Use |
|--------------|---------|-------------|
| JSON schema helper (optional) | Stricter artifact validation | If stdlib validation becomes brittle |
| Existing regression harness (`implant/tests`) | Compatibility verification | Required for default/non-default matrix checks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Generated artifact path | Continue mutating `config.h` per build | Simpler short-term but violates C2P-01 and drift-safety goals |
| Aggressor-integrated selection | Out-of-band shell-only profile selection | Lower UI complexity but worse operator parity with current workflow |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Profile Artifact + Generated Header
**What:** Keep canonical profile JSON in versioned repo path; render deterministic generated header consumed by implant build.
**When to use:** Always for per-build profile customization without source mutation.
**Example flow:**
1. `profiles/http/default-profile.json`
2. `generate-payload/validate_profile.py`
3. `generate-payload/render_profile_header.py --output implant/generated/profile_config.h`
4. Build consumes generated profile values.

### Pattern 2: Selection-Then-Validation Gate
**What:** Aggressor/Python generation selects profile first, validates immediately, then builds.
**When to use:** For deterministic, operator-visible failure handling.
**Example:**
- If profile missing required key -> abort before `make` with stable error text.

### Pattern 3: Compatibility Matrix Regression
**What:** Extend Phase 1 regression harness with default and non-default profile fixtures.
**When to use:** Every phase touching profile-dependent metadata/transport behavior.
**Example checks:**
- Default profile preserves semantic baseline.
- Variant profile updates URI/UA/headers while task exchange remains valid.

### Anti-Patterns to Avoid
- Mutating tracked source/header files during generation.
- Silent fallback to partial/invalid profile values.
- Profile fixtures without requirement traceability (`C2P-01..03`).

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-build config injection | Ad-hoc `sed` rewrites into tracked headers | Generated profile artifact consumed by build | Keeps source immutable and auditable |
| Profile validation | Implicit defaults-only parsing | Explicit validation gate with deterministic failures | Prevents silent protocol drift |
| Compatibility confidence | Manual listener smoke checks only | Fixture-backed profile matrix in `implant/tests` | Supports repeatable C2P-02 verification |

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Default Profile Drift
**What goes wrong:** New abstraction changes baseline behavior unexpectedly.
**How to avoid:** Keep a locked default profile artifact and regression fixture equivalence checks.

### Pitfall 2: Build-Time Coupling Breakage
**What goes wrong:** Aggressor selection and script rendering disagree on file paths/arguments.
**How to avoid:** Define one canonical argument contract and verify it in plan-level tasks.

### Pitfall 3: Over-scoping into Transport Features
**What goes wrong:** Phase 2 implementation starts introducing TCP mode behavior.
**How to avoid:** Keep runtime scope HTTP/S-only and defer transport mode to Phase 3.

</common_pitfalls>

<code_examples>
## Code Examples

### Current tracked-source mutation
```python
# generate-payload/InsertListenerInfo.py
if C2_SERVER_string in line:
    f.write(f'{C2_SERVER_string} "{Target_Server}"\n')
```

### Current HTTP/S macro dependence
```c
// implant/src/http.c
snprintf(url, sizeof(url), "http://%s:%d%s", C2_SERVER, C2_PORT, uri);
```

### Current generation orchestration anchor
```c
# CustomBeacon.cna
$command = "python3 InsertListenerInfo.py " . $TargetServer . " " . $TargetPort . " " . $HTTPSvalue;
```

</code_examples>

<open_questions>
## Open Questions

1. Should profile artifact include optional per-request header order controls now, or defer to later compatibility phases?
   - Recommendation: include required header values now; defer ordering nuance unless compatibility tests prove it necessary.

2. Should generated profile artifacts live under `implant/generated/` or an equivalent build-output path?
   - Recommendation: use an explicit generated path under implant build tree and keep it out of tracked source logic.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `CustomBeacon.cna`
- `generate-payload/InsertListenerInfo.py`
- `implant/src/http.c`
- `implant/headers/config.h`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/02-http-s-profile-abstraction/02-CONTEXT.md`

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/INTEGRATIONS.md`
- `.planning/codebase/CONCERNS.md`

</sources>

<metadata>
## Metadata

**Research scope:** profile artifact abstraction, generation integration, runtime consumption, compatibility validation
**Confidence breakdown:** stack HIGH, architecture HIGH, pitfalls HIGH, open-questions MEDIUM
**Research date:** 2026-02-25
**Valid until:** 2026-03-27

</metadata>
