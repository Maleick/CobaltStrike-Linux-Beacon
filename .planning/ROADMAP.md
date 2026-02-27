# Roadmap: Cobalt Strike Beacon (Linux + macOS ARM64)

## Overview

Two parallel milestone streams. v1.0 (Linux x64) evolves the existing beacon for safety, transport coverage, and CI hardening. v2.0 (macOS ARM64) adds a new platform target for internal purple-team use — `implant-macos/` tree, Clang build, HTTP/S transport, and operator generation workflow via Aggressor.

**Phase Numbering:**
- Integer phases (1–9): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)
- Phases 1–5: v1.0 Linux stream (phases 3–5 paused while v2.0 bootstraps)
- Phases 6–9: v2.0 macOS ARM64 stream (active)

Decimal phases appear between their surrounding integers in numeric order.

## Phase Index

### v1.0 Linux Stream (Phases 1–5)

- [x] **Phase 1: Baseline Validation Harness** - Establish repeatable protocol/parser regression safety. (completed 2026-02-25)
- [x] **Phase 2: HTTP/S Profile Abstraction** - Externalize profile configuration while preserving compatibility. (completed 2026-02-25)
- [ ] **Phase 3: Reverse TCP Transport Mode** - Add TCP beacon transport and generation-mode selection. *(paused)*
- [ ] **Phase 4: Security and Build Hygiene** - Harden TLS defaults and eliminate tracked-source mutation workflow. *(paused)*
- [ ] **Phase 5: CI and Release Readiness** - Automate build/test gating and milestone acceptance checks. *(paused)*

### v2.0 macOS ARM64 Stream (Phases 6–9)

- [x] **Phase 6: macOS Tree Scaffold and Build System** - Compilable Mach-O ARM64 binary with correct protocol baseline. (completed 2026-02-27)
- [ ] **Phase 7: Generation Pipeline and Live Check-in** - Operator Aggressor workflow + confirmed live Team Server check-in.
- [ ] **Phase 8: POSIX Command Parity and SOCKS Pivot** - All in-scope POSIX commands and pivot validated on macOS.
- [ ] **Phase 9: Test Harness and Operator Handoff** - Fixture-backed regression coverage and purple-team deployment docs.

---

## Phase Details

### Phase 1: Baseline Validation Harness
**Goal**: Core protocol parsing and packet handling are protected by automated regression tests.
**Depends on**: Nothing (first phase)
**Requirements**: REL-01, REL-02
**Success Criteria** (what must be TRUE):
  1. Maintainer can run an automated fixture suite locally and receive pass/fail output for metadata and packet encode/decode behavior.
  2. Malformed task payload fixtures do not crash the process and return controlled error paths.
  3. Existing baseline command/task parser behavior is preserved under regression tests.
**Status**: Complete (2026-02-25)
**Plans**: 3/3 complete

Plans:
- [x] 01-01-PLAN.md — Establish fixture corpus, index, and regression harness entrypoints
- [x] 01-02-PLAN.md — Add malformed-task parser hardening test matrix and safeguards
- [x] 01-03-PLAN.md — Add baseline protocol/command smoke compatibility regression suite

---

### Phase 2: HTTP/S Profile Abstraction
**Goal**: Operators can build profile-specific HTTP/S beacons without editing tracked source files.
**Depends on**: Phase 1
**Requirements**: C2P-01, C2P-02, C2P-03
**Success Criteria** (what must be TRUE):
  1. Operator selects a profile configuration artifact during generation and receives a valid implant build.
  2. Beacon check-in/task exchange works for default profile and at least one non-default profile variant.
  3. Custom profile configuration does not require manual edits to `implant/src/*.c` or `implant/headers/*.h`.
**Status**: Complete (2026-02-25)
**Plans**: 3/3 complete

Plans:
- [x] 02-01: Define external profile schema and loader path for generation/runtime config
- [x] 02-02: Refactor HTTP/S metadata and transport fields to consume profile data
- [x] 02-03: Validate compatibility matrix across default and custom profile fixtures

---

### Phase 3: Reverse TCP Transport Mode
**Goal**: Beacon supports reverse TCP transport with operator-selectable generation/runtime mode.
**Depends on**: Phase 2
**Requirements**: NET-01, NET-02, NET-03
**Success Criteria** (what must be TRUE):
  1. Operator can generate a TCP transport payload from the same generation workflow used for HTTP/S.
  2. TCP-mode beacon successfully connects, receives tasks, and returns callbacks through Team Server.
  3. Network interruptions trigger bounded reconnect/backoff behavior rather than process termination.
