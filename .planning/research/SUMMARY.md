# Project Research Summary

**Project:** CobaltStrike-Linux-Beacon — v2.0 macOS ARM64 Milestone
**Domain:** macOS ARM64 (M1-M4) Cobalt Strike beacon implant — porting an existing Linux x64 C codebase to a new `implant-macos/` tree
**Researched:** 2026-02-26
**Confidence:** HIGH

## Executive Summary

This project is a targeted platform port, not a new product build. The existing Linux x64 Cobalt Strike beacon (`implant/`) is a well-structured, modular C codebase where approximately 70% of source files are POSIX-portable and can be copied verbatim into the new `implant-macos/` tree with zero modification. The remaining 30% — `beacon.c`, `commands.c`, and `main.c` — require surgical, well-understood rewrites to replace Linux-specific subsystems: `/proc/self/status` process name lookup, ELFLoader BOF execution (explicitly out of scope), and a pre-existing `uint16_t`/`htonl()` type mismatch in the metadata generation path. The macOS build toolchain is Apple Clang 17 with Homebrew OpenSSL@3 and Homebrew libcurl (both verified installed on the build host), making the dependency picture fully resolved before a single line is written.

The recommended approach is a strictly ordered eight-step build sequence: scaffold the `implant-macos/` directory tree, write the macOS Makefile with dynamic Homebrew path resolution, rewrite the three platform-specific source files, extend the generation pipeline with a `--target` flag, extend the Aggressor script with a platform selector, validate with a live Team Server check-in, and adapt the test harness. The critical-path items are the `beacon.c` rewrite (determines whether the binary can check in at all) and the generation pipeline extension (determines whether operators can produce configured binaries without manual script invocation). These two steps gate all downstream validation.

The primary risks are concentrated in the metadata generation layer and the build pipeline, not the transport or crypto layers. Five issues require resolution before a valid check-in is possible: the `/proc/self/status` silent fallback, the `uint16_t`/`htonl()` type mismatch that Clang will expose where GCC was silent, the Darwin kernel version vs. macOS marketing version mismatch in OS metadata, the mandatory ad-hoc signing step in the Makefile, and the Homebrew path resolution for OpenSSL and libcurl headers. All five are well-understood and have concrete, low-complexity fixes. The wire protocol between the beacon and Team Server is byte-identical on macOS; no protocol-level changes are required.

---

## Key Findings

### Recommended Stack

The macOS ARM64 build requires no new external dependencies beyond what the Linux build already uses conceptually — only the macOS-native versions of the same libraries. Apple Clang 17.0.0 (Xcode CLT, already present on the build host) replaces GCC; Homebrew OpenSSL 3.6.1 replaces the system LibreSSL (which Apple does not expose for linking since macOS 11); Homebrew libcurl 8.18.0 replaces the system curl (which uses SecureTransport, not OpenSSL, and whose headers are not exposed for third-party linking). GNU Make 3.81 (Xcode CLT) is fully compatible with all existing Makefile patterns. No additional installs are required on the current build host — `brew info openssl@3` and `brew info curl` confirm both libraries are installed and at the correct versions.

The single most important Makefile change is replacing hardcoded library paths with `$(shell brew --prefix openssl@3)` and `$(shell brew --prefix curl)` to ensure portability across ARM64 (`/opt/homebrew/`) and Intel (`/usr/local/opt/`) Homebrew installs. All POSIX and network headers available on Linux are present in the macOS SDK with identical APIs; no header-level substitutions are required except replacing the `/proc/self/status` runtime read.

**Core technologies:**
- Apple Clang 17.0.0 (Xcode CLT): C compiler — only linkable native ARM64 compiler on macOS; `-arch arm64` is the sole required addition over existing GCC flags
- Homebrew OpenSSL 3.6.1: crypto and TLS — Apple LibreSSL headers are not exposed for linking on macOS 11+; Homebrew OpenSSL provides identical EVP API
- Homebrew libcurl 8.18.0: HTTP transport — system libcurl uses SecureTransport (deprecated in curl 2025); Homebrew libcurl uses OpenSSL backend, matching Linux behavior
- GNU Make 3.81 (Xcode CLT): build orchestration — all existing `$(lastword ...)`, `$(abspath ...)`, `$(patsubst ...)` patterns are 3.81-compatible

