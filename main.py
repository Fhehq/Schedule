import time
from datetime import datetime
from random import choice
import requests
from urllib3.exceptions import ProtocolError
import json

from telebot import types
from types import SimpleNamespace
import mysql


from bot import admin, admin_groups, campus
from bot.handlers import week_type, create_week_keyboard
from bot.schedule_handlers import get_schedule
from config import *
from bot.bd import *
from bot.admin_groups import all_groups, import_group

print(Fore.GREEN+"Бот запущен")

hello = [
    "👋🏿 Привет, ",
    "👋🏿 Здравствуй, ",
    "👋🏿 Приветствую, ",
    "👋🏿 Хей, ",
    "👋🏿 Добро пожаловать, ",
    "👋🏿 Рад видеть тебя, ",
    "👋🏿 Привет-привет, ",
    "👋🏿 Hola, ",
    "👋🏿 Здравия желаю, ",
    "👋🏿 Здарова, "
]

texts = [
    "🏬 Выбери корпус, чтобы увидеть расписание. Для звонков нажми кнопку ⬇️.",
    "🏬 Посмотри расписание, выбрав корпус! Звонки доступны по кнопке ⬇️.",
    "🏬 Чтобы посмотреть расписание, выбери корпус. Кнопка для звонков ждет тебя ⬇️.",
    "🏬 Выбери корпус для расписания. Звонки можно посмотреть через кнопку ⬇️.",
    "🏬 Чтобы увидеть расписание, жми на корпус. Для звонков нажми кнопку ⬇️.",
    "🏬 Выбери корпус, чтобы узнать расписание! Кнопка для звонков тоже тут ⬇️.",
    "🏬 Выбирай корпус, чтобы глянуть расписание. Звонки? Нажми на кнопку ⬇️.",
    "🏬 Хочешь расписание? Выбирай корпус. Кнопка для звонков внизу ⬇️.",
    "🏬 Жми на свое место обитания, чтобы увидеть расписание. Звонки смотри по кнопке ⬇️.",
    "🏬 Не забудь выбрать кампус для расписания. Кнопка звонков уже здесь ⬇️.",
    "🏬 Расписание ждет, выбери корпус. Для звонков нажми кнопку ⬇️.",
    "🏬 Чтобы узнать расписание, выбери корпус. Кнопка для звонков не подведет ⬇️.",
    "🏬 Выбирай корпус и смотри расписание. Звонки? Жми на кнопку ⬇️.",
    "🏬 Выбирай корпус для расписания! Звонки доступны по кнопке ⬇️.",
    "🏬 Расписание на корпусы доступно, выбери его. Кнопка звонков справа ⬇️.",
    "🏬 Готов увидеть расписание? Жми на выбор корпуса. Звонки смотри кнопкой ⬇️.",
    "🏬 Выбирай корпус и узнай расписание. Кнопка звонков рядом ⬇️.",
    "🏬 Узнай расписание в корпусе. Для звонков нажми кнопку ⬇️."
]


def get_group(campus: str) -> dict :
    with open("data/all_groups.json", "r", encoding="UTF-8") as file:
        data = json.load(file)
        return data[campus]


def text_random() -> str:
    """Случайное текст приветсвия"""
    r = choice(texts)
    return r   


def hello_random() -> str:
    """Случайное приветсвие"""
    r = choice(hello)
    return r


