from __future__ import absolute_import, unicode_literals


# log = get_task_logger(__name__)
import json
import logging

import os
import urllib
from random import randint

import redis
from datetime import timedelta

from PIL import Image
from confusable_homoglyphs import confusables
from django.db.models import Q
from django.utils import timezone
from telegram.error import BadRequest

from bot.hash_utils import Hash
from bot.utils import TinClient, loadAdmins, checkNameImpersonationSingle, checkPhotoImpersonationSingle
from celery import shared_task
from django.conf import settings
from django.db import IntegrityError

import telegram
from bot.models import Member

log = logging.getLogger("tmessage.*")
log.setLevel(False)


@shared_task(name='bot.createMember')
def createMember(mid, username, first_name, last_name=None, type=Member.TELEGRAM):
    try:
        Member.objects.get_or_create(member_id=mid, first_name=first_name, last_name=last_name, username=username, type=type)
    except IntegrityError as err:
        log.error(err)
        log.error("Error saving.... Member_id: {}, Username: {}, First Name: {}, Last Name: {}".format(mid, username, first_name, last_name))


@shared_task(name='bot.welcomeMember')
def welcomeMember():
    from bot.models import MessageTemplate, Group
    redex = redis.StrictRedis(host=settings.REDIS_SERVER, port=settings.REDIS_PORT, db=0)

    try:
        new_members = json.loads(redex.get('new_members').decode('utf-8'))
    except Exception as err:
        new_members = []
    if len(new_members) > 0:
        redex.set('new_members', json.dumps([]))
        token = settings.DJANGO_TELEGRAMBOT['BOTS'][0]['TOKEN']
        msgs = MessageTemplate.objects.filter(type=MessageTemplate.WELCOME)

        if len(msgs) == 0:
            log.error("Welcome Message Template Not Defined")
            return

        msg = msgs[randint(0, len(msgs) - 1)]
        bot = telegram.Bot(token=token)

        chats_ids = set()
        for mm in new_members:
            chats_ids.add(mm['chat']['id'])

        for cid in chats_ids:
            first_names = []; usernames = []; first_name_username = []; username_first_name = []
            for mm in new_members:
                if cid == mm['chat']['id']:
                    m = mm['user']
                    first_names.append(m['first_name'])
                    usernames.append(m['username'])
                    first_name_username.append("{} - @{}".format(m['first_name'], m['username']))
                    username_first_name.append("{} - @{}".format(m['username'], m['first_name']))

            text = msg.text.replace("{{first_name}}", ", ".join(first_names))
            text = text.replace("{{username}}", ", ".join(usernames))
            text = text.replace("{{first_name_username}}",  ", ".join(first_name_username))
            text = text.replace("{{username_first_name}}",  ", ".join(username_first_name))
            log.warning(text)
            bot.sendMessage(cid, text=text, parse_mode=telegram.ParseMode.HTML)


@shared_task(name='bot.checkImpersonation')
def checkImpersonation(group_id=None, member_id=None):
    from bot.models import Member, Group, Message
    token = settings.DJANGO_TELEGRAMBOT['BOTS'][0]['TOKEN']
    bot = telegram.Bot(token=token)
    if group_id and member_id:
        pass
        return

    for group in Group.objects.filter(enabled=True):

        try:
            admins = bot.getChatAdministrators(chat_id=group.id)
        except Exception as err:
            admins = []
            log.error(err)
            continue
        # log.warning("{} ----1--- {}".format(group.id, len(admins)))
        # member_objs = Member.objects.filter(Q(member_id__in=Message.objects.filter(source_id=group.id, created__gt=timezone.now()-timedelta(hours=24)).values_list('from_id', flat=True).distinct()) | Q(status=Member.ACTIVE, group=group))
        member_objs = Member.objects.filter(Q(status__in=[Member.ACTIVE, Member.RESTRICTED], member_id__in=Message.objects.filter(source_id=group.id, created__gt=timezone.now()-timedelta(hours=24)).values_list('from_id', flat=True).distinct()) | Q(status=Member.ACTIVE, group=group))
        # log.warning(list(ids))
        # members = Member.objects.filter(member_id__in=ids)
        # log.warning("{} mem".format(len(member_objs)))

        try:
            admin_users = loadAdmins(admins)
        except Exception as err:
            continue

        for mObj in member_objs:
            # index += 1
            # log.warning("Chat: {} ({}), \tUser: {} {} ({})\n\n".format(group.title, group.id, mObj.first_name, mObj.last_name, mObj.username))
            try:
                member = bot.getChatMember(chat_id=group.id, user_id=mObj.member_id)
            except BadRequest as err:
                continue

            if member:
                # log.warning("Member been checked: {}".format(member))
                evict = checkNameImpersonationSingle(admin_users, member.user, lite=True)
                # log.warning("Evict 1:  {}".format(evict))
                if evict:
                    # log.warning("Evict 1 ({}) from :  {}".format(evict['user_id'], evict))
                    bot.kickChatMember(chat_id=group.id, user_id=evict['user_id'], until_date=timezone.now() + timedelta(days=400))
                    Member.objects.filter(group=group, member_id=evict['user_id']).update(status=Member.KICKED)
                    log.warning("Kicked: {}".format(evict["reason"]))
                else:
                    evict = checkPhotoImpersonationSingle(admin_users, member.user)
                    # log.warning("Evict 2:  {}".format(evict))
                    if evict:
                        # log.warning("Evict 2 ({}) from :  {}".format(evict['user_id'], evict))
                        bot.kickChatMember(chat_id=group.id, user_id=evict['user_id'], until_date=timezone.now() + timedelta(days=400))
                        Member.objects.filter(group=group, member_id=evict['user_id']).update(status=Member.KICKED)
                        log.warning("Kicked: {}".format(evict['reason']))

