# -*-coding:utf-8-*-

from __future__ import unicode_literals

import logging

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.

# TEXT = "Text"
# CONTACT = "Text"
# LOCATION = "Text"
# VENUE = "Text"
# URL = "Text"
#
# AUDIO = "Audio"
# AUDIO_NOTE = "Audio Note"
# DOCUMENT = "Document"
# PHOTO = "Photos"
# VIDEO = "Video"
# VIDEO_NOTE = "Video Note"
#
# ANIMATION = "Animation"
# GAME = "Game"
# STICKERS = "Sticker"
#
#
from bot.utils import MEDIA_CATEGORY

log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        # if self.can_cache:
        #     self.set_cache()

    def delete(self, *args, **kwargs):
        pass

    def set_cache(self, obj=None, timeout=360):
        # try:
        #     iter(self)
        #     obj = list[self._result_cache]
        #     cache.set(self.__class__.__name__, obj)
        # except TypeError as err:
        #     log.warning(err)
        #     cache.set(self.__class__.__name__, self)
        try:
            if obj is None:
                cache.set(self.__class__.__name__, self, timeout=timeout)
            else:
                cache.set(self.__class__.__name__, obj, timeout=timeout)
        except Exception as err:
            log.error(err)

    @classmethod
    def reload(cls, id=None, timeout=360):
        cache.expire(cls.__name__, timeout=0)
        cls.load(id=id, timeout=timeout)

    @classmethod
    def load(cls, id=None, timeout=360, reload=False):
        rules = cache.get(cls.__name__)
        if reload or rules is None:
            if id is None:
                obj_dict = {}
                objs = cls.objects.all()
                log.warning("Total Objects: {} ================ Initialising  Rules ============".format(len(objs)))
                for e in objs:
                    obj_dict[e.type.lower()] = e
                obj_dict['loaded'] = True
                objs[0].set_cache(obj_dict, timeout=timeout)
                rules = obj_dict
            else:
                # TODO: find a set  self.pk = id
                obj, created = cls.objects.get_or_create(pk=id)
                if not created:
                    obj.set_cache()
        return rules


class EngagementRule(SingletonModel):
    TEXT = "Text"; PHOTO = "Photo"; AUDIO = "Audio"; VIDEO = "Video"; OTHERS = "Others"
    MEDIA_GROUP = [(TEXT, "Text"), (PHOTO, "Photo"), (AUDIO, "Audio"), (VIDEO, "Video"), (OTHERS, "Others")]

    READ_ONLY = "Readonly"; KICK = "Kick"
    ACTIONS = [(READ_ONLY, "Readonly"), (KICK, "Kick")]

    type = models.CharField(max_length=16, choices=MEDIA_GROUP)

    is_allowed = models.BooleanField(default=True)
    keywords = models.TextField(null=True, blank=True, default="sex; fuck; fcuk; shit; tits; boobs; cunt; ass; penis; asshole; whore; slut; bitch; 鸡巴/鸡吧; douche; arsehole; piss")
    regex = models.CharField(max_length=512, null=True, blank=True, default="[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,};(0x)?[0-9a-fA-F]{40}")

    is_rate_limited = models.BooleanField(default=True)
    rate_counter = models.IntegerField(default=0)
    rate_interval = models.IntegerField(default=0, help_text="Time in seconds")

    action = models.CharField(max_length=16, choices=ACTIONS, default=None, null=True, blank=True)
    limit_time = models.IntegerField(default=0, help_text="Time in minuets")

    can_delete = models.BooleanField(default=False)

    def to_dict(self):
        # log.warning(".----- {} ----.".format(self.type))
        prefix = self.type.lower()
        dic = {}
        dic['{}_type'.format(prefix)] = self.type
        dic['{}_is_allowed'.format(prefix)] = self.is_allowed

        if prefix == self.TEXT.lower():
            # log.warning('{}_keywords'.format(prefix))
            dic['{}_keywords'.format(prefix)] = self.keywords
            log.warning("0a ----- {} ----".format(dic))
            dic['{}_regex'.format(prefix)] = self.regex
            dic['{}_delete_forbidden'.format(prefix)] = self.can_delete

        dic['{}_is_rate_limited'.format(prefix)] = self.is_rate_limited
        dic['{}_rate_counter'.format(prefix)] = self.rate_counter
        dic['{}_rate_interval'.format(prefix)] = self.rate_interval
        if self.is_allowed:
            dic['{}_action_allowed'.format(prefix)] = self.action
            dic['{}_limit_time_allowed'.format(prefix)] = self.limit_time
            dic['{}_action_banned'.format(prefix)] = None
            dic['{}_limit_time_banned'.format(prefix)] = 0
            dic['{}_can_delete'.format(prefix)] = False
        else:
            dic['{}_action_allowed'.format(prefix)] = None
            dic['{}_limit_time_allowed'.format(prefix)] = 0
            dic['{}_action_banned'.format(prefix)] = self.action
            dic['{}_limit_time_banned'.format(prefix)] = self.limit_time
            dic['{}_can_delete'.format(prefix)] = self.can_delete
        # log.warning("3 ----- {} ----".format(dic))
        return dic

    def __str__(self):
        return "{} - {}".format(self.type, "Allowed" if self.is_allowed else "Banned")

    @classmethod
    def load(cls, gid=None, timeout=360, reload=False):
        rules = cache.get("{}_{}".format(gid, cls.__name__.lower()))
        if reload or rules is None:
            obj_dict = {}
            objs = cls.objects.all()
            # objs = cls.objects.filter(group_id=gid)
            log.warning("Total Objects: {} ================ Initialising  Rules ============".format(len(objs)))
            for e in objs:
                obj_dict[e.type.lower()] = e
            obj_dict['loaded'] = True
            # cache("{}_{}".format(cls.__name__.lower(), gid), obj_dict, timeout=timeout)
            cache.set("{}".format(cls.__name__.lower()), obj_dict, timeout=timeout)
            rules = obj_dict
        return rules

    class Meta:
        pass
        # unique_together = ('type', 'group')


