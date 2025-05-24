import asyncio
import time
import requests
import config  # ← обязательно до использования config.MODE

if config.MODE == "live":
    from bybit_trader import BybitTrader as Trader
else:
    from simulator import TradeSimulator as Trader

from telegram_bot import send_telegram_message
from messages import get_message
from message_formatter import format_open_message, format_close_message
from smma_filter import smma_filter
import db_manager
import telegram_control  # Для управления через Telegram
from pybit.unified_trading import HTTP
import os

def fetch_bybit_symbols():
    print("[Bybit] 🔄 Загрузка списка фьючерсных пар...")
    session = HTTP(
        api_key=os.getenv("BYBIT_API_KEY"),
        api_secret=os.getenv("BYBIT_API_SECRET"),
        testnet=False
    )
    try:
        response = session.get_tickers(category="linear")
        symbols_data = response["result"]["list"]
        symbols = [s["symbol"] for s in symbols_data if "USDT" in s["symbol"]]
        print(f"[Bybit] ✅ Загружено {len(symbols)} пар")
        return symbols
    except Exception as e:
        print(f"[Bybit] ⚠️ Ошибка загрузки пар: {e}")
        return config.SYMBOLS

simulator = Trader(config.DEPOSIT)
if config.MODE == "live":
    balance, available = simulator.get_account_balance()
    print(f"🚀 Подключён к LIVE. Баланс на Bybit: {balance:.2f} USDT (доступно: {available:.2f})")

telegram_control.simulator = simulator

last_alert_time = {}
base_prices = {}
last_volumes = {}
last_directions = {}
closes_history = {}

def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def fetch_all_prices():
    print("[Bybit] 📈 Получение цен и объёмов...")
    session = HTTP(
        api_key=os.getenv("BYBIT_API_KEY"),
        api_secret=os.getenv("BYBIT_API_SECRET"),
        testnet=False
    )
    try:
        response = session.get_tickers(category="linear")
        data = response["result"]["list"]
        return {
            item["symbol"]: (float(item["lastPrice"]), float(item["turnover24h"]))
            for item in data if "USDT" in item["symbol"]
        }
    except Exception as e:
        print(f"[Bybit] ❌ Ошибка получения цен: {e}")
        return {}

def calculate_price_change(base_price, current_price):
    return ((current_price - base_price) / base_price) * 100

async def print_open_trade_status():
    open_trades = simulator.get_open_trades()
    print(f"📊 Открытых сделок: {len(open_trades)} / {config.MAX_OPEN_TRADES}")
    return len(open_trades)

