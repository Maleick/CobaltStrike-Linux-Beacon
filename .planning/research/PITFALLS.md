# Pitfalls Research

**Domain:** macOS ARM64 C implant port — adding `implant-macos/` target to existing Linux x64 C beacon
**Researched:** 2026-02-26
**Confidence:** HIGH (code-confirmed for project-specific issues; MEDIUM for Team Server protocol specifics)

---

## Critical Pitfalls

### Pitfall 1: /proc/self/status Hard-Coded Procname Lookup Breaks Silently on macOS

**What goes wrong:**
`beacon.c:beacon_generate_metadata()` reads `/proc/self/status` to get the process name and falls back to the string `"linuxbeacon"` if the file cannot be opened. On macOS, `/proc/` does not exist. The `fopen` call returns NULL, so the beacon silently uses `"linuxbeacon"` as the process name in every check-in metadata packet sent to Team Server. The beacon checks in successfully, the HMAC passes, tasking works — but the Team Server beacon listing shows `"linuxbeacon"` as the process name for a macOS host, which is wrong and may confuse operators during purple-team exercises.

**Why it happens:**
The fallback string was written for Linux and no macOS alternative (`getprogname()`, `sysctl KERN_PROCARGS2`, or `argv[0]`) was plumbed in. The `/proc` path is not a compile-time guard — it is a runtime open, so it compiles and links cleanly on macOS.

**How to avoid:**
In `implant-macos/`, replace the `fopen("/proc/self/status")` block with:
```c
#include <string.h>
// macOS: use getprogname() — returns the calling process name
const char *procname = getprogname();
if (!procname) procname = "macosbeacon";
```
`getprogname()` is available on all Darwin/macOS versions without any additional libraries. Do not use `#ifdef __APPLE__` inside the shared `implant/` tree — keep the macOS-specific version entirely in `implant-macos/` per the platform isolation decision.

**Warning signs:**
- Operator console shows process name `"linuxbeacon"` for a macOS beacon session
- Compile produces no warnings because the path is a runtime string, not a compile-time symbol

**Phase to address:** Phase 6 (initial macOS tree scaffold) — must be resolved before any check-in testing

---

### Pitfall 2: Metadata Flags Report Wrong Architecture on ARM64

**What goes wrong:**
`beacon.c` sets `METADATA_FLAG_AGENT_X64` and `METADATA_FLAG_TARGET_X64` based on `sizeof(void*) == 8`. On macOS ARM64, `sizeof(void*)` is 8, so both flags are set, which is correct for 64-bit. However, the comment in the code notes the beacon is masking itself as a Windows beacon (`id & ~1` to unset bit 0). Team Server interprets the flag byte differently for different OS contexts. If Team Server uses the flag byte to distinguish Linux from Windows from macOS sessions, the macOS beacon will still appear as a Linux/Windows session unless additional platform bits are set.

**Why it happens:**
The flag byte definition only captures 32-vs-64 and admin status. The existing codebase has no macOS-specific flag. The Cobalt Strike metadata format as documented in community research uses the flag byte for architecture, not OS type — OS type is inferred from context (check-in protocol version, profile, and possibly the sysname string in the info field).

**How to avoid:**
The `utsname.sysname` field populated by `uname()` will be `"Darwin"` on macOS rather than `"Linux"`. Ensure the tab-delimited metadata string `computer\tuser\tprocessname` from `uts.nodename` is populated correctly — `nodename` does work on macOS. The sysname is not explicitly included in the metadata string sent, so Team Server relies on the operator to identify the OS from the session beacon. Document this in the macOS tree clearly: the beacon will check in as a 64-bit non-admin or admin session; operators must identify it as macOS from the hostname/username context. No protocol change is required.

**Warning signs:**
- Team Server beacon list shows what looks like a Windows x64 session; operators cannot distinguish macOS from Linux

**Phase to address:** Phase 6 (scaffold) — document at tree setup; Phase 7 (check-in) — validate metadata appearance in Team Server during first check-in test

---

### Pitfall 3: OS Version Metadata Parses Darwin Kernel Version, Not macOS Version

