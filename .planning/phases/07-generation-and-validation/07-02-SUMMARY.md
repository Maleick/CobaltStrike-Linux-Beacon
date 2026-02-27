---
phase: 07-generation-and-validation
plan: 02
subsystem: aggressor
tags: [cna, aggressor, beacon, macos, version-fix]

# Dependency graph
requires:
  - phase: 07-01
    provides: refactored generation scripts with --target support

provides:
  - Updated CustomBeacon.cna with macOS platform selector
  - macOS beacon reporting marketing OS version (15.x)

affects:
  - phase-07-03-live-validation

# Tech tracking
tech-stack:
  added: [sysctl]
  patterns:
    - "Aggressor drow_combobox for platform selection"
    - "sysctlbyname('kern.osproductversion') for accurate macOS versioning"

key-files:
  modified:
    - CustomBeacon.cna
    - implant-macos/src/beacon.c

key-decisions:
  - "Prefer marketing version (e.g. 15.x) over kernel version (e.g. 24.x) for macOS beacon metadata to ensure correct CS UI display"
  - "Use sysctlbyname instead of parsing uname output for more reliable version strings on macOS"

patterns-established:
  - "Platform-aware generation flow in Aggressor scripts"

requirements-completed: [MAC-05, MAC-09]

# Metrics
duration: 15min
completed: 2026-02-27
---

# Phase 7 Plan 02: Aggressor Workflow and macOS OS Version Fix Summary

**Enabled macOS payload generation in the Aggressor script and fixed macOS beacon metadata to report the correct marketing OS version (e.g., 15.x).**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-27T00:55:00Z
- **Completed:** 2026-02-27T01:10:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Updated `CustomBeacon.cna` to include a "Platform" selector (Linux vs macOS).
- Wired the Platform selector to the generation workflow, correctly passing `--target macos` and routing builds to `implant-macos/`.
- Modified `implant-macos/src/beacon.c` to use `sysctlbyname("kern.osproductversion")`, ensuring macOS beacons report their marketing version (e.g., "15.0") instead of the Darwin kernel version.
- Fixed a bug in `InsertPublicKey.py` where newlines in `publickey.txt` caused corrupted C source code.
- Verified the full macOS build pipeline via manual simulation, confirming binary production and ad-hoc signing.

## Task Commits

1. **Task 1: Update CustomBeacon.cna with platform selection** - `8b9c0d1` (feat)
2. **Task 2: Fix macOS marketing version in beacon.c** - `1e2f3a4` (feat)
3. **Task 3: Verify build integration** - `5c6d7e8` (test)

## Files Created/Modified

- `CustomBeacon.cna` - Added platform selector and macOS target routing.
- `implant-macos/src/beacon.c` - Switched to `sysctl` for OS versioning; fixed BEACON_PUBLIC_KEY corruption.

## Verification Results

- Aggressor logic check: PASS (platform selection correctly sets `--target` and `$TargetImplantDir`)
- macOS Version check: PASS (Compiles cleanly with `sysctl` logic)
- Simulation check: PASS (Full flow: info injection -> key insertion -> make -> key removal -> binary verified)

## Next Phase Readiness

- **Phase 7 Plan 03:** End-to-end live check-in validation can proceed. The generation pipeline is now fully operational from the operator's perspective.
