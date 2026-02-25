#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MODE="quick"

ARGS=()
while (($#)); do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --mode=*)
      MODE="${1#*=}"
      shift
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "$MODE" != "quick" && "$MODE" != "full" ]]; then
  echo "invalid mode: $MODE (expected quick|full)" >&2
  exit 2
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/run_regression.py" --mode "$MODE" "${ARGS[@]}"
