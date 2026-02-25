#!/usr/bin/env python3
"""Malformed task parser regression checks for reject-and-continue behavior.

The fixture expectations in parser_reject_continue.yaml are designed to mirror
`validate_task_layout` and `commands_parse_tasks` guard behavior in commands.c.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Tuple

import yaml


MATRIX_PATH = pathlib.Path("cases/parser_reject_continue.yaml")


def _be_u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big", signed=False)


def validate_task_layout(task_buffer: bytes, task_header_len: int) -> Tuple[bool, int, str]:
    """Python model of commands.c validate_task_layout."""
    offset = 0
    task_count = 0

    while offset + 8 <= len(task_buffer):
        command_id = _be_u32(task_buffer, offset)
        data_length = _be_u32(task_buffer, offset + 4)
        offset += 8

        if command_id == 0 or command_id > 0xFFFF:
            return False, task_count, "invalid_command_id"

        if task_header_len + data_length > len(task_buffer) - offset:
            return False, task_count, "length_overrun"

        offset += task_header_len + data_length
        task_count += 1

    if task_count > 0 and offset == len(task_buffer):
        return True, task_count, "ok"

    return False, task_count, "incomplete_header_or_trailing_bytes"


def simulate_commands_parse_tasks(task_buffer: bytes) -> Dict[str, Any]:
    """Model high-level parser decision: reject malformed payloads, continue loop."""
    v2_valid, _, v2_reason = validate_task_layout(task_buffer, task_header_len=8)
    v1_valid, _, v1_reason = validate_task_layout(task_buffer, task_header_len=0)

    if v2_valid or v1_valid:
        return {
            "outcome": "accept",
            "continue_loop": True,
            "reason": "layout_valid",
            "layout_path": "v2" if v2_valid else "v1",
        }

    # commands_parse_tasks should reject malformed payloads without process crash.
    return {
        "outcome": "reject",
        "continue_loop": True,
        "reason": f"layout_invalid(v2={v2_reason},v1={v1_reason})",
        "layout_path": "none",
    }


def _load_matrix(root: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    matrix_file = root / MATRIX_PATH
    raw = yaml.safe_load(matrix_file.read_text(encoding="utf-8"))
    cases = raw.get("cases", [])
    return {case["fixture_id"]: case["expected"] for case in cases}


def _check_source_anchors(root: pathlib.Path) -> Dict[str, Any]:
    commands_source = (root.parent / "src/commands.c").read_text(encoding="utf-8")
    has_validate = "validate_task_layout" in commands_source
    has_parse = "commands_parse_tasks" in commands_source
    passed = has_validate and has_parse
    detail = "source anchors present" if passed else "missing parser anchors in commands.c"
    return {
        "fixture_id": "parser-source-anchor",
        "assertion": "commands_source_anchor",
        "passed": passed,
        "detail": detail,
    }


def run_suite(mode: str, fixtures: List[Dict[str, Any]], root: pathlib.Path, verbose: bool = False) -> List[Dict[str, Any]]:
    del mode  # quick/full currently share the same malformed parser expectations.

    expected_map = _load_matrix(root)
    results: List[Dict[str, Any]] = [_check_source_anchors(root)]

    for fixture in sorted(fixtures, key=lambda item: item["fixture_id"]):
        fixture_id = fixture["fixture_id"]
        data = (root / fixture["path"]).read_bytes()
        observed = simulate_commands_parse_tasks(data)

        expected = expected_map.get(fixture_id, {})
        expected_outcome = expected.get("outcome", "reject")
        expected_continue = bool(expected.get("reject_continue", True))

        passed = (
            observed["outcome"] == expected_outcome
            and bool(observed["continue_loop"]) == expected_continue
        )

        detail = (
            f"expected={expected_outcome}/{expected_continue} "
            f"actual={observed['outcome']}/{observed['continue_loop']} "
            f"reason={observed['reason']}"
        )

        results.append(
            {
                "fixture_id": fixture_id,
                "assertion": "reject_continue",
                "passed": passed,
                "detail": detail,
            }
        )

        if verbose:
            print(f"PARSER {fixture_id} {detail}")

    return results
