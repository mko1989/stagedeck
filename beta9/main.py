import sys
import json
import time
import ctypes
from pathlib import Path
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import threading
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import cv2
import asyncio
from PIL import Image
from io import BytesIO
from web_server import start_server, broadcast_frame
import winsound

class TextItem:
    def __init__(self, text="", font_family="Arial", font_size=20, font_color="white"):
        self.text = text
        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color

class Field(QWidget):
    def __init__(self, parent=None, field_id="", x=0, y=0, width=200, height=200,
                 title_text="", title_font_family="Arial", title_font_size=20, title_font_color="white",
                 content_font_family="Arial", content_font_size=20, content_font_color="white",
                 show_border=True):
        super().__init__(parent)
        
        self.field_id = field_id
        self.show_border = show_border
        
        # Create title and content
        self.title = TextItem(title_text, title_font_family, title_font_size, title_font_color)
        self.content = TextItem("", content_font_family, content_font_size, content_font_color)
        
        # Set size and position
        self.setFixedSize(width, height)
        self.move(x, y)  # Use absolute coordinates from top-left
        
        # Store position
        self._x = x
        self._y = y
        
        # Transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
    def get_x(self):
        """Get x position"""
        return self._x
        
    def get_y(self):
        """Get y position"""
        return self._y
        
    def set_position(self, x, y):
        """Set position"""
        self._x = x
        self._y = y
        self.move(x, y)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw border if enabled
        if self.show_border:
            painter.setPen(QColor("white"))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # Set up font for title
        title_font = QFont(self.title.font_family, self.title.font_size)
        painter.setFont(title_font)
        
        # Calculate title metrics
        title_metrics = painter.fontMetrics()
        
        # Draw title centered at top
        painter.setPen(QColor(self.title.font_color))
        title_y = 10  # Small padding from top
        painter.drawText(0, title_y, self.width(), title_metrics.height(), Qt.AlignCenter, self.title.text)
        
        # Set up font for content
        content_font = QFont(self.content.font_family, self.content.font_size)
        painter.setFont(content_font)
        
        # Calculate content metrics
        content_metrics = painter.fontMetrics()
        content_height = content_metrics.height()
        
        # Draw content centered in remaining space
        painter.setPen(QColor(self.content.font_color))
        content_y = title_y + title_metrics.height() + 10  # Below title with padding
        remaining_height = self.height() - content_y - 10  # Leave padding at bottom
        
        # Split content into lines and center each line
        lines = self.content.text.split('\n')
        total_lines_height = len(lines) * content_height
        current_y = content_y + (remaining_height - total_lines_height) // 2  # Vertical center
        
        for line in lines:
            painter.drawText(0, current_y, self.width(), content_height, Qt.AlignCenter, line)
            current_y += content_height

class DisplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StageDeck Beta")
        self.setGeometry(100, 100, 800, 600)
        
        # Transparency setup
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Initialize variables
        self.fields = {}
        self._background_color = QColor(0, 0, 0, 255)  # Start with opaque black
        self.ndi_frame = None
        self.original_ndi_size = None
        self.ndi_enabled = False
        self.ndi_receiver = NDIReceiver()
        
        # Border
        self.border_width = 2
        self.dragging = False
        self.offset = None
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.central_widget.setAutoFillBackground(False)
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)
        
        # Setup NDI timer
        self.ndi_timer = QTimer()
        self.ndi_timer.timeout.connect(self.update_ndi)
        self.ndi_timer.setInterval(33)  # ~30fps
        
        # Store screen info
        self.current_screen = 0
        self.normal_geometry = None
        
        # Setup web streaming
        self.web_enabled = False
        self.web_timer = QTimer()
        self.web_timer.timeout.connect(self.broadcast_frame)
        self.web_timer.setInterval(33)  # ~30fps
        
        self.update_background()

    def update_ndi(self):
        """Update NDI frame from receiver"""
        if self.ndi_enabled and self.ndi_receiver:
            frame = self.ndi_receiver.receive_frame()
            if frame is not None:
                self._update_ndi_frame(frame)
            
    def set_ndi_enabled(self, enabled):
        """Enable or disable NDI reception"""
        self.ndi_enabled = enabled
        if enabled:
            self.ndi_timer.start()
        else:
            self.ndi_timer.stop()
            self.ndi_frame = None
            self.original_ndi_size = None
        self.update()
            
    def _update_ndi_frame(self, frame):
        """Update NDI frame while preserving aspect ratio"""
        if frame is not None:
            self.ndi_frame = frame
            if self.original_ndi_size is None:
                self.original_ndi_size = (frame.width(), frame.height())
            self.update()
        
    def get_scaled_ndi_frame(self):
        """Calculate scaled NDI frame dimensions maintaining aspect ratio"""
        if self.ndi_frame is None or self.original_ndi_size is None:
            return None, (0, 0)
            
        window_width = self.width()
        window_height = self.height()
        
        # Calculate scaling factors for both dimensions
        scale_x = window_width / self.original_ndi_size[0]
        scale_y = window_height / self.original_ndi_size[1]
        
        # Use the smaller scaling factor to maintain aspect ratio
        scale = min(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(self.original_ndi_size[0] * scale)
        new_height = int(self.original_ndi_size[1] * scale)
        
        # Scale the frame
        scaled_frame = self.ndi_frame.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        return scaled_frame, (new_width, new_height)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fill background
        painter.fillRect(0, 0, self.width(), self.height(), self._background_color)
        
        # Draw NDI frame if available
        if self.ndi_frame is not None:
            scaled_frame, (width, height) = self.get_scaled_ndi_frame()
            if scaled_frame is not None:
                # Calculate position to center the frame
                x = (self.width() - width) // 2
                y = (self.height() - height) // 2
                
                # Draw the frame
                painter.drawImage(x, y, scaled_frame)
        
        # Draw border if transparent
        if self._background_color.alpha() < 255:
            painter.setPen(QColor("white"))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        # Draw fields on top
        for field in self.fields.values():
            field.update()
            
    def set_background_color(self, color):
        """Set window background color"""
        if isinstance(color, QColor):
            self._background_color = color
        elif isinstance(color, str):
            self._background_color = QColor(color)
        self.update_background()

    def update_background(self):
        """Update window background"""
        if self._background_color.alpha() < 255:
            # Enable transparency
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_NoSystemBackground, True)
            self.central_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            self.central_widget.setAutoFillBackground(False)
            self.central_widget.setStyleSheet("background: transparent;")
        else:
            # Disable transparency
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WA_NoSystemBackground, False)
            self.central_widget.setAttribute(Qt.WA_TranslucentBackground, False)
            self.central_widget.setAutoFillBackground(True)
            self.central_widget.setStyleSheet("")
            
        # Force a repaint
        self.update()
        
    def toggle_transparency(self, state):
        """Toggle window transparency"""
        if state == Qt.Checked:
            # Enable transparency
            self._background_color = QColor(0, 0, 0, 0)  # Fully transparent
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        else:
            # Disable transparency
            self._background_color = QColor(0, 0, 0, 255)  # Opaque black
            self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
            
        # Show window again since changing flags hides it
        self.show()
        self.update_background()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            new_pos = event.globalPos() - self.offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.offset = None

    def get_background_color(self):
        """Get current background color"""
        return self._background_color.name()
        
    def get_safe_geometry(self, screen):
        """Calculate a safe window geometry for the given screen"""
        screen_geo = screen.geometry()
        
        # Use 80% of screen size as maximum for windowed mode
        width = min(800, int(screen_geo.width() * 0.8))
        height = min(600, int(screen_geo.height() * 0.8))
        
        # Center the window on screen
        x = screen_geo.x() + (screen_geo.width() - width) // 2
        y = screen_geo.y() + (screen_geo.height() - height) // 2
        
        return QRect(x, y, width, height)
        
    def move_to_screen(self, screen_index):
        screens = QApplication.screens()
        if 0 <= screen_index < len(screens):
            self.current_screen = screen_index
            screen = screens[screen_index]
            
            if self.isFullScreen():
                # In fullscreen, use entire screen
                self.setGeometry(screen.geometry())
            else:
                # In windowed mode, use safe geometry
                self.setGeometry(self.get_safe_geometry(screen))
                
    def showFullScreen(self):
        screens = QApplication.screens()
        if 0 <= self.current_screen < len(screens):
            screen = screens[self.current_screen]
            # Store current geometry before going fullscreen
            if not self.isFullScreen():
                self.normal_geometry = self.geometry()
            # Set geometry to full screen
            self.setGeometry(screen.geometry())
            super().showFullScreen()
            
    def showNormal(self):
        super().showNormal()
        screens = QApplication.screens()
        if 0 <= self.current_screen < len(screens):
            screen = screens[self.current_screen]
            if self.normal_geometry and screen.geometry().contains(self.normal_geometry.center()):
                # If previous position is valid, use it
                self.setGeometry(self.normal_geometry)
            else:
                # Otherwise use safe default position
                self.setGeometry(self.get_safe_geometry(screen))
                
    def enable_ndi(self, enabled):
        if enabled:
            if not self.ndi_enabled:
                if self.ndi_receiver.initialize():
                    self.ndi_enabled = True
                    self.ndi_timer.start()
                    print("NDI initialized, searching for sources...")
                    return True
                return False
        else:
            self.ndi_enabled = False
            self.ndi_timer.stop()
            self.ndi_frame = None
            self.update()
        return True
        
    def get_ndi_sources(self):
        if self.ndi_enabled:
            return self.ndi_receiver.find_sources()
        return []
        
    def connect_to_ndi_source(self, index):
        if self.ndi_enabled:
            return self.ndi_receiver.connect_to_source(index)
        return False
        
    def add_field(self, field_id, x, y, width, height, title_text="", 
                  title_font_family="Arial", title_font_size=20, title_font_color="white",
                  content_font_family="Arial", content_font_size=20, content_font_color="white",
                  show_border=True):
        # Remove existing field if it exists
        if field_id in self.fields:
            old_field = self.fields[field_id]
            old_field.hide()
            old_field.deleteLater()
            
        # Create new field
        field = Field(self, field_id, x, y, width, height, title_text, title_font_family, title_font_size, title_font_color, content_font_family, content_font_size, content_font_color, show_border)
        self.fields[field_id] = field
        field.show()
        
        # Force a repaint to clear any artifacts
        self.update()
        
    def remove_field(self, field_id):
        if field_id in self.fields:
            self.fields[field_id].deleteLater()
            del self.fields[field_id]
            
    def update_field(self, field_id, value):
        if field_id in self.fields:
            self.fields[field_id].content.text = value
            self.fields[field_id].update()
            
    def update_background(self):
        if not self.ndi_enabled:
            self.update()
            
    def enable_web_streaming(self, enabled: bool):
        """Enable or disable web streaming"""
        self.web_enabled = enabled
        if enabled:
            self.web_timer.start()
        else:
            self.web_timer.stop()
            
    def broadcast_frame(self):
        """Capture and broadcast current window content"""
        if not self.web_enabled:
            return
            
        # Create pixmap from window
        pixmap = self.grab()
        
        # Convert to JPEG bytes
        img_buffer = QBuffer()
        img_buffer.open(QBuffer.ReadWrite)
        pixmap.save(img_buffer, "JPEG", quality=85)
        
        # Broadcast frame
        broadcast_frame(img_buffer.data().data())

class NDIlib_frame_type:
    NONE = 0
    VIDEO = 1
    AUDIO = 2
    METADATA = 3
    ERROR = 4
    STATUS_CHANGE = 100

class NDIlib_source_t(ctypes.Structure):
    _fields_ = [
        ("p_ndi_name", ctypes.c_char_p),
        ("p_url_address", ctypes.c_char_p)
    ]
    
class NDIlib_find_create_t(ctypes.Structure):
    _fields_ = [
        ("show_local_sources", ctypes.c_bool),
        ("p_groups", ctypes.c_char_p),
        ("p_extra_ips", ctypes.c_char_p)
    ]
    
class NDIlib_recv_create_v3_t(ctypes.Structure):
    _fields_ = [
        ("source_to_connect_to", NDIlib_source_t),
        ("color_format", ctypes.c_int),
        ("bandwidth", ctypes.c_int),
        ("allow_video_fields", ctypes.c_bool),
        ("p_ndi_recv_name", ctypes.c_char_p)
    ]
    
class NDIlib_video_frame_v2_t(ctypes.Structure):
    _fields_ = [
        ("xres", ctypes.c_int),
        ("yres", ctypes.c_int),
        ("FourCC", ctypes.c_int),
        ("frame_rate_N", ctypes.c_int),
        ("frame_rate_D", ctypes.c_int),
        ("picture_aspect_ratio", ctypes.c_float),
        ("frame_format_type", ctypes.c_int),
        ("timecode", ctypes.c_longlong),
        ("p_data", ctypes.c_void_p),
        ("line_stride_in_bytes", ctypes.c_int),
        ("p_metadata", ctypes.c_char_p),
        ("timestamp", ctypes.c_longlong)
    ]