### Expected Features

The feature scope is defined by command portability across platforms. The majority of beacon commands are pure POSIX and require no work. Three areas require targeted adaptation: process name metadata (one function call replacement), OS version metadata (one sysctl call), and the command dispatcher (remove one case). BOF execution (command ID 200) is explicitly out of scope.

**Must have (table stakes):**
- HTTP/S check-in loop — beacon does not register without it; libcurl API is portable, no changes to `http.c`
- Metadata generation with correct macOS values — Team Server beacon list must show real process name and macOS version, not Linux fallbacks
- AES/HMAC task decryption — `crypto.c` uses OpenSSL EVP API exclusively; copies verbatim to macOS tree
- Task dispatch loop — `commands_parse_tasks()` is pure C logic; copies verbatim
- `sleep`, `exit`, `cd`, `pwd`, `ls`, `upload`, `download` commands — all pure POSIX; no changes needed
- `shell` command (`COMMAND_EXECUTE_JOB`) — `popen()` is POSIX; the `%COMSPEC% /C` offset logic must be validated against a real session but is expected to carry over unchanged
- SOCKS pivot — `pivot.c` uses `select()` (POSIX); copies verbatim; `CLOCK_MONOTONIC` is present on macOS 10.12+
- Ad-hoc code signature in Makefile — ARM64 binaries cannot execute without at minimum an ad-hoc signature; Clang linker auto-signs at link time on native builds

**Should have (differentiators):**
- Human-readable macOS version in metadata (`sysctlbyname("kern.osproductversion")`) — shows "15.3" instead of "24.3" (Darwin kernel version) in Team Server beacon list
- Fixture-backed regression suite for macOS commands — prevents protocol regressions; test infrastructure from `implant/tests/` is partially reusable

**Defer (v2+):**
- MAC address collection — requires `AF_LINK` + `struct sockaddr_dl` (macOS-specific); not currently collected in Linux tree either
- Process name masquerading via `setprogname()` / `argv[0]` manipulation
- `kqueue`-based SOCKS pivot backend (replacement for `select()` at scale)
- macOS BOF / Mach-O inline execute — separate subsystem, large scope, out of scope per PROJECT.md

### Architecture Approach

The architecture decision from PROJECT.md is to maintain a fully independent `implant-macos/` tree with no shared source via symlinks or cross-tree include paths. This enforces platform isolation at the file system level rather than via `#ifdef __APPLE__` guards. Five source files (`http.c`, `crypto.c`, `profile.c`, `pivot.c`, `files.c`) and all headers are verbatim copies; three files (`main.c`, `beacon.c`, `commands.c`) are macOS-specific rewrites that preserve all protocol semantics while replacing platform-specific subsystems. The generation pipeline (`generate-payload/*.py`) gains a `--target [linux|macos]` flag to route output to the correct `generated/` directory. The profile schema (`profiles/http/*.json`) and all profile rendering tooling are fully shared and require zero changes.

**Major components:**
1. `implant-macos/` source tree — independent, parallel to `implant/`; verbatim copies for POSIX-portable modules, targeted rewrites for platform-specific modules
2. `implant-macos/Makefile` — Apple Clang, `-arch arm64`, dynamic Homebrew path resolution, no ELFLoader sources
3. `generate-payload/` with `--target` flag — routes profile injection and public key injection to `implant-macos/generated/` and `implant-macos/src/beacon.c`
4. `CustomBeacon.cna` with platform selector — adds Platform row to operator dialog; routes generation scripts with `--target macos` when selected
5. `implant-macos/tests/` — adapts existing Python test harness; reuses protocol/parser fixtures unchanged; updates source-anchor fixtures to reflect macOS tree

### Critical Pitfalls

1. **`/proc/self/status` silent procname fallback** — the `fopen` returns NULL on macOS and the beacon silently uses `"linuxbeacon"` as process name in every check-in; replace with `getprogname()` in `implant-macos/src/beacon.c` before any check-in testing; this is Phase 6 critical path

2. **`uint16_t` + `htonl()` type mismatch in beacon metadata** — pre-existing known bug (`var4`, `var5`, `var6` in `beacon.c` lines 216-226) that GCC/x86_64 tolerates accidentally; Clang/ARM64 will generate different stack layout, producing wrong bytes in the metadata packet and causing Team Server HMAC failure or silent session rejection; fix declarations to `uint32_t` in the macOS tree, do not copy the Linux bug

