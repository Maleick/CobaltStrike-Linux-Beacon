# External Integrations

**Analysis Date:** 2026-02-25

## APIs & External Services

**C2 Team Server (Primary External Service):**
- Cobalt Strike Team Server - command-and-control transport and task exchange.
  - SDK/Client: Custom HTTP implementation via libcurl in `implant/src/http.c`.
  - Auth: Session metadata + RSA/AES/HMAC workflow in `implant/src/beacon.c` and `implant/src/crypto.c`.
  - Endpoints used: compile-time URIs in `implant/headers/config.h` (`HTTP_GET_URI`, `HTTP_POST_URI`).

**Cobalt Strike Client Runtime APIs:**
- Aggressor scripting API - listener discovery and beacon task submission in `CustomBeacon.cna` and `sample_linux_bofs/execute_linux_bof.cna`.
  - Integration method: In-process Aggressor functions such as `listener_info`, `beacons.task`, `exec`.
  - Auth: Inherits authenticated Cobalt Strike client session.

**BOF Ecosystem Inputs:**
- TrustedSec/Outflank BOF object files - inline execution payload format consumed by command ID `200` in `implant/src/commands.c`.
  - Integration method: binary object payload transfer from Aggressor script to implant.
  - Auth: delivered over existing beacon channel.

## Data Storage

**Databases:**
- Not detected.

**File Storage:**
- Local filesystem only.
  - Payload/key material files under `generate-payload/` (for example `publickey.txt`, ignored by `.gitignore`).
  - Runtime file transfer uses local filesystem reads/writes through `implant/src/files.c`.

**Caching:**
- None detected (no Redis/memcached/service cache integration).

## Authentication & Identity

**Auth Provider:**
- Custom Cobalt Strike protocol identity.
  - Implementation: metadata generation and cryptographic handshake in `implant/src/beacon.c` plus RSA/AES/HMAC helpers in `implant/src/crypto.c`.
  - Token storage: in-memory `beacon_state_t` fields (`session_key`, `aes_key`, `hmac_key`) in `implant/headers/beacon.h`.
  - Session management: counter-based packet semantics (`last_server_time`, `upload_counter`).

**OAuth Integrations:**
- None detected.

## Monitoring & Observability

**Error Tracking:**
- External error tracking service not detected.

**Analytics:**
- Product analytics integration not detected.

**Logs:**
- Local stdout/stderr debug macros in `implant/headers/debug.h` (`DEBUG_PRINT`, `ERROR_PRINT`).
- No centralized log shipping integration detected.

## CI/CD & Deployment

**Hosting:**
- Not an application hosting project; distributed as locally compiled implant binaries from `implant/bin/`.
  - Deployment model: operator-generated payload via Aggressor (`CustomBeacon.cna`) or manual build flow from `SETUP.md`.

**CI Pipeline:**
- CI service configuration not detected (`.github/workflows`, GitLab CI, etc. absent).

## Environment Configuration

**Development:**
- Required compile-time values in `implant/headers/config.h` for listener host/port/HTTPS mode.
- Required key extraction step uses `generate-payload/Dump.java` against `.cobaltstrike.beacon_keys` (team server side).
- Secrets location: team server key file (`.cobaltstrike.beacon_keys`) and transient `generate-payload/publickey.txt` (gitignored).

**Staging:**
- Not detected as a distinct environment.

**Production:**
- Runtime secret material (session keys) lives in process memory only.
- No dedicated secrets manager integration detected.

## Webhooks & Callbacks

**Incoming:**
- No webhook receiver endpoints detected.

**Outgoing:**
- No webhook calls detected.
- Beacon callback channel is internal Cobalt Strike protocol traffic over HTTP(S), not generic webhooks (`implant/src/beacon.c`).

---

*Integration audit: 2026-02-25*
