# Codebase Structure

**Analysis Date:** 2026-02-25

## Directory Layout

```
CobaltStrike-Linux-Beacon/
├── CustomBeacon.cna                # Main Aggressor script for payload generation/build orchestration
├── README.md                       # Project overview, feature list, demo links
├── SETUP.md                        # Setup/build/operator instructions
├── demo/                           # GIF demonstrations
│   ├── commands.gif
│   └── generate_payloads.gif
├── generate-payload/               # Build-time key/listener mutation utilities
│   ├── Dump.java
│   ├── InsertListenerInfo.py
│   ├── InsertPublicKey.py
│   └── RemovePublicKey.py
├── implant/                        # Native beacon implementation
│   ├── Makefile
│   ├── headers/                    # Public/internal module headers
│   ├── src/                        # Implant runtime source
│   └── elfloader/                  # Vendored ELFLoader integration
└── sample_linux_bofs/              # Sample BOFs + Aggressor tasking script
    ├── build.sh
    ├── execute_linux_bof.cna
    ├── id.c
    └── cat.c
```

## Directory Purposes

**`generate-payload/`:**
- Purpose: prepare source tree for a specific Team Server/public key/listener.
- Contains: Python scripts that rewrite tracked C source/header files and one Java key dump helper.
- Key files: `InsertListenerInfo.py`, `InsertPublicKey.py`, `RemovePublicKey.py`, `Dump.java`.
- Subdirectories: None.

**`implant/`:**
- Purpose: compile and package the Linux beacon executable.
- Contains: C sources (`src/`), module headers (`headers/`), Makefile, and vendored ELFLoader.
- Key files: `Makefile`, `src/main.c`, `src/beacon.c`, `src/commands.c`, `headers/config.h`.
- Subdirectories: `src/`, `headers/`, `elfloader/elfloader-src`, `elfloader/elfloader-headers`.

**`sample_linux_bofs/`:**
- Purpose: demonstration BOF payloads and tasking aliases.
- Contains: BOF C sources, compiled-object build script, Aggressor integration script.
- Key files: `execute_linux_bof.cna`, `build.sh`, `id.c`, `cat.c`.
- Subdirectories: None.

**`demo/`:**
- Purpose: visual demo artifacts for documentation.
- Contains: animated GIF captures.
- Key files: `commands.gif`, `generate_payloads.gif`.
- Subdirectories: None.

## Key File Locations

**Entry Points:**
- `implant/src/main.c`: implant process entry and primary beacon loop.
- `CustomBeacon.cna`: Cobalt Strike menu/dialog entry for payload generation.
- `sample_linux_bofs/execute_linux_bof.cna`: alias entrypoints for Linux BOF tasking.

**Configuration:**
- `implant/headers/config.h`: compile-time C2 host/port/protocol/user-agent/URIs.
- `implant/Makefile`: compilation and link flags.
- `SETUP.md`: operator setup dependencies and generation sequence.

**Core Logic:**
- `implant/src/beacon.c`: metadata generation, check-in, packet encode/decode.
- `implant/src/commands.c`: task parser/dispatcher and command implementations.
- `implant/src/http.c`: HTTP GET/POST transport implementation.
- `implant/src/pivot.c`: SOCKS/pivot socket lifecycle handling.
- `implant/src/files.c`: download and transfer callback handling.

**Testing:**
- Automated test directories/files: Not detected.
- Manual BOF validation assets: `sample_linux_bofs/`.

**Documentation:**
- `README.md`: features and references.
- `SETUP.md`: end-to-end build/usage instructions.

## Naming Conventions

**Files:**
- C modules use lowercase snake_case names (for example `beacon.c`, `commands.c`, `pivot.c`).
- Headers mirror module names (`beacon.h`, `commands.h`, `pivot.h`).
- Aggressor scripts use `.cna` extension (`CustomBeacon.cna`, `execute_linux_bof.cna`).

**Directories:**
- Feature/function directories use lowercase with hyphen or underscore (`generate-payload`, `sample_linux_bofs`).
- Runtime source grouping under `implant/src` and `implant/headers`.

**Special Patterns:**
- Make output directories (`implant/bin`, `implant/obj`) are generated and ignored via global ignore rules.
- BOF compiled artifacts use `*.x64.o` naming and are ignored (`.gitignore`).

## Where to Add New Code

**New Feature:**
- Primary code: `implant/src/` (new module + wiring in `commands.c`/`main.c` as needed).
- Tests: create new test tree (recommended `implant/tests/`) since none exists.
- Config if needed: `implant/headers/config.h` for compile-time constants.

**New Component/Module:**
- Implementation: `implant/src/<feature>.c`.
- Types/interfaces: `implant/headers/<feature>.h`.
- Tests: `implant/tests/<feature>_test.*` (new convention to introduce).

**New Route/Command:**
- Definition: add command/callback IDs in `implant/headers/commands.h`.
- Handler: implement in `implant/src/commands.c` (or dedicated module called by it).
- Tests: add protocol/task parser regression tests in future `implant/tests/`.

**Utilities:**
- Shared helpers: `implant/src/` + matching `implant/headers/`.
- Script/tooling utilities: `generate-payload/` or root-level scripts depending on runtime vs build-time usage.

## Special Directories

**`implant/elfloader/`:**
- Purpose: vendored third-party Linux BOF loader runtime.
- Source: Imported external code (TrustedSec ELFLoader lineage).
- Committed: Yes.

**`implant/bin/` and `implant/obj/`:**
- Purpose: compiled binary and object artifacts.
- Source: generated by `implant/Makefile`.
- Committed: No (ignored by `**/[Bb]in/*` and object ignore rules).

**`.planning/`:**
- Purpose: GSD planning metadata and codebase mapping documents.
- Source: generated by planning workflows.
- Committed: Yes in this repository policy (`commit_docs=true`, `.planning` not ignored).

