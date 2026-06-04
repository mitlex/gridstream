# ======== IMPORTS =========

import json 
import datetime 
from simulator.grid import Grid

# ======== SERVER ORCHESTRATION CONTEXT =========
# Note: This file is executed externally by the Uvicorn web server via the terminal.
# Uvicorn acts as the primary process host, translating raw network bytes into standardised Asynchronous Server Gateway Interface (ASGI) 
# packets and feeding them directly to the FastAPI application routing structures defined below.
# FastAPI is the primary orchestrator of code within this file, orchestrating lifespan phases, triggering the grid physics engine, and directing network paths straight to decorated functions.
# ===============================================

# Modern, high-performance web framework used across Python to build network routing paths and APIs.
# Acts as the system orchestrator that translates incoming web traffic into structured Python events.
# In this program:
#   FastAPI: Application framework that reads ASGI network packets from Uvicorn and routes them to specific functions based on the path at the end of the web address 
#       (e.g., routing 'ws://127.0.0.1:8000/ws' straight to the websocket_endpoint function)
#   WebSocket: A FastAPI object that packages ASGI network data into a clean Python structure we can interact with
#   WebSocketDisconnect: An error type used to catch when a user closes their browser tab or drops connection cleanly
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Python's built-in asynchronous framework used to manage single-threaded concurrent operations.
# Handles cooperative multitasking by pausing tasks during slow I/O operations (like network waits or timers)
# to ensure the CPU remains free to execute other pending tasks.
# In this program:
# Whilst grid_telemetry_loop is paused, enables:
    # Uvicorn to continue:
    #   -listening for new client connections
    #   -streaming data to clients
    #   -listening for client disconnects
    # FastAPI to continue:
    #   -routing new clients to the websocket_endpoint function
    #   -continue serving the dashboard to the one or more client browsers
import asyncio

# Standard engine used across Python to build secure, asynchronous resource management tools.
# Guarantees that system assets (like network pipes, files, or tasks) are safely initialized,
# and automatically cleans them up or shuts them down even if the underlying program crashes.
# In this program: 
# Used to split the lifespan function into a startup and shutdown phase, which FastAPI requires, 
# so that FastAPI can safely launch the physics engine at boot and guarantee cleanup code runs if the server stops.
from contextlib import asynccontextmanager

# Standard FastAPI utility component used to transmit physical files across network protocols.
# Converts file content bytes on the host hard drive into formatted HTTP transmission strings.
# In this program:
# Used inside the serve_dashboard endpoint to intercept standard web browser lookups 
# and automatically push our local 'index.html' dashboard layout file across the network link.
from fastapi.responses import FileResponse

# ======== CODE =========

grid = Grid.create_with_discovered_meters(live_frequency=50.0, system_inertia_factor=0.2) # initialize the grid

# Global variable that contains the latest packet of grid data
# Every client connection will read from this variable, meaning that multiple browsers (clients) will see the same data
latest_packet = None

async def grid_telemetry_loop(): # async def is required to enable the await keyword, which enables the asyncio.sleep to work
    """Runs the grid simulation loop continuously in the background.

    Advances the network physics state every second, builds a unified data 
    packet containing both global metrics and individual substation metrics, 
    and saves the result onto the shared clipboard for connected browsers to read.
    """
    global latest_packet
    tick_count = 1
    
    while True:
        grid.tick()
        
        current_timestamp = datetime.datetime.now().isoformat()
        
        # Construct master packet dictionary
        master_packet = {
            "telemetry_frame": tick_count,
            "grid_global": grid.to_dict(current_timestamp),
            "substations": [
                meter.to_dict(grid.live_frequency, current_timestamp)
                for meter in grid.meters
            ]
        }
        
        # Convert to JSON string and save it to the shared clipboard
        latest_packet = json.dumps(master_packet)
        
        # Increment telemtry frame count and use non-blocking pause
        tick_count += 1
        await asyncio.sleep(1)

@asynccontextmanager # Used in this case to split the lifespan function into a two-phase routine using the 'yield' keyword
async def lifespan(_app: FastAPI): # FastAPI insists on this argument but we don't use it anywhere hence _
    """Manages the server startup and shutdown phases.

    Automatically starts up the background physics simulation loop the moment 
    the server boots, and handles any clean-up messages when the user terminates Uvicorn.
    """
    # FastAPI executes this on startup
    # Asynchronously creating this task means that FastAPI will move to the next line (print) (avoiding the grid_telemetry_loop infinite loop)
    asyncio.create_task(grid_telemetry_loop())
    print("GridStream Physics Engine Heartbeat Started...")
    yield # Pause lifespan - FastAPI tells Uvicorn it can open the doors for web traffic, and FastAPI can begin directing that traffic to websocket_endpoint if the URL ends with /ws
    print("GridStream Server Shutting Down...") # FastAPI executes this when we terminate Uvicorn

# Takes connection requests from Uvicorn and routes them to the websocket_endpoint function if the URL ends with /ws
# Note: The 'lifespan' parameter handles server startup and shutdown, and it only accepts a function wrapped in @asynccontextmanager.
# This decorator is mandatory because it provides the structural safety net (2-phases, with a yield) FastAPI uses to execute cleanup code even if the server crashes.
# FastAPI parks itself at yield and in the event of a crash the structure allows FastAPI to move past the yield line and execute the cleanup code even though the application crashed.
# In our case the cleanup code is just a print statement but in a production application there would be real cleanup processes occurring here.
grid_api = FastAPI(lifespan=lifespan)

@grid_api.get("/")
async def serve_dashboard():
    """Serves the static grid telemetry user interface (dashboard) to the client browser directly from the server root.
    
    When a user hits enter on http://localhost:8000 in their browser address bar it sends a GET request to our server.
    If the user doesn't specify a page (e.g. http://localhost:8000/about.html), it defaults to a GET / request,
    i.e. the browser requests the root ("/") of the site by default.
    FastAPI sees this GET / and matches it to our decorator, and reads "index.html" from disk and streams it back to the client browser.

    Unifies frontend delivery and the live WebSocket pipeline onto a single channel (8000) 
    to ensure a zero-configuration, single-command launch experience.
    """
    # Extracts 'index.html' from disk and injects a 'Content-Type: text/html' header 
    # so the browser renders the file visually as a dashboard.
    return FileResponse("index.html")

@grid_api.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Establishes a live connection to stream telemetry data to a browser.

    Accepts the incoming connection request and reads the latest packet from 
    the shared clipboard every second, broadcasting it out to the browser 
    until the user closes their dashboard tab.
    """
    
    # Accept browser handshake 
    #   await pauses until the network connects and the handshake is accepted - connecting over a network takes a moment; it needs time
    #   this line will not be bypassed until the handshake is accepted
    await websocket.accept()
    
    try: 
        while True:
            if latest_packet is not None:
                await websocket.send_text(latest_packet) # again, await until send_text returns before moving to next line
                
            # Wait 1 second before checking the clipboard for a new update - prevents CPU overload
            await asyncio.sleep(1)

    except WebSocketDisconnect: # Catch the network drop gracefully when a user closes their browser tab
        print("Client disconnected from telemetry stream.")
