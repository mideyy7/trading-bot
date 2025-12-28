import asyncio
from collections import deque
import json
import websockets
import os
import ssl
import certifi
from dotenv import load_dotenv

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
# ALPACA_URL = "wss://stream.data.alpaca.markets/v2/iex"
ALPACA_URL = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
ALPACA_SYMBOL = "FAKEPACA"

# SSL context for macOS / cert verification
ssl_context = ssl.create_default_context(cafile=certifi.where())

prices = deque(maxlen=30)
async def main():
    async with websockets.connect(ALPACA_URL, ssl = ssl_context) as ws:
        #Authenticate
        authentication_msg = {"action": "auth", "key": ALPACA_API_KEY, "secret": ALPACA_SECRET_KEY}
        await ws.send(json.dumps(authentication_msg))
        response = await ws.recv()
        print(response)

        #Subscribe
        # subscription_msg = { "action": "subscribe","trade": [ALPACA_SYMBOL]}  #To test initially
        subscription_msg = {"action":"subscribe","trades":["AAPL"],"quotes":["AMD","CLDR"],"bars":["*"]}
        await ws.send(json.dumps(subscription_msg))
        response = await ws.recv()
        print(response)

        #Receive live trades
        # Receive live trades
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            for event in data:
                if event["T"] == "t":  # Trade event
                    price = event["p"]
                    prices.append(price)
                    ma_10 = sum(list(prices)[-10:])/10 if len(prices) >= 10 else None
                    ma_30 = sum(prices)/30 if len(prices) == 30 else None
                    print(f"Price: {price}, MA10: {ma_10}, MA30: {ma_30}")
       

if __name__ == "__main__":
    asyncio.run(main())






