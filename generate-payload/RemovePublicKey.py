import os
import argparse
import pathlib
import sys

THIS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
SEARCH_STRING = "unsigned char BEACON_PUBLIC_KEY[256] ="

def remove_public_key(target: str):
    replacement_line = f'unsigned char BEACON_PUBLIC_KEY[256] = "\\x30";\n'

    # Determine target path
    if target == "macos":
        beacon_path = REPO_ROOT / "implant-macos/src/beacon.c"
    else:
        beacon_path = REPO_ROOT / "implant/src/beacon.c"

    if not beacon_path.exists():
        print(f"ERROR: Target file not found: {beacon_path}")
        return 1

    # Read original file
    with open(beacon_path, "r") as f:
        lines = f.readlines()

    # Write modified file
    temp_path = beacon_path.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        for line in lines:
            if SEARCH_STRING in line:
                f.write(replacement_line)
                print(f"Replaced public key line with placeholder in {beacon_path.relative_to(REPO_ROOT)}!")
            else:
                f.write(line)

    os.replace(temp_path, beacon_path)
    return 0

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Remove public key from beacon.c")
    parser.add_argument("--target", choices=["linux", "macos"], default="linux", help="Target platform (default: linux)")
    return parser.parse_args(argv)

def main(argv):
    args = parse_args(argv)
    return remove_public_key(args.target)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
