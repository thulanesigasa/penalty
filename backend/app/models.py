from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class GameRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    iteration: int
    target_shot: int
    outcome: str
    payout: float
    profit_loss: float
    epsilon: float
    win_rate: float
