"""
Pomodoro BLE Display for Adafruit Feather nRF52840 + SH1107 + NeoPixel
- Supports START, BREAK, PAUSE, RESUME, STOP commands over BLE UART
- Sends DONE when a countdown reaches zero
- Amber NeoPixel during breaks; red during focus; blue paused; green idle; yellow done
- Static header above countdown ("Pomodoro ends in", "Break ends in", etc.)
CC0-1.0 Public Domain
"""

# ---------------------------
# CONFIG
# ---------------------------
CONFIG = {
    "ble_name": "PomoDisp",   # keep ≤10 chars to fit BLE advertising
    "i2c_address": 0x3C,
    "display_width": 128,
    "display_height": 64,
    "neopixel_pin": "D5",
    "neopixel_brightness": 0.2,
    "auto_readvertise": True,

    # Text
    "text_idle": "Idle",
    "text_paused": "Paused",
    "text_done": "Done!",
    "text_pomodoro": "Pomodoro ends in",
    "text_break": "Break ends in",
}

# ---------------------------
# IMPORTS
# ---------------------------
import time
import board
import displayio
import terminalio
import neopixel
from adafruit_display_text import label
import adafruit_displayio_sh1107

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement, Advertisement
from adafruit_ble.services.nordic import UARTService

# ---------------------------
# NEOPIXEL
# ---------------------------
_NEOPIX_PIN = getattr(board, CONFIG["neopixel_pin"])
pixel = neopixel.NeoPixel(_NEOPIX_PIN, 1,
                          brightness=CONFIG["neopixel_brightness"],
                          auto_write=True)
def set_status(rgb): pixel[0] = rgb

# ---------------------------
# DISPLAY
# ---------------------------
displayio.release_displays()
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=CONFIG["i2c_address"])
display = adafruit_displayio_sh1107.SH1107(display_bus,
                                           width=CONFIG["display_width"],
                                           height=CONFIG["display_height"])

# Two-line layout: header + countdown
root = displayio.Group()
display.root_group = root
header_label = label.Label(terminalio.FONT, text="", x=0, y=18)
timer_label  = label.Label(terminalio.FONT, text="", x=0, y=38)
root.append(header_label)
root.append(timer_label)

def _center_x(txt):
    return (CONFIG["display_width"] - len(txt) * 6) // 2

def set_header(text):
    header_label.text = text
    header_label.x = _center_x(text)

def show_time(mm, ss):
    ts = "{:02d}:{:02d}".format(mm, ss)
    timer_label.text = ts
    timer_label.x = _center_x(ts)

def clear_timer():
    timer_label.text = ""

# ---------------------------
# BLE
# ---------------------------
ble = BLERadio()
uart = UARTService()
adv = ProvideServicesAdvertisement(uart)
# Use short_name to avoid oversized advertising payloads
adv.short_name = CONFIG["ble_name"][:10]
# Also provide a scan response with the same short name
scan_resp = Advertisement()
scan_resp.short_name = CONFIG["ble_name"][:10]

def ensure_advertising():
    if CONFIG["auto_readvertise"] and not ble.connected and not ble.advertising:
        ble.start_advertising(adv, scan_response=scan_resp)

ble.start_advertising(adv, scan_response=scan_resp)

# ---------------------------
# POMODORO STATE
# ---------------------------
countdown = None
paused = False
on_break = False
last_tick = time.monotonic()

def _update_header_for_mode():
    set_header(CONFIG["text_break"] if on_break else CONFIG["text_pomodoro"])

def start_countdown(sec, break_mode=False):
    global countdown, paused, on_break, last_tick
    countdown = int(sec)
    paused = False
    on_break = bool(break_mode)
    last_tick = time.monotonic()

    # LED color by mode
    if on_break:
        set_status((255, 100, 0))   # amber during break
    else:
        set_status((255, 0, 0))     # red during focus

    _update_header_for_mode()
    show_time(countdown // 60, countdown % 60)
    try: uart.write(b"ACK START\n")
    except: pass

def pause():
    global paused
    if countdown is None: return
    paused = True
    set_header(CONFIG["text_paused"])
    set_status((0, 0, 255))  # blue
    try: uart.write(b"ACK PAUSE\n")
    except: pass

def resume():
    global paused
    if countdown is None: return
    paused = False
    if on_break:
        set_status((255, 100, 0))   # amber again
    else:
        set_status((255, 0, 0))     # red
    _update_header_for_mode()
    try: uart.write(b"ACK RESUME\n")
    except: pass

def stop():
    global countdown, paused, on_break
    countdown = None
    paused = False
    on_break = False
    set_status((0, 255, 0))  # green
    set_header(CONFIG["text_idle"])
    clear_timer()
    try: uart.write(b"ACK STOP\n")
    except: pass

# Init UI
stop()

# ---------------------------
# MAIN LOOP
# ---------------------------
print("Ready; advertising (short name):", CONFIG["ble_name"][:10])

while True:
    ensure_advertising()
    now = time.monotonic()

    # Handle BLE commands
    if ble.connected and uart.in_waiting:
        raw = uart.readline()
        if raw:
            try:
                cmd = raw.decode("utf-8").strip().upper()
            except:
                cmd = str(raw).upper()
            parts = cmd.split()
            if not parts:
                pass
            elif parts[0] == "START" and len(parts) >= 2:
                try: start_countdown(int(parts[1]), break_mode=False)
                except: uart.write(b"ERR BAD_START\n")
            elif parts[0] == "BREAK" and len(parts) >= 2:
                try: start_countdown(int(parts[1]), break_mode=True)
                except: uart.write(b"ERR BAD_BREAK\n")
            elif parts[0] == "PAUSE":
                pause()
            elif parts[0] == "RESUME":
                resume()
            elif parts[0] == "STOP":
                stop()
            elif parts[0] == "DONE":
                # optional: if host explicitly says DONE, flash yellow briefly and return to idle
                set_header(CONFIG["text_done"])
                set_status((255, 255, 0))
                time.sleep(1.5)
                stop()
            else:
                try: uart.write(b"ERR UNKNOWN\n")
                except: pass

    # Countdown tick
    if countdown is not None and not paused and (now - last_tick) >= 1.0:
        last_tick = now
        countdown -= 1
        if countdown <= 0:
            # Natural completion
            set_header(CONFIG["text_done"])
            set_status((255, 255, 0))  # yellow done
            try: uart.write(b"DONE\n")
            except: pass
            time.sleep(2.0)
            stop()
        else:
            show_time(countdown // 60, countdown % 60)

    time.sleep(0.05)
