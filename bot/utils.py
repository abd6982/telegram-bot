import logging

import unicodedata
import urllib
from datetime import timedelta, datetime, time

from decimal import Decimal

import os
import pytz
import subprocess

import re

import redis

import telegram, json
from confusable_homoglyphs import confusables
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.db.models.base import ModelState
from django.utils import timezone
from fuzzywuzzy import fuzz
from telethon import TelegramClient
from telethon.errors import UserNotMutualContactError
from telethon.tl.functions.channels import EditBannedRequest, InviteToChannelRequest, DeleteMessagesRequest
from telethon.tl.functions.contacts import GetContactsRequest, ResolveUsernameRequest
from telethon.tl.functions.messages import GetHistoryRequest, AddChatUserRequest
# from telethon.tl.functions.messages import GetHistoryRequest, DeleteMessagesRequest, AddChatUserRequest
from telethon.utils import get_input_peer
from unidecode import unidecode

from telethon.tl.types import UpdateShortMessage, PeerUser, MessageService, UpdateNewChannelMessage, UpdateUserTyping, UpdateUserStatus, UpdateShortChatMessage, PeerChannel, InputChannel, PeerChat, MessageActionChatDeleteUser, ChannelBannedRights, InputUser, InputPeerChannel

from bot.custom_exception import MissingConnectionException, InvalidClient
from bot.hash_utils import Hash

log = logging.getLogger("tmessage.*")
log.setLevel(False)


G_TEXT = "Text"
G_CONTACT = "Text"
G_LOCATION = "Text"
G_VENUE = "Text"
G_URL = "Text"

G_STICKER = "Photo"
G_PHOTO = "Photo"
G_ANIMATION = "Photo"

G_AUDIO = "Audio"
G_AUDIO_NOTE = "Audio"

G_VIDEO = "Video"
G_VIDEO_NOTE = "Video"

G_DOCUMENT = "Others"
G_GAME = "Others"


TEXT = "Text"
CONTACT = "Contact"
LOCATION = "Location"
VENUE = "Venue"
URL = "Url"

STICKER = "Sticker"
PHOTO = "Photo"
ANIMATION = "Animation"

AUDIO = "Audio"
AUDIO_NOTE = "Audio Note"

VIDEO = "Video"
VIDEO_NOTE = "Video Note"

DOCUMENT = "Document"
GAME = "Game"
OTHERS = "Others"

TEXT_GROUP = [TEXT, CONTACT, LOCATION, VENUE, URL]
PHOTO_GROUP = [STICKER, PHOTO, ANIMATION]
AUDIO_GROUP = [AUDIO, AUDIO_NOTE]
VIDEO_GROUP = [VIDEO, VIDEO_NOTE]
OTHER_GROUP = [DOCUMENT, GAME]

MEDIA_CATEGORY = [(G_TEXT, G_TEXT), (G_PHOTO, G_PHOTO), (G_AUDIO, G_AUDIO), (G_VIDEO, G_VIDEO), (G_DOCUMENT, G_DOCUMENT)]

MEDIAS = [TEXT, CONTACT, LOCATION, VENUE, URL, STICKER, PHOTO, ANIMATION, AUDIO, AUDIO_NOTE, VIDEO, VIDEO_NOTE, DOCUMENT, GAME]



def get_connection(label='default', **kwargs):

    try:
        connections = getattr(settings, 'EMAIL_CONNECTIONS')
        options = connections[label]
    except (KeyError, AttributeError) as e:
        options = []
        raise MissingConnectionException('Settings for connection "%s" were not found' % label)

    options.update(kwargs)
    return mail.get_connection(**options)


def get_receivers():
    recipients = [('Paul Okeke', 'pauldiconline@gmail.com'), ('Benfdela', 'Prowebmedia2@gmail.com')]
    return recipients


def callback(update):
    log.warning('I received:  ', update)


# for client in TeleClient.clients:
    # client.add_update_handler(callback)
    # client.add_update_handler(callback)


def ser(obj, model_instance):
    for k, v in vars(obj).items():
        print(k)
        model_instance

    klass = globals()["class_name"]
    instance = klass()


def get_seconds(n, time):
    n = int(n)
    if time in ['sec', 'secs']:
        return n
    elif time in ['min', 'mins']:
        return n * 60
    elif time in ['hour', 'hours']:
        return n * 60 * 60
    elif time in ['day', 'days']:
        return n * 24 * 60 * 60


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    if isinstance(obj, time):
        serial = obj.isoformat()
        return serial
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, ModelState):
        return "---"



