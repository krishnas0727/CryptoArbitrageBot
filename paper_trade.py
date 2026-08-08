class PaperTrader:

    def __init__(self, balance=10000):

        self.balance = balance

        self.total_profit = 0

        self.total_trades = 0


    def execute_trade(
        self,
        buy_exchange,
        sell_exchange,
        buy_price,
        sell_price,
        fees
    ):

        # ==========================================
        # PAPER BUY
        # ==========================================

        buy_order = {

            "exchange": buy_exchange,

            "price": buy_price,

            "status": "FILLED"

        }


        # ==========================================
        # PAPER SELL
        # ==========================================

        sell_order = {

            "exchange": sell_exchange,

            "price": sell_price,

            "status": "FILLED"

        }


        # ==========================================
        # PROFIT
        # ==========================================

        profit = (
            sell_price
            - buy_price
            - fees
        )


        self.balance += profit

        self.total_profit += profit

        self.total_trades += 1


        # ==========================================
        # TRADE RESULT
        # ==========================================

        trade = {

            "buy": buy_exchange,

            "sell": sell_exchange,

            "buy_price": buy_price,

            "sell_price": sell_price,

            "fees": fees,

            "profit": round(profit, 2),

            "buy_order": buy_order,

            "sell_order": sell_order

        }


        return trade


    def summary(self):

        return {

            "balance": round(
                self.balance,
                2
            ),

            "profit": round(
                self.total_profit,
                2
            ),

            "trades": self.total_trades

        }