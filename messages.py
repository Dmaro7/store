MESSAGES = {
    "bot_started": "🚀 Бот запущен. Ожидаем сигналы...",
    "max_open_trades": "⚠️ Максимум открытых сделок достигнут ({limit}). Пропускаем сигналы.",
      # Детализированное логирование анализа цен и объёма
    "price_check": (
        "🔍 Проверка {symbol}:\n"
        "Базовая цена: ${base_price:.6f}\n"
        "Текущая цена: ${current_price:.6f}\n"
        "Изменение: {price_change:.2f}%\n"
        "Объём: ${volume_usdt:,.2f} USDT"
    ),

    "volume_below_threshold": "⏩ Пропущено {symbol} — объём ниже порога.",
    "skip_slow_signal": "⏩ Пропущено {symbol} — цена изменилась слишком медленно ({time_delta} сек > {max_time} сек).",
    "skip_smma_filter": "⏩ Пропущено {symbol} — отклонено SMMA фильтром для {side}.",
    "skip_short_volume": "⏩ Пропущено {symbol} — объём увеличился, шорт отменён.",
    "skip_long_volume_decrease": "⏩ Пропущено {symbol} — объём снизился, лонг отменён.",
    "telegram_sent": "📨 Сообщение отправлено в Telegram.",
    "open_trade_saved": "💾 Сделка сохранена: {trade}.",
    "error_fetch": "❌ Ошибка получения данных: {error}",
    "error_processing": "❌ Ошибка обработки {symbol}: {error}",
    "trailing_stop_moved": "🔄 Трейлинг-стоп по {symbol} перемещён на ${new_level:.6f}.",
    "trailing_stop_triggered": "🔚 Трейлинг-стоп по {symbol} сработал при цене ${current_price:.6f}.",
    "cooldown_active": "⏳ Пропущено {symbol} — ещё не прошёл кулдаун ({remaining_time:.0f} сек).",
    "signal_sent": "📡 Сигнал отправлен по {symbol}. Открываем сделку {side}.",
    
    # ... другие шаблоны Про востановленые сделки после перезагрузки ...
    "restored_trades": "✅ Восстановлено {count} открытых сделок. Продолжаем мониторинг...",
    "monitoring_trade": "🔄 Мониторинг восстановленной сделки: {symbol}",
    "market_scan_time": "⏱ Полный скан: {duration:.2f} сек",
    "scanned_symbols": "✅ Просканированы пары: {symbols}",
    "open_trades_scan_time": "⏱ Скан открытых позиций: {duration:.2f} сек",

}

def get_message(key, **kwargs):
    return MESSAGES.get(key, "").format(**kwargs)
