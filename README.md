# Pomodoro BLE Display (Adafruit Feather + OLED + NeoPixel)

A **wireless Pomodoro status display** built using an **Adafruit Feather nRF52840**, a **SH1107 OLED FeatherWing**, and a **NeoPixel**. It receives **BLE commands** and shows **Pomodoro status + timer + color indicator**.

* Wireless (Bluetooth Low Energy)  
* Works with any Pomodoro app / custom automation  
* Tiny desk or free/busy office door display  
* Battery-powered  
* Optional Freeplane integration  

---

## Hardware Build 

### Parts List

| Item | Qty | Link |
|------|-----|------|
| Adafruit Feather nRF52840 Express | 1 | https://www.adafruit.com/product/4062 |
| SH1107 OLED FeatherWing (128x64) | 1 | https://www.adafruit.com/product/4650 |
| NeoPixel 5mm or Mini PCB | 1 | https://www.adafruit.com/product/1734 or similar |
| JST-PH Battery | 1 | https://www.adafruit.com/category/889 |
| USB-C or Micro USB cable | 1 | for flashing |
| Solder headers | 1 | attach OLED FeatherWing |
| Breadboard/jumpers (optional) | – | for testing |

### Neopixel safety  (optional)

Simple safety components for NeoPixel recommended by Adafruit - but optional if you're only using one neopixel.

| Component | Purpose |
|-----------|---------|
| 470Ω resistor (data line) | Prevents signal spikes to the NeoPixel |
| 1000µF capacitor (across 3V and GND) | Protects against inrush power at startup |

#### Recommended wiring:

```
Feather D5 ---- 470Ω resistor ----> NeoPixel DIN
Feather 3V -----------------------> NeoPixel +
Feather GND ----------------------> NeoPixel GND
1000µF capacitor across + and GND (watch polarity!)
```

NB: The capacitor must be connected with correct polarity: **– to GND**, **+ to 3V**.

This is essential if you expand to multiple LEDs later.



---

### Wiring

None required if using stacking headers - just plug the FeatherWing onto the Feather.

For manual wiring:

| OLED Pin | Feather Pin |
|----------|-------------|
| `3V`     | 3V |
| `GND`    | GND |
| `SDA`    | SDA |
| `SCL`    | SCL |

| NeoPixel Pin | Feather Pin |
|---------------|-------------|
| `+`           | 3V |
| `-`           | GND |
| `DIN`         | D5 |

*(GPIO pin can be changed in `code.py`.)*

---
## Firmware Installation (Feather)

1. Install **CircuitPython 9.2.x** on the Feather  
   https://circuitpython.org/board/feather_nrf52840_express/
2. Download **CircuitPython Library Bundle 9.x**  
   https://circuitpython.org/libraries
3. Copy these to `CIRCUITPY/lib/`:
   ```
   adafruit_ble/
   adafruit_bus_device/
   adafruit_register/
   adafruit_displayio_sh1107.mpy
   adafruit_display_text/
   neopixel.mpy
   ```
4. Copy `code.py` from this repo to the `CIRCUITPY` drive
5. Reset the board — you should see:
   - OLED: `Idle`
   - NeoPixel: green

---

##  BLE Control

The display responds to **BLE UART commands**:

| Command | Effect |
|---------|--------|
| `START <seconds>` | Start countdown |
| `PAUSE` | Pause timer |
| `RESUME` | Resume |
| `STOP` | Stop timer |
| `BREAK <seconds>` | Optional break mode |

Example:
```
START 1500
PAUSE
RESUME
STOP
```

---

## Desktop BLE Client (Mac only here: `mac_pomodoro_ble.py`)

Run BLE commands from your computer:

### Install dependency:
```bash
python3 -m pip install bleak
```

### Example:
```bash
python3 mac_pomodoro_ble.py START 1500
```

You might have to rewrite the pomodoro_ble.py script to work with your platform.

---

## Configuration

Edit settings at the top of `code.py`:

```python
CONFIG = {
  "ble_name": "PomodoroDisp",
  "text_pomodoro": "Pomodoro ends in",
  "text_break": "Break ends in",
  "text_idle": "Idle",
  "text_paused": "Paused",
  "text_done": "Done!",
  "neopixel_pin": "D5"
}
```


---

## Ussage

At this point, you can trigger the hardware timer however you want:
- From shell scripts
- Integrate it with StreamDeck
- Use Raycast or Keyboard Maestro
- Connect it to Obsidian or log workflows
- Tie into your own Pomodoro app - I made one for [Freeplane]([url](https://docs.freeplane.org/)) - see below.

Example shell alias:
```bash
alias pomo25='python3 mac_pomodoro_ble.py START 1500'
```

---

## Optional Freeplane Integration

If you want full mind-map + Pomodoro workflow, follow the set-up instructions for my standaline freeplane pomodoro timer here: https://github.com/saulalbert/freeplane-pomodoro-timer

* Instead of the stanalone script, use the pomodoro script in this repo: `pomodoro_timer.groovy`  
* This automatically sends BLE commands on start/pause/stopping a pomodoro
* Tracks time per Freeplane node  
* Optional log to attributes of main node

### Freeplane setup:
1. Enable scripting in settings
2. Install Groovy Pomodoro script
3. Configure path to `mac_pomodoro_ble.py`
4. Start timer — Feather updates wirelessly
5. You might want to create a copy of the standalone [pomodoro.groovy]([url](https://github.com/saulalbert/freeplane-pomodoro-timer)) script for 'offline' use (i.e., when you're not connecting to the feather).

> NB Freeplane integration is optional and lives in its own folder.

---


## License

This project is released as **CC0-1.0 – Public Domain**  

---

## Power

- Runs from USB **or** LiPo battery
- Supports automatic charging
- You can put this on the door of your office to dissuade interruptions

---

## Maybe happening next

- Integrations into other pomodoro timers
- Battery saver mode
- Task name on OLED
- 3D printable enclosure
- Web Bluetooth control
- Cross-platform GUI


