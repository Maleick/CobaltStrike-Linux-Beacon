---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: macOS ARM64 Beacon
status: in_progress
stopped_at: Completed 06-02-PLAN.md — beacon.c getprogname()+uint32_t fix and main.c version string
last_updated: "2026-02-27T02:39:35Z"
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 10
  completed_plans: 2
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-26)

**Core value:** Operators can deploy a Cobalt Strike-compatible beacon on Linux x64 and macOS ARM64 hosts, with a safe and extensible generation workflow for each platform.
**Current focus:** v2.0 macOS ARM64 Beacon — Phase 6: macOS Tree Scaffold and Build System

## Current Position

Phase: 6 of 9 (macOS Tree Scaffold and Build System)
Plan: 2 of 3 in current phase
Status: In progress — plan 06-02 complete
Last activity: 2026-02-27 — beacon.c and main.c macOS rewrites complete

Progress: [##░░░░░░░░] 20%

## v1.0 Linux Stream (Paused)

Phases 1–2 complete. Phases 3–5 paused pending v2.0 bootstrap.
Resume with: `/gsd:resume-work` (see `.planning/phases/03-reverse-tcp-transport/.continue-here.md`)

| Phase | Status | Plans |
|-------|--------|-------|
| 1. Baseline Validation Harness | ✓ Complete | 3/3 |
| 2. HTTP/S Profile Abstraction | ✓ Complete | 3/3 |
| 3. Reverse TCP Transport | ○ Paused | 0/3 |
| 4. Security and Build Hygiene | ○ Not started | 0/3 |
| 5. CI and Release Readiness | ○ Not started | 0/2 |

## v2.0 macOS Stream Progress

| Phase | Status | Plans |
|-------|--------|-------|
| 6. macOS Tree Scaffold and Build System | ◑ In progress | 2/3 |
| 7. macOS Beacon Core Rewrites | ○ Not started | 0/3 |
| 8. macOS Command Parity | ○ Not started | 0/3 |
| 9. macOS Stabilization | ○ Not started | 0/1 |

## Performance Metrics

**Velocity (v2.0 stream):**
- Total plans completed: 2
- Average duration: 4 min
- Total execution time: 0.1 hours

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| 06-01 | 5 min | 2 | 16 |
| 06-02 | 3 min | 2 | 2 |

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v2.0 Init] macOS ARM64 as new parallel milestone — separate branch, separate implant-macos/ tree
- [v2.0 Init] ARM64 only (M1–M4) — x86_64 macOS excluded from v2.0 scope
- [v2.0 Init] Phased parity — not full command parity in first milestone
- [v2.0 Init] Internal purple-team validation target — not production/external release
- [v2.0 Init] macOS-host build first (Clang/native ARM64)
- [v2.0 Init] branching_strategy: milestone — stream isolation via separate branches
- [06-01] brew --prefix pattern for dynamic Homebrew path resolution — no hardcoded /opt/homebrew or /usr/local
- [06-01] check-deps target fails fast with human-readable errors if Homebrew deps missing
- [06-01] Ad-hoc codesign in link target: checks existing signature before applying codesign
- [06-01] -mmacosx-version-min=12.0 for maximum Apple Silicon (M1-M4) compatibility
- [06-01] Sync comment format: /* copied from implant/src/<file>, last synced 2026-02-26 */
- [06-02] getprogname() in stdlib.h (already included) — no new headers needed for MAC-06 fix
- [06-02] uint32_t + htonl() for all three 4-byte var4/5/6 fields — Linux version incorrectly used htons() for var5 and var6
- [06-02] No #ifdef __APPLE__ guards in implant-macos/ tree — macOS-only by design

### Pending Todos

None.

### Blockers/Concerns (Resolved)

- ~~libcurl + OpenSSL link paths differ on macOS (Homebrew vs System frameworks)~~ — RESOLVED in 06-01 via dynamic brew --prefix path resolution
- ELFLoader is Linux ELF-specific — macOS Mach-O BOF execution is out of scope for v2.0
- macOS ARM64 code signing constraints — Phase 9 stabilization must address for purple-team deployment

## Session Continuity

**Last session:** 2026-02-27T02:39:35Z
**Stopped at:** Completed 06-02-PLAN.md
**Resume file:** .planning/STATE.md
