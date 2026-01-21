# python-gui-autoclicker
Simple Python auto-clicker for Windows with configurable delay and coordinates.

## Description
This tool was created primarily for me and my colleagues to automatically refresh static web pages, which helped simplify repetitive manual actions during daily work.
The application performs mouse clicks at specified screen coordinates with a configurable time interval.

## Features
- GUI-based interface
- Automatic mouse clicking with configurable interval
- Support for start/stop hotkey binding
- Option to stop auto-clicking on manual left mouse click
- Ability to skip auto-clicking by setting coordinates to `0`
- All settings are automatically saved to `config.ini`
- No reconfiguration required on restart

## Build
To build the executable version, only one external tool is required: PyInstaller.

bash:
pyinstaller --onefile --noconsole --name AutoClicker gui.py
