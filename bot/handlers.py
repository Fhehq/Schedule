from datetime import datetime


from telebot import types
from colorama import init, Fore


from bot.admin import is_admin, check_user_group
from bot.admin_groups import is_group_admin, import_group



init(autoreset=True)
DAYS = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница")
DAYS_ENG = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')

def week_type() -> str:
    """Определяет какой тип недели"""
    today = datetime.today()
    week_number = today.isocalendar()[1]
    return "нечетная" if week_number % 2 == 0 else "четная"


def create_week_keyboard(group_key: str, call):
    """Создает инлайн кейбоард группы"""    
    chat_id = call.chat.id if hasattr(call, 'chat') else call.message.chat.id

    markup = types.InlineKeyboardMarkup()
    today = datetime.now()
    weekday = today.weekday()
    tomorrow = (weekday + 1) % 7
    current_week = "chet" if week_type() == "четная" else "nechet"
    
    button = []
    
    day_codes = {
        0: "mon",
        1: "tue", 
        2: "wed",
        3: "thu",
        4: "fri"
    }

    if weekday < 5:
        today_callback = f"{group_key}_{current_week}_{day_codes[weekday]}"
        today_btn = types.InlineKeyboardButton(text="📅 Сегодня", callback_data=today_callback)
        button.append(today_btn)
  
    if tomorrow < 5 or weekday == 6:    
        if weekday == 6:
            current_week = "nechet" if current_week == "chet" else "chet"
        tomorrow_callback = f"{group_key}_{current_week}_{day_codes[tomorrow]}"
        tomorrow_btn = types.InlineKeyboardButton(text="📅 Завтра", callback_data=tomorrow_callback)
        button.append(tomorrow_btn)

    markup.row(*button)    
    chet_callback = f"{group_key}_chet"
    nechet_callback = f"{group_key}_nechet"
    
    chet = types.InlineKeyboardButton(text="🗓️ Четная", callback_data=chet_callback)
    nechet = types.InlineKeyboardButton(text="🗓️ Нечетная", callback_data=nechet_callback)
    markup.row(chet, nechet)

    if is_group_admin(call, group_key) or is_admin(call):
        adm = types.InlineKeyboardButton(text="⚙️ Админ меню", callback_data=f"{group_key}_adm")
        markup.add(adm)
        
    has_group, group = check_user_group(chat_id)
    if has_group == True and group == group_key: 
        delete_btn = types.InlineKeyboardButton("❌ Удалить мою группу", callback_data="delete_my_group")
        markup.add(delete_btn)
        
    if group_key.endswith("d"):
        back = types.InlineKeyboardButton(text="🔙 Назад", callback_data=group_key[:-5])
    else:
        back = types.InlineKeyboardButton(text="🔙 Назад", callback_data=group_key[:-4])
    markup.add(back)
    return markup


def create_back_button(current_callback_data, campus: str): 
    """Автоматическая кнопка назад"""
    parts = current_callback_data.split("_")
    if len(parts) > 2:  
        back_data = "_".join(parts[:-1])
    elif len(parts) == 2:  
        back_data = parts[0]  
    else:
        back_data = campus  
    return types.InlineKeyboardButton(text="🔙 Назад", callback_data=back_data)


def create_day_keyboard(group_key, week_type, campus: str):
    """Создает кнопки дней недели"""
    if week_type == "четную":
        week_type = "chet"
    else:
        week_type = "nechet"
    markup = types.InlineKeyboardMarkup()
    for ind in range(len(DAYS)):
        callback = f"{group_key}_{week_type}_{DAYS_ENG[ind][:3].lower()}"
        print(Fore.CYAN+f"создан callback: {callback}")
        button = types.InlineKeyboardButton(text=DAYS[ind], callback_data=callback)
        markup.add(button)
    markup.add(create_back_button(f"{group_key}_{week_type}", campus))
    return markup


def handle_group_select(call, bot, group_key, campus: str):
    """Выбор направления"""
    markup = types.InlineKeyboardMarkup()
    GROUPS = import_group(campus)
    for subgroup_key, subgroup_name in GROUPS[group_key]["subgroups"].items():
        callback_data = subgroup_key
        button = types.InlineKeyboardButton(text=subgroup_name, callback_data=callback_data)
        markup.add(button)
    markup.add(create_back_button(call.data, campus))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=f'✅ Вы выбрали направление {GROUPS[group_key]["name"]}\nВыберите вашу группу:',
        reply_markup=markup
    )


def handle_week_select(call, bot, subgroup_key, campus: str):
    markup = create_week_keyboard(subgroup_key, call)
    groups = import_group(campus)
    group_name = None
    for group_data in groups.values():
        if subgroup_key in group_data["subgroups"]:
            group_name = group_data["subgroups"][subgroup_key]
            break
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=f'✅ Вы выбрали группу {group_name}\nВыберите тип недели:\n(Сейчас {week_type()} неделя)',
        reply_markup=markup
    )