# tt ="#CRYPTOLIONSOFFICIALLS [🔝24] (+344%) Win/Loses/Open: 78/63/2 WinRate: 55% Average signal ~6hours 29min🔵 #ZEN 🔵Sell 0.00400000 11.11% Buy  0.00360000 Now  0.00361196 0.33% (@ Bittrex)Stop 0.00330000 8.33% 💬 Original signal quote: Buy Some #ZEN now at 0.00360000. Sell : 0.00400000-0.00430000-0.00460000 Take stoploss at 0.00330000"
# tt="✅ #TEST [🔝27] #BLOCK ✅ Target +12.41%  in ~1hours 45min"
#
# "#CRYPTOLIONSOFFICIALLS [🔝24] (+344%)
# Win/Loses/Open: 78/63/2
# WinRate: 55% Average signal ~6hours 29min
#
# 🔵 #ZEN 🔵
# Sell 0.00400000 11.11%
# Buy  0.00360000
# Now  0.00361196 0.33% (@ Bittrex)
# Stop 0.00330000 8.33%
#
# 💬 Original signal quote:
# Buy Some #ZEN now at 0.00360000.
# Sell :
# 0.00400000-0.00430000-0.00460000
#
# Take stoploss at 0.00330000


def deEmojify(inputString):
    returnString = ""
    for character in inputString:
        try:
            character.encode("ascii")
            returnString += character
        except UnicodeEncodeError:
            replaced = unidecode(str(character))
            if replaced != '':
                returnString += replaced
            else:
                try:
                     returnString += "[" + unicodedata.name(character) + "]"
                except ValueError:
                     returnString += "[x]"
    return returnString


