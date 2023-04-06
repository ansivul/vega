from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode

async def bot_echo(message: type.Message):
    text = [
        "Эхо без состояния.",
        "Сообщение:",
        message.text
    ]
    await message.answer('\n'.join(text))
    
async def bot_echo_all(message: type.Message, state: FSMContext):
    state_name = await statae.get_state()
    text = [
        f"Эхо в состоянии {hcode(state_name)}",
        "Сообщение:",
        message.text
    ]
    await message.answer('\n'.join(text))    
    
def register_echo(dp: Dispatcher):
    dp.register_message_hendler(bot_echo)
    dp.register_message_hendler(bot_echo_all, state='*', content_types=types.ContentType().ANY)    