def get_keyboard_with_days(is_admin: bool = False, day: bool = False, user_id: int = 0):
    """Реплей-Кейбоард"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    has_group, _ = admin.check_user_group(user_id)
    if day or has_group:
        btn_today = types.KeyboardButton('📅 Сегодня')
        btn_tomorrow = types.KeyboardButton('📅 Завтра')
        keyboard.add(btn_today, btn_tomorrow)

    btn_start = types.KeyboardButton('🏠 Главное меню')
    btn_schedule = types.KeyboardButton('🏣 Все корпусы')
    btn_my_group = types.KeyboardButton('🗓️ Мое расписание')
    keyboard.add(btn_my_group)
    keyboard.add(btn_start, btn_schedule)

    if is_admin:
        btn_admin = types.KeyboardButton('⚙️ Админ панель')
        keyboard.add(btn_admin)

    return keyboard


@bot.callback_query_handler(func=lambda call: call.data == "remove_admin")
def remove_admin(callback):
    admin.remove_admin_handler(callback)
    
    
@bot.callback_query_handler(func=lambda call: call.data == "ban_menu")
def ban_menu(callback):
    admin.handle_ban_menu(callback)


@bot.callback_query_handler(func=lambda call: call.data == "ban_user")
def ban_user_callback(callback):
    admin.handle_ban_user(callback)
   
    
@bot.callback_query_handler(func=lambda call: call.data == "unban_user")
def ban_menu(callback):    
    admin.handle_unban_user(callback)


@bot.callback_query_handler(func=lambda call: call.data == "add_admin")
def add_admin(callback):
    admin.add_admin_handler(callback)


@bot.callback_query_handler(func=lambda call: call.data == "send_spam")
def send_spam(callback):
    admin.handle_spam(callback)


@bot.callback_query_handler(func=lambda call: call.data == "cancel_spam")
def cancel_spam(callback):
    admin.cancel_spam(callback)


@bot.callback_query_handler(func=lambda call: call.data == "log")
def check_log(callback):
    admin.handle_log(callback)


@bot.callback_query_handler(func=lambda call: call.data == "showlog")
def show_log(callback):
    admin.handle_show_log(callback)


@bot.callback_query_handler(func=lambda call: call.data == "delete_log")
def delete_log(callback):
    admin.handle_delete_log(callback)
    
    
@bot.callback_query_handler(func=lambda call: call.data == "delete_log_yes")
def delete_log_yes(callback):
    admin.handle_log_delete_yes(callback)


@bot.callback_query_handler(func=lambda call: call.data == "users")
def show_users(callback):
    admin.handle_users(callback)


@bot.callback_query_handler(func=lambda call: call.data == "user_id")
def show_user_id(callback):
    admin.handle_user_id(callback)
    
    
@bot.callback_query_handler(func=lambda call: "_cancel_add" in call.data)
def cancel_add_admin(callback):
    admin_groups.cancel_add_admin(callback, bot)


def correct_day_form(number: int) -> str:
    if number == 1:
        day = "день"
        return day
    elif 2 <= number <= 4:
        day = "дня"
        return day
    else:
        day = "дней"
        return day


def add_my_group(message) -> None:
    """Пользователь вводит группы и бот выводит группы с  сопадающим именем и callbeck_data - add_user_in_group_'name'"""
    group = message.text.upper()
    markup = types.InlineKeyboardMarkup()
    flag = False
    for g in all_groups:
        for sg in all_groups[g]["subgroups"]:
            eng_name = sg
            rus_name = all_groups[g]["subgroups"][sg]
            if group in rus_name:
                markup.add(types.InlineKeyboardButton(f"{rus_name}", callback_data=f"add_user_in_group_{eng_name}"))
                flag = True
    if flag: text = f"✅ Вот совпадения:"
    else: text = f"❌ Нет совпадений"
    bot.send_message(message.chat.id, text=text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "delete_my_group")
def delete_user_group(call):
    """Функия удаления своей группы"""
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    cursor = connection.cursor()
    cursor.execute("SELECT group_code FROM user_groups WHERE user_id = %s", (call.message.chat.id,))
    group_result = cursor.fetchone()
    
    if group_result:
        group_code = group_result[0]
        cursor.execute("SELECT student_ids FROM `groups` WHERE group_code = %s", (group_code,))
        result = cursor.fetchone()
        
        if result and result[0]:
            student_ids = result[0].split(',')
            student_ids.remove(str(call.message.chat.id))
            new_ids = ','.join(student_ids) if student_ids else None
            cursor.execute("UPDATE `groups` SET student_ids = %s WHERE group_code = %s", 
                         (new_ids, group_code))
    
    cursor.execute("DELETE FROM user_groups WHERE user_id = %s", (call.message.chat.id,))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    
    user_id = call.message.chat.id
    fake_message = SimpleNamespace(from_user=SimpleNamespace(id=user_id))
    is_admin_flag = admin.is_admin(fake_message)
    keyboard = get_keyboard_with_days(is_admin=is_admin_flag)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)

    bot.send_message(
        call.message.chat.id,
        text="✅ Ваша группа успешно удалена",
        reply_markup=keyboard
    )


@bot.message_handler(commands=["stats"])
def main(message):    
    """Получение краткой статистки бота"""
    len_user = len(admin.get_users())
    date_start = datetime(2025, 1, 27)
    current_date = datetime.now()
    delta = current_date - date_start
    days = delta.days+1
    markup = types.InlineKeyboardMarkup()
    main = types.InlineKeyboardButton("👣 Главное меню", callback_data="start")
    markup.row(main)
    bot.send_message(
        message.chat.id,
        text=f"👫 За все время в боте - {len_user} пользователей\n\n"
        
             f"⌛️ Бот работает уже - {days} {correct_day_form(days)}",
        reply_markup=markup
    )


@bot.message_handler(commands=["start"])
def main(message):
    "Главное меню"""
    ban_user = admin.get_banned_users()
    users = admin.get_users()
    if message.chat.id not in users:
        users.add(message.chat.id)
        admin.save_users(message)

    if message.chat.id not in ban_user:        
        keyboard = get_keyboard_with_days(is_admin = admin.is_admin(message), user_id = message.chat.id)
            
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('🏣 Все корпусы', callback_data='Korp')
        btn3 = types.InlineKeyboardButton('🔔 Звонки', callback_data='zvonki')
        info = types.InlineKeyboardButton("📁 Информация", callback_data = "info")
        markup.row(btn1, btn3)
        markup.row(info)

        
        if admin.is_admin(message):
            adm = types.InlineKeyboardButton("⚙️ Админ панель", callback_data="admpan")  
            markup.add(adm)


        sent_message = bot.send_message(
            message.chat.id,
            text = hello_random()+message.from_user.first_name,
            reply_markup=keyboard
            
        )
        
        bot.send_message(
            message.chat.id,
            text = text_random(),

            reply_markup=markup
        )

    else:
        bot.send_message(
            message.chat.id,
            text = "Вы забанены"
        )

