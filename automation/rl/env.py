import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional, Tuple, Dict, Any

class PenaltyEnv(gym.Env):
    """
    Asynchronous environment wrapper for the 12-target Penalty game.
    Provides standard observations and rewards for DQN training.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, controller: Optional[Any] = None, stake: float = 1.0):
        super().__init__()
        self.controller = controller
        self.stake = stake
        
        # Action space: 12 spots (0 to 11) representing shootout targets
        self.action_space = spaces.Discrete(12)
        
        # State space: 12 elements (grid status: 0=active, 1=hit) + 1 element (current multiplier)
        self.observation_space = spaces.Box(
            low=0.0,
            high=50.0,
            shape=(13,),
            dtype=np.float32
        )
        
        # Simulated goalie save rates per target (non-uniform for RL preference training)
        self.save_rates = [
            0.15, 0.22, 0.12, 0.18,  # Row 1
            0.10, 0.25, 0.14, 0.20,  # Row 2
            0.11, 0.23, 0.13, 0.19   # Row 3
        ]
        
        # Multipliers based on number of successful shots
        self.multipliers = [1.0, 1.15, 1.35, 1.60, 1.95, 2.45, 3.15, 4.15, 5.65, 8.15, 12.50, 21.00, 45.00]
        
        # Initialize default state attributes directly (calling self.reset() in init returns coroutine)
        self.grid_status = np.zeros(12, dtype=np.float32)
        self.hit_count = 0
        self.current_mult = 1.0

    async def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Asynchronously resets the Penalty game round.
        """
        super().reset(seed=seed)
        
        self.grid_status = np.zeros(12, dtype=np.float32)
        self.hit_count = 0
        self.current_mult = 1.0
        
        if self.controller:
            # Command the browser controller to reset/cashout the game
            await self.controller.reset_game()
            await self._update_state_from_browser()
        
        obs = self._get_obs()
        info = {"hit_count": self.hit_count, "multiplier": self.current_mult}
        return obs, info

    def _get_obs(self) -> np.ndarray:
        return np.append(self.grid_status, [self.current_mult]).astype(np.float32)

    async def _update_state_from_browser(self):
        """
        Updates local observation arrays by querying the active browser DOM.
        """
        if self.controller:
            state = await self.controller.get_state()
            self.grid_status = np.array(state["grid"], dtype=np.float32)
            self.hit_count = sum(state["grid"])
            self.current_mult = state["multiplier"]

    async def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Executes a shootout shot.
        Enforces a reward structure of +1.0 for a score/win, and -1.0 for a save/loss.
        """
        # Heavy penalty reward if we attempt to click an already targeted cell
        if self.grid_status[action] == 1.0:
            reward = -2.0
            obs = self._get_obs()
            return obs, reward, False, False, {"invalid": True, "payout": 0.0, "outcome": "INVALID"}

        if self.controller:
            # Click browser elements asynchronously
            success, payout, outcome = await self.controller.click_target(action)
            await self._update_state_from_browser()
            
            terminated = not success or self.hit_count == 12
            
            # +1.0 for a score/win, -1.0 for a save/loss
            if not success:
                reward = -1.0
            else:
                reward = 1.0
                
            info = {
                "invalid": False,
                "payout": payout,
                "outcome": outcome,
                "hit_count": self.hit_count,
                "multiplier": self.current_mult
            }
            return self._get_obs(), reward, terminated, False, info
            
        else:
            # Simulated environment fallback logic
            save_prob = self.save_rates[action]
            is_saved = np.random.rand() < save_prob
            
            if is_saved:
                self.grid_status[action] = 1.0
                reward = -1.0
                terminated = True
                outcome = "LOSS"
                payout = 0.0
            else:
                self.grid_status[action] = 1.0
                self.hit_count += 1
                new_mult = self.multipliers[self.hit_count]
                
                # +1.0 for a score/win, -1.0 for a save/loss
                reward = 1.0
                
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
