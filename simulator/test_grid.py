import unittest
from unittest.mock import patch, MagicMock
from grid import Grid, GridEvent
from meter import Meter

class TestGridLifecycle(unittest.TestCase):
    """Testing function _manage_event_lifecycle"""

    def setUp(self):
        """Set up a fresh grid and a dummy event catalog for each test."""
        # Create a single mock event to make assertions deterministic
        self.mock_event = GridEvent(name="Wind Surge", affected_location="Orkney", load_delta=-150.0)
        
        # Instantiate Grid with empty meters for now, since we are only testing events
        self.grid = Grid(meters=[], live_frequency=50.0, system_inertia_factor=0.2)
        self.grid.possible_events = [self.mock_event]
        self.grid.active_event = None
        self.grid.event_duration = 0

    @patch('grid.random.randint')
    @patch('grid.random.choice')
    def test_no_event_currently_trigger_event_with_high_roll(self, mock_choice, mock_randint):
        mock_randint.side_effect = [95, 10] # force a roll of 95 to trigger a new event, and a roll of 10 for 10 second event duration
        mock_choice.return_value = self.mock_event # force random to choose our pre-defined mock event

        self.grid._manage_event_lifecycle()

        self.assertEqual(self.mock_event, self.grid.active_event)
        self.assertEqual(self.grid.event_duration, 10)

    def test_existing_event_countdown_decrements(self):
        #set up an active event with duration 5 seconds
        self.grid.active_event = self.mock_event
        self.grid.event_duration = 5

        self.grid._manage_event_lifecycle()

        self.assertEqual(self.mock_event, self.grid.active_event)
        self.assertEqual(self.grid.event_duration, 4)
    
    def test_existing_event_ends(self):
        #set up an active event with duration 1 seconds
        self.grid.active_event = self.mock_event
        self.grid.event_duration = 1

        self.grid._manage_event_lifecycle()

        self.assertEqual(None, self.grid.active_event)
        self.assertEqual(self.grid.event_duration, 0)

class TestGridLoadMaths(unittest.TestCase):
    """Testing function _calculate_grid_load"""

    def setUp(self):
        """Set up a fresh grid for testing."""
        self.grid = Grid(meters=[], live_frequency=50.0, system_inertia_factor=0.2)

    def test_calculate_grid_load_sums_correctly(self):
        # use MagicMock to generate two independent fake meters for unit testing
        mock_meter_1 = MagicMock()
        mock_meter_1.active_load = 1200.0
        mock_meter_1.base_load = 1000.0

        mock_meter_2 = MagicMock()
        mock_meter_2.active_load = 900.0
        mock_meter_2.base_load = 1000.0

        # assign our fake meters to the grid
        self.grid.meters = [mock_meter_1, mock_meter_2]

        total_active_load, total_base_load = self.grid._calculate_grid_load()

        self.assertEqual(total_active_load, 2100.0)
        self.assertEqual(total_base_load, 2000.0)

class TestGridFrequencyInertia(unittest.TestCase):
    """Testing function _apply_frequency_inertia"""

    def setUp(self):
        """Set up a fresh grid for testing."""
        self.grid = Grid(meters=[], live_frequency=50.0, system_inertia_factor=0.2)

    def test_apply_frequency_inertia(self):
        # mock total loads
        total_active_load = 2100.0 
        total_base_load = 2000.0

        self.grid._apply_frequency_inertia(total_active_load, total_base_load)

        self.assertEqual(self.grid.live_frequency, 49.99)