class TeleClient():
    id = 0
    allowedGroups = []
    clients = []
    client_objs = []
    default_api_id = 0

    # TARGET_CHANNELS = [1131704561, 1350457716, 1124723913, 1228129346, ]
    # TARGET_CHANNELS = [1158028079]
    TARGET_CHANNELS = []
    TARGET_GROUPS = []
    TARGET_PRIVATE = []

    ALLOWED_GROUP_IDS = []
    TARGET_CHANNELS_IDS = []
    TARGET_GROUPS_IDS = []
    TARGET_PRIVATE_IDS = []


    # FORWARD_TO = [1375066736]
    FORWARD_TO = []

    PUSH_2_MAIL = False
    PUSH_2_DB = False
    ANALYSE = False

    # If you already have a previous 'session_name.session' file, skip this.
    # client.sign_in(phone=None, code=None, password=None, bot_token=None, phone_code_hash=None)
    # client.send_code_request(phone, force_sms=False)
    # client.sign_in(phone=settings.CLIENT[0].PHONE)

    # @classmethod
    # def get_rules(cls):
    #     from bot.models import EngagementRule
    #     if len(cls.RULES['text']) == 0:
    #         for e in EngagementRule.objects.all():
    #             log.warning("================Initialising============")
    #             cls.RULES[e.type.lower()] = e
    #
    #     return cls.RULES

    @classmethod
    def get_config(cls, type_, ids_only=False):
        from bot.models import Config
        if type_ == Config.TARGET_GROUPS:
            if len(cls.TARGET_GROUPS) == 0:
                cls.TARGET_GROUPS = Config.objects.filter(type=type_)
                cls.TARGET_GROUPS_IDS = cls.TARGET_GROUPS.values_list("entity_id", flat=True)
            return cls.TARGET_GROUPS_IDS if ids_only else cls.TARGET_GROUPS

        elif type_ == Config.TARGET_PRIVATE:
            if len(cls.TARGET_PRIVATE) == 0:
                cls.TARGET_PRIVATE = Config.objects.filter(type=type_)
                cls.TARGET_PRIVATE_IDS = cls.TARGET_PRIVATE.values_list("entity_id", flat=True)
            return cls.TARGET_PRIVATE_IDS if ids_only else cls.TARGET_PRIVATE

        elif type_ == Config.TARGET_CHANNELS:
            if len(cls.TARGET_CHANNELS) == 0:
                cls.TARGET_CHANNELS = Config.objects.filter(type=type_)
                cls.TARGET_CHANNELS_IDS = cls.TARGET_CHANNELS.values_list("entity_id", flat=True)

            return cls.TARGET_CHANNELS_IDS if ids_only else cls.TARGET_CHANNELS

        elif type_ == Config.FORWARD_TO:
            if len(cls.FORWARD_TO) == 0:
                cls.FORWARD_TO = Config.objects.filter(type=type_)
                cls.FORWARD_TO_IDS = cls.FORWARD_TO.values_list("entity_id", flat=True)
            return cls.FORWARD_TO_IDS if ids_only else cls.FORWARD_TO
        else:
            return []

    @classmethod
    def get_clients(cls, is_core_client=True):
        from bot.models import Client
        if is_core_client:
            if len(cls.clients) == 0:
                cls.client_objs = Client.objects.filter(enabled=True)
                log.warning("******** - Initializing Clients - ***************")
                for c in cls.client_objs:
                    cc = TelegramClient(session=c.phone, api_id=c.id, api_hash=c.access_hash, update_workers=1, spawn_read_thread=False)
                    # cc.for_id = c
                    cls.clients.append(cc)
            return cls.clients
        else:
            if len(cls.client_objs) == 0:
                cls.client_objs = Client.objects.filter(enabled=True)
            return cls.client_objs

    def get_client_(self, id):
        for client in TeleClient.get_clients():
            if client.api_id == id:
                return client
        return None

    def set_id(self, id):
        self.id = id

    @classmethod
    def get_phone(cls, api_id):
        api_id = str(api_id)
        for c in cls.get_clients(is_core_client=False):
            if api_id == c.id:
                return c.phone
        return None

    @classmethod
    def get_api_id(cls, phone):
        for c in cls.get_clients(is_core_client=False):
            if phone == c.phone:
                return c.id
        return None

    @classmethod
    def get_title(cls, api_id=None, phone=None):
        api_id = str(api_id)
        for c in cls.get_clients(is_core_client=False):
            if api_id == c.id or phone == c.phone:
                return "{} {}".format(c.first_name, ("" if c.last_name is None else c.last_name))
        return None

    @classmethod
    def get_client(cls, api_id=None):
        api_id = int(api_id if api_id else cls.default_api_id)
        for c in cls.get_clients():
            if c.api_id == api_id:
                return c
        return None

    @classmethod
    def logout(cls, api_id):
        client = cls.get_client(api_id)

        if client:
            for handler in client.list_update_handlers():
                client.remove_update_handler(handler)
            client.disconnect()
            return client.log_out()
            try:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                os.remove(os.path.join(BASE_DIR, "%s.session" % cls.get_phone(api_id)))
            except:
                return False
            return True
        else:
            return False

    @classmethod
    def login(cls, api_id, code):
        from bot.models import TelegramUser
        client = cls.get_client(api_id)
        if not client or not client.connect():
            raise InvalidClient()
        try:
            me = client.sign_in(code=code)
        except ValueError as e:
            return False
        if me and cls.is_accessible(api_id):
            tu = TelegramUser()
            tu = tu.tele_2_app(me)
            # tu.save()
            return True
        return False

    @classmethod
    def login_request(cls, api_id):
        client = cls.get_client(api_id)
        if client and client.connect() and client.is_user_authorized():
            return True
        client.send_code_request(cls.get_phone(api_id))
        return True

    @classmethod
    def is_accessible(cls, api_id):
        client = cls.get_client(api_id)
        status = False
        if client:
            try:
                if client.connect():
                    status = client.is_user_authorized()
            except:
                status = False
        return status

    @classmethod
    def getAllowedGroups(cls):
        from bot.models import Group
        if len(cls.allowedGroups) == 0:
            cls.allowedGroups = Group.objects.filter(enabled=True)
        return cls.allowedGroups

    @classmethod
    def setAllowedGroups(cls, groups):
        cls.allowedGroups = groups

    @classmethod
    def getAllowedGroupIDs(cls):
        from bot.models import Group
        if len(cls.ALLOWED_GROUP_IDS) == 0:
            cls.ALLOWED_GROUP_IDS = Group.objects.filter(enabled=True).values_list('id', flat=True)
        return cls.ALLOWED_GROUP_IDS

    @classmethod
    def setAllowedGroupIDS(cls, ids):
        cls.ALLOWED_GROUP_IDS = ids

    def callback(self, update):
        print(".............")


