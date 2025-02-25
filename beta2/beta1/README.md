# Companion Viewer

A dynamic value display application that receives data from Bitfocus Companion via OSC protocol.

## Features
- Receives real-time values via OSC/UDP
- Configurable display fields (size, position, content)
- Full screen or windowed mode
- Always-on-top capability
- Multi-monitor support

## Installation

1. Install Python 3.8 or newer
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

## Configuration
- Add/remove fields through the configuration window
- Adjust field positions and sizes visually
- Toggle between full screen and windowed mode
- Select target monitor for display

## OSC Control

The application listens for OSC messages on port 9191 by default. You can control fields using the following message formats:

### Field Control Messages
- `/field/field1/content 123` - Set content text
- `/field/field1/title "My Title"` - Set title text
- `/field/field1/x 100` - Set x position (from center)
- `/field/field1/y 100` - Set y position (from center)
- `/field/field1/width 200` - Set width
- `/field/field1/height 200` - Set height
- `/field/field1/font_size 24` - Set font size
- `/field/field1/font_color white` - Set font color
- `/field/field1/show_border 1` - Show/hide border

Fields will be created automatically if they don't exist. All positions are relative to the center of the screen.

### Python Example
```python
from pythonosc import udp_client

# Create OSC client
client = udp_client.SimpleUDPClient("127.0.0.1", 9191)

# Create and position a field
client.send_message("/field/test/title", "Test Field")
client.send_message("/field/test/content", "Hello World")
client.send_message("/field/test/x", 0)  # Center horizontally
client.send_message("/field/test/y", 0)  # Center vertically
client.send_message("/field/test/width", 200)
client.send_message("/field/test/height", 100)
