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
character_replacement_data = dict()


def test(bot, update):
    update.message.reply_text(random.choice(['测个屁', '测个头']))


def generate_repeat_text(text):
    output = ''
    for char in text:
        replacement = character_replacement_data.get(char)
        output += replacement if replacement else char
    return output


def set(bot, update, args):
    if len(args) != 1:
        update.message.reply_text('Usage: /setp <Reply Possibility> ([0.00~1.00])')
        return
    if update.message.chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        update.message.reply_text('Only available in group chats')
        return
    try:
        new_p = round(float('0' + args[0]), 6)
        if new_p > 1:
            new_p = 1
        if new_p < 0:
            new_p = 0
    except ValueError:
        update.message.reply_text('Usage: /setp <Reply Possibility> ([0.00~1.00])')
        return
    group_settings[update.message.chat.id] = new_p
    save_settings()
    update.message.reply_text('Success! P = {0:.6f}'.format(new_p))


def get(bot, update):
    if update.message.chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        update.message.reply_text('Only available in group chats')
        return
    if update.message.chat.id not in group_settings:
        group_settings[update.message.chat.id] = DEFAULT_P
    update.message.reply_text(
        'Reply Possibility in current group is: {0:.6f}'.format(group_settings[update.message.chat.id]))


def gepi(bot, update):
    if update.message.chat.id not in group_settings:
        group_settings[update.message.chat.id] = DEFAULT_P
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == my_uid:
            # reply to bot
            if update.message.text:
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
            elif update.message.sticker:
                sticker_set = bot.get_sticker_set(update.message.sticker.set_name)
                reply_sticker = random.choice(sticker_set.stickers)
                update.message.reply_sticker(reply_sticker)
    elif update.message.forward_from:
        if update.message.forward_from.id == my_uid:
            # forward words of bot
            suffix_word = random.choice(suffix_words)
            update.message.reply_text('Forward' + suffix_word)

    elif random.random() <= group_settings[update.message.chat.id]:
        # normal mode
        if random.random() < 0.5:
            suffix_word = random.choice(suffix_words)
            keywords = list()
            input_words = jieba.posseg.cut(update.message.text)
            for w in input_words:
                if w.flag.startswith('v') or w.flag.startswith('a') or w.flag == 'i':
                    keywords.append(w.word)

            if keywords:
                update.message.reply_text(random.choice(keywords) + suffix_word)
        else:
            update.message.reply_text(generate_repeat_text(update.message.text), quote=False)
    print(update.message.chat.id, update.message.chat.title, update.message.from_user.id,
          update.message.from_user.full_name)


def load_settings():
    with settings_lock:
        global group_settings
        global character_replacement_data
        if os.path.isfile('char_replace_data.json'):
            with open('char_replace_data.json') as f:
                character_replacement_data = json.load(f)
        else:
            print('ERROR: char_replace_data.json does not exist')
        if os.path.isfile('settings.json'):
            with open('settings.json') as f:
                group_settings = json.load(f)
        else:
            print('ERROR: settings.json does not exist')


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
    updater.dispatcher.add_handler(CommandHandler('getp', get))
    updater.dispatcher.add_handler(MessageHandler((Filters.text | Filters.sticker) & Filters.group, gepi))
    global my_uid
    my_uid = updater.bot.get_me().id
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
