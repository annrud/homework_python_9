from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def get_keyboards_choice_first_move():
    inline_keyboard = InlineKeyboardMarkup()
    for i in ('да', 'нет'):
        inline_keyboard.insert(InlineKeyboardButton(
            text=i,
            callback_data=f'first_move_{i}',
        ))
    return inline_keyboard

BEST_MOVES = (4, 0, 2, 6, 8, 1, 3, 5, 7)


async def get_game_board(first=None):
    inline_keyboard = InlineKeyboardMarkup()
    for i in range(9):
        inline_keyboard.insert(InlineKeyboardButton(
            text='❔️',
            callback_data=f'button_{first}_{i}',
        ))
    return inline_keyboard


async def get_new_game_board(number=None, keyboard=None, tic='⭕'):
    for row in keyboard.inline_keyboard:
        for button in row:
            if button['callback_data'] == f'button_user_{number}' and button['text'] == '❔️':
                button['text'] = tic
            elif button['callback_data'] == f'button_bot_{number}' and button['text'] == '❔️':
                button['text'] = tic
    return keyboard


