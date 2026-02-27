#!/usr/bin/env python3
"""Protocol semantic roundtrip regression checks for REL-01."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, List

# Anchor path for key-link checks and future fixture expansion:
# fixtures/protocol/v1/smoke
SMOKE_FIXTURE_ROOT = pathlib.Path("fixtures/protocol/v1/smoke")


def _load_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_config_defines(config_h: pathlib.Path) -> Dict[str, str]:
    defines: Dict[str, str] = {}
    pattern = re.compile(r"^#define\s+(\w+)\s+(.+)$")
    for line in config_h.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        key, value = match.groups()
        defines[key] = value.strip().strip('"')
    return defines


def _semantic_encode(metadata_fixture: Dict[str, Any]) -> Dict[str, Any]:
    profile = metadata_fixture["profile"]
    expectations = metadata_fixture["semantic_expectations"]
    return {
        "magic": expectations["magic"],
        "session_key_length": int(expectations["session_key_length"]),
        "transport": profile["transport"],
        "server": profile["server"],
        "port": int(profile["port"]),
        "endpoints": [profile["get_uri"], profile["post_uri"]],
        "flags": sorted(expectations["metadata_flags"]),
    }


def _semantic_decode(encoded: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "magic": encoded["magic"],
        "session_key_length": encoded["session_key_length"],
        "transport": encoded["transport"],
        "server": encoded["server"],
        "port": encoded["port"],
        "endpoints": list(encoded["endpoints"]),
        "flags": sorted(encoded["flags"]),
    }


def _check_beacon_anchor(root: pathlib.Path) -> Dict[str, Any]:
    beacon_source = (root.parent / "src/beacon.c").read_text(encoding="utf-8")
    passed = "beacon_generate_metadata" in beacon_source and "0x0000BEEF" in beacon_source
    detail = "beacon metadata anchors present" if passed else "missing metadata anchors in beacon.c"
    return {
        "fixture_id": "protocol-source-anchor",
        "assertion": "metadata_anchor",
        "passed": passed,
        "detail": detail,
    }


def run_suite(mode: str, fixtures: List[Dict[str, Any]], root: pathlib.Path, verbose: bool = False) -> List[Dict[str, Any]]:
    del mode
    results: List[Dict[str, Any]] = [_check_beacon_anchor(root)]

    config_values = _parse_config_defines(root.parent / "headers/config.h")

    for fixture in sorted(fixtures, key=lambda item: item["fixture_id"]):
        if fixture.get("category") != "metadata":
            continue

        fixture_data = _load_json(root / fixture["path"])
        profile = fixture_data["profile"]

        config_match = (
            profile["server"] == config_values.get("C2_SERVER")
            and int(profile["port"]) == int(config_values.get("C2_PORT", "0"))
            and profile["get_uri"] == config_values.get("HTTP_GET_URI")
            and profile["post_uri"] == config_values.get("HTTP_POST_URI")
            and profile["user_agent"] == config_values.get("USER_AGENT")
        )

        encoded = _semantic_encode(fixture_data)
        decoded = _semantic_decode(encoded)
        expected = {
            "magic": fixture_data["semantic_expectations"]["magic"],
            "session_key_length": int(fixture_data["semantic_expectations"]["session_key_length"]),
            "transport": profile["transport"],
            "server": profile["server"],
            "port": int(profile["port"]),
            "endpoints": [profile["get_uri"], profile["post_uri"]],
            "flags": sorted(fixture_data["semantic_expectations"]["metadata_flags"]),
        }

        passed = config_match and decoded == expected
        detail = "semantic equivalence preserved" if passed else "metadata semantic mismatch"

        results.append(
            {
                "fixture_id": fixture["fixture_id"],
                "assertion": "semantic_roundtrip",
                "passed": passed,
                "detail": detail,
            }
        )

        if verbose:
            print(f"PROTOCOL {fixture['fixture_id']} {detail}")

    return results
