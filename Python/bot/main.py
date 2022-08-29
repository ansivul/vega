from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from tokens import tg_bot_token

bot = Bot(tg_bot_token)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет!")

@dp.message_handler()
async def start_command(message: types.Message):
    await message.reply("Привет - 2 ")
    
if __name__ == '__main__':
    executor.start_polling(dp)