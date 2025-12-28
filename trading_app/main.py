import asyncio
import logging

from strategy import MovingAverageStrategy
from execution import ExecutionEngine
from engine import TradingEngine
from scraper import stream_binance


# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def main():
    """
    Initialize trading strategy, execution engine, and trading engine.
    Stream live market data from Binance and process signals in real-time.
    """
    # --- Initialize components ---
    strategy = MovingAverageStrategy(short_window=2, long_window=5)
    execution = ExecutionEngine()
    engine = TradingEngine(strategy=strategy, execution=execution)

    logger.info("Trading system initialized and connecting to Binance stream...")

    # --- Start streaming market data ---
    await stream_binance(symbol="btcusdt", engine=engine)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user. Exiting gracefully...")