**What goes wrong:**
`beacon.c` uses `sscanf(uts.release, "%d.%d.%d", &major, &minor, &build)` to extract OS version for the metadata packet. On Linux, `uname -r` gives something like `"5.15.0"` (kernel version). On macOS, `uname -r` gives the Darwin kernel version, e.g. `"24.3.0"` for macOS Sequoia 15.3. The Darwin kernel version is offset from the marketing macOS version: Darwin 24.x = macOS 15.x (Sequoia), Darwin 23.x = macOS 14.x (Sonoma). The major byte in the metadata will be `24` or `25`, not `15` — which is nonsensical to Team Server operators reading the OS version metadata.

**Why it happens:**
The code assumes `uname().release` gives a meaningful OS version. On Linux this is a reasonable approximation. On macOS the Darwin version has no direct user-visible meaning.

**How to avoid:**
In `implant-macos/`, replace the `sscanf(uts.release)` version parse with a `sysctl` call to `kern.osproductversion` or parse `/System/Library/CoreServices/SystemVersion.plist` to get the actual macOS version string (e.g. `"15.3.0"`). The simplest correct approach is:
```c
char os_ver[32] = {0};
size_t os_ver_len = sizeof(os_ver);
sysctlbyname("kern.osproductversion", os_ver, &os_ver_len, NULL, 0);
// Then sscanf(os_ver, "%d.%d.%d", &major, &minor, &build)
```
This requires `#include <sys/sysctl.h>` which is available on all macOS versions.

**Warning signs:**
- Team Server metadata shows OS major version `24` or `25` for macOS sessions instead of `15`

**Phase to address:** Phase 7 (macOS check-in implementation)

---

### Pitfall 4: Ad-Hoc Signing Required on Every Build — Missing It Causes Silent Execution Failure on Sequoia

**What goes wrong:**
On macOS ARM64 (Apple Silicon), all native executables must be signed to run. The linker (`clang` on macOS 11+) applies an ad-hoc signature automatically at link time if no explicit signing identity is specified. However, this automatic ad-hoc signature is invalidated if the binary is subsequently modified (e.g., by the current `InsertPublicKey.py` / `InsertListenerInfo.py` in-place source mutation pipeline adapted for macOS). On macOS Sequoia 15.1+, the ability to bypass Gatekeeper for unsigned binaries has been entirely removed for user-interactive paths. On macOS 15.x, a binary with a broken or absent signature will fail to execute — the error is often presented as "can't be opened because Apple cannot check it for malicious software" or a cryptic `Killed: 9` in the terminal.

**Why it happens:**
The Linux payload generation pipeline (`generate-payload/*.py`) rewrites source files in-place and recompiles. If an equivalent macOS pipeline does the same — modify source, recompile — the linker will re-sign automatically. But if the pipeline modifies the compiled binary after linking (e.g., patching bytes directly), the signature is invalidated with no warning at modification time; the failure only surfaces at execution.

**How to avoid:**
- Never modify the compiled macOS binary after linking. All configuration injection (C2 server, port, key) must happen at compile time via generated headers, not post-link binary patching.
- After every compile, add an explicit ad-hoc re-sign step: `codesign --force --sign - ./beacon-macos`
- For purple-team deployment, if the binary is transferred across the network, the `com.apple.quarantine` xattr must be removed: `xattr -d com.apple.quarantine ./beacon-macos`. Quarantine-flagged binaries trigger Gatekeeper even if ad-hoc signed.
- Confirm the CONCERNS.md-documented source mutation pipeline is NOT adapted for macOS; instead use the recommended immutable-source approach with generated includes.

**Warning signs:**
- `Killed: 9` at runtime with no other error message
- `codesign -vv <binary>` reports "invalid signature" or "no signature"
- `spctl --assess --verbose <binary>` reports "rejected"

**Phase to address:** Phase 6 (build system setup for macOS tree) — the `codesign --force --sign -` step must be a mandatory Makefile target, not optional

---

### Pitfall 5: Homebrew Library Path Mismatch Breaks Build on ARM64 Macs

