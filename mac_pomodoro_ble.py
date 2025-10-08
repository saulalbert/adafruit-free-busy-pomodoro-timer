import asyncio
import sys
from bleak import BleakClient, BleakScanner

DEVICE_NAME = "CIRCUITPY8548"

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # write

async def send_command(cmd: str):
    print(f"Looking for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: ad.local_name == DEVICE_NAME
    )
    if device is None:
        print("Device not found. Is the Feather powered and advertising?")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {DEVICE_NAME}")
        await client.write_gatt_char(UART_TX_UUID, cmd.encode("utf-8"))
        print(f"Sent: {cmd}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 mac_pomodoro_ble.py START 1500 | STOP | PAUSE | RESUME")
        sys.exit(1)

    cmd = " ".join(sys.argv[1:])
    asyncio.run(send_command(cmd))

