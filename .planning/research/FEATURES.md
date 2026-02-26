# Feature Landscape: macOS ARM64 Beacon (v2.0)

**Domain:** macOS ARM64 (M1-M4) implant target — HTTP/S Cobalt Strike beacon
**Researched:** 2026-02-26
**Scope:** What changes between Linux implant (`implant/`) and macOS implant (`implant-macos/`)

---

## Command Portability Assessment

Analysis of all existing beacon commands against macOS ARM64 POSIX availability.

### Commands That Work Unchanged on macOS (POSIX-portable)

These commands use only POSIX-portable APIs that are fully present on macOS ARM64. The logic in `implant/src/commands.c` can be copied directly into `implant-macos/` with no modification.

| Command | Command ID | Implementation | Why Unchanged |
|---------|------------|----------------|---------------|
| `sleep` | `COMMAND_SLEEP` | Read two `uint32_t`, update `g_sleep_time_ms`/`g_jitter_percent` | Pure arithmetic, no syscall |
| `cd` | `COMMAND_CD` | `chdir()` + `getcwd()` | POSIX; both available on macOS |
| `pwd` | `COMMAND_PWD` | `getcwd()` | POSIX; identical on macOS |
| `ls` | `COMMAND_FILE_LIST` | `opendir()` / `readdir()` / `closedir()` | POSIX; identical on macOS |
| `upload` | `COMMAND_UPLOAD` / `COMMAND_UPLOAD_CONTINUE` | `fopen()` / `fwrite()` / `fclose()` | POSIX; identical on macOS |
| `download` | `COMMAND_DOWNLOAD` / `COMMAND_CANCEL_DOWNLOAD` | `files.c` state machine; `fread()` + `send_output_to_server()` | POSIX; identical on macOS |
| `exit` | `COMMAND_DIE` | `send_output_to_server()` + `exit(0)` | POSIX; identical on macOS |
| SOCKS pivot | `COMMAND_LISTEN` / `COMMAND_CONNECT` / `COMMAND_SEND` / `COMMAND_CLOSE` | `pivot.c` socket state machine | POSIX sockets; macOS supports `select()`, though `kqueue` is preferred over `epoll`. `select()` path ports unchanged. |

**Confidence:** HIGH (direct source analysis, POSIX specification)

---

### Commands That Need Platform-Specific Adaptation

#### 1. `shell` — COMMAND_EXECUTE_JOB

**Current Linux behavior (commands.c lines 308-374):**

The handler hard-codes a Windows-style prefix skip: it skips 4 bytes (size field) then 17 bytes of `%COMSPEC% /C ` prefix before extracting the actual command string. This offset arithmetic is baked into the Linux implementation with the comment "Windows Shell command".

The command is then executed via `popen()`.

**macOS impact:**

`popen()` is POSIX and works on macOS. The problem is not the execution mechanism — it is the task format parsing. The Cobalt Strike team server's `shell` command format encodes the shell prefix differently depending on the registered beacon platform. The server sends `%COMSPEC% /C <cmd>` for Windows-masquerading beacons, and the Linux beacon already emits the Windows flag in its metadata (`agent_id` lowest bit cleared). The macOS beacon will face the same server-side encoding, so the same fixed-offset strip of `%COMSPEC% /C ` applies to macOS.

However, one consideration: the skip logic is undocumented and based on empirical observation. The correct offset (4 + 17 = 21 bytes) must be validated against a real team server session for macOS — particularly since future CS versions could change this.

**Adaptation required:** Low — copy the handler as-is, but add a dedicated regression fixture confirming the `%COMSPEC% /C ` prefix is indeed present in macOS-directed tasks. Flag the magic offset as a fragile constant.

**Confidence:** MEDIUM (behavior observed in Linux; macOS CS task format not independently verified)

---

#### 2. Metadata generation — `beacon_generate_metadata()`

**Current Linux implementation (beacon.c lines 120-282):**

