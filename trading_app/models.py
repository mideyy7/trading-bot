from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class Tick:
    price: float
    timestamp: datetime
