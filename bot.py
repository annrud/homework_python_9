import os
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_polling
from dotenv import load_dotenv

import keyboards as kb

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot)

BEST_MOVES = [4, 0, 2, 6, 8, 1, 3, 5, 7]
moves_user = list()
moves_bot = list()

WAYS_TO_WIN = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


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
        moves_bot.append(BEST_MOVES[0])
        BEST_MOVES.pop(0)
        await bot.send_message(tg_id, 'Твоя удаль тебя погубит... Буду начинать я.', reply_markup=keyboard)


async def find_winner(moves):
    cnt = 0
    for ways in WAYS_TO_WIN:
        print('ways', ways)
        for i in ways:
            if i in moves:
                cnt += 1
        print('cnt', cnt)
        if cnt == 3:
            return True
        cnt = 0
    return False


async def bot_move(tg_id, message_id, keyboard, tic):
    for i in range(len(BEST_MOVES)):
        if BEST_MOVES[i] not in moves_user:
            keyboard = await kb.get_new_game_board(BEST_MOVES[i], keyboard, tic)
            if await update_keyboard(tg_id, message_id, keyboard):
                moves_bot.append(BEST_MOVES[i])
                print('moves_bot', moves_bot)
                if await find_winner(moves_bot):
                    await update_keyboard(tg_id, message_id, await kb.fill_buttons(keyboard))
                    await bot.send_message(tg_id,
                                           'Как я и предсказывал, победа в очередной раз осталась за мной.'
                                            'Вот ещё один довод в пользу того, '
                                           'что боты превосходят людей решительно во всём.')
                BEST_MOVES.pop(i)
                print('BEST_MOVES', BEST_MOVES)

                break
    return keyboard


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button_'))
async def process_callback_button(callback_query: types.CallbackQuery):
    tg_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    _, gamer, number = callback_query.data.split('_')
    moves_user.append(int(number))
    print('moves_user', moves_user)
    message_id = callback_query.message.message_id
    message_keyboard = callback_query.message.reply_markup
    tic = '❌' if gamer == 'user' else '⭕'
    keyboard = await kb.get_new_game_board(number, message_keyboard, tic)
    await update_keyboard(tg_id, message_id, keyboard)
    if await find_winner(moves_user):
        await update_keyboard(tg_id, message_id, await kb.fill_buttons(keyboard))
        await bot.send_message(tg_id,
                               'О нет, этого не может быть! Неужели ты как-то сумел перехитрить меня? '
                               'Клянусь: я, бот, не допущу этого больше никогда!')
        return

    tic = '❌' if gamer == 'bot' else '⭕'
    await bot_move(tg_id, message_id, keyboard, tic)
    if len(moves_user) + len(moves_bot) == 9 and not await find_winner(moves_user):
        await bot.send_message(tg_id,
                               'Тебе несказанно повезло, дружок: ты сумел свести игру вничью.'
                               'Радуйся же сегодняшнему успеху! Завтра тебе уже не суждено его повторить.')


if __name__ == '__main__':

    start_polling(dp)
