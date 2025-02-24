# StageDeck

A versatile stage display application with support for NDI input and web streaming. With Companion variables handling via OSC.

## Features

- Transparent or opaque window display
- NDI input support
- Web streaming capability
- Timer functionality
- Customizable fields and text display
- OSC control support

## Installation

### Option 1: Install from Executable (Recommended)

1. Download the latest `StageDeck Installer.zip`
2. Extract the zip file
3. Run `StageDeck.exe`

### Option 2: Install from Source

1. Clone this repository
2. Install Python 3.9 or later
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. Launch StageDeck
2. Configure display settings in the Settings tab:
   - Choose monitor
   - Set background color or transparency
   - Enable NDI input as background if needed
   - Configure web streaming

3. Add and customize fields in the Fields tab that can be dynamically set and changed via OSC

4. Use the Timer tab for countdown/countup functionality

### Web Streaming

When web streaming is enabled, access the display from any device on your network:
1. Enable web streaming in the Settings tab
2. Access `http://<computer-ip>:8181` from any web browser
3. The display will update in real-time with minimal latency

## Development

- Main application: `main.py`
- Web server component: `web_server.py`
- Installer creation: `create_installer.py`
- PyInstaller spec: `companion_viewer.spec`
