import os
import json
import subprocess
import datetime
from random import choice as c

import mysql.connector
from colorama import init, Fore, Style


init(autoreset=True)

host = ""
user = ""
password = ""
db_name = ""

def import_group():
    with open("data/groups.json", "r") as file:
        data = json.load(file)
        groups = [group for value in data.values() for v in value.values() for group in v["subgroups"]]
        return groups

def create_groups_table():
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    cursor = conn.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS `groups` (
        group_code VARCHAR(10),
        student_id BIGINT,
        PRIMARY KEY (group_code, student_id)
    )
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS `groups`")
    
    create_table_query = """
    CREATE TABLE `groups` (
        group_code VARCHAR(10) PRIMARY KEY,
        student_ids TEXT
    )
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    cursor = conn.cursor()
    
    groups = import_group()
    
    for group in groups:
        cursor.execute("INSERT IGNORE INTO `groups` (group_code) VALUES (%s)", (group,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(Fore.GREEN + "▶ Данные успешно добавлены или перезаписаны в таблицу 'groups'.")

def reset_schedule():
    ready = input(Fore.RED+"Вы уверены, что хотите сбросить расписание?(Да/Нет): ").lower()
    if ready == "да":
        while True:
            letter = "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890"
            capcha = "".join([c(letter) for _ in range(5)])
            check_capcha = input(Fore.YELLOW+f"Введите каптчу {capcha}: ")
            if check_capcha == capcha:
                conn = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                cursor = conn.cursor()

                cursor.execute("SELECT DISTINCT group_code FROM `groups`")
                groups = [row[0] for row in cursor.fetchall()]
                week_types = ['chet', 'nechet']
                days = ['mon', 'tue', 'wed', 'thu', 'fri']

                query = """
                INSERT INTO schedules 
                (group_code, week_type, schedule_text, lesson_1, lesson_2, lesson_3, lesson_4, lesson_5, day)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                schedule_text = VALUES(schedule_text),
                lesson_1 = VALUES(lesson_1),
                lesson_2 = VALUES(lesson_2),
                lesson_3 = VALUES(lesson_3),
                lesson_4 = VALUES(lesson_4),
                lesson_5 = VALUES(lesson_5)
                """

                for group in groups:
                    for week_type in week_types:
                        for day in days:
                            values = (
                                group,
                                week_type,
                                None,   
                                '', '', '', '', '',
                                day
                            )
                            cursor.execute(query, values)
                conn.commit()
                cursor.close()
                conn.close()
                print("\n"+Fore.GREEN+"▶ Пустое расписание успешно добавлено для всех групп.")
                break
            else:
                print(Fore.YELLOW+"Неверная каптча")
                continue
    else:
        print(Fore.CYAN+"Досвидание")
        return
    
def copy_bd():
    backup_dir = 'data/backups'
    
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/{db_name}_backup_{timestamp}.sql"
    
    command = [
        'mysqldump',
        f'-h{host}',
        f'-u{user}',
        f'-p{password}',
        db_name
    ]
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        try:
            subprocess.run(command, stdout=f, check=True)
            print(Fore.GREEN + f"▶ Резервная копия базы '{db_name}' успешно создана в файле:\n{backup_file}")
        except subprocess.CalledProcessError as e:
            print(Fore.RED + "❌ Ошибка при создании резервной копии:", e)

commands = {
    1: ("Добавить/Перезаписать группы", create_groups_table),
    2: ("Сбросить Расписание", reset_schedule),
    3: ("Сделать копию БД", copy_bd),
}

def menu():
    while True:
        print(Fore.BLUE+"\n" + "~" * 40)
        for key, (desc, _) in commands.items():
            print(Fore.BLUE+f"{key}: {desc}")
        print(Fore.BLUE+"0: Выйти")
        print(Fore.BLUE+"~" * 40)
        try:
            choice = int(input(Fore.YELLOW+"Выберите команду: "))
        except ValueError:
            print(Fore.RED+"❌ Введите номер команды!")
            continue

        if choice == 0:
            print(Fore.CYAN+"До встречи!")
            break

        command = commands.get(choice)
        if command:
            print(f"\n▶ Выполняю: {command[0]}")
            command[1]()
        else:
            print(Fore.RED + "❌ Неверная команда")
    
if __name__ == "__main__":
    menu()