#!/usr/bin/env python3
"""
mac_pomodoro_ble.py — Send BLE UART commands to the Feather Pomodoro display
CC0-1.0 (Public Domain). https://creativecommons.org/publicdomain/zero/1.0/

INSTALL:
  python3 -m pip install bleak

USAGE:
  python3 mac_pomodoro_ble.py START 1500
  python3 mac_pomodoro_ble.py PAUSE
  python3 mac_pomodoro_ble.py RESUME
  python3 mac_pomodoro_ble.py STOP

HOW IT FINDS THE DEVICE:
- By default we match either a specific name (e.g. "PomodoroDisp")
  or any device whose advertised name starts with "CIRCUITPY".
- You can change matchers in CONFIG below or via env var:
  POMODORO_NAME_MATCHERS="MyName;CIRCUITPY" (semicolon-separated).
"""

import os
import sys
import asyncio
from bleak import BleakClient, BleakScanner

# ---------------------------
# CONFIG
# ---------------------------
CONFIG = {
    # One or more name matchers. Any item that endswith('*') is treated as "prefix".
    # Examples: ["PomodoroDisp", "CIRCUITPY*"]
    "name_matchers": os.environ.get("POMODORO_NAME_MATCHERS", "PomodoroDisp;CIRCUITPY*")
                      .split(";"),

    # Nordic UART UUID (write)
    "uart_tx_uuid": "6E400002-B5A3-F393-E0A9-E50E24DCCA9E",

    # Scan timeout seconds
    "scan_timeout": float(os.environ.get("POMODORO_SCAN_TIMEOUT", "10")),
}

def _matches(name: str) -> bool:
    if not name:
        return False
    for raw in CONFIG["name_matchers"]:
        m = raw.strip()
        if not m:
            continue
        if m.endswith("*"):
            if name.startswith(m[:-1]):
                return True
        else:
            if name == m:
                return True
    return False

async def send_command(cmd: str):
    print("Scanning for Feather Pomodoro device...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: _matches(ad.local_name),
        timeout=CONFIG["scan_timeout"]
    )
    if device is None:
        print("Device not found. Check power/advertising.")
        return 2

    async with BleakClient(device) as client:
        print(f"Connected to {device.name or device.address}")
        await client.write_gatt_char(CONFIG["uart_tx_uuid"], cmd.encode("utf-8"))
        print(f"Sent: {cmd}")
    return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: mac_pomodoro_ble.py START 1500 | STOP | PAUSE | RESUME")
        return 1
    cmd = " ".join(sys.argv[1:])
    return asyncio.run(send_command(cmd))

if __name__ == "__main__":
    sys.exit(main())