def getMember(bot_user, chat_id):
    from bot.models import Member
    try:
        member_id = bot_user.id
    except (KeyError, AttributeError):
        return getMemberByDict(bot_user, chat_id)
    first_name = bot_user.first_name
    is_bot = bot_user.is_bot
    try:
        last_name = bot_user.last_name
    except (KeyError, AttributeError):
        last_name = None
    try:
        username = bot_user.username
    except (KeyError, AttributeError):
        username = None
    try:
        language_code = bot_user.language_code
    except (KeyError, AttributeError):
        language_code = None
    return Member.objects.create(member_id=member_id, first_name=first_name, last_name=last_name, username=username, group_id=chat_id, language_code=language_code, is_bot=is_bot)


def getMemberByDict(bot_user, chat_id):
    from bot.models import Member
    member_id = bot_user['id']
    first_name = bot_user['first_name']
    is_bot = bot_user['is_bot']
    try:
        last_name = bot_user['last_name']
    except (KeyError, AttributeError):
        last_name = None
    try:
        username = bot_user['username']
    except (KeyError, AttributeError):
        username = None
    try:
        language_code = bot_user['language_code']
    except (KeyError, AttributeError):
        language_code = None
    return Member.objects.create(member_id=member_id, first_name=first_name, last_name=last_name, username=username, group__id=chat_id, language_code=language_code, is_bot=is_bot)


def getIMember(i_user):
    from bot.models import Member
    try:
        member_id = i_user.pk
    except (KeyError, AttributeError):
        return getIMemberByDict(i_user)

    if len(i_user.full_name) > 0:
        full = i_user.full_name.split(" ")
        first_name = full.pop(0)
        last_name = " ".join(full)
    try:
        username = i_user.username
    except (KeyError, AttributeError):
        username = None

    return Member.objects.update_or_create(member_id=member_id, first_name=first_name, last_name=last_name, username=username, is_bot=False, type=Member.INSTAGRAM)


def getIMemberByDict(i_user):
    from bot.models import Member

    member_id = i_user['pk']

    if len(i_user['full_name']) > 0:
        full = i_user['full_name'].split(" ")
        first_name = full.pop(0)
        last_name = " ".join(full)
    else:
        first_name = last_name = ""
    try:
        username = i_user['username']
    except (KeyError, AttributeError):
        username = None

    try:
        return Member.objects.update_or_create(member_id=member_id, first_name=first_name, last_name=last_name, username=username, is_bot=False, type=Member.INSTAGRAM)
    except Exception as err:
        log.error(err)


def getGroup(chat):
    from bot.models import Group
    return Group.objects.update_or_create(id=chat.id, title=chat.title, username=chat.username, type=chat.type)


class TinClient():
    MEMBERS = []

    api_id = 109317
    api_hash = '71e0a46537592c6d2f2a56cfbfeba33a'
    phone = '+2348077737774'

    # api_id = 187136
    # api_hash = 'aa09410fbbccf046acf7ef14fb60efb6'
    # phone = '+00212661422956'

    # api_id = 160077
    # api_hash = '28bcfee96563fd4f3769fe45683388cb'
    # phone = '+447743770917'
    t_client = None

    TELEGRAM = "Telegram"
    INSTAGRAM = "Instagram"

    i_client = None

    @classmethod
    def getNewMembers(cls):
        return cls.MEMBERS

    @classmethod
    def addNewMember(cls, members):
        cls.MEMBERS.append(members)
        return cls.MEMBERS

    @classmethod
    def setNewMembers(cls, members):
        cls.MEMBERS = members

    @classmethod
    def getConnection(cls, type=TELEGRAM):
        if type == cls.TELEGRAM:
            if not cls.t_client:
                cls.t_client = TelegramClient(cls.phone[1:], cls.api_id, cls.api_hash, update_workers=1)
                cls.t_client.connect()
            return cls.t_client

    def getConnectionInstance(self, type=TELEGRAM):
        if type == self.TELEGRAM:
            client = TelegramClient(self.phone[1:], self.api_id, self.api_hash, update_workers=1)
            client.connect()
            return client


