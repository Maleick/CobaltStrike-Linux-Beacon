# Cobalt Strike Beacon (Linux + macOS ARM64)

## Current Milestone: v2.0 macOS ARM64 Beacon

**Goal:** Extend beacon capability to macOS ARM64 (M1–M4) with HTTP/S transport and payload generation on macOS operator hosts, targeting internal purple-team validation.

**Target features:**
- HTTP/S check-in and task loop on macOS ARM64 (`implant-macos/` tree, Clang/native build)
- macOS-host payload generation workflow (Clang, reusing existing profile schema)
- Phased command parity with fixture-backed regression coverage
- Code signing basics and TLS defaults for purple-team deployment

## What This Is

A brownfield custom multi-platform Beacon project that interoperates with Cobalt Strike Team Server over Beacon protocol transports. The repository delivers a working Linux x64 HTTP/S implant (with BOF execution, SOCKS pivoting, and profile abstraction) via Aggressor workflows, and is expanding to add a macOS ARM64 implant target for internal purple-team use.

## Core Value

Operators can deploy a Cobalt Strike-compatible beacon on Linux x64 and macOS ARM64 hosts, with a safe and extensible generation workflow for each platform.

## Requirements

### Validated

- ✓ HTTP/S listener communication with default profile-compatible metadata/task flow — existing
- ✓ Core command execution (`sleep`, `cd`, `pwd`, `shell`, `ls`, `upload`, `download`, `exit`) — existing
- ✓ Linux BOF inline execution via ELFLoader compatibility path — existing
- ✓ SOCKS proxy/pivot socket handling in beacon runtime loop — existing
- ✓ Aggressor-driven payload generation workflow on Linux build hosts — existing

### Active

**v1.0 Linux stream (phases 3–5, paused — parallel):**
- [ ] Add reverse TCP transport mode while preserving current HTTP/S behavior
- [ ] Add automated regression testing and CI gating for protocol/parser stability
- [ ] Improve security defaults and build hygiene for key/config handling

**v2.0 macOS ARM64 stream (phases 6–9, active):**
- [ ] macOS ARM64 HTTP/S check-in and task loop via `implant-macos/` tree
- [ ] Payload generation workflow on macOS operator hosts (Clang, native ARM64)
- [ ] Phased command parity with fixture-backed regression coverage
- [ ] Code signing basics and TLS defaults for purple-team handoff

### Out of Scope

- Windows implant target — not planned in any current milestone
- macOS x86_64 implant — ARM64 (M1–M4) only in v2.0
- macOS BOF/Mach-O execution — deferred; ELFLoader is Linux-specific
- Full Cobalt Strike profile permutation parity — focus on high-value profile knobs first
- New operator GUI or management dashboard — keep scope on implant/runtime/build pipeline
- Production/external operator release for macOS — internal purple-team validation only in v2.0

## Context

The repository is a compact native C project with Aggressor/Python tooling for payload generation and vendored ELFLoader support for Linux BOFs. A fresh codebase map exists under `.planning/codebase/` and captures current architecture, conventions, concerns, and integrations. Known pain points include in-place source mutation during payload generation, lack of automated tests, and hard-coded HTTP/S profile assumptions.

## Constraints

- **Tech stack**: Keep C + OpenSSL + libcurl + Aggressor/Python tooling — preserves existing runtime and operator workflow
- **Compatibility**: Preserve backward compatibility for current default HTTP/S behavior and existing command IDs/callback semantics — avoids regressions for current users
- **Environment (Linux)**: Build/generation flow must continue to run on Linux-based Cobalt Strike client hosts — required by current Aggressor integration
- **Environment (macOS)**: v2.0 macOS generation flow targets macOS operator hosts (Clang/native ARM64) as the primary build path
- **Security**: Never commit secret values or long-term key material to tracked files — avoids credential leakage
- **Platform isolation**: `implant/` (Linux) and `implant-macos/` (macOS) are separate trees — no platform ifdefs mixing the two targets in shared files

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Initialize as brownfield from existing codebase map | Existing implant capabilities are already validated and should be treated as baseline | ✓ Good |
| Prioritize profile abstraction + TCP transport + regression safety for v1.0 | Aligns with README future goals and highest operational risk areas from CONCERNS.md | — Pending |
| Keep workflow in interactive/standard depth with parallel planning and verification gates | Matches local operating preferences for production-style planning quality | ✓ Good |
| macOS ARM64 as new milestone (v2.0) in parallel with Linux v1.0 phases 3–5 | Major scope expansion; separate milestone branch avoids cross-stream commit contamination | — Pending |
| ARM64-only (M1–M4) for macOS v2.0 | x86_64 macOS is declining; purple-team targets are Apple Silicon; smaller scope reduces risk | — Pending |
| Separate `implant-macos/` tree (no shared ifdefs) | Cleaner build system; avoids Linux-specific assumptions bleeding into macOS path | — Pending |
| Phased parity (not full parity in v2.0) | Unblocks transport baseline without getting blocked on macOS-specific command work | — Pending |
| GSD branching_strategy: milestone | Isolates Linux v1 and macOS v2 commits to separate branches | ✓ Good |

---
*Last updated: 2026-02-26 after v2.0 macOS ARM64 milestone start*
