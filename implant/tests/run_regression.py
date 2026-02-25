#!/usr/bin/env python3
"""Deterministic fixture-driven regression runner for Phase 1."""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
FIXTURE_INDEX = SCRIPT_DIR / "fixture_index.json"
SUITE_MODULES = {
    "parser": SCRIPT_DIR / "test_task_parser.py",
    "protocol": SCRIPT_DIR / "test_protocol_roundtrip.py",
    "smoke": SCRIPT_DIR / "test_command_smoke.py",
}


def load_fixture_index() -> Dict[str, Any]:
    with FIXTURE_INDEX.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def filter_fixtures(fixtures: Iterable[Dict[str, Any]], mode: str, suite: str | None) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for fixture in fixtures:
        modes = fixture.get("modes", ["quick", "full"])
        if mode not in modes:
            continue
        if suite and fixture.get("suite") != suite:
            continue
        selected.append(fixture)
    selected.sort(key=lambda item: item.get("fixture_id", ""))
    return selected


def load_suite_runner(suite: str):
    module_path = SUITE_MODULES[suite]
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"suite_{suite}", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "run_suite", None)


def print_dry_run(fixtures: List[Dict[str, Any]], suite: str | None, mode: str) -> int:
    if not fixtures:
        print(f"DRY-RUN mode={mode} suite={suite or 'all'} fixtures=0")
        return 1
    print(f"DRY-RUN mode={mode} suite={suite or 'all'} fixtures={len(fixtures)}")
    for fixture in fixtures:
        print(f"- {fixture['fixture_id']} ({fixture['suite']})")
    return 0


def run(args: argparse.Namespace) -> int:
    index = load_fixture_index()
    fixtures = filter_fixtures(index.get("fixtures", []), args.mode, args.suite)

    if args.dry_run:
        return print_dry_run(fixtures, args.suite, args.mode)

    suites = [args.suite] if args.suite else sorted({fixture["suite"] for fixture in fixtures})
    if not suites:
        print("FAIL fixture_index semantic no fixtures matched selection")
        return 1

    failures: List[Dict[str, str]] = []
    passes = 0
    for suite in suites:
        runner = load_suite_runner(suite)
        if runner is None:
            failures.append({
                "fixture_id": f"suite-{suite}",
                "assertion": "runner_available",
                "detail": "suite module missing run_suite",
            })
            continue
        suite_fixtures = [f for f in fixtures if f.get("suite") == suite]
        results = runner(mode=args.mode, fixtures=suite_fixtures, root=SCRIPT_DIR, verbose=args.verbose)
        for result in results:
            if result.get("passed"):
                passes += 1
            else:
                failures.append(
                    {
                        "fixture_id": result.get("fixture_id", "unknown"),
                        "assertion": result.get("assertion", "unknown"),
                        "detail": result.get("detail", "no diff summary"),
                    }
                )

    if failures:
        for failure in sorted(failures, key=lambda item: (item["fixture_id"], item["assertion"])):
            print(f"FAIL {failure['fixture_id']} {failure['assertion']} {failure['detail']}")
        print(f"SUMMARY status=failed mode={args.mode} passed={passes} failed={len(failures)}")
        return 1

    print(f"SUMMARY status=passed mode={args.mode} suites={len(suites)} checks={passes}")
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic fixture regressions")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    parser.add_argument("--suite", choices=sorted(SUITE_MODULES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
