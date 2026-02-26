# Technology Stack: macOS ARM64 Beacon (`implant-macos/`)

**Project:** CobaltStrike-Linux-Beacon — v2.0 macOS ARM64 milestone
**Researched:** 2026-02-26
**Scope:** Stack additions and changes needed for the new `implant-macos/` tree. The existing
Linux `implant/` tree (GCC, GNU Make, OpenSSL, libcurl) is unchanged.

---

## Recommended Stack

### Compiler

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Apple Clang (Xcode CLT) | 17.0.0 (clang-1700.6.3.2) | C compiler for ARM64 target | Only supported native compiler for ARM64 macOS; GCC on macOS is a symlink alias to clang; no separate install needed |

**Use `CC = clang` in the macOS Makefile.** Do NOT use `CC = gcc` even though `gcc` resolves to
Clang on macOS — using the explicit name avoids ambiguity and makes it clear this is a
Clang-specific build. The `-arch arm64` flag is the only required addition over the Linux GCC
flags; all existing flags (`-Wall -Wextra -O2`) are accepted by Clang without change.

Verified on this build host: Apple clang 17.0.0, target `arm64-apple-darwin25.4.0`.

### Crypto Library

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| OpenSSL 3 (Homebrew `openssl@3`) | 3.6.1 | RSA, AES-128-CBC, HMAC-SHA256, RAND, base64 via BIO | macOS ships Apple LibreSSL 3.3.6 via `/usr/bin/openssl`, but Apple does NOT expose LibreSSL headers for third-party linking on macOS 11+; Homebrew OpenSSL@3 is the only linkable option |

**Why not Apple LibreSSL:** Since macOS Big Sur, Apple does not ship `.tbd` stubs for its
LibreSSL, making it impossible to link against. The existing `crypto.c` uses
`EVP_PKEY_CTX`, `EVP_CIPHER_CTX`, `HMAC()`, `SHA256()`, `RAND_bytes()`, and OpenSSL BIO
functions — all standard OpenSSL 3 API. These work identically on macOS with Homebrew
OpenSSL@3.

**Install path on ARM64 macOS:** `/opt/homebrew/opt/openssl@3` (symlink to
`/opt/homebrew/Cellar/openssl@3/3.6.1`). Intel Macs use `/usr/local/opt/openssl@3`. Use
`$(shell brew --prefix openssl@3)` in the Makefile to resolve the path at build time,
making the Makefile host-agnostic.

**Verification:** Compiled and linked against OpenSSL 3.6.1 on this host without issues.
The dylib's install_name is an absolute Cellar path, so no `-Wl,-rpath` is required at
runtime — the dynamic linker resolves it directly.

### HTTP Transport Library

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| libcurl (Homebrew `curl`) | 8.18.0 | HTTP GET/POST to C2, SSL transport | Exact same libcurl API as Linux; existing `http.c` uses only `CURLOPT_*` options that are platform-neutral; Homebrew curl links against Homebrew OpenSSL@3 (not Apple SecureTransport), ensuring consistent TLS behavior |

**Why not system libcurl:** macOS system curl (`/usr/bin/curl`) uses Apple SecureTransport,
not OpenSSL, as its TLS backend (confirmed: `curl 8.7.1 (SecureTransport) LibreSSL/3.3.6`).
This means system libcurl headers are not accessible for `-lcurl` linking. Homebrew curl is
`keg-only` and must be linked explicitly. Homebrew curl 8.18.0 links against Homebrew
OpenSSL@3, providing TLS 1.3, HTTP/2, and consistent cipher behavior with the existing
Linux implementation.

**Install path on ARM64 macOS:** `/opt/homebrew/opt/curl`. Use
`$(shell brew --prefix curl)` in the Makefile.

**Verification:** Compiled and linked `libcurl/8.18.0 OpenSSL/3.6.1` on this host; binary
runs without `-Wl,-rpath` because Homebrew embeds absolute paths in its dylib install names.

### Build System

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| GNU Make (Xcode CLT) | 3.81 | Build orchestration | Ships with macOS Xcode Command Line Tools; all existing Makefile patterns (`$(lastword ...)`, `$(abspath ...)`, `$(patsubst ...)`, `$(wildcard ...)`) are compatible with GNU Make 3.81; no additional install needed |

**Note on GNU Make 3.81 vs 4.x:** The macOS system `make` is GNU Make 3.81 (not BSD make).
All features used in the existing Linux `implant/Makefile` are available in 3.81. Homebrew
offers `make` 4.4.1 (`gmake`) but it is not installed on this host and is not required
— the existing patterns are 3.81-compatible.

