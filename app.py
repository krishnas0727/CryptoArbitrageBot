from flask import Flask, render_template, jsonify, request

import config

from arbitrage import (
    analyze_market,
    execute_paper_trade
)

from database import (
    get_all_trades,
    create_database
)


app = Flask(__name__)


# =====================================================
# DATABASE
# =====================================================

create_database()


# =====================================================
# AUTO TRADE CONTROL
# =====================================================

# Same exchange pair-ku repeated trade prevent panna
last_auto_trade_pair = None


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
def home():

    return render_template("index.html")


# =====================================================
# LIVE PRICES
# =====================================================

@app.route("/prices")
def prices():

    return render_template("prices.html")


# =====================================================
# ARBITRAGE
# =====================================================

@app.route("/arbitrage")
def arbitrage_page():

    return render_template("arbitrage.html")


# =====================================================
# TRADE HISTORY
# =====================================================

@app.route("/trades")
def trades_page():

    return render_template("trades.html")


# =====================================================
# SETTINGS PAGE
# =====================================================

@app.route("/settings")
def settings_page():

    return render_template("settings.html")


# =====================================================
# SETTINGS API - GET
# =====================================================

@app.route("/api/settings", methods=["GET"])
def get_settings():

    return jsonify({

        "success": True,

        "settings": {

            "auto_trade":
                config.AUTO_TRADE_ENABLED,

            "min_profit":
                config.MIN_PROFIT

        }

    })


# =====================================================
# SETTINGS API - UPDATE
# =====================================================

@app.route("/api/settings", methods=["POST"])
def update_settings():

    data = request.get_json()

    if not data:

        return jsonify({

            "success": False,

            "message":
                "No settings received."

        }), 400


    # =================================================
    # AUTO TRADE
    # =================================================

    if "auto_trade" in data:

        config.AUTO_TRADE_ENABLED = bool(
            data["auto_trade"]
        )


    # =================================================
    # MINIMUM PROFIT
    # =================================================

    if "min_profit" in data:

        try:

            value = float(
                data["min_profit"]
            )

            if value < 0:

                raise ValueError


            config.MIN_PROFIT = value


        except (ValueError, TypeError):

            return jsonify({

                "success": False,

                "message":
                    "Invalid minimum profit."

            }), 400


    # =================================================
    # PRINT SETTINGS
    # =================================================

    print()

    print("==========================================")

    print("⚙ SETTINGS UPDATED")

    print("==========================================")

    print(
        "Auto Trade :",
        config.AUTO_TRADE_ENABLED
    )

    print(
        "Min Profit :",
        config.MIN_PROFIT
    )


    return jsonify({

        "success": True,

        "message":
            "Settings updated successfully.",

        "settings": {

            "auto_trade":
                config.AUTO_TRADE_ENABLED,

            "min_profit":
                config.MIN_PROFIT

        }

    })


# =====================================================
# MARKET API + AUTOMATIC PAPER TRADING
# =====================================================

@app.route("/api/market")
def market_data():

    global last_auto_trade_pair


    # =================================================
    # GET MARKET DATA
    # =================================================

    data = analyze_market()


    if data is None:

        return jsonify({

            "success": False,

            "message":
                "Unable to fetch enough exchange prices."

        }), 503


    # =================================================
    # AUTO TRADE RESULT
    # =================================================

    auto_trade_result = None


    # =================================================
    # CHECK AUTO TRADE SETTINGS
    # =================================================

    if config.AUTO_TRADE_ENABLED:

        # ---------------------------------------------
        # Check minimum profit
        # ---------------------------------------------

        if data["net_profit"] >= config.MIN_PROFIT:

            current_pair = (

                data["buy_exchange"],

                data["sell_exchange"]

            )


            # =========================================
            # NEW OPPORTUNITY
            # =========================================

            if current_pair != last_auto_trade_pair:

                print()

                print(
                    "=========================================="
                )

                print(
                    "🤖 AUTO TRADING"
                )

                print(
                    "=========================================="
                )


                print(
                    "Buy From :",
                    data["buy_exchange"]
                )


                print(
                    "Sell On  :",
                    data["sell_exchange"]
                )


                print(
                    "Buy Price:",
                    data["buy_price"]
                )


                print(
                    "Sell Price:",
                    data["sell_price"]
                )


                print(
                    "Difference:",
                    data["difference"]
                )


                print(
                    "Fees      :",
                    data["fees"]
                )


                print(
                    "Net Profit:",
                    data["net_profit"]
                )


                # =====================================
                # EXECUTE AUTOMATIC PAPER TRADE
                # =====================================

                auto_trade_result = (
                    execute_paper_trade(data)
                )


                # =====================================
                # SUCCESS
                # =====================================

                if auto_trade_result["success"]:

                    last_auto_trade_pair = (
                        current_pair
                    )


                    print()

                    print(
                        "✅ AUTO PAPER TRADE EXECUTED"
                    )

                    print(
                        "✅ TRADE SAVED TO DATABASE"
                    )


                # =====================================
                # FAILED
                # =====================================

                else:

                    print()

                    print(
                        "❌ AUTO TRADE FAILED"
                    )

                    print(
                        auto_trade_result.get(
                            "message",
                            "Unknown error"
                        )
                    )


        # =================================================
        # PROFIT BELOW MINIMUM
        # =================================================

        else:

            # New profitable opportunity varumbothu
            # trade allow panna reset pannrom.

            last_auto_trade_pair = None


    # =================================================
    # AUTO TRADE DISABLED
    # =================================================

    else:

        last_auto_trade_pair = None


    # =================================================
    # API RESPONSE
    # =================================================

    return jsonify({

        "success": True,

        "data": data,

        "settings": {

            "auto_trade":
                config.AUTO_TRADE_ENABLED,

            "min_profit":
                config.MIN_PROFIT

        },

        "auto_trade":
            auto_trade_result

    })


# =====================================================
# TRADE HISTORY API
# =====================================================

@app.route("/api/trades")
def trades_api():

    trade_list = get_all_trades()


    return jsonify({

        "success": True,

        "trades": trade_list

    })


# =====================================================
# APPLICATION START
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )