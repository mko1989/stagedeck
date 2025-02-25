from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import json
from typing import Optional, Dict
from queue import Queue
import threading

app = FastAPI()

# Store active connections
connections: Dict[int, WebSocket] = {}
connection_counter = 0

# Queue for new frames
frame_queue = Queue(maxsize=1)  # Only keep latest frame

# HTML template for the viewer page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Companion Viewer</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
        }
        #display {
            max-width: 100%;
            max-height: 100vh;
            object-fit: contain;
        }
    </style>
</head>
<body>
    <img id="display" src="">
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const display = document.getElementById('display');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.frame) {
                display.src = 'data:image/jpeg;base64,' + data.frame;
            }
        };
        
        ws.onclose = function() {
            console.log('Connection closed, attempting to reconnect...');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global connection_counter
    await websocket.accept()
    
    # Assign unique ID to this connection
    connection_id = connection_counter
    connection_counter += 1
    connections[connection_id] = websocket
    
    try:
        while True:
            # Keep connection alive and wait for frames
            await asyncio.sleep(0.016)  # ~60fps max
    except:
        pass
    finally:
        del connections[connection_id]

def broadcast_frame(image_data: bytes):
    """Broadcast frame to all connected clients"""
    if not connections:
        return
        
    # Convert to base64
    frame_b64 = base64.b64encode(image_data).decode('utf-8')
    data = json.dumps({"frame": frame_b64})
    
    # Put in queue for broadcasting
    try:
        frame_queue.put_nowait(data)
    except:
        # Queue full, skip frame
        pass

async def broadcast_worker():
    """Worker to broadcast frames from queue"""
    while True:
        try:
            if not frame_queue.empty():
                data = frame_queue.get_nowait()
                # Broadcast to all connections
                for conn_id, websocket in list(connections.items()):
                    try:
                        await websocket.send_text(data)
                    except:
                        # Connection probably closed
                        try:
                            del connections[conn_id]
                        except:
                            pass
        except:
            pass
        await asyncio.sleep(0.016)  # ~60fps max

def start_server(host: str = "0.0.0.0", port: int = 8181):
    """Start the FastAPI server"""
    import uvicorn
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Start broadcast worker on server startup
        task = asyncio.create_task(broadcast_worker())
        yield
        # Cancel broadcast worker on server shutdown
        task.cancel()
        
    app.router.lifespan_context = lifespan
    
    # Run server
    uvicorn.run(app, host=host, port=port)
