# Phase 8 Context: POSIX Command Parity and SOCKS Pivot

Goal: All in-scope POSIX commands and SOCKS pivot work correctly on macOS — validated by execution-path testing.

## Decisions

- **Locked Decision**: Use a 2-plan breakdown.
  - Plan 1: File/directory commands (`cd`, `ls`, `upload`, `download`).
  - Plan 2: SOCKS pivot (`listen`, `connect`, `send`, `close`).
- **Locked Decision**: Focus on execution-path validation, not just static analysis.
- **Locked Decision**: Document any behavioral differences from Linux.
- **Locked Decision**: Confirm `select()` behavior and document `FD_SETSIZE` limit on macOS (typically 1024).
- **Locked Decision**: No Linux-specific API calls (`epoll`, `AF_PACKET`, `SIOCGIFHWADDR`) allowed in the macOS build.

## Deferred Ideas

- `kqueue`-based SOCKS pivot backend (deferred to v3+ / MAC-EXT-02).
- MAC address collection (deferred to v3+ / MAC-EXT-04).

## Claude's Discretion

- **Validation Method**: Since a live macOS runner is not available in the planning environment, the plans will provide the user with the necessary verification steps and automated scripts/commands they can run on their macOS build machine.
- **Scope**: While Phase 7 covers `shell`, `pwd`, and `sleep`, Phase 8 will re-verify them to ensure full parity and document any platform-specific nuances (e.g., APFS filesystem quirks or macOS-specific file attributes).
