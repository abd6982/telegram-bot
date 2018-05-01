# -*-coding:utf-8-*-

# Example code for telegrambot.py module
import json

import redis
from django.core.cache import cache
from django.core.files import images
from django.db import IntegrityError
from django.utils import timezone

from datetime import timedelta

from bot.apps import BotClient
from bot.forms import EngagementRuleForm
from bot.models import Message, EngagementRule
from telegram.ext import CommandHandler, MessageHandler, Filters

from bot.utils import getIMember, TinClient, MEDIA_CATEGORY, loadAdmins, checkNameImpersonationSingle, checkPhotoImpersonationSingle, botLog
from django_telegrambot.apps import DjangoTelegramBot
from bot.lib import *
import logging

log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.

def start(bot, update):
    log.warning("********STARTED*************")
    # log.warning(bot)
    sender = update.message.__dict__
    text = "Moderator bot is active now".format(sender['from_user']['first_name'], bot.first_name)

    try:
        getGroup(update.message.chat)
    except Exception as err:
        pass

    # text = getattr(update.message, 'text')

    bot.sendMessage(update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)


def help(bot, update):
    text = "The follow commands are available:\n"
    text += "/start\n"
    text += "/group id (To register group details [Admins only])\n"
    bot.sendMessage(update.message.chat_id, text=text)


def staff(bot, update):
    log.warning("Start.....")
    # from confusable_homoglyphs import categories, confusables
    # categories
    # confusables
    admins = bot.getChatAdministrators(chat_id=update.message.chat.id)
    for a in admins:
        u = a.user
        log.warning("{} {} @({}) - {}".format(u.first_name, u.last_name, u.username, a.status))
    # bot.sendMessage(update.message.chat_id, text="")


def echo(bot, update):
    log.warning("-----------")
    bot.sendMessage(update.message.chat_id, text="'{}' deleted".format(update.message.text), parse_mode=telegram.ParseMode.HTML)


@restrictedGroups
def quite(bot, update):
    from bot.utils import kickMemberOut
    log.warning(update.message.chat)
    member = bot.getChatMember(update.message.chat_id, update.message.from_user.id)
    try:
        update.message.left_chat_member.id
        is_bot = True
        can_add = False
    except:
        is_bot = update.message.from_user.is_bot
        can_add = not is_bot

    if member.status not in ['creator', 'administrator'] or is_bot:
        log.warning("Unauthorized access denied for USER: {} from Group: {}.".format(update.effective_user.id, update.message.chat_id))
        # status = bot.deleteMessage(chat_id=1001312267994, message_id=update.message.message_id)
        status = bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)

        # log.warning(update)
        # log.warning(update.message.chat_id)

        app_member = getMember(update.message.from_user, update.message.chat.id)[0]
        gid = update.message.chat_id
        Defaulter.objects.create(member=app_member, group=Group(id=gid, ))
        hours_ago = timezone.now() - timedelta(hours=24)

        count = 0
        if can_add:
            count = Defaulter.objects.filter(member=app_member, created__gte=hours_ago, group__id=update.message.chat.id).count()

        if count >= 20:
            kickMemberOut(channel_id=update.message.chat_id, user_id=update.message.from_user.id, kick=True)
            # if banUser(bot, update, update.message.from_user.id):
            Defaulter.objects.filter(member=app_member, group__id=gid).delete()
                # bot.sendMessage(update.message.chat_id, text="<i>{} Kicked</i>".format(update.message.from_user.id), parse_mode=telegram.ParseMode.HTML)
            # else:
            #     bot.sendMessage(update.message.chat_id, text="<i>Unable to kick {}</i>".format(update.message.from_user.id), parse_mode=telegram.ParseMode.HTML)


def report_defaulter(bot, update, can_add, text, full_report=True, author=None):
    from bot.models import IDefaulter
    bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
    if not full_report:
        bot.sendMessage(update.message.chat_id, text=text, parse_mode=telegram.ParseMode.HTML)
        return
    t_member = getMember(update.message.from_user, update.message.chat_id)[0]

    if author:
        i_member = getIMember(author)[0]
        IDefaulter.objects.create(member=i_member, group=Group(id=update.message.chat_id))

    Defaulter.objects.create(member=t_member, group=Group(id=update.message.chat_id))

    hours_ago = timezone.now() - timedelta(hours=24)

    count = 0
    if can_add:
        count = Defaulter.objects.filter(member=t_member, created__gte=hours_ago, group__id=update.message.chat.id).count()

    bot.sendMessage(update.message.chat_id, text="{}\n❗Warning {}/3 ❗️".format(text, count), parse_mode=telegram.ParseMode.HTML)

    if count >= settings.OFFENSE_LIMIT:
        status = bot.kick_chat_member(chat_id=update.message.chat_id, user_id=update.message.from_user.id, until_date=datetime(2040, 12, 25))
        if status:
            Defaulter.objects.filter(member=t_member, group__id=update.message.chat_id).delete()