3. **Darwin kernel version vs. macOS marketing version** — `uname().release` returns `"24.3.0"` (Darwin) not `"15.3"` (macOS Sequoia); replace `sscanf(uts.release)` with `sysctlbyname("kern.osproductversion")` for correct operator-visible metadata

4. **Ad-hoc signing absent from Makefile** — ARM64 binaries without a signature fail silently on macOS Sequoia 15.1+ (`Killed: 9`); Clang linker auto-signs natively but a `codesign --force --sign -` target must be explicit in the Makefile for robustness; never apply post-link binary patches without re-signing

5. **Homebrew library path mismatch** — hardcoding `/opt/homebrew/` breaks on Intel Macs and CI runners; use `$(shell brew --prefix openssl@3)` and `$(shell brew --prefix curl)` in the Makefile to resolve dynamically

---

## Implications for Roadmap

Based on combined research, the implementation follows a strict dependency chain. The existing research documents already propose specific phase numbers (6-9) that map to the broader project roadmap. The phase structure below preserves those numbers and adds the rationale and ordering logic.

### Phase 6: macOS Tree Scaffold and Build System

**Rationale:** Everything downstream depends on a compilable macOS binary. The Makefile, verbatim copies, and the three targeted rewrites are prerequisites for any check-in attempt. The `uint16_t` type mismatch and the `/proc/self/status` procname fix must land here — attempting live check-in with these bugs present wastes diagnostic effort on protocol-layer confusion.

**Delivers:** A Mach-O ARM64 binary that compiles cleanly with zero Clang warnings under `-Wall -Wextra`, carries a valid ad-hoc signature, and links against Homebrew OpenSSL and libcurl via dynamic Homebrew path resolution.

**Addresses:** Table-stakes HTTP/S check-in loop, metadata generation, crypto layer, `sleep`/`exit` commands (minimum viable operator control), ad-hoc code signing.

**Avoids:** Pitfalls 1 (`/proc/self/status`), 4 (ad-hoc signing), 5 (Homebrew path mismatch), and the `uint16_t` type mismatch (Pitfall 6 in PITFALLS.md).

**Steps in order:**
1. Create `implant-macos/` directory scaffold; verbatim copy `http.c`, `crypto.c`, `profile.c`, `pivot.c`, `files.c`, all headers
2. Write `implant-macos/Makefile` with dynamic Homebrew path resolution and no ELFLoader sources
3. Rewrite `beacon.c` (macOS): replace `/proc/self/status` with `getprogname()`; fix `uint16_t`/`htonl()` to `uint32_t`; leave `uname()` for now (Darwin version acceptable at this phase)
4. Rewrite `commands.c` (macOS): remove ELFRunner include and case 200; preserve shell prefix offset
5. Update `main.c` (macOS): cosmetic debug string change only

**Research flag:** Standard patterns — no additional research needed; all decisions are resolved.

---

### Phase 7: Generation Pipeline and Live Check-in Validation

**Rationale:** A compilable binary with hardcoded values is not operator-usable. The generation pipeline extension unblocks operators from using the Aggressor workflow. Live check-in validation is the only true confirmation that the wire protocol is correct — compile success is not sufficient.

**Delivers:** An operator-configurable macOS beacon generated through the existing Aggressor workflow, with confirmed live check-in against a Team Server showing correct hostname, username, process name, and OS version.

**Addresses:** Generation pipeline routing (`--target` flag), Aggressor platform selector, human-readable macOS version in metadata (`sysctlbyname`), shell command offset validation against real session.

**Avoids:** Pitfall 3 (Darwin kernel version), Pitfall 10 (wrong libcurl TLS backend at transport validation time), "looks done but isn't" check-in validation items.

**Steps in order:**
1. Extend `InsertListenerInfo.py`, `InsertPublicKey.py`, `RemovePublicKey.py` with `--target [linux|macos]` flag
2. Extend `CustomBeacon.cna` with Platform selector row; route generation script invocations with `--target macos`
3. Replace `uname().release` parse with `sysctlbyname("kern.osproductversion")` in macOS `beacon.c`
4. Run end-to-end live check-in; validate beacon appears in Team Server console with correct metadata
5. Validate `sleep` + `pwd` + `shell` command execution and response

