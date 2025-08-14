import sys
import os

import telebot
from colorama import init, Fore

from bot.schedule_handlers import (
    handle_edit_schedule,
    handle_edit_week_select,
    handle_edit_day_select,
    save_full_day,
    save_lesson,
    handle_schedule_day
)
from bot.admin_groups import (
    handle_admin_panel,
    handle_add_group_admin,
    handle_remove_group_admin,
    import_group
)
from bot.handlers import create_day_keyboard, handle_group_select, handle_week_select


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
init(autoreset=True)
def handle_campus_callbacks(call, bot, campus):
    GROUPS = import_group(campus)
    print(Fore.CYAN+f"Получен callback: {call.data}")
    if "_edit_chet" in call.data or "_edit_nechet" in call.data:
        if len(call.data.split("_")) == 3:
            handle_edit_week_select(call, bot)
        elif len(call.data.split("_")) == 4:
            handle_edit_day_select(call, bot)
        elif len(call.data.split("_")) == 5:  
            parts = call.data.split("_")
            group_code = parts[0]
            week_type = parts[2]
            day = parts[3]
            edit_type = parts[4]
            
            if edit_type == "all":
                msg = bot.send_message(
                    chat_id=call.message.chat.id,
                    text="🖊️ Введите расписание на весь день.\nКаждая пара с новой строки:"
                )
                bot.register_next_step_handler(msg, save_full_day, bot, group_code, week_type, day)
            else:
                msg = bot.send_message(
                    chat_id=call.message.chat.id,
                    text="🖊️ Введите новое расписание для выбранной пары:"
                )
                bot.register_next_step_handler(msg, save_lesson, bot, group_code, week_type, day, edit_type)
        return
    
    if "_edit" in call.data:
        handle_edit_schedule(call, bot)
        return
    if "_add_admin" in call.data:
        handle_add_group_admin(call, bot,)
        return
    
    elif "_remove_admin" in call.data:
        handle_remove_group_admin(call, bot)
        return
    
    days_map = {
        'mon': 'понедельник',
        'tue': 'вторник',
        'wed': 'среду', 
        'thu': 'четверг',
        'fri': 'пятницу'
    }
    
    
    if call.data.endswith("_adm") :
        print(Fore.CYAN+f"Найден callback админ панели: {call.data}")
        handle_admin_panel(call, bot)
        return
    
    for day_code, day_name in days_map.items():
        if f"_{day_code}" in call.data:
            handle_schedule_day(call, bot, day_name, campus)
            return

    try:
        if call.data.endswith("_nechet") or call.data.endswith("_chet"):
            week_type = "четную" if call.data.endswith("_chet") else "нечетную"
            group_code = call.data.replace("_chet", "").replace("_nechet", "")
            markup = create_day_keyboard(group_code, week_type, campus)
            new_text = f'🗓️ Вы выбрали {week_type} неделю\nТеперь выберите день'
            
            if call.message.text != new_text:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.id,
                    text=new_text,
                    reply_markup=markup
                )
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise e

    for group_key, group_data in GROUPS.items():
        if call.data in group_data["subgroups"]:
            handle_week_select(call, bot, call.data, campus)
            return

    if call.data in GROUPS:
        handle_group_select(call, bot, call.data, campus)