**What goes wrong:**
The Linux `Makefile` uses `LDFLAGS = -lssl -lcrypto -lcurl` with no explicit include or library paths, relying on GCC finding system libraries in standard locations. On macOS ARM64, Homebrew installs libraries to `/opt/homebrew/` (not `/usr/local/`). The system-provided `libcurl` on macOS uses Apple's Secure Transport TLS backend, not OpenSSL, meaning `#include <openssl/sha.h>` and `#include <openssl/hmac.h>` (used in `beacon.c` and `crypto.c`) will not be found without explicit `-I/opt/homebrew/opt/openssl@3/include`. The macOS `Makefile` must explicitly set:
```
CFLAGS += -I/opt/homebrew/opt/openssl@3/include -I/opt/homebrew/opt/curl/include
LDFLAGS = -L/opt/homebrew/opt/openssl@3/lib -L/opt/homebrew/opt/curl/lib -lssl -lcrypto -lcurl
```
If these paths are hardcoded, they will break on Intel-transition machines using `/usr/local/homebrew` or on CI runners where Homebrew paths differ.

**Why it happens:**
Homebrew relocated the prefix from `/usr/local/` to `/opt/homebrew/` with the introduction of Apple Silicon support. Any Makefile that hardcodes `/usr/local/` or relies on the compiler finding headers without explicit paths will silently fail with "file not found" for OpenSSL headers.

**How to avoid:**
Use `$(shell brew --prefix openssl@3)` and `$(shell brew --prefix curl)` in the macOS `Makefile` to resolve paths dynamically:
```makefile
OPENSSL_PREFIX := $(shell brew --prefix openssl@3)
CURL_PREFIX := $(shell brew --prefix curl)
CFLAGS += -I$(OPENSSL_PREFIX)/include -I$(CURL_PREFIX)/include
LDFLAGS += -L$(OPENSSL_PREFIX)/lib -L$(CURL_PREFIX)/lib -lssl -lcrypto -lcurl
```
This is robust across Intel and ARM64 Homebrew installs.

**Warning signs:**
- `fatal error: 'openssl/ssl.h' file not found` at compile time
- `ld: library not found for -lcurl` at link time when using system curl (which has no OpenSSL)
- `building for macOS-arm64 but attempting to link with file built for macOS-x86_64` — indicates mixing Rosetta/Intel library with native ARM64 build

**Phase to address:** Phase 6 (macOS build system) — must be solved before any compilation is attempted

---

### Pitfall 6: var4/var5/var6 uint16_t + htonl() Type Mismatch — Clang Generates Different Code Than GCC

**What goes wrong:**
`beacon.c` lines 216-226 have a pre-existing known bug (documented in CONCERNS.md): `var4`, `var5`, and `var6` are declared as `uint16_t` but `htonl()` (which returns `uint32_t`) is called on them, and then 4 bytes are written via `memcpy`. On Linux x86_64 with GCC, this often "works" accidentally due to stack layout and GCC's behavior of silently truncating the `uint16_t` variable before passing to `htonl`. Clang on macOS with `-Wall -Wextra` will emit `-Wimplicit-int-conversion` warnings for this, but more critically: Clang's optimizer on ARM64 may generate different register-width operations for this pattern, meaning the 4 bytes written to the metadata buffer could contain different values than the Linux GCC build produces.

**Why it happens:**
`htonl(uint16_t)` on a 16-bit value: the value is implicitly widened to `uint32_t` before `htonl`, byte-swapped as 32 bits, but only the low 16 bits of the result are stored in the `uint16_t` variable. Then `memcpy(offset, &var4, 4)` reads 4 bytes from `&var4` — 2 bytes of the var4 value plus 2 bytes of whatever is adjacent on the stack. On GCC/x86_64 the adjacent bytes are often the next variable; on Clang/ARM64 the stack frame and register spill layout may differ, producing different garbage bytes for the upper 2 bytes. If Team Server validates these fields, the macOS beacon may fail to check in.

**How to avoid:**
This must be fixed in `implant-macos/` before the macOS tree can produce a valid check-in. Declare all three variables as `uint32_t` and use `htonl()` correctly, or keep them as `uint16_t` and use `htons()` with 2-byte `memcpy`. The correct fix depends on what Team Server actually expects in those fields. The existing Linux behavior should be reproduced exactly: use `uint32_t` + `htonl()` + 4-byte `memcpy`.

