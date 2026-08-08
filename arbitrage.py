from exchange import get_live_prices
from paper_trade import PaperTrader
from database import create_database, save_trade

import config
import time


# ============================================================
# AUTO TRADE CONTROL
# ============================================================

last_trade_time = 0
last_trade_key = None


# ============================================================
# ANALYZE MARKET
# ============================================================

def analyze_market():

    prices = get_live_prices()

    if len(prices) < 2:
        return None

    # Lowest price = BUY
    buy_exchange = min(
        prices,
        key=prices.get
    )

    # Highest price = SELL
    sell_exchange = max(
        prices,
        key=prices.get
    )

    buy_price = prices[buy_exchange]
    sell_price = prices[sell_exchange]

    # Price difference
    difference = sell_price - buy_price

    # Total fees
    total_fees = (
        config.BUY_FEE
        + config.SELL_FEE
        + config.TRANSFER_FEE
    )

    # Net profit
    net_profit = difference - total_fees

    return {

        "prices": prices,

        "buy_exchange": buy_exchange,

        "sell_exchange": sell_exchange,

        "buy_price": round(
            buy_price,
            2
        ),

        "sell_price": round(
            sell_price,
            2
        ),

        "difference": round(
            difference,
            2
        ),

        "fees": round(
            total_fees,
            2
        ),

        "net_profit": round(
            net_profit,
            2
        ),

        "minimum_profit":
            config.MIN_PROFIT,

        "auto_trade_enabled":
            config.AUTO_TRADE_ENABLED

    }


# ============================================================
# AUTOMATIC PAPER TRADE
# ============================================================

def execute_paper_trade(market_data):

    global last_trade_time
    global last_trade_key

    # --------------------------------------------------------
    # Market data check
    # --------------------------------------------------------

    if not market_data:

        return {
            "success": False,
            "message": "Market data unavailable."
        }


    # --------------------------------------------------------
    # AUTO TRADE CHECK
    # --------------------------------------------------------

    if not config.AUTO_TRADE_ENABLED:

        return {
            "success": False,
            "message":
                "Automatic trading is disabled."
        }


    # --------------------------------------------------------
    # MINIMUM PROFIT CHECK
    # --------------------------------------------------------

    if (
        market_data["net_profit"]
        < config.MIN_PROFIT
    ):

        return {

            "success": False,

            "message":
                f"Profit "
                f"{market_data['net_profit']:.2f} "
                f"is below minimum "
                f"{config.MIN_PROFIT:.2f} USDT."

        }


    # --------------------------------------------------------
    # CURRENT TIME
    # --------------------------------------------------------

    current_time = time.time()


    # --------------------------------------------------------
    # CREATE OPPORTUNITY KEY
    # --------------------------------------------------------

    trade_key = (

        market_data["buy_exchange"],

        market_data["sell_exchange"]

    )


    # --------------------------------------------------------
    # COOLDOWN CHECK
    # --------------------------------------------------------

    if (

        trade_key == last_trade_key

        and

        current_time - last_trade_time
        < config.AUTO_TRADE_COOLDOWN

    ):

        remaining = int(

            config.AUTO_TRADE_COOLDOWN
            -
            (
                current_time
                -
                last_trade_time
            )

        )

        return {

            "success": False,

            "message":
                f"Cooldown active. "
                f"Wait {remaining}s."

        }


    # --------------------------------------------------------
    # CREATE DATABASE
    # --------------------------------------------------------

    create_database()


    # --------------------------------------------------------
    # CREATE PAPER TRADER
    # --------------------------------------------------------

    trader = PaperTrader(

        balance=config.INITIAL_BALANCE

    )


    # --------------------------------------------------------
    # EXECUTE PAPER TRADE
    # --------------------------------------------------------

    trade = trader.execute_trade(

        market_data["buy_exchange"],

        market_data["sell_exchange"],

        market_data["buy_price"],

        market_data["sell_price"],

        market_data["fees"]

    )


    # --------------------------------------------------------
    # SAVE TRADE
    # --------------------------------------------------------

    save_trade(trade)


    # --------------------------------------------------------
    # UPDATE COOLDOWN
    # --------------------------------------------------------

    last_trade_time = current_time

    last_trade_key = trade_key


    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {

        "success": True,

        "message":
            "Automatic paper trade executed.",

        "trade": trade,

        "summary": {

            "balance":
                round(
                    trader.balance,
                    2
                ),

            "profit":
                round(
                    trader.total_profit,
                    2
                ),

            "trades":
                trader.total_trades

        }

    }


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    data = analyze_market()

    if data:

        print()
        print(
            "========== ARBITRAGE ANALYSIS =========="
        )
        print()

        print(
            f"Buy From       : "
            f"{data['buy_exchange']}"
        )

        print(
            f"Buy Price      : "
            f"{data['buy_price']:.2f} USDT"
        )

        print()

        print(
            f"Sell On        : "
            f"{data['sell_exchange']}"
        )

        print(
            f"Sell Price     : "
            f"{data['sell_price']:.2f} USDT"
        )

        print()

        print(
            f"Difference     : "
            f"{data['difference']:.2f} USDT"
        )

        print(
            f"Total Fees     : "
            f"{data['fees']:.2f} USDT"
        )

        print(
            f"Minimum Profit : "
            f"{data['minimum_profit']:.2f} USDT"
        )

        print(
            f"Net Profit     : "
            f"{data['net_profit']:.2f} USDT"
        )

        print()

        if (
            config.AUTO_TRADE_ENABLED
            and
            data["net_profit"]
            >= config.MIN_PROFIT
        ):

            print(
                "🟢 AUTO TRADE OPPORTUNITY"
            )

        else:

            print(
                "🔴 NO AUTO TRADE"
            )