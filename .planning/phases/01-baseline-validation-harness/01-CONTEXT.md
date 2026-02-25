# Phase 1: Baseline Validation Harness - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver an automated regression validation harness for existing protocol/task-parser behavior so maintainers can detect breakage early. Scope is limited to requirement IDs REL-01 and REL-02 and current Phase 1 success criteria; no new beacon capabilities are introduced in this phase.

</domain>

<decisions>
## Implementation Decisions

### Pass/Fail Contract
- Protocol encode/decode validation passes on **semantic equivalence**, not unconditional byte-for-byte equality.
- Any mismatch against approved fixture expectations is treated as a regression by default (**fail by default**) unless an intentional fixture update is explicitly reviewed and approved.
- Malformed task payload tests must validate **reject + continue loop** behavior (no crash, no uncontrolled termination).
- Regression failures should emit **minimal deterministic diagnostics** (fixture ID, assertion target, stable diff summary).

### Regression Execution Workflow
- Regression suite is expected to run **locally before PR** and in **CI**.
- Suite strategy is **fast local gate + full CI suite**.
- Merge policy is **blocked on regression failure** until fixed or explicitly approved with fixture rationale.
- Default developer output should be **actionable summary first** (deep dump is optional, not default).

### Fixture Governance
- Canonical protocol fixtures are **versioned in repository**.
- Fixture updates require **explicit reviewer approval + rationale** for behavior change.
- Intentional behavior shifts are tracked via **versioned fixture sets**, not silent overwrite of history.
- Fixture inventory must maintain **REQ/success-criteria traceability** (fixture set mapped to REL-01/REL-02 and phase outcomes).

### Claude's Discretion
- Exact local command UX for quick vs full suite entry points.
- Exact fixture file/directory naming conventions and index file layout.
- Optional verbose diagnostics toggle design, provided default output remains compact and deterministic.

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-baseline-validation-harness*
*Context gathered: 2026-02-25*
