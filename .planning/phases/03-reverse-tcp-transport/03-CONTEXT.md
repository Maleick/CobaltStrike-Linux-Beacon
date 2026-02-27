# Phase 3: Reverse TCP Transport Mode - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Add reverse TCP as a selectable beacon transport. Operator picks a TCP listener in the Aggressor dialog; the beacon is built for TCP mode, connects out over a persistent raw TCP socket, sends check-in metadata, receives tasks, and returns callbacks. Network interruptions trigger bounded reconnect/backoff without process termination.

Scope covers: `tcp.c`/`tcp.h` transport module, `transport.h` unified interface, Makefile TCP build target, `CustomBeacon.cna` dialog/generation updates, `InsertListenerInfo.py` interface migration, and transport-mode regression tests.

HTTP/S transport behavior is unchanged by this phase.

</domain>

<decisions>
## Implementation Decisions

### Transport Mode Selection (Aggressor CNA)

- TCP mode is **auto-derived from listener type** at Generate click — no explicit transport dropdown needed
- Supported listener type for TCP: `windows/beacon_tcp/reverse_tcp`
- Dialog switches from `drow_listener_stage` to **`drow_listener`** (shows all listener types, including stageless/TCP)
- Static dialog description updated to: "Supports HTTP, HTTPS, and TCP listeners"
- On Generate click: detect `payloadType` → map to transport mode string (`http` / `https` / `tcp`)
- **Validation**: extend existing check to accept `reverse_tcp` alongside `reverse_http` and `reverse_https`
- Updated error message: "Only reverse_http, reverse_https, and reverse_tcp are supported."
- Log **`[Transport: <mode>]`** to CS console at the start of each generation run
- If operator fills a Profile Path but selects a TCP listener: **log a warning** in CS console (e.g., `[TCP MODE] Profile path ignored`) — do not error
- TCP profile path is not passed to generation scripts; profile is irrelevant for TCP
- **Success message** includes transport mode: `"TCP implant generated at ..."` (vs generic message for HTTP/S)
- No live dialog field greying or dynamic description — detection happens only at Generate click

### InsertListenerInfo.py Interface Migration

- **Clean break**: replace the old `0`/`1` HTTPS flag arg with a **transport mode string** (`http` / `https` / `tcp`)
- New call signature: `python3 InsertListenerInfo.py <host> <port> <transport_mode> [<profile_path>]`
- Profile path arg is **omitted** (not passed as empty string) when transport mode is `tcp`
- No backwards compatibility with old `0`/`1` flag — CNA is the only caller and is updated in the same phase

### TCP Transport Module (`tcp.c` / `tcp.h`)

- **New source file**: `implant/src/tcp.c` and `implant/headers/tcp.h` — mirrors existing `http.c`/`http.h` pattern
- **Persistent connection**: beacon connects once, holds socket open across all check-in cycles
- Reconnect triggers only on socket error (handled by reconnect/backoff policy — see Phase 3 plans)

### Unified Transport Interface (`transport.h`)

- `transport.h` declares a unified interface consumed by `beacon.c`:
  - `transport_checkin()` — sends metadata, reads task response
  - `transport_send_output()` — sends callback data
- `beacon.c` calls `transport_checkin()` and `transport_send_output()` — no `#ifdef` at call sites
- **Compile-time selection via `#ifdef TRANSPORT_TCP`**: Makefile links either `tcp.o` or `http.o`

### TCP Wire Protocol

- **Framing**: length-prefixed — `[4 bytes big-endian length][payload blob]` per message
- **Payload structure reused exactly**: same `[counter][length][encrypted data][HMAC]` structure as HTTP/S — no new wire format
- **Request-response model**: beacon sends check-in packet, then blocks/reads synchronously for task response; sleeps between cycles
- Existing `beacon_checkin()` encrypt/HMAC logic is unchanged

### Claude's Discretion

- RSA key injection step for TCP builds (whether `InsertPublicKey.py` applies to TCP)
- Socket fd storage location (global state vs `beacon_state_t`)
- `transport_connect()` initialization placement in the beacon main loop
- Exact Makefile variable name for transport mode flag (e.g., `TRANSPORT=tcp` vs `TRANSPORT_TCP=1`)
- Error handling and errno reporting within `tcp.c`

</decisions>

<specifics>
## Specific Ideas

- The existing `http_get()` / `http_post()` pattern in `http.c` is the direct model for `tcp_checkin()` / `tcp_send_output()` in `tcp.c`
- The `genPayload` CNA callback already has the `$payloadType` / `$HTTPSvalue` pattern; TCP transport mode extends this by mapping `reverse_tcp` → `"tcp"` string instead of a 0/1 flag

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-reverse-tcp-transport*
*Context gathered: 2026-02-26*