async def monitor_market():
    print(get_message("bot_started"))

    restored_trades = simulator.get_open_trades()
    restored_count = len(restored_trades)
    if restored_count > 0:
        print(get_message("restored_trades", count=restored_count))

    for trade in restored_trades:
        print(get_message("monitoring_trade", symbol=trade["symbol"]))

    while True:
        start_market_scan = time.time()
        prices = fetch_all_prices()
        symbols = fetch_bybit_symbols()
        chunks = list(chunk_list(symbols, 100))

        scanned_symbols = []

        for current_chunk in chunks:
            for symbol in current_chunk:
                if getattr(config, "TRADING_PAUSED", False):
                    await asyncio.sleep(1)
                    continue

                scanned_symbols.append(symbol)

                try:
                    if config.USE_SECOND_SMMA_LOGIC:
                        await active_logic(simulator, prices, base_prices, last_alert_time)
                        break
                    else:
                        if len(simulator.get_open_trades()) >= config.MAX_OPEN_TRADES:
                            print(get_message("max_open_trades", limit=config.MAX_OPEN_TRADES))
                            continue

                        new_price, new_volume = prices.get(symbol, (None, None))

                        if new_price is None:
                            print(get_message("error_processing", symbol=symbol, error="Нет цены"))
                            continue

                        if symbol not in last_alert_time:
                            last_alert_time[symbol] = time.time()
                        if symbol not in closes_history:
                            closes_history[symbol] = []

                        closes_history[symbol].append(new_price)
                        if len(closes_history[symbol]) > config.SMMA_LENGTH:
                            closes_history[symbol] = closes_history[symbol][-config.SMMA_LENGTH:]

                        if symbol not in base_prices:
                            base_prices[symbol] = new_price

                        old_price = base_prices[symbol]
                        volume_usdt = new_volume * new_price
                        price_change = calculate_price_change(old_price, new_price)

                        print(get_message("price_check", symbol=symbol, price_change=price_change, volume_usdt=volume_usdt, base_price=old_price, current_price=new_price))
                        if volume_usdt < config.MIN_VOLUME_USDT:
                            print(get_message("volume_below_threshold", symbol=symbol))
                            continue

                        now = time.time()
                        time_since_base = int(now - last_alert_time.get(symbol, now))

                        if config.MAX_PRICE_CHANGE_TIME > 0 and time_since_base > config.MAX_PRICE_CHANGE_TIME:
                            print(get_message("skip_slow_signal", symbol=symbol, time_delta=time_since_base, max_time=config.MAX_PRICE_CHANGE_TIME))
                            continue

                        if now - last_alert_time.get(symbol, 0) < config.COOLDOWN_MINUTES * 60:
                            continue

                        if config.USE_SMMA_FILTER:
                            side_direction = "buy" if price_change >= 0 else "sell"
                            if not smma_filter(symbol, closes_history[symbol], side_direction):
                                print(get_message("skip_smma_filter", symbol=symbol, side=side_direction))
                                continue

                        if price_change >= config.PUMP_THRESHOLD or price_change <= config.DUMP_THRESHOLD:
                            side = "buy" if price_change >= config.PUMP_THRESHOLD else "sell"

                            if not getattr(config, "USE_AUTO_CLOSE_OPPOSITE", False):
                                open_trades = simulator.get_open_trades()
                                if any(t for t in open_trades if t["symbol"] == symbol and t["side"].lower() == side):
                                    print(f"⛔ Сделка {side.upper()} по {symbol} уже открыта. Пропуск.")
                                    continue
                                if any(t for t in open_trades if t["symbol"] == symbol):
                                    print(f"⛔ Уже есть активная сделка по {symbol}. Пропуск.")
                                    continue

                            try:
                                if getattr(config, "USE_AUTO_CLOSE_OPPOSITE", False):
                                    opposite_side = "sell" if side == "buy" else "buy"
                                    for trade in simulator.get_open_trades():
                                        if trade["symbol"] == symbol and trade["side"].lower() == opposite_side:
                                            trade["close_reason"] = "REV"
                                            pnl, updated_deposit = simulator.close_trade(trade, new_price)
                                            stats = simulator.get_stats()
                                            db_manager.close_trade(trade["symbol"])
                                            message = format_close_message(trade, pnl, updated_deposit, stats)
                                            await send_telegram_message(message)
                                            if trade in simulator.open_trades:
                                                simulator.open_trades.remove(trade)
                                            break

                                await print_open_trade_status()

                                trade = simulator.open_trade(
                                    symbol, side, new_price, config.TRADE_AMOUNT, config.LEVERAGE,
                                    config.TP_LEVELS, config.TP_PERCENTAGES, config.SL_PERCENT,
                                    config.USE_TRAILING_STOP, config.TRAILING_STOP_PERCENT
                                )
                                if trade is None:
                                    print(f"❌ Сделка по {symbol} не открыта — ордер не прошёл.")
                                    continue

                                trade["volume_usdt"] = volume_usdt
                                trade["balance_at_open"] = simulator.deposit
                                trade["price_change_time"] = time_since_base
                                trade["ts_activated"] = False

                                db_manager.save_trade(trade)

                                message = format_open_message(trade, "SIMULATION", new_volume, new_price, base_prices)
                                sent_message = await send_telegram_message(message)

                                if sent_message and hasattr(sent_message, "message_id"):
                                    trade["open_message_id"] = sent_message.message_id
                                if sent_message and hasattr(sent_message.chat, "id"):
                                    trade["open_chat_id"] = sent_message.chat.id

                                print(get_message("telegram_sent"))

                                last_alert_time[symbol] = now
                                base_prices[symbol] = new_price
                                last_volumes[symbol] = new_volume
                                last_directions[symbol] = side

                            except Exception as e:
                                print(get_message("error_processing", symbol=symbol, error=e))

                except Exception as e:
                    print(get_message("error_processing", symbol=symbol, error=e))

        print(get_message("scanned_symbols", symbols=", ".join(scanned_symbols)))
        print(get_message("market_scan_time", duration=time.time() - start_market_scan))

        await asyncio.sleep(config.SCAN_DELAY_SECONDS)

async def monitor_open_trades():
    while True:
        start_open_scan = time.time()
        await check_for_close_trades()
        print(get_message("open_trades_scan_time", duration=time.time() - start_open_scan))
        await asyncio.sleep(config.OPEN_TRADES_SCAN_INTERVAL)

async def check_for_close_trades():
    open_trades = simulator.get_open_trades()
    prices = fetch_all_prices()

    for trade in open_trades:
        symbol = trade["symbol"]
        current_price, _ = prices.get(symbol, (trade["entry_price"], 0))

        # 🎯 Проверка TP1
        if not trade["tp_triggered"][0]:
            tp1_price = trade["tp_prices"][0]
            if (trade["side"] == "buy" and current_price >= tp1_price) or \
               (trade["side"] == "sell" and current_price <= tp1_price):

                tp1_qty = trade["amount"] * (trade["tp_percents"][0] / 100)

                simulator.place_market_order_by_base(
                    symbol.replace("_", ""),
                    tp1_qty,
                    "sell" if trade["side"] == "buy" else "buy"
                )

                simulator.mark_tp_triggered(trade, 0)

                # 🔁 Активируем трейлинг-стоп (только если не активирован)
                if not trade.get("ts_activated", False):
                    result = simulator.activate_trailing_stop(
                        symbol.replace("_", ""),
                        trade.get("trailing_percent")
                    )
                    if result is not None:
                        simulator.mark_ts_activated(trade)

        # 🛑 Общая проверка условий закрытия всей позиции
        if simulator.should_close_trade(trade, current_price):
            pnl, updated_deposit = simulator.close_trade(trade, current_price)
            stats = simulator.get_stats()

            db_manager.close_trade(trade["symbol"])

            message = format_close_message(trade, pnl, updated_deposit, stats)
            await send_telegram_message(message)
            print(get_message("telegram_sent"))

async def main():
    await asyncio.gather(
        monitor_market(),
        monitor_open_trades(),
        telegram_control.start_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
