import logging
import os

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils.executor import start_polling
from dotenv import load_dotenv
import messages as msg
import keyboards as kb

load_dotenv()

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot=bot,
                storage=storage)


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
async def process_start_command(message: types.Message, state: FSMContext):
    """Выдача инлайн-кнопок с выбором первого хода."""
    async with state.proxy() as data:
        data.clear()
    tg_id = message.from_user.id
    keyboard = await kb.get_keyboards_choice_first_move()
    await message.answer(text=msg.messages.get('greetings'))
    await bot.send_message(
        tg_id, 'Хочешь оставить за собой первый ход?',  reply_markup=keyboard
    )


@dp.callback_query_handler(
    lambda c: c.data and c.data.startswith('first_move_')
)
async def process_callback(
        callback_query: types.CallbackQuery, state: FSMContext
):
    """Коллбек с выбором первого хода."""
    async with state.proxy() as data:
        data.clear()
    async with state.proxy() as data:
        data['BEST_MOVES'] = [4, 0, 2, 6, 8, 1, 3, 5, 7]
    tg_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    answer = callback_query.data.replace('first_move_', '')
    best_moves = data['BEST_MOVES']
    if answer == 'да':
        keyboard = await kb.get_game_board('user')
        await bot.send_message(
            tg_id,
            'Ну что ж, даю тебе фору: играй крестиками.',
            reply_markup=keyboard
        )
    else:
        keyboard = await kb.get_game_board('bot')
        keyboard = await kb.get_new_game_board(
            best_moves[0], keyboard, tic='❌'
        )
        async with state.proxy() as data:
            data[f'move_{best_moves[0]}'] = 'bot'
            best_moves.pop(0)
            data['BEST_MOVES'] = best_moves
        await bot.send_message(
            tg_id,
            'Твоя удаль тебя погубит... Буду начинать я.',
            reply_markup=keyboard
        )


async def check_tie(chat_id, keyboard, data):
    """Проверка закончена ли игра в ничью."""
    cnt = 0
    for row in keyboard.inline_keyboard:
        for button in row:
            if button['text'] != '❔️':
                cnt += 1
                if cnt == 9 and not await find_winner(data):
                    await bot.send_message(
                        chat_id,
                        msg.messages.get('tie')
                    )


async def find_winner(data):
    """Поиск выигрышных путей."""
    ways_to_win = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )
    list_win = list()
    for ways in ways_to_win:
        for i in ways:
            list_win.append(data.get(f'move_{i}'))
        if list_win[0] == list_win[1] == list_win[2] is not None:
            return True
        list_win.clear()
    return False


async def bot_move(tg_id, message_id, keyboard, tic, state: FSMContext):
    """Ход бота."""
    async with state.proxy() as data:
        best_moves = data.get('BEST_MOVES')
    for i in range(len(best_moves)):
        async with state.proxy() as data:
            if data.get(f'move_{best_moves[i]}') is None:
                data[f'move_{best_moves[i]}'] = 'bot'
                keyboard = await kb.get_new_game_board(
                    best_moves[i], keyboard, tic
                )
                if await update_keyboard(tg_id, message_id, keyboard):
                    if await find_winner(data):
                        await update_keyboard(
                            tg_id, message_id, await kb.fill_buttons(keyboard)
                        )
                        await bot.send_message(
                            tg_id,
                            msg.messages.get('win_bot')
                        )
                    best_moves.pop(i)
                    data['BEST_MOVES'] = best_moves
                    break
    return keyboard


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('button_'))
async def process_callback_button(
        callback_query: types.CallbackQuery, state: FSMContext
):
    """Коллбек с выбором хода юзером."""
    tg_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)
    _, gamer, number = callback_query.data.split('_')
    async with state.proxy() as data:
        best_moves = data.get('BEST_MOVES')
        data[f'move_{number}'] = 'user'
        best_moves.remove(int(number))
        data['BEST_MOVES'] = best_moves
    message_id = callback_query.message.message_id
    message_keyboard = callback_query.message.reply_markup
    tic = '❌' if gamer == 'user' else '⭕'
    keyboard = await kb.get_new_game_board(number, message_keyboard, tic)
    await update_keyboard(tg_id, message_id, keyboard)
    if await find_winner(data):
        await update_keyboard(
            tg_id, message_id, await kb.fill_buttons(keyboard)
        )
        await bot.send_message(
            tg_id,
            msg.messages.get('win_user')
        )
        return
    tic = '❌' if gamer == 'bot' else '⭕'
    await bot_move(tg_id, message_id, keyboard, tic, state)
    async with state.proxy() as data:
        await check_tie(tg_id, keyboard, data)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    start_polling(dp, on_shutdown=shutdown)