Two Linux-specific pieces:

**a. Process name via `/proc/self/status`**

```c
FILE* fileptr = fopen("/proc/self/status", "r");
```

`/proc` does not exist on macOS. This path returns NULL on macOS; the existing fallback (`"linuxbeacon"`) triggers, so the binary does not crash — but the process name field will always be the fallback string. For a functional macOS beacon this field should reflect the actual process name.

**macOS replacement:** `getprogname()` — a libc function (`<stdlib.h>`) that returns the program name as set by the OS at launch. Available since macOS 10.4, present on all Apple Silicon targets. Zero-dependency, one call.

```c
// macOS replacement
const char *procname = getprogname();
if (!procname) procname = "macbeacon";
```

**b. OS version parsing via `uname()` + kernel release string**

```c
struct utsname uts;
uname(&uts);
int major = 0, minor = 0, build = 0;
sscanf(uts.release, "%d.%d.%d", &major, &minor, &build);
```

`uname()` is POSIX and present on macOS. However, the `release` field format is different between Linux and macOS:

- Linux example: `5.15.0-76-generic`  → parses to `major=5`, `minor=15`, `build=0`
- macOS example: `24.3.0` (Darwin kernel version) → parses to `major=24`, `minor=3`, `build=0`

The Darwin kernel version numbers are not macOS marketing version numbers. macOS 15.x (Sequoia) corresponds to Darwin 24.x kernel. The three-part numeric format (`%d.%d.%d`) parses fine, but the values reported to the team server will be Darwin kernel version numbers, not macOS 10.x/11.x/14.x/15.x marketing versions.

For purple-team use this is acceptable — the operator will see Darwin kernel numbers in the beacon metadata. If human-readable macOS version is required, it can be obtained via `sysctl kern.osproductversion` or `sw_vers`, but that adds complexity. The current `sscanf` parse works without modification for the transport goal.

The `nodename` field (`uts.nodename`) works identically on macOS — it returns the hostname.

**c. Metadata flags — `sizeof(void*) == 8` check**

```c
if (sizeof(void*) == 8) {
    flags |= METADATA_FLAG_AGENT_X64;
    flags |= METADATA_FLAG_TARGET_X64;
}
```

ARM64 is 64-bit; `sizeof(void*)` is 8 on ARM64. This sets both flags correctly. No change needed.

**Confidence:** HIGH for `getprogname()` replacement (Apple docs); MEDIUM for version number semantics (Darwin vs macOS marketing version observed empirically)

---

#### 3. Network interface enumeration — `beacon_get_local_ip()`

**Current Linux implementation (beacon.c lines 40-81):**

Uses `getifaddrs()` with `AF_INET` to enumerate IPv4 addresses. This approach is identical on macOS — `getifaddrs()`, `<ifaddrs.h>`, and `AF_INET` are all POSIX/BSD and fully available on macOS ARM64. The IP enumeration logic ports unchanged.

**MAC address note:** The current implementation does not enumerate MAC addresses for the metadata payload. If MAC address collection is added in future (it is not currently present in the metadata generation), macOS requires a different approach than Linux. Linux uses `SIOCGIFHWADDR` ioctl with `ifr_hwaddr`; macOS uses `getifaddrs()` with `AF_LINK` + `sockaddr_dl`. These are structurally different. MAC collection should be treated as a separate feature requiring macOS-specific code.

**Confidence:** HIGH — `getifaddrs()` is documented macOS API; `ifr_hwaddr`/`SIOCGIFHWADDR` Linux-only confirmed by official BSD documentation

---

#### 4. BOF execution — command ID 200

ELFLoader in `implant/elfloader/` is explicitly Linux-only (ELF object format). Mach-O BOF execution is a different format and completely separate subsystem. This command is **out of scope** per project constraints and must be omitted from `implant-macos/` entirely.

**Adaptation:** Remove case 200 from the macOS command dispatcher. Sending an unknown command ID from the team server will hit the `default:` handler, returning "Unknown command!" — acceptable for out-of-scope scope.

---

### Summary Table

| Command | Status on macOS | Work Required | Complexity |
|---------|-----------------|---------------|------------|
| `sleep` | Unchanged | None | None |
| `cd` | Unchanged | None | None |
| `pwd` | Unchanged | None | None |
| `ls` | Unchanged | None | None |
| `upload` / `upload continue` | Unchanged | None | None |
| `download` / `cancel download` | Unchanged | None | None |
| `exit` (CALLBACK_DEAD) | Unchanged | None | None |
| SOCKS pivot (listen/connect/send/close) | Unchanged | None | None |
| `shell` (COMMAND_EXECUTE_JOB) | Needs validation fixture | Regression test for offset | Low |
| Metadata: process name | `/proc` unavailable | Replace with `getprogname()` | Low |
| Metadata: OS version | Parses Darwin kernel ver | Acceptable as-is; optionally improve | Low |
| Metadata: IP enumeration | Unchanged | None | None |
| BOF execution (ID 200) | Out of scope | Omit from macOS tree | None |

---

## Table Stakes

Features that must be present for the macOS beacon to function at all with a Cobalt Strike team server.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| HTTP/S check-in loop | Without check-in the beacon does not register | Low | libcurl ports; TLS verification already disabled |
| Metadata generation with correct format | Team server rejects malformed metadata | Low-Med | `/proc` fix + verify Darwin version parse |
| AES/HMAC task decryption | Tasks are unusable without this | None | `crypto.c` uses OpenSSL; OpenSSL available on macOS via Homebrew |
| Task dispatch loop | Core command execution | None | `commands_parse_tasks()` is pure C logic |
| `sleep` command | Operator control of beacon timing | None | Pure arithmetic |
| `shell` command | Primary command execution path | Low | Validate %COMSPEC% offset against real session |
| `cd` / `pwd` | Navigation; PWD used at initial check-in | None | POSIX portable |
| `exit` / `CALLBACK_DEAD` | Operator cleanup | None | POSIX `exit()` |
| `ls` | File system reconnaissance | None | POSIX `opendir`/`readdir` |
| `upload` / `download` | File transfer | None | POSIX file I/O |
| Ad-hoc code signature | ARM64 binary will not execute without at least ad-hoc signing | Low | `codesign -s -` applied at build time; Clang linker auto-signs on Apple Silicon |
| Profile schema consumption | HTTP profile knobs must apply correctly | None | Schema is pure C preprocessor macros; reusable unchanged |

---

## Differentiators

Features that go beyond table stakes, valued but not blocking.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Human-readable macOS version in metadata | Shows "15.3 Sequoia" instead of "24.3.0 Darwin" in beacon list | Low | `sysctl kern.osproductversion` + parse; optional polish |
| MAC address collection | Richer host identification in metadata | Med | Requires AF_LINK + sockaddr_dl; macOS-specific code path |
| Process name masquerading | Beacon appears as legitimate process name in `ps` output | Med | Set via `argv[0]` manipulation or `setprogname()`; OPSEC improvement |
| SOCKS pivot via `kqueue` instead of `select` | Better performance with many pivot sockets on macOS | Med | `pivot.c` uses `select()`; `kqueue` is macOS-native and more scalable; defer unless pivot is primary use case |
| Fixture-backed regression suite for macOS commands | Prevents protocol regressions during development | Med | No test infrastructure exists; high value but scoped to separate phase |

---

## Anti-Features

Features to explicitly NOT build in v2.0.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| macOS BOF / Mach-O inline execution | ELFLoader is Linux-specific; macOS BOF requires entirely new subsystem | Out of scope per PROJECT.md; case 200 not included in macOS tree |
| macOS x86_64 support (Rosetta) | ARM64-only scope; Rosetta complicates `uname -m` detection | Ignore; ARM64 native only |
| Developer ID / notarization | Purple-team internal use only; notarization requires Apple Developer account + network submission | Ad-hoc signing is sufficient; never commit developer certificates |
| macOS Keychain integration for CA trust | Adds complexity; existing `CURLOPT_SSL_VERIFYPEER=0` already handles self-signed C2 TLS | Keep existing TLS verification disabled behavior |
| Full macOS profile permutation parity | Large scope; not required for HTTP/S default profile | Focus on default profile knobs; per PROJECT.md constraints |
| macOS persistence mechanisms (LaunchAgent, LaunchDaemon) | Out of scope for purple-team v2.0 target | Operator handles persistence externally |
| Windows Aggressor payload generation path for macOS | Existing Aggressor workflow blocks Windows path explicitly; macOS generation uses Clang/native | macOS operator host path only |

---

## Feature Dependencies

```
HTTP/S check-in  requires  OpenSSL (crypto.c)
                 requires  libcurl (http.c)
                 requires  Profile schema (profile.c)

Metadata generation  requires  uname() [POSIX - OK]
                     requires  getprogname() [macOS replacement for /proc/self/status]
                     requires  getifaddrs() [POSIX - OK]
                     requires  OpenSSL SHA256/RSA encrypt

Ad-hoc signing  required by  ARM64 binary execution (OS enforced)
                applied by   Clang linker automatically OR explicit codesign -s - post-build step

Profile schema reuse  requires  No platform ifdefs in schema files [confirmed - pure macro definitions]

macOS build tree (implant-macos/)  requires  Clang ARM64 cross-compile or native macOS build host
                                  requires  Homebrew OpenSSL (or system LibreSSL fallback)
                                  requires  Homebrew libcurl with OpenSSL backend
```

---

## Code Signing: Detailed Assessment

**Question 3 answered explicitly.**

### Can an unsigned binary run on macOS ARM64?

No. All native ARM64 binaries must have at least an ad-hoc signature. The macOS kernel rejects execution of unsigned ARM64 code. This is a hard OS-level constraint introduced in macOS 11 Big Sur (2020) and applies to all Apple Silicon M1-M4 systems.

- `METADATA_FLAG_AGENT_X64` and `METADATA_FLAG_TARGET_X64` are set correctly because `sizeof(void*)==8` on ARM64.
- The OS enforcement is not Gatekeeper (user-bypassable UI) — it is kernel-level code signing verification at exec time.

### Ad-hoc signing vs Developer ID for purple-team use

| Mechanism | Gatekeeper | Works off build host | Requires Apple account | OPSEC |
|-----------|------------|---------------------|----------------------|-------|
| No signature | Rejected at exec | N/A | No | N/A |
| Ad-hoc (`codesign -s -`) | Fails `spctl` check but bypassed for locally built binaries | Only on same host (or after manual approval on target) | No | Low — easily identified |
| Developer ID signed | Full Gatekeeper pass | Yes | Yes ($99/yr) | Medium |
| Developer ID + notarized | Best Gatekeeper pass | Yes | Yes | Medium |

**For purple-team (internal) deployment:** Ad-hoc signing is sufficient. Locally compiled binaries are not subject to Gatekeeper's spctl checks by default — macOS Sequoia's Gatekeeper tightening applies to downloaded/quarantined binaries, not locally compiled ones. The Clang linker on Apple Silicon automatically applies ad-hoc signing; no explicit post-build step is required when building natively on an M-chip Mac.

**If binary is transferred to target via upload:** The file will have the quarantine bit cleared if copied via `scp`/implant upload (no browser download), so Gatekeeper does not fire. Ad-hoc remains workable.

**Confidence:** HIGH — multiple official Apple documentation sources and Hacker News technical discussion confirmed; Sequoia Gatekeeper tightening confirmed with source.

### SIP impact

