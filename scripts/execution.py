from models import Signal, Tick
from datetime import datetime

class ExecutionEngine:
    def __init__(self):
        self.position = 0
        self.entry_price = None
        self.total_pnl = 0.0
        self.pnl_pct = 0.0
        self.trades = []


    def on_signal(self, signal:Signal, tick:Tick):
        if signal == Signal.BUY and self.position == 0:
            self.position = 1
            self.entry_price = tick.price
            self.trades.append({
                'time': tick.timestamp,
                'action': 'BUY',
                'price': tick.price
            })
        elif signal == Signal.SELL and self.position == 1:
            pnl = tick.price - self.entry_price
            self.total_pnl += pnl
            self.pnl_pct = (pnl / self.entry_price) * 100
            self.trades.append({
                    'time': tick.timestamp,
                    'action': 'SELL',
                    'price': tick.price,
                    'pnl': pnl
                })
            self.position = 0
            self.entry_price = None
        print("=" * 60)
        print("Working")
        print(self.trades)

       