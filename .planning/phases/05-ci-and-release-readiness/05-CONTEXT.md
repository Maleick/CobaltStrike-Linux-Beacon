# Phase 5: CI and Release Readiness

Goal: Every change is validated by automated Linux build/test gates before milestone completion.

## Success Criteria
1. CI pipeline builds implant and executes regression suite on Linux for each change.
2. Failing tests/builds block merge-ready status until resolved.
3. Release checklist verifies all mapped v1 requirements are covered by completed phase outputs.

## Requirements
- REL-03: CI pipeline builds the implant and runs regression tests on Linux for each change.

## User Decisions (Proposed Breakdown)
- 05-01-PLAN.md — Add CI workflow for build and regression suite execution (GitHub Actions).
- 05-02-PLAN.md — Add release-readiness checks tied to roadmap requirement coverage; finalize milestone v1.0.

## Claude's Discretion
- Use GitHub Actions for CI workflow (standard and already implied by "GitHub Actions" in the proposed breakdown).
- CI should run on `ubuntu-latest`.
- CI should install dependencies: `libssl-dev`, `libcurl4-openssl-dev`, `python3`.
- `05-02` will involve creating a checklist or automated script to verify requirements coverage.
- Finalizing milestone v1.0 will involve updating `ROADMAP.md` and `STATE.md`.
