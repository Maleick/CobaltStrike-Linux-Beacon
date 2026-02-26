# Architecture Research

**Domain:** macOS ARM64 Cobalt Strike Beacon implant — integration with existing Linux x64 codebase
**Researched:** 2026-02-26
**Confidence:** HIGH (based on direct source analysis of all implant modules and generation tooling)

---

## Standard Architecture

### System Overview

```
+-----------------------------------------------------------------------+
|                         OPERATOR WORKFLOW                             |
|  +----------------+   +------------------------------------------+   |
|  | CustomBeacon   |   |  generate-payload/ (Python)              |   |
|  |   .cna         |-->|  InsertListenerInfo.py                   |   |
|  | (Aggressor)    |   |  InsertPublicKey.py / RemovePublicKey.py |   |
|  +----------------+   +--------------------+---------------------+   |
|                                            |                          |
|                        writes implant[-macos]/generated/             |
+--------------------------------------------+--------------------------+
                                             |
+--------------------------------------------v--------------------------+
|                          BUILD LAYER                                  |
|  +----------------------------+  +--------------------------------+   |
|  |  implant/Makefile          |  |  implant-macos/Makefile        |   |
|  |  (gcc, Linux x64)          |  |  (clang, ARM64, separate tree) |   |
|  |  implant/generated/        |  |  implant-macos/generated/      |   |
|  |    profile_config.h        |  |    profile_config.h            |   |
|  +----------------------------+  +--------------------------------+   |
+-----------------------------------------------------------------------+
                                             |
+--------------------------------------------v--------------------------+
|                  IMPLANT RUNTIME (macOS ARM64)                        |
|  +---------+  +----------+  +-----------+  +---------------------+   |
|  | main.c  |  | beacon.c |  | commands.c|  |  http.c             |   |
|  |(loop/   |  |(metadata/|  |(task      |  | (libcurl GET/POST)  |   |
|  | signal) |  | crypto)  |  | dispatch) |  |                     |   |
|  +----+----+  +----+-----+  +-----+-----+  +----------+----------+   |
|       |            |              |                    |              |
|  +----v------------v--------------v--------------------v-----------+  |
|  |        profile.c (compile-time profile_config.h values)         |  |
|  +------------------------------------------------------------------+  |
|  +------------------------+  +--------------+  +------------------+   |
|  | crypto.c (OpenSSL EVP) |  |  pivot.c     |  |  files.c         |   |
|  | RSA/AES-128-CBC/HMAC   |  |  (SOCKS)     |  |  (download poll) |   |
|  +------------------------+  +--------------+  +------------------+   |
+-----------------------------------------------------------------------+
                                      |  HTTPS/HTTP
                               +------v------+
                               |  Cobalt     |
                               |  Strike     |
                               |  Team Server|
                               +-------------+
```

### Component Responsibilities

| Component | Responsibility | macOS Status |
|-----------|----------------|--------------|
| `main.c` | Process entry, beacon loop, signal handling, sleep/jitter | REWRITE: remove `/proc/self/status` reference; replace `usleep` with equivalent; update debug version string |
| `beacon.c` | Metadata generation, RSA encrypt, AES/HMAC task decrypt, check-in/send | REWRITE: replace `/proc/self/status` procname read with `getprogname()` (BSD/macOS); `uname()` still works on macOS but reports Darwin kernel version |
| `http.c` | libcurl GET (metadata in Cookie header), libcurl POST (AES+HMAC packet) | COPY VERBATIM — no platform-specific code; pure libcurl |
| `crypto.c` | OpenSSL EVP: RSA-PKCS1, AES-128-CBC, HMAC-SHA256, base64 via BIO | COPY VERBATIM — OpenSSL EVP API is cross-platform |
| `profile.c` | Compile-time constants from `generated/profile_config.h` with config.h fallback | COPY VERBATIM — pure preprocessor logic, no platform code |
| `commands.c` | Task parser/dispatcher, shell via popen, cd/pwd/ls/upload/download/SOCKS | REWRITE: remove ELFRunner (Linux BOFs are out of scope per PROJECT.md); verify `COMMAND_EXECUTE_JOB` shell prefix handling |
| `pivot.c` | SOCKS socket lifecycle (select, connect, read, write, reaper) | COPY VERBATIM — pure POSIX socket API; `CLOCK_MONOTONIC` is available on macOS |
| `files.c` | Download chunked transfer, upload write, download poll | COPY VERBATIM — pure POSIX file I/O |

