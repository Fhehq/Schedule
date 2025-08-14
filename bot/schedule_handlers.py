import json


from colorama import init, Fore
from telebot import types
import mysql.connector


from config import host, user, password, db_name
from bot.admin import is_admin


init(autoreset=True)

DAYS = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница")
DAYS_ENG = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')

def import_group(campus: str) -> dict: 
    """Возвращает словрь с группами"""
    with open("data/groups.json", "r", encoding="UTF-8") as file:
        data = json.load(file)
        if campus == "all":
            return {k: v for key, value in data.items() for k, v in value.items()}
        return data[campus]


def is_group_admin(call, group_code: str) -> bool:
    """Проверка является ли человек админом группы"""
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


def handle_schedule_day(call, bot, day_name, campus):
    """Вывод расписания"""
    group = call.data.split("_")[0]
    week_type = "нечетная" if "_nechet" in call.data else "четная"
    week_suffix = "nechet" if "_nechet" in call.data else "chet"

    current_day = call.data.split("_")[2]
    markup = types.InlineKeyboardMarkup()
    
    days_order = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4}
    days_list = ['mon', 'tue', 'wed', 'thu', 'fri']
    schedule_text = get_schedule(week_suffix, current_day, group, campus)
    
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
        
    back = types.InlineKeyboardButton(text="🔙 Назад", callback_data=f"{group}_{week_suffix}")
    markup.add(back)
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=schedule_text,
        reply_markup=markup
    )


def get_schedule(week_suffix, current_day, group, campus) -> str:
    """Получение пар"""
    days_map = {
        'mon': 'понедельник',
        'tue': 'вторник',
        'wed': 'среду', 
        'thu': 'четверг',
        'fri': 'пятницу'
    }
    
    day_name = days_map[current_day]
    week_type = "нечетная" if week_suffix == "nechet" else "четная"
    group_name = None
    
    groups = import_group(campus)
    
    for group_data in groups.values():
        if group in group_data["subgroups"]:
            group_name = group_data["subgroups"][group]
            break

    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    cur = conn.cursor()
    
    query = """
    SELECT lesson_1, lesson_2, lesson_3, lesson_4, lesson_5
    FROM schedules 
    WHERE group_code = %s AND week_type = %s AND day = %s
    """
    cur.execute(query, (group, week_suffix, current_day))
    lessons = cur.fetchall()

    schedule_text = f"Расписание на {day_name} для группы {group_name} ({week_type} неделя):\n\n"
    if lessons:
        lessons = lessons[0]
        for i, lesson in enumerate(lessons, 1):
            schedule_text += f"{i} пара: {lesson if lesson and lesson.strip() else 'Пары нет или её не добавили'}\n"
    cur.close()
    conn.close()
    return schedule_text


def handle_edit_schedule(call, bot):
    """Обработчик изменение расписания (Выбор недели)"""
    group_code = call.data.replace("_edit", "")
    
    if not (is_group_admin(call, group_code) or is_admin(call)):
        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙Назад", callback_data=f"{group_code}_adm")
        markup.add(back)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text="У вас нет прав для редактирования расписания",
            reply_markup=markup
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    chet = types.InlineKeyboardButton("🗓️Четная неделя", callback_data=f"{group_code}_edit_chet")
    nechet = types.InlineKeyboardButton("🗓️Нечетная неделя", callback_data=f"{group_code}_edit_nechet")
    markup.row(chet, nechet)
    back = types.InlineKeyboardButton("🔙Назад", callback_data=f"{group_code}_adm")
    markup.add(back)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text="🗓️ Выберите неделю для редактирования расписания:",
        reply_markup=markup
    )


def handle_edit_week_select(call, bot):
    """Обработчик изменения расписания (выбор дня)"""
    group_code = call.data.split("_edit_")[0]
    week_type = call.data.split("_edit_")[1]
    
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        day_code = DAYS_ENG[DAYS.index(day)][:3].lower()
        btn = types.InlineKeyboardButton(day, callback_data=f"{group_code}_edit_{week_type}_{day_code}")
        markup.add(btn)
    
    back = types.InlineKeyboardButton("🔙Назад", callback_data=f"{group_code}_edit")
    markup.add(back)
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=f"📆 Выберите день для редактирования расписания:",
        reply_markup=markup
    )