TEXT_REGREX = r"((^[Dd][Xx])(\d+))\s*(by)*\s*(@*.*)\s+((https://instagram.com/p/|http://instagram.com/p/|https://www.instagram.com/p/|http://www.instagram.com/p/)(.+)\/*\s*(.*))"


def error(bot, update, error):
    try:
        bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception as err:
        log.error(err)
    log.error('Update "%s" caused error "%s"' % (update, error))


def getType(message):
    from bot.utils import URL, TEXT, CONTACT, LOCATION, VENUE, STICKER, PHOTO, ANIMATION, AUDIO, AUDIO_NOTE, VIDEO, VIDEO_NOTE, DOCUMENT, GAME, OTHERS
    try:
        if message.text:
            if len(message.entities) > 0 and message.entities[0].type == URL.lower():
                return URL, TEXT
            else:
                return TEXT, TEXT
    except Exception as err:
        log.error(err)

    try:
        if message.contact:
            return CONTACT, TEXT
    except Exception as err:
        log.error(err)

    try:
        if message.location:
            return LOCATION, TEXT
    except Exception as err:
        log.error(err)

    try:
        if message.venue:
            return VENUE, TEXT
    except Exception as err:
        log.error(err)

    try:
        if message.sticker:
            return STICKER, PHOTO
    except Exception as err:
        log.error(err)

    try:
        if message.photo:
            return PHOTO, PHOTO
    except Exception as err:
        log.error(err)

    try:
        if message.animation:
            return ANIMATION, PHOTO
    except Exception as err:
        log.error(message.to_dict())
        log.error(err)

    try:
        if message.audio:
            return AUDIO, AUDIO
    except Exception as err:
        log.error(err)

    try:
        if message.voice:
            return AUDIO_NOTE, AUDIO
    except Exception as err:
        log.error(err)

    try:
        if message.video:
            return VIDEO, VIDEO
    except Exception as err:
        log.error(err)

    try:
        if message.video_note:
            return VIDEO_NOTE,  VIDEO
    except Exception as err:
        log.error(err)

    try:
        if message.document:
            if message.document.mime_type == "video/mp4":
                return VIDEO, VIDEO
            elif message.document.mime_type in ["image/png", "image/gif", "image/jpg", "image/jpeg"]:
                return PHOTO, PHOTO
            else:
                return DOCUMENT, OTHERS
        elif message.game:
            return GAME,  OTHERS
        else:
            return OTHERS, OTHERS
    except Exception as err:
        log.error(err)

    return "loaded", "loaded"


