import sqlite3
import os

from config import DATABASE_NAME


# ============================================================
# DATABASE FOLDER
# ============================================================

os.makedirs(
    os.path.dirname(DATABASE_NAME),
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            buy_exchange TEXT NOT NULL,

            sell_exchange TEXT NOT NULL,

            buy_price REAL NOT NULL,

            sell_price REAL NOT NULL,

            fees REAL NOT NULL,

            profit REAL NOT NULL,

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()

    conn.close()


# ============================================================
# SAVE TRADE
# ============================================================

def save_trade(trade):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trades
        (
            buy_exchange,
            sell_exchange,
            buy_price,
            sell_price,
            fees,
            profit
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        trade["buy"],

        trade["sell"],

        float(
            trade["buy_price"]
        ),

        float(
            trade["sell_price"]
        ),

        float(
            trade["fees"]
        ),

        float(
            trade["profit"]
        )

    ))

    conn.commit()

    conn.close()


# ============================================================
# GET ALL TRADES
# ============================================================

def get_all_trades():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            id,

            buy_exchange,

            sell_exchange,

            buy_price,

            sell_price,

            fees,

            profit,

            created_at

        FROM trades

        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# DELETE ALL TRADES
# ============================================================

def delete_all_trades():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM trades
    """)

    conn.commit()

    conn.close()

    print(
        "✅ All old trades deleted"
    )


# ============================================================
# TOTAL PROFIT
# ============================================================

def get_total_profit():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(
                SUM(profit),
                0
            )
        FROM trades
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return round(
        float(result),
        2
    )


# ============================================================
# TOTAL TRADES
# ============================================================

def get_total_trades():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*)
        FROM trades
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return int(result)