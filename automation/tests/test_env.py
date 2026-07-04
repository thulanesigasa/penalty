import os
import sys
import unittest
# Add parent directory of tests to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from rl.env import PenaltyEnv

class TestPenaltyEnv(unittest.TestCase):
    def setUp(self):
        # Initialize in simulated mode (no browser controller passed)
        self.env = PenaltyEnv(controller=None, stake=1.0)

    def test_initial_state(self):
        obs, info = self.env.reset()
        # State: 12 spots + 1 multiplier = 13 elements
        self.assertEqual(len(obs), 13)
        # All spots should be 0 (unhit) initially
        self.assertTrue(np.all(obs[:12] == 0.0))
        # Initial multiplier should be 1.0
        self.assertEqual(obs[12], 1.0)
        self.assertEqual(info["hit_count"], 0)
        self.assertEqual(info["multiplier"], 1.0)

    def test_valid_step(self):
        self.env.reset()
        # Choose action 4
        obs, reward, terminated, truncated, info = self.env.step(4)
        
        # Grid status at index 4 should be 1.0 (hit)
        self.assertEqual(obs[4], 1.0)
        self.assertFalse(info["invalid"])
        
        # In simulation mode, step results in either a WIN or LOSS
        if info["outcome"] == "WIN":
            self.assertEqual(obs[12], 1.15)  # first step multiplier
            self.assertTrue(reward > 0)
            self.assertFalse(terminated)
        else:
            self.assertEqual(info["outcome"], "LOSS")
            self.assertEqual(reward, -1.0)  # lost stake
            self.assertTrue(terminated)

    def test_invalid_step(self):
        self.env.reset()
        # Trigger same target twice
        # First shot
        obs1, reward1, terminated1, truncated1, info1 = self.env.step(2)
        if terminated1:
            # If goalie saved it, reset and hit index 2 once
            obs1, info1 = self.env.reset()
            # Force target 2 to be hit to test invalid step
            self.env.grid_status[2] = 1.0
            
        # Second shot on the same index 2
        obs2, reward2, terminated2, truncated2, info2 = self.env.step(2)
        
        self.assertTrue(info2["invalid"])
        self.assertEqual(reward2, -2.0)  # invalid action penalty
        self.assertFalse(terminated2)

if __name__ == "__main__":
    unittest.main()
