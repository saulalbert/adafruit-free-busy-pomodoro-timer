# Pomodoro BLE Display (Adafruit Feather + OLED + NeoPixel)

A **wireless Pomodoro status display** built using an **Adafruit Feather nRF52840**, a **SH1107 OLED FeatherWing**, and a **NeoPixel**. It receives **BLE commands** from a Mac/Linux/Windows machine and shows **Pomodoro status + timer + color indicator**.

* Wireless (Bluetooth Low Energy)  
* Works with any Pomodoro app / custom automation  
* Tiny desk display  
* Battery-powered and hackable  
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

##  Firmware Installation

1. Install **CircuitPython 9.2.x** on your Feather:
   https://circuitpython.org/board/feather_nrf52840_express/

2. Download the **CircuitPython 9.x Library Bundle**:
   https://circuitpython.org/libraries

3. Copy these folders/files into the `CIRCUITPY/lib/` folder:
