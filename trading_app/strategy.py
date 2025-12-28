from collections import deque
from typing import Optional
from models import Signal, Tick


class MovingAverageStrategy:
    """
    A simple moving average crossover strategy.
    Generates BUY when short-term MA crosses above long-term MA,
    and SELL when short-term MA crosses below long-term MA.
    """

    def __init__(self, short_window: int, long_window: int):
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

        self.short_window: int = short_window
        self.long_window: int = long_window
        self.prices: deque[float] = deque(maxlen=long_window)

        # Previous MA values to detect crossovers
        self.prev_short_ma: Optional[float] = None
        self.prev_long_ma: Optional[float] = None

    def _moving_average(self, window: int) -> Optional[float]:
        """
        Compute the moving average over the last 'window' prices.
        Returns None if not enough data is available.
        """
        if len(self.prices) < window:
            return None
        return sum(list(self.prices)[-window:]) / window

    def on_tick(self, tick: Tick) -> Signal:
        self.prices.append(tick.price)

        short_ma = self._moving_average(self.short_window)
        long_ma = self._moving_average(self.long_window)

        # Temporary simulation: alternate BUY/SELL every 5 ticks
        if len(self.prices) % 5 == 0:
            if (len(self.prices) // 5) % 2 == 0:
                return Signal.BUY
            else:
                return Signal.SELL

        # Not enough data yet
        if short_ma is None or long_ma is None:
            return Signal.HOLD

        signal = Signal.HOLD

        if self.prev_short_ma is not None and self.prev_long_ma is not None:
            # Bullish crossover: short MA crosses above long MA
            if self.prev_short_ma <= self.prev_long_ma and short_ma > long_ma:
                signal = Signal.BUY
            # Bearish crossover: short MA crosses below long MA
            elif self.prev_short_ma >= self.prev_long_ma and short_ma < long_ma:
                signal = Signal.SELL

        # Update previous MA values
        self.prev_short_ma = short_ma
        self.prev_long_ma = long_ma

        return signal
