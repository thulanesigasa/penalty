import os
import json
import asyncio
import numpy as np
from dotenv import load_dotenv
import websockets

from rl.env import PenaltyEnv
from rl.agent import DQNAgent
from browser.controller import BrowserController

# Load shared environment configurations
load_dotenv()

BACKEND_WS_URL = os.getenv("BACKEND_WS_URL", "ws://localhost:8000/ws/bot")
CHROME_DEBUG_WS = os.getenv("CHROME_DEBUG_WS", "http://localhost:9222")

class AutomationOrchestrator:
    """
    Orchestrates the reinforcement learning execution loop.
    Asynchronously links browser actions, DQN predictions, database updates,
    and FastAPI WebSocket logs broadcast.
    """
    def __init__(self):
        self.is_running = False
        self.bet_amount = 1.0
        self.delay_speed = 1.0  # seconds delay between actions
        
        # Instantiate async-ready components
        self.controller = BrowserController(CHROME_DEBUG_WS)
        self.env = PenaltyEnv(controller=self.controller, stake=self.bet_amount)
        self.agent = DQNAgent(state_dim=13, action_dim=12)
        
        # DQN exploration rate variables
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.9995
        
        # Live counters
        self.iteration = 0
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0

    async def connect_and_loop(self):
        """
        Launches the browser, prompts manual login handoff, and boots up
        the WebSocket event listeners.
        """
        print("[Orchestrator] Initializing browser session...")
        await self.controller.connect(headless=False)
        
        # Pause execution to allow manual demo account sign-in
        await self.controller.pause_for_login(target_url="penalty")
        
        print(f"[Orchestrator] Connecting to API WebSocket: {BACKEND_WS_URL}")
        retry_delay = 2.0
        
        while True:
            try:
                async with websockets.connect(BACKEND_WS_URL) as ws:
                    print("[Orchestrator] Connected to WebSocket bridge successfully.")
                    retry_delay = 2.0  # reset retry interval
                    
                    # Run backend instruction listener and AI loop concurrently
                    listen_task = asyncio.create_task(self.listen_commands(ws))
                    loop_task = asyncio.create_task(self.agent_loop(ws))
                    
                    await asyncio.gather(listen_task, loop_task)
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                print(f"[Orchestrator] WebSocket disconnected: {e}. Reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30.0)
            except Exception as e:
                print(f"[Orchestrator] Unexpected loop error: {e}")
                await asyncio.sleep(2.0)

    async def listen_commands(self, ws):
        """
        Monitors incoming dashboard controls (START, STOP, adjust bet/speed).
        """
        try:
            async for message in ws:
                data = json.loads(message)
                cmd_type = data.get("type")
                if cmd_type == "command":
                    action = data.get("action")
                    if action == "START":
                        self.is_running = True
                        print("[Orchestrator] Training command: START")
                    elif action == "STOP":
                        self.is_running = False
                        print("[Orchestrator] Training command: STOP")
                    elif action == "SET_SPEED":
                        self.delay_speed = float(data.get("value", 1.0))
                        print(f"[Orchestrator] Speed delay set to {self.delay_speed}s")
                    elif action == "SET_BET":
                        self.bet_amount = float(data.get("value", 1.0))
                        self.env.stake = self.bet_amount
                        print(f"[Orchestrator] Bet amount adjusted to {self.bet_amount} USD")
        except websockets.exceptions.ConnectionClosed:
            pass

    async def agent_loop(self, ws):
        """
        Continuous Reinforcement Learning training loop.
        """
        # Retrieve initial reset state asynchronously
        obs, info = await self.env.reset()
        
        while True:
            if not self.is_running:
                await asyncio.sleep(0.5)
                continue
                
            self.iteration += 1
            
            # Predict action from model policy
            action = self.agent.act(obs, self.epsilon)
            
            # Execute shooting action in browser asynchronously
            next_obs, reward, terminated, truncated, info = await self.env.step(action)
            
            # Save experience trajectory tuple
            self.agent.buffer.push(obs, action, reward, next_obs, terminated)
            
            # Run neural net optimization (backprop)
            loss = 0.0
            if len(self.agent.buffer) > self.agent.batch_size:
                # DQNAgent.learn is fast enough to execute inline
                loss = self.agent.learn()
                
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
            
            # Get latest neural net Q-values
            q_values = self.agent.get_q_values(obs).tolist()
            
            # Package live telemetry payload
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
            
            # Forward telemetry to WebSocket gateway
            try:
                await ws.send(json.dumps(telemetry_data))
            except Exception:
                pass
                
            # Stream screenshot frames every 5 steps
            if self.iteration % 5 == 0:
                screenshot_b64 = await self.controller.capture_screenshot()
                if screenshot_b64:
                    try:
                        await ws.send(json.dumps({
                            "type": "screenshot",
                            "payload": {
                                "base64": screenshot_b64
                            }
                        }))
                    except Exception:
                        pass
            
            # Trigger reset if round finished
            if terminated:
                obs, info = await self.env.reset()
            else:
                obs = next_obs
                
            # Epsilon decay
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
                
            # Checkpoint model parameters every 5000 rounds
            if self.iteration % 5000 == 0:
                os.makedirs("checkpoints", exist_ok=True)
                self.agent.save(f"checkpoints/dqn_penalty_{self.iteration}.pth")
                
            # Limiter delay
            await asyncio.sleep(self.delay_speed)

if __name__ == "__main__":
    orchestrator = AutomationOrchestrator()
    try:
        asyncio.run(orchestrator.connect_and_loop())
    except KeyboardInterrupt:
        print("[Orchestrator] Stopped by user command.")
    except Exception as e:
        print(f"[Orchestrator] Critical run failure: {e}")