---

## Recommended Project Structure

```
CobaltStrike-Linux-Beacon/
|
+-- implant/                        # Existing Linux x64 tree (unchanged)
|   +-- Makefile
|   +-- src/
|   +-- headers/
|   +-- generated/                  # Written by InsertListenerInfo.py (linux path)
|   +-- elfloader/
|
+-- implant-macos/                  # New macOS ARM64 tree
|   +-- Makefile                    # Separate: CC=clang, target=arm64-apple-macos11
|   +-- src/
|   |   +-- main.c                  # REWRITE: remove /proc, fix version string
|   |   +-- beacon.c                # REWRITE: remove /proc/self/status, use getprogname()
|   |   +-- commands.c              # REWRITE: remove ELFRunner, verify shell prefix
|   |   +-- http.c                  # COPY from implant/src/http.c
|   |   +-- crypto.c                # COPY from implant/src/crypto.c
|   |   +-- profile.c               # COPY from implant/src/profile.c
|   |   +-- pivot.c                 # COPY from implant/src/pivot.c
|   |   +-- files.c                 # COPY from implant/src/files.c
|   +-- headers/
|   |   +-- beacon.h                # COPY verbatim (struct layout unchanged)
|   |   +-- commands.h              # COPY verbatim (command IDs/callbacks unchanged)
|   |   +-- config.h                # COPY verbatim (fallback constants)
|   |   +-- crypto.h                # COPY verbatim
|   |   +-- debug.h                 # COPY verbatim
|   |   +-- files.h                 # COPY verbatim
|   |   +-- http.h                  # COPY verbatim
|   |   +-- pivot.h                 # COPY verbatim
|   |   +-- profile.h               # COPY verbatim
|   +-- generated/                  # Written by generation pipeline for macOS target
|       +-- profile_config.h        # Rendered by render_profile_header.py (gitignored)
|       +-- selected_profile.json   # Intermediate (gitignored)
|
+-- profiles/                       # SHARED unchanged — target-agnostic schema
|   +-- http/
|       +-- default-profile.json
|       +-- nondefault-profile.json
|
+-- generate-payload/               # MODIFY: add --target flag for macOS routing
|   +-- InsertListenerInfo.py       # MODIFY: --target linux|macos routes generated/ path
|   +-- InsertPublicKey.py          # MODIFY: --target linux|macos routes beacon.c path
|   +-- RemovePublicKey.py          # MODIFY: --target linux|macos routes beacon.c path
|   +-- render_profile_header.py    # UNCHANGED (target-agnostic renderer)
|   +-- validate_profile.py        # UNCHANGED (schema-only, target-agnostic)
|
+-- CustomBeacon.cna                # MODIFY: add Platform selection, macOS build path
```

### Structure Rationale

- **`implant-macos/` separate tree:** Enforces the "no platform ifdefs" constraint in PROJECT.md. Each tree compiles independently with its own Makefile and generated/ directory. No risk of Linux assumptions bleeding into macOS sources through conditional compilation.
- **`profiles/` shared:** Profile JSON defines HTTP transport behavior (URIs, headers, user-agent, host/port). The schema has no platform fields. The renderer (`render_profile_header.py`) produces pure C preprocessor defines that work identically in both trees. Zero changes needed.
- **`generate-payload/` modified, not duplicated:** The Python generation scripts are build-time tools. A `--target` flag (defaulting to `linux` for backward compatibility) routes output to the correct tree's `generated/` directory and the correct `beacon.c` path for public key mutation.
- **`generated/` per-tree:** Each implant tree owns its own `generated/` subdirectory. Both are gitignored. This eliminates the risk of one platform's generation artifacts contaminating the other's build.

---

## Architectural Patterns

### Pattern 1: Verbatim Copy for Pure POSIX/OpenSSL Modules

