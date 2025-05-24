from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import asyncio
import config

API_TOKEN = config.TELEGRAM_TOKEN

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher()

simulator = None  # Свяжем из main.py

@dp.message(Command("status"))
async def show_status(message: Message):
    if simulator:
        stats = simulator.get_stats()
        await message.answer(
            f"📊 Статистика:\n"
            f"Открытых сделок: {stats['open_trades']}\n"
            f"Всего сделок: {stats['total_trades']}\n"
            f"Баланс: ${simulator.deposit:.2f}\n\n"
            f"TP Levels: {config.TP_LEVELS}\n"
            f"SL: {config.SL_PERCENT}%\n"
            f"TS: {config.TRAILING_STOP_PERCENT}%\n"
            f"PUMP_THRESHOLD: {config.PUMP_THRESHOLD}%\n"
            f"DUMP_THRESHOLD: {config.DUMP_THRESHOLD}%\n"
            f"TRADE_AMOUNT: {config.TRADE_AMOUNT}$\n"
            f"LEVERAGE: {config.LEVERAGE}x"
        )
    else:
        await message.answer("❗ Симулятор не подключён!")

@dp.message(Command("pause"))
async def pause_trading(message: Message):
    config.TRADING_PAUSED = True
    await message.answer("⏸️ Открытие новых сделок приостановлена.")

@dp.message(Command("resume"))
async def resume_trading(message: Message):
    config.TRADING_PAUSED = False
    await message.answer("▶️ Открытие новых сделок возобновлена.")

@dp.message(Command("reverse_on"))
async def reverse_on(message: Message):
    config.USE_AUTO_CLOSE_OPPOSITE = True
    await message.answer("🔄 Реверс включён.")

@dp.message(Command("reverse_off"))
async def reverse_off(message: Message):
    config.USE_AUTO_CLOSE_OPPOSITE = False
    await message.answer("⛔ Реверс отключён.")

async def set_param(message: Message, param_name: str, value: float, is_list=False, index=None):
    try:
        value = float(value)
        if is_list and index is not None:
            config.__dict__[param_name][index] = value
            await message.answer(f"✅ Установлено {param_name}[{index+1}] = {value}")
        else:
            config.__dict__[param_name] = value
            await message.answer(f"✅ Установлено {param_name} = {value}")
    except Exception as e:
        await message.answer(f"❗ Ошибка изменения {param_name}: {e}")

@dp.message(Command("set_tp1"))
async def set_tp1(message: Message, command: CommandObject):
    await set_param(message, "TP_LEVELS", command.args, is_list=True, index=0)

@dp.message(Command("set_tp2"))
async def set_tp2(message: Message, command: CommandObject):
    await set_param(message, "TP_LEVELS", command.args, is_list=True, index=1)

@dp.message(Command("set_tp3"))
async def set_tp3(message: Message, command: CommandObject):
    await set_param(message, "TP_LEVELS", command.args, is_list=True, index=2)

@dp.message(Command("set_sl"))
async def set_sl(message: Message, command: CommandObject):
    await set_param(message, "SL_PERCENT", command.args)

@dp.message(Command("set_ts"))
async def set_ts(message: Message, command: CommandObject):
    await set_param(message, "TRAILING_STOP_PERCENT", command.args)

@dp.message(Command("set_trade_amount"))
async def set_trade_amount(message: Message, command: CommandObject):
    await set_param(message, "TRADE_AMOUNT", command.args)

@dp.message(Command("set_leverage"))
async def set_leverage(message: Message, command: CommandObject):
    await set_param(message, "LEVERAGE", command.args)

# ✅ Новые команды для PUMP и DUMP
@dp.message(Command("set_pump"))
async def set_pump(message: Message, command: CommandObject):
    await set_param(message, "PUMP_THRESHOLD", command.args)

@dp.message(Command("set_dump"))
async def set_dump(message: Message, command: CommandObject):
    await set_param(message, "DUMP_THRESHOLD", command.args)

@dp.message(Command("filter_off"))
async def disable_direction_filter(message: Message):
    config.USE_PRICE_DIRECTION_FILTER = False
    await message.answer("🔕 Фильтр по направлению (PUMP/DUMP) отключён.")

@dp.message(Command("filter_on"))
async def enable_direction_filter(message: Message):
    config.USE_PRICE_DIRECTION_FILTER = True
    await message.answer("📈 Фильтр по направлению (PUMP/DUMP) включён.")


async def start_bot():
    await dp.start_polling(bot)
