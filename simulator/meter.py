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
            Higher value causes the live voltage to move towards the current target voltage faster every grid tick;
            Lower value does the opposite. 
        load_stability_factor (float): Rate at which demand relaxes to baseline.
            Higher value causes the active load to move towards the current target load faster every grid tick;
            Lower value does the opposite. 
        load_to_voltage_coupling_factor (float): Scales how heavily 
            load deltas (due to events) impact the substation target equilibrium voltage.
            Higher value causes a greater shift in the current target equilibrium voltage during grid disruptions; 
            lower value does the opposite.
        status (str): Represents meter health (e.g. operational, fault).
    """

    def __init__(self, id, location, live_voltage, active_load, target_voltage, base_load, voltage_stability_factor=0.05, load_stability_factor=0.08, load_to_voltage_coupling_factor=0.01, status="operational"):
        self.id = id
        self.location = location
        self.live_voltage = live_voltage
        self.active_load = active_load
        self.target_voltage = target_voltage
        self.base_load = base_load
        self.voltage_stability_factor = voltage_stability_factor
        self.load_stability_factor = load_stability_factor
        self.load_to_voltage_coupling_factor = load_to_voltage_coupling_factor
        self.status = status

    def jitter(self, event_delta=0.0, voltage_jitter_range=0.5, load_jitter_range=10.0):
        """Simulates minute local fluctuations and applies recovery stability.

        Generates random noise within the specified ranges for voltage and load, 
        factors in operational offsets caused by active grid events, and pulls 
        the metrics toward a dynamic equilibrium target using the meter's 
        stability factors to prevent random walk drift.

        Args:
            event_delta (float): Active system disruption load offset in 
                Kilowatts (kW). Defaults to 0.0.
            voltage_jitter_range (float): Maximum absolute bounds for random 
                voltage noise. Defaults to 0.5.
            load_jitter_range (float): Maximum absolute bounds for random 
                load noise. Defaults to 10.0.
        """

        voltage_jitter = random.uniform(-voltage_jitter_range, voltage_jitter_range)
        load_jitter = random.uniform(-load_jitter_range, load_jitter_range)

        # Apply jitters
        self.live_voltage += voltage_jitter
        self.active_load += load_jitter

        # Set the target center points for load and voltage based on current grid event.
        target_load_equilibrium = self.base_load + event_delta
        target_voltage_equilibrium = self.target_voltage - (event_delta * self.load_to_voltage_coupling_factor)

        # Smoothly pull the live voltage and load values toward their target_voltage/load_equilbirium values on every grid tick.
        # The mathematics here act like a rubber band, slowing down changes and preventing random 
        # numbers from drifting away into unrealistic figures.
        # the stability factors limit how quickly we approach target values from our current live voltage/active load
        self.live_voltage  += (target_voltage_equilibrium - self.live_voltage) * self.voltage_stability_factor 
        self.active_load += (target_load_equilibrium - self.active_load) * self.load_stability_factor

    def to_dict(self, grid_frequency, timestamp):
        """Generates a dictionary of the meter's telemetry data.

        Args:
            grid_frequency (float): The current global grid frequency in Hz.
            timestamp (str): The synchronized system ISO timestamp.

        Returns:
            dict: A dictionary containing readings and metadata.
        """

        return {
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