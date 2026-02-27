#!/usr/bin/env python3
"""Resolve listener values into a selected profile and render generated config."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict

from validate_profile import validate_profile

THIS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
DEFAULT_PROFILE = REPO_ROOT / "profiles/http/default-profile.json"

def _resolve_path(raw: str) -> pathlib.Path:
    candidate = pathlib.Path(raw)
    if candidate.is_absolute():
        return candidate
    return (THIS_DIR / candidate).resolve()


def _load_profile(path: pathlib.Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"profile file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid profile JSON at {path}: {exc}") from exc


def _write_selected_profile(profile: Dict[str, Any], output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def insert_listener_info(target_server: str, target_port: int, https_value: int, profile_path: pathlib.Path, target: str, transport: str, ssl_ignore_verify: bool = False) -> int:
    profile = _load_profile(profile_path)

    profile["host"] = target_server
    profile["port"] = int(target_port)
    profile["use_https"] = bool(int(https_value))
    profile["ssl_ignore_verify"] = ssl_ignore_verify

    # Dynamically set output paths based on target
    if target == "macos":
        generated_dir = REPO_ROOT / "implant-macos/generated"
    else:
        generated_dir = REPO_ROOT / "implant/generated"

    selected_profile_path = generated_dir / "selected_profile.json"
    generated_header_path = generated_dir / "profile_config.h"

    _write_selected_profile(profile, selected_profile_path)

    _, errors = validate_profile(selected_profile_path)
    if errors:
        for error in errors:
            print(f"INVALID {selected_profile_path}: {error}")
        return 1

    render_cmd = [
        sys.executable,
        str(THIS_DIR / "render_profile_header.py"),
        "--profile",
        str(selected_profile_path),
        "--output",
        str(generated_header_path),
    ]
    subprocess.run(render_cmd, check=True)

    print(f"Profile selection resolved: source={profile_path} target={target}")
    print(f"Generated profile JSON: {selected_profile_path.relative_to(REPO_ROOT)}")
    print(f"Generated profile header: {generated_header_path.relative_to(REPO_ROOT)}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inject listener values into selected profile artifact")
    parser.add_argument("target_server")
    parser.add_argument("target_port", type=int)
    parser.add_argument("https_value", type=int, choices=[0, 1])
    parser.add_argument("profile_path", nargs="?", default=str(DEFAULT_PROFILE))
    parser.add_argument("--target", choices=["linux", "macos"], default="linux", help="Target platform (default: linux)")
    parser.add_argument("--transport", choices=["http", "tcp"], default="http", help="Transport type (default: http)")
    parser.add_argument("--ssl-ignore-verify", action="store_true", help="Disable SSL certificate verification")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    profile_path = _resolve_path(args.profile_path)

    try:
        return insert_listener_info(args.target_server, args.target_port, args.https_value, profile_path, args.target, args.transport, args.ssl_ignore_verify)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR InsertListenerInfo: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
