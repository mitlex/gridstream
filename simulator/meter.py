import datetime
import time
import json
import random

def get_meter_data_JSON(meter_id, location, timestamp, status, frequency_hz, voltage_v, load_kw):
    """Generates a JSON object representing meter data.

    Builds a Python dictionary of meter data and converts it to a JSON object.

    Args:
        meter_id: (integer) identifier for the meter 
        location: (string) meter location
        timestamp: (string) time of reading
        status: (string) operational/inoperational meter
        frequency_hz: (float) frequency registered by meter
        voltage_v: (float) voltage registed by meter
        load_kw: (float) wattage registered by meter

    Returns:
        JSON object
    """
    dict = {
        "meter_id": meter_id,
        "timestamp": timestamp,
        "status": f'{status}',
        "readings": {
            "frequency_hz": frequency_hz,
            "voltage_v": voltage_v,
            "load_kw": load_kw
            },
        "metadata": {
            "location": f'{location}'
        }
    }

    return json.dumps(dict, sort_keys=False, indent=4)

# CONSTANTS

# initial state
TARGET_FREQ_HZ = 50.0 
TARGET_VOLTAGE_V = 230.4
BASE_LOAD_KW = 1000.0 

# Inertia (snap-back strength)
FREQ_INERTIA = 0.1
VOLT_INERTIA = 0.05
LOAD_INERTIA = 0.02

# Jitter ("noise" range)
FREQ_JITTER_RANGE = 0.005
VOLT_JITTER_RANGE = 0.5
LOAD_JITTER_RANGE = 10.0

# STATE CHANGES
current_freq = TARGET_FREQ_HZ
current_voltage = TARGET_VOLTAGE_V
current_load = BASE_LOAD_KW

# meter metadata
meter_id = 1
location = "Glasgow"
status = "Operational"

# begin readings
while True:

    # add jitter to represent minute grid fluctuations
    freq_jitter = random.uniform(-FREQ_JITTER_RANGE, FREQ_JITTER_RANGE) #random.uniform gives us a float between two input values
    voltage_jitter = random.uniform(-VOLT_JITTER_RANGE, VOLT_JITTER_RANGE)
    load_jitter = random.uniform(-LOAD_JITTER_RANGE, LOAD_JITTER_RANGE)

    # apply jitters
    current_freq += freq_jitter
    current_voltage += voltage_jitter
    current_load += load_jitter

    # simulate grid inertia to pull freq, volt, load back to base values (and avoid infinite random number drift)
    current_freq += (50.0 - current_freq) * FREQ_INERTIA
    current_voltage += (230.0 - current_voltage) * VOLT_INERTIA
    current_load += (1000.0 - current_load) * LOAD_INERTIA
    
    date_time_iso = datetime.datetime.now().isoformat()
    
    print(get_meter_data_JSON(meter_id, location, date_time_iso, status, round(current_freq, 3), round(current_voltage, 2), round(current_load, 1)))
    
    time.sleep(7) #pause for 1 second before next reading













    