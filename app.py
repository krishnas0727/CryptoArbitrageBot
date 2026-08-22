import os
import sys

# Ensure Windows stdout handles UTF-8 emojis cleanly
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask, render_template, jsonify, request

import config

from arbitrage import (
    analyze_market,
    execute_paper_trade
)

from database import (
    get_all_trades,
    get_latest_trade,
    create_database,
    get_portfolio,
    reset_portfolio,
    get_total_profit,
    get_total_trades
)


import threading
import time

app = Flask(__name__)


# =====================================================
# DATABASE
# =====================================================

create_database()


_auto_trader_started = False

def start_background_auto_trader():
    global _auto_trader_started
    if _auto_trader_started:
        return
    _auto_trader_started = True

    def auto_trader_loop():
        global last_background_trade_result
        print("🤖 Background Auto-Trader Thread Started...", flush=True)
        while True:
            try:
                if getattr(config, "AUTO_TRADE_ENABLED", False) is True:
                    data = analyze_market()
                    if data and data.get("net_profit", 0) >= getattr(config, "MIN_PROFIT", 0.01):
                        res = execute_paper_trade(data)
                        if res and res.get("success"):
                            last_background_trade_result = res
                            trade = res.get("trade", {})
                            print(f"⚡ [Background Auto-Trader] Executed: {trade.get('buy_exchange')} ➔ {trade.get('sell_exchange')} | Profit: +${trade.get('profit', 0):.2f} USDT", flush=True)
            except Exception as e:
                print(f"⚠️ [Background Auto-Trader] Error: {e}", flush=True)

            time.sleep(getattr(config, "REFRESH_INTERVAL", 3))

    thread = threading.Thread(target=auto_trader_loop, daemon=True)
    thread.start()

start_background_auto_trader()


# =====================================================
# DASHBOARD & SPA TAB ROUTES
# =====================================================

@app.route("/")
@app.route("/prices")
@app.route("/arbitrage")
@app.route("/trades")
@app.route("/settings")
def home():
    return render_template("index.html")


# =====================================================
# PORTFOLIO API - GET & RESET
# =====================================================

@app.route("/api/portfolio", methods=["GET"])
def get_portfolio_api():
    try:
        from exchange import get_all_live_balances
        portfolio = get_all_live_balances()
    except Exception:
        portfolio = get_portfolio()

    return jsonify({

        "success": True,

        "portfolio": portfolio,

        "total_profit": get_total_profit(),

        "total_trades": get_total_trades()

    })


@app.route("/api/portfolio/reset", methods=["POST"])
def reset_portfolio_api():
    from database import delete_all_trades, reset_portfolio, get_portfolio
    delete_all_trades()
    reset_portfolio(0.00)

    return jsonify({
        "success": True,
        "message": "Wallet balance reset to $0.00 USDT.",
        "portfolio": get_portfolio()
    })


# =====================================================
# MANUAL TRADE API
# =====================================================

@app.route("/api/trade", methods=["POST"])
def manual_trade_api():

    data = request.get_json() or {}

    custom_amount = data.get("trade_amount")

    if custom_amount:
        try:
            custom_amount = float(custom_amount)
            if custom_amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid trade amount."
            }), 400

    market_data = analyze_market()

    if not market_data:
        return jsonify({
            "success": False,
            "message": "Unable to fetch live prices for execution."
        }), 503

    result = execute_paper_trade(market_data, custom_amount=custom_amount, is_manual=True)

    if result.get("success"):
        return jsonify({
            "success": True,
            "message": "Manual trade executed successfully!",
            "trade": result["trade"],
            "summary": result["summary"]
        })

    return jsonify({
        "success": False,
        "message": result.get("message", "Execution failed.")
    }), 400


# =====================================================
# SETTINGS API - GET
# =====================================================

