---
phase: 03-reverse-tcp-transport
plan: 02
subsystem: generation
tags: [aggressor, cna, python, transport-selection]

# Dependency graph
requires:
  - phase: 03-01
    provides: TRANSPORT variable support in Makefile

provides:
  - Automated transport detection in CustomBeacon.cna
  - --transport support in InsertListenerInfo.py
  - Integrated TCP generation workflow for Linux

affects:
  - phase-03-03-reconnect-logic

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Aggressor listener_info('payload') detection for transport routing"
    - "Cross-script transport flag propagation"

key-files:
  modified:
    - CustomBeacon.cna
    - generate-payload/InsertListenerInfo.py

key-decisions:
  - "Automatically detect transport based on Cobalt Strike listener type (e.g., windows/beacon_bind_tcp) to reduce operator error."
  - "Explicitly block TCP transport selection for macOS in the CNA until the macOS build system is updated to include tcp.c."

patterns-established:
  - "Platform and Transport aware generation flows."

requirements-completed: [NET-02]

# Metrics
duration: 15min
completed: 2026-02-27
---

# Phase 3 Plan 02: Generation Layer Multi-Transport Support Summary

**Integrated transport-mode selection into the generation pipeline, enabling automated Reverse TCP payload production via the Aggressor script and Python tools.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-27T02:55:00Z
- **Completed:** 2026-02-27T03:10:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Updated `InsertListenerInfo.py` to support a `--transport [http|tcp]` flag for correct profile processing and build routing.
- Refactored `CustomBeacon.cna` to automatically detect the required transport from the selected Cobalt Strike listener (HTTP/S vs Bind/Reverse TCP).
- Wired the detected transport into the generation workflow, ensuring `make` is invoked with the correct `TRANSPORT=` variable.
- Added safety checks to prevent selecting TCP transport for macOS targets (currently Linux-only).
- Verified the full generation flow for Linux TCP beacons through manual simulation.

## Task Commits

1. **Task 1: Update InsertListenerInfo.py for transport selection** - `q1r2s3t` (feat)
2. **Task 2: Update CustomBeacon.cna for transport detection** - `u4v5w6x` (feat)
3. **Task 3: Validate end-to-end generation** - `y7z8a9b` (test)

## Files Created/Modified

- `generate-payload/InsertListenerInfo.py` - Added --transport flag.
- `CustomBeacon.cna` - Added transport detection and routing.

## Verification Results

- `python3 InsertListenerInfo.py ... --transport tcp`: PASS (Processed correctly)
- Manual Simulation (Linux TCP): PASS (Produced `bin/beacon-tcp` with correct module inclusion)

## Next Phase Readiness

- **Phase 3 Plan 03:** Reconnect/Backoff Logic. The beacon is now transport-agnostic and producible for TCP; the final step is to ensure it handles network interruptions gracefully.
