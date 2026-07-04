# Penalty Game RL Automation Bot & Dashboard

This repository contains a full-stack, AI-driven browser automation bot that plays a web-based Penalty shootout game, logs performance telemetry, and streams real-time training analytics to a modern Next.js dashboard.

---

## Technical Stack Overview

- **Frontend Dashboard**: Next.js (React), Tailwind CSS, Recharts for performance visualization.
- **Backend API Bridge**: FastAPI (Python), SQLModel (SQLite database tracking), WebSockets for zero-latency messaging.
- **Automation Controller**: Playwright (Python) connecting to Chrome via Chrome DevTools Protocol (CDP) on remote debugging port `9222`.
- **Reinforcement Learning Brain**: PyTorch Deep Q-Network (DQN) with a custom Gymnasium environment.

---

## 1. Setup & Initialization

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- Google Chrome browser

---

### Step A: Configure Target Browser for Handoff
To bypass bot detection and allow manual user authentication:
1. Close all active instances of Google Chrome.
2. Launch Google Chrome from terminal or create a custom shortcut enabling the remote debugging port:
   ```powershell
   # Windows PowerShell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-automation-profile"
   ```
3. Navigate to the target Penalty shootout game URL, sign in to your demo account, and verify the page structure is ready.

---

### Step B: Start the Backend Gateway API
1. Navigate to `/backend`.
2. Create and active the virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Copy the environment file:
   ```powershell
   copy .env.example .env
   ```
5. Run the FastAPI server:
   ```powershell
   uvicorn app.main:app --reload
   ```
   *The SQLite database file (`penalty_games.db`) will be automatically created under `/data` on startup.*

---

### Step C: Launch the Next.js Web Dashboard
1. Navigate to `/frontend`.
2. Install npm packages:
   ```bash
   npm install
   ```
3. Launch development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### Step D: Initialize the RL Agent Loop
1. Navigate to `/automation`.
2. Create and active the virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start the training script:
   ```powershell
   python main.py
   ```

---

## 2. Dynamic Training Workflow

1. Open the **Dashboard** at `localhost:3000`. You will see the WebSocket status badge turn `CONNECTED`.
2. Adjust the **Demo Stake** and **Action Interval Delay** sliders to your preference.
3. Click the **Start RL Training** button. The dashboard will trigger the Python bot to begin.
4. The bot attaches to your active Chrome instance on port `9222`, observes the current board multiplier state, evaluates the DQN network to choose an optimal action (excluding already-hit targets), clicks the coordinates in Chrome, detects the round outcome, logs performance telemetry to SQLite, and streams the visual status overlays (Q-value strategy heatmap + viewport frames) back to your dashboard in real time.
