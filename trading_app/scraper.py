import websockets
import json
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())

async def stream_binance(symbol: str, engine):
    url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"

    async with websockets.connect(url, ssl = ssl_context) as ws:
        async for message in ws:
            data = json.loads(message)
            price = float(data["p"])
            # print(price)
            engine.on_price(price)