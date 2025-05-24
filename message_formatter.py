from datetime import datetime, timedelta, timezone
from config import MODE, TP_LEVELS, TP_PERCENTAGES, PRIVATE_CHAT_ID

def format_time_delta(seconds):
    if seconds < 60:
        return f"{int(seconds)} сек"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins} мин {secs} сек"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours} ч {mins} мин"

def format_open_message(trade, mode=MODE, volume_24h=None, price=None, base_prices=None,
                        current_price=None, base_price=None, price_change=None, price_change_time=None):
    open_time_utc = datetime.fromtimestamp(trade["opened_at"], tz=timezone.utc)
    open_time_msk = open_time_utc + timedelta(hours=3)
    time_str = f"{open_time_msk.strftime('%d.%m.%Y')} / {open_time_msk.strftime('%H:%M')} МСК ({open_time_utc.strftime('%H:%M')} UTC)"

    emoji = "🟢" if trade['side'].lower() == "buy" else "🔴"
    side_text = f"<b><i>{trade['side'].upper()}</i></b>"
    token = trade['symbol'].split('_')[0]
    tv_symbol = f"{token}USDT"
    symbol_link = f'<a href="https://www.tradingview.com/chart/?symbol={tv_symbol}">{token}/USDT</a>'

    if base_price is None:
        if base_prices:
            base_price = base_prices.get(trade["symbol"], trade["entry_price"])
        else:
            base_price = trade["entry_price"]

    if current_price is None:
        current_price = trade["entry_price"]

    if price_change is None:
        price_change = ((current_price - base_price) / base_price) * 100 if base_price else 0

    if price_change_time is None:
        price_change_time = int(trade.get("price_change_time", 0))

    change_time_str = f"за {format_time_delta(price_change_time)}" if price_change_time else ""
    ts_status = "activ" if trade.get("ts_activated") else "not activ"

    volume_usdt = volume_24h * price if volume_24h and price else trade.get("volume_usdt", 0)
    volume_millions = volume_usdt / 1_000_000

    return (
        f"⚠️ [{mode} Mode]\n\n"
        f"{emoji} Открыта: {side_text} {symbol_link}\n\n"
        f"Изменение: #{token}\n"
        f"({price_change:+.2f}%) {change_time_str}\n"
        f"Цена отсчёта: <b>${base_price:.4f}</b>\n"
        f"Цена входа: <b>${trade['entry_price']}</b>\n"
        f"24 час. Объём: {volume_millions:.2f}М USDT\n"
        f"Объём: ${trade['amount']}\n"
        f"Плечо: {trade['leverage']}x\n"
        f"Баланс: <b>${trade.get('balance_at_open', 0):.2f}</b>\n\n"
        f"TP1: +{TP_LEVELS[0]}% ({TP_PERCENTAGES[0]}%)\n"
        f"TP2: +{TP_LEVELS[1]}% ({TP_PERCENTAGES[1]}%)\n"
        f"TP3: +{TP_LEVELS[2]}% ({TP_PERCENTAGES[2]}%)\n"
        f"SL: -{trade['sl_percent']}%\n"
        f"TS: ON, {ts_status} ({trade['trailing_percent']}%)\n\n"
        f"Открыта: {time_str}"
    )

def format_close_message(trade, pnl, deposit, stats):
    close_utc = datetime.fromtimestamp(trade["closed_at"], tz=timezone.utc)
    close_msk = close_utc + timedelta(hours=3)
    time_str = f"{close_msk.strftime('%d.%m.%Y')} / {close_msk.strftime('%H:%M')} МСК ({close_utc.strftime('%H:%M')} UTC)"

    token = trade['symbol'].split('_')[0]
    tv_symbol = f"{token}USDT"
    symbol_link = f'<a href="https://www.tradingview.com/chart/?symbol={tv_symbol}">{token}/USDT</a>'
    circles = "🟢🟢🟢" if pnl >= 0 else "🔴🔴🔴"
    profit_text = f"<b>${pnl:.2f}</b>"
    side_text = f"<b><i>{trade['side'].upper()}</i></b>"
    reason = trade.get('close_reason', 'вручную')
    reason_display = reason if reason != "REV" else "REV 🟡 "

    open_message_id = trade.get("open_message_id")
    message_link = ""
    if open_message_id:
        internal_chat_id = PRIVATE_CHAT_ID.replace("-100", "")
        message_link = f'\n[<a href="https://t.me/c/{internal_chat_id}/{open_message_id}">Открытие сделки</a>]'

    duration_seconds = trade["closed_at"] - trade["opened_at"]
    duration_str = format_time_delta(duration_seconds)

    if trade["trailing_stop"] and trade.get("trailing_level"):
        ts_level = trade.get("trailing_level")
        trailing_percent = abs(((trade['entry_price'] - ts_level) / trade['entry_price']) * 100)
        trailing_info = f"ON — ${ts_level:.5f} ({trailing_percent:.2f}%)"
    else:
        trailing_info = "Отключён"

    invested = trade['amount'] * trade['leverage']
    pnl_percent = (pnl / invested) * 100 if invested != 0 else 0
    pnl_sign = "+" if pnl >= 0 else ""

    volume_usdt = trade.get("volume_usdt", 0)
    volume_millions = volume_usdt / 1_000_000

    stats_block = (
        f"<i><b>Статистика с момента запуска бота:</b></i>\n\n"
        f"<i>Всего откр. сделок: {stats['total_trades']}</i>\n"
        f"<i>Открытых сделок: {stats['open_trades']}</i>\n\n"
        f"<i>Закрыты по TP1: {stats['tp1_count']} (+${stats['tp1_profit']:.2f})</i>\n"
        f"<i>Закрыты по TP2: {stats['tp2_count']} (+${stats['tp2_profit']:.2f})</i>\n"
        f"<i>Закрыты по TP3: {stats['tp3_count']} (+${stats['tp3_profit']:.2f})</i>\n"
        f"<i>Закрыты по TS: {stats['ts_count']} (+${stats['ts_profit']:.2f})</i>\n"
        f"<i>Закрыты по SL: {stats['sl_count']} (-${stats['sl_loss']:.2f})</i>\n"
        f"<i>Закрыты по REV: {stats.get('rev_count', 0)} (+${stats.get('rev_profit', 0):.2f})</i>"
    )

    status_text = 'Полностью закрыта' if trade["status"] == "closed" else f'Закрыто ({trade["closed_percent"]:.0f}%)'

    return (
        f"⚠️ [{MODE.upper()} Mode]\n\n"
        f"{circles} {symbol_link}\n"
        f"Закрыта по {reason_display}\n\n"
        f"Сделка {side_text} #{token}{message_link}\n\n"
        f"Цена откр: ${trade['entry_price']}\n"
        f"Цена закр: ${trade['exit_price']} (по {reason_display})\n"
        f"24 час. Объём: {volume_millions:.2f}М USDT\n\n"
        f"<i>Статус: {status_text}</i>\n"
        f"<i>Длительность: {duration_str}</i>\n"
        f"<i>TS: {trailing_info}</i>\n\n"
        f"<i>Прибыль: {profit_text} ({pnl_sign}{pnl_percent:.2f}%)</i>\n"
        f"<i>Баланс: ${deposit:.2f}</i>\n\n"
        f"{stats_block}\n\n"
        f"Закрыта: {time_str}"
    )