@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify({
        "success": True,
        "settings": {
            "auto_trade": config.AUTO_TRADE_ENABLED,
            "min_profit": config.MIN_PROFIT,
            "trade_amount": getattr(config, "DEFAULT_TRADE_AMOUNT", 1000.0),
            "slippage_enabled": getattr(config, "SLIPPAGE_ENABLED", True),
            "slippage_pct": getattr(config, "SLIPPAGE_PCT", 0.05),
            "cooldown": getattr(config, "AUTO_TRADE_COOLDOWN", 30),
            "symbol": getattr(config, "SYMBOL", "BTC/USDT"),
            "trading_mode": getattr(config, "TRADING_MODE", "PAPER")
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
            "message": "No settings received."
        }), 400

    if "auto_trade" in data:
        config.AUTO_TRADE_ENABLED = bool(data["auto_trade"])

    if "min_profit" in data:
        try:
            val = float(data["min_profit"])
            if val >= 0:
                config.MIN_PROFIT = val
        except (ValueError, TypeError):
            pass

    if "trade_amount" in data:
        try:
            val = float(data["trade_amount"])
            if val > 0:
                config.DEFAULT_TRADE_AMOUNT = val
        except (ValueError, TypeError):
            pass

    if "slippage_enabled" in data:
        config.SLIPPAGE_ENABLED = bool(data["slippage_enabled"])

    if "slippage_pct" in data:
        try:
            val = float(data["slippage_pct"])
            if val >= 0:
                config.SLIPPAGE_PCT = val
        except (ValueError, TypeError):
            pass

    if "cooldown" in data:
        try:
            val = int(data["cooldown"])
            if val >= 0:
                config.AUTO_TRADE_COOLDOWN = val
        except (ValueError, TypeError):
            pass

    if "symbol" in data and data["symbol"]:
        config.SYMBOL = str(data["symbol"]).strip()

    if "trading_mode" in data:
        if data["trading_mode"] in ["PAPER", "LIVE", "TESTNET"]:
            config.TRADING_MODE = data["trading_mode"]

    return jsonify({
        "success": True,
        "message": "Settings updated successfully.",
        "settings": {
            "auto_trade": config.AUTO_TRADE_ENABLED,
            "min_profit": config.MIN_PROFIT,
            "trade_amount": getattr(config, "DEFAULT_TRADE_AMOUNT", 1000.0),
            "slippage_enabled": getattr(config, "SLIPPAGE_ENABLED", True),
            "slippage_pct": getattr(config, "SLIPPAGE_PCT", 0.05),
            "cooldown": getattr(config, "AUTO_TRADE_COOLDOWN", 30),
            "symbol": getattr(config, "SYMBOL", "BTC/USDT"),
            "trading_mode": getattr(config, "TRADING_MODE", "PAPER")
        }
    })


# =====================================================
# API KEYS MANAGEMENT & CONNECTION TESTING
# =====================================================

@app.route("/api/keys", methods=["GET"])
def get_keys_api():
    from database import get_all_api_keys
    return jsonify({
        "success": True,
        "keys": get_all_api_keys()
    })


@app.route("/api/keys", methods=["POST"])
def save_key_api():
    from database import save_api_key
    data = request.get_json() or {}
    exchange = data.get("exchange")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")

    if not exchange or not api_key or not api_secret:
        return jsonify({
            "success": False,
            "message": "Exchange, API Key, and API Secret are required."
        }), 400

    save_api_key(exchange, api_key, api_secret)
    return jsonify({
        "success": True,
        "message": f"API key for {exchange} saved successfully!"
    })


@app.route("/api/keys/delete", methods=["POST"])
def delete_key_api():
    from database import delete_api_key
    data = request.get_json() or {}
    exchange = data.get("exchange")

    if not exchange:
        return jsonify({"success": False, "message": "Exchange name required."}), 400

    delete_api_key(exchange)
    return jsonify({
        "success": True,
        "message": f"API key for {exchange} removed."
    })


@app.route("/api/keys/test", methods=["POST"])
def test_key_api():
    from exchange import test_exchange_connection
    from database import save_api_key
    data = request.get_json() or {}
    exchange = data.get("exchange")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")

    if not exchange:
        return jsonify({"success": False, "message": "Exchange name required."}), 400

    if api_key and api_secret:
        save_api_key(exchange, api_key, api_secret)

    res = test_exchange_connection(exchange)
    return jsonify(res)



# =====================================================
# MARKET API + AUTOMATIC PAPER TRADING
# =====================================================

@app.route("/api/market")
def market_data():

    data = analyze_market()

    if data is None:

        return jsonify({

            "success": False,

            "message": "Unable to fetch enough exchange prices."

        }), 503


    mode = getattr(config, "TRADING_MODE", "PAPER")
    if mode == "LIVE":
        try:
            from exchange import get_all_live_balances
            portfolio = get_all_live_balances()
        except Exception:
            portfolio = get_portfolio()
    else:
        portfolio = get_portfolio()

    total_profit = get_total_profit()
    total_trades = get_total_trades()


    return jsonify({

        "success": True,

        "data": data,

        "summary": {

            "balance": round(portfolio.get("usdt_balance", 10000.0), 2),

            "profit": total_profit,

            "trades": total_trades,

            "portfolio": portfolio

        },

        "settings": {

            "auto_trade": config.AUTO_TRADE_ENABLED,

            "min_profit": config.MIN_PROFIT,

            "trading_mode": getattr(config, "TRADING_MODE", "PAPER")

        },

        "auto_trade": ({"success": True, "trade": get_latest_trade()} if get_latest_trade() else last_background_trade_result) if getattr(config, "AUTO_TRADE_ENABLED", True) else None

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


@app.route("/api/trades/clear", methods=["POST"])
def clear_trades_api():
    from database import delete_all_trades, reset_portfolio
    delete_all_trades()
    reset_portfolio()
    return jsonify({
        "success": True,
        "message": "All trade history log cleared and paper balance reset successfully."
    })


# =====================================================
# APPLICATION START
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )