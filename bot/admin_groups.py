from datetime  import datetime
import json


from colorama import init, Fore
from telebot import types
import mysql.connector
import pymysql


from config import host, user, password, db_name, bot
from bot.admin import is_admin


init(autoreset=True)

def import_group(campus) -> dict:
    """Получение вссех групп"""
    with open("data/groups.json", "r", encoding="UTF-8") as file:
        data = json.load(file)
        if campus == "all":
            return {k: v for key, value in data.items() for k, v in value.items()}
        return data[campus]
        

all_groups  = import_group("all")


def get_admins() -> list[int]:
    """Получние админов"""
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
        print(Fore.CYAN+f"Ошибка получения админов: {ex}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()


def save_admins(admin_ids):
    """Сохранение нового админа"""
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
                cursor.execute("INSERT INTO admins (admin_id) VALUES (%s)", (admin_id,))
        connection.commit()
    except Exception as ex:
        print(Fore.RED+f"Ошибка сохранения админов: {ex}")
    finally:
        if 'connection' in locals():
            connection.close()
          
            
def is_group_admin(call, group_code: str) -> bool:
    """Является ли человек админов группы"""
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    cur = conn.cursor()
    
    query = "SELECT * FROM group_admins WHERE admin_id = %s AND group_code = %s"
    cur.execute(query, (call.from_user.id, group_code))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result is not None


def handle_admin_panel(call, bot):
    """Обрабатывает админ панель"""
    group_code = call.data.replace("_adm", "")
    print(Fore.CYAN+f"⚙️ Админ панель для группы {group_code}")        
    if is_group_admin(call, group_code) or is_admin(call):   
        if group_code.endswith("d"):
            group_key = group_code[:-5]
        else:
            group_key = group_code[:-4]
        group_rus = all_groups[group_key]["subgroups"][group_code]
                
        markup = types.InlineKeyboardMarkup()
        edit_schedule = types.InlineKeyboardButton("📝 Редактировать расписание", callback_data=f"{group_code}_edit")
        add_admin = types.InlineKeyboardButton("➕ Добавить админа", callback_data=f"{group_code}_add_admin")
        remove_admin = types.InlineKeyboardButton("➖ Удалить админа", callback_data=f"{group_code}_remove_admin")
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=group_code)
        
        markup.add(edit_schedule)
        markup.row(add_admin, remove_admin)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=f"⚙️ Админ панель - {group_rus}",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=group_code)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="❌ У вас нет прав администратора для этой группы",
            reply_markup=markup
        )
        
        
def handle_add_group_admin(call, bot):
    """Добавление админа"""
    if is_group_admin(call, group_code) or is_admin(call):  
        group_code = call.data.split("_add_admin")[0]
        
        with mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        ) as conn:
            with conn.cursor(buffered=True) as cur:
                cur.execute("INSERT IGNORE INTO group_admins (group_code, waiting_admin) VALUES (%s, TRUE)", 
                        (group_code,))
                cur.execute("UPDATE group_admins SET waiting_admin = TRUE WHERE group_code = %s", 
                        (group_code,))
                conn.commit()
        
        markup = types.InlineKeyboardMarkup()
        cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f"{group_code}_cancel_add")
        markup.add(cancel)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="📬 Отправьте ID пользователя, которого хотите назначить администратором группы.",
            reply_markup=markup
        )
        bot.register_next_step_handler(call.message, process_new_admin_id, group_code)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=group_code)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="❌ У вас нет прав администратора для этой группы",
            reply_markup=markup
        )
    

def process_new_admin_id(message, group_code):
    """Ввод нового админа"""
    try:
        new_admin_id = int(message.text)
        
        with mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        ) as conn:
            with conn.cursor(buffered=True) as cur:
                cur.execute("INSERT INTO group_admins (group_code, admin_id) VALUES (%s, %s)",
                          (group_code, new_admin_id))
                conn.commit()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - добавлен админ {new_admin_id} в админ панель группы {group_code} - добавил администратор {message.from_user.id} {message.from_user.first_name}\n"
        
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)


        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=f"{group_code}_adm")
        markup.add(back)
        
        bot.send_message(message.chat.id,
                        f"✅ Администратор (ID: {new_admin_id}) успешно добавлен",
                        reply_markup=markup)
                        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка: ID должен быть числом")


def cancel_add_admin(call, bot):
    """Отмена добавления"""
    if is_group_admin(call, group_code) or is_admin(call):
        group_code = call.data.split('_cancel_')[0]
        
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=f"{group_code}_adm")
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="❌ Действие отменено",
            reply_markup=markup
        )
        
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=group_code)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="❌ У вас нет прав администратора для этой группы",
            reply_markup=markup
        )


def handle_remove_group_admin(call, bot):
    """Удаления админа"""
    if is_group_admin(call, group_code) or is_admin(call):
        group_code = call.data.split("_remove_admin")[0]
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=f"{group_code}_cancel_add")
        markup.add(back)
        msg = bot.send_message(call.message.chat.id, "📬 Введите ID администратора группы, которого хотите удалить:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: process_remove_group_admin(m, bot, group_code))
    else:
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙 Назад", callback_data=group_code)
        markup.add(back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="❌ У вас нет прав администратора для этой группы",
            reply_markup=markup
        )


def process_remove_group_admin(message, bot, group_code):
    """Ввод ID для удаления"""
    if is_group_admin(message, group_code) or is_admin(message):
        try:
            admin_id = int(message.text)
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM group_admins WHERE group_code = %s AND admin_id = %s",
                        (group_code, admin_id))
            
            if cursor.fetchone():
                cursor.execute("DELETE FROM group_admins WHERE group_code = %s AND admin_id = %s",
                            (group_code, admin_id))
                conn.commit()
                
                markup = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton("🔙 Назад", callback_data=f"{group_code}_adm")
                markup.add(back)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"{timestamp} удален админ {admin_id} из админ панели группы {group_code} - удалил администратор {message.from_user.id} {message.from_user.first_name}\n"
        
                with open('log.txt', 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                bot.send_message(message.chat.id, 
                            f"✅ Администратор (ID: {admin_id}) успешно удален",
                            reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "❌ Администратор с таким ID не найден")
                
            cursor.close()
            conn.close()
            
        except ValueError:
            bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректный ID")
        else:
            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton("🔙 Назад", callback_data=group_code)
            markup.add(back)
            
            bot.edit_message_text(
                chat_id=message.message.chat.id,
                message_id=message.message.id,
                text="❌ У вас нет прав администратора для этой группы",
                reply_markup=markup)