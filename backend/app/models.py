from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class GameRecord(SQLModel, table=True):
    """
    SQLModel database table representing training iteration telemetry.
    Stores logs of actions taken, outcomes received, and policy coefficients.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # ISO 8601 string of the exact database write timestamp
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Sequential training count (iteration)
    iteration: int
    
    # Target clicked (0-11)
    target_shot: int
    
    # Win or Loss outcomes (WIN / LOSS / INVALID)
    outcome: str
    
    # Return payouts (multiplier payouts)
    payout: float
    
    # Realized profit or loss (change in stake)
    profit_loss: float
    
    # Epsilon decay rate coefficient
    epsilon: float
    
    # Session average success rate
    win_rate: float