**Warning signs:**
- Clang emits `-Wimplicit-int-conversion` or `-Wshorten-64-to-32` on these lines
- Team Server shows HMAC failure or metadata parse error on first macOS check-in
- Values in metadata dissection tool (`cs-decrypt-metadata.py`) show wrong bytes for var4-6 fields

**Phase to address:** Phase 7 (macOS check-in) — fix immediately when porting `beacon.c` to `implant-macos/`; do not copy the Linux bug

---

## Moderate Pitfalls

### Pitfall 7: Local IP Byte Order Comment Is Wrong — But Works by Accident; May Diverge on macOS

**What goes wrong:**
`beacon.c:beacon_get_local_ip()` has a comment claiming the returned value is "in correct byte order (little endian)" and the fallback is `0x0100007f` (which is 127.0.0.1 in little-endian). However, `sin_addr.s_addr` from `getifaddrs` is in network byte order (big-endian). The function returns network-byte-order data but the comment claims little-endian. Later, `beacon_generate_metadata()` wraps this in another `htonl()` call, double-converting it. On x86_64 Linux (little-endian host), the double-conversion may produce the correct wire bytes by coincidence. On macOS ARM64, which is also little-endian, the same coincidental behavior applies — so this particular bug will likely not manifest differently on ARM64. However, the confusion creates risk during future debugging.

**How to avoid:**
When porting to `implant-macos/`, clean up the `beacon_get_local_ip()` function to have a consistent return convention (return host-byte-order `uint32_t`, then `htonl()` once in `beacon_generate_metadata`). Since macOS is also little-endian this will not break behavior, but the code will be correct and maintainable.

**Warning signs:**
- IP address appears byte-swapped in Team Server beacon listing

**Phase to address:** Phase 7 (check-in implementation) — clean up as part of port, validate IP display in Team Server

---

### Pitfall 8: getifaddrs() AF_LINK Entries on macOS Must Be Skipped Explicitly

**What goes wrong:**
`beacon.c:beacon_get_local_ip()` iterates `getifaddrs` and checks `ifa->ifa_addr->sa_family == AF_INET`. The code already checks `if (ifa->ifa_addr == NULL) continue;` which is correct. However, on macOS, `getifaddrs` returns additional entries with `sa_family == AF_LINK` (link-layer addresses). The NULL check before the `sa_family` test already handles this correctly. There is no crash risk. The behavioral difference from Linux is that macOS returns more interface entries (one `AF_LINK` entry per interface plus the `AF_INET`/`AF_INET6` entries). The existing filter `sa_family == AF_INET` already correctly ignores `AF_LINK` entries.

**Why it is still a risk:**
If a future developer adds MAC address collection to the macOS version and tries to use the same loop, they will need `AF_LINK` handling via `struct sockaddr_dl` (macOS) rather than `AF_PACKET` + `struct sockaddr_ll` (Linux). These are incompatible types.

**How to avoid:**
The existing IP collection code works correctly on macOS as-is. For any MAC address collection in the macOS tree, use `AF_LINK` + `struct sockaddr_dl` pattern rather than the Linux `AF_PACKET` pattern:
```c
#include <net/if_dl.h>
if (ifa->ifa_addr->sa_family == AF_LINK) {
    struct sockaddr_dl *sdl = (struct sockaddr_dl *)ifa->ifa_addr;
    unsigned char *mac = (unsigned char *)LLADDR(sdl);
    // mac[0..5] is the MAC address
}
```

**Warning signs:**
- Compilation error: `struct sockaddr_ll` or `AF_PACKET` undefined on macOS
- Link-layer address lookup returns garbage or zero MAC addresses

**Phase to address:** Phase 8 (command parity) — only relevant when MAC address or interface enumeration commands are ported

---

### Pitfall 9: select() FD_SETSIZE Limit in pivot.c — macOS Default Is 1024 (Same as Linux Default, but macOS kqueue Is the Right Fix)

**What goes wrong:**
`pivot.c` uses `select()` for all SOCKS socket management. `select()` has a hard limit of `FD_SETSIZE` file descriptors (default 1024 on both Linux and macOS). On macOS, the correct high-performance replacement is `kqueue()`/`kevent()`, while on Linux it is `epoll()`. The CONCERNS.md already flags "epoll/kqueue abstraction for scale." The macOS port will inherit the `select()` limitation.

