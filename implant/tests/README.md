# Regression Fixtures and Harness

This directory contains the baseline fixture contract and deterministic regression harness
for Phase 1 (`REL-01`, `REL-02`).

## Layout

- `fixture_index.json`: Canonical registry for fixture IDs, suite ownership, version, assertion mode, and requirement traceability.
- `fixtures/protocol/v1/metadata/`: Metadata and protocol semantic fixtures.
- `fixtures/protocol/v1/profile/`: Default/non-default profile metadata compatibility fixtures.
- `fixtures/protocol/v1/tasks/`: Malformed task payload fixtures.
- `fixtures/protocol/v1/smoke/`: Baseline command smoke fixtures.
- `fixtures/profiles/http/`: Canonical profile artifact fixtures used by profile matrix tests.
- `cases/`: Matrix files that map fixtures to expected parser outcomes.

## Governance Rules

- Assertion mode is semantic equivalence by default (`assertion_mode: semantic`).
- Regression behavior is fail-by-default unless fixture updates are explicitly approved.
- Fixture IDs are stable and must remain deterministic in runner output.
- Fixture changes require rationale and review, especially if expected outcomes change.
- Profile fixtures must preserve semantic compatibility for default and non-default matrices unless explicitly approved.

## Running

Quick local gate:

```bash
bash implant/tests/run_regression.sh --mode quick
```

Full suite:

```bash
bash implant/tests/run_regression.sh --mode full
```

Profile-only suite:

```bash
python3 implant/tests/run_regression.py --suite profile --mode quick
```
