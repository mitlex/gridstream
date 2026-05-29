class GridEvent:
    """A blueprint for physical and operational disruptions on the electrical network.

    Defines a specific localized or system-wide (global) anomaly that instantly shifts 
    consumer demand (load), triggering an eventual frequency and voltage reaction.

    Attributes:
        name (str): The identifier of the disruption (e.g., "TV Pickup").
        affected_location (str): The target scope, either matching a specific 
            substation location or marked as "GLOBAL".
        load_delta (float): The net change in power demand measured in 
            Kilowatts (kW). Positive values indicate consumption spikes; 
            negative values indicate surges in generation or sudden shedding.
    """
    def __init__(self, name, affected_location, load_delta):
        self.name = name
        self.affected_location = affected_location
        self.load_delta = load_delta