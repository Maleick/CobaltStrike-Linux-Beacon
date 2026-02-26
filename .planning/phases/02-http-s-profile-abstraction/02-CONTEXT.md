# Phase 2: HTTP/S Profile Abstraction - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Externalize HTTP/S profile configuration from tracked source macros so operators can build profile-specific implants through the existing generation workflow while preserving default Cobalt Strike-compatible behavior. Scope is limited to requirement IDs C2P-01, C2P-02, and C2P-03; no new transport mode or non-HTTP protocol features are included.

</domain>

<decisions>
## Implementation Decisions

### Profile Configuration Artifact Shape
- Profile configuration is stored as **versioned JSON artifacts in-repo** (for example under `profiles/http/`).
- Each profile must include at least: `profile_id`, `schema_version`, `host`, `port`, `use_https`, `http_get_uri`, `http_post_uri`, `user_agent`, and `http_headers`.
- Validation is **strict and fail-fast**: missing required fields or invalid values abort generation with deterministic error output.
- A default profile artifact must mirror current baseline values so existing operator behavior remains stable.

### Generation-Time Selection Workflow
- Operator profile selection happens at generation time and defaults to the baseline profile when no override is supplied.
- Selection must be available through the existing Aggressor/Python generation path (no manual C source edits).
- Generation flow must validate the selected profile before build and produce deterministic diagnostics on invalid profile input.
- Selected profile values are rendered into build-consumed artifacts (generated files), not committed source rewrites.

### Runtime Fallback and Default Profile Behavior
- If no custom profile is selected, runtime behavior must match the current default HTTP/S profile semantics.
- If a selected profile artifact cannot be parsed/validated, generation fails before compilation (no silent fallback to partial values).
- Runtime transport behavior remains HTTP/S-only in this phase and must preserve existing metadata and task exchange semantics.
- Default profile remains the compatibility anchor for regression checks.

### Compatibility Expectations
- Compatibility policy remains **fail by default** unless fixture/profile updates are intentionally approved.
- Default profile must preserve semantic behavior already validated in Phase 1 (metadata/task contract).
- At least one non-default profile variant must pass check-in/task exchange compatibility validation.
- Phase output must eliminate the need for manual edits to `implant/src/*.c` and `implant/headers/*.h` for profile changes.

### Claude's Discretion
- Exact profile file naming conventions and directory organization beneath `profiles/http/`.
- Exact UX wording/layout for profile selection prompt in Aggressor workflow.
- Choice of script-level validation approach (custom Python checks vs schema helper), as long as output remains deterministic.
- Exact generated artifact path/naming used by Make/build integration.

</decisions>

<specifics>
## Specific Ideas

- Keep default profile values aligned with current baseline in `implant/headers/config.h` so migration risk is controlled.
- Keep diagnostics concise and fixture-addressable, consistent with Phase 1 regression output style.

</specifics>

<deferred>
## Deferred Ideas

- Reverse TCP profile/transport selection belongs to Phase 3.
- TLS verification policy hardening belongs to Phase 4.
- Full profile DSL parity for all Cobalt Strike directives is out of current milestone scope.

</deferred>

---

*Phase: 02-http-s-profile-abstraction*
*Context gathered: 2026-02-25*