@bot.callback_query_handler(func=lambda call: call.data == "start")
def handle_back_button(callback):
    """Главное меню(Кнопка назад)"""
    ban_user = admin.get_banned_users()
    if callback.message.chat.id not in ban_user:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('🏣 Выбрать корпус', callback_data='Korp')
        btn3 = types.InlineKeyboardButton('🔔 Звонки', callback_data='zvonki')
        info = types.InlineKeyboardButton("📁 Информация", callback_data = "info")
        markup.row(btn1, btn3)
        markup.row(info)

        if admin.is_admin(callback):
            adm = types.InlineKeyboardButton("⚙️ Админ панель", callback_data="admpan")        
            markup.add(adm) 
                               
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                                text = hello_random()+"снова "+callback.from_user.first_name+". \n\n"+text_random(), reply_markup=markup)
    else:
        bot.send_message(
            callback.message.chat.id,
            text = "🚫 Вы забанены!"
        )


@bot.callback_query_handler(func=lambda call: call.data == "admpan")
def handle_adm_back_button(callback):
    if admin.is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        add = types.InlineKeyboardButton("➕ Добавить Админа", callback_data="add_admin")       
        remove = types.InlineKeyboardButton("➖ Удалить Админа", callback_data="remove_admin") 
        spam = types.InlineKeyboardButton("💬 Рассылка", callback_data="send_spam") 
        users = types.InlineKeyboardButton("👥 Кол-во пользователь", callback_data="users") 
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        log = types.InlineKeyboardButton("🗒 Логи", callback_data="log")
        ban = types.InlineKeyboardButton("🚫 Баны", callback_data="ban_menu")
        markup.row(add, remove)
        markup.add(spam, log)
        markup.add(users, ban)
        markup.add(back)
        
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text=f"Здравствуйте админ, {callback.from_user.first_name} !\n\n Выберите действие:", reply_markup=markup)     
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id, text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.", reply_markup=markup)


