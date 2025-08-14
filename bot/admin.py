from datetime import datetime
from random import choice as c


from telebot import types
import pymysql
import mysql
from colorama import init, Fore


from config import *


init(autoreset=True)

def check_user_group(user_id) -> bool | str:
    """Проверка добавил ли человек группу"""
    connection = mysql.connector.connect(
        host=host,
        user=user, 
        password=password,
        database=db_name
    )
    cursor = connection.cursor()
    
    cursor.execute("SELECT group_code FROM user_groups WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()

    if result:
        group_code = result[0]
        return True, group_code
    return False, None

def save_users(message):
    """Занесение новых юзеров в БД"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - новый пользователь {message.from_user.id} {message.from_user.first_name}\n"
        
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)

        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO users (user_id, user_name) VALUES (%s, %s)", 
                (message.from_user.id, message.from_user.username)
            )
        connection.commit()
    except Exception as ex:
        print(Fore.RED+f"‼️ Ошибка сохранения пользователей: {ex} ‼️")
    finally:
        if 'connection' in locals():
            connection.close()

def get_users() -> set[int]:
    """Получение юзеров"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user, 
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users")
            result = cursor.fetchall()
            return {row['user_id'] for row in result}
    except Exception as ex:
        print(Fore.RED+f"Ошибка получения пользователей: {ex}")
        return set()
    finally:
        if 'connection' in locals():
            connection.close()
            
     
def handle_ban_menu(callback):
    """Меню бана"""
    if is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        ban_user = types.InlineKeyboardButton("🔨 Забанить", callback_data="ban_user")
        unban_user = types.InlineKeyboardButton("🔓 Разбанить", callback_data="unban_user") 
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="admpan")
        markup.add(ban_user, unban_user)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="Выберите действие:",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )

def handle_ban_user(callback):
    """Обработчик блокировки юзера"""
    if is_admin(callback):
        msg = bot.send_message(callback.message.chat.id, "✍️ Введите ID пользователя для бана:")
        bot.register_next_step_handler(msg, process_ban_user)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )
def process_ban_user(message):
    """Ввод ID для блокировки"""
    try:
        user_id = int(message.text)
        if user_id in get_admins():
            text = "❌ Вы не можете заблокировать другого админа"
        else:
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO ban_users (user_id) VALUES (%s)", (user_id,))
            connection.commit()


            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - забанен пользователь {user_id} - забанил администратор {message.from_user.id} {message.from_user.first_name}\n"
            
            with open('log.txt', 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            text = f"✅ Пользователь с ID {user_id} успешно забанен"
            
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        
    except ValueError:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, "❌ Ошибка: ID должен быть числом", reply_markup=markup)

def handle_unban_user(callback):
    """Обработчик разбана юзера"""
    if is_admin(callback):
        msg = bot.send_message(callback.message.chat.id, "✍️ Введите ID пользователя для разбана:")
        bot.register_next_step_handler(msg, process_unban_user)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def process_unban_user(message):
    """Ввод ID для разбана"""
    try:
        user_id = int(message.text)
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM ban_users WHERE user_id = %s", (user_id,))
        connection.commit()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - разбанен пользователь {user_id} - разбанил администратор {message.from_user.id} {message.from_user.first_name}\n"
        
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, f"✅ Пользователь с ID {user_id} успешно разбанен", reply_markup=markup)
        
    except ValueError:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, "❌ Ошибка: ID должен быть числом", reply_markup=markup)


