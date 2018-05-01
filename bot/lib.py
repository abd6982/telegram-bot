import logging
import re
from datetime import timedelta, datetime

import os
import telegram
from django.conf import settings
from django.utils import timezone
from functools import wraps

# from telethon.tl.functions.messages import DeleteMessagesRequest
# from telethon.tl.types import MessageService, MessageActionChatDeleteUser
from telethon import TelegramClient
from telethon.tl.functions.account import CheckUsernameRequest
from telethon.tl.functions.channels import InviteToChannelRequest, EditBannedRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import InputChannel, InputUser, ChannelBannedRights
from telethon.utils import get_input_peer

from bot.models import Defaulter, Group, Member
from bot.utils import getGroup, TeleClient, getMember

log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)

CheckUsernameRequest

LIST_OF_ADMINS = [442824327, 87654321]

GROUP = "/group"

RESTRICT = "/restrict"
UNBAN = "/unban"
BAN = "/ban"

TEST_COMMAND = "/test"

text_header = "😀 Hello {}, Your search result for \"{}\" is:\n\n{}"
text_header_eg = "⚠️ {}, please enter a search keyword in the format:\n\n{}"
text_empty = "😩 {}, unfortunately your search returned Empty Result"
empty_search = "⚠️ Missing Searck Keyword\n\n"

regex = r"(^/\w+@\w+|/\w+)\s*(\w*)"


def restrictedGroups(func):
    log.warning("------Group-------")
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        group_id = str(update.message.chat_id)
        if group_id not in TeleClient.getAllowedGroupIDs():
            log.warning("Unauthorized access denied for  User: {} from GROUP: {}.".format(update.effective_user.id, update.message.chat_id))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


# TODO: Pass paramter to exempt bot
# def requireAdmin(func, exempt_bot=False):
def requireAdmin(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        member = bot.getChatMember(update.message.chat_id, update.effective_user.id)
        # if not exempt_bot:
        #     update.message.from_user.is_bot
        if member.status not in ['creator', 'administrator'] or update.message.from_user.is_bot:
            if update.message.from_user.is_bot:
                return
            log.warning("Unauthorized access denied for USER: {} from Group: {}.".format(update.effective_user.id, update.message.chat_id))

            status = bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
            app_member = getMember(update.message.from_user)[0]
            Defaulter.objects.create(member=app_member, group=Group(id=update.message.chat_id,))
            hours_ago = timezone.now() - timedelta(hours=24)
            if Defaulter.objects.filter(created__gte=hours_ago, group__id=update.message.chat.id).count() >= 2:
                if banUser(bot, update, update.message.from_user.id):
                    bot.sendMessage(update.message.chat_id, text="<b><i>{} Kicked</i></b>", parse_mode=telegram.ParseMode.HTML)
        return func(bot, update, *args, **kwargs)
    return wrapped


def forward_search_result(bot, update):
    pass



# @requireAdmin
def group(bot, update, args):
    # log.warning(update)
    # log.warning(update.message.from_user.id)

    member = bot.getChatMember(update.message.chat_id, update.message.from_user.id)

    # log.warning(member)
    if member.status in ['creator', 'administrator'] and not update.message.from_user.is_bot:
        for arg in args:
            if arg == "id":
                group, created = getGroup(update.message.chat)
                if created:
                    text_header = "😀 Hello {}, \nI am happy to meet you!\n\nYour Group ID is <b>\"{}\"</b>"
                else:
                    text_header = "😀 Hello {}, Your Group ID is \"{}\""
                bot.sendMessage(update.message.chat_id, text=text_header.format(update.message.from_user.first_name, update.message.chat.id), parse_mode=telegram.ParseMode.HTML)

                return
    else:
        bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)


def restrictUser(bot, update, args):
    return bot.restrictChatMember(chat_id=update.message.chat_id, user_id=update.message.from_user.id, until_date=timezone.now()+timedelta(minutes=args[0]),
                              can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)


def banUser(bot, update, args):
    log.warning("*************Kick***************")
    return bot.kickChatMember(chat_id=update.message.chat_id, user_id=update.message.from_user.id, until_date=timezone.now()+timedelta(hours=args[0]))


def unbanUser(bot, update, args):
    return bot.unbanChatMember(chat_id=update.message.chat_id, user_id=update.message.from_user.id)


def test_msg(bot, update):
    log.warning(update.message.chat_id, "   ", update.message.from_user.id)
    log.warning("*************Bot***************")
    log.warning(bot)
    log.warning("*************Me***************")
    log.warning(bot.get_me())
    log.warning("*************Update***************")
    log.warning(update)
    log.warning("**************Chat**************")
    log.warning(update.message.chat)
    log.warning("*************User***************")
    log.warning(update.message.from_user)
    log.warning("*************Others***************")
    log.warning("From User ID:   %s" % update.message.from_user.id)
    log.warning("Message ID:  %s" %update.message.message_id)
    log.warning("Chat ID:  %s" %update.message.chat_id)
    log.warning("Bot member:   %s" % update.message.from_user.is_bot)
    log.warning("Chat Member:  %s" % bot.getChatMember(update.message.chat_id, update.message.from_user.id))


@restrictedGroups
@requireAdmin
def test_command(bot, update, args):
    log.warning("*************Bot***************")
    log.warning(bot)
    log.warning("*************Me***************")
    log.warning(bot.get_me())
    log.warning("*************Update***************")
    log.warning(update)
    log.warning("**************Chat**************")
    log.warning(update.message.chat)
    log.warning("*************Others***************")
    log.warning("Message ID:  %s" %update.message.message_id)
    log.warning("Chat ID:  %s" %update.message.chat_id)
    log.warning(update.message.from_user)
    log.warning("From User ID:   %s" % update.message.from_user.id)
    log.warning("Bot member:   %s" % update.message.from_user.is_bot)
    log.warning("Chat Member:  %s" % bot.getChatMember(update.message.chat_id, update.message.from_user.id))


def create_member(bot, update):
    user = update.message.from_user
    # TODO: sent this to Celery
    try:
        Member.objects.create(member_id=user.id, first_name=user.first_name, username=user.username, type=Member.TELEGRAM, is_bot=user.is_bot, is_blacklisted=True)
    except Exception as err:
        pass
        # log.error(err)
        # log.error("Failed Creating Members:  member_id={}, first_name={}, last_name={}, username={}, type={}, is_bot={}, is_blacklisted={}".format(user.id, user.first_name, user.username, Member.TELEGRAM, user.is_bot, True))
