import json
import os
import time

HISTORY_FILE = "trade_history.json"

def current_time_utc():
    return time.strftime('%d.%m.%Y %H:%M UTC', time.gmtime())

def load_trade_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        try:
            content = f.read().strip()
            return json.loads(content) if content else []
        except json.JSONDecodeError:
            print("⚠️ Файл trade_history.json повреждён или пуст. Очищаем историю.")
            return []

def save_trade_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def add_trade_to_history(trade):
    history = load_trade_history()
    history.append(trade)
    save_trade_history(history)
    print(f"✅ Добавлена сделка в историю. Текущий объём истории: {len(history)}")

def get_success_probability(symbol):
    history = load_trade_history()
    symbol_trades = [t for t in history if t.get("symbol") == symbol]
    total = len(symbol_trades)
    if total == 0:
        return "Недостаточно данных"
    success = sum(1 for t in symbol_trades if t.get("pnl", 0) > 0)
    probability = round(success / total * 100, 2)
    return f"{probability}% (на основе {total} сделок)"
