# macOS ARM64 Beacon Operator Runbook

This guide covers the generation, deployment, and management of the macOS ARM64 beacon for internal purple-team validation.

## 1. Generation Pipeline

The macOS beacon is generated via the **Custom Beacons** menu in Cobalt Strike.

1.  **Open Cobalt Strike** and ensure `CustomBeacon.cna` is loaded.
2.  Navigate to **Custom Beacons** -> **Generate Custom Beacons**.
3.  **Dialog Configuration:**
    - **Listener:** Select a valid HTTP or HTTPS listener.
    - **Executable Name:** Enter the desired name for your binary (e.g., `beacon-macos`).
    - **Profile Path:** Path to your custom JSON profile (default is `../profiles/http/default-profile.json`).
    - **Platform:** Select **macOS**.
4.  **Build Execution:**
    - Click **Generate**.
    - The Aggressor script will invoke the Python generation tools (`InsertListenerInfo.py`, `InsertPublicKey.py`) with the `--target macos` flag.
    - It will then run `make` in the `implant-macos/` directory to produce a Mach-O ARM64 binary.
5.  **Output Location:** The final binary will be located at `implant-macos/bin/<Executable Name>`.

## 2. Deployment Procedure

Once generated, the beacon must be transferred to the target macOS host.

### Quarantine Attribute
macOS attaches a quarantine extended attribute (`com.apple.quarantine`) to files downloaded from the internet or transferred via certain channels. This will cause the beacon to fail execution with a "Killed: 9" error or a security warning.

To remove the quarantine attribute:
```bash
xattr -d com.apple.quarantine /path/to/beacon-macos
```

### Execution
Ensure the binary has execution permissions:
```bash
chmod +x /path/to/beacon-macos
./beacon-macos
```

## 3. Signature & Verification

The build system automatically applies an **ad-hoc code signature** to the binary. This is sufficient for execution on Apple Silicon (M1-M4) but does not provide identity-based trust.

To verify the signature and architecture:
```bash
# Verify signature
codesign -dv /path/to/beacon-macos

# Verify architecture (should be arm64)
file /path/to/beacon-macos
```

## 4. Operational Monitoring

### Metadata in Team Server
When the beacon checks in, verify the following metadata in the Cobalt Strike console:
- **Hostname & User:** Should match the target host and execution context.
- **Process Name:** Should show the correct process name (via `getprogname()`).
- **OS Version:** Should report the macOS marketing version (e.g., `15.0`).
- **Architecture:** Will show `x64` for compatibility with the Cobalt Strike UI.

### Supported Commands
The v2.0 macOS beacon supports the following core POSIX commands:
- `sleep`, `cd`, `pwd`, `ls`, `upload`, `download`, `exit`.
- **SOCKS Pivot:** Standard `select()`-based SOCKS proxying.

## 5. Troubleshooting

- **Killed: 9:** Usually caused by a missing or invalid code signature, or the quarantine attribute still being present.
- **No Check-in:** Check the `profile_config.h` in `implant-macos/generated/` to ensure the listener IP and port are correct.
- **Command Output Garbage:** Likely a shell task offset mismatch (standard is 21 bytes).

## 6. Build Optimization

The default `make` command produces an optimized binary with ad-hoc signing. To strip debug symbols for a smaller footprint:
```bash
strip implant-macos/bin/beacon-macos
```
*Note: The current build system handles most optimization via Clang `-O2`.*