class Chat(models.Model):
    TYPE = [("private", "Private"), ("group", "Group"), ("supergroup", "Super Group"), ("channel", "Channel")]

    id = models.BigIntegerField(primary_key=True, null=False, blank=False)
    type = models.CharField(max_length=128, choices=TYPE)
    title = models.CharField(max_length=128, null=True, blank=True, default=None)
    username = models.CharField(max_length=128, null=True, blank=True, default=None)
    first_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    last_name = models.CharField(max_length=128, null=True, blank=True, default=None, help_text="First name of the other party in a private chat")
    all_members_are_administrators = models.BooleanField(default=False)
    photo = models.ForeignKey('ChatPhoto', on_delete=models.CASCADE, default=None, null=True, blank=True)
    description = models.CharField(max_length=254, null=True, blank=True, default=None)
    invite_link = models.CharField(max_length=128, null=True, blank=True, default=None)
    pinned_message = models.ForeignKey('Message', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name='pinned_message')
    sticker_set_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    can_set_sticker_set = models.BooleanField(default=False)


class ChatPhoto(models.Model):
    small_file_id = models.CharField(max_length=32)
    big_file_id = models.CharField(max_length=32)


class Member(models.Model):
    INSTAGRAM = "Instagram"; TELEGRAM = "Telegram"
    TYPE = [(INSTAGRAM, INSTAGRAM), (TELEGRAM, TELEGRAM)]

    ACTIVE = "Active"; RESTRICTED = "Restricted"; KICKED = "Kicked"; LEFT = "Left"
    STATUS = [(ACTIVE, _("Active")), (RESTRICTED, _("Restricted")), (KICKED, _("Kicked")), (LEFT, _("Left"))]

    member_id = models.BigIntegerField(null=False, blank=False)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    username = models.CharField(max_length=128, null=True, blank=True, default=None)
    type = models.CharField(max_length=16, choices=TYPE, default=TELEGRAM)
    status = models.CharField(max_length=16, choices=STATUS, default=ACTIVE)
    language_code = models.CharField(max_length=128, null=True, blank=True, default=None)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, default=None)
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True, default=None)
    is_bot = models.BooleanField(default=False)
    batch_id = models.UUIDField(null=True, blank=True, default=None)
    is_blacklisted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {} ({})".format(self.first_name, self.last_name, "t" if self.type == Member.TELEGRAM else "i")

    class Meta:
        unique_together = ('member_id', 'type', 'group')


