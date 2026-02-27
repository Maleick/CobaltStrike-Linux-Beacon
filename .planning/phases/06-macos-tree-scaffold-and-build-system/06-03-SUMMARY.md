---
phase: 06-macos-tree-scaffold-and-build-system
plan: 03
subsystem: build
tags: [macos, arm64, clang, mach-o, codesign, commands-c, elfrunner-removal]

# Dependency graph
requires:
  - phase: 06-01
    provides: implant-macos/ tree scaffold, Makefile with brew --prefix, all verbatim .c/.h copies
  - phase: 06-02
    provides: beacon.c with getprogname()+uint32_t fix, main.c version string

provides:
  - implant-macos/src/commands.c (macOS port without ELFRunner or case 200)
  - implant-macos/bin/beacon-macos (Mach-O 64-bit executable arm64, ad-hoc signed)
  - implant-macos/generated/profile_config.h (Phase 6 build stub)

affects:
  - phase-07-macos-beacon-core-rewrites
  - phase-08-macos-command-parity
  - phase-09-macos-stabilization

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zero-warning ARM64 Clang build enforced — all warnings treated as failures"
    - "Phase 6 build stub pattern for generated/profile_config.h (replaced in Phase 7)"
    - "pclose() return value explicitly discarded via (void) cast for -Wunused-variable compliance"
    - "__attribute__((unused)) on static helper functions not yet called"
    - "size_t for length/offset variables compared to sizeof() results"

key-files:
  created:
    - implant-macos/src/commands.c
    - implant-macos/generated/profile_config.h
  modified:
    - implant-macos/src/pivot.c

key-decisions:
  - "Fixed 4 Clang -Wall -Wextra warnings in commands.c and 2 in pivot.c for zero-warning build"
  - "dirLengthOffset changed from int to size_t to fix sign-compare warning"
  - "next_id() in pivot.c marked __attribute__((unused)) — it exists for future use but is not called in Phase 6"
  - "pclose() return value discarded via (void) cast — exit status not needed for shell command flow"
  - "print_len guarded in #ifdef DEBUG — only used by DEBUG_PRINT, not in release build"

patterns-established:
  - "Suppress unused-function warnings with __attribute__((unused)) rather than removing the function"
  - "Cast unused return values explicitly to (void) to satisfy -Wunused-variable"
  - "Use size_t consistently for length/offset variables compared against sizeof() expressions"

requirements-completed: [MAC-01, MAC-02]

# Metrics
duration: 4min
completed: 2026-02-27
---

# Phase 6 Plan 03: commands.c macOS Port and Full ARM64 Build Summary

**Mach-O ARM64 beacon-macos binary compiled with zero warnings, ad-hoc signed, linking Homebrew OpenSSL@3 and curl, confirming all Phase 6 success criteria**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-27T02:42:32Z
- **Completed:** 2026-02-27T02:46:40Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Wrote `implant-macos/src/commands.c` with ELFRunner include and case 200 BOF block removed, COMMAND_EXECUTE_JOB 4+17 byte offset preserved verbatim
- Produced `implant-macos/bin/beacon-macos`: Mach-O 64-bit executable arm64 with ad-hoc linker-signed signature
- Zero warnings under `-Wall -Wextra -O2 -arch arm64` (6 total warnings fixed across commands.c and pivot.c)
- All five Phase 6 success criteria (MAC-01 through MAC-06) verified

## Task Commits

Each task was committed atomically:

1. **Task 1: Write implant-macos/src/commands.c** - `56cb84d` (feat)
2. **Task 2: Build Mach-O ARM64 binary and verify** - `edd8fb1` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `implant-macos/src/commands.c` - macOS port: ELFRunner removed, case 200 removed, all POSIX commands preserved verbatim
- `implant-macos/generated/profile_config.h` - Phase 6 build stub (empty; profile.c falls back to config.h defaults)
- `implant-macos/src/pivot.c` - Fixed 2 Clang warnings (unused next_id function, sign-compare in host_len)

## Decisions Made

- Fixed 4 compiler warnings in commands.c (pclose unused, dirLengthOffset sign-compare, print_len unused in release): all are minor correctness issues in the verbatim Linux copy that Clang -Wextra flags on ARM64 macOS
- Fixed 2 compiler warnings in pivot.c (next_id unused-function, host_len sign-compare): verbatim copy from 06-01 that also needed attention
- `next_id()` preserved with `__attribute__((unused))` rather than deleted — it exists for future socket ID allocation use
- `dirLengthOffset` and `host_len` changed to `size_t` — correct type for lengths compared to `sizeof()` results

