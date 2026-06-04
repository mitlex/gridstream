import unittest
from unittest.mock import patch, MagicMock
from grid import Grid, GridEvent

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

    # Decorators process bottom-up; @patch acts as a factory that creates a MagicMock for each target.
    # Python injects these created MagicMock objects into the parameters from left to right.
    # These fakes intercept and temporarily replace the real 'random' functions inside the 'grid' module.
    @patch('grid.random.randint')
    @patch('grid.random.choice')
    def test_no_event_currently_trigger_event_with_high_roll(self, mock_choice, mock_randint):
        # side_effect yields values sequentially for the two separate randint() calls
        # therefore force a roll of 95 to trigger a new event, and a roll of 10 for 10 second event duration
        mock_randint.side_effect = [95, 10] 
        
        # return_value forces choice() to always return our specific mock event
        mock_choice.return_value = self.mock_event 

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
        # Note that we do this so that we don't need to create real meter objects in this test
        # By instead using MagicMock objects, we isolate the testing to this Grid class method
        # Therefore if the test fails, we know that it's not a problem with the meter class
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

class TestGridFactoryConstructor(unittest.TestCase):
    """Testing the alternative constructor create_with_discovered_meters."""

    # @patch enters grid.py and temporarily swaps out the real 'Meter' class constructor with a fake MagicMock factory object.
    # This means we isolate the test to the grid class; we won't use the meter class constructor at all
    # MagicMock will also record the arguments that would have been passed to the meter constructor, 
    # allowing us to assert that the final meter_id matches 100 + # number of locations (e.g. if we have 5 locations, the last meter_id should be 105)
    @patch('grid.Meter')
    def test_factory_creates_unique_meters_ignoring_global(self, mock_meter_class):
        # Python automatically injects the fake MagicMock factory into our 'mock_meter_class' parameter.
        # Every time the loop inside create_with_discovered_meters() tries to build a meter,
        # it calls this mock instead of the Meter class; the mock records the exact arguments used in its history log (meter id, location, etc.).

        # Note on Mock Behavior: Because this mock is 'blind', it doesn't actually know the Meter constructor 
        # parameters or build physical Meter objects. It simply returns a MagicMock instance 
        # on each iteration to fill the grid's meter list, which acts as a data log recording the exact arguments used.

        # If we printed the populated grid.meter list at this point, it would look like a collection of generic fakes:
        #   grid_instance.meters = [
        #       <MagicMock name='Meter()' id='140224164...' call_args=call(id=101, location='Orkney', live_voltage=230.0, active_load=1000.0, target_voltage=230.0, base_load=1000.0)>,
        #       <MagicMock name='Meter()' id='140224168...' call_args=call(id=102, location='Manchester', live_voltage=230.0, active_load=1000.0, target_voltage=230.0, base_load=1000.0)>,
        #       ... ]
        grid_instance = Grid.create_with_discovered_meters(live_frequency=50.0, system_inertia_factor=0.2)
        self.assertIsInstance(grid_instance, Grid)

        # check that the number of meters matches the number of unique locations
        locations = []
        for event in grid_instance.possible_events:
            if event.affected_location != "GLOBAL" and event.affected_location not in locations:
                locations.append(event.affected_location)
        self.assertEqual(len(grid_instance.meters), len(locations))
        
        # assert_any_call scans the MagicMock factory object call log (which should contain X number of entries (1 per meter) with our expected meter attributes)
        # to guarantee at least one entry matches our expected final ID (i.e. 105 if we had 5 meters) and baseline metrics.

        expected_final_id = 100 + len(locations)
        mock_meter_class.assert_any_call(
            id=expected_final_id,
            location=unittest.mock.ANY,  # location can be anything - unittest.mock.any accepts any text here
            live_voltage=230.0,
            active_load=1000.0,
            target_voltage=230.0,
            base_load=1000.0
        )

class TestGridDictionary(unittest.TestCase):
    """Testing the grid's to_dict method."""    

    def test_to_dict(self):
        """Verify that to_dict returns a valid dictionary with correct keys."""
        grid_instance = Grid.create_with_discovered_meters(live_frequency=50.0, system_inertia_factor=0.2)

        test_timestamp = "2026-05-25T12:00:00"
        data = grid_instance.to_dict(timestamp=test_timestamp)
        
        self.assertEqual(data["timestamp"], test_timestamp)
        self.assertEqual(data["metrics"]["live_frequency_hz"], round(grid_instance.live_frequency, 3))
        self.assertEqual(data["metrics"]["target_frequency_hz"], grid_instance.target_frequency)
        self.assertEqual(data["metrics"]["active_meters_count"], len(grid_instance.meters))

        expected_event_name = grid_instance.active_event.name if grid_instance.active_event else None
        expected_event_location = grid_instance.active_event.affected_location if grid_instance.active_event else None
        self.assertEqual(data["system_status"]["active_event"], expected_event_name)
        self.assertEqual(data["system_status"]["active_event_location"], expected_event_location)
        self.assertEqual(data["system_status"]["event_duration_remaining_s"], grid_instance.event_duration)



