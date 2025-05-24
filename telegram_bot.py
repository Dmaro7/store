from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
import asyncio
import config

API_TOKEN = config.TELEGRAM_TOKEN

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

async def send_telegram_message(message_text: str):
    try:
        await bot.send_message(
            chat_id=config.PRIVATE_CHAT_ID,
            text=message_text,
            disable_web_page_preview=True  # ✅ Отключаем превью ссылок
        )
        print("✅ Сообщение отправлено в Telegram")
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения в Telegram: {e}")

async def start_bot():
    from telegram_control import dp as control_dp
    await control_dp.start_polling(bot)