**What:** Copy `http.c`, `crypto.c`, `profile.c`, `pivot.c`, `files.c`, and all headers to `implant-macos/` without modification. No symlinks. No shared include paths.

**When to use:** When all system calls in a module are POSIX (sockets, file I/O, select, fcntl, getpid), all crypto is OpenSSL EVP API, and all profile logic is pure preprocessor.

**Verified portable modules:**
- `http.c`: libcurl + snprintf + malloc/free only
- `crypto.c`: OpenSSL EVP only
- `profile.c`: preprocessor defines only, no runtime platform detection
- `pivot.c`: select()/fcntl()/POSIX sockets + clock_gettime(CLOCK_MONOTONIC) — available macOS 10.12+, all Apple Silicon targets run macOS 11.0 minimum
- `files.c`: POSIX file I/O + realpath only
- All headers: struct definitions and function declarations, no platform ifdefs

**Trade-offs:** Introduces copy duplication — if `http.c` is patched for a Linux bug, the macOS copy must be updated manually. For five files this is manageable. The tradeoff is explicitly accepted by the "no shared ifdefs" architecture decision in PROJECT.md.

### Pattern 2: Targeted Rewrite for Platform-Specific Modules

**What:** For `main.c`, `beacon.c`, and `commands.c`, create macOS-specific versions that replace platform-specific subsystems while preserving all protocol semantics exactly.

**Specific rewrites required:**

`beacon.c` — two platform-specific sections to change:

1. Process name retrieval in `beacon_generate_metadata()`:
   - Linux: reads `/proc/self/status` with `fgets` + `sscanf("Name:%31s", procname)`
   - macOS: replace with `getprogname()` (BSD/macOS, available since macOS 10.0) or `proc_name(getpid(), procname, sizeof(procname))` from `libproc.h` (macOS 10.5+)
   - Recommended: `getprogname()` — simpler, no extra header, universally available on Apple Silicon targets

2. OS version reporting in metadata:
   - `uname(&uts)` works on macOS. `uts.release` returns Darwin kernel version (e.g., "25.4.0" for macOS 26). These are cosmetic display values in the Cobalt Strike metadata — the Team Server does not reject beacons based on OS version. Reporting Darwin kernel major/minor is acceptable for purple-team use without special handling.

`main.c` — one cosmetic change:
   - Debug string: `"Linux Cobalt Strike Beacon"` should read `"macOS ARM64 Beacon"` for operator identification in debug builds. No functional impact.

`commands.c` — two sections to change:

1. Remove ELFRunner BOF subsystem:
   - Delete `#include "ELFRunner_include.h"`
   - Remove `case 200:` entirely. The default case in `commands_execute()` returns `"Unknown command!"` which is correct behavior for an unsupported command.
   - macOS BOF/Mach-O execution is explicitly out of scope per PROJECT.md.

2. `COMMAND_EXECUTE_JOB` shell prefix:
   - The current implementation skips 4+17 bytes to strip `%COMSPEC% /C ` from the CS-generated shell command.
   - The Cobalt Strike team server sends this Windows-format prefix for the `shell` command regardless of beacon platform. This offset logic must be preserved on macOS — the wire format from the server is the same.
   - HIGH confidence this skip offset is correct for macOS: CS shell task format is server-controlled and platform-independent.

**Protocol contract that must not change:**
- Metadata magic: `0x0000BEEF` in big-endian at offset 0
- Session key: 16 raw bytes at offset 8
- Agent flags: `METADATA_FLAG_AGENT_X64 = 2`, `METADATA_FLAG_TARGET_X64 = 4` — must remain set for ARM64 (pointer size is 8 bytes on ARM64)
- All callback IDs (CALLBACK_OUTPUT, CALLBACK_PWD, CALLBACK_FILE, etc.) — unchanged
- All command IDs (COMMAND_SLEEP, COMMAND_CD, COMMAND_PWD, etc.) — unchanged

### Pattern 3: Generation Pipeline Routing via --target Flag

**What:** Extend `InsertListenerInfo.py`, `InsertPublicKey.py`, and `RemovePublicKey.py` to accept a `--target [linux|macos]` argument that routes output paths.

