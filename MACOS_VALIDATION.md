# macOS Beacon Live Validation Steps

Please perform these steps to validate the macOS ARM64 beacon implementation (Phase 7).

## 1. Generation & Execution
1. Open Cobalt Strike and ensure your **Aggressor script (`CustomBeacon.cna`)** is loaded.
2. Go to **Custom Beacons** -> **Generate Custom Beacons**.
3. In the dialog:
   - Select a valid **HTTP or HTTPS listener**.
   - Set **Platform** to **macOS**.
   - (Optional) Set a custom **Profile Path**.
   - Click **Generate**.
4. Confirm the binary is generated (e.g., in `implant-macos/bin/`).
5. Transfer the binary to your target macOS ARM64 host.
6. **Important:** Remove the quarantine attribute before running:
   ```bash
   xattr -d com.apple.quarantine <binary_name>
   chmod +x <binary_name>
   ./<binary_name>
   ```

## 2. Metadata Verification
In the Cobalt Strike **Beacons** tab, verify the new check-in:
- [ ] **External IP:** Correct for the target host.
- [ ] **User:** Correct username.
- [ ] **Computer:** Correct hostname.
- [ ] **Process:** Should match the binary name (e.g., `beacon-macos`).
- [ ] **OS Version:** Should show **15.x** (or your actual macOS marketing version).
- [ ] **Arch:** Should show **x64** (this is expected for CS compatibility).

## 3. Command Validation
Interact with the beacon and run the following commands:
- [ ] `sleep 5 10`: Confirm the beacon updates its heartbeat.
- [ ] `pwd`: Confirm it returns the current working directory.
- [ ] `shell id`: Confirm it returns the output of the `id` command.
    - *Note: If this returns garbage or "command not found", the 21-byte shell offset may be incorrect for your specific CS version.*

## 4. Reporting Results
Please let me know if any of the above checks fail. If all pass, we will close Phase 7 and move to Phase 8 (Command Parity & SOCKS Pivot).
