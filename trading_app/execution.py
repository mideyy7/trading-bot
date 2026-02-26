from models import Signal, Tick
import zmq

class ExecutionEngine:
    def __init__(self):
        self.position = 0
        self.entry_price: float | None = None
        self.total_pnl = 0.0
        self.pnl_pct = 0.0
        # self.trades = []


    def on_signal(self, signal:Signal, tick:Tick):
        trade = None
        if signal == Signal.BUY and self.position == 0:
            self.position = 1
            self.entry_price = tick.price
            trade = {
                'time': tick.timestamp,
                'action': 'BUY',
                'price': tick.price
            }
        elif signal == Signal.SELL and self.position == 1:
            assert self.entry_price is not None
            pnl = tick.price - self.entry_price
            self.total_pnl += pnl
            self.pnl_pct = (pnl / self.entry_price) * 100
            trade = {
                'time': tick.timestamp,
                'action': 'SELL',
                'price': tick.price
            }
            self.position = 0
            self.entry_price = None
            
        if trade is not None:
            context = zmq.Context()
            socket = context.socket(zmq.PUSH)
            socket.connect("tcp://localhost:5555")
            socket.send_json(trade)

        return trade