---

## Compiler Flags: Linux GCC vs macOS Clang

### What stays the same

```makefile
CFLAGS = -Wall -Wextra -O2 -I./headers -I./generated
LDFLAGS = -lssl -lcrypto -lcurl
```

All of these flags are accepted by Apple Clang identically to Linux GCC. Verified on
ARM64 macOS with no warnings or errors for this flag set.

### What must be added

```makefile
# macOS Makefile (implant-macos/Makefile)
CC = clang

BREW_OPENSSL := $(shell brew --prefix openssl@3 2>/dev/null)
BREW_CURL    := $(shell brew --prefix curl 2>/dev/null)

CFLAGS = -Wall -Wextra -O2 \
         -arch arm64 \
         -I./headers \
         -I./generated \
         -I$(BREW_OPENSSL)/include \
         -I$(BREW_CURL)/include

LDFLAGS = -L$(BREW_OPENSSL)/lib \
          -L$(BREW_CURL)/lib \
          -lssl -lcrypto -lcurl
```

Key differences from Linux:

| Flag | Linux GCC | macOS Clang | Reason |
|------|-----------|-------------|--------|
| `CC` | `gcc` | `clang` | Explicit compiler name |
| `-arch arm64` | not needed | required | Disambiguates ARM64 vs Rosetta on operator host; also signals to linker |
| `-I$(BREW_OPENSSL)/include` | not needed (headers in system path) | required | OpenSSL headers only in Homebrew, not system SDK |
| `-I$(BREW_CURL)/include` | not needed | required | libcurl headers only in Homebrew curl (keg-only) |
| `-L$(BREW_OPENSSL)/lib` | not needed | required | Link against Homebrew's OpenSSL, not system LibreSSL |
| `-L$(BREW_CURL)/lib` | not needed | required | Link against Homebrew's libcurl, not system curl |
| `-I./elfloader/elfloader-headers` | needed | NOT needed | ELFLoader is Linux-only; macOS BOF execution is out of scope |
| `$(wildcard elfloader/...)` sources | included | NOT included | No ELFLoader in macOS build |

### What is NOT needed

- `-Wl,-rpath,...` — Homebrew dylibs embed absolute install paths in their `install_name`
  fields (confirmed via `otool -L`). The dynamic linker resolves `/opt/homebrew/opt/*/lib/*.dylib`
  directly without rpath hints.
- `codesign -s -` as an explicit build step — Apple ld automatically applies ad-hoc
  signing to all ARM64 Mach-O binaries at link time. Confirmed: built binaries show
  `flags=0x20002(adhoc,linker-signed)` in `codesign -dv` output. No post-build signing
  step needed for purple-team deployment.
- `-mmacosx-version-min=X.Y` — Unless targeting very old macOS, the SDK default
  (currently macOS 26 on this host) is appropriate. For maximum compatibility set
  `-mmacosx-version-min=12.0` (ARM64 was introduced in macOS 11.0; 12.0 is a safe
  baseline for all M1–M4 targets).

---

## POSIX/Network Headers: Availability on macOS ARM64

All headers used in the existing Linux source files are present in the macOS SDK. No
substitutions are required at the header-include level.

| Header | Linux | macOS ARM64 | Notes |
|--------|-------|-------------|-------|
| `<unistd.h>` | YES | YES | `usleep`, `getpid`, `geteuid`, `getcwd`, `chdir` all present |
| `<signal.h>` | YES | YES | `SIGINT`, `SIGTERM` identical |
| `<sys/utsname.h>` | YES | YES | `uname()`, `struct utsname` present; see behavioral difference below |
| `<arpa/inet.h>` | YES | YES | `htonl`, `htons`, `ntohl`, `ntohs`, `AF_INET` identical |
| `<sys/socket.h>` | YES | YES | `socket`, `bind`, `listen`, `accept`, `connect`, `setsockopt` identical |
| `<sys/ioctl.h>` | YES | YES | `SIOCGIFCONF`, `IFNAMSIZ` present |
| `<net/if.h>` | YES | YES | `struct ifreq` present; must include before `<ifaddrs.h>` |
| `<ifaddrs.h>` | YES | YES | `getifaddrs`, `freeifaddrs` present and API-identical |
| `<netdb.h>` | YES | YES | `gethostbyname`, `struct hostent` present (deprecated but present) |
| `<fcntl.h>` | YES | YES | `fcntl`, `F_GETFL`, `F_SETFL`, `O_NONBLOCK` identical |
| `<dirent.h>` | YES | YES | `opendir`, `readdir`, `closedir`, `struct dirent` identical |
| `<sys/stat.h>` | YES | YES | `stat`, `struct stat` identical |
| `<pwd.h>` | YES | YES | `getpwuid`, `struct passwd` identical |
| `<grp.h>` | YES | YES | `struct group` identical |
| `<time.h>` | YES | YES | `clock_gettime(CLOCK_MONOTONIC,...)` present on macOS 10.12+ |
| `<limits.h>` | YES | YES | `PATH_MAX` present |
| `<openssl/sha.h>` | YES | YES (Homebrew) | Requires Homebrew include path |
| `<openssl/hmac.h>` | YES | YES (Homebrew) | Requires Homebrew include path |
| `<curl/curl.h>` | YES | YES (Homebrew) | Requires Homebrew curl include path |

