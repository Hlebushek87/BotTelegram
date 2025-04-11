import sqlite3
import telebot
import re
from telebot import types

bot = telebot.TeleBot('7701081384:AAEXnHumeQkJ3v6KqbLyeVmrWx9nluv0bYw')
conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()
conn.commit()


def db_table_val(user_id: int, user_name: str, user_surname: str, username: str, phone_number: str,
                 order_amount: str = None):
    if order_amount is not None:
        cursor.execute('SELECT order_amount FROM pizzabotdb WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                total = float(result[0]) + float(order_amount)
                order_amount = str(total)
            except ValueError:
                pass

    cursor.execute(
        'INSERT OR REPLACE INTO pizzabotdb (user_id, user_name, user_surname, username, phone_number, order_amount) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, user_name, user_surname, username, phone_number, order_amount))
    conn.commit()


def get_user_phone(user_id: int) -> str:
    cursor.execute('SELECT phone_number FROM pizzabotdb WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def is_valid_phone_number(phone_number: str) -> bool:
    pattern = re.compile(r'^(\+7|7|8)?\d{10}$')
    return bool(pattern.match(phone_number))



menu = {
    "Пепперони": 500,
    "Маргарита": 450,
    "Гавайская": 550,
    "Четыре сыра": 600,
    "Вегетарианская": 400,
}


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Об организации')
    btn2 = types.KeyboardButton('Тех.поддержка')
    btn3 = types.KeyboardButton('Меню')
    btn4 = types.KeyboardButton('Сделать заказ')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.from_user.id,
                     'Здравствуйте! Приветствуем Вас в нашем чат-боте пиццерии! Здесь вы можете посмотреть меню, сделать заказ, узнать контакты нашей организации и написать в тех.поддержку',
                     reply_markup=markup)

    us_id = message.from_user.id
    us_name = message.from_user.first_name
    us_sname = message.from_user.last_name
    username = message.from_user.username

    db_table_val(user_id=us_id, user_name=us_name, user_surname=us_sname, username=username, phone_number=None,
                 order_amount=None)


@bot.message_handler(commands=['change_phone'])
def change_phone(message):
    msg = bot.send_message(message.from_user.id,
                           'Введите новый номер телефона (например, +79991234567 или 89991234567):',
                           parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_phone_step)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'Об организации':
        bot.send_message(message.from_user.id, 'Ботопицца - сеть пиццерий, готовящих самую сочную, горячую и вкусную пиццу на вашем районе!', parse_mode='Markdown')

    elif message.text == 'Тех.поддержка':
        bot.send_message(message.from_user.id,
                         'Здесь вы можете сообщить о найденной вами ошибке. Или, если у вас возникли предложения или жалобы, то можете тоже писать сюда @Helper',
                         parse_mode='Markdown')

    elif message.text == 'Меню':
        menu_text = "Меню:\n"
        for item, price in menu.items():
            menu_text += f"{item}: {price} руб.\n"
        bot.send_message(message.from_user.id, menu_text, parse_mode='Markdown')

    elif message.text == 'Сделать заказ':
        user_id = message.from_user.id
        phone_number = get_user_phone(user_id)

        if phone_number:
            msg = bot.send_message(message.from_user.id,
                                   'Пожалуйста, введите ваш заказ (например, "Пепперони, Маргарита"):',
                                   parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_order_step)
        else:
            msg = bot.send_message(message.from_user.id,
                                   'Пожалуйста, введите ваш номер телефона (например, +79991234567 или 89991234567):',
                                   parse_mode='Markdown')
            bot.register_next_step_handler(msg, process_phone_step)

    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки ниже для взаимодействия с ботом.')


def process_phone_step(message):
    try:
        phone_number = message.text.strip()

        if not is_valid_phone_number(phone_number):
            bot.send_message(message.from_user.id,
                             'Некорректный номер телефона. Пожалуйста, введите номер в формате +79991234567 или 89991234567.')
            return

        us_id = message.from_user.id
        us_name = message.from_user.first_name
        us_sname = message.from_user.last_name
        username = message.from_user.username

        db_table_val(user_id=us_id, user_name=us_name, user_surname=us_sname, username=username,
                     phone_number=phone_number)

        msg = bot.send_message(message.from_user.id,
                               'Спасибо! Теперь введите ваш заказ (например, "Пепперони, Маргарита"):',
                               parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_order_step)
    except Exception as e:
        bot.reply_to(message, 'Ошибка при сохранении номера телефона.')


def process_order_step(message):
    try:
        order_text = message.text.strip()
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        msg = bot.send_message(message.from_user.id, 'Пожалуйста, введите адрес доставки:')
        bot.register_next_step_handler(msg, lambda m: process_address_step(m, order_text, user_id, user_name))
    except Exception as e:
        bot.reply_to(message, 'Ошибка при обработке заказа.')


def process_address_step(message, order_text, user_id, user_name):
    try:
        address = message.text.strip()

        order_items = [item.strip() for item in order_text.split(",")]
        total_amount = 0
        valid_items = []

        for item in order_items:
            if item in menu:
                total_amount += menu[item]
                valid_items.append(item)

        if not valid_items:
            bot.send_message(message.from_user.id,
                             'В вашем заказе не найдено блюд из нашего меню. Пожалуйста, начните заказ заново.')
            return

        phone_number = get_user_phone(user_id)

        admin_chat_id = 1350688295
        bot.send_message(
            admin_chat_id,
            f'Новый заказ от пользователя {user_name} (ID: {user_id}, телефон: {phone_number}):\n'
            f'Заказ: {", ".join(valid_items)}\n'
            f'Адрес доставки: {address}\n'
            f'Сумма заказа: {total_amount} руб.'
        )

        db_table_val(
            user_id=user_id,
            user_name=user_name,
            user_surname=message.from_user.last_name,
            username=message.from_user.username,
            phone_number=phone_number,
            order_amount=str(total_amount) )

        bot.send_message(
            message.from_user.id,
            f'Спасибо за ваш заказ!\n'
            f'Ваш заказ: {", ".join(valid_items)}\n'
            f'Адрес доставки: {address}\n'
            f'Сумма заказа: {total_amount} руб.\n'
            f'Мы свяжемся с вами в ближайшее время.',
            parse_mode='Markdown'
        )
    except Exception as e:
        bot.reply_to(message, 'Ошибка при обработке адреса доставки.')


bot.polling(none_stop=True, interval=0)