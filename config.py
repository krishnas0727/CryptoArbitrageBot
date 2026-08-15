# ==========================================
# CRYPTO ARBITRAGE BOT CONFIGURATION
# ==========================================

# Trading pair
SYMBOL = "BTC/USDT"


# ==========================================
# PAPER TRADING & EXECUTION
# ==========================================

INITIAL_BALANCE = 10000.00
DEFAULT_TRADE_AMOUNT = 1000.00  # USDT max per trade
DYNAMIC_BALANCE_TRADING = True  # Auto-adjust trade amount to available USDT balance
MIN_TRADE_USDT = 5.0            # Minimum USDT required to execute a live trade
SLIPPAGE_ENABLED = True
SLIPPAGE_PCT = 0.02            # 0.02% order book impact
MAKER_TAKER_FEE_PCT = 0.05     # 0.05% per trade (standard exchange fee)
TRADING_MODE = "PAPER"         # "PAPER", "LIVE", or "TESTNET"



# ==========================================
# FEES (FLAT FALLBACK / TRANSFER)
# ==========================================

BUY_FEE = 0.50
SELL_FEE = 0.50
TRANSFER_FEE = 0.20


# ==========================================
# AUTO TRADE
# ==========================================

# True  = Automatic paper trading ON
# False = Automatic paper trading OFF

AUTO_TRADE_ENABLED = True


# Minimum net profit required
# before automatic paper trade

MIN_PROFIT = 0.10
AUTO_TRADE_COOLDOWN = 10
REFRESH_INTERVAL = 2


# ==========================================
# DATABASE
# ==========================================

DATABASE_NAME = "data/trades.db"