def deleteServiceMessage():
    from bot.models import Group
    client = TinClient.getConnection()
    authorised = client.is_user_authorized()
    if authorised:
        groups = Group.objects.filter(enabled=True)

        for group in groups:
            log.warning("***Checking group {} ({}) now.".format(group.title, group.id))
            gid = abs(int(group.id))
            if group.id.startswith('100') or group.id.startswith('-100'):
                gid = int(str(gid)[3:])
            try:
                entity = client.get_entity(PeerChannel(gid))
            except ValueError as err:
                log.warning(err)
                try:
                    entity = client.get_entity(PeerChat(gid))
                except ValueError as err:
                    log.warning(err)
                    return

            result = client(GetHistoryRequest(entity, limit=100, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0))
            msg_ids = []

            for m in result.messages:
                if isinstance(m, MessageService):
                    if (m.action, MessageActionChatDeleteUser):
                        msg_ids.append(m.id)

            if len(msg_ids) > 0:
                client.delete_messages(entity, msg_ids)
            else:
                log.warning("***No service Message to be deleted...")

        if len(groups) == 0:
            log.warning("***No Authorised Groups Found...")
    else:
        log.warning("***** Login required...")


def kickMemberOut(channel_id, user_id, kick=True):
    log.warning("Kick? {}:   Channel: {}:    User:  {}".format(kick, channel_id, user_id))
    client = TinClient.getConnection()
    authorised = client.is_user_authorized()

    if authorised:
        gid = abs(int(channel_id))
        channel_id = str(channel_id)
        if channel_id.startswith('100') or channel_id.startswith('-100'):
            gid = int(str(gid)[3:])
        try:
            user = client.get_input_entity(PeerUser(user_id=user_id))
            entity = client.get_input_entity(PeerChannel(gid))
        except ValueError as err:
            try:
                entity = client.get_input_entity(PeerChat(gid))
            except ValueError as err:
                log.error(err)
                return

        until = datetime(2040, 12, 25)
        if kick:
            rights = ChannelBannedRights(until, view_messages=True, send_messages=True, send_media=True, send_stickers=True, send_gifs=True, send_games=True, send_inline=True, embed_links=True)
        else:
            rights = ChannelBannedRights(until, view_messages=False, send_messages=False, send_media=False, send_stickers=False, send_gifs=False, send_games=False, send_inline=False, embed_links=False)

        client.invoke(EditBannedRequest(channel=entity, user_id=user, banned_rights=rights))
    else:
        log.warning("Client  unauthorised")


DEFAULT_CHANNEL = 1153647546
# DEFAULT_CHANNEL = 1188959006    #My Test


def addUser(client, username, channel_id=DEFAULT_CHANNEL):
    try:
        user = client.invoke(ResolveUsernameRequest(username))
        return add_user_by_id(client, user_id=user.users[0].id, channel_id=channel_id)
    except Exception as err:
        msg = "Add User @{} attempt to channel ({}) failed. Confirm the username is valid".format(username, channel_id)
        log.error(msg)
        log.error(err)
        return msg


def add_user_by_id(client, user_id, channel_id=DEFAULT_CHANNEL):
    try:
        # client.invoke(InviteToChannelRequest(get_input_peer(channel), [get_input_peer(user)]))
        # client.invoke(InviteToChannelRequest(
        #     # InputChannel(get_input_peer(user.chats[0]).channel_id, get_input_peer(user.chats[0]).access_hash),
        #     InputChannel(channel.id, channel.access_hash),
        #     [InputUser(get_input_peer(user.users[0]).user_id, get_input_peer(user.users[0]).access_hash)]
        # ))
        # client.invoke(InviteToChannelRequest(InputChannel(channel.id, channel.access_hash), [InputUser(get_input_peer(user.users[0]).user_id, get_input_peer(user.users[0]).access_hash)]))
        # client.invoke(InviteToChannelRequest(client.get_entity(PeerChannel(1188959006)), [user]))
        # client.invoke(InviteToChannelRequest(client.get_input_entity(PeerChannel(channel_id)), [client.get_input_entity(PeerUser(user_id=user.users[0].id))]))

        user_entity = client.get_input_entity(PeerUser(user_id))
        channel_entity = client.get_entity(PeerChannel(channel_id=int(channel_id)))
        client.invoke(InviteToChannelRequest(channel_entity, [user_entity]))

        log.warning("Added User: {} to Channel: {}".format(user_id, channel_id))
        return "User added successfully"
    except Exception as err:
        reason = err.args[1] if len(err.args) > 1 else err.message
        msg = "Add User {} attempt to channel ({}) failed [{}]".format(user_id, channel_id, reason)
        log.error(msg)
        log.error(err)
    return msg


