---
phase: 06-macos-tree-scaffold-and-build-system
plan: "01"
subsystem: infra
tags: [clang, arm64, makefile, homebrew, openssl, libcurl, macos]

# Dependency graph
requires: []
provides:
  - implant-macos/ directory tree with src/, headers/, generated/, bin/, obj/
  - 5 verbatim POSIX-portable source files (http.c, crypto.c, profile.c, pivot.c, files.c)
  - 9 verbatim header files (all from implant/headers/)
  - implant-macos/Makefile with Apple Clang, -arch arm64, dynamic Homebrew path resolution
  - generated/.gitkeep placeholder for profile_config.h generation pipeline
affects:
  - 06-02 (adds beacon.c, main.c to this tree)
  - 06-03 (adds commands.c and exercises this Makefile in build verification)

# Tech tracking
tech-stack:
  added: [Apple Clang (CC=clang), Homebrew openssl@3, Homebrew curl, codesign ad-hoc signing]
  patterns:
    - Dynamic Homebrew path resolution via $(shell brew --prefix <package>)
    - Verbatim copy with sync comment header for POSIX-portable source files
    - Separate implant-macos/ tree (no ifdefs shared with Linux implant/)
    - wildcard src/*.c pattern for source discovery (no ELFLoader)

key-files:
  created:
    - implant-macos/Makefile
    - implant-macos/src/http.c
    - implant-macos/src/crypto.c
    - implant-macos/src/profile.c
    - implant-macos/src/pivot.c
    - implant-macos/src/files.c
    - implant-macos/headers/beacon.h
    - implant-macos/headers/commands.h
    - implant-macos/headers/config.h
    - implant-macos/headers/crypto.h
    - implant-macos/headers/debug.h
    - implant-macos/headers/files.h
    - implant-macos/headers/http.h
    - implant-macos/headers/pivot.h
    - implant-macos/headers/profile.h
    - implant-macos/generated/.gitkeep
  modified: []

key-decisions:
  - "Used $(shell brew --prefix openssl@3 2>/dev/null) pattern — no hardcoded /opt/homebrew or /usr/local paths, works on both ARM64 and Intel Homebrew installs"
  - "Added check-deps target that fails fast with human-readable error messages if Homebrew dependencies missing"
  - "Ad-hoc codesign step in link target: checks for existing signature first, applies only if absent"
  - "-mmacosx-version-min=12.0 chosen for maximum Apple Silicon (M1-M4) compatibility"
  - "Sync comment format established: /* copied from implant/src/<file>, last synced 2026-02-26 */"

patterns-established:
  - "Sync comment header: first line of every verbatim-copied file identifies source path and sync date"
  - "brew --prefix pattern: dynamic Homebrew path resolution for any macOS dependency"
  - "check-deps target: validate Homebrew deps before attempting compilation"
  - "No cross-tree include paths: implant-macos/ is fully self-contained"

requirements-completed: [MAC-01, MAC-02, MAC-03]

# Metrics
duration: 5min
completed: "2026-02-27"
---

# Phase 6 Plan 01: macOS Tree Scaffold and Build System Summary

**implant-macos/ tree scaffolded with 5 verbatim POSIX source files, 9 verbatim headers, and a dynamic-Homebrew-path ARM64 Makefile — prerequisite for all macOS beacon plans**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-27T02:28:34Z
- **Completed:** 2026-02-27T02:33:16Z
- **Tasks:** 2
- **Files modified:** 16 (15 source/header/placeholder + 1 Makefile)

## Accomplishments

- Created complete implant-macos/ directory tree (src/, headers/, generated/, bin/, obj/) with 5 POSIX-portable source files and 9 header files copied verbatim from implant/ with sync comment headers
- Wrote macOS-specific Makefile with CC=clang, -arch arm64, -mmacosx-version-min=12.0, dynamic Homebrew path resolution via $(shell brew --prefix ...), and ad-hoc code signing step
- Confirmed make check-deps exits 0 and make fails only at link stage due to missing beacon.c/main.c/commands.c (expected — those are macOS rewrites in plans 06-02 and 06-03)
- No ELFLoader references anywhere in the implant-macos/ tree; tree is fully self-contained (no cross-tree -I paths)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create directory scaffold and copy verbatim source/header files** - `f3bceeb` (feat)
2. **Task 2: Write implant-macos/Makefile with Apple Clang and dynamic Homebrew path resolution** - `5843bd3` (feat)

## Files Created/Modified

- `implant-macos/Makefile` - macOS ARM64 build system with dynamic Homebrew path resolution, check-deps, ad-hoc signing
- `implant-macos/src/http.c` - libcurl HTTP GET/POST transport (verbatim copy from implant/src/http.c)
- `implant-macos/src/crypto.c` - OpenSSL EVP RSA+AES+base64 crypto layer (verbatim copy)
- `implant-macos/src/profile.c` - Profile schema consumer with generated profile_config.h support (verbatim copy)
- `implant-macos/src/pivot.c` - POSIX select()-based SOCKS pivot manager (verbatim copy)
- `implant-macos/src/files.c` - POSIX file I/O for download/upload chunking (verbatim copy)
- `implant-macos/headers/beacon.h` - beacon_state_t struct and function declarations (verbatim copy)
- `implant-macos/headers/commands.h` - Command and callback type constants (verbatim copy)
- `implant-macos/headers/config.h` - C2 server defaults and extern key declarations (verbatim copy)
- `implant-macos/headers/crypto.h` - Crypto function declarations (verbatim copy)
- `implant-macos/headers/debug.h` - Conditional debug macro definitions (verbatim copy)
- `implant-macos/headers/files.h` - File operation function declarations (verbatim copy)
- `implant-macos/headers/http.h` - HTTP response struct and function declarations (verbatim copy)
- `implant-macos/headers/pivot.h` - SOCKS pivot struct and function declarations (verbatim copy)
- `implant-macos/headers/profile.h` - Profile config struct and accessor declarations (verbatim copy)
- `implant-macos/generated/.gitkeep` - Placeholder to preserve generated/ directory in git

## Decisions Made

- Used `$(shell brew --prefix openssl@3 2>/dev/null)` pattern — no hardcoded /opt/homebrew or /usr/local paths, works on both ARM64 and Intel Homebrew installs
- Added check-deps target that exits 1 with a human-readable error message if Homebrew dependencies are missing
- Ad-hoc codesign step in link target checks for existing signature first, applies only if absent (handles Apple Clang sometimes signing automatically)
- `-mmacosx-version-min=12.0` chosen for maximum Apple Silicon (M1-M4) compatibility (Monterey baseline)
- Sync comment format established: `/* copied from implant/src/<file>, last synced 2026-02-26 */`

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — all files created successfully. Build output confirmed Makefile is syntactically valid and Homebrew paths resolve (5 source files compile). Link fails only on missing symbols from beacon.c/main.c/commands.c as expected.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- implant-macos/ tree is complete and ready for plan 06-02 to add beacon.c and main.c (macOS rewrites)
- plan 06-03 will add commands.c (ELFRunner removal) and exercise the Makefile in full build verification
- The Makefile's check-deps target confirms Homebrew openssl@3 and curl are installed and resolvable on the build host

## Self-Check: PASSED

All 17 created files verified present on disk. Task commits f3bceeb and 5843bd3 confirmed in git log.

---
*Phase: 06-macos-tree-scaffold-and-build-system*
*Completed: 2026-02-27*
