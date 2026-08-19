import ccxt
import time
from datetime import datetime
import sys
import os

# Ensure Windows stdout handles UTF-8 emojis cleanly
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config
from config import SYMBOL
from database import get_api_key



# ============================================================
# PUBLIC EXCHANGE CONFIGURATION (FOR PRICE MONITORING)
# ============================================================

import urllib.request
import json

proxy_url = os.environ.get("EXCHANGE_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

binance_opts = {"enableRateLimit": True, "timeout": 20000}
bybit_opts = {
    "enableRateLimit": True,
    "timeout": 20000,
    "urls": {
        "api": {
            "public": "https://api.bytick.com",
            "private": "https://api.bytick.com"
        }
    },
    "options": {"defaultType": "spot"}
}
coinbase_opts = {"enableRateLimit": True, "timeout": 20000}

if proxy_url:
    for opts in (binance_opts, bybit_opts, coinbase_opts):
        if "socks" in proxy_url.lower():
            opts["socksProxy"] = proxy_url
        else:
            opts["httpsProxy"] = proxy_url

exchanges = {
    "Binance": ccxt.binance(binance_opts),
    "Bybit": ccxt.bybit(bybit_opts),
    "Coinbase": ccxt.coinbase(coinbase_opts)
}


# ============================================================
# GET AUTHENTICATED EXCHANGE INSTANCE
# ============================================================

def get_authenticated_exchange(name):
    key_info = get_api_key(name)
    if not key_info or not key_info.get("api_key") or not key_info.get("api_secret"):
        return None, f"No API keys configured for {name}."

    exchange_class = getattr(ccxt, name.lower(), None)
    if not exchange_class:
        return None, f"Unsupported exchange: {name}"

    try:
        config_opts = {
            "apiKey": key_info["api_key"],
            "secret": key_info["api_secret"],
            "enableRateLimit": True,
            "timeout": 20000
        }

        # Check for proxy configuration in environment
        proxy_url = os.environ.get("EXCHANGE_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if proxy_url:
            if "socks" in proxy_url.lower():
                config_opts["socksProxy"] = proxy_url
            else:
                config_opts["httpsProxy"] = proxy_url

        if name.lower() == "bybit":
            config_opts["urls"] = {
                "api": {
                    "public": "https://api.bytick.com",
                    "private": "https://api.bytick.com"
                }
            }
            config_opts["options"] = {"defaultType": "spot"}

        ex_instance = exchange_class(config_opts)
        return ex_instance, None
    except Exception as e:
        return None, f"Failed to initialize {name}: {str(e)}"



# ============================================================
# TEST API KEY CONNECTION & FETCH LIVE BALANCE
# ============================================================

def test_exchange_connection(name):
    ex_instance, err = get_authenticated_exchange(name)
    if err:
        return {
            "success": False,
            "message": err
        }

    proxy_url = os.environ.get("EXCHANGE_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    proxy_status = f" [Proxy Active: {proxy_url[:12]}...]" if proxy_url else " [Proxy Active: NO (EXCHANGE_PROXY Env Var missing on Render)]"

    try:
        balance = ex_instance.fetch_balance()
        usdt_free = balance.get("free", {}).get("USDT", 0.0) or balance.get("free", {}).get("USD", 0.0)
        btc_free = balance.get("free", {}).get("BTC", 0.0)

        return {
            "success": True,
            "message": f"Successfully connected to {name}!{proxy_status}",
            "usdt_balance": round(float(usdt_free or 0.0), 2),
            "btc_balance": round(float(btc_free or 0.0), 6)
        }
    except ccxt.AuthenticationError as e:
        return {
            "success": False,
            "message": f"🔑 Authentication Error: Invalid API Key or Secret for {name}.{proxy_status}"
        }
    except ccxt.PermissionDenied as e:
        return {
            "success": False,
            "message": f"🚫 Permission Error: API Key lacks trading/reading permission on {name}.{proxy_status}"
        }
    except (ccxt.NetworkError, ccxt.ExchangeError) as e:
        err_msg = str(e)
        if "restricted location" in err_msg or "451" in err_msg:
            return {
                "success": False,
                "message": f"🌐 Binance Geo-Block (HTTP 451): Render server IP is blocked by Binance.com.{proxy_status} Ensure EXCHANGE_PROXY is set in Render Env Vars & Save Changes was clicked."
            }
        elif "403 Forbidden" in err_msg or "CloudFront" in err_msg or "access from your country" in err_msg:
            return {
                "success": False,
                "message": f"🌐 Bybit Cloud Block (HTTP 403): Bybit CloudFront blocks cloud server IPs.{proxy_status} Ensure EXCHANGE_PROXY is set in Render Env Vars & Save Changes was clicked."
            }
        return {
            "success": False,
            "message": f"🌐 Network Error connecting to {name}: {err_msg}{proxy_status}"
        }
    except Exception as e:
        err_msg = str(e)
        if "restricted location" in err_msg or "451" in err_msg:
            return {
                "success": False,
                "message": f"🌐 Binance Geo-Block (HTTP 451): Render server IP is blocked by Binance.com.{proxy_status} Ensure EXCHANGE_PROXY is set in Render Env Vars & Save Changes was clicked."
            }
        elif "403 Forbidden" in err_msg or "CloudFront" in err_msg or "access from your country" in err_msg:
            return {
                "success": False,
                "message": f"🌐 Bybit Cloud Block (HTTP 403): Bybit CloudFront blocks cloud server IPs.{proxy_status} Ensure EXCHANGE_PROXY is set in Render Env Vars & Save Changes was clicked."
            }
        return {
            "success": False,
            "message": f"❌ {name} Connection Error: {err_msg}{proxy_status}"
        }


def get_direct_price(name, symbol=SYMBOL):
    clean_sym = symbol.replace('/', '')
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    if name.lower() == "binance":
        for url in [
            f"https://data-api.binance.vision/api/v3/ticker/price?symbol={clean_sym}",
            f"https://api.binance.us/api/v3/ticker/price?symbol={clean_sym}",
            f"https://api.binance.com/api/v3/ticker/price?symbol={clean_sym}"
        ]:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                res = json.loads(urllib.request.urlopen(req, context=ctx, timeout=6).read())
                if 'price' in res and float(res['price']) > 0:
                    return float(res['price'])
            except Exception:
                continue

    elif name.lower() == "bybit":
        # 1. Try Bybit Kline V5 API (unblocked on cloud servers)
        for base_url in ["https://api.bybit.com", "https://api.bytick.com"]:
            try:
                url = f"{base_url}/v5/market/kline?category=spot&symbol={clean_sym}&interval=1&limit=1"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                res = json.loads(urllib.request.urlopen(req, context=ctx, timeout=6).read())
                k_list = res.get('result', {}).get('list', [])
                if k_list and len(k_list[0]) >= 5:
                    close_price = float(k_list[0][4])
                    if close_price > 0:
                        return close_price
            except Exception:
                continue

        # 2. Try Bybit Tickers V5 API
        for base_url in ["https://api.bybit.com", "https://api.bytick.com"]:
            try:
                url = f"{base_url}/v5/market/tickers?category=spot&symbol={clean_sym}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                res = json.loads(urllib.request.urlopen(req, context=ctx, timeout=6).read())
                tickers = res.get('result', {}).get('list', [])
                if tickers and 'lastPrice' in tickers[0] and float(tickers[0]['lastPrice']) > 0:
                    return float(tickers[0]['lastPrice'])
            except Exception:
                continue

        # 3. Gate.io Fallback for spot price
        try:
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={clean_sym[:3]}_{clean_sym[3:]}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            res = json.loads(urllib.request.urlopen(req, context=ctx, timeout=6).read())
            if res and isinstance(res, list) and 'last' in res[0]:
                return float(res[0]['last'])
        except Exception:
            pass

    elif name.lower() == "coinbase":
        base_coin = symbol.split('/')[0]
        try:
            url = f"https://api.coinbase.com/v2/prices/{base_coin}-USD/spot"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            res = json.loads(urllib.request.urlopen(req, context=ctx, timeout=6).read())
            if 'data' in res and 'amount' in res['data']:
                return float(res['data']['amount'])
        except Exception:
            pass

    return None


import concurrent.futures

def fetch_single_exchange_price(name_and_exchange):
    name, exchange = name_and_exchange
    fetched_price = None

    # 1. Direct REST Endpoint Fast-Track (fastest for cloud servers)
    direct_p = get_direct_price(name, SYMBOL)
    if direct_p and direct_p > 0:
        fetched_price = direct_p

    # 2. CCXT Fallback if direct REST endpoint didn't return
    if fetched_price is None:
        try:
            ticker = exchange.fetch_ticker(SYMBOL)
            last_price = ticker.get("last")
            if last_price and float(last_price) > 0:
                fetched_price = float(last_price)
        except Exception:
            pass

    return name, fetched_price


# ============================================================
# GET LIVE PRICES
# ============================================================

def get_live_prices():

    prices = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(fetch_single_exchange_price, exchanges.items()))

    for name, fetched_price in results:
        if fetched_price and fetched_price > 0:
            prices[name] = round(fetched_price, 2)
            print(f"📊 {name}: {prices[name]:.2f} USDT")
        else:
            print(f"⚠️ {name}: Price unavailable")

    return prices



# ============================================================
# EXECUTE LIVE REAL TRADE ON EXCHANGES
# ============================================================

def execute_live_real_trade(buy_exchange_name, sell_exchange_name, buy_price, sell_price, trade_amount=1000.0):
    # 1. Instantiate Buy Exchange
    buy_ex, buy_err = get_authenticated_exchange(buy_exchange_name)
    if buy_err:
        return {
            "success": False,
            "message": buy_err
        }

    # 2. Instantiate Sell Exchange
    sell_ex, sell_err = get_authenticated_exchange(sell_exchange_name)
    if sell_err:
        return {
            "success": False,
            "message": sell_err
        }

    # 3. Balance verification on Buy Exchange & Dynamic Sizing
    try:
        buy_balance = buy_ex.fetch_balance()
        free_usdt = float(buy_balance.get("free", {}).get("USDT", 0.0) or buy_balance.get("free", {}).get("USD", 0.0) or 0.0)

        min_required = getattr(config, "MIN_TRADE_USDT", 5.0)
        if free_usdt < min_required:
            return {
                "success": False,
                "message": f"Insufficient USDT on {buy_exchange_name}. Required minimum: ${min_required:.2f}, Available: ${free_usdt:.2f}"
            }

        # Dynamic Sizing: Auto-adjust trade amount to available USDT balance (leaving 2% buffer for fees/slippage)
        if getattr(config, "DYNAMIC_BALANCE_TRADING", True):
            trade_amount = round(min(trade_amount, free_usdt * 0.98), 2)
            print(f"💰 Dynamic Trade Amount set to ${trade_amount:.2f} USDT (Available: ${free_usdt:.2f} USDT)")

    except Exception as e:
        return {
            "success": False,
            "message": f"Unable to verify USDT balance on {buy_exchange_name}: {str(e)}"
        }


    # 4. Calculate Quantity
    btc_amount = round(trade_amount / buy_price, 5)

    # 5. Place BUY Order on Buy Exchange
    try:
        print(f"🚀 Submitting REAL BUY order on {buy_exchange_name} for {btc_amount} BTC...")
        buy_order = buy_ex.create_market_buy_order(SYMBOL, btc_amount)
        buy_order_id = buy_order.get("id") or f"LIVE-BUY-{int(time.time())}"
        effective_buy_price = float(buy_order.get("price") or buy_price)
    except ccxt.InsufficientFunds as e:
        return {"success": False, "message": f"Insufficient funds on {buy_exchange_name}: {str(e)}"}
    except ccxt.ExchangeError as e:
        return {"success": False, "message": f"Exchange error on {buy_exchange_name}: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to execute BUY order on {buy_exchange_name}: {str(e)}"}

    # 6. Place SELL Order on Sell Exchange
    try:
        print(f"🚀 Submitting REAL SELL order on {sell_exchange_name} for {btc_amount} BTC...")
        sell_order = sell_ex.create_market_sell_order(SYMBOL, btc_amount)
        sell_order_id = sell_order.get("id") or f"LIVE-SELL-{int(time.time())}"
        effective_sell_price = float(sell_order.get("price") or sell_price)
    except Exception as e:
        print(f"⚠️ SELL ORDER FAILED on {sell_exchange_name}: {str(e)}")
        return {
            "success": False,
            "message": f"⚠️ BUY Order Filled on {buy_exchange_name} (ID: {buy_order_id}), BUT SELL Order Failed on {sell_exchange_name}: {str(e)}"
        }

    # 7. Calculate real fees & profit
    buy_fee = round(trade_amount * 0.001, 2)
    sell_fee = round((btc_amount * effective_sell_price) * 0.001, 2)
    total_fees = round(buy_fee + sell_fee, 2)
    net_profit = round((btc_amount * effective_sell_price) - trade_amount - total_fees, 2)

    return {
        "success": True,
        "message": f"LIVE TRADE EXECUTED: Buy on {buy_exchange_name}, Sell on {sell_exchange_name}.",
        "trade": {
            "buy": buy_exchange_name,
            "sell": sell_exchange_name,
            "buy_exchange": buy_exchange_name,
            "sell_exchange": sell_exchange_name,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "effective_buy_price": effective_buy_price,
            "effective_sell_price": effective_sell_price,
            "fees": total_fees,
            "profit": net_profit,
            "buy_order_id": buy_order_id,
            "sell_order_id": sell_order_id,
            "btc_amount": btc_amount,
            "slippage": 0.0,
            "trade_amount": trade_amount,
            "created_at": datetime.now().astimezone().isoformat(),
            "mode": "LIVE"
        }
    }


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