SIP (System Integrity Protection) protects specific OS directories (`/System`, `/usr`, `/sbin`, `/bin`, etc.) from modification even by root. SIP does NOT:
- Prevent execution of unsigned binaries from user-writable paths
- Prevent ad-hoc signed binaries from running
- Apply to files in `/tmp`, `/Users`, or operator-chosen drop paths

SIP is irrelevant to beacon execution as long as the binary is placed in a user-writable path. SIP does constrain `task_for_pid` / process injection capabilities, but the beacon does not use those.

---

## HTTP/S Transport: macOS Behavior

**Question 5 answered explicitly.**

### libcurl portability

libcurl's API (`curl_easy_*`, `CURLOPT_*`, `curl_slist_*`) is cross-platform. All libcurl calls in `implant/src/http.c` are portable to macOS without modification.

### TLS backend differences

The macOS system curl uses Apple's SecureTransport backend, not OpenSSL. The project's `crypto.c` depends on OpenSSL directly (SHA256, HMAC, AES, RSA). This means:

- **Recommended build path:** Link against Homebrew OpenSSL (`brew install openssl@3`) to get consistent OpenSSL 3.x on both Linux and macOS
- The existing `CURLOPT_SSL_VERIFYPEER=0` / `CURLOPT_SSL_VERIFYHOST=0` pattern works regardless of TLS backend when verification is disabled, which is the current behavior for self-signed C2 TLS

### Certificate store behavior

When `CURLOPT_SSL_VERIFYPEER=0` is set (as in the current Linux implementation), libcurl does no certificate validation at all — neither against the Keychain nor a CA bundle file. This is the existing behavior; it works identically on macOS regardless of backend. No change needed.

**Note:** SecureTransport was officially deprecated in curl as of early 2025 and will be removed. Homebrew's formula already defaults to OpenSSL on new installations. Building with Homebrew OpenSSL avoids the SecureTransport deprecation path entirely.

**Confidence:** HIGH — libcurl official documentation + Homebrew formula + curl deprecation announcement confirmed

---

## Profile Schema Reuse

**Question 6 answered explicitly.**

The profile system (`implant/src/profile.c`, `implant/headers/profile.h`) is entirely C preprocessor macro-based. The schema consists of:
- `PROFILE_ID`, `PROFILE_SCHEMA_VERSION` — string identifiers
- `PROFILE_C2_SERVER`, `PROFILE_C2_PORT`, `PROFILE_C2_USE_HTTPS` — connection params
- `PROFILE_HTTP_GET_URI`, `PROFILE_HTTP_POST_URI` — URI paths
- `PROFILE_USER_AGENT` — string constant
- `PROFILE_HEADER_0..7` — optional static HTTP headers
- Fallback to `implant/headers/config.h` if generated header absent

There are no Linux-specific values, paths, or ifdefs in the profile system. The `generated/profile_config.h` mechanism is purely a macro-definition file that the build system injects. The same schema file format can be consumed by `implant-macos/` with zero modification.

The Python generation scripts (`InsertListenerInfo.py`) target `implant/headers/config.h` by path. A macOS generation path would need a parallel script targeting `implant-macos/headers/config.h` (or equivalent generated header path), but the schema content and format are identical.

**Confidence:** HIGH — direct source code analysis

---

## Platform-Specific Pitfalls Noted

