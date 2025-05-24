import config

def calculate_smma(prices, length):
    if not prices or len(prices) < length:
        return None
    smma = prices[0]
    for price in prices[1:]:
        smma = (smma * (length - 1) + price) / length
    return smma

def smma_filter(symbol, closes, direction):
    #print(f"⚙️ SMMA фильтр вызван для {symbol} с направлением {direction}, закрытия: {closes}")

    if not getattr(config, "USE_SMMA_FILTER", False):
        print("⚙️ SMMA фильтр отключён в конфиге.")
        return True  # Фильтр отключён

    smma_length = getattr(config, "SMMA_LENGTH", 50)
    if len(closes) < smma_length:
        print(f"⚠️ Недостаточно данных для SMMA по {symbol}: нужно {smma_length}, есть {len(closes)}")
        return True  # Недостаточно данных — пропускаем фильтр

    smma_value = calculate_smma(closes[-smma_length:], smma_length)
    last_close = closes[-1]

    print(f"🔍 SMMA фильтр {symbol}: Закрытие={last_close}, SMMA={smma_value}, Направление={direction}")

    # Приводим направление к нижнему регистру
    direction = direction.lower()

    if last_close > smma_value and direction == "buy":
        print(f"✅ Сигнал BUY по {symbol} разрешён SMMA фильтром (Close={last_close} > SMMA={smma_value})")
        return True
    if last_close < smma_value and direction == "sell":
        print(f"✅ Сигнал SELL по {symbol} разрешён SMMA фильтром (Close={last_close} < SMMA={smma_value})")
        return True

    print(f"⛔ Сигнал {direction.upper()} по {symbol} отклонён фильтром SMMA (Close={last_close}, SMMA={smma_value})")
    return False  # Фильтр не пропускает сделку
