# Roadmap: Cobalt Strike Linux Beacon

## Overview

This roadmap evolves the existing Linux beacon from a working proof-of-concept into a safer and more extensible operator platform. The sequence prioritizes regression safety first, then profile flexibility, transport expansion, and security/build hardening, finishing with CI-backed release readiness.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Baseline Validation Harness** - Establish repeatable protocol/parser regression safety. (completed 2026-02-25)
- [x] **Phase 2: HTTP/S Profile Abstraction** - Externalize profile configuration while preserving compatibility. (completed 2026-02-25)
- [ ] **Phase 3: Reverse TCP Transport Mode** - Add TCP beacon transport and generation-mode selection.
- [ ] **Phase 4: Security and Build Hygiene** - Harden TLS defaults and eliminate tracked-source mutation workflow.
- [ ] **Phase 5: CI and Release Readiness** - Automate build/test gating and milestone acceptance checks.

## Phase Details

### Phase 1: Baseline Validation Harness
**Goal**: Core protocol parsing and packet handling are protected by automated regression tests.
**Depends on**: Nothing (first phase)
**Requirements**: REL-01, REL-02
**Success Criteria** (what must be TRUE):
  1. Maintainer can run an automated fixture suite locally and receive pass/fail output for metadata and packet encode/decode behavior.
  2. Malformed task payload fixtures do not crash the process and return controlled error paths.
  3. Existing baseline command/task parser behavior is preserved under regression tests.
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Establish fixture corpus, index, and regression harness entrypoints
- [ ] 01-02-PLAN.md — Add malformed-task parser hardening test matrix and safeguards
- [ ] 01-03-PLAN.md — Add baseline protocol/command smoke compatibility regression suite

### Phase 2: HTTP/S Profile Abstraction
**Goal**: Operators can build profile-specific HTTP/S beacons without editing tracked source files.
**Depends on**: Phase 1
**Requirements**: C2P-01, C2P-02, C2P-03
**Success Criteria** (what must be TRUE):
  1. Operator selects a profile configuration artifact during generation and receives a valid implant build.
  2. Beacon check-in/task exchange works for default profile and at least one non-default profile variant.
  3. Custom profile configuration does not require manual edits to `implant/src/*.c` or `implant/headers/*.h`.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Define external profile schema and loader path for generation/runtime config
- [ ] 02-02: Refactor HTTP/S metadata and transport fields to consume profile data
- [ ] 02-03: Validate compatibility matrix across default and custom profile fixtures

### Phase 3: Reverse TCP Transport Mode
**Goal**: Beacon supports reverse TCP transport with operator-selectable generation/runtime mode.
**Depends on**: Phase 2
**Requirements**: NET-01, NET-02, NET-03
**Success Criteria** (what must be TRUE):
  1. Operator can generate a TCP transport payload from the same generation workflow used for HTTP/S.
  2. TCP-mode beacon successfully connects, receives tasks, and returns callbacks through Team Server.
  3. Network interruptions trigger bounded reconnect/backoff behavior rather than process termination.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Implement TCP transport module and runtime mode selection
- [ ] 03-02: Extend generation scripts/Aggressor flow for transport mode selection
- [ ] 03-03: Add reconnect/backoff policy and transport-mode regression tests

### Phase 4: Security and Build Hygiene
**Goal**: Transport and generation defaults reduce operator risk and accidental leakage.
**Depends on**: Phase 3
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. HTTPS transport verifies certificates by default and allows explicit operator override when required.
  2. Build pipeline no longer mutates tracked source files for key/listener injection.
  3. Temporary key/config artifacts are cleaned automatically after generation.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Add TLS verification controls with secure defaults
- [ ] 04-02: Replace in-place source rewriting with generated build-time artifacts
- [ ] 04-03: Add cleanup and safe temp-file handling for key/config material

### Phase 5: CI and Release Readiness
**Goal**: Every change is validated by automated Linux build/test gates before milestone completion.
**Depends on**: Phase 4
**Requirements**: REL-03
**Success Criteria** (what must be TRUE):
  1. CI pipeline builds implant and executes regression suite on Linux for each change.
  2. Failing tests/builds block merge-ready status until resolved.
  3. Release checklist verifies all mapped v1 requirements are covered by completed phase outputs.
**Plans**: 2 plans

Plans:
- [ ] 05-01: Add CI workflow for build and regression suite execution
- [ ] 05-02: Add release-readiness checks tied to roadmap requirement coverage

## Progress

**Execution Order:**
Phases execute in numeric order: 2 → 2.1 → 2.2 → 3 → 3.1 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline Validation Harness | 0/3 | Complete    | 2026-02-25 |
| 2. HTTP/S Profile Abstraction | 0/3 | Complete    | 2026-02-25 |
| 3. Reverse TCP Transport Mode | 0/3 | Not started | - |
| 4. Security and Build Hygiene | 0/3 | Not started | - |
| 5. CI and Release Readiness | 0/2 | Not started | - |
