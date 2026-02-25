# Coding Conventions

**Analysis Date:** 2026-02-25

## Naming Patterns

**Files:**
- C source files use lowercase snake_case (for example `implant/src/beacon.c`, `implant/src/files.c`).
- Header names mirror module names (`implant/headers/beacon.h`, `implant/headers/http.h`).
- Script filenames use descriptive PascalCase or snake_case depending on ecosystem (`generate-payload/InsertPublicKey.py`, `sample_linux_bofs/build.sh`).

**Functions:**
- C functions are lower snake_case (`beacon_checkin`, `commands_execute`, `command_download`).
- Global helper callbacks follow subsystem naming (`pivot_callback_func`, `write_callback`).
- Aggressor Script functions frequently use camelCase (`genBeaconMenu`, `genPayload`).

**Variables:**
- Local variables are lower snake_case in C (`response_code`, `ciphertext_len`, `task_len`).
- Macros/constants are UPPER_SNAKE_CASE (`COMMAND_SLEEP`, `CALLBACK_ERROR`, `SLEEP_TIME`).
- Global mutable state uses `g_` prefix (`g_beacon_state`, `g_sleep_time_ms`, `g_pivot_list`).

**Types:**
- Struct types use `_t` suffix (`beacon_state_t`, `http_response_t`, `socket_entry_t`).
- Internal linked-list structs may omit `_t` typedef (`file_entry` in `implant/src/files.c`).
- Enum-style constants are macro defines rather than C enums (`implant/headers/commands.h`).

## Code Style

**Formatting:**
- Formatting tool config (clang-format/uncrustify/astyle) not detected.
- Indentation is mostly 4 spaces; occasional tab indentation appears in legacy blocks.
- Braces predominantly follow K&R style (`if (...) {`) with mixed spacing in older sections.
- Semicolons are always required (C/Aggressor syntax).

**Linting:**
- Static lint configuration not detected.
- Warnings are enabled in build via `-Wall -Wextra` in `implant/Makefile`.
- Debug instrumentation is compile-flag controlled with `-DDEBUG`.

## Import Organization

**Order:**
1. Related project headers first in many modules (`"beacon.h"`, `"crypto.h"`, etc.).
2. C standard library headers.
3. OS/network/third-party headers (`<curl/curl.h>`, OpenSSL, socket headers).
4. Local debug/support headers (`"debug.h"`, `"pivot.h"`).

**Grouping:**
- Includes are grouped logically but not strictly sorted alphabetically.
- Blank-line grouping appears between local and system headers.

**Path Aliases:**
- Not used; project relies on relative include paths and Makefile `-I` flags.

## Error Handling

**Patterns:**
- Functions generally return `0` on success and `-1` (or nonzero) on failure.
- Allocation and I/O errors are checked close to call sites with early returns.
- Command handlers emit error callbacks/messages to C2 (`CALLBACK_ERROR`) instead of terminating process.

**Error Types:**
- Parse/validation failures are handled with bounds checks and guard clauses.
- Network/crypto failures are logged via `ERROR_PRINT` and surfaced through return codes.
- Long-lived loop typically continues running after recoverable failures.

## Logging

**Framework:**
- Logging is macro-based in `implant/headers/debug.h`.
- `DEBUG_PRINT` and hex dump macros are compiled out unless `DEBUG` is defined.

**Patterns:**
- Diagnostic logging is concentrated around protocol/task/socket operations.
- Error messages use stderr when debug is enabled (`ERROR_PRINT`).
- No structured logging backend or log-level routing integration detected.

## Comments

**When to Comment:**
- Protocol and packet layout details are heavily documented inline (`implant/src/beacon.c`, `implant/src/commands.c`).
- Comments explain byte-order and legacy protocol behavior more than obvious code operations.
- TODO/FIXME tags are sparse; intent comments are preferred.

**JSDoc/TSDoc:**
- Not applicable to this C/Aggressor/Python codebase.

**TODO Comments:**
- Formal `TODO(owner)` convention not detected.
- Existing future work is tracked in `README.md` rather than inline tags.

## Function Design

**Size:**
- Core dispatcher/transport functions can be large (for example `commands_execute` in `implant/src/commands.c`).
- Utility helpers remain smaller and focused (`write_callback`, `crypto_random_bytes`).

**Parameters:**
- Binary protocol handlers use pointer + length signatures (`const uint8_t *data, size_t len`).
- Output buffers are commonly returned through out-parameters (`uint8_t **output`, `size_t *output_len`).

**Return Values:**
- Integer status codes dominate C interfaces.
- Callback type and payload are often separated (`commands_execute` sets `callback_type` + output buffer).

## Module Design

**Organization:**
- One responsibility cluster per file: protocol (`beacon.c`), transport (`http.c`), crypto (`crypto.c`), tasking (`commands.c`), pivot (`pivot.c`), file transfer (`files.c`).
- Header/source pair layout under `implant/headers` and `implant/src`.

**Dependencies:**
- Shared state crosses module boundaries via extern globals (`g_beacon_state`, sleep/jitter globals).
- `commands.c` acts as a central integration hub and therefore has the highest coupling.

**Reusability:**
- Reusable protocol constants/interfaces are centralized in headers.
- Build-time scripts intentionally mutate source/header values; treat them as part of generation pipeline, not reusable libraries.

---

*Convention analysis: 2026-02-25*
