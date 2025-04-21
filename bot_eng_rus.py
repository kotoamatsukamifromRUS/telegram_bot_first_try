import translate
import telebot
from random import choice
from datetime import datetime
import json
import random
import re

translator = translate.Translator(from_lang="english", to_lang="russian")

# Настройки бота
token = "YOUR_TOKEN"
bot = telebot.TeleBot(token)
LOG_FILE = "/bot_logs.txt"
DATA_USER = "/data_user.json"
ENG_RUS_EXER = "/eng_rus.json"
comms = ["/start", "/random_eng", "/theme", "/new_start"]
THEMES = "/themes.json"
# данные пользователей
try:
    with open(DATA_USER, "r", encoding="utf-8") as f:
        data_user = json.load(f)
except:
    data_user = {}
# темы
try:
    with open(THEMES, "r", encoding="utf-8") as f:
        themes = json.load(f)
except:
    themes = {}
# текста
try:
    with open(ENG_RUS_EXER, "r", encoding="utf-8") as f:
        sentences = json.load(f)
    if "context_reading_exercises" not in sentences:
        raise ValueError
    sentences = sentences["context_reading_exercises"]
except:
    print("Ошибка в извлечении инфы")
    sentences = {}


def log_message(user, message_text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {user.id} | @{user.username} | {user.first_name} {user.last_name} | {message_text}\n"

    print(log_entry.strip())

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


@bot.message_handler(commands=["start"])
def start_bot(message):
    bot.send_message(
        message.chat.id,
        f"Приветствую, {message.from_user.first_name}!\n"
        f"Список доступных команд:\n" + "\n".join(comms),
    )


@bot.message_handler(commands=["theme"])
def show_theme(message):
    try:
        log_message(message.from_user, f"| {message.text}")
        tema = choice(list(themes.keys()))
        bot.send_message(
            message.chat.id, "\n".join(themes[tema]), parse_mode="MarkdownV2"
        )

    except IndexError:
        available_themes = "\n".join(themes.keys())
        bot.send_message(
            message.chat.id,
            f"Пожалуйста, укажите тему. Доступные темы:\n\n{available_themes}\n\n"
            "Пример использования: /theme food",
        )


@bot.message_handler(commands=["random_eng"])
def rand_sentence(message):
    log_message(message.from_user, f"| {message.text}")
    try:
        user_sentences = data_user.get(str(message.from_user.username), {}).get(
            "completed", []
        )

        if len(user_sentences) >= len(sentences):
            bot.send_message(
                message.chat.id,
                "Вы завершили все наши упражнения!\nЕсли желаете начать сначала нажмите /new_start",
            )
        else:
            available = [
                i for i in range(1, len(sentences) + 1) if i not in user_sentences
            ]
            if not available:
                bot.send_message(message.chat.id, "Все упражнения пройдены!")
                return

            curr_sentence_number = random.choice(available)
            curr_sentence = sentences[f"exercise_{curr_sentence_number}"]
            english_text = re.escape(curr_sentence["english"])
            russian_text = re.escape(curr_sentence["russian"])

            # Обновляем данные пользователя
            if str(message.from_user.username) not in data_user:
                data_user[str(message.from_user.username)] = {"completed": []}
            data_user[str(message.from_user.username)]["completed"].append(
                curr_sentence_number
            )

            with open(DATA_USER, "w", encoding="utf-8") as f:
                json.dump(data_user, f, ensure_ascii=False, indent=2)

            bot.send_message(
                message.chat.id,
                f"{english_text}\n\n||{russian_text}||",
                parse_mode="MarkdownV2",
            )
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка")


@bot.message_handler(commands=["new_start"])
def new_start(message):
    try:
        username = str(message.from_user.username)
        if username in data_user:
            data_user[username]["completed"] = []
            with open(DATA_USER, "w", encoding="utf-8") as f:
                json.dump(data_user, f, ensure_ascii=False, indent=2)
            bot.send_message(message.chat.id, "Ваш прогресс сброшен!")
        else:
            bot.send_message(message.chat.id, "У вас нет сохранённого прогресса")
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сбросе прогресса")


@bot.message_handler(content_types=["text"])
def count(message):

    try:
        bot.send_message(message.chat.id, translator.translate(message.text))
        log_message(message.from_user, f"| {message.text}")
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Введите слово корректно")


with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write("\n" + "=" * 50 + "\n")
    f.write(f"Бот запущен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 50 + "\n\n")

print("Бот запущен")
bot.polling(none_stop=True, interval=0)
