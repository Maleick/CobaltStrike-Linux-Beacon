# Technology Stack

**Analysis Date:** 2026-02-25

## Languages

**Primary:**
- C (GCC toolchain) - Implant runtime and protocol implementation in `implant/src/*.c` with interfaces in `implant/headers/*.h`.

**Secondary:**
- Aggressor Script (CNA) - Cobalt Strike client-side orchestration in `CustomBeacon.cna` and `sample_linux_bofs/execute_linux_bof.cna`.
- Python 3 - Build-time source mutation scripts in `generate-payload/*.py`.
- Java - Team server public key extraction utility in `generate-payload/Dump.java`.
- POSIX shell - BOF sample build script in `sample_linux_bofs/build.sh`.

## Runtime

**Environment:**
- Linux userland runtime with glibc-compatible networking/system APIs used by `implant/src/*.c`.
- OpenSSL runtime libraries (`libssl`, `libcrypto`) and libcurl (`libcurl`) required by `implant/Makefile`.

**Package Manager:**
- System package manager (APT in setup docs) for dependency installation (`build-essential`, `libssl-dev`, `libcurl4-openssl-dev`).
- Lockfile: Not detected.

## Frameworks

**Core:**
- Cobalt Strike HTTP/S beacon protocol implementation - custom in `implant/src/beacon.c`, `implant/src/http.c`, and `implant/src/crypto.c`.
- TrustedSec ELFLoader (vendored) - Linux BOF execution support in `implant/elfloader/elfloader-src/*.c`.

**Testing:**
- Automated unit/integration test framework: Not detected.
- Manual operator validation flows documented in `README.md` and `SETUP.md`.

**Build/Dev:**
- GNU Make - implant build orchestration in `implant/Makefile`.
- GCC - native compilation for implant and BOF samples (`implant/Makefile`, `sample_linux_bofs/build.sh`).
- Python scripts - listener/public-key injection pipeline in `generate-payload/InsertListenerInfo.py` and `generate-payload/InsertPublicKey.py`.

## Key Dependencies

**Critical:**
- OpenSSL EVP/HMAC/SHA APIs - cryptography and metadata/session handling in `implant/src/crypto.c` and `implant/src/beacon.c`.
- libcurl - beacon HTTP(S) transport in `implant/src/http.c`.
- Cobalt Strike Aggressor runtime APIs - payload generation and tasking in `CustomBeacon.cna` and `sample_linux_bofs/execute_linux_bof.cna`.

**Infrastructure:**
- POSIX sockets/syscalls - network pivoting and file/task execution in `implant/src/pivot.c`, `implant/src/commands.c`, and `implant/src/files.c`.
- Vendored ELFLoader compatibility layer - BOF execution bridge in `implant/elfloader/elfloader-src/*.c`.

## Configuration

**Environment:**
- Team server connection is compile-time configured through macros in `implant/headers/config.h` (`C2_SERVER`, `C2_PORT`, `C2_USE_HTTPS`).
- Listener data is inserted by `generate-payload/InsertListenerInfo.py` by rewriting `implant/headers/config.h`.
- Team server public key is inserted into `implant/src/beacon.c` by `generate-payload/InsertPublicKey.py` and reverted by `generate-payload/RemovePublicKey.py`.

**Build:**
- Implant build config: `implant/Makefile`.
- Payload generation orchestration: `CustomBeacon.cna` + scripts under `generate-payload/`.
- Sample BOF compilation: `sample_linux_bofs/build.sh`.

## Platform Requirements

**Development:**
- Linux host for Cobalt Strike client + Aggressor `exec` build integration (`CustomBeacon.cna` checks Linux path semantics).
- Tooling from `SETUP.md`: `build-essential`, `libssl-dev`, `libcurl4-openssl-dev`, `python3`, Java runtime for `Dump.java`.

**Production:**
- Implant target is Linux x64 userland with network egress to Cobalt Strike Team Server HTTP/S listener.
- BOF execution path expects compatible ELF object payloads (TrustedSec/Outflank style).

---

*Stack analysis: 2026-02-25*
*Update after major dependency changes*
