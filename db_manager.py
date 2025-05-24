import psycopg2
import json
import config

DATABASE_URL = config.DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            entry_price REAL,
            amount REAL,
            leverage INTEGER,
            status TEXT,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tp_levels TEXT,
            tp_percents TEXT,
            sl_percent REAL,
            trailing_stop BOOLEAN,
            trailing_percent REAL,
            balance_at_open REAL
        );
    ''')
    conn.commit()
    conn.close()

def save_trade(trade):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO trades (symbol, side, entry_price, amount, leverage, status, opened_at,
                            tp_levels, tp_percents, sl_percent, trailing_stop, trailing_percent, balance_at_open)
        VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s), %s, %s, %s, %s, %s, %s);
    ''', (
        trade["symbol"],
        trade["side"],
        trade["entry_price"],
        trade["amount"],
        trade["leverage"],
        trade["status"],
        trade["opened_at"],
        json.dumps(trade.get("tp_levels", [])),
        json.dumps(trade.get("tp_percents", [])),
        trade.get("sl_percent", 0),
        trade.get("trailing_stop", False),
        trade.get("trailing_percent", 0),
        trade.get("balance_at_open", 0)
    ))
    conn.commit()
    conn.close()

def load_open_trades():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT symbol, side, entry_price, amount, leverage, status, EXTRACT(EPOCH FROM opened_at),
               tp_levels, tp_percents, sl_percent, trailing_stop, trailing_percent, balance_at_open
        FROM trades WHERE status = 'open';
    ''')
    rows = cur.fetchall()
    conn.close()

    trades = []
    for row in rows:
        trade = {
            "symbol": row[0],
            "side": row[1],
            "entry_price": row[2],
            "amount": row[3],
            "leverage": row[4],
            "status": row[5],
            "opened_at": row[6],
            "tp_levels": json.loads(row[7]) if row[7] else [],
            "tp_percents": json.loads(row[8]) if row[8] else [],
            "sl_percent": row[9],
            "trailing_stop": row[10],
            "trailing_percent": row[11],
            "balance_at_open": row[12]
        }
        trades.append(trade)
    return trades

# Новый метод для удаления сделки после закрытия
def close_trade(symbol):
    conn = get_connection()
    cur = conn.cursor()
    # Полностью удаляем сделку, а не просто обновляем статус
    cur.execute("DELETE FROM trades WHERE symbol = %s AND status = 'open';", (symbol,))
    conn.commit()
    conn.close()

def close_trade_db(symbol):  # Совместимость с simulator
    close_trade(symbol)