**Why it matters for macOS specifically:**
On macOS, `DYLD_LIBRARY_PATH` and Sandbox restrictions can cause unexpected fd exhaustion in some contexts. More critically, `select()` on macOS does not modify the timeout value on return (unlike Linux where `select()` modifies `tv` to reflect remaining time), so the 10ms timeout behavior in `pivot_poll_checker` is safe and correct.

**How to avoid:**
For the purple-team v2.0 scope (internal use, low pivot socket count), copying the `select()`-based pivot.c to `implant-macos/` is acceptable. Do not introduce `epoll()` calls in the macOS tree — `epoll` is Linux-specific and will not compile on macOS. If scaling is needed in a future milestone, use `kqueue()`.

**Warning signs:**
- Compilation error: `epoll_create`, `epoll_ctl`, `epoll_wait` undefined on macOS
- More than ~900 simultaneous pivot sockets causes silent degradation

**Phase to address:** Phase 8 (SOCKS pivot) — confirm no `epoll` calls are added; mark `kqueue` as a future improvement

---

### Pitfall 10: libcurl on macOS Uses Secure Transport by Default — CURLOPT_SSL_VERIFYPEER=0 Behavior Differs

**What goes wrong:**
`http.c` disables SSL verification with `CURLOPT_SSL_VERIFYPEER=0` and `CURLOPT_SSL_VERIFYHOST=0`. This works identically on macOS when using Homebrew's libcurl (which is OpenSSL-backed). However, macOS ships a system `libcurl` that uses Apple's Secure Transport TLS backend. If the macOS build accidentally links against the system libcurl (via `-lcurl` without the Homebrew path), the `CURLOPT_SSL_VERIFYPEER=0` still works to disable verification. The more significant risk is that the system libcurl does not expose `CURLOPT_CAINFO` (pointing to a CA bundle file) because Secure Transport uses the macOS Keychain. Any future code that attempts to set `CURLOPT_CAINFO` with a hardcoded Linux path like `/etc/ssl/certs/ca-certificates.crt` will silently fail (return `CURLE_UNKNOWN_OPTION` or be ignored) on macOS.

**How to avoid:**
- Ensure the macOS `Makefile` links against Homebrew libcurl (`$(brew --prefix curl)/lib`) to guarantee consistent OpenSSL-backed behavior
- Never hardcode Linux CA bundle paths. The macOS CA bundle location is `/etc/ssl/cert.pem` but this is irrelevant as long as `CURLOPT_SSL_VERIFYPEER=0` is in use for the Team Server connection
- Document that macOS TLS cert verification is intentionally disabled per the same design decision as Linux

**Warning signs:**
- `curl_easy_perform` returns `CURLE_SSL_CACERT` or `CURLE_SSL_PEER_CERTIFICATE` on macOS despite `VERIFYPEER=0` — indicates linking against wrong curl build

