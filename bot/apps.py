from __future__ import unicode_literals

import inspect
import logging
import threading

import re
import types
from getpass import getpass

from datetime import datetime, timedelta

import pytz
from django.apps import AppConfig
from django.conf import settings
from django.db.models import base
from telethon import TelegramClient as TClient, TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import UpdateShortMessage, PeerUser, MessageService, UpdateNewChannelMessage, UpdateUserTyping, UpdateUserStatus, UpdateShortChatMessage, PeerChannel, InputChannel


log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)

# log.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")


class BotClient(AppConfig):
    name = 'bot'

    _rules = {"text": {}, "photo": {}, "audio": {}, "video": {}, "others": {}, "loaded": False}

    def ready(self):
        from bot import signals

    @classmethod
    def get_rules(cls, force_init=False):
        from bot.models import EngagementRule
        if cls._rules['text'] == {} or force_init:
            rules = EngagementRule.objects.all()
            log.warning("Total: {}================Initialising  Rules============".format(len(rules)))
            for e in rules:
                cls._rules[e.type.lower()] = e
            cls._rules['loaded'] = True
        return cls._rules


            # If you already have a previous 'session_name.session' file, skip this.
    # client.sign_in(phone=None, code=None, password=None, bot_token=None, phone_code_hash=None)
    # client.send_code_request(phone, force_sms=False)
    # client.sign_in(phone=settings.CLIENT[0].PHONE)

# def test(phone):
#     try:
#         client.sign_in(phone=phone)
#     except FloodWaitError as e:
#         print(e)

    # me = client.sign_in(code=83736)  # Put whatever code you received here.
    #
    # print(me.stringify())
    #
    # client.send_message('@africanquene', 'My remote message')
    # client.send_file('username', '/home/myself/Pictures/holidays.jpg')
    #
    # client.download_profile_photo(me)
    # total, messages, senders = client.get_message_history('username')
    # client.download_media(messages[0])

    # def callback(update):
    #     print('I received', update)
    #
    # client.add_update_handler(callback)


    # print(0)
    # print("Is class: {}".format(inspect.isclass(update)))
    # print("Type: {}".format(type(update)))
    # print("class name: {}".format(update.__class__))

    # client.remove_update_handler(callback)
    # def push_2_mail_db(cls, update, for_id=109317):
        # log.warning("**********msg*******")
#
# client.add_update_handler(callback)
#
#
# friend  = client.get_entity(friend_id)
#
#
# client.add_update_handler(push_2_mail_db)
# client.remove_update_handler(push_2_mail_db)
# client.list_update_handlers()
#




def callback(update):
    msg ="-----"
    # try:
    #     msg = update.message
    # except AttributeError:
    #     return
    # print(msg)
    # if isinstance(update, MessageService):
    #     return
    # if isinstance(update, UpdateUserTyping):
    #     return
    # if isinstance(update, UpdateUserStatus):
    #     return
    print('****************1*******************')
    if isinstance(update, UpdateNewChannelMessage):
        log.warning(update)
        words = re.split('\W+', msg.message)
        print(words)
    if isinstance(update, UpdateShortMessage):
        log.warning(update)
    if isinstance(update, UpdateShortChatMessage):
        log.warning(update)

    print('****************2*******************')


# def call(update, for_id):
#     from bot.models import Message
#     from bot.tasks import sendMail
#
#     if isinstance(update, UpdateNewChannelMessage):
#         if update.message.to_id.channel_id not in TeleClient.TARGET_CHANNELS:
#             # return
#             pass
#         print("--------Channel Message---------:  ")
#         # log.warning(update)
#
#         html_message = "Hello,<br><br>This is to let know there is a {} message ({}) on {} UTC: <p>{}<br>***{}***</p>".format(
#             Message.CHANNEL,
#             update.message.to_id.channel_id,
#             update.message.date,
#             update.message.message,
#             update.message.id
#         )
#         message = "Hello, This is to let know there is a {} message ({}) on {} UTC: {}<br>***{}***".format(
#             # "@"+update.message.chat.username +" (individual)" if update.message.chat.type=='private' else ("@"+update.message.chat.username +" (Group)" if "---" else "")
#             Message.CHANNEL,
#             update.message.to_id.channel_id,
#             update.message.date,
#             update.message.message,
#             update.message.id
#         )
#         sendMail.apply_async(kwargs={'subject': "Chat Notification", 'message': message, 'recipients': get_receivers(), 'html_message': html_message})
#         Message.objects.create(message_id=update.message.id, for_id=for_id, from_id=update.message.from_id, source=Message.CHANNEL, source_id=update.message.to_id.channel_id, text=update.message.message, date=update.message.date.replace(tzinfo=pytz.UTC))
#         print("--------Saved to DB---------")
#
#     if isinstance(update, UpdateShortChatMessage):
#         if update.chat_id not in TeleClient.TARGET_GROUPS:
#             # return
#             pass
#         print("--------Group Chat Message---------")
#         # log.warning(update)
#
#         html_message = "Hello,<br><br>This is to let know there is a {} message ({}) on {} UTC: <p>{}<br>***{}***</p>".format(
#             Message.GROUP,
#             update.chat_id,
#             update.date,
#             update.message,
#             update.id
#         )
#         message = "Hello, This is to let know there is a {} message ({}) on {} UTC: {}<br>***{}***".format(
#             # "@"+update.message.chat.username +" (individual)" if update.message.chat.type=='private' else ("@"+update.message.chat.username +" (Group)" if "---" else "")
#             Message.CHANNEL,
#             update.chat_id,
#             update.date,
#             update.message,
#             update.id
#         )
#         sendMail.apply_async(kwargs={'subject': "Chat Notification", 'message': message, 'recipients': get_receivers(), 'html_message': html_message})
#         Message.objects.create(message_id=update.id, for_id=for_id, from_id=update.from_id, source=Message.GROUP, source_id=update.chat_id, text=update.message, date=update.date.replace(tzinfo=pytz.UTC))
#
#
#     if isinstance(update, UpdateShortMessage):
#         if update.user_id not in TeleClient.TARGET_PRIVATE:
#             # return
#             pass
#         print("--------Private Chat Message---------")
#         # log.warning(update)
#
#         html_message = "Hello,<br><br>This is to let know there is a {} message ({}) on {} UTC: <p>{}<br>***{}***</p>".format(
#             Message.CHANNEL,
#             update.user_id,
#             update.date,
#             update.message,
#             update.id
#         )
#         message = "Hello, This is to let know there is a {} message ({}) on {} UTC: {}<br>***{}***".format(
#             # "@"+update.message.chat.username +" (individual)" if update.message.chat.type=='private' else ("@"+update.message.chat.username +" (Group)" if "---" else "")
#             Message.CHANNEL,
#             update.user_id,
#             update.date,
#             update.message,
#             update.id
#         )
#         print("--------Saving to DB---------")
#
#         sendMail.apply_async(kwargs={'subject': "Chat Notification", 'message': message, 'recipients': get_receivers(), 'html_message': html_message})
#         Message.objects.create(message_id=update.id, for_id=for_id, from_id=update.user_id, source=Message.INDIVIDUAL, source_id=update.user_id, text=update.message, date=update.date.replace(tzinfo=pytz.UTC))

