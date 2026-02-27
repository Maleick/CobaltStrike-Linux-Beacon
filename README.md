# Cobalt Strike Beacons

Custom Cobalt Strike Beacons written in C for multiple platforms, communicating with the Cobalt Strike teamserver over HTTP/S.

The goal is to demonstrate that custom implants can be built for any platform — not just Linux. The only hard requirement is speaking the Cobalt Strike wire protocol correctly. With custom Beacons you can define custom behavior, add new features, support different platforms and file formats, apply compile-time obfuscation, and more.

## Platforms

| Platform | Arch | Status |
|----------|------|--------|
| Linux    | x86_64 | ✅ v1.0 — available |
| macOS    | ARM64 (M1–M4) | 🚧 v2.0 — in development |

## Features (Linux v1.0)
- HTTP/S listener support (default C2 profile)
- Built-in commands: `sleep`, `cd`, `pwd`, `shell`, `ls`, `exit`, `upload`, `download`
- Linux BOF execution via TrustedSec's ELFLoader (TrustedSec & Outflank BOF format)
- HTTP/S profile abstraction — runtime-selectable C2 profiles
- SOCKS proxy

## Features (macOS v2.0 — in progress)
- ARM64 native Mach-O binary (Apple Clang, Homebrew OpenSSL@3 + libcurl)
- Same HTTP/S C2 protocol as Linux v1.0
- Ad-hoc codesigned for local execution
- BOF support via macOS-native loader (planned)

## Demo
Generating payloads with the Aggressor Script
![Linux Beacon Payload Generation](demo/generate_payloads.gif)

Running commands & BOFs in the Linux Beacon
![Linux Beacon Commands Demo](demo/commands.gif)

## Setup
See [SETUP.md](SETUP.md) for build and usage instructions.

## Roadmap

### v1.0 — Linux Stream
- [x] Phase 1: Baseline validation harness
- [x] Phase 2: HTTP/S profile abstraction
- [ ] Phase 3: Reverse TCP transport
- [ ] Phase 4: Security and build hygiene
- [ ] Phase 5: CI and release readiness

### v2.0 — macOS ARM64 Stream
- [ ] Phase 6: macOS tree scaffold and build system ← *active*
- [ ] Phase 7: Generation pipeline and live check-in validation
- [ ] Phase 8: POSIX command parity and SOCKS pivot
- [ ] Phase 9: Test harness and operator handoff

## Special Thanks
Thank you to [Kyle Avery](https://x.com/kyleavery) for help with BOF execution integration and implant testing.

## Resources
- [TrustedSec ELFLoader & BOFs](https://github.com/trustedsec/ELFLoader)
- [Outflank NIX BOF Template](https://github.com/outflanknl/nix_bof_template)
- [PaloAlto Unit42 — CS Metadata Encryption](https://unit42.paloaltonetworks.com/cobalt-strike-metadata-encryption-decryption/)
- [SANS ISC Diary 27968](https://isc.sans.edu/diary/27968)
- [cs-decrypt-metadata-py — Didier Stevens](https://blog.didierstevens.com/2021/10/22/new-tool-cs-decrypt-metadata-py/)
- [SentinelOne CobaltStrikeParser](https://github.com/Sentinel-One/CobaltStrikeParser)