**Phase to address:** Phase 6 (build system) and Phase 7 (transport validation)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copy `beacon.c` from Linux tree without fixing var4/var5/var6 type mismatch | Less diff between trees | macOS check-in may fail against some Team Server versions; Clang warnings become errors with `-Werror` | Never — fix it when porting |
| Hardcode `/opt/homebrew` paths in macOS Makefile | Builds immediately on developer machine | Breaks on Intel Macs, CI runners, non-standard Homebrew prefixes | Only as a documented temporary fallback; use `brew --prefix` |
| Skip ad-hoc codesign step in Makefile | Faster iteration | Binary silently fails to execute on Sequoia 15.1+; operators cannot deploy | Never on macOS |
| Use `select()` in pivot.c instead of `kqueue()` | No platform-specific code needed | Hard `FD_SETSIZE=1024` socket limit; no macOS-native event notification | Acceptable for v2.0 purple-team scope; document the limit |
| Rely on automatic ad-hoc signing from linker instead of explicit `codesign` step | No extra Makefile target | Post-link modifications (stripped symbols, UPX, etc.) invalidate the signature with no warning | Never if any post-link transforms are applied |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Team Server metadata | Copying Linux metadata code produces `"linuxbeacon"` procname; Darwin kernel version (`24.x`) in OS major field | Replace `/proc/self/status` with `getprogname()`; replace `uname().release` parse with `sysctlbyname("kern.osproductversion")` |
| OpenSSL headers | Using system OpenSSL headers (`/usr/include/openssl/`) which are absent or Secure Transport shims on macOS | Explicitly include Homebrew OpenSSL headers via `brew --prefix openssl@3` |
| Build pipeline key injection | Adapting Linux in-place source mutation for macOS | Inject via generated header at compile time; post-link binary patching breaks the linker's automatic ad-hoc signature |
| macOS quarantine | Deploying beacon via `scp` or `curl` adds `com.apple.quarantine` xattr | Run `xattr -d com.apple.quarantine ./beacon-macos` on target before execution, or build + deploy in a workflow that does not trigger quarantine attribution |
| Cobalt Strike Aggressor build path | Running macOS payload generation on Linux host with `macOS_cwd` detection | The `CustomBeacon.cna` Windows-path guard documented in CONCERNS.md — add analogous macOS host detection for the macOS generation workflow |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `select()` with >1024 pivot sockets | Silent socket management failure; fd numbers above 1024 are not tracked | Use `kqueue()` for macOS in a future milestone | At ~900 simultaneous pivot sockets (leaving buffer) |
| `usleep()` in `command_send_socks` EAGAIN spin loop | CPU spike during high-throughput SOCKS sessions | Replace with `kqueue()` writable event | Under sustained SOCKS writes; not relevant for purple-team v2.0 |
| Single-threaded main loop | Beacon unresponsive during long `popen`/`shell` execution | This is a Linux-inherited design choice; carry it forward into macOS tree with same limitation | Any shell command exceeding the sleep interval |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Deploying macOS beacon without ad-hoc signature | Binary fails to run on Sequoia 15.1+; if run on older macOS, no integrity protection | Always sign with `codesign --force --sign -` as a Makefile step |
| Using `com.apple.quarantine`-tagged binary in purple-team exercise | Gatekeeper blocks execution before the beacon runs; reveals binary to macOS security logging | Strip quarantine xattr in deployment procedure or use in-memory execution method |
| Linking against system libcurl (Secure Transport) instead of Homebrew libcurl (OpenSSL) | TLS behavior may differ subtly; `CURLOPT_CAINFO` silently ignored; unexpected cert validation | Use `brew --prefix curl` in Makefile; verify TLS backend with `curl-config --version` |
| Leaving debug symbols in release macOS binary | Binary string analysis trivially reveals C2 server, URIs, and user-agent in plaintext | Add `-s` strip flag or `strip` post-link step; pair with `codesign --force --sign -` after strip |

---

## "Looks Done But Isn't" Checklist