class Leech(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('member', 'group')


class Defaulter(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class IDefaulter(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class TelegramUser(models.Model):
    id = models.IntegerField(primary_key=True, null=False, blank=False)
    verified = models.BooleanField(default=False)
    bot_chat_history = models.BooleanField(default=False)
    bot_inline_geo = models.BooleanField(default=False)
    bot = models.BooleanField(default=False)
    username = models.CharField(max_length=128, null=True, blank=True, default=None)
    restricted = models.BooleanField(default=False)
    phone = models.CharField(max_length=32)
    access_hash = models.CharField(max_length=128)
    contact = models.BooleanField(default=False)
    restriction_reason = models.CharField(max_length=128)
    deleted = models.BooleanField(default=False)
    mutual_contact = models.BooleanField(default=False)
    bot_inline_placeholder = models.CharField(max_length=128)
    is_self = models.BooleanField(default=False)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    lang_code = models.CharField(max_length=128, null=True, blank=True, default=None)
    min = models.BooleanField(default=False)
    bot_info_version = models.CharField(max_length=128, null=True, blank=True, default=None)
    photo = models.CharField(max_length=128, null=True, blank=True, default=None)
    bot_nochats = models.BooleanField(default=False)

    def __init__(self, dictionary=None, *args, **kwargs):
        if dictionary:
            self.__dict__.update(dictionary)
        else:
            super(TelegramUser, self).__init__(*args, **kwargs)

    def tele_2_app(self, tele):
        return self.__dict__.update(tele.__dict__)


class Config(models.Model):
    TARGET_CHANNELS = "TARGET CHANNELS"; TARGET_GROUPS = "TARGET GROUPS"; TARGET_PRIVATE = "TARGET PRIVATE"; FORWARD_TO = "FORWARD TO"

    TYPE = [(TARGET_CHANNELS, "TARGET CHANNELS"), (TARGET_GROUPS, "TARGET GROUPS"), (TARGET_PRIVATE, "TARGET PRIVATE"), (FORWARD_TO, "FORWARD TO")]

    entity_id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64, null=True, blank=True, default=None)
    username = models.CharField(max_length=64, null=True, blank=True, default=None)
    access_hash = models.CharField(max_length=64)
    update = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s" % (self.first_name, "" if self.last_name is None else self.last_name )


class Client(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    phone = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64, null=True, blank=True, default=None)
    username = models.CharField(max_length=64, null=True, blank=True, default=None)
    access_hash = models.CharField(max_length=64)
    update = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s (%s)" % (self.first_name, ("" if self.last_name is None else self.last_name), self.phone)


class Channel(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=64)
    username = models.CharField(max_length=64, null=True, blank=True, default=None)
    access_hash = models.CharField(max_length=64)
    creator = models.BooleanField(default=False)
    update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # def save(self, *args, **kwargs):
    #     super(Channel, self).save(using='default')
    #     super(Channel, self).save(using='log')


class Coin(models.Model):
    NOT_TREATED = "Not Treated"; TREATED = "Treated"; FAILED_ATTEMPTS = "Failed Attempt"
    DONE = [(NOT_TREATED, "Not Treated"), (TREATED, "Treated"), (FAILED_ATTEMPTS, "Failed Attempt")]

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source = models.CharField(max_length=32)
    name = models.CharField(max_length=32)
    sell_value = models.DecimalField(decimal_places=8, max_digits=11, default=0)
    sell_percent = models.DecimalField(decimal_places=3, max_digits=6, default=0)
    buy_value = models.DecimalField(decimal_places=8, max_digits=11, default=0)
    buy_percent = models.DecimalField(decimal_places=3, max_digits=6, default=0)
    now_value = models.DecimalField(decimal_places=8, max_digits=11, default=0)
    now_percent = models.DecimalField(decimal_places=3, max_digits=6, default=0)
    stop_value = models.DecimalField(decimal_places=8, max_digits=11, default=0)
    stop_percent = models.DecimalField(decimal_places=3, max_digits=6, default=0)
    reward = models.DecimalField(decimal_places=8, max_digits=11, default=0)
    created = models.DateTimeField(auto_now_add=True)
    done = models.CharField(max_length=16, choices=DONE, default=NOT_TREATED)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # super(Coin, self).save(using='default_2')
        super(Coin, self).save(using='default')
        super(Coin, self).save(using='log')


class Group(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    title = models.CharField(max_length=64)
    username = models.CharField(max_length=64, null=True, blank=True, default=None)
    type = models.CharField(max_length=64)
    category = models.IntegerField(null=True, blank=True, default=5)
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Message(models.Model):
    INDIVIDUAL = 'Private'; GROUP = 'Group'; CHANNEL = 'Channel';
    MESSAGE_SOURCE = [(INDIVIDUAL, 'Private'), (GROUP, 'Group'), (CHANNEL, 'Channel')]

    from_id = models.BigIntegerField(null=True, blank=True, default=None)
    message_id = models.IntegerField(null=False, blank=False)
    source = models.CharField(null=True, blank=True, default=None, max_length=128, choices=MESSAGE_SOURCE)
    source_id = models.BigIntegerField(null=False, blank=False)
    text = models.TextField(null=True, blank=True, default=None)
    type = models.CharField(max_length=16, choices=MEDIA_CATEGORY)
    date = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    for_id = models.BigIntegerField()
    treated = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class MessageTemplate(models.Model):
    WELCOME = 'Welcome'; WARNING = 'Warning';
    # MESSAGE_TYPE = [(WELCOME, 'Welcome'), (WARNING, 'Warning')]
    MESSAGE_TYPE = [(WELCOME, 'Welcome')]

    type = models.CharField(null=True, blank=True, default=None, max_length=16, choices=MESSAGE_TYPE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, default=None)
    text = models.TextField(null=True, blank=True, default=None, help_text='''
        Avaiable Templates are: <br>
            {{first_name}}:  Paul <br>
            {{username}}:  paul_username <br>
            {{first_name_username}}:  Paul - paul_username <br>
            {{username_first_name}}:  paul_username - Paul
    ''')
    update = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Result(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source = models.CharField(max_length=32)
    coin_name = models.CharField(max_length=32)
    type = models.CharField(max_length=32)
    percent = models.DecimalField(decimal_places=8, max_digits=11, default=0)
    time = models.IntegerField(null=True, blank=True, default=0)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} ({})".format(self.source, self.coin_name)

    def save(self, *args, **kwargs):
        # super(Result, self).save(using='default_2')
        super(Result, self).save(using='default')
        super(Result, self).save(using='log')


#
# class Message(models.Model):
#     id = models.IntegerField(primary_key=True, null=False, blank=False)
#     fromm = models.ForeignKey(Member, blank=True, null=True, default=None, on_delete=models.CASCADE)
#     date = models.DateTimeField()
#     chat = models.ForeignKey(Chat, related_name='chat', on_delete=models.CASCADE)
#     forward_from = models.ForeignKey(Member, default=None, null=True, blank=True, related_name='forward_from', on_delete=models.CASCADE)
#     forward_from_chat = models.ForeignKey(Chat, null=True, blank=True, default=None, related_name='forward_from_chat', on_delete=models.CASCADE)
#     forward_from_message_id = models.IntegerField(null=True, blank=True, default=None)
#     forward_signature = models.CharField(null=True, blank=True, default=None, max_length=128)
#     forward_date = models.DateTimeField(null=True, blank=True, default=None,)
#     reply_to_message = models.ForeignKey('self', null=True, blank=True, default=None, on_delete=models.CASCADE)
#     edit_date = models.DateTimeField(null=True, blank=True, default=None,)
#     media_group_id = models.CharField(null=True, blank=True, default=None, max_length=128)
#     author_signature = models.CharField(null=True, blank=True, default=None, max_length=128)
#     text = models.TextField(null=True, blank=True, default=None)
#     # entities =
#     # caption_entities =


class MessageEntity(models.Model):
    # Can be mention (@username), hashtag, bot_command, url, email, bold (bold text), italic (italic text), code (monowidth string),
    # pre (monowidth block), text_link (for clickable text URLs), text_mention (for users without usernames)
    type = models.CharField(null=True, blank=True, default=None, max_length=128)
    offset = models.IntegerField()
    length = models.IntegerField()
    url = models.URLField(blank=True, null=True, default=None)
    member = models.ForeignKey(Member, default=None, null=True, blank=True, on_delete=models.CASCADE)


class PhotoSize(models.Model):
    file_id = models.CharField(primary_key=True, max_length=128)
    width = models.IntegerField()
    height = models.IntegerField()
    file_size = models.IntegerField(blank=True, null=True, default=None)


class Update(models.Model):
    id = models.IntegerField(primary_key=True, null=False, blank=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

