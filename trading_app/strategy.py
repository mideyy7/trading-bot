from collections import deque
from itertools import islice
from models import Signal, Tick


class MovingAverageStrategy:
    """
    Moving average crossover strategy with RSI confirmation and cooldown.
    Generates BUY when short MA crosses above long MA and RSI < 70 (not overbought).
    Generates SELL when short MA crosses below long MA and RSI > 30 (not oversold).
    """
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    COOLDOWN_TICKS = 10

    def __init__(self, short_window, long_window):
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

        self.short_window = short_window
        self.long_window = long_window
        # Deque must be large enough for both MA windows and RSI period
        self.prices = deque(maxlen=max(long_window, self.RSI_PERIOD + 1))

        self.prev_short_ma = None
        self.prev_long_ma = None
        self.ticks_since_signal = self.COOLDOWN_TICKS  # Start ready to signal

    def _moving_average(self, window):
        """Compute the moving average over the last 'window' prices."""
        if len(self.prices) < window:
            return None
        # islice on reversed deque avoids allocating a full list copy
        return sum(islice(reversed(self.prices), window)) / window

    def _rsi(self):
        """
        Compute RSI over RSI_PERIOD using simple average gains/losses.
        Returns None if there isn't enough price history yet.
        """
        if len(self.prices) < self.RSI_PERIOD + 1:
            return None

        prices = list(self.prices)[-(self.RSI_PERIOD + 1):]
        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))

        avg_gain = sum(gains) / self.RSI_PERIOD
        avg_loss = sum(losses) / self.RSI_PERIOD

        if avg_loss == 0:
            return 100.0  # All gains, maximally overbought

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def on_tick(self, tick):
        self.prices.append(tick.price)
        self.ticks_since_signal += 1

        short_ma = self._moving_average(self.short_window)
        long_ma = self._moving_average(self.long_window)

        # Not enough data yet
        if short_ma is None or long_ma is None:
            return Signal.HOLD

        signal = Signal.HOLD

        if self.prev_short_ma is not None and self.prev_long_ma is not None:
            if self.ticks_since_signal >= self.COOLDOWN_TICKS:
                rsi = self._rsi()

                # Bullish crossover: short MA crosses above long MA
                if self.prev_short_ma <= self.prev_long_ma and short_ma > long_ma:
                    # RSI confirmation: only buy if market is not overbought
                    if rsi is None or rsi < self.RSI_OVERBOUGHT:
                        signal = Signal.BUY
                        self.ticks_since_signal = 0

                # Bearish crossover: short MA crosses below long MA
                elif self.prev_short_ma >= self.prev_long_ma and short_ma < long_ma:
                    # RSI confirmation: only sell if market is not oversold
                    if rsi is None or rsi > self.RSI_OVERSOLD:
                        signal = Signal.SELL
                        self.ticks_since_signal = 0

        self.prev_short_ma = short_ma
        self.prev_long_ma = long_ma
        return signal
