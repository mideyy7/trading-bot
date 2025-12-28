#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <zmq.hpp>
#include <nlohmann/json.hpp>

struct Trade {
    std::string timestamp;
    std::string action;
    double price;
    double pnl;

    Trade(const std::string& ts, const std::string& act, double p, double pnl_val = 0.0)
        : timestamp(ts), action(act), price(p), pnl(pnl_val) {}
};

class ExecutionEngine {
private:
    int position;               // 0 = flat, 1 = long
    double entry_price;
    double cash;
    double total_pnl;
    std::vector<Trade> trades;
    zmq::socket_t& confirmation_socket;

    static constexpr char buy_marker = '1';
    static constexpr char sell_marker = 'X';

public:
    ExecutionEngine(double starting_cash, zmq::socket_t& conf_sock)
        : position(0), entry_price(0.0), cash(starting_cash), total_pnl(0.0), confirmation_socket(conf_sock) 
    {
        std::cout << std::string(70, '=') << "\n"
                  << "🚀 C++ EXECUTION ENGINE INITIALIZED\n"
                  << std::string(70, '=') << "\n"
                  << std::fixed << std::setprecision(2)
                  << "Starting Capital: $" << cash << "\n"
                  << "Confirmation socket: READY\n"
                  << std::string(70, '=') << "\n"
                  << "⏳ Waiting for signals from Python...\n\n";
    }

    void on_signal(const std::string& action, double price, const std::string& timestamp) {
        bool executed = false;
        double trade_pnl = 0.0;
        int demo_temp = 0;

        if (action == "BUY" && position == 0) {
            position = 1;
            entry_price = price;
            trades.emplace_back(timestamp, "BUY", price);
            executed = true;

            print_trade(buy_marker, "BUY", timestamp, price);

        } else if (action == "SELL" && position == 1) {
            trade_pnl = price - entry_price;
            total_pnl += trade_pnl;
            cash += trade_pnl;
            trades.emplace_back(timestamp, "SELL", price, trade_pnl);
            executed = true;

            print_trade(sell_marker, "SELL", timestamp, price, trade_pnl);

            position = 0;
            entry_price = 0.0;

        }
         else {
            std::cout << "⚠️  [" << timestamp << "] Ignored " << action
                      << " signal (current position: " << (position ? "LONG" : "FLAT") << ")\n";
        }

        if (executed) send_confirmation(action, price, timestamp, trade_pnl);
    }

private:
    void print_trade(char marker, const std::string& action, const std::string& timestamp,
                     double price, double pnl = 0.0) const 
    {
        std::cout << std::string(70, marker) << "\n"
                  << marker << " [" << timestamp << "] " << action << " EXECUTED\n"
                  << "   Entry/Exit Price: $" << price << "\n";

        if (action == "SELL") {
            std::cout << "   Trade PnL: $" << pnl << (pnl > 0 ? " ✅ PROFIT" : " ❌ LOSS") << "\n"
                      << "   Total PnL: $" << total_pnl << "\n"
                      << "   Portfolio Value: $" << (cash + (position * price)) << "\n";
        } else {
            std::cout << "   Position: LONG\n";
        }

        std::cout << std::string(70, marker) << "\n\n";
    }

    void send_confirmation(const std::string& action, double price,
                           const std::string& timestamp, double pnl) 
    {
        try {
            nlohmann::json confirmation;
            confirmation["action"] = action;
            confirmation["price"] = price;
            confirmation["time"] = timestamp;
            confirmation["position"] = position;
            confirmation["total_pnl"] = total_pnl;
            if (action == "SELL") confirmation["pnl"] = pnl;

            confirmation_socket.send(zmq::buffer(confirmation.dump()), zmq::send_flags::none);
            std::cout << "📤 Confirmation sent to Python: " << action << "\n";

        } catch (const std::exception& e) {
            std::cerr << "❌ Failed to send confirmation: " << e.what() << "\n";
        }
    }

public:
    void print_summary() const {
        std::cout << "\n" << std::string(70, '=') << "\n"
                  << "📊 TRADING SESSION SUMMARY\n"
                  << std::string(70, '=') << "\n";

        if (trades.empty()) {
            std::cout << "No trades executed.\n";
        } else {
            std::cout << "\nTrade History:\n" << std::string(70, '-') << "\n";
            for (const auto& t : trades) {
                std::cout << "[" << t.timestamp << "] " 
                          << std::setw(4) << t.action 
                          << " | Price: $" << std::setw(10) << t.price;
                if (t.action == "SELL") std::cout << " | PnL: $" << std::setw(8) << t.pnl;
                std::cout << "\n";
            }
            std::cout << std::string(70, '-') << "\n"
                      << "Total Trades: " << trades.size() << "\n"
                      << "Total PnL: $" << total_pnl 
                      << (total_pnl > 0 ? " ✅" : (total_pnl < 0 ? " ❌" : "")) << "\n";
        }

        double final_value = cash + (position * entry_price);
        std::cout << "Final Portfolio Value: $" << final_value << "\n"
                  << "Current Position: " << (position ? "LONG" : "FLAT") << "\n"
                  << std::string(70, '=') << "\n";
    }
};

// -----------------------------
// Main execution loop
// -----------------------------
int main() {
    try {
        zmq::context_t context(1);

        // Socket to RECEIVE signals from Python
        zmq::socket_t receiver(context, zmq::socket_type::pull);
        receiver.bind("tcp://*:5555");

        // Socket to SEND confirmations TO Python
        zmq::socket_t sender(context, zmq::socket_type::push);
        sender.connect("tcp://localhost:5556");

        std::cout << "\n╔══════════════════════════════════════════════════════════════════╗\n"
                  << "║   C++ EXECUTION ENGINE WITH PYTHON CONFIRMATIONS                ║\n"
                  << "╚══════════════════════════════════════════════════════════════════╝\n\n";

        ExecutionEngine engine(100000.0, sender);

        std::cout << std::fixed << std::setprecision(2);

        while (true) {
            zmq::message_t message;
            auto result = receiver.recv(message, zmq::recv_flags::none);

            if (!result) {
                std::cerr << "❌ Failed to receive message\n";
                continue;
            }

            std::string msg_str(static_cast<char*>(message.data()), message.size());
            try {
                auto j = nlohmann::json::parse(msg_str);
                engine.on_signal(j["action"], j["price"], j["time"]);
            } catch (const std::exception& e) {
                std::cerr << "❌ Error processing message: " << e.what() << "\n";
            }
        }

        engine.print_summary();

    } catch (const zmq::error_t& e) {
        std::cerr << "❌ ZeroMQ error: " << e.what() << "\n";
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "❌ Unexpected error: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
