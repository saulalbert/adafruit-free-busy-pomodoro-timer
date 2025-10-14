"""
Pomodoro BLE Display for Adafruit Feather nRF52840 + SH1107 + NeoPixel
CC0-1.0 Public Domain
"""

# ---------------------------
# CONFIG
# ---------------------------
CONFIG = {
    "ble_name": "PomodoroDisp",
    "i2c_address": 0x3C,
    "display_width": 128,
    "display_height": 64,
    "neopixel_pin": "D5",
    "neopixel_brightness": 0.2,
    "auto_readvertise": True,
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
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
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

def set_header(text):
    header_label.text = text
    header_label.x = (CONFIG["display_width"] - len(text) * 6) // 2

def show_time(mm, ss):
    ts = "{:02d}:{:02d}".format(mm, ss)
    timer_label.text = ts
    timer_label.x = (CONFIG["display_width"] - len(ts) * 6) // 2

# ---------------------------
# BLE
# ---------------------------
ble = BLERadio()
uart = UARTService()
adv = ProvideServicesAdvertisement(uart)
adv.complete_name = CONFIG["ble_name"]

def ensure_advertising():
    if CONFIG["auto_readvertise"] and not ble.connected and not ble.advertising:
        ble.start_advertising(adv)

ble.start_advertising(adv)

# ---------------------------
# POMODORO STATE
# ---------------------------
countdown = None
paused = False
on_break = False
last_tick = time.monotonic()

def start_countdown(sec, break_mode=False):
    global countdown, paused, on_break, last_tick
    countdown = sec
    paused = False
    on_break = break_mode
    last_tick = time.monotonic()
    set_header(CONFIG["text_break"] if break_mode else CONFIG["text_pomodoro"])
    set_status((255, 0, 0))  # red
    show_time(sec // 60, sec % 60)

def pause():
    global paused
    paused = True
    set_header(CONFIG["text_paused"])
    set_status((0, 0, 255))  # blue

def resume():
    global paused
    paused = False
    set_status((255, 0, 0))  # red
    set_header(CONFIG["text_break"] if on_break else CONFIG["text_pomodoro"])

def stop():
    global countdown, paused, on_break
    countdown = None
    paused = False
    on_break = False
    set_status((0, 255, 0))  # green
    set_header(CONFIG["text_idle"])
    timer_label.text = ""

stop()

# ---------------------------
# MAIN LOOP
# ---------------------------
print("Ready, advertising as", CONFIG["ble_name"])

while True:
    ensure_advertising()
    now = time.monotonic()

    # Handle BLE commands
    if ble.connected and uart.in_waiting:
        cmd = uart.readline().decode("utf-8").strip().upper()
        parts = cmd.split()
        if parts[0] == "START":
            start_countdown(int(parts[1]))
        elif parts[0] == "BREAK":
            start_countdown(int(parts[1]), break_mode=True)
        elif parts[0] == "PAUSE":
            pause()
        elif parts[0] == "RESUME":
            resume()
        elif parts[0] == "STOP":
            stop()

    # Tick countdown
    if countdown and not paused and now - last_tick > 1:
        last_tick = now
        countdown -= 1
        if countdown <= 0:
            set_header(CONFIG["text_done"])
            set_status((255, 255, 0))  # yellow
            time.sleep(2)
            stop()
        else:
            show_time(countdown // 60, countdown % 60)

    time.sleep(0.05)

