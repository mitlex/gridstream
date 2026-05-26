import time
import datetime
import json
from simulator.grid import Grid

def run_simulation_smoke_test():
    print("🚀 Initializing GridStream Telemetry Hub Smoke Test...")
    
    # Initialize your grid using your factory constructor
    grid = Grid.create_with_discovered_meters(live_frequency=50.0, system_inertia_factor=0.2)
    
    print(f"📡 Connected to {len(grid.meters)} auto-discovered sub-stations.")
    print("Press Ctrl+C to stop the stream.\n")
    time.sleep(2)  # Give the engineer a moment to read the boot logs

    try:
        tick_count = 1
        while True:
            # 1. Advance the physics engine by 1 simulated second
            grid.tick()
            
            # 2. Capture a single synchronized timestamp for this step
            current_timestamp = datetime.datetime.now().isoformat()
            
            # 3. Parse our JSON strings back into temporary objects to build a master frame
            master_packet = {
                "telemetry_frame": tick_count,
                "grid_global": json.loads(grid.to_json(current_timestamp)),
                "substations": [
                    json.loads(meter.to_json(grid.live_frequency, current_timestamp)) 
                    for meter in grid.meters
                ]
            }
            
            # 4. Print the unified master payload to the terminal screen
            print(json.dumps(master_packet, indent=2))
            print("\n" + "="*60 + "\n")
            
            tick_count += 1
            time.sleep(1)  # Space out ticks by 1 real-world second
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation terminated by engineer. Pipeline offline.")

if __name__ == "__main__":
    run_simulation_smoke_test()