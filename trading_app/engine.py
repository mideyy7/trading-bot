from models import Tick, Signal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Core trading engine that handles incoming price ticks,
    generates signals using a strategy, and passes them to the execution engine.
    """
    
    def __init__(self, strategy, execution):
        self.strategy = strategy
        self.execution = execution

    def on_price(self, price: float) -> Signal:
        """
        Process a new price tick.
        Generates a signal using the strategy and executes it.
        """
        tick = Tick(price=price, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        signal = self.strategy.on_tick(tick)
        
        if signal != Signal.HOLD:
            logger.info(f"Signal generated: {signal.value} at price {price}")
        else:
            logger.debug(f"HOLD signal at price {price}")

        self.execution.on_signal(signal, tick)
        return signal
