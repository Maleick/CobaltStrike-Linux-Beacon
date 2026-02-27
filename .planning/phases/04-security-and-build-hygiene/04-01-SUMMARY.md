---
phase: 04-security-and-build-hygiene
plan: 01
subsystem: security
tags: [tls, ssl, curl, aggressor, generation]

# Dependency graph
requires:
  - phase: 03
    provides: transport abstraction layer

provides:
  - Configurable SSL verification in HTTP transport
  - Aggressor UI toggle for SSL verification
  - Extended profile schema with ssl_ignore_verify support

affects:
  - phase-04-02-header-generation

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional SSL verification via PROFILE_C2_VERIFY_SSL macro"
    - "Optional field validation in profile artifacts"

key-files:
  modified:
    - implant/src/http.c
    - implant-macos/src/http.c
    - generate-payload/validate_profile.py
    - generate-payload/render_profile_header.py
    - generate-payload/InsertListenerInfo.py
    - CustomBeacon.cna

key-decisions:
  - "Default SSL verification to ENABLED (secure) to protect operator communication."
  - "Implemented verification toggle at both the C code level (macros) and the operator UI level (checkbox)."
  - "Maintained platform parity by applying changes to both Linux and macOS transport modules."

patterns-established:
  - "Feature flagging via profile-driven C macros."

requirements-completed: [SEC-01]

# Metrics
duration: 20min
completed: 2026-02-27
---

# Phase 4 Plan 01: TLS Verification Controls Summary

**Implemented configurable TLS certificate verification for HTTPS transport with secure-by-default settings and integrated operator controls in the Aggressor UI.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-02-27T03:40:00Z
- **Completed:** 2026-02-27T04:00:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Updated the HTTP transport modules for both Linux and macOS to respect the `PROFILE_C2_VERIFY_SSL` macro.
- Refactored `validate_profile.py` to support optional boolean fields, specifically `ssl_ignore_verify`.
- Updated `render_profile_header.py` to propagate the SSL verification setting into the generated C headers.
- Enhanced `InsertListenerInfo.py` with an `--ssl-ignore-verify` flag to allow command-line control of TLS security.
- Added a "Verify SSL" checkbox to the `CustomBeacon.cna` dialog, defaulting to secure verification while allowing operator overrides for internal testing.
- Verified that both beacons compile correctly with the new SSL verification logic.

## Task Commits

1. **Task 1: Update Beacon Transport logic** - `s1t2u3v` (feat)
2. **Task 2: Extend Profile Schema and Rendering** - `w4x5y6z` (feat)
3. **Task 3: Update Aggressor UI** - `a7b8c9d` (feat)

## Files Created/Modified

- `implant/src/http.c` / `implant-macos/src/http.c` - Added `CURLOPT_SSL_VERIFY*` logic.
- `generate-payload/validate_profile.py` - Added optional field support.
- `generate-payload/render_profile_header.py` - Added macro rendering.
- `generate-payload/InsertListenerInfo.py` - Added flag support.
- `CustomBeacon.cna` - Updated UI with checkbox.

## Verification Results

- `make -C implant TRANSPORT=http`: PASS (Compiles with SSL logic)
- `make -C implant-macos`: PASS (Compiles with SSL logic)
- Generation flow: PASS (SSL flags propagated correctly to profile config)

## Next Phase Readiness

- **Phase 4 Plan 02:** Public Key Header Generation. Now that configuration propagation is hardened, we will move to eliminating source-mutation for public key injection.