### Headers that are Linux-only (NOT available on macOS)

These headers are referenced in the Linux source and must NOT be included in
`implant-macos/` source files:

| Linux Header | Usage in Linux Source | macOS Alternative |
|--------------|----------------------|-------------------|
| `<linux/ioctl.h>` | Not directly used in this codebase (uses `<sys/ioctl.h>`) | `<sys/ioctl.h>` (already used) |
| `/proc/self/status` (filesystem) | `beacon.c`: process name via `fopen("/proc/self/status", "r")` | `getprogname()` from `<stdlib.h>`, or `proc_name(getpid(), ...)` from `<libproc.h>` |

---

## Behavioral Differences Requiring Source Changes in `implant-macos/`

These are not compiler or linker issues — they are places where the Linux source uses
Linux-specific behavior that compiles but produces wrong output on macOS:

### 1. `/proc/self/status` (CRITICAL — macOS has no `/proc`)

**Location:** `implant/src/beacon.c`, `beacon_generate_metadata()`, lines ~244–258

**Linux code:**
```c
FILE* fileptr = fopen("/proc/self/status", "r");
if (fileptr == NULL) {
    snprintf(procname, sizeof(procname), "linuxbeacon");
} else {
    char tmp[40];
    if (fgets(tmp, sizeof(tmp), fileptr))
        sscanf(tmp, "Name:%31s", procname);
    fclose(fileptr);
}
```

**macOS replacement:**
```c
// getprogname() is available in <stdlib.h> on macOS 10.5+
const char *gp = getprogname();
if (gp) {
    snprintf(procname, sizeof(procname), "%s", gp);
} else {
    snprintf(procname, sizeof(procname), "macosbeacon");
}
```

`getprogname()` is declared in `<stdlib.h>` (already included everywhere) and returns
`argv[0]`'s basename — the same information `/proc/self/status` Name field provides on
Linux. Confirmed present in macOS SDK.

### 2. `utsname.release` format differs (MODERATE)

**Location:** `implant/src/beacon.c`, `beacon_generate_metadata()`, lines ~205–211

**Linux behavior:** `uts.release` is a kernel version string like `"5.15.0"`, so
`sscanf(uts.release, "%d.%d.%d", &major, &minor, &build)` parses OS major/minor (5.15).

**macOS behavior:** `uts.sysname` is `"Darwin"` and `uts.release` is a Darwin kernel
version like `"25.4.0"` — NOT a macOS version number. Darwin 25 = macOS 26; Darwin 24 =
macOS 15; Darwin 23 = macOS 14. The existing `sscanf` pattern still compiles and runs
without error, but produces Darwin kernel numbers instead of macOS version numbers.

Confirmed on this host: `uname()` returns `sysname="Darwin"`, `release="25.4.0"`,
`machine="arm64"`.

The `nodename` field from `utsname` works correctly on both platforms (returns hostname).

**Implication for macOS build:** The metadata sent to the teamserver will report Darwin
kernel version numbers in the OS version fields. For a purple-team implant this is
acceptable — the teamserver still receives valid integers and the beacon is identifiable.
If correct macOS version numbers are required, use `sysctl("kern.osproductversion")` as a
replacement in `implant-macos/`.

### 3. `geteuid()` and `getenv("USER")` (NO CHANGE NEEDED)

Both `geteuid()` (for admin flag) and `getenv("USER")` (for username) work identically on
macOS. No changes needed.

### 4. ELFLoader / BOF execution (NO macOS EQUIVALENT IN SCOPE)

**Location:** `implant/src/commands.c`, command ID 200

