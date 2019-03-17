import json
import logging
import os
import random
from threading import Lock

import jieba.posseg
from telegram import Chat
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler

logging.basicConfig(level=logging.INFO)
DEFAULT_P = 0.1
suffix_words = ['个屁', '个头', '个几把', '个鬼', '个卵']
my_uid = 0
group_settings = dict()
settings_lock = Lock()


def test(bot, update):
    update.message.reply_text(random.choice(['测个屁', '测个头']))


def set(bot, update, args):
    if len(args) != 1:
        update.message.reply_text('Usage: /set <Reply Possibility> ([0.00~1.00])')
        return
    if update.message.chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        update.message.reply_text('Only available in group chats')
        return
    try:
        new_p = round(float(args[0]), 2)
        if new_p > 1:
            new_p = 1
        if new_p < 0:
            new_p = 0
    except ValueError:
        update.message.reply_text('Usage: /set <Reply Possibility> ([0.00~1.00])')
        return
    group_settings[update.message.chat.id] = new_p
    save_settings()
    update.message.reply_text('Success!')


def get(bot, update):
    if update.message.chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        update.message.reply_text('Only available in group chats')
        return
    update.message.reply_text(
        'Reply Possibility in current group is: {0:.2f}'.format(group_settings[update.message.chat.id]))


def gepi(bot, update):
    if update.message.chat.id not in group_settings:
        group_settings[update.message.chat.id] = DEFAULT_P
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == my_uid:
            # reply to bot
            suffix_word = random.choice(suffix_words)
            keywords = list()
            input_words = jieba.posseg.cut(update.message.text)
            for w in input_words:
                if w.flag.startswith('v'):
                    keywords.append(w.word)

            if keywords:
                update.message.reply_text(random.choice(keywords) + suffix_word)
            else:
                update.message.reply_text(update.message.text + suffix_word)
    elif random.random() <= group_settings[update.message.chat.id]:
        # normal mode
        suffix_word = random.choice(suffix_words)
        keywords = list()
        input_words = jieba.posseg.cut(update.message.text)
        for w in input_words:
            if w.flag.startswith('v') or w.flag.startswith('a') or w.flag == 'i':
                keywords.append(w.word)

        if keywords:
            update.message.reply_text(random.choice(keywords) + suffix_word)


def load_settings():
    with settings_lock:
        global group_settings
        if not os.path.isfile('settings.json'):
            with open('settings.json', 'w') as f:
                json.dump(group_settings, f)
        else:
            with open('settings.json') as f:
                group_settings = json.load(f)


def save_settings():
    with settings_lock:
        with open('settings.json', 'w') as f:
            json.dump(group_settings, f)


def main():
    bot_token = os.environ.get('BOT_TOKEN')
    load_settings()
    updater = Updater(bot_token)
    updater.dispatcher.add_handler(CommandHandler('test', test))
    updater.dispatcher.add_handler(CommandHandler('setp', set, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('getp', get, pass_args=True))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & Filters.group, gepi))
    global my_uid
    my_uid = updater.bot.get_me().id
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()