class NDIReceiver:
    def __init__(self):
        self.ndi = None
        self.finder = None
        self.receiver = None
        self.video_frame = None
        self.current_source = None
        self.sources = []
        self.sources_ptr = None
        
    def initialize(self):
        # Load NDI library - try multiple possible paths
        ndi_paths = [
            Path("C:/Program Files/NDI/NDI 6 Runtime/v6/Processing.NDI.Lib.x64.dll"),
            Path("C:/Program Files/NDI/NDI 6 SDK/Lib/x64/Processing.NDI.Lib.x64.dll"),
            Path("C:/Program Files/NDI/NDI 5 Runtime/Processing.NDI.Lib.x64.dll"),
            Path("C:/Program Files/NDI/NDI 5 SDK/Lib/x64/Processing.NDI.Lib.x64.dll"),
            Path("Processing.NDI.Lib.x64.dll")
        ]
        
        for path in ndi_paths:
            try:
                print(f"Trying NDI path: {path}")
                if path.exists():
                    self.ndi = ctypes.WinDLL(str(path))
                    print(f"Found NDI DLL at: {path}")
                    print(f"Successfully loaded NDI from: {path}")
                    break
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue
                
        if not self.ndi:
            print("Failed to initialize NDI: Could not find NDI Runtime. Please make sure NDI Runtime is installed.")
            return False
            
        # Set up function signatures
        self.ndi.NDIlib_initialize.restype = ctypes.c_bool
        
        self.ndi.NDIlib_find_create_v2.argtypes = [ctypes.POINTER(NDIlib_find_create_t)]
        self.ndi.NDIlib_find_create_v2.restype = ctypes.c_void_p
        
        self.ndi.NDIlib_find_get_current_sources.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        self.ndi.NDIlib_find_get_current_sources.restype = ctypes.POINTER(NDIlib_source_t)
        
        self.ndi.NDIlib_recv_create_v3.argtypes = [ctypes.POINTER(NDIlib_recv_create_v3_t)]
        self.ndi.NDIlib_recv_create_v3.restype = ctypes.c_void_p
        
        self.ndi.NDIlib_recv_destroy.argtypes = [ctypes.c_void_p]
        self.ndi.NDIlib_recv_destroy.restype = None
        
        self.ndi.NDIlib_find_destroy.argtypes = [ctypes.c_void_p]
        self.ndi.NDIlib_find_destroy.restype = None
        
        print("Initializing NDI...")
        if not self.ndi.NDIlib_initialize():
            print("Failed to initialize NDI library")
            return False
            
        print("Creating NDI finder...")
        find_create = NDIlib_find_create_t(show_local_sources=True, p_groups=None, p_extra_ips=None)
        self.finder = self.ndi.NDIlib_find_create_v2(ctypes.byref(find_create))
        if not self.finder:
            print("Failed to create NDI finder")
            return False
            
        print("NDI initialized successfully")
        return True
        
    def find_sources(self):
        if not self.finder:
            print("Cannot find sources - NDI finder not initialized")
            return []
            
        # Wait for sources to be discovered
        time.sleep(1.0)  # Give NDI time to discover sources
        
        # Get number of sources
        num_sources = ctypes.c_uint32(0)
        self.sources_ptr = self.ndi.NDIlib_find_get_current_sources(self.finder, ctypes.byref(num_sources))
        
        if not self.sources_ptr or num_sources.value == 0:
            self.sources = []
            return []
            
        # Convert sources to Python list
        self.sources = []
        for i in range(num_sources.value):
            source = self.sources_ptr[i]
            name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else "Unknown"
            self.sources.append(name)
            
        print(f"Found {len(self.sources)} NDI sources")
        for source in self.sources:
            print(f"Found NDI source: {source}")
            
        return self.sources
        
    def connect_to_source(self, source_index):
        if source_index >= len(self.sources):
            print(f"Invalid source index: {source_index}")
            return False
            
        if not self.sources_ptr:
            print("No sources available")
            return False
            
        try:
            # Clean up existing receiver
            if self.receiver:
                self.ndi.NDIlib_recv_destroy(ctypes.c_void_p(self.receiver))
                self.receiver = None
                self.current_source = None  # Clear current source reference
                
            # Create receiver for the selected source
            source = self.sources_ptr[source_index]
            
            # Create receiver description
            recv_desc = NDIlib_recv_create_v3_t()
            recv_desc.source_to_connect_to = source
            recv_desc.color_format = 0  # BGRX_BGRA = 0
            recv_desc.bandwidth = 100  # Highest quality (100 = highest, -10 = audio only)
            recv_desc.allow_video_fields = False
            recv_desc.p_ndi_recv_name = None
            
            # Create receiver with proper error handling
            try:
                self.receiver = self.ndi.NDIlib_recv_create_v3(ctypes.byref(recv_desc))
                if not self.receiver:
                    print("Failed to create receiver")
                    return False
                    
                # Store current source index
                self.current_source = source_index
                print(f"Connected to NDI source: {self.sources[source_index]}")
                return True
                
            except Exception as e:
                print(f"Failed to create receiver: {e}")
                return False
                
        except Exception as e:
            print(f"Error connecting to source: {e}")
            return False

    def receive_frame(self):
        """Receive a frame from NDI source"""
        if not self.receiver or self.current_source is None:
            return None
            
        video_frame = NDIlib_video_frame_v2_t()
        if self.ndi.NDIlib_recv_capture_v2(ctypes.c_void_p(self.receiver), ctypes.byref(video_frame), None, None, 0) == NDIlib_frame_type.VIDEO:
            try:
                # Get frame dimensions and data
                width = video_frame.xres
                height = video_frame.yres
                buffer_size = width * height * 4  # RGBA format
                
                # Create buffer and copy frame data
                buffer = (ctypes.c_ubyte * buffer_size).from_address(video_frame.p_data)
                
                # Create QImage with correct format (NDI uses BGRA)
                image = QImage(
                    buffer,
                    width,
                    height,
                    video_frame.line_stride_in_bytes,
                    QImage.Format_ARGB32  # This will handle BGRA correctly
                )
                
                # Create a deep copy before freeing the frame
                copied_image = image.copy()
                
                # Free the frame
                self.ndi.NDIlib_recv_free_video_v2(ctypes.c_void_p(self.receiver), ctypes.byref(video_frame))
                
                return copied_image
            except Exception as e:
                print(f"Error receiving NDI frame: {e}")
                self.ndi.NDIlib_recv_free_video_v2(ctypes.c_void_p(self.receiver), ctypes.byref(video_frame))
                return None
        return None
        
    def cleanup(self):
        """Clean up NDI resources"""
        if self.receiver:
            try:
                self.ndi.NDIlib_recv_destroy(ctypes.c_void_p(self.receiver))
            except:
                pass
            self.receiver = None
            
        if self.finder:
            try:
                self.ndi.NDIlib_find_destroy(ctypes.c_void_p(self.finder))
            except:
                pass
            self.finder = None
            
        if self.ndi:
            try:
                self.ndi.NDIlib_destroy()
            except:
                pass
            self.ndi = None
            
    def __del__(self):
        self.cleanup()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StageDeck Beta")
        self.display_window = DisplayWindow()
        self.display_window.show()
        
        # Initialize variables
        self.server = None
        self.server_thread = None
        self.osc_port = 9191
        self.web_port = 8181
        
        # Initialize timer variables
        self.timer_running = False
        self.remaining_time = 0
        self.overtime = 0  # Track overtime seconds
        self.blink_state = False
        self.timer = None
        self.blink_timer = None
        
        # Initialize sound variables
        self.warning_sound_path = "sounds/warning1.wav"
        self.end_sound_path = "sounds/end1.wav"
        self.warning_sound_thread = None
        self.warning_sound_playing = False
        self._sound_lock = threading.Lock()  # Lock for thread safety
        
        # Create main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Settings tab
        settings_tab = QWidget()
        tabs.addTab(settings_tab, "Settings")
        settings_layout = QVBoxLayout(settings_tab)
        
        # Port settings
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("OSC Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(9191)
        self.port_input.valueChanged.connect(self.update_port)
        port_layout.addWidget(self.port_input)
        settings_layout.addLayout(port_layout)
        
        # Monitor selection
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("Display Monitor:"))
        self.monitor_combo = QComboBox()
        self.update_monitor_list()
        self.monitor_combo.currentIndexChanged.connect(self.update_monitor)
        monitor_layout.addWidget(self.monitor_combo)
        settings_layout.addLayout(monitor_layout)
        
        # Window controls
        window_controls = QHBoxLayout()
        
        fullscreen_button = QPushButton("Show Fullscreen")
        fullscreen_button.clicked.connect(self.display_window.showFullScreen)
        window_controls.addWidget(fullscreen_button)
        
        windowed_button = QPushButton("Show Windowed")
        windowed_button.clicked.connect(self.display_window.showNormal)
        window_controls.addWidget(windowed_button)
        
        settings_layout.addLayout(window_controls)
        
        # Background settings
        bg_group = QGroupBox("Background Settings")
        bg_layout = QVBoxLayout()
        
        # Color picker
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Background Color:"))
        self.color_button = QPushButton()
        self.color_button.clicked.connect(self.choose_background_color)
        color_layout.addWidget(self.color_button)
        bg_layout.addLayout(color_layout)
        
        # Transparency checkbox
        self.transparent_bg = QCheckBox("Transparent Background")
        self.transparent_bg.stateChanged.connect(self.toggle_transparency)
        bg_layout.addLayout(QHBoxLayout())
        bg_layout.itemAt(bg_layout.count()-1).layout().addWidget(self.transparent_bg)
        
        # NDI settings
        ndi_layout = QHBoxLayout()
        self.ndi_enabled = QCheckBox("Enable NDI")
        self.ndi_enabled.stateChanged.connect(self.update_ndi_enabled)
        ndi_layout.addWidget(self.ndi_enabled)
        
        self.ndi_source_combo = QComboBox()
        self.ndi_source_combo.currentIndexChanged.connect(self.update_ndi_source)
        ndi_layout.addWidget(self.ndi_source_combo)
        bg_layout.addLayout(ndi_layout)
        
        # Web streaming settings
        web_group = QGroupBox("Web Streaming")
        web_layout = QVBoxLayout()
        
        # Enable checkbox
        self.web_enabled = QCheckBox("Enable Web Streaming")
        self.web_enabled.stateChanged.connect(self.toggle_web_streaming)
        web_layout.addWidget(self.web_enabled)
        
        # Port settings
        web_port_layout = QHBoxLayout()
        web_port_layout.addWidget(QLabel("Web Port:"))
        self.web_port_input = QSpinBox()
        self.web_port_input.setRange(1024, 65535)
        self.web_port_input.setValue(8181)
        web_port_layout.addWidget(self.web_port_input)
        web_layout.addLayout(web_port_layout)
        
        web_group.setLayout(web_layout)
        settings_layout.addWidget(web_group)
        
        bg_group.setLayout(bg_layout)
        settings_layout.addWidget(bg_group)
        
        tabs.addTab(settings_tab, "Settings")
        
        # Fields tab
        fields_tab = QWidget()
        fields_layout = QVBoxLayout(fields_tab)
        
        # Field list and ID
        field_list_layout = QHBoxLayout()
        
        # Field ID input
        field_id_layout = QVBoxLayout()
        field_id_layout.addWidget(QLabel("Field ID:"))
        self.field_id_input = QLineEdit()
        field_id_layout.addWidget(self.field_id_input)
        field_list_layout.addLayout(field_id_layout)
        
        # Field list
        field_list_group = QGroupBox("Fields")
        field_list_inner = QVBoxLayout()
        self.fields_list = QListWidget()
        self.fields_list.currentItemChanged.connect(self.load_field)
        field_list_inner.addWidget(self.fields_list)
        field_list_group.setLayout(field_list_inner)
        field_list_layout.addWidget(field_list_group)
        
        fields_layout.addLayout(field_list_layout)
        
        # Field editor
        field_editor = QGroupBox("Field Properties")
        editor_layout = QGridLayout()
        
        # Position and size
        editor_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_input = QSpinBox()
        self.x_input.setRange(-9999, 9999)
        editor_layout.addWidget(self.x_input, 0, 1)
        
        editor_layout.addWidget(QLabel("Y:"), 0, 2)
        self.y_input = QSpinBox()
        self.y_input.setRange(-9999, 9999)
        editor_layout.addWidget(self.y_input, 0, 3)
        
        editor_layout.addWidget(QLabel("Width:"), 1, 0)
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 9999)
        self.width_input.setValue(200)  # Default width
        editor_layout.addWidget(self.width_input, 1, 1)
        
        editor_layout.addWidget(QLabel("Height:"), 1, 2)
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 9999)
        self.height_input.setValue(200)  # Default height
        editor_layout.addWidget(self.height_input, 1, 3)
        
        # Show border checkbox
        self.show_border = QCheckBox("Show Border")
        self.show_border.setChecked(True)  # Default to showing border
        editor_layout.addWidget(self.show_border, 2, 0, 1, 2)
        
        # Title settings
        editor_layout.addWidget(QLabel("Title:"), 3, 0)
        self.title_input = QLineEdit()
        editor_layout.addWidget(self.title_input, 3, 1, 1, 3)
        
        # Title font settings
        editor_layout.addWidget(QLabel("Title Font:"), 4, 0)
        self.title_font_combo = QFontComboBox()
        self.title_font_combo.setCurrentText("Arial")  # Default font
        editor_layout.addWidget(self.title_font_combo, 4, 1)
        
        self.title_size_input = QSpinBox()
        self.title_size_input.setRange(6, 72)
        self.title_size_input.setValue(20)  # Default size
        editor_layout.addWidget(self.title_size_input, 4, 2)
        
        self.title_color_button = QPushButton()
        self.title_color_button.setText("#FFFFFF")  # Default white
        self.title_color_button.clicked.connect(self.choose_title_font_color)
        editor_layout.addWidget(self.title_color_button, 4, 3)
        
        # Content font settings
        editor_layout.addWidget(QLabel("Content Font:"), 5, 0)
        self.content_font_combo = QFontComboBox()
        self.content_font_combo.setCurrentText("Arial")  # Default font
        editor_layout.addWidget(self.content_font_combo, 5, 1)
        
        self.content_size_input = QSpinBox()
        self.content_size_input.setRange(6, 72)
        self.content_size_input.setValue(20)  # Default size
        editor_layout.addWidget(self.content_size_input, 5, 2)
        
        self.content_color_button = QPushButton()
        self.content_color_button.setText("#FFFFFF")  # Default white
        self.content_color_button.clicked.connect(self.choose_content_font_color)
        editor_layout.addWidget(self.content_color_button, 5, 3)
        
        field_editor.setLayout(editor_layout)
        fields_layout.addWidget(field_editor)
        
        # Field actions
        actions_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Field")
        add_button.clicked.connect(self.add_field)
        actions_layout.addWidget(add_button)
        
        update_button = QPushButton("Update Field")
        update_button.clicked.connect(self.update_field)
        actions_layout.addWidget(update_button)
        
        delete_button = QPushButton("Delete Field")
        delete_button.clicked.connect(self.delete_field)
        actions_layout.addWidget(delete_button)
        
        fields_layout.addLayout(actions_layout)
        
        tabs.addTab(fields_tab, "Fields")
        
        # Timer tab
        timer_tab = QWidget()
        timer_layout = QVBoxLayout(timer_tab)
        
        # Timer field controls
        field_controls = QHBoxLayout()
        self.create_timer_button = QPushButton("Create Timer Field")
        self.create_timer_button.clicked.connect(self.create_timer_field)
        field_controls.addWidget(self.create_timer_button)
        
        self.remove_timer_button = QPushButton("Remove Timer Field")
        self.remove_timer_button.clicked.connect(self.remove_timer_field)
        field_controls.addWidget(self.remove_timer_button)
        
        timer_layout.addLayout(field_controls)
        
        # Timer input fields
        timer_input_layout = QHBoxLayout()
        
        # Hours input
        hours_layout = QVBoxLayout()
        hours_layout.addWidget(QLabel("Hours"))
        self.hours_input = QSpinBox()
        self.hours_input.setRange(0, 99)
        hours_layout.addWidget(self.hours_input)
        timer_input_layout.addLayout(hours_layout)
        
        # Minutes input
        minutes_layout = QVBoxLayout()
        minutes_layout.addWidget(QLabel("Minutes"))
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(0, 59)
        minutes_layout.addWidget(self.minutes_input)
        timer_input_layout.addLayout(minutes_layout)
        
        # Seconds input
        seconds_layout = QVBoxLayout()
        seconds_layout.addWidget(QLabel("Seconds"))
        self.seconds_input = QSpinBox()
        self.seconds_input.setRange(0, 59)
        seconds_layout.addWidget(self.seconds_input)
        timer_input_layout.addLayout(seconds_layout)
        
        timer_layout.addLayout(timer_input_layout)
        
        # Warning settings
        warning_group = QGroupBox("Warning Settings")
        warning_layout = QVBoxLayout()
        
        # Warning time
        warning_time_layout = QHBoxLayout()
        warning_controls_layout = QVBoxLayout()
        
        warning_checkbox_layout = QHBoxLayout()
        self.enable_warning = QCheckBox("Enable warning (turn yellow) at:")
        self.enable_warning.setChecked(True)
        warning_checkbox_layout.addWidget(self.enable_warning)
        
        self.enable_warning_sound = QCheckBox("Play sound")
        self.enable_warning_sound.setChecked(True)
        warning_checkbox_layout.addWidget(self.enable_warning_sound)
        warning_controls_layout.addLayout(warning_checkbox_layout)
        
        warning_sound_layout = QHBoxLayout()
        self.warning_sound_combo = QComboBox()
        self.warning_sound_combo.addItems(["Sound 1", "Sound 2", "Sound 3", "Custom..."])
        self.warning_sound_combo.currentTextChanged.connect(self.warning_sound_changed)
        warning_sound_layout.addWidget(self.warning_sound_combo)
        
        self.warning_sound_browse = QPushButton("Browse...")
        self.warning_sound_browse.clicked.connect(self.browse_warning_sound)
        warning_sound_layout.addWidget(self.warning_sound_browse)
        
        self.warning_sound_test = QPushButton("Test")
        self.warning_sound_test.clicked.connect(self.test_warning_sound)
        warning_sound_layout.addWidget(self.warning_sound_test)
        warning_controls_layout.addLayout(warning_sound_layout)
        
        warning_time_layout.addLayout(warning_controls_layout)
        
        self.warning_time = QSpinBox()
        self.warning_time.setRange(0, 300)
        self.warning_time.setValue(30)  # Default 30 seconds
        self.warning_time.setSuffix(" sec")
        warning_time_layout.addWidget(self.warning_time)
        warning_layout.addLayout(warning_time_layout)
        
        # End warning
        end_warning_layout = QHBoxLayout()
        end_controls_layout = QVBoxLayout()
        
        end_checkbox_layout = QHBoxLayout()
        self.enable_end_warning = QCheckBox("Enable blinking red when done")
        self.enable_end_warning.setChecked(True)
        end_checkbox_layout.addWidget(self.enable_end_warning)
        
        self.enable_end_sound = QCheckBox("Play sound")
        self.enable_end_sound.setChecked(True)
        end_checkbox_layout.addWidget(self.enable_end_sound)
        end_controls_layout.addLayout(end_checkbox_layout)
        
        end_sound_layout = QHBoxLayout()
        self.end_sound_combo = QComboBox()
        self.end_sound_combo.addItems(["Sound 1", "Sound 2", "Sound 3", "Custom..."])
        self.end_sound_combo.currentTextChanged.connect(self.end_sound_changed)
        end_sound_layout.addWidget(self.end_sound_combo)
        
        self.end_sound_browse = QPushButton("Browse...")
        self.end_sound_browse.clicked.connect(self.browse_end_sound)
        end_sound_layout.addWidget(self.end_sound_browse)
        
        self.end_sound_test = QPushButton("Test")
        self.end_sound_test.clicked.connect(self.test_end_sound)
        end_sound_layout.addWidget(self.end_sound_test)
        end_controls_layout.addLayout(end_sound_layout)
        
        end_warning_layout.addLayout(end_controls_layout)
        warning_layout.addLayout(end_warning_layout)
        
        warning_group.setLayout(warning_layout)
        timer_layout.addWidget(warning_group)
        
        # Timer presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))
        
        for minutes in [5, 10, 15, 20, 30, 45, 60]:
            button = QPushButton(f"{minutes} min")
            button.clicked.connect(lambda checked, m=minutes: self.set_timer_duration(m * 60))
            preset_layout.addWidget(button)
            
        timer_layout.addLayout(preset_layout)
        
        # Timer control buttons
        timer_controls_layout = QHBoxLayout()
        
        self.timer_start_button = QPushButton("Start")
        self.timer_start_button.clicked.connect(self.start_timer)
        timer_controls_layout.addWidget(self.timer_start_button)
        
        self.timer_pause_button = QPushButton("Pause")
        self.timer_pause_button.clicked.connect(self.pause_timer)
        timer_controls_layout.addWidget(self.timer_pause_button)
        
        self.timer_stop_button = QPushButton("Stop")
        self.timer_stop_button.clicked.connect(self.stop_timer)
        timer_controls_layout.addWidget(self.timer_stop_button)
        
        timer_layout.addLayout(timer_controls_layout)
        
        # Timer display
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setFont(QFont("Arial", 24))
        timer_layout.addWidget(self.timer_display)
        
        tabs.addTab(timer_tab, "Timer")
        
        # Load saved configuration
        self.load_config()
        
        # Setup OSC server
        self.start_osc_server()
        
        # Show main window
        self.show()
        
    def toggle_transparency(self, state):
        """Toggle window transparency"""
        if state == Qt.Checked:
            # Enable transparency
            self.display_window._background_color = QColor(0, 0, 0, 0)  # Fully transparent
            self.display_window.setWindowFlags(self.display_window.windowFlags() | Qt.FramelessWindowHint)
        else:
            # Disable transparency
            self.display_window._background_color = QColor(0, 0, 0, 255)  # Opaque black
            self.display_window.setWindowFlags(self.display_window.windowFlags() & ~Qt.FramelessWindowHint)
            
        # Show window again since changing flags hides it
        self.display_window.show()
        self.display_window.update_background()
            
    def update_ndi_enabled(self, state):
        enabled = state == Qt.Checked
        if self.display_window.enable_ndi(enabled):
            if enabled:
                # Update source list
                sources = self.display_window.get_ndi_sources()
                self.ndi_source_combo.clear()
                self.ndi_source_combo.addItems(sources)
        else:
            self.ndi_enabled.setChecked(False)
            
    def update_ndi_source(self, index):
        if index >= 0:
            self.display_window.connect_to_ndi_source(index)
            
    def update_monitor_list(self):
        self.monitor_combo.clear()
        for i, screen in enumerate(QApplication.screens()):
            geometry = screen.geometry()
            self.monitor_combo.addItem(f"Monitor {i+1} ({geometry.width()}x{geometry.height()} at {geometry.x()},{geometry.y()})")
            
    def update_monitor(self, index):
        self.display_window.move_to_screen(index)
        self.save_config()
        
    def update_port(self, new_port):
        """Update OSC server port"""
        if new_port != self.osc_port:
            self.osc_port = new_port
            self.start_osc_server()
            
    def start_osc_server(self):
        """Start the OSC server with proper cleanup and error handling"""
        try:
            # Clean up existing server if any
            self.cleanup_osc_server()
            
            # Create dispatcher and register handlers
            dispatcher = Dispatcher()
            dispatcher.map("/field/*", self.handle_osc_message)
            
            # Create and start new server
            self.server = BlockingOSCUDPServer(("0.0.0.0", self.osc_port), dispatcher)
            print(f"OSC Server listening on port {self.osc_port}")
            
            # Start server in a thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 10048:  # Port already in use
                print(f"Error: OSC port {self.osc_port} is already in use. Please close any other applications using this port.")
                # Try next available port
                self.osc_port += 1
                self.port_input.setValue(self.osc_port)
                self.start_osc_server()  # Retry with new port
            else:
                print(f"Error starting OSC server: {e}")
        except Exception as e:
            print(f"Error starting OSC server: {e}")
            
    def cleanup_osc_server(self):
        """Clean up OSC server resources"""
        if hasattr(self, 'server') and self.server:
            self.server.shutdown()
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join()
            self.server = None
            self.server_thread = None
            
    def handle_osc_message(self, address, *args):
        """Handle incoming OSC messages"""
        try:
            # Split address into parts
            parts = address.split('/')
            if len(parts) < 3:  # Need at least /field/field_id
                return
                
            field_id = parts[2]  # Get field ID from /field/field_id
            
            # Get or create field
            field = self.display_window.fields.get(field_id)
            if not field:
                # Create field on main thread
                if QThread.currentThread() != QApplication.instance().thread():
                    # Schedule field creation on main thread
                    QMetaObject.invokeMethod(self, "_create_field_from_osc",
                                          Qt.ConnectionType.BlockingQueuedConnection,
                                          Q_ARG(str, field_id))
                    field = self.display_window.fields.get(field_id)
                    if not field:
                        return
                else:
                    self._create_field_from_osc(field_id)
                    field = self.display_window.fields.get(field_id)
                    if not field:
                        return
                
            # Handle different message types based on address
            if len(parts) > 3:
                property_name = parts[3]
                if len(args) > 0:
                    value = args[0]
                    
                    if property_name == "content":
                        field.content.text = str(value)
                    elif property_name == "title":
                        field.title.text = str(value)
                    elif property_name == "x":
                        field.move(int(value), field.y())
                    elif property_name == "y":
                        field.move(field.x(), int(value))
                    elif property_name == "width":
                        field.resize(int(value), field.height())
                    elif property_name == "height":
                        field.resize(field.width(), int(value))
                    elif property_name == "font_size":
                        field.content.font_size = int(value)
                        field.title.font_size = int(value)
                    elif property_name == "font_color":
                        field.content.font_color = str(value)
                        field.title.font_color = str(value)
                    elif property_name == "show_border":
                        field.show_border = bool(value)
                    
                    field.update()
                    self.display_window.update()
            
        except Exception as e:
            print(f"Error handling OSC message: {e}")
            
    @pyqtSlot(str)
    def _create_field_from_osc(self, field_id):
        """Create a new field from OSC message on the main thread"""
        try:
            field = self.display_window.add_field(
                field_id,
                x=200, y=10,  # Default position
                width=300, height=200,  # Default size
                title_text=field_id,
                title_font_family="Arial",
                title_font_size=24,
                title_font_color="white",
                content_font_family="Arial",
                content_font_size=32,
                content_font_color="white",
                show_border=True
            )
            self.fields_list.addItem(field_id)
            self.save_config()  # Save the new field configuration
        except Exception as e:
            print(f"Error creating field from OSC: {e}")
            
    def choose_background_color(self):
        color = QColorDialog.getColor(QColor(self.display_window._background_color))
        if color.isValid():
            self.display_window.set_background_color(color.name())
            self.save_config()
            
    def choose_title_font_color(self):
        color = QColorDialog.getColor(QColor(self.title_color_button.text()))
        if color.isValid():
            self.title_color_button.setText(color.name())
            
    def choose_content_font_color(self):
        color = QColorDialog.getColor(QColor(self.content_color_button.text()))
        if color.isValid():
            self.content_color_button.setText(color.name())
            
    def load_field(self, current, previous):
        if not current:
            return
            
        field_id = current.text()
        if field_id not in self.display_window.fields:
            return
            
        field = self.display_window.fields[field_id]
        self.field_id_input.setText(field_id)
        self.x_input.setValue(field.get_x())
        self.y_input.setValue(field.get_y())
        self.width_input.setValue(field.width())
        self.height_input.setValue(field.height())
        self.show_border.setChecked(field.show_border)
        self.title_input.setText(field.title.text)
        self.title_font_combo.setCurrentText(field.title.font_family)
        self.title_size_input.setValue(field.title.font_size)
        self.title_color_button.setText(field.title.font_color)
        self.content_font_combo.setCurrentText(field.content.font_family)
        self.content_size_input.setValue(field.content.font_size)
        self.content_color_button.setText(field.content.font_color)
        
    def add_field(self):
        field_id = self.field_id_input.text()
        if not field_id:
            return
            
        self.display_window.add_field(
            field_id,
            self.x_input.value(),
            self.y_input.value(),
            self.width_input.value(),
            self.height_input.value(),
            self.title_input.text(),
            self.title_font_combo.currentText(),
            self.title_size_input.value(),
            self.title_color_button.text(),
            self.content_font_combo.currentText(),
            self.content_size_input.value(),
            self.content_color_button.text(),
            self.show_border.isChecked()
        )
        
        # Update field list
        if self.fields_list.findItems(field_id, Qt.MatchExactly):
            return
        self.fields_list.addItem(field_id)
        self.save_config()
        
    def update_field(self):
        current = self.fields_list.currentItem()
        if not current:
            return
            
        field_id = current.text()
        self.display_window.add_field(
            field_id,
            self.x_input.value(),
            self.y_input.value(),
            self.width_input.value(),
            self.height_input.value(),
            self.title_input.text(),
            self.title_font_combo.currentText(),
            self.title_size_input.value(),
            self.title_color_button.text(),
            self.content_font_combo.currentText(),
            self.content_size_input.value(),
            self.content_color_button.text(),
            self.show_border.isChecked()
        )
        self.save_config()
        
    def delete_field(self):
        current = self.fields_list.currentItem()
        if not current:
            return
            
        field_id = current.text()
        self.display_window.remove_field(field_id)
        self.fields_list.takeItem(self.fields_list.row(current))
        self.save_config()
        
    def closeEvent(self, event):
        """Handle application shutdown"""
        # Clean up OSC server
        self.cleanup_osc_server()
        
        # Clean up NDI
        if self.display_window.ndi_receiver:
            self.display_window.ndi_receiver.cleanup()
            
        # Save fields
        self.save_config()
        
        # Close display window
        self.display_window.close()
        
        event.accept()
        
    def log_message(self, message):
        """Log a message - now just prints to console"""
        print(f"[Companion Viewer] {message}")
        
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                
            # Load background color
            if 'background_color' in config:
                self.display_window.set_background_color(config['background_color'])
                
            # Load fields
            if 'fields' in config:
                for field_id, field_data in config['fields'].items():
                    self.display_window.add_field(
                        field_id,
                        field_data['x'],
                        field_data['y'],
                        field_data['width'],
                        field_data['height'],
                        field_data.get('title_text', ''),
                        field_data.get('title_font_family', 'Arial'),
                        field_data.get('title_font_size', 20),
                        field_data.get('title_font_color', 'white'),
                        field_data.get('content_font_family', 'Arial'),
                        field_data.get('content_font_size', 20),
                        field_data.get('content_font_color', 'white'),
                        field_data.get('show_border', True)
                    )
                    # Add to field list
                    self.fields_list.addItem(field_id)
                    
        except FileNotFoundError:
            pass
            
    def save_config(self):
        config = {
            'background_color': self.display_window._background_color.name(),
            'fields': {}
        }
        
        # Save fields
        for field_id, field in self.display_window.fields.items():
            config['fields'][field_id] = {
                'x': field.get_x(),
                'y': field.get_y(),
                'width': field.width(),
                'height': field.height(),
                'title_text': field.title.text,
                'title_font_family': field.title.font_family,
                'title_font_size': field.title.font_size,
                'title_font_color': field.title.font_color,
                'content_font_family': field.content.font_family,
                'content_font_size': field.content.font_size,
                'content_font_color': field.content.font_color,
                'show_border': field.show_border
            }
            
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
    def add_field_to_list(self, field_id, field):
        """Add field to the fields list widget"""
        # Add to fields list widget if not already there
        if not self.fields_list.findItems(field_id, Qt.MatchExactly):
            item = QListWidgetItem(field_id)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.fields_list.addItem(item)
            self.fields_list.setCurrentItem(item)
        
    def remove_field_from_list(self, field_id):
        """Remove field from the fields list widget"""
        # Find and remove from fields list widget
        items = self.fields_list.findItems(field_id, Qt.MatchExactly)
        for item in items:
            self.fields_list.takeItem(self.fields_list.row(item))
            
        # Update selection
        if self.fields_list.count() > 0:
            self.fields_list.setCurrentRow(0)
            
    def create_timer_field(self):
        """Create timer field if it doesn't exist"""
        if "timer" not in self.display_window.fields:
            # Stop any running timer before creating new field
            if self.timer_running:
                self.stop_timer()
                
            # Create the field
            field = self.display_window.add_field(
                "timer",
                x=200, y=10,  # Position near top
                width=300, height=200,  # Larger default size
                title_text="Timer",
                title_font_size=24,
                content_font_size=32
            )
            
            # Add to fields list
            self.add_field_to_list("timer", field)
            
            # Update the field with current time
            self.update_timer_display()
            
            # Update button states
            self.create_timer_button.setEnabled(False)
            self.remove_timer_button.setEnabled(True)
            
    def remove_timer_field(self):
        """Remove timer field if it exists"""
        if "timer" in self.display_window.fields:
            # Stop any running timer before removing field
            if self.timer_running:
                self.stop_timer()
                
            # Remove the field
            self.display_window.remove_field("timer")
            
            # Remove from fields list
            self.remove_field_from_list("timer")
            
            # Update button states
            self.create_timer_button.setEnabled(True)
            self.remove_timer_button.setEnabled(False)
            
    def update_button_states(self):
        """Update timer field button states based on field existence"""
        has_timer = "timer" in self.display_window.fields
        self.create_timer_button.setEnabled(not has_timer)
        self.remove_timer_button.setEnabled(has_timer)
        
    def start_timer(self):
        """Start/stop timer"""
        if not self.timer_running:
            # Calculate total seconds
            total_seconds = (self.hours_input.value() * 3600 + 
                           self.minutes_input.value() * 60 + 
                           self.seconds_input.value())
            
            if total_seconds <= 0:
                return
                
            self.remaining_time = total_seconds
            self.overtime = 0  # Reset overtime
            self.timer_running = True
            self.timer_start_button.setText("Stop")
            
            # Create and start main timer
            if not self.timer:
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)  # Update every second
            
            # Create blink timer if needed
            if not self.blink_timer:
                self.blink_timer = QTimer()
                self.blink_timer.timeout.connect(self.blink_timer_text)
            
            # Reset any previous styling
            if "timer" in self.display_window.fields:
                self.update_timer_field_color("white")
        else:
            self.stop_timer()
            
    def stop_timer(self):
        """Stop the timer"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
        if self.blink_timer and self.blink_timer.isActive():
            self.blink_timer.stop()
            
        self.timer_running = False
        self.timer_start_button.setText("Start")
        
        # Reset timer to input values
        total_seconds = (self.hours_input.value() * 3600 + 
                        self.minutes_input.value() * 60 + 
                        self.seconds_input.value())
        self.remaining_time = total_seconds
        self.overtime = 0  # Reset overtime
        
        # Reset display color
        self.update_timer_field_color("white")
        self.update_timer_display()
        
        # Stop any playing sounds
        self.stop_warning_sound()
        winsound.PlaySound(None, winsound.SND_PURGE)  # Stop any playing sounds
        
    def pause_timer(self):
        """Pause the timer"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
            self.timer_running = False
            self.timer_start_button.setText("Start")
            
    def update_timer(self):
        """Update timer countdown"""
        if not self.timer_running:
            return
            
        if self.remaining_time > 0:
            # Stop warning sound early at 3 seconds
            if self.remaining_time == 3:
                self.stop_warning_sound()
                
            self.remaining_time -= 1
            
            # Change color and play warning sound when warning time is reached
            if self.enable_warning.isChecked() and self.remaining_time <= self.warning_time.value() and self.remaining_time > 1:
                self.update_timer_field_color("yellow")
                if self.enable_warning_sound.isChecked() and not self.warning_sound_playing:
                    self.warning_sound_playing = True
                    self.warning_sound_thread = threading.Thread(target=self.play_warning_sound)
                    self.warning_sound_thread.daemon = True
                    self.warning_sound_thread.start()
                    
            self.update_timer_display()
                
            # Handle timer completion
            if self.remaining_time == 0:
                # Start blinking if enabled
                if self.enable_end_warning.isChecked():
                    self.blink_timer.start(500)  # Blink every 0.5 seconds
                    
                    # Play end sound if enabled
                    if self.enable_end_sound.isChecked():
                        threading.Thread(target=self.play_end_sound, daemon=True).start()
        else:
            # In overtime
            self.overtime += 1
            self.update_timer_display()
            
    def blink_timer_text(self):
        """Blink timer text when time is up"""
        if not self.enable_end_warning.isChecked():
            if self.blink_timer and self.blink_timer.isActive():
                self.blink_timer.stop()
            self.update_timer_field_color("white")
            return
            
        self.blink_state = not self.blink_state
        self.update_timer_field_color("red" if self.blink_state else "black")
        
    def update_timer_display(self):
        """Update timer display"""
        if not hasattr(self, 'remaining_time'):
            self.remaining_time = 0
            
        if self.remaining_time > 0:
            # Normal countdown
            hours = self.remaining_time // 3600
            minutes = (self.remaining_time % 3600) // 60
            seconds = self.remaining_time % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            # Overtime display with plus sign
            hours = self.overtime // 3600
            minutes = (self.overtime % 3600) // 60
            seconds = self.overtime % 60
            time_str = f"+{hours:02d}:{minutes:02d}:{seconds:02d}"
            
        self.timer_display.setText(time_str)
        self.update_timer_field_text(time_str)
        
    def set_timer_duration(self, duration):
        """Set timer duration in seconds"""
        self.stop_timer()  # Stop any running timer
        self.remaining_time = duration
        
        # Update input fields
        self.hours_input.setValue(duration // 3600)
        self.minutes_input.setValue((duration % 3600) // 60)
        self.seconds_input.setValue(duration % 60)
        
        self.update_timer_display()
        
    def update_timer_field_color(self, color):
        """Update timer field color if it exists"""
        if "timer" in self.display_window.fields:
            self.display_window.fields['timer'].content.font_color = color
            self.display_window.fields['timer'].update()
            
    def update_timer_field_text(self, text):
        """Update timer field text if it exists"""
        if "timer" in self.display_window.fields:
            self.display_window.fields['timer'].content.text = text
            self.display_window.fields['timer'].update()
            
    def toggle_web_streaming(self, state):
        """Toggle web streaming"""
        enabled = state == Qt.Checked
        if enabled:
            # Start web server in separate thread
            def run_server():
                # Create and set event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Start server
                start_server(port=self.web_port_input.value())
                
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
        # Enable streaming in display window
        self.display_window.enable_web_streaming(enabled)

    def warning_sound_changed(self, text):
        """Handle warning sound selection change"""
        if text == "Custom...":
            self.browse_warning_sound()
        else:
            sound_num = int(text.split()[-1])
            self.warning_sound_path = f"sounds/warning{sound_num}.wav"
            
    def end_sound_changed(self, text):
        """Handle end sound selection change"""
        if text == "Custom...":
            self.browse_end_sound()
        else:
            sound_num = int(text.split()[-1])
            self.end_sound_path = f"sounds/end{sound_num}.wav"

    def play_warning_sound(self):
        """Play warning sound in a loop"""
        try:
            # Play sound with loop flag - will continue until explicitly stopped
            winsound.PlaySound(self.warning_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            # Wait until we need to stop
            while self.warning_sound_playing and self.timer_running:
                time.sleep(0.1)
        finally:
            self.warning_sound_playing = False
            winsound.PlaySound(None, winsound.SND_PURGE)
            
    def play_end_sound(self):
        """Play end sound once"""
        try:
            # First ensure warning sound is stopped
            winsound.PlaySound(None, winsound.SND_PURGE)
            time.sleep(0.1)  # Small delay to ensure warning sound is stopped
            # Play end sound
            winsound.PlaySound(self.end_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            pass
            
    def stop_warning_sound(self):
        """Stop warning sound"""
        self.warning_sound_playing = False
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except:
            pass
            
    def test_warning_sound(self):
        """Test warning sound"""
        try:
            winsound.PlaySound(self.warning_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except:
            QMessageBox.warning(self, "Sound Error", "Could not play warning sound file.")
            
    def test_end_sound(self):
        """Test end sound"""
        try:
            winsound.PlaySound(self.end_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except:
            QMessageBox.warning(self, "Sound Error", "Could not play end sound file.")
            
    def browse_warning_sound(self):
        """Browse for custom warning sound"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Warning Sound", "",
            "Sound Files (*.wav *.mp3);;All Files (*.*)"
        )
        if file_name:
            self.warning_sound_path = file_name
            self.warning_sound_combo.setCurrentText("Custom...")
            
    def browse_end_sound(self):
        """Browse for custom end sound"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select End Sound", "",
            "Sound Files (*.wav *.mp3);;All Files (*.*)"
        )
        if file_name:
            self.end_sound_path = file_name
            self.end_sound_combo.setCurrentText("Custom...")
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