**Research flag:** The shell command `%COMSPEC% /C` offset (21 bytes) is HIGH confidence based on existing Linux behavior but warrants a regression fixture confirming the offset against a real macOS-directed session. Flag for validation during step 5.

---

### Phase 8: POSIX Command Parity and SOCKS Pivot

**Rationale:** With transport proven, command-by-command validation is low-risk incremental work. All remaining commands are pure POSIX and the verbatim copies from Phase 6 need only execution-path testing, not code changes.

**Delivers:** Full command parity with the Linux beacon for all in-scope commands: `cd`, `pwd`, `ls`, `upload`, `download`, SOCKS pivot (`listen`/`connect`/`send`/`close`).

**Avoids:** Accidental introduction of `epoll` calls (Linux-only; will not compile on macOS); `AF_PACKET`/`SIOCGIFHWADDR` MAC collection (Linux-only); `FD_SETSIZE` pivot socket count must be documented as a known limit.

**Research flag:** Standard patterns — no additional research needed; all POSIX APIs are confirmed present.

---

### Phase 9: Test Harness and Operator Handoff

**Rationale:** Protocol regressions during purple-team exercises are high-cost to diagnose. The existing `implant/tests/` Python test harness is partially reusable and provides immediate value with minimal adaptation effort.

**Delivers:** `implant-macos/tests/` with adapted runner; protocol/parser fixtures reused unchanged; source-anchor fixtures updated for macOS tree (no ELFRunner, `getprogname` instead of `/proc`); quarantine xattr deployment procedure documented.

**Avoids:** Pitfall 2 (metadata flag confusion — document in operator guide), quarantine xattr deployment block, debug symbol exposure in release binary.

**Research flag:** Standard patterns for test harness adaptation. Quarantine xattr deployment procedure needs documentation, not research.

---

### Phase Ordering Rationale

- **Phase 6 before Phase 7:** A non-compilable or protocol-broken binary makes live check-in testing impossible. The five pre-check-in fixes (procname, type mismatch, ad-hoc signing, Homebrew paths, command dispatcher) must all land before any Team Server interaction is attempted.
- **Phase 7 before Phase 8:** Transport validation gates command-parity work. Debugging command-level issues on top of unvalidated transport multiplies diagnostic surface area.
- **Phase 8 before Phase 9:** Command parity must be functionally complete before test fixtures are written, otherwise fixtures are written against incomplete behavior.
- **Generation pipeline in Phase 7, not Phase 6:** The operator workflow (Aggressor + Python scripts) is not on the critical path for the binary itself. A manual `python3 InsertListenerInfo.py ... --target macos && make -C implant-macos` sequence is sufficient for Phase 6 validation. Moving generation pipeline work to Phase 7 keeps Phase 6 focused on the hardest technical items.

### Research Flags

Phases needing deeper research during planning:
- **Phase 7:** Shell command `%COMSPEC% /C` offset validation against a real macOS-directed Team Server session. HIGH confidence the offset is correct but requires live-session fixture to lock in. Flag for verification during end-to-end testing step.

Phases with standard patterns (skip research-phase):
- **Phase 6:** All decisions are resolved by direct source analysis and verified compilation on the build host. No additional research needed.
- **Phase 8:** All POSIX APIs confirmed present. `select()` vs `kqueue()` is a known deferred decision. No research needed.
- **Phase 9:** Test harness adaptation follows established patterns from the existing `implant/tests/` infrastructure. No research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified on this ARM64 build host: Clang 17, OpenSSL 3.6.1, libcurl 8.18.0 confirmed installed and linked. No inference. |
| Features | HIGH | Direct source analysis of all `implant/src/` files. Command portability assessed against POSIX specification and macOS SDK. Code signing behavior confirmed via `codesign -dv`. |
| Architecture | HIGH | Based on full read of existing codebase (`implant/src/`, `implant/headers/`, `generate-payload/`, `implant/tests/`, `CustomBeacon.cna`, `.planning/PROJECT.md`). All component boundaries and data flows are code-confirmed. |
| Pitfalls | HIGH (code-confirmed) / MEDIUM (protocol-specific) | All build-system and API pitfalls are code-confirmed. Team Server metadata field semantics (var4/var5/var6, `%COMSPEC%` offset) carry MEDIUM confidence — behavior is observed from Linux deployment and community Cobalt Strike protocol research but not independently verified against macOS-targeted sessions. |