| Area | Pitfall | Impact | Mitigation |
|------|---------|--------|------------|
| Process name | `/proc/self/status` returns NULL silently | Metadata reports fallback name always | Replace with `getprogname()` |
| Shell command parse | `%COMSPEC% /C ` offset (21 bytes) not validated for macOS task format | Wrong command extracted or crash | Add fixture-backed regression test against real session |
| uname version | Darwin kernel version != macOS marketing version | Confusing beacon metadata display | Acceptable for v2.0; document in operator guide |
| Code signing | ARM64 binary silently fails to execute without signature | Beacon never starts | Clang auto-signs on-device; document for cross-compile path |
| libcurl TLS backend | System curl uses SecureTransport (deprecated 2025) | Build fragility | Use Homebrew OpenSSL explicitly in Makefile |
| MAC address | `SIOCGIFHWADDR` / `ifr_hwaddr` Linux-only | Linker error if naively ported | Not currently collected; use `AF_LINK`+`sockaddr_dl` if added |
| `select()` vs `kqueue` | `select()` works on macOS but is limited to FD_SETSIZE descriptors | Practical constraint for SOCKS at scale | Acceptable for v2.0 purple-team scope |
| BOF command (ID 200) | References `ELFRunner_include.h` (Linux-specific) | Compilation failure if included | Omit entirely; separate `commands.c` in `implant-macos/` tree |

---

## MVP Recommendation

**Phase 6 (transport baseline — what must be in this phase):**

1. HTTP/S check-in loop working on ARM64 (libcurl + OpenSSL via Homebrew)
2. Metadata generation with `getprogname()` fix (replaces `/proc/self/status` path)
3. AES/HMAC/RSA crypto layer ported (`crypto.c` — OpenSSL API; no changes needed)
4. Profile schema consumed unchanged
5. Ad-hoc code signing documented in build instructions (Clang auto-signs natively; document for cross-compile)
6. `sleep`, `exit` commands (minimum viable operator control)

**Phase 7 (command parity — defer until transport proven):**

7. `shell` command with `%COMSPEC% /C ` offset validation fixture
8. `cd`, `pwd`, `ls`, `upload`, `download` (all pure POSIX — low effort, low risk)
9. SOCKS pivot (`pivot.c` using `select()` — copy as-is from Linux)

**Defer beyond v2.0:**

- Human-readable macOS version string in metadata
- MAC address collection (requires new macOS-specific code)
- Process name masquerading
- Mach-O BOF / inline execute (separate subsystem, large scope)
- `kqueue`-based pivot socket backend

---

## Sources

- Apple Developer Documentation: `getifaddrs(3)` — https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/getifaddrs.3.html
- curl SSL CA Certificates official documentation — https://curl.se/docs/sslcerts.html
- curl `CURLOPT_SSL_VERIFYPEER` reference — https://curl.se/libcurl/c/CURLOPT_SSL_VERIFYPEER.html
- Hacker News: "Unsigned (arm64) binaries don't run at all on M1 Macs" — https://news.ycombinator.com/item?id=26996578
- Apple Silicon Macs will require signed code (Eclectic Light Company, 2020) — https://eclecticlight.co/2020/08/22/apple-silicon-macs-will-require-signed-code/
- Hackaday: Apple Forces The Signing Of Applications In MacOS Sequoia 15.1 — https://hackaday.com/2024/11/01/apple-forces-the-signing-of-applications-in-macos-sequoia-15-1/
- Ad-Hoc Code Signing a Mac Application (2024) — https://stories.miln.eu/graham/2024-06-25-ad-hoc-code-signing-a-mac-app/
- SpecterOps: ARM-ed and Dangerous: Dylib Injection on macOS (2025) — https://specterops.io/blog/2025/08/21/armed-and-dangerous-dylib-injection-on-macos/
- Apple Developer Forums: uname output on M1 Mac — https://developer.apple.com/forums/thread/668206
- curl/curl GitHub: --cacert behavior inconsistency macOS vs Linux — https://github.com/curl/curl/issues/12604
- Wikipedia: System Integrity Protection — https://en.wikipedia.org/wiki/System_Integrity_Protection
- Homebrew curl formula — https://formulae.brew.sh/formula/curl
- macOS Code Signing for Patched Binaries — https://www.storbeck.dev/posts/macos-code-signing-patched-binaries
- Direct source analysis: `implant/src/beacon.c`, `implant/src/commands.c`, `implant/src/http.c`, `implant/src/profile.c`, `implant/headers/config.h`