def handle_edit_day_select(call, bot):
    """Обработчик изменения расписания"""
    parts = call.data.split("_edit_")
    group_code = parts[0]
    week_type, day = parts[1].split("_")
    day_names = {
        'mon': 'Понедельник',
        'tue': 'Вторник',
        'wed': 'Среда',
        'thu': 'Четверг',
        'fri': 'Пятница'
    }
    day_name = day_names[day]
    week_type_name = "четная" if week_type == "chet" else "нечетная"

    with mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    ) as conn:
        with conn.cursor(buffered=True) as cur:
            query = "SELECT lesson_1, lesson_2, lesson_3, lesson_4, lesson_5 FROM schedules WHERE group_code = %s AND week_type = %s AND day = %s"
            cur.execute(query, (group_code, week_type, day))
            current_schedule = cur.fetchone() or ("", "", "", "", "")

    markup = types.InlineKeyboardMarkup()
    edit_all = types.InlineKeyboardButton(
        "📝 Редактировать весь день",
        callback_data=f"{group_code}_edit_{week_type}_{day}_all"
    )
    markup.add(edit_all)

    for i in range(5):
        btn = types.InlineKeyboardButton(
            f"{'✏️' if current_schedule[i] else '➕'} Пара {i+1}",
            callback_data=f"{group_code}_edit_{week_type}_{day}_{i+1}"
        )
        markup.add(btn)

    back = types.InlineKeyboardButton("🔙Назад", callback_data=f"{group_code}_edit_{week_type}")
    markup.add(back)

    schedule_text = f"Редактирование расписания\n{day_name} ({week_type_name} неделя)\n\nТекущее расписание:\n\n"
    for i, lesson in enumerate(current_schedule, 1):
        schedule_text += f"{i} пара: {lesson if lesson and lesson.strip() else 'Пары нет или ее не добавили'}\n"

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=schedule_text + "\nВыберите действие:",
        reply_markup=markup
    )


def save_lesson(message, bot, group_code, week_type, day, lesson_num):
    """Сохранения пары после изменения"""
    with mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    ) as conn:
        with conn.cursor(buffered=True) as cur:
            lesson_column = f"lesson_{lesson_num}"
            cur.execute("SELECT 1 FROM schedules WHERE group_code = %s AND week_type = %s AND day = %s",
                       (group_code, week_type, day))
            exists = cur.fetchone()

            if exists:
                query = f"UPDATE schedules SET {lesson_column} = %s WHERE group_code = %s AND week_type = %s AND day = %s"
            else:
                query = f"INSERT INTO schedules (group_code, week_type, day, {lesson_column}) VALUES (%s, %s, %s, %s)"

            cur.execute(query, (message.text, group_code, week_type, day))
            
            cur.execute("""
                SELECT lesson_1, lesson_2, lesson_3, lesson_4, lesson_5 
                FROM schedules 
                WHERE group_code = %s AND week_type = %s AND day = %s
            """, (group_code, week_type, day))
            lessons = cur.fetchone()
            
            cur.execute("SELECT student_ids FROM `groups` WHERE group_code = %s", (group_code,))
            result = cur.fetchone()
            
            
            day_names = {
                    'mon': 'Понедельник',
                    'tue': 'Вторник',
                    'wed': 'Среда',
                    'thu': 'Четверг',
                    'fri': 'Пятница'}
                
            if week_type == "chet":
                week_type_rus = "четная"
            else:
                week_type_rus = "нечетная"
            if result and result[0] and lessons:
                student_ids = result[0].split(',')
                
                notification_text = f"🔔 Обновлено расписание на {day_names[day]} ({week_type_rus} неделя):\n\n"
                for i, lesson in enumerate(lessons, 1):
                    notification_text += f"{i} пара: {lesson if lesson else 'Пары нет или её не добавили'}\n"
                
                for student_id in student_ids:
                    try:
                        bot.send_message(chat_id=int(student_id), text=notification_text)
                    except:
                        continue
                        
            conn.commit()

            markup = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton("🔙К выбору пары",
                                            callback_data=f"{group_code}_edit_{week_type}_{day}")
            markup.add(back)

            bot.send_message(
                chat_id=message.chat.id,
                text="✅ Расписание успешно обновлено!",
                reply_markup=markup
            )


