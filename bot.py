import os


from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_polling
from dotenv import load_dotenv

import keyboards as kb

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot)

BEST_MOVES = [4, 0, 2, 6, 8, 1, 3, 5, 7]


async def update_keyboard(chat_id, message_id, keyboard):
    try:
        return await bot.edit_message_reply_markup(
            chat_id,
            message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        print(e)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    """Выдача кнопок по команде "start"."""
    tg_id = message.from_user.id
    keyboard = await kb.get_keyboards_choice_first_move()
    await message.answer(text='''
Добро пожаловать на ринг грандиознейших интеллектуальных состязаний всех времён.
Твой мозг и мой процессор сойдутся в схатке за доской игры "Крестики-нолики". 
Приготовься к бою, жалкий человечишка. Вот-вот начнется решающее сражений.
        ''')
    await bot.send_message(tg_id, 'Хочешь оставить за собой первый ход?',  reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('first_move_'))
async def process_callback(callback_query: types.CallbackQuery):
    """Выдача контента инлайн-кнопки."""
    tg_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    answer = callback_query.data.replace('first_move_', '')
    if answer == 'да':
        keyboard = await kb.get_game_board('user')
        await bot.send_message(tg_id, 'Ну что ж, даю тебе фору: играй крестиками.', reply_markup=keyboard)
    else:
        keyboard = await kb.get_game_board('bot')
        keyboard = await kb.get_new_game_board(BEST_MOVES[0], keyboard, tic='❌')
        BEST_MOVES.pop(0)
        await bot.send_message(tg_id, 'Твоя удаль тебя погубит... Буду начинать я.', reply_markup=keyboard)


async def bot_move(tg_id, message_id, keyboard, tic):
    for i in range(len(BEST_MOVES)):
        keyboard = await kb.get_new_game_board(BEST_MOVES[i], keyboard, tic)
        if await update_keyboard(tg_id, message_id, keyboard):
            break
    return keyboard


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button_'))
async def process_callback_button(callback_query: types.CallbackQuery):
    tg_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    _, gamer, number = callback_query.data.split('_')
    message_id = callback_query.message.message_id
    message_keyboard = callback_query.message.reply_markup
    tic = '❌' if gamer == 'user' else '⭕'
    keyboard = await kb.get_new_game_board(number, message_keyboard, tic)
    await update_keyboard(tg_id, message_id, keyboard)
    tic = '❌' if gamer == 'bot' else '⭕'
    await bot_move(tg_id, message_id, keyboard, tic)


if __name__ == '__main__':
    start_polling(dp)
