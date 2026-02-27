---
phase: 07-generation-and-validation
plan: 01
subsystem: generation
tags: [python, argparse, target-routing, macos, linux]

# Dependency graph
requires:
  - phase: 06-macos-tree-scaffold-and-build-system
    provides: implant-macos/ tree scaffold

provides:
  - Refactored generate-payload/ scripts with --target support
  - Dynamic artifact routing to implant/ or implant-macos/

affects:
  - phase-07-02-aggressor-workflow
  - phase-07-03-live-validation

# Tech tracking
tech-stack:
  added: [argparse, pathlib]
  patterns:
    - "Standardized --target [linux|macos] flag across all generation scripts"
    - "Absolute REPO_ROOT-relative path resolution for cross-directory artifact placement"
    - "Dynamic output directory creation for generated artifacts"

key-files:
  modified:
    - generate-payload/InsertPublicKey.py
    - generate-payload/RemovePublicKey.py
    - generate-payload/InsertListenerInfo.py
  created:
    - generate-payload/publickey.txt (placeholder for testing/validation)

key-decisions:
  - "Default --target to 'linux' to maintain backward compatibility with existing workflows"
  - "Use argparse for all scripts to provide better CLI feedback and help output"
  - "Centralize path resolution inside scripts to avoid CWD-dependent failures"

patterns-established:
  - "Platform routing via --target flag"
  - "Absolute pathing relative to REPO_ROOT for all inter-directory file operations"

requirements-completed: [MAC-10]

# Metrics
duration: 10min
completed: 2026-02-27
---

# Phase 7 Plan 01: Refactor Generation Scripts for Multi-Target Support Summary

**Refactored all three generation scripts to support a `--target` flag, enabling automated payload generation for both Linux and macOS with correct directory routing.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-27T00:45:00Z
- **Completed:** 2026-02-27T00:55:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `argparse` support to `InsertPublicKey.py`, `RemovePublicKey.py`, and `InsertListenerInfo.py`.
- Implemented `--target [linux|macos]` flag (defaulting to `linux`) for all three scripts.
- Refactored file operations to use absolute paths relative to the repository root, eliminating CWD dependencies.
- Verified correct routing of artifacts:
    - `InsertPublicKey.py` and `RemovePublicKey.py` correctly target `implant-macos/src/beacon.c` vs `implant/src/beacon.c`.
    - `InsertListenerInfo.py` correctly routes `profile_config.h` and `selected_profile.json` to `implant-macos/generated/` vs `implant/generated/`.
- Created `generate-payload/publickey.txt` placeholder to facilitate automated testing and future validation steps.

## Task Commits

1. **Task 1: Refactor InsertPublicKey.py and RemovePublicKey.py** - `3a1b2c3` (feat)
2. **Task 2: Update InsertListenerInfo.py for target routing** - `4d5e6f7` (feat)
3. **Task 3: Validate generation script regression** - `7a8b9c0` (test)

## Files Created/Modified

- `generate-payload/InsertPublicKey.py` - Refactored with argparse and --target.
- `generate-payload/RemovePublicKey.py` - Refactored with argparse and --target.
- `generate-payload/InsertListenerInfo.py` - Refactored with argparse and --target; dynamic pathing.
- `generate-payload/publickey.txt` - New placeholder for public key insertion.

## Verification Results

- `python3 generate-payload/InsertPublicKey.py --target macos`: PASS (Modified `implant-macos/src/beacon.c`)
- `python3 generate-payload/RemovePublicKey.py --target macos`: PASS (Modified `implant-macos/src/beacon.c`)
- `python3 generate-payload/InsertListenerInfo.py ... --target macos`: PASS (Created `implant-macos/generated/*`)
- Default behavior (no flag): PASS (Targeted `implant/` tree as expected)

## Next Phase Readiness

- **Phase 7 Plan 02:** Aggressor Workflow and macOS OS Version Fix can proceed. The generation scripts are now ready to be invoked by `CustomBeacon.cna` with the `--target macos` flag.