def save_full_day(message, bot, group_code, week_type, day):
    """Сохранения дня после изменения"""
    try:
        lessons = []
        for line in message.text.split('\n'):
            if line.strip():
                lessons.append(line.strip())
            else:
                lessons.append("")

        while len(lessons) < 5:
            lessons.append("")
        lessons = lessons[:5]

        with mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        ) as conn:
            with conn.cursor(buffered=True) as cur:
                cur.execute("SELECT 1 FROM schedules WHERE group_code = %s AND week_type = %s AND day = %s",
                    (group_code, week_type, day))
                exists = cur.fetchone()

                params = tuple(lessons) + (group_code, week_type, day)

                if exists:
                    query = """UPDATE schedules 
                    SET lesson_1 = %s, lesson_2 = %s, lesson_3 = %s, lesson_4 = %s, lesson_5 = %s
                    WHERE group_code = %s AND week_type = %s AND day = %s"""
                else:
                    query = """INSERT INTO schedules 
                    (lesson_1, lesson_2, lesson_3, lesson_4, lesson_5,
                    group_code, week_type, day)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

                cur.execute(query, params)
                cur.execute("SELECT student_ids FROM `groups` WHERE group_code = %s", (group_code,))
                result = cur.fetchone()
                
                day_names = {
                    'mon': 'Понедельник',
                    'tue': 'Вторник',
                    'wed': 'Среда',
                    'thu': 'Четверг',
                    'fri': 'Пятница'}
                
                if week_type == "chet":
                    week_type_rus = "четная"
                else:
                    week_type_rus = "нечетная"
                    
                if result and result[0]:
                    student_ids = result[0].split(',')
                
                    notification_text = f"🔔 Обновлено расписание на {day_names[day]} ({week_type_rus} неделя):\n\n"
                    for i, lesson in enumerate(lessons, 1):
                        notification_text += f"{i} пара: {lesson if lesson else 'Пары нет или её не добавили'}\n"
                    for student_id in student_ids:
                        try:
                            bot.send_message(chat_id=int(student_id), text=notification_text)
                        except:
                            continue
                            
                conn.commit()

        markup = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton("🔙К выбору дня", 
                                        callback_data=f"{group_code}_edit_{week_type}")
        markup.add(back)
        
        result_text = "✅ Расписание на день обновлено:\n\n"
        for i, lesson in enumerate(lessons, 1):
            result_text += f"{i} пара: {lesson if lesson else 'Пары нет или её не добавили'}\n"
        
        bot.send_message(
            chat_id=message.chat.id,
            text=result_text,
            reply_markup=markup
        )
        
    except Exception as e:
        markup = types.InlineKeyboardMarkup()
        retry = types.InlineKeyboardButton("🔄 Повторить ввод",
                                         callback_data=f"{group_code}_edit_{week_type}_{day}_all")
        back = types.InlineKeyboardButton("🔙Назад",
                                        callback_data=f"{group_code}_edit_{week_type}_{day}")
        markup.row(retry, back)
        print(Fore.RED+f"‼️ Ошибка при сохранении расписания: {e}")
        bot.send_message(
            chat_id=message.chat.id,
            text="❌ Ошибка при сохранении расписания. Попробуйте еще раз",
            reply_markup=markup
        )
    finally:
        if 'conn' in locals():
            cur.close()
            conn.close()