def get_banned_users() -> set:
    """Получние забаненных юзеров"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM ban_users")
            result = cursor.fetchall()
            return {row['user_id'] for row in result}
    except Exception as ex:
        print(Fore.RED+f"Ошибка получения заблокированных пользователей: {ex}")
        return set()
    finally:
        if 'connection' in locals():
            connection.close()
   

def get_admins() -> list:
    """Получение админов"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password, 
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT admin_id FROM admins")
            result = cursor.fetchall()
            return [row['admin_id'] for row in result]
    except Exception as ex:
        print(Fore.RED+f"Ошибка получения админов: {ex}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def save_admins(admin_ids, message):
    """Сохранение админа"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE admins")
            for admin_id in admin_ids:
                cursor.execute("INSERT INTO admins (admin_id, username) VALUES (%s, %s)", 
                            (admin_id, message.from_user.username))

        connection.commit()
    except Exception as ex:
        print(Fore.RED+f"Ошибка сохранения админов: {ex}")
    finally:
        if 'connection' in locals():
            connection.close()


def is_admin(message) -> bool:
    """Проверка на админа"""
    admin_ids = get_admins()
    return message.from_user.id in admin_ids


def handle_log(callback):
    """Меню логов"""
    if is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        check_log = types.InlineKeyboardButton("🗒 посмотерть логи", callback_data="showlog")
        delete_log = types.InlineKeyboardButton("🗑 удалить логи", callback_data="delete_log")
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="admpan")
        markup.add(check_log)
        markup.add(delete_log)
        markup.add(back)
        try:
            if callback.message and callback.message.text:
                bot.edit_message_text("😋 Выберите что хотите", 
                                    callback.message.chat.id, 
                                    callback.message.message_id, 
                                    reply_markup=markup)
            else:
                bot.send_message(callback.message.chat.id, 
                            "😋 Выберите что хотите", 
                            reply_markup=markup)
        except Exception as e:
            bot.send_message(callback.message.chat.id, 
                            "😋 Выберите что хотите", 
                            reply_markup=markup)

    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )
        

def handle_show_log(callback):
    """Отправка файла логов в чат"""
    if is_admin(callback) and callback.data == "showlog":
        try:
            if os.path.exists('log.txt') and os.path.getsize('log.txt') > 0:
                with open('log.txt', 'rb', encoding="UTF-8") as f:
                    markup = types.InlineKeyboardMarkup()
                    back = types.InlineKeyboardButton("🔙 Назад", callback_data="log")
                    markup.add(back)
                    
                    bot.send_document(callback.message.chat.id,
                                    document=f,
                                    caption="📝 Содержимое логов",
                                    reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton("🔙 Назад", callback_data="log")
                markup.add(back)
                
                bot.send_message(callback.message.chat.id,
                               "📝 Логи пусты",
                               reply_markup=markup)
                               
        except Exception as e:
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton("🔙 Назад", callback_data="showlog")
            markup.add(back)
            
            bot.send_message(callback.message.chat.id,
                           "❌ Ошибка при чтении логов",
                           reply_markup=markup)



    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то перейдите админ панель через вашу группу", reply_markup=markup)
    
    
def handle_delete_log(callback):
    """Удаление логов"""
    if is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="admpan")
        yes = types.InlineKeyboardButton("✅ Да", callback_data="delete_log_yes")
        markup.add(yes)
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="Вы уверены что хотите удалить логи?",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def handle_log_delete_yes(callback):
    """Подтвреждение удаление логов"""
    if is_admin(callback):
        letter = "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890"
        kapcha = "".join([c(letter) for _ in range(5)])
 

        markup = types.InlineKeyboardMarkup()
        cancel = types.InlineKeyboardButton("⚙️ Админ меню", callback_data="admpan")
        markup.add(cancel)
        
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        
        msg = bot.send_message(callback.message.chat.id,
                             f"Для удаления логов введите капчу: {kapcha}")
        
        def check_captcha(message):
            try:
                if message.text == kapcha:
                    with open('log.txt', 'w', encoding='utf-8') as f:
                        f.write('')
                    bot.send_message(message.chat.id, "✅ Логи успешно удалены", reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, "❌ Неверная капча", reply_markup=markup)
            except:
                bot.send_message(message.chat.id, "❌ Ошибка при удалении логов", reply_markup=markup)
                
        bot.register_next_step_handler(msg, check_captcha)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )            
          
  
def handle_admin_panel(callback):
    """Обработчик админ панели"""
    if is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        add = types.InlineKeyboardButton("➕ Добавить Админа", callback_data="add_admin")
        remove = types.InlineKeyboardButton("➖ Удалить Админа", callback_data="remove_admin")
        spam = types.InlineKeyboardButton("💬 Рассылка", callback_data="send_spam")
        users = types.InlineKeyboardButton("👥 Кол-во пользователь", callback_data="users")
        change_zvonki = types.InlineKeyboardButton("🔔 Изменить звонки", callback_data="change_zvonki")
        log = types.InlineKeyboardButton("🗒 Логи", callback_data="log")
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        
        markup.row(add, remove)
        markup.add(spam, users)
        markup.add(change_zvonki)
        markup.add(log)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text=f"🫡 Здравствуйте администратор, {callback.from_user.first_name}! Выберите действие:",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def handle_spam(callback):
    """Обработчик рассылки"""
    if is_admin(callback):
        global is_spam_cancelled
        is_spam_cancelled = False
        markup = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton("❌ Отменить рассылку", callback_data="cancel_spam")
        markup.add(cancel_button)
        msg = bot.send_message(callback.message.chat.id, "Введите текст для рассылки:", reply_markup=markup)
        bot.register_next_step_handler(msg, ask_add_admin_button)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒У вас нет доступа\n\nЕсли вы админ какой-либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def ask_add_admin_button(message):
    """Спрашивает нужна ли ссылка на админа"""
    global spam_text
    spam_text = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="add_btn_yes"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="add_btn_no"))

    bot.send_message(message.chat.id, "Добавить кнопку с ссылкой на админа?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["add_btn_yes", "add_btn_no"])
def process_add_admin_button_choice(call):
    if call.data == "add_btn_yes":
        process_spam_text(call.message, add_admin_button=True)
    else:
        process_spam_text(call.message, add_admin_button=False)


def process_spam_text(message, add_admin_button=False):
    """Ввод текста рассылки и ее реализация"""
    global is_spam_cancelled, spam_text

    reply_markup = None
    if add_admin_button:
        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.add(types.InlineKeyboardButton("Связь с админом", url=""))

    if spam_text:
        users = get_users()
        for user_id in users:
            if is_spam_cancelled:
                markup = types.InlineKeyboardMarkup()
                admmen = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
                markup.add(admmen)
                bot.send_message(message.chat.id, "❌ Рассылка была отменена.", reply_markup=markup)
                break
            try:
                bot.send_message(user_id, spam_text, reply_markup=reply_markup)
            except Exception as e:
                print(Fore.RED + f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - запущена рассылка - {message.chat.id}\n"

            with open('log.txt', 'a', encoding='utf-8') as f:
                f.write(log_entry)

            if not is_spam_cancelled:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admpan"))
                bot.send_message(message.chat.id, "✅ Рассылка завершена.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "‼️ Сообщение не может быть пустым. ‼️")

def cancel_spam(call):
    """Обработчик отмены рассылки"""
    if is_admin(call):
        global is_spam_cancelled
        is_spam_cancelled = True
        markup = types.InlineKeyboardMarkup()
        admmen = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
        markup.add(admmen)
        bot.send_message(call.message.chat.id, "❌ Рассылка отменена.", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="🔒У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )
        
        
def handle_users(callback):
    """Получние кол-во юзеров"""
    if is_admin(callback):
        len_user = len(get_users())
        markup = types.InlineKeyboardMarkup()
        user_id = types.InlineKeyboardButton("🙋🏻 Их id/name", callback_data="user_id")
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="admpan")
        markup.add(user_id)
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text=f"👣 Количетсво пользователей:{len_user}\n",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒 У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def handle_user_id(callback):
    if is_admin(callback):
        id_name = [user for user in get_users()]
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="users")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text=f"{id_name}",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒 У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )
        
        
def add_admin_handler(callback):
    """Добавление нового админа"""
    if is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("❌ Отмена", callback_data="admpan")
        markup.add(back)
        msg = bot.send_message(callback.message.chat.id, "✍️ Введите ID нового администратора:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_admin_id)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒 У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def process_admin_id(message):
    """Ввод ID нового админа"""
    try:
        new_admin_id = int(message.text)
        admin_ids = get_admins()
        
        if new_admin_id in admin_ids:
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
            markup.add(back)
            bot.send_message(message.chat.id, "‼️ Этот пользователь уже является администратором. ‼️", reply_markup=markup)
            return

        admin_ids.append(new_admin_id)
        save_admins(admin_ids)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - добавили админа {new_admin_id} добавил - {message.from_user.id} {message.from_user.first_name}\n"

        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️Админ Меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, f"✅Администратор с ID {new_admin_id} успешно добавлен.", reply_markup=markup)
        
        for owner_id in []:
            bot.send_message(owner_id, f"🔔 {timestamp} - добавили админа\nID: {new_admin_id}\nДобавил: {message.from_user.first_name} ({message.from_user.id})")

    except ValueError:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, "❌ Ошибка: ID должен быть числом.", reply_markup=markup)
        

def remove_admin_handler(callback):
    """Удаление админа"""
    if is_admin(callback):
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
        markup.add(back)
        msg = bot.send_message(callback.message.chat.id, "✍️ Введите ID администратора, которого хотите удалить:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_remove_admin)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        markup.add(back)
        bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            text="🔒 У вас нету доступа\n\nЕсли вы админ какой то либо группы, то переходите в админ панель через вашу группу.",
            reply_markup=markup
        )


def process_remove_admin(message):
    """Ввод ID для удаления админа"""
    try:
        admin_id = int(message.text)
        admin_ids = get_admins()
        if admin_id not in admin_ids:
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
            markup.add(back)
            bot.send_message(message.chat.id, "‼️ Этот пользователь не является администратором. ‼️", reply_markup=markup)
            return
        if admin_id == "id_MainAdmin":
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
            markup.add(back)
            bot.send_message(message.chat.id, "❌ Невозможно удалить основного администратора.", reply_markup=markup)
            return
        admin_ids.remove(admin_id)
        save_admins(admin_ids)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - удалили админа {admin_id} удалил - {message.from_user.id} {message.from_user.first_name}\n"

        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
        for owner_id in []:
            bot.send_message(owner_id, f"{timestamp} - удалили админа {admin_id} удалил - {message.from_user.id} {message.from_user.first_name}\n")
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, f"✅ Администратор с ID {admin_id} успешно удален.", reply_markup=markup)

    except ValueError:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("⚙️ Админ Меню", callback_data="admpan")
        markup.add(back)
        bot.send_message(message.chat.id, "❌ Ошибка: ID должен быть числом.", reply_markup=markup)
