import time
import datetime
import random
from meter import Meter
from grid_event import GridEvent

class Grid():
    """An environmental orchestrator managing a synchronized electrical network.

    Maintains the global network frequency by aggregating local sub-station load data 
    and simulating the mechanical inertia of large spinning turbines. Manages random 
    system-wide and localized disruption events over a discrete timeline.

    Attributes:
        meters (list[Meter]): Collection of connected local sub-station smart meters.
        live_frequency (float): Present actual operating frequency of the grid in Hz.
        system_inertia_factor (float): The rate of resistance to sudden changes, 
            simulating structural mechanical turbine momentum.
        target_frequency (float): Ideal network frequency standard (typically 50.0 Hz).
        load_sensitivity (float): Scaling factor dictating how much the system equilibrium 
            shifts per Kilowatt (kW) of load deviation.
        active_event (GridEvent or None): The disruption model currently impacting the grid.
        event_duration (int): Remaining simulation cycles (seconds) for the active event.
        possible_events (list[GridEvent]): Pre-instantiated catalog of possible disruptions.
    """
    def __init__(self, meters, live_frequency, system_inertia_factor, target_frequency=50.0, load_sensitivity=0.0005):
        self.meters = meters
        self.live_frequency = live_frequency
        self.system_inertia_factor = system_inertia_factor
        self.target_frequency = target_frequency
        self.load_sensitivity = load_sensitivity
        
        self.active_event = None
        self.event_duration = 0

        self.possible_events = [
            GridEvent(name="Local Wind Farm Surge", affected_location="Orkney", load_delta=-150.0), # Net load decreases because local wind turbines inject excess power into the substation lines.
            GridEvent(name="Industrial Park Shift Change", affected_location="Manchester", load_delta=-300.0), # Net load decreases because heavy industrial machinery is powered down as workers swap shifts.
            GridEvent(name="District Water Pump Failure", affected_location="Argyll", load_delta=-400.0), # Net load decreases because a massive water utility pump loses electrical power and stops drawing current.
            GridEvent(name="Local Biomass Generator Trip", affected_location="Aberdeenshire", load_delta=240.0), # Net load increases because the sudden loss of local power generation forces the grid to supply the deficit.
            GridEvent(name="Subdivision EV Charging Rush", affected_location="London", load_delta=180.0), # Net load increases as multiple residential electric vehicles plug in simultaneously after commuting.
            
            # Global/System-wide Events (Rippled across all local meters evenly)
            GridEvent(name="Major Football Match Half-Time", affected_location="GLOBAL", load_delta=250.0), # Net load increases system-wide as many kettles, appliances, and lights are switched on at once.
            GridEvent(name="Regional Solar Eclipse", affected_location="GLOBAL", load_delta=350.0), # Net load increases because losing rooftop solar generation forces properties to draw power from the grid instead.
            GridEvent(name="Late Night Baseline Drop", affected_location="GLOBAL", load_delta=-500.0) # Net load decreases significantly as businesses close down and consumers go to sleep for the night.
        ]

    def tick(self):
        """Advances the global grid simulation by a single discrete step.

        Orchestrates the execution sequence for the current cycle: processes
        ongoing or new network events, prompts connected meters to update local
        metrics, factors in active localized or systemic shocks, aggregates 
        total network demand, and computes the resulting global frequency.
        """
        self._manage_event_lifecycle() # handle event triggers and countdowns

        for meter in self.meters: # allow meters to update metrics
            meter.jitter()
            if self.active_event is not None and (self.active_event.affected_location == meter.location or self.active_event.affected_location == "GLOBAL"):
                meter.active_load += self.active_event.load_delta

        total_active_load, total_base_load = self._calculate_grid_load() # calculate grid totals

        self._apply_frequency_inertia(total_active_load, total_base_load) # account for grid inertia

    def _manage_event_lifecycle(self):
        """Manages random event activation and ongoing structural countdown timers.

        If no event is active, handles a probability roll to introduce a random shock 
        from the event catalog. If an event is ongoing, decrements its remaining lifetime 
        and safely returns the grid back to normal operations once elapsed.
        """
        if self.active_event == None:
            event = random.choice(self.possible_events)
            roll = random.randint(0, 100)
            if roll >= 90:
                self.active_event = event
                self.event_duration = random.randint(5, 20)
        else:
            self.event_duration -= 1
            if self.event_duration == 0:
                self.active_event = None

    def _calculate_grid_load(self):
        """Aggregates all baseline and active power metrics across connected sub-stations.

        Loops through the internal collection of meters to compile total active demand 
        and compare it to expected standard baseline requirements.

        Returns:
            tuple[float, float]: Total real-time active load (kW) and total planned 
                base load (kW) across the entire grid environment.
        """
        total_active_load = 0.0
        total_base_load = 0.0
        for meter in self.meters:
            total_active_load += meter.active_load
            total_base_load += meter.base_load
        return total_active_load, total_base_load

    def _apply_frequency_inertia(self, total_active_load, total_base_load):
        """Executes physical turbine momentum calculations to alter global grid frequency.

        Measures supply stress based on aggregate load deviations, shifts the target 
        equilibrium frequency, and applies a dampening inertia formula to simulate physical 
        generator response lag.

        Args:
            total_active_load (float): Sum of all concurrent active load readings across meters (kW).
            total_base_load (float): Sum of all structural baseline load goals across meters (kW).
        """
        grid_load_delta = total_active_load - total_base_load
        target_equilibrium_frequency = self.target_frequency - (grid_load_delta * self.load_sensitivity)
        self.live_frequency += (target_equilibrium_frequency - self.live_frequency) * self.system_inertia_factor


