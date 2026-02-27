# Phase 04 Context: Security and Build Hygiene

## Objective
Harden the HTTPS transport defaults and improve the build pipeline by eliminating tracked source file mutations and ensuring temporary artifact cleanup.

## Requirements
- **SEC-01**: HTTPS transport verifies certificates by default with explicit opt-out configuration.
- **SEC-02**: Key/listener build-time injection no longer mutates tracked C source files in-place.
- **SEC-03**: Payload generation cleans temporary key/config artifacts after build completion.

## Decisions

### SEC-01: TLS Verification
- Secure default: Verification is ENABLED by default.
- Implementation: `CURLOPT_SSL_VERIFYPEER` and `CURLOPT_SSL_VERIFYHOST` set to `1L` unless overridden.
- Toggle: Aggressor dialog will have an "Ignore SSL Errors" checkbox (default: unchecked).
- Profile Schema: Add `ssl_ignore_verify` (bool) to profile JSON and generated header.

### SEC-02: Build-time Key Injection
- Instead of searching and replacing strings in `beacon.c`, we will use a generated header `generated/public_key.h`.
- `beacon.c` will `#include "generated/public_key.h"`.
- The header will define the `BEACON_PUBLIC_KEY` array.
- This prevents `git status` from showing modified files after a generation run.

### SEC-03: Cleanup
- `make clean` will be updated to remove everything in `generated/`.
- Aggressor script will be responsible for ensuring a clean state after successful generation.

## Constraints
- Must support both Linux (`implant/`) and macOS (`implant-macos/`) targets.
- Must maintain compatibility with existing profile loading logic.
- Do not break the ability to build manually (though manual builds will now require running the generation scripts first to create headers).

## Claude's Discretion
- Name of the new script: `generate-payload/GeneratePublicKeyHeader.py`.
- Name of the macro/variable in `public_key.h`: `BEACON_PUBLIC_KEY`.
- Location of generated artifacts: `implant/generated/` and `implant-macos/generated/`.