**Overall confidence:** HIGH

### Gaps to Address

- **`%COMSPEC% /C` shell task offset on macOS:** The 21-byte skip logic in `commands.c` is empirically observed from Linux behavior and expected to apply identically to macOS (server-controlled format). Validate with a regression fixture during Phase 7 live check-in. If the offset is wrong, `COMMAND_EXECUTE_JOB` returns garbled output; the fix is a constant adjustment in the macOS `commands.c`.

- **Team Server version compatibility for `var4`/`var5`/`var6` fields:** The correct wire behavior for these fields (metadata packet bytes 216-226) is inferred from the existing Linux deployment. The `uint32_t` + `htonl()` fix aligns with community CS metadata research (Unit 42 reference). Validate by confirming a successful check-in with a metadata decode tool during Phase 7.

- **macOS Sequoia Gatekeeper for non-locally-built binaries:** Ad-hoc signing is confirmed sufficient for locally compiled binaries. If the binary is transferred to a target host that did not build it, the quarantine xattr procedure (`xattr -d com.apple.quarantine`) must be tested in the Phase 9 deployment scenario. This is a procedure gap, not an architecture gap.

- **Intel Mac compatibility of macOS Makefile:** The `brew --prefix` dynamic resolution handles Intel (`/usr/local/opt/`) vs ARM64 (`/opt/homebrew/opt/`) automatically. Not tested on an Intel host. Treat as LOW-risk given Apple Silicon dominance among active operator deployments.

---

## Sources

### Primary (HIGH confidence)

- Apple Clang 17.0.0 — verified on this host: `clang --version` output and ARM64 compilation test
- Homebrew OpenSSL 3.6.1 — `brew info openssl@3`; compiled and linked on this host
- Homebrew libcurl 8.18.0 — `brew info curl`; compiled and linked on this host; `otool -L` confirms Homebrew paths
- macOS SDK POSIX header availability — verified against `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/`
- Direct source analysis of `implant/src/beacon.c`, `commands.c`, `http.c`, `crypto.c`, `profile.c`, `pivot.c`, `files.c` (all modules)
- `.planning/PROJECT.md` — platform isolation constraint, ARM64-only decision, separate tree decision
- `.planning/codebase/CONCERNS.md` — var4/var5/var6 known bug, source mutation risk
- Apple Developer Documentation: `getprogname(3)`, `getifaddrs(3)`, `sysctlbyname(3)`, `CLOCK_MONOTONIC` availability
- Apple LibreSSL linking impossibility (Big Sur+): https://github.com/orgs/Homebrew/discussions/3258
- macOS ad-hoc code signing: https://stories.miln.eu/graham/2024-06-25-ad-hoc-code-signing-a-mac-app/
- Apple Silicon requires signed code: https://eclecticlight.co/2020/08/22/apple-silicon-macs-will-require-signed-code/
- Hackaday: Apple Forces Signing in macOS Sequoia 15.1: https://hackaday.com/2024/11/01/apple-forces-the-signing-of-applications-in-macos-sequoia-15-1/

### Secondary (MEDIUM confidence)

- Palo Alto Unit 42: Cobalt Strike Metadata Encryption/Decryption — https://unit42.paloaltonetworks.com/cobalt-strike-metadata-encryption-decryption/ — basis for var4/var5/var6 field semantics interpretation
- Community Cobalt Strike protocol research (multiple sources) — shell task `%COMSPEC% /C` format is server-controlled and platform-independent
- Apple Developer Forums: uname output on M1 Mac — https://developer.apple.com/forums/thread/668206 — Darwin version format confirmation
- Hacker News: "Unsigned (arm64) binaries don't run at all on M1 Macs" — https://news.ycombinator.com/item?id=26996578

### Tertiary (LOW confidence)

- SpecterOps: ARM-ed and Dangerous: Dylib Injection on macOS (2025) — https://specterops.io/blog/2025/08/21/armed-and-dangerous-dylib-injection-on-macos/ — contextual macOS ARM64 binary execution behavior; not directly applicable to this project

---

*Research completed: 2026-02-26*
*Ready for roadmap: yes*