**Status**: Not started (v1 stream paused — resume with `/gsd:resume-work`)
**Plans**: 3 plans

Plans:
- [ ] 03-01: Implement TCP transport module and runtime mode selection
- [ ] 03-02: Extend generation scripts/Aggressor flow for transport mode selection
- [ ] 03-03: Add reconnect/backoff policy and transport-mode regression tests

---

### Phase 4: Security and Build Hygiene
**Goal**: Transport and generation defaults reduce operator risk and accidental leakage.
**Depends on**: Phase 3
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. HTTPS transport verifies certificates by default and allows explicit operator override when required.
  2. Build pipeline no longer mutates tracked source files for key/listener injection.
  3. Temporary key/config artifacts are cleaned automatically after generation.
**Status**: Not started (v1 stream paused)
**Plans**: 3 plans

Plans:
- [ ] 04-01: Add TLS verification controls with secure defaults
- [ ] 04-02: Replace in-place source rewriting with generated build-time artifacts
- [ ] 04-03: Add cleanup and safe temp-file handling for key/config material

---

### Phase 5: CI and Release Readiness
**Goal**: Every change is validated by automated Linux build/test gates before milestone completion.
**Depends on**: Phase 4
**Requirements**: REL-03
**Success Criteria** (what must be TRUE):
  1. CI pipeline builds implant and executes regression suite on Linux for each change.
  2. Failing tests/builds block merge-ready status until resolved.
  3. Release checklist verifies all mapped v1 requirements are covered by completed phase outputs.
**Status**: Not started (v1 stream paused)
**Plans**: 2 plans

Plans:
- [ ] 05-01: Add CI workflow for build and regression suite execution
- [ ] 05-02: Add release-readiness checks tied to roadmap requirement coverage

---

### Phase 6: macOS Tree Scaffold and Build System
**Goal**: A compilable macOS ARM64 binary with correct protocol baseline — no `/proc` fallback, no type mismatch, valid ad-hoc signature.
**Depends on**: Phase 2 (profile schema reused; generation pipeline extended in Phase 7)
**Requirements**: MAC-01, MAC-02, MAC-03, MAC-04, MAC-06
**Research**: Not needed — all decisions resolved by research; no unknowns remain at build-system level.
**Success Criteria** (what must be TRUE):
  1. `make -C implant-macos` produces a clean Mach-O ARM64 binary with zero warnings under `-Wall -Wextra`.
  2. Binary carries a valid ad-hoc code signature and executes on macOS Sequoia 15.x without `Killed: 9`.
  3. Homebrew OpenSSL and libcurl paths are resolved dynamically — build succeeds regardless of ARM64 vs Intel Homebrew layout.
  4. Metadata packet uses `uint32_t` for `var4`/`var5`/`var6` — no `uint16_t`/`htonl()` type mismatch.
  5. Beacon shows real process name (`getprogname()`) — not Linux `/proc/self/status` fallback.
**Status**: Complete (2026-02-27)
**Plans**: 3/3 complete

Plans:
- [x] 06-01: Scaffold `implant-macos/` tree — verbatim copies (`http.c`, `crypto.c`, `profile.c`, `pivot.c`, `files.c`, all headers) + macOS Makefile with dynamic Homebrew path resolution
- [x] 06-02: Rewrite `beacon.c` for macOS — `getprogname()`, `uint32_t` type fix, remove ELFLoader dependency; rewrite `main.c` (cosmetic)
- [x] 06-03: Rewrite `commands.c` for macOS — remove ELFRunner include and case 200; preserve shell prefix offset; verify compilation clean

---

### Phase 7: Generation Pipeline and Live Check-in Validation
**Goal**: Operator-configurable macOS payload via Aggressor workflow + confirmed live Team Server check-in showing correct metadata.
**Depends on**: Phase 6
**Requirements**: MAC-05, MAC-07, MAC-08, MAC-09, MAC-10
**Research**: `%COMSPEC% /C` shell task offset (21 bytes) is HIGH confidence from Linux behavior; validate against real macOS-directed session during live check-in step.
**Success Criteria** (what must be TRUE):
  1. Operator selects macOS ARM64 in the Aggressor dialog and receives a configured binary — no manual Python invocation required.
  2. `--target macos` routes all generated artifacts to `implant-macos/generated/` without affecting the Linux generation path.
  3. Live check-in: beacon appears in Team Server console with correct hostname, username, process name, and macOS marketing version (`15.x`).
  4. `sleep`, `pwd`, and `shell` commands execute and return correct output in a live session.
