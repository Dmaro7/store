import os
import json
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env (если используется)

BOT_ENABLED = True  # Полное включение/отключение бота
MODE = "live"  # Возможные значения: "off", "simulation", "live"

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")


# Telegram настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_CHAT_ID = CHAT_ID
TELEGRAM_USERNAME = "trader_7817_bot"

#Для приватных групп используйте ID вида -100xxxxxxxxxx
PRIVATE_CHAT_ID = os.getenv("PRIVATE_CHAT_ID", CHAT_ID)


import os

DATABASE_URL = os.getenv("DATABASE_URL")  # Строка подключения из Railway Variables или .env

import os

CHAT_IDS = [int(chat_id.strip()) for chat_id in os.getenv("CHAT_IDS", "123456789").split(",")]

# Торговые пары для отслеживания
SYMBOLS = ["BTC_USDT", "ETH_USDT", "SOL_USDT"]  # Можно расширять список

CHUNK_SIZE = 100              # Размер одного чанка (кол-во пар в одном цикле)

MAX_OPEN_TRADES = 1  # Максимально допустимое количество открытых сделок
USE_RANDOM_SCAN = True # выполняет рандомное сканирование пар 
OPEN_TRADES_SCAN_INTERVAL = 0.05  # Интервал проверки открытых сделок в секундах

USE_VOLUME_FILTER = True  # Фильтр роста объёма после лонга (пропуск шортов)
USE_VOLUME_DECREASE_FILTER = True  # Фильтр снижения объёма после шорта (пропуск лонгов)
# Фильтр по времени изменения цены (в секундах). 
# 0 = фильтр отключён, любое другое значение — ограничение времени в секундах.
MAX_PRICE_CHANGE_TIME = 0  # Например, не учитывать сигналы, если цена изменилась за более чем 5 минут (300 секунд).
USE_AUTO_CLOSE_OPPOSITE = False  # Включаем автоматическое закрытие противоположных сделок

# Порог обновления базовой цены (в процентах)
BASE_PRICE_UPDATE_THRESHOLD = 0.1  # Можно изменить на любое нужное значение, например 0.5

# Торговые пороги
USE_PRICE_DIRECTION_FILTER = False  # если False — сигналы PUMP/DUMP игнорируются

PUMP_THRESHOLD = 1.5  # Рост цены в % для сигнала "памп"
DUMP_THRESHOLD = -1.5  # Падение цены в % для сигнала "дамп"
MIN_VOLUME_USDT = 700000  # Минимальный объём в USDT для обработки пары

# Тайминги
COOLDOWN_MINUTES = 0  # Кулдаун между сигналами по одной паре
SCAN_DELAY_SECONDS = 0.5  # Задержка между циклами сканирования (в секундах)

# Настройки торговли и симуляции
# MODE = os.getenv("MODE", "simulation")  # "simulation" или "live"
DEPOSIT = int(os.getenv("DEPOSIT", 20))
TRADE_AMOUNT = int(os.getenv("TRADE_AMOUNT", 5))
LEVERAGE = int(os.getenv("LEVERAGE", 1.0))

TP_LEVELS = [1.5, 3.0, 5.0]  # Take Profit уровни в %
TP_PERCENTAGES = [30, 60, 10]  # Проценты от позиции на каждом TP

SL_PERCENT = 7.0  # Stop Loss в %
USE_TRAILING_STOP = True  # Включить трейлинг стоп
ACTIVATE_TS_AFTER_TP1 = True  # Если True — ТС активируется только после срабатывания TP1
TRAILING_STOP_PERCENT = 0.5  # Величина трейлинг стопа в %

# Индивидуальные пороги для пар (если нужно переопределить)
PAIR_THRESHOLDS = {
    "BTC_USDT": {"pump": 0.5, "dump": -0.5},
    "ETH_USDT": {"pump": 0.7, "dump": -0.7}  
}

#Фильтр по SMMA как тренд
USE_SMMA_FILTER = True  # Включение фильтра SMMA
SMMA_LENGTH = 50        # Длина SMMA

# Вторая SMMA (MTF)
USE_SECOND_SMMA_LOGIC = False
SECOND_SMMA_LENGTH = 100  # длина сглаживания SMMA для второй логики

SECOND_SMMA_TF = "Hour1"  # таймфрейм, с которого брать SMMA для MEXC | Таймфрейм | Значение `interval` |
#| 1 минута  | `Min1`              |
#| 5 минут   | `Min5`              |
#| 15 минут  | `Min15`             |
#| 30 минут  | `Min30`             |
#| 1 час     | `Hour1`             |
#| 4 часа    | `Hour4`             |
#| 1 день    | `Day1`              |
#| 1 неделя  | `Week1`             |

SMMA_DISTANCE_PERCENT = 2  # минимальное отклонение от SMMA
VOLUME_SPIKE_MULTIPLIER = 2.0  # объём в X раз выше среднего




# Для комады боту /pause
TRADING_PAUSED = False


def get_current_interval():
    """Функция для динамического управления интервалами (можно доработать)."""
    return SCAN_DELAY_SECONDS
