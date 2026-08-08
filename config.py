# ==========================================
# CRYPTO ARBITRAGE BOT CONFIGURATION
# ==========================================

# Trading pair
SYMBOL = "BTC/USDT"


# ==========================================
# PAPER TRADING
# ==========================================

INITIAL_BALANCE = 10000.00


# ==========================================
# FEES
# ==========================================

BUY_FEE = 2.00
SELL_FEE = 2.00
TRANSFER_FEE = 3.00


# ==========================================
# AUTO TRADE
# ==========================================

# True  = Automatic paper trading ON
# False = Automatic paper trading OFF

AUTO_TRADE_ENABLED = True


# Minimum net profit required
# before automatic paper trade

MIN_PROFIT = 0.50


# Same exchange pair-ku
# repeated trade prevent panna cooldown

AUTO_TRADE_COOLDOWN = 30


# ==========================================
# MARKET REFRESH
# ==========================================

REFRESH_INTERVAL = 5


# ==========================================
# DATABASE
# ==========================================

DATABASE_NAME = "data/trades.db"