<div align="center">

# XLAT_NOVA

**Mouse & Keyboard Latency Measurement Tool**

*(A maintained fork of [Finalmouse XLAT](https://github.com/teamfinalmouse/xlat))*

[English](README.md) | [中文](README_zh.md)

</div>

## Overview

XLAT_NOVA measures input latency — click, motion and key press — between your
device and the host over USB. It runs on the STM32F746G-DISCO discovery board
and pairs a hardware trigger (GPIO edge) with the HID report timestamps it
captures from the USB host port.

It is a maintained fork of the open-source Finalmouse XLAT project (GPLv3).

## Features

- Three detection modes: **Mouse Click**, **Mouse Motion**, **Keyboard**
- Switching modes automatically applies the correct detection settings
  (edge / debounce / input bias) — no manual fiddling
- Bilingual UI (English / 中文), with the language choice saved across reboots
  (a firmware upgrade resets the UI back to English by default)
- Custom black theme with a personal logo
- One-click flasher tools for **macOS** and **Windows 10/11** (ST-LINK driver included)

## Improvements over upstream XLAT

Compared with the original Finalmouse XLAT firmware, this fork adds or fixes:

- **Bilingual UI (English / 中文)** — the language choice is saved in internal
  flash and survives reboots; a firmware upgrade resets the UI to English by
  default.
- **Auto detection configuration per mode** — the original firmware kept the
  same trigger edge when switching modes (e.g. Motion still used the click
  mode's falling edge), which produced wrong readings unless configured
  manually. Switching modes now automatically applies the correct edge /
  debounce / input bias.
- **Custom black theme** with a personal logo.
- **One-click flashing tools** for macOS and Windows 10/11, with a bundled
  ST-LINK driver; the Windows driver uninstall tool removes all driver traces
  (device nodes, driver packages, config files and registry entries).

## Required Hardware

- STM32F746G-DISCO (or a compatible STM32F7 discovery board with USB host)
- USB OTG cable / adapter for the device under test
- ST-LINK mini-USB cable (on-board ST-Link) for power & flashing

## Quick Start

### 1. Flash the firmware

Use the bundled flasher:

- **macOS**: open `XLAT一键刷机.app`
- **Windows**: run `1-Install-Driver.bat` first, then `2-Flash-XLAT.exe`

Or flash manually:

```sh
st-flash --connect-under-reset write build/release/xlat.bin 0x08000000
```

### 2. Wire the trigger input

| Signal | Connect to |
| --- | --- |
| Trigger input (D12) | CN7 pin 5 |
| GND | CN7 pin 7 |

The auto-trigger output uses D11 (CN7 pin 4) or D6, configured in Settings.

### 3. Measure

1. Connect the device under test to the USB host port and power the board.
2. On the home screen, choose the mode in **Settings → Mode**.
3. Move / click / press the key; the latency appears on the screen.
4. Press **Clear** to reset the statistics.

## Detection modes & auto-config

The mode dropdown automatically applies the matching detection config:

| Mode | Edge | Debounce | Bias |
| --- | --- | --- | --- |
| Mouse: Motion | Rising | 20 ms | Pull-up |
| Mouse: Click | Falling | 50 ms | Pull-up |
| Keyboard: Key | Falling | 50 ms | Pull-up |

## Known issues & troubleshooting

Carried over from the upstream XLAT README:

- **LCD artifacts / init failure**: if the display fails to initialize or shows
  artifacts, press **Reboot** or power-cycle the board.
- **Device not detected**: if the mouse or keyboard is not recognized, first
  flash the latest firmware (support for new devices is added regularly). If it
  still fails, the device needs descriptor support — collect the USB VID:PID
  and the HID report descriptor and report them so it can be added.

## Building from source

```sh
# requires arm-none-eabi toolchain + cmake + ninja
cmake -S . -B build -GNinja -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

## License

GPLv3. This project is a fork of
[Finalmouse XLAT](https://github.com/teamfinalmouse/xlat); see [COPYING](COPYING).
