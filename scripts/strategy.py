from collections import deque
from models import Signal, Tick


class MovingAverageStrategy:
    def __init__(self, short_window: int, long_window: int):
        self.short_window = short_window
        self.long_window = long_window

        self.prices = deque(maxlen=long_window)

        # Store previous MA values for crossover detection
        self.prev_short_ma = None
        self.prev_long_ma = None

    def _moving_average(self, window: int):
        if len(self.prices) < window:
            return None
        return sum(list(self.prices)[-window:]) / window

    def on_tick(self, tick: Tick) -> Signal:
        self.prices.append(tick.price)

        short_ma = self._moving_average(self.short_window)
        long_ma = self._moving_average(self.long_window)

        # Not enough data yet
        if short_ma is None or long_ma is None:
            return Signal.HOLD

        signal = Signal.HOLD

        # Detect crossover
        if self.prev_short_ma is not None and self.prev_long_ma is not None:
            # Bullish crossover
            if self.prev_short_ma <= self.prev_long_ma and short_ma > long_ma:
                signal = Signal.BUY

            # Bearish crossover
            elif self.prev_short_ma >= self.prev_long_ma and short_ma < long_ma:
                signal = Signal.SELL

        # Update previous values
        self.prev_short_ma = short_ma
        self.prev_long_ma = long_ma

        return signal
