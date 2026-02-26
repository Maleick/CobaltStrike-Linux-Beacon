# Cobalt Strike Linux Beacon

## What This Is

A brownfield custom Linux Beacon project that interoperates with Cobalt Strike Team Server over Beacon protocol transports. The current repository already delivers a working HTTP/S implant, Linux BOF execution, and SOCKS pivoting for operators using Aggressor workflows. This initialization defines the next milestone to improve compatibility, transport coverage, reliability, and security hardening.

## Core Value

Operators can deploy a Linux beacon that remains Cobalt Strike-compatible while being safely extensible for new transports and profile behaviors.

## Requirements

### Validated

- ✓ HTTP/S listener communication with default profile-compatible metadata/task flow — existing
- ✓ Core command execution (`sleep`, `cd`, `pwd`, `shell`, `ls`, `upload`, `download`, `exit`) — existing
- ✓ Linux BOF inline execution via ELFLoader compatibility path — existing
- ✓ SOCKS proxy/pivot socket handling in beacon runtime loop — existing
- ✓ Aggressor-driven payload generation workflow on Linux build hosts — existing

### Active

- [ ] Add configurable custom HTTP/S profile compatibility without manual source edits
- [ ] Add reverse TCP transport mode while preserving current HTTP/S behavior
- [ ] Add automated regression testing and CI gating for protocol/parser stability
- [ ] Improve security defaults and build hygiene for key/config handling

### Out of Scope

- Windows/macOS implant targets — this milestone is Linux x64 only
- Full parity with every Cobalt Strike profile permutation — focus on high-value profile knobs first
- New operator GUI or management dashboard — keep scope on implant/runtime/build pipeline

## Context

The repository is a compact native C project with Aggressor/Python tooling for payload generation and vendored ELFLoader support for Linux BOFs. A fresh codebase map exists under `.planning/codebase/` and captures current architecture, conventions, concerns, and integrations. Known pain points include in-place source mutation during payload generation, lack of automated tests, and hard-coded HTTP/S profile assumptions.

## Constraints

- **Tech stack**: Keep C + OpenSSL + libcurl + Aggressor/Python tooling — preserves existing runtime and operator workflow
- **Compatibility**: Preserve backward compatibility for current default HTTP/S behavior and existing command IDs/callback semantics — avoids regressions for current users
- **Environment**: Build/generation flow must continue to run on Linux-based Cobalt Strike client hosts — required by current Aggressor integration
- **Security**: Never commit secret values or long-term key material to tracked files — avoids credential leakage

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Initialize as brownfield from existing codebase map | Existing implant capabilities are already validated and should be treated as baseline | ✓ Good |
| Prioritize profile abstraction + TCP transport + regression safety for next milestone | Aligns with README future goals and highest operational risk areas from CONCERNS.md | — Pending |
| Keep workflow in interactive/standard depth with parallel planning and verification gates | Matches local operating preferences for production-style planning quality | — Pending |

---
*Last updated: 2026-02-25 after initialization*
