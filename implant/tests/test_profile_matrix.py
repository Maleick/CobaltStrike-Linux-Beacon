#!/usr/bin/env python3
"""Profile compatibility matrix checks for default and non-default HTTP/S profiles."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, Iterable, List

ALLOWED_INVARIANTS = {
    "metadata_magic_unchanged",
    "task_exchange_compatible",
}


def _load_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _render_headers(profile_data: Dict[str, Any]) -> List[str]:
    headers = profile_data.get("http_headers", {})
    rendered: List[str] = []
    for key in sorted(headers.keys()):
        rendered.append(f"{key}: {headers[key]}")
    return rendered


def _transport(profile_data: Dict[str, Any]) -> str:
    return "https" if bool(profile_data.get("use_https")) else "http"


def _build_semantic_snapshot(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "transport": _transport(profile_data),
        "server": profile_data.get("host"),
        "port": int(profile_data.get("port", 0)),
        "get_uri": profile_data.get("http_get_uri"),
        "post_uri": profile_data.get("http_post_uri"),
        "user_agent": profile_data.get("user_agent"),
        "required_headers": _render_headers(profile_data),
    }


def _check_source_anchors(root: pathlib.Path) -> Dict[str, Any]:
    profile_source = (root.parent / "src/profile.c").read_text(encoding="utf-8")
    http_source = (root.parent / "src/http.c").read_text(encoding="utf-8")

    has_profile_api = "profile_get_http_get_uri" in profile_source and "profile_get_header_count" in profile_source
    has_http_usage = "profile_get_server" in http_source and "profile_get_user_agent" in http_source
    passed = has_profile_api and has_http_usage

    return {
        "fixture_id": "profile-source-anchor",
        "assertion": "profile_runtime_anchor",
        "passed": passed,
        "detail": "profile/http anchors present" if passed else "missing profile/http integration anchors",
    }


def _check_invariants(metadata_fixture: Dict[str, Any], mode: str) -> Dict[str, Any]:
    invariants = metadata_fixture.get("semantic_invariants", [])
    invariant_set = set(invariants)

    has_only_allowed = invariant_set.issubset(ALLOWED_INVARIANTS)
    has_required = {"metadata_magic_unchanged", "task_exchange_compatible"}.issubset(invariant_set)
    no_duplicates = len(invariants) == len(invariant_set)

    if mode == "quick":
        passed = has_only_allowed and has_required
    else:
        passed = has_only_allowed and has_required and no_duplicates and len(invariants) >= 2

    detail = (
        f"invariants={','.join(invariants)} "
        f"allowed={has_only_allowed} required={has_required} unique={no_duplicates}"
    )

    return {
        "assertion": "semantic_invariants",
        "passed": passed,
        "detail": detail,
    }


def _check_fixture(
    fixture: Dict[str, Any],
    metadata_fixture: Dict[str, Any],
    profile_fixture: Dict[str, Any],
    mode: str,
) -> List[Dict[str, Any]]:
    fixture_id = fixture["fixture_id"]

    expected = metadata_fixture.get("expected", {})
    observed = _build_semantic_snapshot(profile_fixture)
    semantic_passed = observed == expected

    semantic_detail = "semantic equivalence preserved" if semantic_passed else (
        f"expected={json.dumps(expected, sort_keys=True)} observed={json.dumps(observed, sort_keys=True)}"
    )

    metadata_id_passed = metadata_fixture.get("fixture_id") == fixture_id
    metadata_id_detail = (
        "fixture IDs aligned"
        if metadata_id_passed
        else f"index fixture_id={fixture_id} metadata fixture_id={metadata_fixture.get('fixture_id')}"
    )

    invariants_result = _check_invariants(metadata_fixture, mode)

    return [
        {
            "fixture_id": fixture_id,
            "assertion": "fixture_id_alignment",
            "passed": metadata_id_passed,
            "detail": metadata_id_detail,
        },
        {
            "fixture_id": fixture_id,
            "assertion": "profile_semantic_compatibility",
            "passed": semantic_passed,
            "detail": semantic_detail,
        },
        {
            "fixture_id": fixture_id,
            "assertion": invariants_result["assertion"],
            "passed": invariants_result["passed"],
            "detail": invariants_result["detail"],
        },
    ]


def run_suite(mode: str, fixtures: List[Dict[str, Any]], root: pathlib.Path, verbose: bool = False) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = [_check_source_anchors(root)]

    for fixture in sorted(fixtures, key=lambda item: item["fixture_id"]):
        metadata_fixture = _load_json(root / fixture["path"])
        profile_fixture_path = root / metadata_fixture["profile_fixture"]
        profile_fixture = _load_json(profile_fixture_path)

        fixture_results = _check_fixture(fixture, metadata_fixture, profile_fixture, mode)
        results.extend(fixture_results)

        if verbose:
            for item in fixture_results:
                print(f"PROFILE {item['fixture_id']} {item['assertion']} {item['detail']}")

    return results
