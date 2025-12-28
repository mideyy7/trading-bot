# =============================================================================
# app.py - Fixed to show C++ trades on web dashboard
# =============================================================================

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi.responses import StreamingResponse # Add this import
import asyncio


from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import zmq
import zmq.asyncio

from strategy import MovingAverageStrategy
from execution import ExecutionEngine
from engine import TradingEngine
from scraper import stream_binance

app = FastAPI()

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Shared state
# -----------------------------
trades_history = []             # All trades (both signals sent and C++ confirmations)
system_status = {
    "status": "STARTING",
    "position": 0,
    "pnl": 0.0,
    "current_price": 0.0,
    "total_trades": 0
}

# -----------------------------
# ZMQ setup
# -----------------------------
ctx = zmq.asyncio.Context()

# Send signals to C++
cpp_sender = ctx.socket(zmq.PUSH)
cpp_sender.connect("tcp://localhost:5555")

# Receive confirmations FROM C++ (NEW!)
cpp_receiver = ctx.socket(zmq.PULL)
cpp_receiver.bind("tcp://*:5556")  # C++ will send confirmations here

# -----------------------------
# Listen for C++ confirmations
# -----------------------------
async def cpp_confirmation_listener():
    """
    Listen for trade confirmations from C++ execution engine
    This is what displays trades on the web!
    """
    print("🎧 Listening for C++ trade confirmations on port 5556...")
    
    while True:
        try:
            # Wait for message from C++
            msg = await cpp_receiver.recv_json()
            
            print(f"📥 Received from C++: {msg}")
            
            # Add to trade history
            trade_record = {
                "time": msg.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "action": msg.get("action"),
                "price": msg.get("price"),
                "pnl": msg.get("pnl", 0.0),
                "source": "C++"
            }
            
            trades_history.append(trade_record)
            
            # Update system status
            system_status["total_trades"] = len(trades_history)
            if msg.get("position") is not None:
                system_status["position"] = msg["position"]
            if msg.get("total_pnl") is not None:
                system_status["pnl"] = msg["total_pnl"]
            
            print(f"✅ Trade added to dashboard: {trade_record}")
            
        except Exception as e:
            print(f"❌ Error in C++ listener: {e}")
            await asyncio.sleep(1)

# -----------------------------
# Background strategy runner
# -----------------------------
async def strategy_runner():
    """
    Run strategy and send signals to C++
    """
    print("🚀 Starting strategy runner...")
    
    strategy = MovingAverageStrategy(3, 8)  # Aggressive for testing
    execution = ExecutionEngine()
    engine = TradingEngine(strategy, execution)

    # Override execution to send to C++
    original_on_signal = execution.on_signal

    def patched_on_signal(signal, tick):
        """Send signals to C++ engine"""
        trade = original_on_signal(signal, tick)
        
        if trade:
            # Prepare message for C++
            cpp_message = {
                "action": trade["action"],
                "price": trade["price"],
                "time": trade["time"]
            }
            
            # Send to C++
            asyncio.create_task(send_to_cpp(cpp_message))
            
            # Log signal sent (not the actual trade - C++ will confirm)
            print(f"📤 Signal sent to C++: {trade['action']} @ ${trade['price']}")
        
        return trade

    execution.on_signal = patched_on_signal

    # Update current price
    async def update_price_wrapper(tick):
        system_status["current_price"] = tick.price
        system_status["status"] = "RUNNING"
        await engine.on_tick(tick)
    
    # Run Binance streaming
    try:
        from scraper import stream_binance_with_callback
        await stream_binance_with_callback("btcusdt", update_price_wrapper)
    except ImportError:
        # Fallback if scraper doesn't have callback version
        await stream_binance("btcusdt", engine)

async def send_to_cpp(message):
    """Send message to C++ engine"""
    try:
        await cpp_sender.send_json(message)
    except Exception as e:
        print(f"❌ Error sending to C++: {e}")

# -----------------------------
# Lifespan for background tasks
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*70)
    print("🌐 STARTING WEB DASHBOARD")
    print("="*70)
    
    tasks = [
        asyncio.create_task(strategy_runner()),
        asyncio.create_task(cpp_confirmation_listener()),  # KEY: Listen to C++
    ]
    
    print("✅ Background tasks started")
    print("📊 Dashboard: http://localhost:8000")
    print("="*70 + "\n")
    
    try:
        yield
    finally:
        print("\n🛑 Shutting down...")
        for t in tasks:
            t.cancel()

app.router.lifespan_context = lifespan

# -----------------------------
# FastAPI routes
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/trades")
async def get_trades():
    """Return all trades"""
    return JSONResponse(content=trades_history)

@app.get("/status")
async def get_status():
    """Return system status"""
    return JSONResponse(content=system_status)

# Create a queue to hold updates for the web dashboard
web_update_queue = asyncio.Queue()

# ... inside cpp_confirmation_listener ...
async def cpp_confirmation_listener():
    while True:
        try:
            msg = await cpp_receiver.recv_json()
            # ... your existing logic to update trades_history ...
            
            # NEW: Push the update to the queue for the web dashboard
            await web_update_queue.put(msg) 
            
        except Exception as e:
            print(f"❌ Error in C++ listener: {e}")
            await asyncio.sleep(1)

# NEW: Add the SSE route that index.html is looking for
@app.get("/trades/stream")
async def trade_stream():
    async def event_generator():
        while True:
            # Wait for a new trade confirmation from the queue
            trade_data = await web_update_queue.get()
            yield f"data: {json.dumps(trade_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)