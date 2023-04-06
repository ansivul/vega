from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode

async def admin_start(message: type.Message):
    await message.replay('Hello, admin!')

def register_admin(dp: Dispatcher):
    dp.register_message_hendler(admin_start, commands=['start'], is_admin=True)
      