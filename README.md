# StageDeck

A versatile stage display application with support for NDI input and web streaming.

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

## Building the Installer

To create a standalone executable installer:

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the installer creation script:
   ```bash
   python create_installer.py
   ```

3. The installer will be created as `StageDeck Installer.zip`

## Usage

1. Launch StageDeck
2. Configure display settings in the Settings tab:
   - Choose monitor
   - Set background color or transparency
   - Enable NDI input if needed
   - Configure web streaming

3. Add and customize fields in the Fields tab

4. Use the Timer tab for countdown/countup functionality

### Web Streaming

When web streaming is enabled, access the display from any device on your network:
1. Enable web streaming in the Settings tab
2. Access `http://<computer-ip>:8181` from any web browser
3. The display will update in real-time with minimal latency

## Development

- Main application: `main.py`
- Web server component: `web_server.py`
<<<<<<< HEAD
- PyInstaller spec: `stagedeck.spec`
=======
- Installer creation: `create_installer.py`
- PyInstaller spec: `companion_viewer.spec`
>>>>>>> c0b2564a41945d9df9eb14ab6dfef9dbfc1de4a9