def act(bot, update, rule):
    # log.warning("{}::{}::{}::{}".format(rule.action, update.message.chat_id, update.message.from_user.id, rule.limit_time))
    if rule.action == EngagementRuleForm.READONLY:
        bot.restrictChatMember(chat_id=update.message.chat_id, user_id=update.message.from_user.id, until_date=timezone.now() + timedelta(minutes=rule.limit_time),
                                      can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
        Member.objects.filter(group__id=update.message.chat_id, member_id=update.message.from_user.id).update(status=Member.RESTRICTED)
    elif rule.action == EngagementRuleForm.BAN:
        bot.restrictChatMember(chat_id=update.message.chat_id, user_id=update.message.from_user.id, until_date=timezone.now() + timedelta(minutes=rule.limit_time),
                                      can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
        Member.objects.filter(group__id=update.message.chat_id, member_id=update.message.from_user.id).update(status=Member.RESTRICTED)
    elif rule.action == EngagementRuleForm.KICK:
        bot.kickChatMember(chat_id=update.message.chat_id, user_id=update.message.from_user.id, until_date=timezone.now() + timedelta(days=400))
        Member.objects.filter(group__id=update.message.chat_id, member_id=update.message.from_user.id).update(status=Member.KICKED)
    return None


def modulator(bot, update):
    log.warning("---------------* in *---------------------")
    # log.warning(update.message)
    # from bot.utils import TEXT_GROUP, PHOTO_GROUP, AUDIO_GROUP, VIDEO_GROUP, OTHER_GROUP
    try:
        if update.message.new_chat_members:
            log.warning("---------------* new *---------------------")
            try:
                admins = bot.getChatAdministrators(chat_id=update.message.chat.id)
                admin_users = loadAdmins(admins, group_id=update.message.chat.id)
            except Exception as err:
                log.error(err)
                try:
                    log.warning("Trying again....")
                    admins = bot.getChatAdministrators(chat_id=update.message.chat.id)
                    admin_users = loadAdmins(admins, group_id=update.message.chat.id)
                except Exception as err:
                    getMember(update.message.new_chat_members[0], update.message.chat.id)
                    log.error(err)
                    return
            if len(admin_users) > 0:
                for new_member in update.message.new_chat_members:
                    log.warning("Joined {} (@{} : {}): {}".format(update.message.chat.title, update.message.chat.username, update.message.chat.id, new_member))
                    try:
                        getMember(new_member, update.message.chat.id)
                    except IntegrityError as err:
                        log.warning("Yes {}".format(err))
                        Member.objects.filter(member_id=new_member.id).update(status=Member.ACTIVE)
                    except Exception as err:
                        log.error("Error Adding memeber:  {}".format(err))

                    try:
                        evict = checkNameImpersonationSingle(admin_users, new_member)
                        if evict:
                            bot.kickChatMember(chat_id=update.message.chat.id, user_id=evict['user_id'], until_date=timezone.now() + timedelta(days=400))
                            log.warning("Kicked: {}".format(evict["reason"]))
                            Member.objects.filter(member_id=evict['user_id']).update(status=Member.KICKED)
                            return
                        else:
                            evict = checkPhotoImpersonationSingle(admin_users, update.message.from_user)
                            if evict:
                                bot.kickChatMember(chat_id=update.message.chat.id, user_id=evict['user_id'], until_date=timezone.now() + timedelta(days=400))
                                log.warning("Kicked: {}".format(evict['reason']))
                                Member.objects.filter(member_id=evict['user_id']).update(status=Member.KICKED)
                                return

                        redex = redis.StrictRedis(host=settings.REDIS_SERVER, port=settings.REDIS_PORT, db=0)
                        member = {}
                        member['user'] = {"id": new_member.id, "first_name": new_member.first_name, "username": new_member.username}
                        member['chat'] = {"id": update.message.chat.id, "title": update.message.chat.title}

                        try:
                            new_members = json.loads(redex.get('new_members').decode('utf-8'))
                        except Exception as err:
                            new_members = []

                        new_members.append(member)

                        redex.set('new_members', json.dumps(new_members))
                        log.warning(":Logging member for welcome...3 {}".format(json.dumps(new_members)))

                        return
                    except Exception as err:
                        log.error(err)
                        return

            return
    except Exception as err:
        log.error("Failed : ".format(err))
    # log.warning(1)
    try:
        if update.message.left_chat_member:
            log.warning("Left: {}".format(update.message.left_chat_member))
            Member.objects.filter(group__id=update.message.chat_id, member_id=update.message.from_user.id).update(status=Member.LEFT)
            return
    except Exception as err:
        log.error("Failed : ".format(err))
    # log.warning(2)
    # log.warning(update.message.chat.id)
    # log.warning(update.message.from_user.id)
    try:
        member = bot.getChatMember(update.message.chat.id, update.message.from_user.id)
        # log.warning("2a")
    except Exception as err:
        log.error(err)
        # TODO: Look for a way to make this function callable from within app by passing all required keys like chat_id, user_id, user_first_name etc
        return
    # log.warning(3)
    # log.warning("---in-- 2 ")
    if member.status in ['creator', 'administrator'] or update.message.from_user.is_bot:
        return
    mtype, mgroup = getType(update.message)
    # log.warning(4)
    # log.warning("Type [Message: {}, Group: {} ]".format(mtype, mgroup))
    try:
        getMember(update.message.from_user, update.message.chat.id)
    except Exception as err:
        pass
        # log.error("Error Adding memeber:  {}".format(err))
    # rules = BotClient.get_rules()
    rules = EngagementRule.load(timeout=60*60*24)   # Save it for 24hrs
    # log.warning(rules)
    rule = rules[mgroup.lower()]
    # log.warning(rule.__class__.__name__)
    # try:
    #     log.warning("{}".format(rule.to_dict()))
    # except Exception as err:
    #     log.warning(err)
    # log.warning(6)

    if rules["loaded"] and rule.is_allowed:
        acted = False
        if rule.is_rate_limited:
            import time
            # Message.objects.create(from_id=update.message.from_user.id, message_id=update.message.message_id, source=Message.CHANNEL, source_id=update.message.chat.id, text=update.message.text,
            #              type=mgroup, date=update.message.date, for_id=update.message.chat.id, treated=False)
            # now = timezone.now()
            # msgs = Message.objects.filter(created__gte=(now - timedelta(seconds=rule.rate_interval)), from_id=update.message.from_user.id, source_id=update.message.chat.id)
            # if msgs.count() >= rule.rate_counter:
            seconds = int(time.time())

            msg_keys = cache.keys("{}_{}_message_*".format(update.message.from_user.id, update.message.chat.id))
            # msg_count = cache.get("{}_{}_message_{}".format(update.message.from_user.id, update.message.chat.id, seconds)) or 0
            # msg_count += 1

            if len(msg_keys) + 1 >= rule.rate_counter:
                act(bot, update, rule)
                cache.delete_pattern("{}_{}_message_*".format(update.message.from_user.id, update.message.chat.id))
                botLog("{}:: Action: '{}' {}, for Exceeding Limit".format(update.message.chat.title, rule.action, update.message.from_user.first_name))
                acted = True  # Why you shouldn't return here, if the word used is a forbidden word. It need to be deleted

            cache.set("{}_{}_message_{}".format(update.message.from_user.id, update.message.chat.id, seconds), seconds, timeout=rule.rate_interval)

        if rule.keywords and len(rule.keywords) > 0:
            log.warning("Keywords Length: {}".format(len(rule.keywords.split(";"))))
            for k in rule.keywords.split(";"):
                # x += 1
                # log.warning("{}.  {} : {}".format(x, k.strip(), update.message.text.lower()))
                # log.warning("Result : {}".format(len(k.strip()) > 0 and k.strip().lower() in update.message.text.lower()))
                if len(k.strip()) > 0 and k.strip().lower() in update.message.text.lower():
                    # log.warning("1 can_delete: {}".format(rule.can_delete))
                    if rule.can_delete:
                        bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
                    if not acted:
                        act(bot, update, rule)
                        botLog("{}:: Action: '{}' {}, for using the Keyword '{}' in '{}'".format(update.message.chat.title, rule.action, update.message.from_user.first_name, k.strip(),
                                                                                                 update.message.text))
                    break
        if rule.regex and len(rule.regex) > 0:
            for r in rule.regex.split(";"):
                result = re.findall(r.strip(), update.message.text)
                if len(r.strip()) > 0 and len(result) > 0:
                    # log.warning("2 can_delete: {}".format(rule.can_delete))
                    if rule.can_delete:
                        bot.deleteMessage(chat_id=update.message.chat.id, message_id=update.message.message_id)
                    if not acted:
                        act(bot, update, rule)
                        botLog("{}:: Action: '{}' {}, for using the Banned '{}' ({})".format(update.message.chat.title, rule.action, update.message.from_user.first_name, result, update.message.text))
                    break
    elif rules["loaded"]:
        if rule.can_delete:
            bot.deleteMessage(chat_id=update.message.chat.id, message_id=update.message.message_id)
        act(bot, update, rule)


    log.warning(update.message.text)
    if member:
        try:
            admins = bot.getChatAdministrators(chat_id=update.message.chat.id)
            admin_users = loadAdmins(admins, group_id=update.message.chat.id)
        except Exception as err:
            log.error(err)
            return

        evict = checkNameImpersonationSingle(admin_users, member.user)
        if evict:
            bot.kickChatMember(chat_id=group.id, user_id=evict['user_id'], until_date=timezone.now() + timedelta(days=400))
            Member.objects.filter(group=group, member_id=evict['user_id']).update(status=Member.KICKED)
            log.warning("Kicked: {}".format(evict["reason"]))
        else:
            evict = checkPhotoImpersonationSingle(admin_users, member.user)
            if evict:
                bot.kickChatMember(chat_id=group.id, user_id=evict['user_id'], until_date=timezone.now() + timedelta(days=400))
                Member.objects.filter(group=group, member_id=evict['user_id']).update(status=Member.KICKED)
                log.warning("Kicked: {}".format(evict['reason']))


def main():
    log.warning("......Loading handlers for telegram bot")

    # Default dispatcher (this is related to the first bot in settings.DJANGO_TELEGRAMBOT['BOTS'])
    dp = DjangoTelegramBot.dispatcher
    # To get Dispatcher related to a specific bot
    # dp = DjangoTelegramBot.getDispatcher('BOT_n_token')     #get by bot token
    # dp = DjangoTelegramBot.getDispatcher('BOT_n_username')  #get by bot username

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    # dp.add_handler(CommandHandler("help", help))
    # dp.add_handler(CommandHandler("staff", staff))
    # From libs
    # dp.add_handler(CommandHandler(GROUP[1:], group, pass_args=True))

    # dp.add_handler(CommandHandler(RESTRICT[1:], restrictUser, pass_args=True))
    # dp.add_handler(CommandHandler(BAN[1:], banUser, pass_args=True))
    # dp.add_handler(CommandHandler(UNBAN[1:], unbanUser, pass_args=True))

    # dp.add_handler(CommandHandler(TEST_COMMAND[1:], test_command, pass_args=True))

    # ConversationHandler()
    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler([Filters.text], echo))
    dp.add_handler(MessageHandler([], modulator))

    # Filters.successful_payment
    # dp.add_handler(MessageHandler([], create_member))
    # dp.add_handler(MessageHandler([], test_msg))

    # log all errors
    dp.add_error_handler(error)