`commands.c` includes `<ELFRunner_include.h>` and calls `ELFRunner("go", ...)`. This is
Linux ELF-only. macOS BOF execution is explicitly out of scope for v2.0. The
`implant-macos/` build must exclude ELFLoader sources entirely and must not include the
BOF command case (command ID 200). The macOS `commands.c` should return "unsupported" or
omit the case entirely.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Crypto | Homebrew OpenSSL@3 | Apple LibreSSL | Apple does not expose LibreSSL headers for linking since macOS 11; impossible to link |
| Crypto | Homebrew OpenSSL@3 | MacPorts OpenSSL | Homebrew is already present on this operator host; MacPorts would require separate install |
| HTTP | Homebrew libcurl | System libcurl | System libcurl uses SecureTransport TLS (not OpenSSL), headers not exposed for `-lcurl`; version mismatch (8.7.1 vs 8.18.0) |
| Compiler | Apple Clang (Xcode CLT) | Homebrew LLVM | No benefit over system Clang for this use case; system Clang is already version 17 |
| Compiler | Apple Clang | GCC via Homebrew | GCC cross-compiles to ARM64 but is non-standard on macOS; no toolchain advantage; arm64 ABI differences in assembly-level code would matter |
| Build | GNU Make 3.81 (Xcode CLT) | Homebrew make 4.4.1 | No features of GNU Make 4.x are used; 3.81 handles all existing patterns; one less dependency |
| Signing | Automatic (linker-signed) | `codesign -s -` post-step | Apple ld on ARM64 automatically applies ad-hoc signature; no manual step needed |

---

## Installation

### Prerequisites (operator macOS ARM64 host)

```bash
# Install Xcode Command Line Tools (provides clang, GNU make, SDK headers)
xcode-select --install

# Install Homebrew (ARM64 path: /opt/homebrew)
# https://brew.sh

# Install required libraries
brew install openssl@3 curl

# Verify paths
brew --prefix openssl@3   # should return /opt/homebrew/opt/openssl@3
brew --prefix curl        # should return /opt/homebrew/opt/curl
```

### macOS Makefile skeleton (implant-macos/Makefile)

```makefile
OUTPUT ?= beacon-macos

CC = clang

BREW_OPENSSL := $(shell brew --prefix openssl@3 2>/dev/null)
BREW_CURL    := $(shell brew --prefix curl 2>/dev/null)

CFLAGS = -Wall -Wextra -O2 \
         -arch arm64 \
         -I./headers \
         -I./generated \
         -I$(BREW_OPENSSL)/include \
         -I$(BREW_CURL)/include

LDFLAGS = -L$(BREW_OPENSSL)/lib \
          -L$(BREW_CURL)/lib \
          -lssl -lcrypto -lcurl

# Note: no ELFLoader sources in macOS build
SOURCES = $(wildcard src/*.c)
# ... remainder mirrors Linux Makefile structure
```

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Compiler (Clang, flags) | HIGH | Verified by compiling on this ARM64 macOS host; `clang --version`, flags tested |
| OpenSSL@3 (Homebrew) | HIGH | `brew info openssl@3` confirms 3.6.1 installed; compiled and ran OpenSSL test binary |
| libcurl (Homebrew) | HIGH | `brew info curl` confirms 8.18.0 installed; compiled and ran curl test binary |
| POSIX header availability | HIGH | Verified all headers against macOS SDK via `ls "$SDK/usr/include/"`; compiled POSIX header test |
| GNU Make 3.81 compatibility | HIGH | Verified `$(lastword ...)`, `$(abspath ...)` work in macOS system make |
| Ad-hoc signing | HIGH | `codesign -dv` confirms linker-signed flag; binary runs without explicit `codesign` call |
| `/proc/self/status` absence | HIGH | Confirmed `/proc` does not exist; `getprogname()` confirmed in SDK |
| `utsname.release` format | HIGH | Ran `uname()` on this host; Darwin 25.4.0 confirmed |

---

## Sources

- Homebrew openssl@3 formula: https://formulae.brew.sh/formula/openssl@3
- Homebrew curl formula: https://formulae.brew.sh/formula/curl
- Homebrew keg-only build docs: https://docs.brew.sh/How-to-Build-Software-Outside-Homebrew-with-Homebrew-keg-only-Dependencies
- Apple LibreSSL linking impossibility (Big Sur+): https://github.com/orgs/Homebrew/discussions/3258
- macOS ad-hoc code signing: https://stories.miln.eu/graham/2024-06-25-ad-hoc-code-signing-a-mac-app/
- Apple Silicon requires signed code: https://eclecticlight.co/2020/08/22/apple-silicon-macs-will-require-signed-code/
- macOS `getifaddrs` man page: https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/getifaddrs.3.html
- System `libproc.h` for `proc_name()`: macOS SDK at `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/libproc.h`
