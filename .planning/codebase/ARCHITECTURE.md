# Architecture

**Analysis Date:** 2026-02-25

## Pattern Overview

**Overall:** Monolithic native beacon executable with script-driven build/task orchestration.

**Key Characteristics:**
- Single-process implant loop in `implant/src/main.c`.
- Protocol, command, file transfer, and SOCKS pivot logic are compiled into one binary under `implant/src/`.
- Build-time behavior and C2 target parameters are injected by Aggressor + Python scripts (`CustomBeacon.cna`, `generate-payload/*.py`).
- BOF execution is delegated to vendored ELFLoader components under `implant/elfloader/`.

## Layers

**Build & Generation Layer:**
- Purpose: produce configured implant binaries for specific listeners and keys.
- Contains: `CustomBeacon.cna`, `generate-payload/InsertListenerInfo.py`, `generate-payload/InsertPublicKey.py`, `generate-payload/RemovePublicKey.py`.
- Depends on: Cobalt Strike Aggressor runtime, Python3, GNU Make.
- Used by: operators generating payloads in Cobalt Strike client or manual Linux build workflow.

**C2 Protocol Layer:**
- Purpose: establish session metadata, encrypt/decrypt traffic, and exchange task/output packets.
- Contains: `implant/src/beacon.c`, `implant/src/http.c`, `implant/src/crypto.c`, `implant/headers/beacon.h`.
- Depends on: OpenSSL, libcurl, compile-time config in `implant/headers/config.h`.
- Used by: main event loop and command execution callbacks.

**Task Execution Layer:**
- Purpose: parse task blobs and execute command-specific actions.
- Contains: `implant/src/commands.c`, `implant/src/files.c`, `implant/src/pivot.c`, `implant/headers/commands.h`.
- Depends on: protocol layer for send/receive and callback emission.
- Used by: decrypted task processing in beacon check-in cycle.

**BOF Compatibility Layer:**
- Purpose: execute Linux BOF object payloads in-process.
- Contains: `implant/elfloader/elfloader-src/*.c` and `implant/elfloader/elfloader-headers/*.h`.
- Depends on: task parser custom command flow (ID 200) in `implant/src/commands.c`.
- Used by: Aggressor BOF tasking script `sample_linux_bofs/execute_linux_bof.cna`.

## Data Flow

**Payload Generation Flow:**
1. Operator runs `Generate Custom Beacons` menu action in `CustomBeacon.cna`.
2. Aggressor validates listener type and extracts host/port/protocol with `listener_info`.
3. `generate-payload/InsertListenerInfo.py` rewrites `implant/headers/config.h` macros.
4. `generate-payload/InsertPublicKey.py` injects DER public key bytes into `implant/src/beacon.c`.
5. `make` builds `implant/bin/<name>` via `implant/Makefile`, then `RemovePublicKey.py` restores placeholder key line.

**Beacon Runtime Loop:**
1. `implant/src/main.c` initializes `beacon_state_t`, signal handlers, and pivot subsystem.
2. `beacon_checkin` in `implant/src/beacon.c` sends metadata/task requests using `implant/src/http.c`.
3. Decrypted tasks are parsed in `commands_parse_tasks` and dispatched by `commands_execute` (`implant/src/commands.c`).
4. Command output is wrapped with callback type and sent through `beacon_send_output`.
5. Loop also polls file downloads (`implant/src/files.c`) and SOCKS sockets (`implant/src/pivot.c`) before next sleep/jitter cycle.

**State Management:**
- Central state object: `beacon_state_t` in `implant/headers/beacon.h`.
- Global mutable runtime knobs: `g_sleep_time_ms`, `g_jitter_percent`, and `g_beacon_state` in `implant/src/main.c`.
- Additional subsystem-local linked lists for file transfer and pivot sockets in `implant/src/files.c` and `implant/src/pivot.c`.

## Key Abstractions

**Beacon Session State (`beacon_state_t`):**
- Purpose: runtime identity/session and pending task/output state.
- Examples: `session_key`, `aes_key`, `hmac_key`, `agent_id`, `last_server_time`, `upload_counter`.
- Pattern: shared mutable state passed through beacon subsystem and referenced globally for callbacks.

**Task/Callback ID Contract:**
- Purpose: map incoming command IDs and outgoing callback IDs to behaviors.
- Examples: `COMMAND_SLEEP`, `COMMAND_EXECUTE_JOB`, `CALLBACK_OUTPUT`, `CALLBACK_ERROR` in `implant/headers/commands.h`.
- Pattern: protocol constant table with large switch-based dispatch in `implant/src/commands.c`.

**Socket/File Transfer Entries:**
- Purpose: track long-lived stream/file operations across loop iterations.
- Examples: `socket_entry_t` (pivot sockets) and `file_entry` list for downloads.
- Pattern: intrusive linked-list state machines polled in main loop.

## Entry Points

**Implant Binary Entry:**
- Location: `implant/src/main.c` (`int main(void)`).
- Triggers: process launch of compiled implant binary.
- Responsibilities: initialize beacon state, perform recurring check-in/task loop, coordinate pivot/file polling.

**Payload Generation Entry:**
- Location: `CustomBeacon.cna` (`genBeaconMenu`, `genPayload`).
- Triggers: Cobalt Strike Script Manager menu action.
- Responsibilities: collect listener info, run generation scripts, invoke `make`, notify operator.

**BOF Tasking Entry:**
- Location: `sample_linux_bofs/execute_linux_bof.cna` (`alias linux_id`, `alias linux_cat`).
- Triggers: operator command aliases in beacon console.
- Responsibilities: read BOF object bytes and send custom command 200 task payload.

## Error Handling

**Strategy:** Return-code driven local handling with callback/error-message fallback.

**Patterns:**
- C functions generally return `0/-1` and guard allocation/network calls (`implant/src/http.c`, `implant/src/crypto.c`).
- Command handlers emit `CALLBACK_ERROR` or textual failure messages for operator visibility (`implant/src/commands.c`, `implant/src/files.c`).
- SSL/network failures are logged through `ERROR_PRINT` and may continue looping rather than aborting process.

## Cross-Cutting Concerns

**Logging:**
- Compile-time debug macro system in `implant/headers/debug.h` gated by `-DDEBUG`.

**Validation:**
- Task parsing includes protocol layout probing/sanity checks (`validate_task_layout` in `implant/src/commands.c`).
- Input validation is present but inconsistent across command handlers.

**Authentication:**
- Session authenticity relies on RSA-encrypted metadata bootstrap and AES/HMAC packet protections (`implant/src/beacon.c`, `implant/src/crypto.c`).

---

*Architecture analysis: 2026-02-25*
*Update when major patterns change*
