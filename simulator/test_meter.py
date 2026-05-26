import unittest
import json
from meter import Meter

class TestMeterPhysics(unittest.TestCase):

    def test_voltage_recovery_mechanism(self):
        """Ensure voltage moves toward the target when resting far away."""
        # 1. Setup a meter under extreme voltage conditions
        test_meter = Meter(
            id=1, 
            location="TestBay", 
            live_voltage=250.0,  # Surge state
            active_load=1000.0, 
            target_voltage=230.0, 
            base_load=1000.0,
            voltage_stability_factor=0.1
        )
        
        # 2. Execute jitter with ZERO random noise to isolate stability math
        test_meter.jitter(voltage_jitter_range=0.0, load_jitter_range=0.0)
        
        # 3. Assert that the recovery math successfully reduced the voltage surge
        self.assertLess(test_meter.live_voltage, 250.0)

    def test_load_recovery_mechanism(self):
        """Ensure load moves toward the base load when resting far away."""
        # 1. Setup a meter under extreme load conditions
        test_meter = Meter(
            id=1, 
            location="TestBay", 
            live_voltage=230.0,  
            active_load=2000.0, # Surge state
            target_voltage=230.0, 
            base_load=1000.0,
            load_stability_factor=0.04
        )
        
        # 2. Execute jitter with ZERO random noise to isolate stability math
        test_meter.jitter(voltage_jitter_range=0.0, load_jitter_range=0.0)
        
        # 3. Assert that the recovery math successfully reduced the load surge
        self.assertLess(test_meter.active_load, 2000.0)

    def test_voltage_and_load_jitter_bounds(self):
        """Verify that the random noise generated stays within the specified jitter ranges before stability adjustments."""
        # 1. Setup meter perfectly balanced at baseline targets
        test_meter = Meter(
            id=1, 
            location="TestBay", 
            live_voltage=230.0,  
            active_load=1000.0, 
            target_voltage=230.0, 
            base_load=1000.0
        )
        
        # 2. Define strict testing ranges
        v_range = 0.5
        l_range = 10.0
        
        # 3. Execute a single tick
        test_meter.jitter(voltage_jitter_range=v_range, load_jitter_range=l_range)
        
        # 4. Combined assertions for Voltage Bounds
        self.assertGreaterEqual(test_meter.live_voltage, 230.0 - v_range)
        self.assertLessEqual(test_meter.live_voltage, 230.0 + v_range)
        
        # 5. Combined assertions for Load Bounds
        self.assertGreaterEqual(test_meter.active_load, 1000.0 - l_range)
        self.assertLessEqual(test_meter.active_load, 1000.0 + l_range)

    def test_voltage_and_load_zero_jitter_static(self):
        """Verify that the live voltage and active load remain at baseline values with zero jitter"""
        # 1. Setup meter perfectly balanced at baseline targets
        test_meter = Meter(
            id=1, 
            location="TestBay", 
            live_voltage=230.0,  
            active_load=1000.0, 
            target_voltage=230.0, 
            base_load=1000.0
        )
        
        # 2. Execute jitter with ZERO random noise to isolate stability math
        test_meter.jitter(voltage_jitter_range=0.0, load_jitter_range=0.0)
        
        # 3. Combined assertions for Voltage and Load
        self.assertEqual(test_meter.live_voltage, test_meter.target_voltage)
        self.assertEqual(test_meter.active_load, test_meter.base_load)

    def test_to_json_serialization_and_structure(self):
        """Verify that to_json returns a valid JSON string with correct keys."""
        # 1. Setup a standard meter
        test_meter = Meter(
            id=1, 
            location="London", 
            live_voltage=230.0,  
            active_load=1000.0, 
            target_voltage=230.0, 
            base_load=1000.0
        )
        
        # 2. Define dummy environmental inputs
        test_timestamp = "2026-05-25T12:00:00"
        test_freq = 50.05
        
        # 3. Call the method to get the JSON string
        json_string = test_meter.to_json(grid_frequency=test_freq, timestamp=test_timestamp)
        
        # 4. Parse the JSON string back into a Python dictionary
        data = json.loads(json_string)
        
        # 5. Assertions on structure and values
        self.assertEqual(data["meter_id"], 1)
        self.assertEqual(data["timestamp"], test_timestamp)
        self.assertEqual(data["metadata"]["location"], "London")
        self.assertEqual(data["readings"]["grid_frequency_hz"], test_freq)

if __name__ == '__main__':
    unittest.main()