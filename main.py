import pandas as pd
import matplotlib.pyplot as plt

def main():
    df = pd.read_csv("prices.csv")

    print("=" * 60)
    print("Data has been read successfully")
    print(df.head())

    #ensure date is datemime
    df["date"] = pd.to_datetime(df["date"])

    #resets the index numbering that might have been altered by sorting
    df = df.sort_values("date").reset_index(drop=True)

    #calculate moving averages
    df["moving_average_10"] = df["price"].rolling(window=10).mean()
    df["moving_average_30"] = df["price"].rolling(window=30).mean()

    #The first 10 and 30 days respectily will not have moving averages because they have no prior prices recorded
    #Delete them as they won't be needed
    df = df.dropna().reset_index(drop = True)

    print("=" * 60)
    print("Moving averages have been calculated successfully")
    print(df.head())


    #Graphical representatiomn to check correctness
    # plt.plot(df["date"], df["price"], label = "Price")
    # plt.plot(df["date"], df["moving_average_10"], label = "MA_10")
    # plt.plot(df["date"], df["moving_average_30"], label = "MA_30")
    # plt.show()

    def generate_signal(row):
        if row["moving_average_10"] > row["moving_average_30"]:
            return "BUY"
        elif row["moving_average_10"] < row["moving_average_30"]:
            return "SELL"
        else:
            return "HOLD"
        
    df["signal"] = df.apply(generate_signal, axis = 1)

    print("=" * 60)
    print("Signals have been generated successfully")
    print(df[["date", "price", "signal"]].head(10))

    #BACKTESTING
    starting_cash = 10000
    cash = starting_cash
    position = 0        #how many units owned
    position_history = []   #Track position over time
    cash_history = []       #Track cash over time
    equity_history = []     #Track total equity (cash + holdings value)

    print("BACKTESTING")
    print("=" * 60)
    print(f"Starting with ${cash:.2f}")

    for i in range(len(df)):
        current_price = df.loc[i, "price"]
        current_signal = df.loc[i, "signal"]
        current_date = df.loc[i, "date"]

        #Execute trade based on signal
        if current_signal == "BUY" and position == 0:
            amoount_to_invest = cash * 0.95  #keep 5 perccent of cash as buffer
            quantity = int(amoount_to_invest / current_price)

            if quantity > 0:
                cost = quantity * current_price
                cash -= cost
                position = quantity
                print(f"{current_date.date()} | BUY | {quantity} UNITS AT {current_price:.2f} | Cost: {cost:.2f}")
        elif current_signal == "SELL" and position > 0:
            proceeds = position * current_price
            cash += proceeds
            print(f"{current_date.date()} | SELL | {position} UNITS AT {current_price:.2f} | Proceeds: {proceeds:.2f}")
            position = 0

        #Track portfolio state
        holdings_value = position * current_price
        total_equity = cash + holdings_value

        #Track the history of position, cash and equity
        position_history.append(position)
        cash_history.append(cash)
        equity_history.append(total_equity)

    #Final liquidation to close any open positions
    if position > 0:
        final_price = df.loc[len(df) - 1, "price"]
        proceeds = position * final_price
        cash += proceeds
        print(f"FINAL LIQUIDATION | SELL | {position} UNITS AT {final_price:.2f} | Proceeds: {proceeds:.2f}")
        position = 0

    #Calculate performance metrics
    final_equity = cash
    total_return = final_equity - starting_cash
    total_return_percent = (total_return / starting_cash) * 100

    #Count trades
    df["position"] = position_history
    trades = df[df["signal"].isin(["BUY", "SELL"])]
    num_trades = len(trades)

    #Calculate win rate by comparing entry and exit prices
    buy_trades = df[df["signal"] == "BUY"]["price"].values
    sell_trades = df[df["signal"] == "SELL"]["price"].values
    min_len = min(len(buy_trades), len(sell_trades))
    if min_len > 0:
        winning_trades = sum(sell_trades[:min_len] > buy_trades[:min_len])
        win_rate = (winning_trades / min_len) * 100
    else:
        win_rate = 0

    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"Starting capital: ${starting_cash:.2f}")
    print(f"Ending capital: ${final_equity:.2f}")
    print(f"Total Return: ${total_return:.2f}   {total_return_percent:.2f}%")
    print(f"Total Trades: ${num_trades}")
    print(f"Win Rate: {win_rate:.2f}")

    #**Visulaization**
    df["equity"] = equity_history
    df["cash"] = cash_history
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Price and Moving Averages
    ax1.plot(df["date"], df["price"], label="Price", color="black", linewidth=1)
    ax1.plot(df["date"], df["moving_average_10"], label="MA 10", color="blue", linewidth=1)
    ax1.plot(df["date"], df["moving_average_30"], label="MA 30", color="red", linewidth=1)
    
    # Mark buy/sell signals
    buy_signals = df[df["signal"] == "BUY"]
    sell_signals = df[df["signal"] == "SELL"]
    ax1.scatter(buy_signals["date"], buy_signals["price"], color="green", marker="^", s=100, label="BUY", zorder=5)
    ax1.scatter(sell_signals["date"], sell_signals["price"], color="red", marker="v", s=100, label="SELL", zorder=5)
    
    ax1.set_title("Price and Moving Average Crossover Strategy")
    ax1.set_ylabel("Price ($)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Portfolio Equity
    ax2.plot(df["date"], df["equity"], label="Total Equity", color="green", linewidth=2)
    ax2.axhline(y=starting_cash, color="gray", linestyle="--", label="Starting Capital")
    ax2.fill_between(df["date"], starting_cash, df["equity"], 
                      where=(df["equity"] >= starting_cash), alpha=0.3, color="green")
    ax2.fill_between(df["date"], starting_cash, df["equity"], 
                      where=(df["equity"] < starting_cash), alpha=0.3, color="red")
    
    ax2.set_title("Portfolio Equity Over Time")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Equity ($)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("backtest_results.png", dpi=150)
    print(f"\n📊 Chart saved to 'backtest_results.png'")
    plt.show()
    
    df.to_csv("output.csv", index=False)
    print(f"📁 Full results saved to 'backtest_output.csv'\n")


if __name__ == "__main__":
    main()