## Build Output

```
[CC] Compiling src/beacon.c
[CC] Compiling src/commands.c
[CC] Compiling src/crypto.c
[CC] Compiling src/files.c
[CC] Compiling src/http.c
[CC] Compiling src/main.c
[CC] Compiling src/pivot.c
[CC] Compiling src/profile.c
[LD] Linking bin/beacon-macos
[+] Build complete: bin/beacon-macos
[+] Verifying ad-hoc code signature...
[+] Ad-hoc signature present
```

Warning count: **0**

## Verification Results

**file command:**
```
implant-macos/bin/beacon-macos: Mach-O 64-bit executable arm64
```

**codesign -dv:**
```
Executable=implant-macos/bin/beacon-macos
Identifier=beacon-macos
Format=Mach-O thin (arm64)
CodeDirectory v=20400 size=709 flags=0x20002(adhoc,linker-signed) hashes=19+0 location=embedded
Signature=adhoc
Info.plist=not bound
TeamIdentifier=not set
Sealed Resources=none
Internal requirements=none
```

**otool -L (Homebrew dynamic libraries):**
```
/opt/homebrew/opt/openssl@3/lib/libssl.3.dylib (compatibility version 3.0.0, current version 3.0.0)
/opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib (compatibility version 3.0.0, current version 3.0.0)
/opt/homebrew/opt/curl/lib/libcurl.4.dylib (compatibility version 13.0.0, current version 13.0.0)
/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1356.0.0)
```

**Binary size:** 74,912 bytes

**Shell prefix offset confirmed:** `offset = 4; offset += 17;` — 4+17=21 bytes, preserved exactly from Linux version

## Phase 6 Criteria Summary

| Criterion | Result |
|-----------|--------|
| MAC-01: Clean ARM64 compilation, zero warnings | PASS — 0 warnings |
| MAC-02: Ad-hoc code signature | PASS — flags=0x20002(adhoc,linker-signed) |
| MAC-03: Homebrew dynamic library paths | PASS — /opt/homebrew/opt/openssl@3 and curl |
| MAC-04: uint32_t var4/var5/var6 | PASS — 3 matches in beacon.c |
| MAC-06: getprogname() process name | PASS — 1 match in beacon.c, no /proc/self/status |
| EXTRA: No ELFRunner in code | PASS — removed from commands.c, absent from all headers |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed 4 Clang warnings in commands.c preventing zero-warning build**
- **Found during:** Task 1 (compile check after writing commands.c)
- **Issue:** Linux verbatim copy triggered 4 -Wall -Wextra warnings on ARM64 Clang: (a) unused `status` from `pclose()`, (b) `dirLengthOffset` int vs size_t sign-compare, (c) same sign-compare in bounds check, (d) `print_len` unused in release build
- **Fix:** Cast pclose() return to (void); change dirLengthOffset to size_t; guard print_len in #ifdef DEBUG
- **Files modified:** `implant-macos/src/commands.c`
- **Verification:** Recompiled with zero output (zero warnings, zero errors)
- **Committed in:** `56cb84d` (Task 1 commit)

**2. [Rule 1 - Bug] Fixed 2 Clang warnings in pivot.c (verbatim copy from 06-01)**
- **Found during:** Task 2 (clean rebuild showing 2 warnings in pivot.c)
- **Issue:** (a) `next_id()` static function defined but not called — -Wunused-function; (b) `host_len` declared as `int` compared to `sizeof(host_z)` — -Wsign-compare
- **Fix:** Added `__attribute__((unused))` to next_id(); changed host_len to `size_t`
- **Files modified:** `implant-macos/src/pivot.c`
- **Verification:** Clean rebuild with zero warnings
- **Committed in:** `edd8fb1` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - compiler warnings blocking zero-warning success criterion)
**Impact on plan:** Both auto-fixes necessary to meet MAC-01 zero-warning requirement. No scope creep. All fixes are minimal type/suppression changes with no behavioral impact.

## Issues Encountered

None beyond the compiler warnings documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 6 complete: compilable, ad-hoc signed Mach-O ARM64 binary with correct protocol baseline exists
- Phase 7 (macOS Beacon Core Rewrites) can begin: replace profile_config.h stub with real InsertListenerInfo.py output
- Binary not yet executable without live Cobalt Strike Team Server and configured profile — that is Phase 7+ scope
- No blockers for Phase 7

---
*Phase: 06-macos-tree-scaffold-and-build-system*
*Completed: 2026-02-27*
