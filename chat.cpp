#include <iostream>
#include <string>

struct Trade {
    std::string action;
    double price;
    int units;
};

int main() {
    double cash = 100000.0;   // starting cash
    int position = 0;          // starting position
    double last_price = 87641; // starting price

    std::string line;
    while (std::getline(std::cin, line)) {
        // Format: ACTION,PRICE
        size_t pos = line.find(',');
        std::string action = line.substr(0, pos);
        double price = std::stod(line.substr(pos + 1));
        int units = 1; // for simplicity, buy/sell 1 unit per signal

        if (action == "BUY") {
            if (cash >= price * units) {
                cash -= price * units;
                position += units;
            } else {
                std::cout << "Not enough cash to buy.\n";
                continue;
            }
        } else if (action == "SELL") {
            if (position >= units) {
                cash += price * units;
                position -= units;
            } else {
                std::cout << "Not enough position to sell.\n";
                continue;
            }
        }

        last_price = price;
        double portfolio_value = cash + position * last_price;

        std::cout << action << " " << units << " @ " << price 
                  << " | Cash: " << cash 
                  << " | Position: " << position 
                  << " | Portfolio: " << portfolio_value << std::endl;
        std::cout.flush();
    }

    return 0;
}
