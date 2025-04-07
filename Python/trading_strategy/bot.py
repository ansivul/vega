import sys
import asyncio
import logging
import io
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Filter
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Если бот запускается на Windows, переключаемся на SelectorEventLoop
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Загружаем переменные окружения из файла .env
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_CHAT_ID = 123456789  # Замените на ваш реальный Telegram chat_id для уведомлений

logging.basicConfig(level=logging.INFO)

# Создаем бота с HTML-разметкой
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# Глобальная переменная для хранения торговой пары
trading_pair = "BTCUSDT"

# Главное меню с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Изменить торговую пару"), KeyboardButton(text="Запустить скрипт")]
    ],
    resize_keyboard=True
)

# Кастомный фильтр для текстовых сообщений
class TextFilter(Filter):
    def __init__(self, equals: str = None, endswith: str = None, ignore_case: bool = False):
        self.equals = equals
        self.endswith = endswith
        self.ignore_case = ignore_case

    async def __call__(self, message: types.Message) -> bool:
        if message.text is None:
            return False
        text = message.text
        if self.ignore_case:
            text = text.lower()
        if self.equals is not None:
            expected = self.equals.lower() if self.ignore_case else self.equals
            return text == expected
        if self.endswith is not None:
            expected = self.endswith.lower() if self.ignore_case else self.endswith
            return text.endswith(expected)
        return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите действие:", reply_markup=main_keyboard)

@dp.message(TextFilter(equals="Изменить торговую пару"))
async def change_trading_pair(message: types.Message):
    await message.answer("Пожалуйста, отправьте новую торговую пару (например, BNBUSDT):")

@dp.message(TextFilter(endswith="USDT", ignore_case=True))
async def update_trading_pair(message: types.Message):
    global trading_pair
    new_pair = message.text.strip().upper()
    trading_pair = new_pair
    await message.answer(f"Торговая пара обновлена на: {trading_pair}")

@dp.message(TextFilter(equals="Запустить скрипт"))
async def force_run_script(message: types.Message):
    await message.answer("Запускаю скрипт...")
    try:
        from trading_strategy import trading_strategy, TIMEFRAME
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        try:
            # Запускаем синхронную функцию в отдельном потоке, чтобы не блокировать бота
            # Python 3.8
            # loop = asyncio.get_running_loop()
            # await loop.run_in_executor(None, trading_strategy, trading_pair, TIMEFRAME)
            # Запускаем торговую стратегию в отдельном потоке
            await asyncio.to_thread(trading_strategy, trading_pair, TIMEFRAME)
        finally:
            sys.stdout = old_stdout
        output = buffer.getvalue()
        if not output:
            output = "Скрипт выполнен, но не было вывода."
        # Отправляем вывод частями (ограничение Telegram – 4096 символов)
        for chunk in [output[i:i+4096] for i in range(0, len(output), 4096)]:
            await message.answer(chunk)
    except Exception as e:
        await message.answer(f"Ошибка при выполнении скрипта: {e}")

# Функция, запускаемая по расписанию
async def scheduled_run():
    try:
        # Уведомляем администратора о запуске по расписанию
        await bot.send_message(ADMIN_CHAT_ID, "⏰ <b>Автоматический запуск скрипта по расписанию</b> начался.")
        from trading_strategy import trading_strategy, TIMEFRAME
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        try:
            # Запускаем синхронную функцию в отдельном потоке, чтобы не блокировать бота
            # Python 3.8
            # loop = asyncio.get_running_loop()
            # await loop.run_in_executor(None, trading_strategy, trading_pair, TIMEFRAME)
            # Запускаем торговую стратегию в отдельном потоке
            await asyncio.to_thread(trading_strategy, trading_pair, TIMEFRAME)
        finally:
            sys.stdout = old_stdout
        output = buffer.getvalue()
        if not output:
            output = "Скрипт выполнен, но не было вывода."
        for chunk in [output[i:i+4096] for i in range(0, len(output), 4096)]:
            await bot.send_message(ADMIN_CHAT_ID, chunk, parse_mode="HTML")
    except Exception as e:
        await bot.send_message(ADMIN_CHAT_ID, f"Ошибка при автоматическом запуске скрипта: {e}")

async def main():
    # Инициализируем планировщик задач (timezone UTC)
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Планируем задачу: 23:50, 03:50, 07:50, 11:50, 15:50, 19:50 UTC
    scheduler.add_job(scheduled_run, 'cron', hour='23,3,7,11,15,19', minute=50)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