@bot.callback_query_handler(func = lambda call: call.data == "info")
def handle_info_button(callback):    
    markup = types.InlineKeyboardMarkup()
    help = types.InlineKeyboardButton("💫Помощь", url = "")
    projects = types.InlineKeyboardButton("💻 Другие проекты", callback_data="projects")
    donate = types.InlineKeyboardButton("💰 Поддержать", callback_data="donate")
    back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
    markup.row(help)
    markup.row(projects)
    markup.row(donate)
    markup.add(back)
    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                          text = "🤖 Бот для просмотра расписания и звонков в колледже."
                          "\n\n‼️ Данный бот написан не колледжом."
                          "\n\n🫡 Пока что этот бот находится в бета тесте, если вы вдруг обнаружите какую то ошибку, то пишите и мы сразу ее исправим."
                          "\n\n🔫 Бот не несет отвественность за корректность расписания."
                          "\n\n🤓 В случае вопроса или жалобы работы бота напишите в поддержку.", reply_markup = markup)

@bot.callback_query_handler(func=lambda call: call.data == "donate")
def handle_donate_button(callback):
    markup = types.InlineKeyboardMarkup()
    back = types.InlineKeyboardButton("🔙 Назад", callback_data="info")
    donate = types.InlineKeyboardButton("💵 Счет", url="")
    markup.add(donate)
    markup.add(back)
    
    bot.edit_message_text(
        chat_id=callback.message.chat.id, 
        message_id=callback.message.id, 
        text="💸 Можете просто подержать нас и помочь с оплатой хоситинга или же перевести 200р и мы выложим ваш текст в бота)"
        "\n\n(Чтобы скопировать просто нажмите)"
        "\n\nКарта - ``"
        "\n\nTRC20 - `-`",
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "projects")
def handle_projects_button(callback):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🔜 Скоро', callback_data=' ')
    btn3 = types.InlineKeyboardButton('🔜 Скоро', callback_data=' ')
    back = types.InlineKeyboardButton("🔙 назад", callback_data="info")
    markup.row(btn1)
    markup.row(btn3)
    markup.row(back)           
    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.id,
                            text=f'😋 Наши другие проекты', reply_markup=markup) 


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    print(Fore.CYAN+f"Пришла call.data - {call.data}")
    if call.data == 'zvonki':
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="start")
        markup.add(back)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              text="🔔 Звонки:\nпонедельник:\n"
                                   "разговоры о важном: 8:30-9:15\n"
                                   "1 пара: 9:20-10:05 10:10-10:50\n"
                                   "2 пара: 11-15-12:00; 12:05-12:50\n"
                                   "3 пара: 13:20-14:05; 14:10-14:55\n"
                                   "4 пара: 15:15-16:00; 16:05-16:50\n\n"
                                   "Остальные дни\n"
                                   "1 пара: 8:30-9:15; 9:20-10:05\n"
                                   "2 пара: 10:25-11:10; 11:15-12:00\n"
                                   "3 пара: 12:30-13:15; 13:20-14:05\n"
                                   "4 пара: 14:25-15:10; 15:15-16:00\n", message_id=call.message.id,
                              reply_markup=markup)


    elif call.data == 'Korp':
        ban_user = admin.get_banned_users()
        if call.message.chat.id not in ban_user:
            ban_user = admin.get_banned_users()
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="start")
            Nov = types.InlineKeyboardButton(text="🏫 Новорязанская", callback_data="nov")
            Dub = types.InlineKeyboardButton(text="🏢 Дубининская", callback_data="dub")
            Sad = types.InlineKeyboardButton(text="🏬 Садовническая", callback_data="sad")
            markup.row(Nov)
            markup.row(Dub)
            markup.row(Sad)
            markup.add(back)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                text=f'Для выбора нажми на кнопку ⬇️', reply_markup=markup)
        else:
            bot.send_message(chat_id=callback.message.chat.id, text="🚫 Вы забанены!")


    elif call.data == 'dub':
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="🔙 Назад", callback_data="Korp")
        ipo = types.InlineKeyboardButton(text="💻 ИПО", callback_data="Dipo")
        gdo = types.InlineKeyboardButton(text="💻 ГДО", callback_data="gdo")
        tdo = types.InlineKeyboardButton(text="🛒 ТДО", callback_data="tdo")
        to = types.InlineKeyboardButton(text="♥️ ТО", callback_data="to")
        gds = types.InlineKeyboardButton(text="💻 ГДС", callback_data="gds")
        ips = types.InlineKeyboardButton(text="♥️ ИПС", callback_data="ips")
        sko = types.InlineKeyboardButton(text="💻 СКО", callback_data="Dsko")
        markup.row(ipo, gdo, tdo)
        markup.row(to, gds, ips, sko)
        markup.add(back)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f'✅ Отлично, вы выбрали корпус на Дубининской\n\nТеперь выбери свое направление',
                              reply_markup=markup)


    elif call.data == 'nov':
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="🔙 Назад", callback_data="Korp")
        ipo = types.InlineKeyboardButton(text="💻 ИПО", callback_data="Nipo")
        msho = types.InlineKeyboardButton(text="♥️ МШО", callback_data="msho")
        ksho = types.InlineKeyboardButton(text="♥️ КШО", callback_data="ksho")
        do = types.InlineKeyboardButton(text="♥️ ДО", callback_data="do")
        mfo = types.InlineKeyboardButton(text="♥️ МФО", callback_data="mfo")
        kshs = types.InlineKeyboardButton(text="♥️ КШС", callback_data="kshs")
        sko = types.InlineKeyboardButton(text="💻 СКО", callback_data="Nsko")
        ds = types.InlineKeyboardButton(text="♥️ ДС", callback_data="ds")
        pro = types.InlineKeyboardButton(text="♥️ ПРО", callback_data="Npro")
        markup.row(ipo, msho, ksho)
        markup.row(do, mfo, kshs)
        markup.row(sko, ds, pro)
        markup.add(back)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f'✅ Отлично, вы выбрали корпус на Новорязанской\n\nТеперь выбери свое направление',
                              reply_markup=markup)
        

    elif call.data == 'sad':
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="🔙 Назад", callback_data="Korp")
        ipo = types.InlineKeyboardButton(text="💻 ИПО", callback_data="Sipo")
        m = types.InlineKeyboardButton(text="💻 М", callback_data="m")
        gdo = types.InlineKeyboardButton(text="🛒 ГДО", callback_data="Sgdo")
        sko = types.InlineKeyboardButton(text="💻 СКО", callback_data="Ssko")
        markup.row(ipo, m, gdo, sko)
        markup.add(back)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f'✅ Отлично, вы выбрали корпус на Садовнической\n\nТеперь выбери свое направление',
                              reply_markup=markup)
    
    elif call.data.startswith("add_user_in_group"):
        group_name = call.data.replace("add_user_in_group_", "")
        user_id = call.message.chat.id
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        cursor = connection.cursor()
        
        try:
            cursor.execute("SELECT student_ids FROM `groups` WHERE group_code = %s", (group_name,))
            result = cursor.fetchone()
            
            if result:
                current_ids = result[0].split(',') if result[0] else []
                if str(user_id) not in current_ids:
                    current_ids.append(str(user_id))
                new_ids = ','.join(current_ids)
                cursor.execute("UPDATE `groups` SET student_ids = %s WHERE group_code = %s", 
                            (new_ids, group_name))
            else:
                cursor.execute("INSERT INTO `groups` (group_code, student_ids) VALUES (%s, %s)", 
                            (group_name, str(user_id)))
            
            cursor.execute("""
            INSERT INTO user_groups (user_id, group_code)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE group_code = %s
            """, (user_id, group_name, group_name))
            
            connection.commit()
                        
            group_code = group_name
            if group_code.endswith("d"):
                group_key = group_code[:-5]
            else:
                group_key = group_code[:-4]
            group_rus = admin_groups.all_groups[group_key]["subgroups"][group_code]
            
            fake_message = SimpleNamespace(from_user=SimpleNamespace(id=user_id))
            is_admin_flag = admin.is_admin(fake_message)
            keyboard = get_keyboard_with_days(is_admin = is_admin_flag, day = True)

            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)

            bot.send_message(
                chat_id=call.message.chat.id,
                text=f'✅ Отлично! Группа {group_rus} установлена как ваша основная группа',
                reply_markup=keyboard
            )
            
        finally:
            cursor.close()
            connection.close()


    elif call.data in get_group("dub"):
        campus.handle_campus_callbacks(call, bot, "dub")
    elif call.data in get_group("nov"):
        campus.handle_campus_callbacks(call, bot, "nov")
    elif call.data in get_group("sad"):
        campus.handle_campus_callbacks(call, bot, "sad")
    elif any(x in call.data.split('_')[0] for x in ['Dipo', 'gdo', 'tdo', 'Dsko', 'msho', 'to', 'gds', 'ips']):
        campus.handle_campus_callbacks(call, bot, "dub")       
    elif any(x in call.data.split('_')[0] for x in ['Nipo', 'Npro', 'ds', 'Nsko', 'kshs', 'mfo', 'do', 'ksho', 'msho']):
        campus.handle_campus_callbacks(call, bot, "nov")
    elif any(x in call.data.split('_')[0] for x in ['Sipo', 'Sgdo', 'Ssko', 'm', 'ds']):
        campus.handle_campus_callbacks(call, bot, "dub")


               
