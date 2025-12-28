import asyncio
from strategy import MovingAverageStrategy
from execution import ExecutionEngine
from engine import TradingEngine
from scraper import stream_binance

async def main():
    strategy = MovingAverageStrategy(10,30)
    execution = ExecutionEngine()
    engine = TradingEngine(strategy, execution)
    await stream_binance("btcusdt", engine)

if __name__ == "__main__":
    asyncio.run(main())