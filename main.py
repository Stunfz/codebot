import datetime
import re
import sqlite3
import logging
import html
import roles
import os
import subprocess
from define import process_message, process_photo, send_all_users, handle_commands, home_users, settings_menu, back_from_settings, change_language, back_from_set, support_menu
from gpt4fo import process_question
from aiogram.utils.markdown import hlink
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, date
from aiogram.dispatcher.filters import Text
from msg_text import msg_text, abouts
from aiogram.dispatcher.filters import Filter




# Инициализация бота
logging.basicConfig(level=logging.INFO)
API_TOKEN = 'token'
bot = Bot(token=API_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Настройки подключения к базе данных
##################################################################
#счет
users_count = {}
##################################################################
#цвета
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
#

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Начать общение ✍️'),
                 types.KeyboardButton(''),
                 types.KeyboardButton('Роли 🎭'),
                 types.KeyboardButton(''),
                 types.KeyboardButton('Профиль 📊'))

    inline_keyboard = roles.create_roles_menu()
    #db
    await message.answer(
        text=msg_text,
        reply_markup=inline_keyboard and keyboard
    )

    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username
    cursor.execute('SELECT * FROM users WHERE chat_check AND user_id=?', (user_id,))
    sql = cursor.fetchall()
    cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    user = cursor.fetchone()

    if len(sql) == 0:
        cursor.execute('UPDATE users SET chat_check = 1 WHERE user_id = ?', (user_id,))
        conn.commit()  # Save changes to the database

    if user:
        print(f'{bcolors.OKBLUE}Значение chat_check успешно обновлено.')
    else:
        print(f'{bcolors.WARNING}Вы уже зарегистрированы в базе данных, и значение chat_check уже равно 1.')
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (user_id, chat_id, username, 1, "Nols", 2, 0, "", 0, ""))
        conn.commit()
        print(f'{bcolors.OKGREEN}Вы успешно зарегистрированы в базе данных.')

    with open("users_vk.txt", "a") as file:
        file.write(f"User ID: {message.from_user.id}\nChat ID: {message.chat.id}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    current_date = message.date.date()

    if current_date not in users_count:
        users_count[current_date] = 1
    else:
        users_count[current_date] += 1


@dp.message_handler(lambda message: message.text == 'Роли 🎭')
async def roles_button_handler(message: types.Message):
    inline_keyboard = roles.create_roles_menu()
    await message.answer('<b>🧠 Выберите роль, для работы</b>:', reply_markup=inline_keyboard)

dp.register_message_handler(roles_button_handler, lambda message: message.text == 'Роли 🎭')
dp.register_callback_query_handler(roles.handle_roles_callback, lambda query: query.data in ['medicine', 'financier', 'youtuber', 'instagrammer', 'athlete', 
                                                                                             'entrepreneur', 'crypto_trader', 'writer', 'poet', 'reko', 
                                                                                             'sport', 'raper', 'matem', 'comm', 'psyhol', 'def'])
dp.register_callback_query_handler(roles.use_button_callback, lambda query: query.data == 'use')
dp.register_callback_query_handler(roles.on_button_callback, lambda query: query.data == 'on')


@dp.message_handler(Command('repid'))
async def repid_handler(message: types.Message):
    await process_message(message)

# Регистрация обработчика сообщений с фото
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def photo_handler(message: types.Message):
    await process_photo(message)

# Обработчик команды /sendall
@dp.message_handler(commands=['sendall'])
async def send_all_user(message: types.Message):
    await send_all_users(message)


@dp.message_handler(commands=['about', 'add', 'restart', 'support'])
async def handle_command(message: types.Message):
    await handle_commands(message)


# Обработчик команды /new_users
@dp.message_handler(commands=['check'])
async def count_new_messages_and_users(message: types.Message):
    if message.from_user.id == id:
        # Получаем текущую дату
        current_date = message.date.date()
        # Проверяем, есть ли текущая дата в словаре users_count
        if current_date in users_count:
            users_count_today = users_count[current_date]
        else:
            users_count_today = 0

        # Открываем файл с сообщениями
        with open("messages_vk.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Подсчет количества новых сообщений
        messages_count_today = 0
        for line in lines:
            if f"Date: {current_date}" in line:
                messages_count_today += 1

        # Отправка ответа с количеством принятых запросов и пользователей
        await message.reply(
            f"Информация:\n"
            f"Принятых запросов за сегодня: {messages_count_today}\n"
            f"Принятых пользователей за сегодня: {users_count_today}"
        )
    else:
        sticker_id = 'CAACAgIAAxkBAAELGKplmBfzpvvpm5Z9oXYr_FiSCn3_FQAC1gADVp29Cgl1yQziLyEKNAQ'
        await bot.send_sticker(chat_id=message.chat.id, sticker=sticker_id)
        await message.reply(f'Ещё не подрос для данной команды')
            
@dp.message_handler(lambda message: message.text == 'Профиль 📊')
async def home_user(message: types.Message):
    await home_users(message)


@dp.callback_query_handler(lambda callback: callback.data == 'settings')
async def settings_men(callback: types.CallbackQuery):
    await settings_menu(callback)

@dp.callback_query_handler(lambda callback: callback.data == 'back_from_settings')
async def back_set_menu(callback: types.CallbackQuery):
    await back_from_settings(callback)

@dp.callback_query_handler(lambda callback: callback.data == 'back_from_settings')
async def back_set_menu(callback: types.CallbackQuery):
    await back_from_settings(callback)

@dp.callback_query_handler(lambda callback: callback.data == 'support')
async def support_menu_handler(callback: types.CallbackQuery):
    await support_menu(callback) 

@dp.callback_query_handler(lambda callback: callback.data == 'support_link')
async def support_link_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Ссылка на поддержку: ссылка")

@dp.callback_query_handler(lambda callback: callback.data == 'change_language')
async def handle_change_language(callback: types.CallbackQuery):
    await change_language(callback)

@dp.callback_query_handler(lambda callback: callback.data in ['llama', 'gigachat', 'gpt3.5'])
async def handle_language_selection(callback: types.CallbackQuery):
    # Get the user ID from the callback query
    user_id = callback.message.chat.id

    # Connect to the SQLite database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Check if user has a subscription
    cursor.execute("SELECT sub FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        user_sub = user_data[0]

        # Update the user's model column in the users table
        if callback.data == 'llama':
            if user_sub == 1:
                model_id = 1
                cursor.execute("UPDATE users SET model = ? WHERE user_id = ?", (model_id, user_id))
                conn.commit()
                await callback.message.answer('<b>Языковая модель, обновлена 🧠</b>', parse_mode="HTML")
            else:
                await callback.message.answer('<b>Нейросеть, доступна только пользователям с подпиской. </b>', parse_mode="HTML")
        elif callback.data == 'gigachat':
            if user_sub == 1:
                model_id = 0
                cursor.execute("UPDATE users SET model = ? WHERE user_id = ?", (model_id, user_id))
                conn.commit()
                await callback.message.answer('<b>Языковая модель, обновлена 🧠</b>', parse_mode="HTML")
            else:
                await callback.message.answer('<b>Нейросеть, доступна только пользователям с подпиской. </b>', parse_mode="HTML")
        elif callback.data == 'gpt3.5':
            model_id = 2
            cursor.execute("UPDATE users SET model = ? WHERE user_id = ?", (model_id, user_id))
            conn.commit()
            await callback.message.answer('<b>Языковая модель, обновлена 🧠</b>', parse_mode="HTML")
    else:
        # Обработка случая, когда пользователь не найден в базе данных
        await callback.message.answer('<b>Вы не зарегистрированы в системе </b>', parse_mode="HTML")

    conn.close()





@dp.callback_query_handler(lambda c: c.data == 'reset')
async def reset_callback(callback: types.CallbackQuery):
    # Delete the original message
    await callback.message.delete()
    # Call the home_users function
    await home_users(callback.message)

@dp.message_handler()
async def generate_response(message: types.Message):
    cursor.execute("SELECT model FROM users WHERE user_id = {}".format(message.from_user.id))
    data = cursor.fetchone()

    if data is not None:
        response_type = int(data[0])
    else:
        # 
        # ...
        response_type = 0

    if response_type == 0:
        await process_question  (message)
    elif response_type == 1:
        await process_question(message)
    else:
        await process_question(message)




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


