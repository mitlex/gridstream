import json
import random

class Meter():
    """A simulated smart meter measuring local electrical metrics.

    Tracks and simulates high-frequency variations in local substation voltage 
    and power demand (load), returning to baseline targets via local stability 
    mechanisms.

    Attributes:
        id (int): Unique identifier for the meter.
        location (str): Geographical location of the substation.
        live_voltage (float): Present voltage reading in Volts (V).
        active_load (float): Present power consumption in Kilowatts (kW).
        target_voltage (float): Substation baseline voltage target.
        base_load (float): Expected average power consumption baseline.
        voltage_stability_factor (float): Strength of voltage regulation.
        load_stability_factor (float): Rate at which demand relaxes to baseline.
        status (str): Represents meter health (e.g. operational, fault).
    """

    def __init__(self, id, location, live_voltage, active_load, target_voltage, base_load, voltage_stability_factor=0.05, load_stability_factor=0.02, status="operational"):
        self.id = id
        self.location = location
        self.live_voltage = live_voltage
        self.active_load = active_load
        self.target_voltage = target_voltage
        self.base_load = base_load
        self.voltage_stability_factor = voltage_stability_factor
        self.load_stability_factor = load_stability_factor
        self.status = status

    def jitter(self, voltage_jitter_range=0.5, load_jitter_range=10.0):
        """Simulates minute local fluctuations and applies recovery stability.

        Generates random noise within the specified ranges for voltage and load,
        applies it to the live values, and then pulls them back toward their
        respective baseline targets using the meter's stability factors.

        Args:
            voltage_jitter_range (float): Maximum absolute bounds for random 
                voltage noise. Defaults to 0.5.
            load_jitter_range (float): Maximum absolute bounds for random 
                load noise. Defaults to 10.0.
        """

        voltage_jitter = random.uniform(-voltage_jitter_range, voltage_jitter_range)
        load_jitter = random.uniform(-load_jitter_range, load_jitter_range)

        # apply jitters
        self.live_voltage += voltage_jitter
        self.active_load += load_jitter

        # simulate grid inertia to pull volt and load back to target/base values (and avoid infinite random number drift)
        self.live_voltage  += (self.target_voltage - self.live_voltage ) * self.voltage_stability_factor
        self.active_load += (self.base_load - self.active_load) * self.load_stability_factor

    def to_json(self, grid_frequency, timestamp):
        """Generates a JSON string of the meter's telemetry data.

        Args:
            grid_frequency (float): The current global grid frequency in Hz.
            timestamp (str): The synchronized system ISO timestamp.

        Returns:
            str: A formatted JSON string containing readings and metadata.
        """

        telemetry_data = {
            "meter_id": self.id,
            "timestamp": timestamp,
            "status": self.status,
            "readings": {
                "grid_frequency_hz": grid_frequency,
                "voltage_v": round(self.live_voltage, 2),
                "load_kw": round(self.active_load, 1)
                },
            "metadata": {
                "location": self.location
            }
        }

        return json.dumps(telemetry_data, sort_keys=False, indent=4)