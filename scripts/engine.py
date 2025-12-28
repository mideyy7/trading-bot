from models import Tick
from datetime import datetime

class TradingEngine:
    def __init__(self, strategy, execution):
        self.strategy = strategy
        self.execution = execution

    def on_price(self, price: float):
        tick = Tick(price=price, timestamp=datetime.now().strftime("%Y-%m-%d"))
        signal = self.strategy.on_tick(tick)
        self.execution.on_signal(signal, tick)
        return signal