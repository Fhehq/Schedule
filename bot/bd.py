import pymysql
from colorama import init, Fore


from config import *


init(autoreset=True)

try:
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        port = 3306,
        cursorclass=pymysql.cursors.DictCursor
    )
    print(Fore.GREEN+"Подключение к базе данных установлено")

except Exception as ex:
    print(Fore.RED+"Ошибка при подключении к базе данных")
    print(Fore.RED+ex)
