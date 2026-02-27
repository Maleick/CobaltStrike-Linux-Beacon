# Requirements: Cobalt Strike Beacon (Linux + macOS ARM64)

**Defined:** 2026-02-25
**Updated:** 2026-02-26 (v2.0 macOS ARM64 Beacon milestone added)
**Core Value:** Operators can deploy a Cobalt Strike-compatible beacon on Linux x64 and macOS ARM64 hosts, with a safe and extensible generation workflow for each platform.

---

## v1 Requirements — Linux x64 Beacon

Requirements for initial Linux release.

### C2 Profile Compatibility

- [x] **C2P-01**: Operator can define HTTP/S profile values (URIs, headers, user-agent) without manually editing tracked source files. *(Phase 2 — Complete)*
- [x] **C2P-02**: Beacon metadata/task packet behavior remains valid when profile values are customized. *(Phase 2 — Complete)*
- [x] **C2P-03**: Payload generation flow can select a profile configuration per build target. *(Phase 2 — Complete)*

### Transport Modes

- [ ] **NET-01**: Beacon supports reverse TCP transport mode in addition to existing HTTP/S mode.
- [ ] **NET-02**: Operator can select transport mode (`http`, `https`, `tcp`) during payload generation.
- [ ] **NET-03**: Beacon performs bounded reconnect/backoff in TCP mode without process termination.

### Reliability and Validation

- [x] **REL-01**: Automated tests validate metadata/packet encoding and decoding against known-good fixtures. *(Phase 1 — Complete)*
- [x] **REL-02**: Automated tests cover malformed task payload handling and verify no crash conditions. *(Phase 1 — Complete)*
- [ ] **REL-03**: CI pipeline builds the implant and runs regression tests on Linux for each change.

### Security and Build Hygiene

- [ ] **SEC-01**: HTTPS transport verifies certificates by default with explicit opt-out configuration.
- [ ] **SEC-02**: Key/listener build-time injection no longer mutates tracked C source files in-place.
- [ ] **SEC-03**: Payload generation cleans temporary key/config artifacts after build completion.

---

## v2 Requirements — macOS ARM64 Beacon

Requirements for macOS ARM64 purple-team milestone. ARM64 (M1–M4) only; internal validation target.

### Build and Binary Integrity

- [x] **MAC-01**: `implant-macos/` compiles cleanly with Apple Clang and `-arch arm64` with zero warnings under `-Wall -Wextra`. *(Phase 6, plan 06-01 — Makefile with CC=clang, -arch arm64, -Wall -Wextra established)*
- [x] **MAC-02**: Generated Mach-O binary carries a valid ad-hoc code signature; executes on macOS Sequoia 15.x without `Killed: 9`. *(Phase 6, plan 06-01 — ad-hoc codesign step in Makefile link target)*
- [x] **MAC-03**: Build system resolves Homebrew OpenSSL and libcurl paths dynamically (`brew --prefix`) — portable across ARM64 and Intel Homebrew layouts. *(Phase 6, plan 06-01 — dynamic brew --prefix path resolution, make check-deps passes)*

### Protocol Correctness

- [x] **MAC-04**: Beacon metadata packet uses `uint32_t` types for `var4`/`var5`/`var6` fields — no `uint16_t`/`htonl()` mismatch that causes Team Server HMAC failure.
- [ ] **MAC-05**: Beacon check-in shows correct macOS marketing version (`15.x` via `sysctlbyname("kern.osproductversion")`) — not Darwin kernel version (`24.x`).
- [x] **MAC-06**: Beacon check-in shows real process name via `getprogname()` — not Linux `/proc/self/status` fallback (`"linuxbeacon"`).
- [ ] **MAC-01**: `implant-macos/` compiles cleanly with Apple Clang and `-arch arm64` with zero warnings under `-Wall -Wextra`.
- [ ] **MAC-02**: Generated Mach-O binary carries a valid ad-hoc code signature; executes on macOS Sequoia 15.x without `Killed: 9`.
- [ ] **MAC-03**: Build system resolves Homebrew OpenSSL and libcurl paths dynamically (`brew --prefix`) — portable across ARM64 and Intel Homebrew layouts.

### Protocol Correctness

- [ ] **MAC-04**: Beacon metadata packet uses `uint32_t` types for `var4`/`var5`/`var6` fields — no `uint16_t`/`htonl()` mismatch that causes Team Server HMAC failure.
- [ ] **MAC-05**: Beacon check-in shows correct macOS marketing version (`15.x` via `sysctlbyname("kern.osproductversion")`) — not Darwin kernel version (`24.x`).
- [ ] **MAC-06**: Beacon check-in shows real process name via `getprogname()` — not Linux `/proc/self/status` fallback (`"linuxbeacon"`).

### Transport and C2 Connectivity

- [ ] **MAC-07**: macOS beacon successfully connects to Team Server, completes initial check-in, and appears in operator console with correct hostname, username, process name, and OS version.
- [ ] **MAC-08**: Beacon receives, decrypts (AES+HMAC), and dispatches tasks correctly using the existing `crypto.c` / `commands.c` path on macOS.

