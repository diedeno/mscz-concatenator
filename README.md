[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html)

# mscz-concatenator

A simple graphical front-end for [**ms-concatenate.py**](https://github.com/Zen-Master-SoSo/mscore/blob/master/scripts/ms_concatenate.py), part of the [Zen-Master-SoSo/mscore](https://github.com/Zen-Master-SoSo/mscore) library, announced on https://linuxmusicians.com/viewtopic.php?t=28728

This tool lets you **concatenate multiple MuseScore `.mscz` files** into a single new file.


![screenshot](screenshot.png)

### Features 
- Combine multiple `.mscz` MuseScore files into one.
- Reorder files before concatenation.
- Available as: - Windows standalone `.exe`
                - Linux executable`
---

## Installation

### Option 1 — Use the prebuilt executables

#### **Linux**
Download the native executable dist/mscz-concatenator
Then make it executable and run:
```bash
chmod +x mscz-concatenator
./mscz-concatenator
````

#### **Windows**
Download: dist/mscz-concatenator.exe
Then double-click to launch. No installation required.

### Option 2 — Run from source (Linux / Windows)

-Download ms_concatenator.py and mscz-concatentor.py and save in the same directory.
Install Python 3.8+ and dependencies:
```bash
pip install mscore3
````
(The mscore library is available here: https://github.com/Zen-Master-SoSo/mscore)

Run the GUI:
```bash
python3 mscz-concatenator.py
````