**Current hardcoded paths in InsertListenerInfo.py:**
```
GENERATED_DIR = REPO_ROOT / "implant/generated"
SELECTED_PROFILE_PATH = GENERATED_DIR / "selected_profile.json"
GENERATED_HEADER_PATH = GENERATED_DIR / "profile_config.h"
```

**macOS routing (with --target macos):**
```
GENERATED_DIR = REPO_ROOT / "implant-macos/generated"
```
The `render_profile_header.py` call receives `--output` pointing to whichever generated/ path is active — no changes to the renderer itself.

**Current hardcoded path in InsertPublicKey.py:**
```
"../implant/src/beacon.c"
```
With `--target macos` this becomes `"../implant-macos/src/beacon.c"`.

**Backward compatibility:** Default `--target linux` preserves existing behavior for the Linux generation workflow. The existing Aggressor calls to these scripts work unchanged until the macOS option is wired in.

---

## Data Flow

### macOS Build Generation Flow

```
Operator (Aggressor dialog)
  | listener host, port, https_value, profile_path, target=macos
  v
CustomBeacon.cna genPayload callback
  |
  v
python3 InsertListenerInfo.py <host> <port> <https> <profile> --target macos
  | reads profiles/http/<profile>.json
  | writes implant-macos/generated/selected_profile.json
  | calls render_profile_header.py --output implant-macos/generated/profile_config.h
  v
python3 InsertPublicKey.py --target macos
  | reads generate-payload/publickey.txt
  | mutates BEACON_PUBLIC_KEY[256] in implant-macos/src/beacon.c
  v
make -C implant-macos clean && make -C implant-macos OUTPUT=<name>
  | clang -target arm64-apple-macos11
  | -I./headers -I./generated  (picks up profile_config.h)
  | -lssl -lcrypto -lcurl
  | produces implant-macos/bin/<name>  (Mach-O ARM64)
  v
python3 RemovePublicKey.py --target macos
  | restores stub key in implant-macos/src/beacon.c
  v
show_message("Generated at .../implant-macos/bin/<name>")
```

### macOS Runtime Check-in Flow

```
main() -> profile_load() -> beacon_init() -> pivot_init()
  |
  v (loop: running == 1)
download_poll()
beacon_checkin(state)
  |
  +-> beacon_generate_metadata()
  |     getpid(), getenv("USER"), getprogname()  [macOS-specific procname]
  |     uname() -> Darwin kernel version
  |     beacon_get_local_ip() via getifaddrs()   [POSIX, unchanged]
  |
  +-> crypto_rsa_encrypt(metadata) -> 256-byte RSA blob (BEACON_PUBLIC_KEY)
  |
  +-> http_get(profile_get_http_get_uri(), encrypted_metadata)
  |     libcurl GET with Cookie: base64(RSA-blob)
  |     -> Team Server
  |     <- AES-128-CBC task blob + HMAC-SHA256
  |
  +-> beacon_decrypt_tasks() -> verify HMAC, decrypt AES, check replay counter
        |
        v
      commands_parse_tasks(task_data, task_len)
        | auto-detect v1 (no header) vs v2 (8-byte per-task header)
        v per task
      commands_execute()
        | popen() for shell commands
        | POSIX filesystem ops for cd/pwd/ls/upload/download
        | pivot_* calls for SOCKS
        v
      send_output_to_server(output, len, callback_type)
        -> beacon_send_output()
           -> AES encrypt + HMAC + http_post() -> Team Server
pivot_poll(pivot_callback_func)
nanosleep/usleep -> beacon_sleep()
```

### Key Data Flows

1. **Profile injection:** `profiles/http/*.json` is target-agnostic. `InsertListenerInfo.py --target macos` writes listener values into the profile, then `render_profile_header.py` emits `implant-macos/generated/profile_config.h`. The `profile.c` module reads these defines at compile time. No runtime file reads. The profile pipeline is entirely shared — only the output path differs per target.

2. **Public key injection:** `generate-payload/publickey.txt` contains the Team Server's DER-encoded RSA public key in hex. `InsertPublicKey.py --target macos` reads it and performs an in-place substitution of the `BEACON_PUBLIC_KEY[256]` array initializer in `implant-macos/src/beacon.c`. After `make`, `RemovePublicKey.py --target macos` restores the stub. This is the existing mutation model; only the target file path changes.

