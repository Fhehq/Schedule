import telebot
import os; from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

bot = telebot.TeleBot(os.getenv('TOKEN'))

host = ""
user = ""
password = ""
db_name = ""