### Operator Workflow

- [ ] **MAC-09**: Operator can generate a configured macOS ARM64 payload through the existing Aggressor workflow by selecting "macOS" platform — no manual script invocation required.
- [ ] **MAC-10**: Generation pipeline (`InsertListenerInfo.py`, `InsertPublicKey.py`, `RemovePublicKey.py`) routes output to `implant-macos/generated/` when `--target macos` is specified — Linux output is unaffected.

### Command Parity (POSIX scope)

- [ ] **MAC-11**: Core POSIX commands work correctly on macOS: `sleep`, `exit`, `cd`, `pwd`, `ls`, `upload`, `download`, `shell`.
- [ ] **MAC-12**: SOCKS pivot (`listen`/`connect`/`send`/`close`) works on macOS using the existing `select()`-based `pivot.c` implementation.

### Regression Coverage

- [ ] **MAC-13**: `implant-macos/tests/` fixture suite validates protocol encode/decode and macOS-specific metadata on the macOS tree — reuses existing protocol/parser fixtures where compatible.

### Deployment Readiness

- [ ] **MAC-14**: Quarantine xattr deployment procedure is documented — operator can run a transferred binary on a target macOS host without Gatekeeper blocking execution.

---

## Deferred Requirements

Tracked but not in any current milestone roadmap.

### Linux Performance and Ecosystem

- **PERF-01**: Pivot subsystem supports higher socket concurrency with event-backend optimization.
- **COMP-01**: Broader compatibility matrix across additional Cobalt Strike profile permutations.
- **OBS-01**: Structured runtime telemetry for debugging and operator diagnostics.

### macOS Extended Capabilities (v3+)

- **MAC-EXT-01**: macOS BOF / Mach-O inline execute — separate subsystem, large scope, explicitly deferred.
- **MAC-EXT-02**: `kqueue`-based SOCKS pivot backend (replacement for `select()` at scale).
- **MAC-EXT-03**: Process name masquerading via `setprogname()` / `argv[0]` manipulation.
- **MAC-EXT-04**: MAC address collection (`AF_LINK` + `struct sockaddr_dl`).

---

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Windows implant target | Not planned in any current milestone |
| macOS x86_64 implant | ARM64 (M1–M4) only in v2.0 |
| macOS BOF / Mach-O inline execute | ELFLoader is Linux-specific; macOS equivalent is separate large scope — deferred |
| Full profile DSL parity for every C2 profile directive | Too broad for current milestone; high risk without staged rollout |
| New operator GUI/management plane | Not required to deliver core implant capability |
| Production/external operator release for macOS | Internal purple-team validation only in v2.0 |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REL-01 | Phase 1 | ✓ Complete |
| REL-02 | Phase 1 | ✓ Complete |
| C2P-01 | Phase 2 | ✓ Complete |
| C2P-02 | Phase 2 | ✓ Complete |
| C2P-03 | Phase 2 | ✓ Complete |
| NET-01 | Phase 3 | Pending (v1 paused) |
| NET-02 | Phase 3 | Pending (v1 paused) |
| NET-03 | Phase 3 | Pending (v1 paused) |
| SEC-01 | Phase 4 | Pending (v1 paused) |
| SEC-02 | Phase 4 | Pending (v1 paused) |
| SEC-03 | Phase 4 | Pending (v1 paused) |
| REL-03 | Phase 5 | Pending (v1 paused) |
| MAC-01 | Phase 6 | ✓ Complete (06-01) |
| MAC-02 | Phase 6 | ✓ Complete (06-01) |
| MAC-03 | Phase 6 | ✓ Complete (06-01) |
| MAC-04 | Phase 6 | ✓ Complete (06-02) |
| MAC-05 | Phase 7 | Pending |
| MAC-06 | Phase 6 | ✓ Complete (06-02) |
| MAC-01 | Phase 6 | Pending |
| MAC-02 | Phase 6 | Pending |
| MAC-03 | Phase 6 | Pending |
| MAC-04 | Phase 6 | Pending |
| MAC-05 | Phase 7 | Pending |
| MAC-06 | Phase 6 | Pending |
| MAC-07 | Phase 7 | Pending |
| MAC-08 | Phase 7 | Pending |
| MAC-09 | Phase 7 | Pending |
| MAC-10 | Phase 7 | Pending |
| MAC-11 | Phase 8 | Pending |
| MAC-12 | Phase 8 | Pending |
| MAC-13 | Phase 9 | Pending |
| MAC-14 | Phase 9 | Pending |

**Coverage:**
- v1 requirements: 12 total (5 complete, 7 pending on paused stream)
- v2 requirements: 14 total (3 complete, 11 pending on active stream)
- v2 requirements: 14 total (0 complete, all mapped to phases 6–9)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-27 after Phase 6 Plan 06-01 (MAC-01, MAC-02, MAC-03 complete)*
*Last updated: 2026-02-26 after v2.0 macOS ARM64 milestone research*
