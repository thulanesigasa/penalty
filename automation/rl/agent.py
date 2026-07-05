import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
from typing import Tuple

class QNetwork(nn.Module):
    """
    Multi-layer Perceptron (MLP) mapping 13 input features (12 target cells + current multiplier)
    to 12 output values (predicted Q-values for shooting spots 0-11).
    """
    def __init__(self, state_dim: int = 13, action_dim: int = 12):
        super(QNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

class ReplayBuffer:
    """
    Experience replay storage to break correlations between consecutive observations.
    """
    def __init__(self, capacity: int = 50000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        state, action, reward, next_state, done = zip(*random.sample(self.buffer, batch_size))
        return (
            np.array(state, dtype=np.float32),
            np.array(action, dtype=np.int64),
            np.array(reward, dtype=np.float32),
            np.array(next_state, dtype=np.float32),
            np.array(done, dtype=np.float32)
        )

    def __len__(self) -> int:
        return len(self.buffer)

class DQNAgent:
    """
    Deep Q-Network Agent coordinating epsilon-greedy exploration, target synchronization,
    backpropagation loss optimization, and model checkpoints saving/loading.
    """
    def __init__(
        self,
        state_dim: int = 13,
        action_dim: int = 12,
        lr: float = 1e-3,
        gamma: float = 0.95,
        buffer_capacity: int = 50000,
        batch_size: int = 64,
        target_update_freq: int = 500
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.learn_steps = 0
        
        # Instantiate policy and target networks (Double DQN approach)
        self.q_net = QNetwork(state_dim, action_dim)
        self.target_net = QNetwork(state_dim, action_dim)
        self.target_net.load_state_dict(self.q_net.state_dict())
        
        # Optimizer and Replay Buffer setup
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_capacity)
        
        # Select target training device (GPU if available, else CPU fallback)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_net.to(self.device)
        self.target_net.to(self.device)

    def act(self, state: np.ndarray, epsilon: float = 0.1) -> int:
        """
        Calculates the best action to perform using an epsilon-greedy strategy.
        Filters out targets that have already been clicked (i.e. state[i] == 1.0) to prevent invalid moves.
        """
        # Epsilon-greedy exploration step
        if random.random() < epsilon:
            # Choose from active (un-clicked) targets
            active_spots = np.where(state[:12] == 0.0)[0]
            if len(active_spots) > 0:
                return int(random.choice(active_spots))
            return random.randint(0, self.action_dim - 1)
        
        # Exploitation step
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.q_net(state_t)
            
            # Select action with maximum Q-value that is still active (unhit)
            active_spots = np.where(state[:12] == 0.0)[0]
            if len(active_spots) > 0:
                q_vals_cpu = q_values.squeeze(0).cpu().numpy()
                best_action = active_spots[np.argmax(q_vals_cpu[active_spots])]
                return int(best_action)
            else:
                return int(torch.argmax(q_values).item())

    def learn(self) -> float:
        """
        Samples transitions from experience buffer, calculates Double DQN Huber loss,
        optimizes weight gradients, and updates the target network periodically.
        """
        if len(self.buffer) < self.batch_size:
            return 0.0
            
        # Sample mini-batch from experience buffer
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)
        
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        # Extract estimated Q-values of selected actions from policy network
        curr_q = self.q_net(states_t).gather(1, actions_t)
        
        # Compute target Q-values using Double DQN logic
        with torch.no_grad():
            # Get optimal action from policy network
            best_actions = self.q_net(next_states_t).argmax(dim=1, keepdim=True)
            # Evaluate this action using target network
            max_next_q = self.target_net(next_states_t).gather(1, best_actions)
            target_q = rewards_t + (1 - dones_t) * self.gamma * max_next_q
            
        # Smooth L1 (Huber) loss function
        loss_fn = nn.SmoothL1Loss()
        loss = loss_fn(curr_q, target_q)
        
        # Optimize neural network parameter weights
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Increment step count and sync target parameters if threshold reached
        self.learn_steps += 1
        if self.learn_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
            
        return float(loss.item())

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """
        Helper method to extract Q-value predictions for all actions from state.
        Used to feed visual dashboard strategy overlays.
        """
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_vals = self.q_net(state_t).squeeze(0).cpu().numpy()
        return q_vals

    def save(self, filepath: str):
        """
        Saves target model weights to disk.
        """
        torch.save(self.q_net.state_dict(), filepath)

    def load(self, filepath: str):
        """
        Loads saved model weights from disk.
        """
        self.q_net.load_state_dict(torch.load(filepath, map_location=self.device))
        self.target_net.load_state_dict(self.q_net.state_dict())
