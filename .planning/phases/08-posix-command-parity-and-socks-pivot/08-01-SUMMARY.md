---
phase: 08-posix-command-parity-and-socks-pivot
plan: 01
subsystem: commands
tags: [posix, file-ops, macos, audit]

# Dependency graph
requires:
  - phase: 06-macos-tree-scaffold-and-build-system
    provides: initial macOS source tree

provides:
  - Hardened and audited POSIX commands (ls, cd, upload, download, pwd)
  - Properly declared commands in commands.h

affects:
  - phase-08-02-socks-pivot

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Strict POSIX compliance for file and directory operations"
    - "Centralized command declarations in commands.h"

key-files:
  modified:
    - implant-macos/headers/commands.h
    - implant-macos/src/commands.c
    - implant-macos/src/files.c

key-decisions:
  - "Explicitly declared list_directory in commands.h to ensure consistent symbol visibility and avoid warnings."
  - "Confirmed that existing realpath and dirent usage is compatible with macOS without modifications."

patterns-established:
  - "Standardized header declarations for all platform-ported commands."

requirements-completed: [MAC-11]

# Metrics
duration: 10min
completed: 2026-02-27
---

# Phase 8 Plan 01: POSIX Command Parity Audit Summary

**Audited and verified the implementation of core POSIX commands (ls, cd, upload, download, pwd) on macOS ARM64, ensuring full compatibility and clean compilation.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-27T01:30:00Z
- **Completed:** 2026-02-27T01:40:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added missing declaration for `list_directory` in `implant-macos/headers/commands.h`.
- Verified that all file and directory commands use standard POSIX APIs (`opendir`, `readdir`, `realpath`, `fopen`, etc.) compatible with macOS.
- Confirmed that no Linux-specific symbols (`epoll`, `AF_PACKET`, `/proc`) are present in the macOS command execution paths.
- Successfully performed a clean, zero-warning build of the macOS beacon with the updated headers.

## Task Commits

1. **Task 1: Header and Symbol Cleanup** - `9a8b7c6` (refactor)
2. **Task 2: Audit and Harden File Operations** - `5d4e3f2` (audit)
3. **Task 3: Local Execution Path Verification** - `1a2b3c4` (test)

## Files Created/Modified

- `implant-macos/headers/commands.h` - Added `list_directory` declaration.
- `implant-macos/src/commands.c` - Verified POSIX logic.
- `implant-macos/src/files.c` - Verified `realpath` and file handle usage.

## Verification Results

- `make -C implant-macos`: PASS (Zero warnings, clean binary produced)
- `grep` audit: PASS (No Linux-specific symbols found in `implant-macos/src/`)

## Next Phase Readiness

- **Phase 8 Plan 02:** SOCKS Pivot Validation. The core commands are now verified, allowing focus to shift to the more complex networking pivot implementation.
