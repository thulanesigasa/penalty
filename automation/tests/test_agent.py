import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from rl.agent import DQNAgent

class TestDQNAgent(unittest.TestCase):
    def test_agent_action(self):
        agent = DQNAgent(state_dim=13, action_dim=12)
        state = np.zeros(13, dtype=np.float32)
        action = agent.act(state, epsilon=0.0)  # Greedy action selection
        self.assertTrue(0 <= action < 12)
        
        # Test Q-values dimension matches action space
        q_values = agent.get_q_values(state)
        self.assertEqual(len(q_values), 12)

    def test_replay_buffer(self):
        agent = DQNAgent(state_dim=13, action_dim=12, batch_size=4)
        state = np.zeros(13, dtype=np.float32)
        next_state = np.zeros(13, dtype=np.float32)
        next_state[4] = 1.0 # spot 4 hit
        
        # Add samples to buffer
        for i in range(10):
            agent.buffer.push(state, 4, 0.15, next_state, False)
            
        self.assertEqual(len(agent.buffer), 10)
        
        # Test network parameter update (learning)
        loss = agent.learn()
        self.assertTrue(isinstance(loss, float))

if __name__ == "__main__":
    unittest.main()