3. **Task dispatch:** The Cobalt Strike server sends an AES-128-CBC encrypted task blob with HMAC-SHA256 appended. `beacon_decrypt_tasks()` verifies HMAC, decrypts, checks the Unix timestamp counter. `commands_parse_tasks()` auto-detects server version (v1/v2 layout). `commands_execute()` dispatches on command ID. All protocol semantics are byte-identical on macOS — there is no platform-specific framing at the wire level.

---

## Phase 6 Build Order (Transport Baseline)

The dependency chain for a working HTTP check-in on macOS ARM64 is strictly ordered. Each step unblocks the next.

```
Step 1: Create implant-macos/ directory scaffold
  Copy verbatim: http.c, crypto.c, profile.c, pivot.c, files.c, all headers
  Create stub rewrites for: main.c, beacon.c, commands.c
  UNBLOCKS: Step 2

Step 2: Write implant-macos/Makefile
  CC = clang
  CFLAGS includes: -target arm64-apple-macos11
  No elfloader/ sources (removed from SOURCES list)
  LDFLAGS: -lssl -lcrypto -lcurl (Homebrew paths for Apple Silicon)
  UNBLOCKS: Step 3 (can attempt build)

Step 3: Rewrite beacon.c (macOS)
  Replace /proc/self/status with getprogname()
  Confirm uname() field semantics for Darwin
  Rewrite main.c cosmetic string only
  UNBLOCKS: Step 4 (binary compiles)

Step 4: Rewrite commands.c (macOS)
  Remove ELFRunner include and case 200
  Verify COMMAND_EXECUTE_JOB shell prefix offset
  UNBLOCKS: Step 5

Step 5: Extend generate-payload/ with --target macos
  Add --target flag to InsertListenerInfo.py, InsertPublicKey.py, RemovePublicKey.py
  UNBLOCKS: Step 6

Step 6: Extend CustomBeacon.cna
  Add Platform row to dialog (Linux / macOS ARM64)
  Route $ImplantSrcDirectory and generation script args based on selection
  UNBLOCKS: Operator-driven workflow

Step 7: Manual end-to-end validation
  Run generation pipeline manually (python scripts + make)
  Execute binary against Team Server
  Confirm beacon appears in CS console
  Confirm sleep + pwd + shell commands return correct output
  UNBLOCKS: Step 8

Step 8: macOS test harness
  Create implant-macos/tests/ with adapted runner
  Update source anchor expectations (no ELFRunner, getprogname)
  Run fixture regression suite
```

Steps 3 and 5 are the critical-path items for Phase 6. Step 3 (beacon.c rewrite) determines whether the binary can check in at all. Step 5 (generation pipeline) determines whether operators can produce configured binaries without manual script invocation.

Do NOT attempt Step 7 (live check-in) before Step 4 is complete — debugging protocol issues and command dispatch issues simultaneously multiplies diagnostic surface area.

---

## Anti-Patterns

### Anti-Pattern 1: Shared source via symlinks or cross-tree include paths

**What people do:** Point `implant-macos/Makefile` `-I` flags at `implant/headers/` or add symlinks to share source files.

**Why it's wrong:** Forces platform ifdefs (`#ifdef __APPLE__`) into what should be shared headers. This violates the "no platform ifdefs" constraint from PROJECT.md. A change to `implant/src/commands.c` for a Linux BOF fix could silently break the macOS build. The coupled build is harder to reason about and harder to test independently.

**Do this instead:** Maintain verbatim copies in `implant-macos/src/` and `implant-macos/headers/` for portable modules. Note the copy source in a comment at the top of each file (e.g., `/* copied from implant/src/http.c, last synced 2026-02-26 */`). Update manually when the Linux source changes.

### Anti-Pattern 2: Single `generated/` directory shared by both targets

**What people do:** Both `InsertListenerInfo.py` runs write to `implant/generated/profile_config.h`, which both Makefiles include via a shared `-I` path.

