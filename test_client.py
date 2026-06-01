import asyncio
import websockets

async def listen_to_server():
    # Connect directly to local FastAPI endpoint URL
    url = "ws://localhost:8000/ws"
    
    async with websockets.connect(url) as websocket:
        print(f"Connected to data pipe at: {url}")
        
        # Continuously capture incoming messages
        while True:
            message = await websocket.recv()
            print(f"Server says: {message}")

# Trigger the asynchronous main logic loop
asyncio.run(listen_to_server())