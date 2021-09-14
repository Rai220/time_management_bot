#!/usr/bin/env python

import logging
import threading
import time
import random
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

UNDER_CONSTURCTION = f'Сорян, функция в разработке 🙏'
TOKEN = os.getenv("TOKEN", "<INSERT TELEGRAM BOT TOKEN>")


def time_has_come(user, update, context):
    rt = random.randint(600, 60000)
    time.sleep(rt)

    update.message.reply_text(
        f"Ну что ж! Время настало! Ты ждал этого момента целых {rt} секунд! ⌛",
        reply_markup=ReplyKeyboardMarkup(
            main_keyboard, one_time_keyboard=True, input_field_placeholder=''
        )
    )


def when_time_comes(user, update: Update, context: CallbackContext):
    update.message.reply_text(
        f"Я напишу тебе, когда настанет время! ⌛"
    )

    threading.Thread(target=time_has_come, args=(
        user, update, context), ).start()


def start(user, update: Update, context: CallbackContext):
    user['text_input'] = True
    user['tasks'] = []

    reply_keyboard = [[commands["ALL_TASKS"]["text"]]]
    update.message.reply_text(
        f'Присылай мне свои задачи на сегодня по-одной. Когда закончишь, нажми кнопку "✅ Это все задачи"',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder=''
        ),
    )


def start_collect_task(user, update: Update, context: CallbackContext):
    user["current_task"] = commands["START_WORK"]
    text = update.message.text
    user['tasks'].append(text)

    reply_keyboard = [[commands["ALL_TASKS"]["text"]]]
    update.message.reply_text(
        f'Присылай мне свои задачи на сегодня по-одной. Когда закончишь, нажми кнопку "✅ Это все задачи".\nТекущий список задач:\n' +
        "\n".join(user['tasks']),
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Введи описание задачи:'
        ),
    )


def all_tasks(user, update: Update, context: CallbackContext):
    user["current_task"] = commands["ALL_TASKS"]
    user['text_input'] = True

    if len(user['tasks']) == 0:
        update.message.reply_text("Придумай хотя бы одну задачу!")
        start_collect_task(user, update, context)
    else:
        arr = []
        tasks = []
        for i in range(0, len(user['tasks'])):
            arr.append(f"{i}")
            tasks.append(f"{i}. {user['tasks'][i]}")

        reply_keyboard = [arr]
        update.message.reply_text(
            f"Подумай и выбери главную задачу с который ты начнёшь:\n" +
            "\n".join(tasks),
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder=''
            ),
        )


def start_from_task_number(user, update: Update, context: CallbackContext):
    try:
        text = update.message.text
        task_id = int(text)
        task = user["tasks"][task_id]
        user["task"] = task

        reply_keyboard = [[commands["MUSIC_ON"]["text"]]]
        update.message.reply_text(
            f"На ближайшие 25 минут твоя задача - {task}. Надеь наушники и включи рабочую музыку 🎧🎵",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder=''
            ),
        )
    except Exception as e:
        all_tasks(user, update, context)


def music_on(user, update: Update, context: CallbackContext):
    reply_keyboard = [[commands["TOOLS_OPEN"]["text"]]]
    update.message.reply_text(
        f"Открой необходимые для работы инструменты (Miro, IDE, Jira, Confluence, Word и т.п.) 📂🖥",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder=''
        )
    )


def run_in_25(user, update: Update, context: CallbackContext):
    time.sleep(25 * 60)

    update.message.reply_text(
        f"⌛ Прошло 25 минут с тех пор, как ты работаешь над задачей {user['task']}! Надеюсь, тебе удалось начать работать! Если да, то ты молодец!",
        reply_markup=ReplyKeyboardMarkup(
            main_keyboard, one_time_keyboard=True, input_field_placeholder=''
        )
    )


def tools_opened(user, update: Update, context: CallbackContext):
    update.message.reply_text(
        f"Отлично! Постарайся не отвлекаться 25 минут. Я тебе напишу, когда время пройдет! ⌛"
    )

    threading.Thread(target=run_in_25, args=(user, update, context), ).start()


commands = {
    "WHEN_TIME_COMES": {"text": "Когда наступит время ⏱", "cmd": when_time_comes},
    "START_WORK": {"text": "Помоги мне начать работать 🙏", "cmd": start, "text_input": start_collect_task},
    "ALL_TASKS": {"text": "✅ Это все задачи", "cmd": all_tasks, "text_input": start_from_task_number},
    "MUSIC_ON": {"text": "Включил! 🎧🎵", "cmd": music_on},
    "TOOLS_OPEN": {"text": "Открыл! 📂🖥", "cmd": tools_opened}
}

userdata = {}
main_keyboard = [[commands["START_WORK"]["text"]],
                 [commands["WHEN_TIME_COMES"]["text"]]]


def message(update: Update, context: CallbackContext) -> None:
    if update and update.message and update.message.from_user and update.message.from_user.id:
        id = update.message.from_user.id
        user = userdata.get(id, {})
        userdata[id] = user
        text = update.message.text

        cmd_found = False

        for name in commands:
            cmd = commands[name]
            if cmd["text"] == text:
                cmd_found = True
                if cmd["cmd"]:
                    user["current_task"] = cmd
                    cmd["cmd"](user, update, context)

        if not cmd_found and user.get('text_input', False) and user.get('current_task', {}).get("text_input"):
            cmd_found = True
            user['current_task']['text_input'](user, update, context)

        if not cmd_found:
            update.message.reply_text(
                f'Что вы хотите сделать?',
                reply_markup=ReplyKeyboardMarkup(
                    main_keyboard, one_time_keyboard=True, input_field_placeholder=''
                ),
            )


def main() -> None:
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, message))

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