@bot.message_handler(content_types=['text'])
def handle_text(message):
    print(Fore.CYAN+f"Получено текстовое сообщение: {message.text}")
    if message.text == '🏠 Главное меню':
        print(Fore.CYAN+"Нажата кнопка Главное меню")
        ban_user = admin.get_banned_users()
        if message.chat.id not in ban_user:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('🏣 Выбрать корпус', callback_data='Korp')
            btn3 = types.InlineKeyboardButton('🔔 Звонки', callback_data='zvonki')
            info = types.InlineKeyboardButton("📁Информация", callback_data = "info")
            markup.row(btn1, btn3)
            markup.row(info)
            
            if admin.is_admin(message):
                adm = types.InlineKeyboardButton("⚙️ Админ панель", callback_data="admpan")        
                markup.add(adm)
                
            bot.send_message(
                message.chat.id,
                text = hello_random()+"снова "+message.from_user.first_name+".\n\n"+text_random(),
                reply_markup=markup
            )
        else:
            bot.send_message(message.chat.id, "🚫 Вы забанены!")

    elif message.text == '🏣 Все корпусы':
        ban_user = admin.get_banned_users()
        print(Fore.CYAN+"Нажата кнопка Расписание")
        if message.chat.id not in ban_user:
            ban_user = admin.get_banned_users()
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="start")
            Nov = types.InlineKeyboardButton(text="🏫 Новорязанская", callback_data="nov")
            Dub = types.InlineKeyboardButton(text="🏢 Дубининская", callback_data="dub")
            Sad = types.InlineKeyboardButton(text="🏬 Садовническая", callback_data="sad")
            markup.row(Nov)
            markup.row(Dub)
            markup.row(Sad)
            markup.add(back)
            bot.send_message(message.chat.id, text = 'Для выбора выбери корпус ⬇️', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text = "🚫 Вы забанены!")


    elif message.text == '⚙️ Админ панель':
        if admin.is_admin(message):
            markup = types.InlineKeyboardMarkup()
            add = types.InlineKeyboardButton("➕ Добавить Админа", callback_data="add_admin")       
            remove = types.InlineKeyboardButton("➖ Удалить Админа", callback_data="remove_admin") 
            spam = types.InlineKeyboardButton("💬 Рассылка", callback_data="send_spam") 
            users = types.InlineKeyboardButton("👥 Кол-во пользователь", callback_data="users") 
            back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
            log = types.InlineKeyboardButton("🗒 Логи", callback_data="log")
            ban = types.InlineKeyboardButton("🚫 баны", callback_data="ban_menu")
            markup.row(add, remove)
            markup.add(spam, log)
            markup.add(users, ban)
            markup.add(back)
            bot.send_message(message.chat.id, text=f"Здравствуйте админ, {message.from_user.first_name} !\n\nВыберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет прав администратора.")

    elif message.text == '🗓️ Мое расписание':  
        ban_user = admin.get_banned_users()
        if message.chat.id not in ban_user:
            has_group, group = admin.check_user_group(message.chat.id)
            print(has_group, group)
            if has_group:
                if group in get_group("nov"):
                    subgroup_key = group
                    campus = "nov"
                elif group in get_group("dub"):
                    subgroup_key = group
                    campus = "dub"
                elif group in get_group("sad"):
                    subgroup_key = group
                    campus = "sad"

                markup = create_week_keyboard(subgroup_key, message)
                groups = import_group(campus)
                for group_data in groups:
                    if subgroup_key in groups[group_data]["subgroups"]:
                        group_name = groups[group_data]["subgroups"][subgroup_key]
                        break

                bot.send_message(
                    chat_id=message.chat.id,
                    text=f'✅ Вы выбрали группу {group_name}\nВыберите тип недели:\n(Сейчас {week_type()} неделя)',
                    reply_markup=markup
                )
                
            else:
                msg = bot.send_message(message.chat.id, text=f"‼️ Вы еще не добавили свою группу!\n\n✒️ Напишите часть или полность вашу группу\n\nПримеры:\nИПО\nИПО-31.22\nИПО-31")
                bot.register_next_step_handler(msg, add_my_group)
        else:
            bot.send_message(message.chat.id, text = "🚫 Вы забанены!")
    
    elif message.text in ["📅 Сегодня", "📅 Завтра"]:
        ban_user = admin.get_banned_users()
        if message.chat.id not in ban_user:
            markup = types.InlineKeyboardMarkup()
            
            day_codes = {
                0: "mon",
                1: "tue", 
                2: "wed",
                3: "thu",
                4: "fri",
                5: False,
                6: False
            }

            _, group = admin.check_user_group(message.chat.id)
            if group in get_group("nov"):
                subgroup_key = group
                campus = "nov"
            elif group in get_group("dub"):
                subgroup_key = group
                campus = "dub"
            elif group in get_group("sad"):
                subgroup_key = group
                campus = "sad"

            today = datetime.now()
            weekday = today.weekday()
            tomorrow = (weekday + 1) % 7
            today = datetime.today()
            week_number = today.isocalendar()[1]
            week_suffix = "nechet" if week_number % 2 == 0 else "chet"
            
            if message.text == "📅 Сегодня":
                current_day = day_codes[weekday]
            else:
                current_day = day_codes[tomorrow]
                
            if current_day:
                if tomorrow == 0:
                    if week_suffix == "nechet":
                        week_suffix = "chet"
                    else:
                        week_suffix = "nechet"
                        
                schedule_text = get_schedule(week_suffix, current_day, group, campus)
                
                days_order = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4}
                days_list = ['mon', 'tue', 'wed', 'thu', 'fri']
                
                if week_suffix == "nechet":
                    reweek_suffix = "chet"
                else:
                    reweek_suffix = "nechet"
                nav_row = []
                
                if days_order[current_day] > 0:
                    prev_day = days_list[days_order[current_day] - 1]
                    prev_btn = types.InlineKeyboardButton("⬅️", callback_data=f"{group}_{week_suffix}_{prev_day}")
                    nav_row.append(prev_btn)
                if days_order[current_day] == 0:
                    next_btn = types.InlineKeyboardButton("⬅️", callback_data=f"{group}_{reweek_suffix}_fri")
                    nav_row.append(next_btn)
                            
                if days_order[current_day] < 4:
                    next_day = days_list[days_order[current_day] + 1]
                    next_btn = types.InlineKeyboardButton("➡️", callback_data=f"{group}_{week_suffix}_{next_day}")
                    nav_row.append(next_btn)
                if days_order[current_day] == 4:
                    next_btn = types.InlineKeyboardButton("➡️", callback_data=f"{group}_{reweek_suffix}_mon")
                    nav_row.append(next_btn)

                if nav_row:
                    markup.row(*nav_row)
            else:
                schedule_text = "🎉 Поздравляю, у вас выходной"
                back = types.InlineKeyboardButton("🔙 Главное меню", callback_data=f"start")
                markup.add(back)


            bot.send_message(message.chat.id, text = schedule_text, reply_markup=markup)

    try:
        admin_id = int(message.text)
        with mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        ) as conn:
            with conn.cursor(buffered=True) as cur:
                cur.execute("SELECT group_code FROM group_admins WHERE waiting_admin = TRUE")
                result = cur.fetchone()
                if result:
                    pass
    except ValueError:
        pass

         

while True:
    try:
        bot.polling(none_stop=True, 
                   timeout=60,
                   long_polling_timeout=60,
                   interval=3)
    except (requests.exceptions.ConnectionError, 
            ProtocolError,
            TimeoutError) as e:
        print(Fore.YELLOW + "Переподключение к серверам Telegram...")
        time.sleep(15)
        continue
    except Exception as e:
        print(Fore.RED + f"Ошибка в работе бота: {e}")
        time.sleep(15)
        continue
