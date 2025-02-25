import time
from pythonosc.udp_client import SimpleUDPClient
from typing import Dict, Any

class OSCClient:
    """
    OSC Client for sending StageDeck information to Bitfocus Companion.
    This client sends field IDs, content, and timer information.
    """
    
    def __init__(self, ip="127.0.0.1", port=9000):
        """
        Initialize the OSC client with target IP and port.
        
        Args:
            ip (str): Target IP address (default: 127.0.0.1)
            port (int): Target OSC port (default: 9000)
        """
        self.ip = ip
        self.port = port
        self.client = SimpleUDPClient(ip, port)
        self.last_timer_update = 0
        self.update_interval = 0.1  # Limit updates to 10 per second
        
    def set_target(self, ip, port):
        """
        Update the target IP and port.
        
        Args:
            ip (str): New target IP address
            port (int): New target OSC port
        """
        self.ip = ip
        self.port = port
        self.client = SimpleUDPClient(ip, port)
        
    def send_field_update(self, field_id: str, content: str):
        """
        Send field update to Companion.
        
        Args:
            field_id (str): ID of the field being updated
            content (str): Content of the field
        """
        # Send field ID and content
        self.client.send_message(f"/stagedeck/field/{field_id}", content)
        
    def send_fields_list(self, fields: Dict[str, Any]):
        """
        Send the list of all field IDs to Companion.
        
        Args:
            fields (Dict[str, Any]): Dictionary of fields
        """
        # Send the number of fields
        self.client.send_message("/stagedeck/fields/count", len(fields))
        
        # Send each field ID
        for i, field_id in enumerate(fields.keys()):
            self.client.send_message(f"/stagedeck/fields/{i}", field_id)
            
    def send_timer_update(self, remaining_seconds: int, running: bool, warning: bool = False):
        """
        Send timer update to Companion.
        
        Args:
            remaining_seconds (int): Remaining time in seconds
            running (bool): Whether the timer is running
            warning (bool): Whether the timer is in warning state
        """
        # Limit update rate to avoid flooding
        current_time = time.time()
        if current_time - self.last_timer_update < self.update_interval:
            return
            
        self.last_timer_update = current_time
        
        # Send timer status
        self.client.send_message("/stagedeck/timer/running", 1 if running else 0)
        self.client.send_message("/stagedeck/timer/warning", 1 if warning else 0)
        self.client.send_message("/stagedeck/timer/remaining", remaining_seconds)
        
        # Send formatted time values for easier display in Companion
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        
        self.client.send_message("/stagedeck/timer/hours", hours)
        self.client.send_message("/stagedeck/timer/minutes", minutes)
        self.client.send_message("/stagedeck/timer/seconds", seconds)
        
        # Send formatted time string (HH:MM:SS)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.client.send_message("/stagedeck/timer/display", time_str)