**Why it's wrong:** A macOS generation run overwrites the Linux profile config. An operator who generates a macOS payload then immediately generates a Linux payload gets the macOS profile baked into the Linux binary until regenerated. The in-place mutation pattern already creates fragility; sharing the generated directory amplifies it.

**Do this instead:** Each implant tree owns its `generated/` subdirectory. The `--target` flag controls which path receives output. Both `implant/generated/` and `implant-macos/generated/` are gitignored.

### Anti-Pattern 3: Requiring macOS operator host for the generation workflow

**What people do:** Assume the Aggressor generation dialog only needs to work when the Cobalt Strike client runs on macOS.

**Why it's wrong:** The existing `CustomBeacon.cna` checks `substr(cwd(), 0, 1) eq "/"` to detect a Unix host and runs local shell commands via `exec()`. Cobalt Strike clients are commonly run on Linux. For Phase 6 (internal purple-team use), targeting macOS operators running CS natively is acceptable, but the architecture should not prevent future use from Linux hosts (which would require a macOS cross-compilation toolchain or a remote build step).

**Do this instead:** Document the Phase 6 constraint explicitly in the Aggressor script: macOS generation requires running the CS client on a macOS host with Homebrew dependencies installed. Add a check in the CNA dialog that detects macOS (`uname` check) when the macOS target is selected and shows a warning if the operator host is not macOS.

### Anti-Pattern 4: Treating compile success as validation of correctness

**What people do:** Consider Phase 6 complete when `clang` produces a Mach-O binary without errors.

**Why it's wrong:** The critical contract is the Cobalt Strike wire protocol — metadata format, AES+HMAC task decryption, callback packet structure. A binary that compiles correctly but has a wrong byte order in the agent_id field, wrong flag bits, or a truncated info string will check in but appear broken or be silently dropped by the Team Server depending on the CS version.

**Do this instead:** After the first successful build, run a live check-in against a Team Server and confirm all three: (a) the beacon appears in the CS console with correct hostname and user, (b) `sleep` and `pwd` tasks execute and return correct output, (c) the beacon ID is stable across reconnects. Only after live validation is Phase 6 transport baseline considered done.

---

## Integration Points

### External Services

| Service | Integration Pattern | macOS Notes |
|---------|---------------------|-------------|
| Cobalt Strike Team Server | libcurl HTTP GET (metadata in Cookie: base64), HTTP POST (AES+HMAC blob at `?id=<agent_id>`) | Protocol is identical on macOS. Team Server does not distinguish platform from wire format. Session flags `METADATA_FLAG_AGENT_X64=2` and `METADATA_FLAG_TARGET_X64=4` must remain set for ARM64 (pointer size 8 bytes). |
| OpenSSL | EVP API for RSA-PKCS1, AES-128-CBC, HMAC-SHA256, base64 via BIO | macOS does not ship OpenSSL. Homebrew OpenSSL at `/opt/homebrew/opt/openssl@3` (Apple Silicon path) is required. Makefile must add `-L$(brew --prefix openssl)/lib -I$(brew --prefix openssl)/include`. |
| libcurl | curl_easy_* API, curl_slist_* for headers | macOS ships libcurl but it links against Secure Transport (Apple TLS), not OpenSSL. For TLS backend consistency, link against Homebrew curl: `brew install curl`. Use `-L$(brew --prefix curl)/lib`. Alternatively, the system libcurl works for HTTPS if TLS verification is disabled (already done: `CURLOPT_SSL_VERIFYPEER=0`, `CURLOPT_SSL_VERIFYHOST=0`). |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| main.c <-> beacon.c | Direct function calls (beacon_init, beacon_checkin, beacon_cleanup, beacon_sleep) + shared globals (g_beacon_state, g_sleep_time_ms, g_jitter_percent) | Globals declared in main.c, externed in beacon.c and commands.c. Pattern copies unchanged to macOS tree. |
| beacon.c <-> http.c | Direct calls to http_get(), http_post(), http_response_free() | http.c calls profile_get_*() internally — profile is compiled in, no runtime argument passing needed. |
| beacon.c <-> crypto.c | Direct calls: crypto_rsa_encrypt(), crypto_aes_decrypt(), crypto_aes_encrypt(), base64_encode(), crypto_random_bytes() | No platform dependencies. Copies verbatim. |
| commands.c <-> beacon.c | send_output_to_server() calls beacon_send_output(g_beacon_state, ...) | g_beacon_state is the global pointer set in main(). Unchanged in macOS tree. |
| commands.c <-> pivot.c | command_listen_socks(), command_connect_socks(), command_send_socks(), command_close_socks() direct calls; callback via pivot_callback_func function pointer | pivot.c is fully POSIX — copy verbatim. |
| commands.c <-> files.c | command_download(), command_download_stop(), download_poll() direct calls | files.c is fully POSIX — copy verbatim. |
| generate-payload/ <-> implant-macos/ | Python scripts write to implant-macos/generated/ and mutate implant-macos/src/beacon.c | --target macos flag controls path routing. Mutation model (in-place file rewrite) is preserved. |
| CustomBeacon.cna <-> generate-payload/ | exec() calls Python scripts from $GeneratePayloadDirectory | macOS generation adds Platform row to dialog; sets $ImplantSrcDirectory to implant-macos/ when macOS is selected. Python scripts receive --target macos. |
| profiles/ <-> generate-payload/ | InsertListenerInfo.py reads JSON from profiles/http/; render_profile_header.py writes profile_config.h | Fully shared. Profile schema has no platform-specific fields. Zero changes needed. |

