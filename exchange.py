import ccxt
from config import SYMBOL


# ============================================================
# EXCHANGE CONFIGURATION
# ============================================================

exchanges = {
    "Binance": ccxt.binance({
        "enableRateLimit": True,
        "timeout": 10000
    }),

    "Bybit": ccxt.bybit({
        "enableRateLimit": True,
        "timeout": 10000
    }),

    "Kraken": ccxt.kraken({
        "enableRateLimit": True,
        "timeout": 10000
    })
}


# ============================================================
# GET LIVE PRICES
# ============================================================

def get_live_prices():

    prices = {}

    for name, exchange in exchanges.items():

        try:

            ticker = exchange.fetch_ticker(SYMBOL)

            last_price = ticker.get("last")

            if last_price is None:
                print(f"⚠️ {name}: Price unavailable")
                continue

            price = float(last_price)

            if price <= 0:
                print(f"⚠️ {name}: Invalid price {price}")
                continue

            prices[name] = price

            print(
                f"📊 {name}: "
                f"{price:.2f} USDT"
            )

        except ccxt.NetworkError as e:

            print(
                f"🌐 {name} Network Error: {e}"
            )

        except ccxt.ExchangeError as e:

            print(
                f"🏦 {name} Exchange Error: {e}"
            )

        except Exception as e:

            print(
                f"❌ {name} Error: {e}"
            )

    return prices


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print("     LIVE EXCHANGE PRICES")
    print("==============================\n")

    prices = get_live_prices()

    if not prices:

        print(
            "\n❌ No exchange prices available."
        )

    else:

        for exchange, price in prices.items():

            print(
                f"{exchange:10} : "
                f"{price:.2f} USDT"
            )

    print("\n==============================\n")