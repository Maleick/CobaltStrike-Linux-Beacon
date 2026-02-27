#!/usr/bin/env python3
"""Baseline command smoke checks for sleep/pwd/cd callback compatibility."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, List

EXPECTED_CALLBACKS_PATH = pathlib.Path("fixtures/protocol/v1/smoke/expected_callbacks.json")


def _load_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_defines(path: pathlib.Path, prefix: str) -> Dict[str, int]:
    defines: Dict[str, int] = {}
    pattern = re.compile(r"^#define\s+(" + re.escape(prefix) + r"\w+)\s+([0-9xa-fA-F]+)")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        key, raw_value = match.groups()
        value = int(raw_value, 16) if raw_value.lower().startswith("0x") else int(raw_value)
        defines[key] = value
    return defines


def _command_key(command_name: str) -> str:
    return {
        "sleep": "COMMAND_SLEEP",
        "pwd": "COMMAND_PWD",
        "cd": "COMMAND_CD",
    }[command_name]


def run_suite(mode: str, fixtures: List[Dict[str, Any]], root: pathlib.Path, verbose: bool = False) -> List[Dict[str, Any]]:
    del mode
    results: List[Dict[str, Any]] = []

    commands_h = root.parent / "headers/commands.h"
    command_defines = _parse_defines(commands_h, "COMMAND_")
    callback_defines = _parse_defines(commands_h, "CALLBACK_")

    expected_callbacks = _load_json(root / EXPECTED_CALLBACKS_PATH)
    callback_names = expected_callbacks["callbacks"]
    callback_codes = expected_callbacks["callback_codes"]

    for fixture in sorted(fixtures, key=lambda item: item["fixture_id"]):
        fixture_data = _load_json(root / fixture["path"])
        command_name = fixture_data["command"]
        expected_callback_name = callback_names.get(command_name)

        fixture_command_id = int(fixture_data["command_id"])
        command_header_id = command_defines.get(_command_key(command_name), -1)

        callback_code_in_json = int(callback_codes.get(expected_callback_name or "", -1))
        callback_code_in_header = callback_defines.get(expected_callback_name or "", -2)

        callback_matches = callback_code_in_json == callback_code_in_header
        command_matches = fixture_command_id == command_header_id

        passed = command_matches and callback_matches
        detail = (
            f"command={command_name} id_fixture={fixture_command_id} id_header={command_header_id} "
            f"callback={expected_callback_name} code_fixture={callback_code_in_json} code_header={callback_code_in_header}"
        )

        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "assertion": "callback_semantic_match",
                "passed": passed,
                "detail": detail,
            }
        )

        if verbose:
            print(f"SMOKE {fixture['fixture_id']} {detail}")

    smoke_source_anchor = (root.parent / "src/commands.c").read_text(encoding="utf-8")
    has_switch_cases = "case COMMAND_SLEEP" in smoke_source_anchor and "case COMMAND_PWD" in smoke_source_anchor
    results.append(
        {
            "fixture_id": "smoke-source-anchor",
            "assertion": "commands_switch_anchor",
            "passed": has_switch_cases,
            "detail": "sleep/pwd switch anchors present" if has_switch_cases else "missing smoke switch anchors",
        }
    )

    return results