def removeUser(client, username, channel_id=DEFAULT_CHANNEL):
    try:
        msg = removeUser_by_user(client, user=client(ResolveUsernameRequest(username)).users[0], channel_id=channel_id)
    except Exception as err:
        msg = "Attempt to kicked user @{}  from channel ({}) failed. Confirm the username is valid".format(username, channel_id)
        log.error(msg)
        log.error(err)
    return msg


def removeUser_by_user(client, user, channel_id=DEFAULT_CHANNEL):
    msg = ""
    try:
        until = datetime(2040, 12, 25)
        rights = ChannelBannedRights(until, view_messages=True, send_messages=True, send_media=True, send_stickers=True, send_gifs=True, send_games=True, send_inline=True, embed_links=True)

        channel_entity = client.get_input_entity(PeerChannel(channel_id=int(channel_id)))
        client(EditBannedRequest(channel_entity, client.get_input_entity(PeerUser(user_id=user.id)), banned_rights=rights))
        msg = 'Kicked User: {} from Channel ({})'.format(user.first_name, channel_id)
        log.warning(msg)
    except Exception as err:
        reason = err.args[1] if len(err.args) > 1 else err.message
        msg = "Attempt to kick User: {} from Channle ({}) failed [{}]".format(user.first_name, channel_id, reason)
        log.error(msg)
        log.error(err)
    return msg


def sendMsg(client, msg, channel_id=DEFAULT_CHANNEL):
    channel_entity = client.get_entity(PeerChannel(channel_id=int(channel_id)))
    client.send_message(entity=channel_entity, message=msg, reply_to=None, parse_mode=None, link_preview=True)


# InviteToChannelRequest
# def addMember(channel_id, user_id):
#     client = getConnection()
#     contacts = client(GetContactsRequest(''))
#     user = contacts.users[0]  # For instance
#     client.invoke(AddChatUserRequest(
#         chad_id=channel_id,
#         user_id=user,  # Yes, the name is misleading
#         fwd_limit=10
#     ))


def checkNameImpersonationSingle(admins, user, lite=False):
    for admin in admins:
        # log.warning("********* {} {} @({}) - {}".format(admin.first_name, admin.last_name, admin.username, user))
        afl = "{} {}".format(admin.first_name.strip(), admin.last_name.strip() if admin.last_name else "")
        fl = "{} {}".format(user.first_name.strip(), user.last_name.strip() if user.last_name else "")
        score = fuzz.ratio(afl, fl)
        if score > 80:
            log.warning("{}:{}? {}".format(fl, afl, score))
            return {"user_id": user.id, "reason": "'{} {}' for impersonating '{} {}' Rate: {}".format(fl, user.username, afl, admin.username, score)}
        if not lite:
            results = confusables.is_confusable(fl, greedy=True, preferred_aliases=['latin'])
            if results:
                _fl = fl
                for r in results:
                    for hom in r['homoglyphs']:
                        _fl = _fl.replace(r['character'], hom['c'])
                        if fuzz.ratio(afl, fl) > 80:
                            return {"user_id": user.id, "reason": "{} {} for impersonating '{} {}'".format(fl, user.username, afl, admin.username)}


# def loadAdmins(admins):
#     users = []
#     for au in admins:
#         photos = au.user.get_profile_photos().photos
#         # save_path = os.path.join(settings.MEDIA_ROOT, "profile/pictures/{}.{}".format(au.user.id, photos[0][0].get_file().file_path.split(".")[-1:][0]))
#         # au.image_path = urllib.request.urlretrieve(photos[0][0].get_file().file_path, save_path)[0]
#         if len(photos) > 0:
#             au.user.image_path = urllib.request.urlretrieve(photos[0][0].get_file().file_path, "media/profile/pictures/{}.{}".format(au.user.id, photos[0][0].get_file().file_path.split(".")[-1:][0]))[0]
#             hasher = Hash(os.path.join(settings.BASE_DIR, au.user.image_path))
#             au.user.image_score = hasher.ahash()
#             # au.user.image_score_decimal = int(au.user.image_score, base=2)
#             au.user.hash_score = hasher.calc_scores()
#         else:
#             au.user.image_path = None
#         users.append(au.user)
#     return users


