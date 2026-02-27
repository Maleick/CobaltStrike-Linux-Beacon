#!/usr/bin/env python3
"""Validate HTTP/S profile artifacts for deterministic build gating."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Tuple

REQUIRED_FIELDS = {
    "profile_id": str,
    "schema_version": str,
    "host": str,
    "port": int,
    "use_https": bool,
    "http_get_uri": str,
    "http_post_uri": str,
    "user_agent": str,
    "http_headers": dict,
    "ssl_ignore_verify": bool,
}

OPTIONAL_FIELDS = {"ssl_ignore_verify"}

def _load_json(path: pathlib.Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"profile file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg} (line {exc.lineno})")


def _validate_required_fields(profile: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in profile:
            if field in OPTIONAL_FIELDS:
                continue
            errors.append(f"missing required field '{field}'")
            continue
        value = profile[field]
        if expected_type is int and isinstance(value, bool):
            errors.append(f"field '{field}' must be int, got bool")
            continue
        if not isinstance(value, expected_type):
            errors.append(f"field '{field}' must be {expected_type.__name__}, got {type(value).__name__}")
    return errors


def _validate_semantics(profile: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    profile_id = profile.get("profile_id")
    if isinstance(profile_id, str) and not profile_id.strip():
        errors.append("profile_id cannot be empty")

    host = profile.get("host")
    if isinstance(host, str) and not host.strip():
        errors.append("host cannot be empty")

    port = profile.get("port")
    if isinstance(port, int) and not (1 <= port <= 65535):
        errors.append("port must be between 1 and 65535")

    for field in ("http_get_uri", "http_post_uri"):
        uri = profile.get(field)
        if isinstance(uri, str):
            if not uri.startswith("/"):
                errors.append(f"{field} must start with '/'")
            if " " in uri:
                errors.append(f"{field} must not contain spaces")

    user_agent = profile.get("user_agent")
    if isinstance(user_agent, str) and len(user_agent.strip()) < 10:
        errors.append("user_agent appears too short")

    headers = profile.get("http_headers")
    if isinstance(headers, dict):
        if not headers:
            errors.append("http_headers must include at least one header")
        for key, value in headers.items():
            if not isinstance(key, str) or not key.strip():
                errors.append("http_headers keys must be non-empty strings")
            if not isinstance(value, str) or not value.strip():
                errors.append(f"http_headers['{key}'] must be non-empty string")

    return errors


def validate_profile(path: pathlib.Path) -> Tuple[Dict[str, Any], List[str]]:
    profile = _load_json(path)
    errors = _validate_required_fields(profile)
    errors.extend(_validate_semantics(profile))
    return profile, errors


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate profile JSON artifacts")
    parser.add_argument("profile", type=pathlib.Path, help="Path to profile JSON file")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    profile_path = args.profile

    try:
        profile, errors = validate_profile(profile_path)
    except ValueError as exc:
        print(f"INVALID {profile_path}: {exc}")
        return 1

    if errors:
        for error in errors:
            print(f"INVALID {profile_path}: {error}")
        return 1

    print(
        "VALID profile_id={pid} schema={schema} host={host} port={port} https={https}".format(
            pid=profile["profile_id"],
            schema=profile["schema_version"],
            host=profile["host"],
            port=profile["port"],
            https=str(profile["use_https"]).lower(),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