### Test Harness Compatibility

The existing `implant/tests/` Python test harness is partially reusable for macOS:

| Test Module | macOS Reuse | Notes |
|-------------|-------------|-------|
| `test_task_parser.py` | Full reuse — runs as Python model | Pure Python reimplementation of `validate_task_layout` and `commands_parse_tasks`. No binary dependency. Works for macOS protocol validation without modification. |
| `test_protocol_roundtrip.py` | Partial — path adjustment needed | References `root.parent / "src/beacon.c"` for source anchor checks. For macOS, root must point to `implant-macos/tests/` so the relative path resolves to `implant-macos/src/beacon.c`. Create `implant-macos/tests/` with an adapted runner. |
| `test_command_smoke.py` | Partial — fixture expectations change | Checks source anchors in commands.c. The macOS version removes ELFRunner — the anchor check for `ELFRunner` will fail. Create macOS-specific smoke fixtures that do not expect ELFRunner. |
| `test_profile_matrix.py` | Full reuse | Operates on JSON profiles and rendered headers. If implant-macos/tests/ shares the same fixture paths for profiles/, these tests run unchanged. |
| `run_regression.py` + `run_regression.sh` | Copy to `implant-macos/tests/` with path adjustments | SUITE_MODULES paths are relative to SCRIPT_DIR. A macOS copy of the runner with its own fixture_index.json is the cleanest approach. The Makefile test-quick and test-full targets in implant-macos/Makefile point at implant-macos/tests/run_regression.sh. |

Recommended approach for Phase 6: Create `implant-macos/tests/` that copies the runner infrastructure. Reuse all protocol/parser fixtures unchanged (they are wire-format models). Update only the source-anchor fixtures to match the macOS-specific source tree (no ELFRunner, getprogname instead of /proc).

---

## Sources

- Direct source analysis of all files in `implant/src/`, `implant/headers/`, `generate-payload/`, `implant/tests/`, `CustomBeacon.cna` (read 2026-02-26, HIGH confidence)
- `.planning/PROJECT.md`: platform isolation constraint, ARM64-only decision, separate tree decision (read 2026-02-26)
- `.planning/codebase/STRUCTURE.md`: naming conventions, directory purposes (read 2026-02-26)
- `.planning/codebase/INTEGRATIONS.md`: external service integration map (read 2026-02-26)
- macOS API availability: `getprogname()` available since macOS 10.0; `CLOCK_MONOTONIC` since macOS 10.12; all Apple Silicon targets run macOS 11.0 minimum. All referenced POSIX APIs are present in the macOS SDK. (HIGH confidence — standard macOS SDK documentation)

---

*Architecture research for: macOS ARM64 beacon implant integration with existing Linux x64 codebase*
*Researched: 2026-02-26*
