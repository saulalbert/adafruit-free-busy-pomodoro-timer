import time
import board, displayio, terminalio, neopixel
from adafruit_display_text import label
import adafruit_displayio_sh1107

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

print("Pomodoro display (SH1107 + BLE) starting...")

# ---------------------
# NeoPixel setup
# ---------------------
pixel = neopixel.NeoPixel(board.D5, 1, brightness=0.2, auto_write=True)

def set_status(color):
    pixel[0] = color   # (R,G,B)

# ---------------------
# OLED setup
# ---------------------
displayio.release_displays()
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

display = adafruit_displayio_sh1107.SH1107(display_bus, width=128, height=64)

splash = displayio.Group()
display.root_group = splash

def show_text(text):
    splash.pop() if len(splash) else None
    text_area = label.Label(terminalio.FONT, text=text, x=10, y=32)
    splash.append(text_area)

def show_time(mm, ss):
    splash.pop() if len(splash) else None
    timestr = "{:02d}:{:02d}".format(mm, ss)
    x = (128 - len(timestr) * 6) // 2
    text_area = label.Label(terminalio.FONT, text=timestr, x=x, y=32)
    splash.append(text_area)

# ---------------------
# BLE setup
# ---------------------

ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)
advertisement.complete_name = "HelloBLE"
ble.start_advertising(advertisement)
print("Advertising as HelloBLE")



# ---------------------
# Pomodoro state
# ---------------------
countdown = None
last_tick = time.monotonic()
paused = False

def start_countdown(sec):
    global countdown, last_tick, paused
    countdown = int(sec)
    paused = False
    last_tick = time.monotonic()
    show_time(countdown // 60, countdown % 60)
    set_status((255, 0, 0))  # red running
    try: uart.write(b"ACK START\n")
    except: pass

def stop_countdown():
    global countdown, paused
    countdown = None
    paused = False
    show_text("Idle")
    set_status((0, 255, 0))  # green idle
    try: uart.write(b"ACK STOP\n")
    except: pass

def pause_countdown():
    global paused
    if countdown is not None:
        paused = True
        show_text("Paused")
        set_status((0, 0, 255))  # blue paused
        try: uart.write(b"ACK PAUSE\n")
        except: pass

def resume_countdown():
    global paused
    if countdown is not None and paused:
        paused = False
        set_status((255, 0, 0))  # back to red
        show_time(countdown // 60, countdown % 60)
        try: uart.write(b"ACK RESUME\n")
        except: pass

# ---------------------
# Init
# ---------------------
stop_countdown()

# ---------------------
# Main loop
# ---------------------
while True:
    # Make sure we keep advertising if disconnected
    if not ble.connected and not ble.advertising:
        ble.start_advertising(advertisement)
    
    now = time.monotonic()

    # BLE commands
    if ble.connected and uart.in_waiting:
        line = uart.readline()
        if line:
            try:
                cmd = line.decode("utf-8").strip().upper()
            except:
                cmd = str(line).upper()
            parts = cmd.split()
            if parts and parts[0] == "START" and len(parts) >= 2:
                try: start_countdown(int(parts[1]))
                except: uart.write(b"ERR BAD_START\n")
            elif parts and parts[0] == "STOP":
                stop_countdown()
            elif parts and parts[0] == "PAUSE":
                pause_countdown()
            elif parts and parts[0] == "RESUME":
                resume_countdown()
            else:
                try: uart.write(b"ERR UNKNOWN\n")
                except: pass

    # Countdown update
    if countdown is not None and not paused and now - last_tick >= 1.0:
        elapsed = int(now - last_tick)
        last_tick = now
        countdown -= elapsed
        if countdown <= 0:
            show_text("Done!")
            set_status((255, 255, 0))  # yellow finished
            try: uart.write(b"DONE\n")
            except: pass
            time.sleep(2.0)
            stop_countdown()
        else:
            show_time(countdown // 60, countdown % 60)

    time.sleep(0.05)