**Plans**: 3 plans

Plans:
- [ ] 07-01: Extend generation scripts with `--target [linux|macos]` flag — `InsertListenerInfo.py`, `InsertPublicKey.py`, `RemovePublicKey.py`; route to `implant-macos/generated/`
- [ ] 07-02: Extend `CustomBeacon.cna` with Platform selector row; wire `--target macos` to generation invocations; replace `uname().release` parse with `sysctlbyname("kern.osproductversion")` in macOS `beacon.c`
- [ ] 07-03: End-to-end live check-in validation — generate macOS payload, confirm metadata in Team Server console, validate `sleep`/`pwd`/`shell` responses, lock shell offset fixture

---

### Phase 8: POSIX Command Parity and SOCKS Pivot
**Goal**: All in-scope POSIX commands and SOCKS pivot work correctly on macOS — validated by execution-path testing.
**Depends on**: Phase 7 (transport confirmed correct before command-level testing)
**Requirements**: MAC-11, MAC-12
**Research**: Not needed — all remaining commands are pure POSIX; `select()` pivot confirmed compatible; no `epoll`/`AF_PACKET` dependencies in scope.
**Success Criteria** (what must be TRUE):
  1. `cd`, `ls`, `upload`, `download` commands return correct output/behavior on macOS.
  2. SOCKS pivot establishes sessions, forwards traffic, and closes cleanly on macOS.
  3. No Linux-specific API calls (`epoll`, `AF_PACKET`, `SIOCGIFHWADDR`) are present in the macOS build.
**Plans**: 2 plans

Plans:
- [ ] 08-01: Execute and validate file/directory commands (`cd`, `ls`, `upload`, `download`) against macOS filesystem — document any behavioral differences from Linux
- [ ] 08-02: Execute and validate SOCKS pivot (`listen`/`connect`/`send`/`close`) on macOS — confirm `select()` behavior and document `FD_SETSIZE` limit

---

### Phase 9: Test Harness and Operator Handoff
**Goal**: Fixture-backed regression coverage prevents protocol regressions during purple-team exercises; deployment procedure documented.
**Depends on**: Phase 8 (command parity complete before fixtures written against final behavior)
**Requirements**: MAC-13, MAC-14
**Research**: Not needed — test harness adaptation follows patterns from existing `implant/tests/`; quarantine xattr procedure is operational documentation.
**Success Criteria** (what must be TRUE):
  1. `implant-macos/tests/` runner executes and passes for protocol encode/decode and macOS-specific metadata fixtures.
  2. Existing `implant/tests/` protocol fixtures are reused unchanged where compatible; macOS-specific fixtures cover `getprogname()` and `sysctlbyname()` output.
  3. Operator runbook documents the quarantine xattr deployment procedure (`xattr -d com.apple.quarantine`) for transferred binaries.
  4. No ELFRunner or `/proc/self/status` fixture references remain in the macOS test tree.
**Plans**: 2 plans

Plans:
- [ ] 09-01: Adapt `implant/tests/` into `implant-macos/tests/` — update source anchors (no ELFRunner), add macOS metadata fixtures, verify protocol fixtures pass unchanged
- [ ] 09-02: Write operator runbook for macOS purple-team deployment — quarantine xattr procedure, ad-hoc signing verification, debug symbol stripping for release builds

---

## Progress

**Execution Order:** Active phases: 6 → 7 → 8 → 9 (macOS stream). Paused phases: 3 → 4 → 5 (Linux stream).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline Validation Harness | 3/3 | ✓ Complete | 2026-02-25 |
| 2. HTTP/S Profile Abstraction | 3/3 | ✓ Complete | 2026-02-25 |
| 3. Reverse TCP Transport Mode | 0/3 | Paused (v1 stream) | — |
| 4. Security and Build Hygiene | 0/3 | Paused (v1 stream) | — |
| 5. CI and Release Readiness | 0/2 | Paused (v1 stream) | — |
| 6. macOS Tree Scaffold and Build System | 3/3 | ✓ Complete | 2026-02-27 |
| 7. Generation Pipeline and Live Check-in | 0/3 | Not started | — |
| 8. POSIX Command Parity and SOCKS Pivot | 0/2 | Not started | — |
| 9. Test Harness and Operator Handoff | 0/2 | Not started | — |
