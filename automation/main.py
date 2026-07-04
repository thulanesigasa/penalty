import os
import json
import time
import asyncio
import numpy as np
from dotenv import load_dotenv
import websockets

from rl.env import PenaltyEnv
from rl.agent import DQNAgent
from browser.controller import BrowserController

# Load environment configs
load_dotenv()

BACKEND_WS_URL = os.getenv("BACKEND_WS_URL", "ws://localhost:8000/ws/bot")
CHROME_DEBUG_WS = os.getenv("CHROME_DEBUG_WS", "http://localhost:9222")

class AutomationOrchestrator:
    def __init__(self):
        self.is_running = False
        self.bet_amount = 1.0
        self.delay_speed = 1.0 # delay between actions in seconds
        
        # Initialize browser controller and RL environment
        self.controller = BrowserController(CHROME_DEBUG_WS)
        self.env = PenaltyEnv(controller=self.controller, stake=self.bet_amount)
        self.agent = DQNAgent(state_dim=13, action_dim=12)
        
        # Training hyperparams
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.9995  # decayed over iterations
        
        # Statistics
        self.iteration = 0
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0

    async def connect_and_loop(self):
        print(f"Connecting to Backend WebSocket at: {BACKEND_WS_URL}")
        retry_delay = 2
        while True:
            try:
                async with websockets.connect(BACKEND_WS_URL) as ws:
                    print("Connected to API Bridge successfully!")
                    
                    # Spawn listener for backend commands (START/STOP/SET_SPEED)
                    listen_task = asyncio.create_task(self.listen_commands(ws))
                    # Run training step generator loop
                    loop_task = asyncio.create_task(self.agent_loop(ws))
                    
                    await asyncio.gather(listen_task, loop_task)
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                print(f"WebSocket disconnected: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30)

    async def listen_commands(self, ws):
        try:
            async for message in ws:
                data = json.loads(message)
                cmd_type = data.get("type")
                if cmd_type == "command":
                    action = data.get("action")
                    if action == "START":
                        self.is_running = True
                        print("Bot training started.")
                    elif action == "STOP":
                        self.is_running = False
                        print("Bot training paused.")
                    elif action == "SET_SPEED":
                        self.delay_speed = float(data.get("value", 1.0))
                        print(f"Speed delay adjusted to: {self.delay_speed}s")
                    elif action == "SET_BET":
                        self.bet_amount = float(data.get("value", 1.0))
                        self.env.stake = self.bet_amount
                        print(f"Bet amount adjusted to: {self.bet_amount}")
        except websockets.exceptions.ConnectionClosed:
            pass

    async def agent_loop(self, ws):
        obs, info = await asyncio.to_thread(self.env.reset)
        
        while True:
            if not self.is_running:
                # Idle wait when paused
                await asyncio.sleep(0.5)
                continue
                
            self.iteration += 1
            
            # Select target using current DQN policy
            action = self.agent.act(obs, self.epsilon)
            
            # Execute target click in game (runs inside thread to protect async loops)
            next_obs, reward, terminated, truncated, info = await asyncio.to_thread(
                self.env.step, action
            )
            
            # Log experience transition details
            self.agent.buffer.push(obs, action, reward, next_obs, terminated)
            
            # Optimize Neural Network parameters (SGD step)
            loss = 0.0
            if len(self.agent.buffer) > self.agent.batch_size:
                loss = await asyncio.to_thread(self.agent.learn)
                
            # Log outcomes
            outcome = info.get("outcome", "LOSS")
            if outcome == "WIN":
                self.wins += 1
                self.total_profit += (info.get("payout", 0.0) - self.bet_amount)
            elif outcome == "LOSS":
                self.losses += 1
                self.total_profit -= self.bet_amount
                
            total_games = max(self.wins + self.losses, 1)
            win_rate = self.wins / total_games
            
            # Extract Q-values strategy representation
            q_values = self.agent.get_q_values(obs).tolist()
            
            # Compile telemetry payload
            telemetry_data = {
                "type": "telemetry",
                "payload": {
                    "iteration": self.iteration,
                    "target_shot": action,
                    "outcome": outcome,
                    "payout": float(info.get("payout", 0.0)),
                    "profit_loss": float(reward),
                    "epsilon": round(float(self.epsilon), 4),
                    "win_rate": round(float(win_rate), 4),
                    "loss": round(float(loss), 5),
                    "q_values": q_values,
                    "grid_state": obs[:12].tolist()
                }
            }
            
            # Send telemetry to socket server
            try:
                await ws.send(json.dumps(telemetry_data))
            except Exception:
                pass
                
            # Periodically stream screen updates (every 5 steps)
            if self.iteration % 5 == 0:
                screenshot_b64 = await asyncio.to_thread(self.controller.capture_screenshot)
                if screenshot_b64:
                    screenshot_data = {
                        "type": "screenshot",
                        "payload": {
                            "base64": screenshot_b64
                        }
                    }
                    try:
                        await ws.send(json.dumps(screenshot_data))
                    except Exception:
                        pass
            
            # Reset environment on terminal game state
            if terminated:
                obs, info = await asyncio.to_thread(self.env.reset)
            else:
                obs = next_obs
                
            # Decaying Epsilon
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
                
            # Periodic model parameter saving (every 5000 runs)
            if self.iteration % 5000 == 0:
                os.makedirs("checkpoints", exist_ok=True)
                self.agent.save(f"checkpoints/dqn_penalty_{self.iteration}.pth")
                
            # Configurable rate limiter
            await asyncio.sleep(self.delay_speed)

if __name__ == "__main__":
    orchestrator = AutomationOrchestrator()
    try:
        asyncio.run(orchestrator.connect_and_loop())
    except KeyboardInterrupt:
        print("Bot automation stopped.")