def loadAdmins(bot, group_id, reload=False, timeout=60*60):
    from bot.models import Group, EngagementRule
    admin_users = cache.get("{}_admins".format(group_id)) or []
    if len(admin_users) == 0 or reload:
        admins = bot.getChatAdministrators(chat_id=group_id)
        rules = EngagementRule.load(gid=group_id, timeout=60*60*24)
        if rules['loaded']:
            if True:
                for au in admins:
                    photos = au.user.get_profile_photos().photos
                    # save_path = os.path.join(settings.MEDIA_ROOT, "profile/pictures/{}.{}".format(au.user.id, photos[0][0].get_file().file_path.split(".")[-1:][0]))
                    # au.image_path = urllib.request.urlretrieve(photos[0][0].get_file().file_path, save_path)[0]
                    if len(photos) > 0:
                        try:
                            au.user.image_path = urllib.request.urlretrieve(photos[0][0].get_file().file_path, "media/profile/pictures/{}/{}.{}".format(group_id, au.user.id, photos[0][0].get_file().file_path.split(".")[-1:][0]))[0]
                            hasher = Hash(os.path.join(settings.BASE_DIR, au.user.image_path))
                            au.user.image_score = hasher.ahash()
                            # au.user.image_score_decimal = int(au.user.image_score, base=2)
                            au.user.hash_score = hasher.calc_scores()
                        except Exception as err:
                            log.error(err)
                    else:
                        au.user.image_path = None
                    admin_users.append(au.user)
                cache.set("{}_admins".format(group_id), admin_users, timeout=timeout)
            else:
                for au in admins:
                    admin_users.append(au.user)
    return admin_users


def checkPhotoImpersonationSingle(admins, user):
    photos = user.get_profile_photos().photos
    if len(photos) > 0:
        image_path = urllib.request.urlretrieve(photos[0][0].get_file().file_path, "media/profile/pictures/{}.{}".format(user.id, photos[0][0].get_file().file_path.split(".")[-1:][0]))[0]
        hasher = Hash(os.path.join(settings.BASE_DIR, image_path))
        image_score = hasher.ahash()
        # u.image_score_decimal = int(u.image_score, base=2)
        hash_score = hasher.calc_scores()

        for admin in admins:
            if admin.image_path:
                vector = []
                for h1, h2 in zip(hash_score, admin.hash_score):
                    vector.append(Hash.calc_difference(h1[1], h2[1]))

                diff = 0
                for i in range(len(admin.image_score)):
                    if image_score[i] != admin.image_score[i]:
                        diff += 1

                if Hash.predict(vector) or diff < 80:
                    return {"user_id": user.id, "reason": "{} {} {} was found using same picture ({}) with Admin ({} {}) [Difference Score: {}/256]".
                                 format(user.first_name, user.last_name, ("" if user.username is None else "(@"+ user.username +")"), image_path, admin.first_name, admin.last_name or "", diff)}

    return None


def checkPhotoImpersonation(admins, users):
    evict = []
    for user in users:
        photos = user.get_profile_photos().photos
        if len(photos) > 0:
            image_path = urllib.request.urlretrieve(photos[0][0].get_file().file_path, "media/profile/pictures/{}.{}".format(user.id, photos[0][0].get_file().file_path.split(".")[-1:][0]))[0]
            hasher = Hash(os.path.join(settings.BASE_DIR, image_path))
            image_score = hasher.ahash()
            # u.image_score_decimal = int(u.image_score, base=2)
            hash_score = hasher.calc_scores()

            for admin in admins:
                if admin.image_path:
                    vector = []
                    for h1, h2 in zip(hash_score, admin.hash_score):
                        vector.append(Hash.calc_difference(h1[1], h2[1]))

                    if Hash.predict(vector):
                        diff = 0
                        for i in range(len(admin.image_score)):
                            if image_score[i] != admin.image_score[i]:
                                diff += 1
                        evict.append({"user_id": user.id, "reason": "{} {} {} was found using same picture ({}) with Admin ({} {} [Difference Score: {}/256]".
                                     format(user.first_name, user.last_name, ("" if user.username is None else "(@"+ user.username +")"), image_path, admin.first_name, admin.last_name, diff)})
                        break
    return evict


def botLog(bot, text, further=False):
    bot.sendMessage(chat_id=settings.LOG_CHANNEL_ID, text=text)


def botKick(bot, chat_id, user_id, log_text=None, further=False):
    bot.kickChatMember(chat_id=chat_id, user_id=user_id, until_date=timezone.now() + timedelta(days=400))
    if log_text:
        botLog(bot, text=log_text, further=further)
