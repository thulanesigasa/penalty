import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import create_db_and_tables, get_session
from app.models import GameRecord
from app.services.websocket_manager import manager

app = FastAPI(title="Penalty Game AI Bridge API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/history")
async def get_history(limit: int = 100, db: AsyncSession = Depends(get_session)):
    statement = select(GameRecord).order_by(desc(GameRecord.id)).limit(limit)
    result = await db.execute(statement)
    results = list(result.scalars().all())
    # Reverse to keep chronological ordering for charts
    results.reverse()
    return results

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_session)):
    # Total count
    total_count_result = await db.execute(select(func.count(GameRecord.id)))
    total_count = total_count_result.scalar() or 0
    if total_count == 0:
        return {"total_iterations": 0, "win_rate": 0.0, "total_profit": 0.0}

    # Total wins
    wins_result = await db.execute(select(func.count(GameRecord.id)).where(GameRecord.outcome == "WIN"))
    total_wins = wins_result.scalar() or 0
    win_rate = (total_wins / total_count) if total_count > 0 else 0.0

    # Total profit
    profit_result = await db.execute(select(func.sum(GameRecord.profit_loss)))
    total_profit = profit_result.scalar() or 0.0

    return {
        "total_iterations": total_count,
        "win_rate": round(win_rate, 4),
        "total_profit": round(total_profit, 2)
    }

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect_dashboard(websocket)
    try:
        while True:
            # Await control instructions from UI (e.g., {"type": "command", "action": "START"})
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # Forward instruction straight to the bot
                await manager.send_to_bot(msg)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)

@app.websocket("/ws/bot")
async def websocket_bot(websocket: WebSocket):
    await manager.connect_bot(websocket)
    from app.database import async_session_maker
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # If telemetry logs payload, write to DB
                if msg.get("type") == "telemetry":
                    record_data = msg.get("payload", {})
                    async with async_session_maker() as db:
                        record = GameRecord(
                            iteration=record_data.get("iteration"),
                            target_shot=record_data.get("target_shot"),
                            outcome=record_data.get("outcome"),
                            payout=record_data.get("payout"),
                            profit_loss=record_data.get("profit_loss"),
                            epsilon=record_data.get("epsilon"),
                            win_rate=record_data.get("win_rate")
                        )
                        db.add(record)
                        await db.commit()
                # Broadcast logs or live visual states to frontend dashboards
                await manager.broadcast_to_dashboards(msg)
            except Exception as e:
                print(f"Error handling bot message: {e}")
    except WebSocketDisconnect:
        manager.disconnect_bot()
