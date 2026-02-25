# Requirements: Cobalt Strike Linux Beacon

**Defined:** 2026-02-25
**Core Value:** Operators can deploy a Linux beacon that remains Cobalt Strike-compatible while being safely extensible for new transports and profile behaviors.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### C2 Profile Compatibility

- [ ] **C2P-01**: Operator can define HTTP/S profile values (URIs, headers, user-agent) without manually editing tracked source files.
- [ ] **C2P-02**: Beacon metadata/task packet behavior remains valid when profile values are customized.
- [ ] **C2P-03**: Payload generation flow can select a profile configuration per build target.

### Transport Modes

- [ ] **NET-01**: Beacon supports reverse TCP transport mode in addition to existing HTTP/S mode.
- [ ] **NET-02**: Operator can select transport mode (`http`, `https`, `tcp`) during payload generation.
- [ ] **NET-03**: Beacon performs bounded reconnect/backoff in TCP mode without process termination.

### Reliability and Validation

- [ ] **REL-01**: Automated tests validate metadata/packet encoding and decoding against known-good fixtures.
- [ ] **REL-02**: Automated tests cover malformed task payload handling and verify no crash conditions.
- [ ] **REL-03**: CI pipeline builds the implant and runs regression tests on Linux for each change.

### Security and Build Hygiene

- [ ] **SEC-01**: HTTPS transport verifies certificates by default with explicit opt-out configuration.
- [ ] **SEC-02**: Key/listener build-time injection no longer mutates tracked C source files in-place.
- [ ] **SEC-03**: Payload generation cleans temporary key/config artifacts after build completion.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Performance and Ecosystem

- **PERF-01**: Pivot subsystem supports higher socket concurrency with event-backend optimization.
- **COMP-01**: Broader compatibility matrix across additional Cobalt Strike profile permutations.
- **OBS-01**: Structured runtime telemetry for debugging and operator diagnostics.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Cross-platform (Windows/macOS) implant support | Increases scope beyond Linux-beacon milestone priorities |
| Full profile DSL parity for every C2 profile directive | Too broad for current milestone; high risk without staged rollout |
| New operator GUI/management plane | Not required to deliver core implant capability improvements |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| REL-01 | Phase 1 | Pending |
| REL-02 | Phase 1 | Pending |
| C2P-01 | Phase 2 | Pending |
| C2P-02 | Phase 2 | Pending |
| C2P-03 | Phase 2 | Pending |
| NET-01 | Phase 3 | Pending |
| NET-02 | Phase 3 | Pending |
| NET-03 | Phase 3 | Pending |
| SEC-01 | Phase 4 | Pending |
| SEC-02 | Phase 4 | Pending |
| SEC-03 | Phase 4 | Pending |
| REL-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 after roadmap creation*