- [ ] **macOS Check-in:** Compiles and links on macOS — verify actual check-in reaches Team Server and appears in beacon list with correct hostname/user/OS
- [ ] **Process name:** Operator console shows actual binary name, not `"linuxbeacon"` — test by checking Team Server beacon metadata
- [ ] **OS version:** Team Server shows macOS version (e.g., `15.3`), not Darwin kernel version (e.g., `24.3`) — verify with metadata decode tool
- [ ] **Ad-hoc signing:** `codesign -vv ./beacon-macos` shows valid ad-hoc signature — verify after every clean build
- [ ] **Quarantine strip:** Beacon runs on a fresh macOS test host without Gatekeeper dialog — test by transferring binary via `scp` then attempting execution without any xattr modification first (expected to fail on Sequoia); then test with `xattr -d com.apple.quarantine`
- [ ] **Library linking:** `otool -L ./beacon-macos` shows Homebrew paths (`/opt/homebrew/`) for libssl, libcrypto, libcurl — not system paths
- [ ] **var4/var5/var6 fix confirmed:** Clang build produces zero `-Wimplicit-int-conversion` warnings for these fields

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| `/proc/self/status` procname on macOS | LOW | Add `getprogname()` call in `implant-macos/` beacon metadata generation; recompile and re-sign |
| Broken ad-hoc signature | LOW | `codesign --force --sign - ./beacon-macos` restores signature; no rebuild required |
| Wrong OpenSSL library at link | MEDIUM | Identify via `otool -L`; update Makefile to use `brew --prefix openssl@3`; clean rebuild |
| var4/var5/var6 type mismatch causing check-in failure | MEDIUM | Fix declaration to `uint32_t` in macOS tree; verify with metadata decode tool; recompile and re-sign |
| Darwin kernel version in OS metadata | LOW | Replace `uname().release` parse with `sysctlbyname("kern.osproductversion")` in macOS tree |
| Quarantine blocking execution on target | LOW | `xattr -d com.apple.quarantine ./beacon-macos` on target host before execution |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| `/proc/self/status` procname | Phase 6 (tree scaffold) | `codesign -vv` + Team Server metadata shows real process name |
| var4/var5/var6 uint16_t type mismatch | Phase 7 (check-in) | Zero Clang `-Wimplicit-int-conversion` warnings; successful check-in |
| OS version = Darwin kernel version | Phase 7 (check-in) | Team Server shows `15.x` not `24.x`; `cs-decrypt-metadata.py` output |
| Ad-hoc signing not in Makefile | Phase 6 (build system) | `codesign -vv ./beacon-macos` passes; binary runs on fresh Sequoia host |
| Homebrew library path mismatch | Phase 6 (build system) | Clean compile on ARM64 Mac; `otool -L` shows `/opt/homebrew/` paths |
| Quarantine xattr deployment block | Phase 9 (handoff/packaging) | Binary transferred via `scp` + xattr removed runs without dialog |
| Libcurl system vs Homebrew TLS backend | Phase 6 (build) + Phase 7 (transport) | `curl-config --version` confirms OpenSSL backend; HTTPS check-in succeeds |
| select() not epoll() in pivot.c | Phase 8 (SOCKS) | No `epoll` symbols in macOS tree; `select()` compiles cleanly |
| AF_LINK vs AF_PACKET MAC collection | Phase 8 (command parity) | MAC address collection (if implemented) uses `struct sockaddr_dl`, not `sockaddr_ll` |
| Source mutation pipeline post-link binary patching | Phase 6 (build pipeline) | Makefile injects config via generated header; no post-link byte patching step |

---

## Sources

- Apple Developer: [Addressing Architectural Differences in macOS Code](https://developer.apple.com/documentation/apple-silicon/addressing-architectural-differences-in-your-macos-code)
- Hackaday: [Apple Forces Signing in macOS Sequoia 15.1](https://hackaday.com/2024/11/01/apple-forces-the-signing-of-applications-in-macos-sequoia-15-1/)
- MacRumors: [macOS 15.1 Removes Unsigned Application Launch](https://forums.macrumors.com/threads/macos-15-1-completely-removes-ability-to-launch-unsigned-applications.2441792/)
- Homebrew curl formula: [brew formulae curl](https://formulae.brew.sh/formula/curl)
- GitHub actions runner images: [brew openssl install on macOS 14 Arm64 borked](https://github.com/actions/runner-images/issues/9755)
- Apple Developer Forums: [Intel vs ARM memory alignment](https://developer.apple.com/forums/thread/651200)
- curl official: [SSL CA Certificates](https://curl.se/docs/sslcerts.html)
- macOS getifaddrs man page: [getifaddrs(3) osx](https://www.unix.com/man-page/osx/3/getifaddrs/)
- SpecterOps: [Dylib Injection on macOS ARM64](https://specterops.io/blog/2025/08/21/armed-and-dangerous-dylib-injection-on-macos/)
- Palo Alto Unit 42: [Cobalt Strike Metadata Encryption/Decryption](https://unit42.paloaltonetworks.com/cobalt-strike-metadata-encryption-decryption/)
- Project codebase: `implant/src/beacon.c` (lines 40-81 getifaddrs, 192-265 OS metadata, 216-226 var4-6 bug)
- Project codebase: `implant/src/pivot.c` (select-based SOCKS, no epoll)
- Project codebase: `.planning/codebase/CONCERNS.md` (var4/var5/var6 known bug, source mutation risk)

---

*Pitfalls research for: macOS ARM64 C implant port (adding implant-macos/ to CobaltStrike-Linux-Beacon)*
*Researched: 2026-02-26*
