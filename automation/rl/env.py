import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional, Tuple, Dict, Any

class PenaltyEnv(gym.Env):
    """
    Gymnasium environment representing the 12-target Penalty game.
    Can run in either 'simulation' mode (for offline training) or
    'browser' mode (attaching to the Playwright controller).
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, controller: Optional[Any] = None, stake: float = 1.0):
        super().__init__()
        self.controller = controller
        self.stake = stake
        
        # Action space: 12 spots (0 to 11)
        self.action_space = spaces.Discrete(12)
        
        # State space: 12 elements (grid status: 0=active, 1=hit) + 1 element (current multiplier)
        # We represent this as a Box of size 13
        self.observation_space = spaces.Box(
            low=0.0,
            high=50.0,
            shape=(13,),
            dtype=np.float32
        )
        
        # Safe/Dangerous probabilities for simulation mode
        # Non-uniform to allow RL to learn target preferences
        self.save_rates = [
            0.15, 0.22, 0.12, 0.18,  # Row 1
            0.10, 0.25, 0.14, 0.20,  # Row 2
            0.11, 0.23, 0.13, 0.19   # Row 3
        ]
        
        # Multipliers based on number of successful shots
        self.multipliers = [1.0, 1.15, 1.35, 1.60, 1.95, 2.45, 3.15, 4.15, 5.65, 8.15, 12.50, 21.00, 45.00]
        
        self.reset()

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        
        self.grid_status = np.zeros(12, dtype=np.float32)
        self.hit_count = 0
        self.current_mult = 1.0
        
        if self.controller:
            # Let the browser controller reset the game (e.g. click cashout or new game)
            self.controller.reset_game()
            self._update_state_from_browser()
        
        obs = self._get_obs()
        info = {"hit_count": self.hit_count, "multiplier": self.current_mult}
        return obs, info

    def _get_obs(self) -> np.ndarray:
        return np.append(self.grid_status, [self.current_mult]).astype(np.float32)

    def _update_state_from_browser(self):
        if self.controller:
            state = self.controller.get_state()
            self.grid_status = np.array(state["grid"], dtype=np.float32)
            self.hit_count = sum(state["grid"])
            self.current_mult = state["multiplier"]

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        # Invalid action check (hitting already targeted cell)
        if self.grid_status[action] == 1.0:
            reward = -2.0  # Heavy penalty for selecting already-hit cells
            obs = self._get_obs()
            return obs, reward, False, False, {"invalid": True, "payout": 0.0, "outcome": "INVALID"}

        if self.controller:
            # Executing action through browser
            success, payout, outcome = self.controller.click_target(action)
            self._update_state_from_browser()
            
            terminated = not success or self.hit_count == 12
            # Reward: payout increase or loss of stake
            if not success:
                reward = -self.stake
            else:
                reward = self.stake * (self.multipliers[self.hit_count] - self.multipliers[self.hit_count - 1])
                
            info = {
                "invalid": False,
                "payout": payout,
                "outcome": outcome,
                "hit_count": self.hit_count,
                "multiplier": self.current_mult
            }
            return self._get_obs(), reward, terminated, False, info
            
        else:
            # Simulation Mode
            save_prob = self.save_rates[action]
            is_saved = np.random.rand() < save_prob
            
            if is_saved:
                # Goalie saved the ball -> Lose round
                self.grid_status[action] = 1.0  # visual update
                reward = -self.stake
                terminated = True
                outcome = "LOSS"
                payout = 0.0
            else:
                # Goal scored!
                self.grid_status[action] = 1.0
                self.hit_count += 1
                new_mult = self.multipliers[self.hit_count]
                reward = self.stake * (new_mult - self.current_mult)
                self.current_mult = new_mult
                terminated = (self.hit_count == 12)
                outcome = "WIN"
                payout = self.stake * self.current_mult
                
            obs = self._get_obs()
            info = {
                "invalid": False,
                "payout": payout,
                "outcome": outcome,
                "hit_count": self.hit_count,
                "multiplier": self.current_mult
            }
            return obs, reward, terminated, False, info
