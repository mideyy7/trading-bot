import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_prices(num_days=200, starting_price=42000):
    """
    Generate realistic-looking price data with trends and volatility
    """
    
    dates = []
    prices = []
    
    current_date = datetime(2024, 1, 1)
    current_price = starting_price
    
    for i in range(num_days):
        dates.append(current_date)
        
        # Add some trending behavior
        trend = np.sin(i / 20) * 500  # Cyclical trend
        
        # Add random daily volatility
        volatility = np.random.randn() * 300
        
        # Small upward drift
        drift = 10
        
        # Update price
        current_price = current_price + drift + trend/10 + volatility
        
        # Don't let price go too low
        current_price = max(current_price, starting_price * 0.5)
        
        prices.append(round(current_price, 2))
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    
    return df

if __name__ == "__main__":
    # Generate 200 days of price data
    df = generate_sample_prices(num_days=200, starting_price=42000)
    
    # Save to CSV
    df.to_csv("prices.csv", index=False)
    
    print("✅ Sample price data generated!")
    print(f"📁 File: prices.csv")
    print(f"📊 Days: {len(df)}")
    print(f"💰 Starting price: ${df['price'].iloc[0]:,.2f}")
    print(f"💰 Ending price: ${df['price'].iloc[-1]:,.2f}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nLast 5 rows:")
    print(df.tail())