import functools
import json
import logging

import subprocess

import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from telethon.errors import FloodWaitError
from telethon.tl.functions.contacts import ResolveUsernameRequest

from bot.apps import BotClient
from bot.utils import TeleClient, addUser, removeUser, DEFAULT_CHANNEL, sendMsg, TinClient
from bot.forms import UserForm, EngagementRuleForm
from bot.models import Message, Coin, Result, Client, Defaulter, Group, Member, Leech, IDefaulter, EngagementRule
from django_telegrambot.apps import DjangoTelegramBot
from django.db import connection

log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)

app_type = settings.TYPE


# Create your views here.
def index(request):
    bot_list = DjangoTelegramBot.bots
    context = {'bot_list': bot_list, 'update_mode':settings.DJANGO_TELEGRAMBOT['MODE']}
    return render(request, 'bot/index.html', context)


@staff_member_required
def home(request):
    client_list = TeleClient().get_clients()

    msg = request.GET.get('msg', None)

    clients = []
    for c in client_list:
        a_handlers = c.list_update_handlers()
        handlers = [("Push to Mail/DB", "push_2_mail_db")]
        # handlers = ["Push to Mail/DB"]
        active_handlers = []
        for ah in a_handlers:
            active_handlers.append(ah.__name__)
        clients.append({'api_id': c.api_id, 'phone': TeleClient.get_phone(c.api_id), 'title': TeleClient.get_title(api_id=c.api_id), 'status': TeleClient.is_accessible(c.api_id), 'handlers': handlers, 'active_handlers': active_handlers})
    return render(request, 'bot/index.html', context={'clients': clients, 'msg': msg, 'type': app_type})


@staff_member_required
def init(request):
    msg = TeleClient.init()
    log.warning("--------------------%s-----------------------" % msg)
    return JsonResponse(msg, safe=False)


@staff_member_required
def restart_service(request):
    # return JsonResponse(restart.restart_t_client(), safe=False)
    return JsonResponse({}, safe=False)


@login_required
def messages(request, id=None):
    if id:
        context = Message.objects.filter(for_id=id).order_by('-created')
    else:
        context = Message.objects.all().order_by('-created')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(text__icontains=q) | Q(from_id__icontains=q) | Q(source__icontains=q)).order_by('-created')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/messages.html', context={'context': context, 'q': q, 'account': id, 'type': app_type})


@login_required
def client(request, id=None):
    if id:
        context = Client.objects.filter(id=id).order_by('phone')
    else:
        context = Client.objects.all().order_by('phone')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(id__icontains=q) | Q(phone__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q)).order_by('-created')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/client-details.html', context={'context': context, 'q': q, 'type': app_type})


@login_required
def bot(request, id=None):
    # data = [{"id": "544559680", "username": "m_controller_bot", "first_name": "m_controller_bot"},]

    return render(request, 'bot/bot-details.html', context={'context': {}, 'type': app_type})


@login_required
def member(request, member_id=None, group_id=None):
    if member_id and group_id:
        context = Member.objects.filter(member_id=member_id, group_id=group_id).order_by('-created', 'member_id')
    else:
        context = Member.objects.all().order_by('-created', 'member_id')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        try:
            q = int(q)
            context = context.filter(member_id__exact=q).order_by('-created', 'member_id')
        except:
            context = context.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(user__username__icontains=q)).order_by('-created', 'member_id')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/member-details.html', context={'context': context, 'q': q, 'type': app_type,})


@login_required
def rule_detail(request, type=None):
    if type:
        context = EngagementRule.objects.filter(type=type)
    else:
        context = None
        # context = EngagementRule.objects.all().order_by('type')

    if request.method == "POST":
        form = EngagementRuleForm(request.POST, instance=context)
        if form.is_valid():
            form.save(commit=False)
            form.save()
            return redirect(reverse("core:rule-detail"))
    else:
        form = EngagementRuleForm(instance=context)

    return render(request, 'bot/rule-detail.html', context={'context': context, 'form': form, 'type': app_type,})


@login_required
def rule_add(request, type=None):
    if type:
        context = EngagementRule.objects.filter(type=type)
    else:
        context = None
        # context = EngagementRule.objects.all().order_by('type')

    if request.method == "POST":
        form = EngagementRuleForm(request.POST)
        if form.is_valid():

            is_allowed = form.cleaned_data.get('text_is_allowed', False)
            rate_counter = rate_interval = limit_time = 0
            action = None
            is_rate_limited = can_delete = False
            if is_allowed:
                is_rate_limited = form.cleaned_data.get('text_is_rate_limited', False)
                if is_rate_limited:
                    rate_counter = form.cleaned_data.get('text_rate_counter', 3)
                    rate_interval = form.cleaned_data.get('text_rate_interval', 1)

                keywords = form.cleaned_data.get('text_keywords', "").strip()
                regex = form.cleaned_data.get('text_regex', "").strip()

                if is_rate_limited or len(keywords) > 0 or len(regex) > 0:
                    action = form.cleaned_data.get('text_action_allowed', EngagementRuleForm.KICK)
                    limit_time = 60 if form.cleaned_data.get('text_limit_time_allowed', 60) is None else form.cleaned_data.get('text_limit_time_allowed', 60)

                if len(keywords) > 0 or len(regex) > 0:
                    can_delete = form.cleaned_data.get('text_delete_forbidden', False)
            else:
                action = form.cleaned_data.get('text_action_banned', EngagementRuleForm.KICK)
                limit_time = 60 if form.cleaned_data.get('text_limit_time_banned', 60) is None else form.cleaned_data.get('text_limit_time_banned', 60)
                can_delete = form.cleaned_data.get('text_can_delete', False)
            
            text_rule = EngagementRule.objects.filter(type=EngagementRule.TEXT).first()
            if text_rule:
                EngagementRule.objects.filter(type=EngagementRule.TEXT).update(is_allowed=is_allowed, keywords=keywords, regex=regex, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)
            else:
                EngagementRule.objects.create(type=EngagementRule.TEXT, is_allowed=is_allowed, keywords=keywords, regex=regex, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)
            
            
            is_allowed = form.cleaned_data.get('photo_is_allowed', False)
            rate_counter = rate_interval = limit_time = 0
            action = None
            is_rate_limited = can_delete = False
            if is_allowed:
                is_rate_limited = form.cleaned_data.get('photo_is_rate_limited', False)
                if is_rate_limited:
                    rate_counter = form.cleaned_data.get('photo_rate_counter', 3)
                    rate_interval = form.cleaned_data.get('photo_rate_interval', 1)
                    action = form.cleaned_data.get('photo_action_allowed', EngagementRuleForm.KICK)
                    limit_time = 60 if form.cleaned_data.get('photo_limit_time_allowed', 60) is None else form.cleaned_data.get('photo_limit_time_allowed', 60)
            else:
                action = form.cleaned_data.get('photo_action_banned', EngagementRuleForm.KICK)
                limit_time = 60 if form.cleaned_data.get('photo_limit_time_banned', 60) is None else form.cleaned_data.get('photo_limit_time_banned', 60)
                can_delete = form.cleaned_data.get('photo_can_delete', False)
            
            photo_rule = EngagementRule.objects.filter(type=EngagementRule.PHOTO).first()
            if photo_rule:
                EngagementRule.objects.filter(type=EngagementRule.PHOTO).update(is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)
            else:
                EngagementRule.objects.create(type=EngagementRule.PHOTO, is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)

            is_allowed = form.cleaned_data.get('audio_is_allowed', False)
            rate_counter = rate_interval = limit_time = 0
            action = None
            is_rate_limited = can_delete = False
            if is_allowed:
                is_rate_limited = form.cleaned_data.get('audio_is_rate_limited', False)
                if is_rate_limited:
                    rate_counter = form.cleaned_data.get('audio_rate_counter', 3)
                    rate_interval = form.cleaned_data.get('audio_rate_interval', 1)
                    action = form.cleaned_data.get('audio_action_allowed', EngagementRuleForm.KICK)
                    limit_time = 60 if form.cleaned_data.get('audio_limit_time_allowed', 60) is None else form.cleaned_data.get('audio_limit_time_allowed', 60)
            else:
                action = form.cleaned_data.get('audio_action_banned', EngagementRuleForm.KICK)
                limit_time = 60 if form.cleaned_data.get('audio_limit_time_banned', 60) is None else form.cleaned_data.get('audio_limit_time_banned', 60)
                can_delete = form.cleaned_data.get('audio_can_delete', False)
            
            audio_rule = EngagementRule.objects.filter(type=EngagementRule.AUDIO).first()
            if audio_rule:
                EngagementRule.objects.filter(type=EngagementRule.AUDIO).update(is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)
            else:
                EngagementRule.objects.create(type=EngagementRule.AUDIO, is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)


            is_allowed = form.cleaned_data.get('video_is_allowed', False)
            rate_counter = rate_interval = limit_time = 0
            action = None
            is_rate_limited = can_delete = False
            if is_allowed:
                is_rate_limited = form.cleaned_data.get('video_is_rate_limited', False)
                if is_rate_limited:
                    rate_counter = form.cleaned_data.get('video_rate_counter', 3)
                    rate_interval = form.cleaned_data.get('video_rate_interval', 1)
                    action = form.cleaned_data.get('video_action_allowed', EngagementRuleForm.KICK)
                    limit_time = 60 if form.cleaned_data.get('video_limit_time_allowed', 60) is None else form.cleaned_data.get('video_limit_time_allowed', 60)
            else:
                action = form.cleaned_data.get('video_action_banned', EngagementRuleForm.KICK)
                limit_time = 60 if form.cleaned_data.get('video_limit_time_banned', 60) is None else form.cleaned_data.get('video_limit_time_banned', 60)
                can_delete = form.cleaned_data.get('video_can_delete', False)
            
            video_rule = EngagementRule.objects.filter(type=EngagementRule.VIDEO).first()
            if video_rule:
                EngagementRule.objects.filter(type=EngagementRule.VIDEO).update(is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)
            else:
                EngagementRule.objects.create(type=EngagementRule.VIDEO, is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)

            is_allowed = form.cleaned_data.get('others_is_allowed', False)
            rate_counter = rate_interval = limit_time = 0
            action = None
            is_rate_limited = can_delete = False
            if is_allowed:
                is_rate_limited = form.cleaned_data.get('others_is_rate_limited', False)
                if is_rate_limited:
                    rate_counter = form.cleaned_data.get('others_rate_counter', 3)
                    rate_interval = form.cleaned_data.get('others_rate_interval', 1)
                    action = form.cleaned_data.get('others_action_allowed', EngagementRuleForm.KICK)
                    limit_time = 60 if form.cleaned_data.get('others_limit_time_allowed', 60) is None else form.cleaned_data.get('others_limit_time_allowed', 60)
            else:
                action = form.cleaned_data.get('others_action_banned', EngagementRuleForm.KICK)
                limit_time = 60 if form.cleaned_data.get('others_limit_time_banned', 60) in [None, 60] else form.cleaned_data.get('others_limit_time_banned', 60)
                can_delete = form.cleaned_data.get('others_can_delete', False)
            
            others_rule = EngagementRule.objects.filter(type=EngagementRule.OTHERS).first()
            if others_rule:
                EngagementRule.objects.filter(type=EngagementRule.OTHERS).update(is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)
            else:
                EngagementRule.objects.create(type=EngagementRule.OTHERS, is_allowed=is_allowed, is_rate_limited=is_rate_limited, rate_counter=rate_counter, rate_interval=rate_interval, action=action, limit_time=limit_time, can_delete=can_delete)

            EngagementRule.load(timeout=None, reload=True)
            return redirect("{}?msg={}".format(reverse("core:bot-rule-add"), "Saved Successfully"))
    else:
        rules = {}
        for e in EngagementRule.objects.all():
            rules = {**rules, **e.to_dict()}

        form = EngagementRuleForm(initial=rules)

    msg = request.GET.get('msg', None)
    return render(request, 'bot/rule-form.html', context={'context': context, 'form': form, 'type': app_type, "msg": msg})



@login_required
def i_member_blacklist(request, username=None):
    if username:
        i_client = TinClient.getConnection(type=TinClient.INSTAGRAM)
        status = i_client.searchUsername(username[1:].strip()) if username.startswith("@") else i_client.searchUsername(username.strip())
        if status:
            return JsonResponse({'msg': 'success', 'iuser': i_client.LastJson['user']})
        else:
            return JsonResponse({'msg': 'Invalid Username'}, safe=False)
    elif request.method == "POST":
        log.warning(request.POST['group_id'])
        member = Member.objects.filter(member_id=request.POST['member_id'], type=Member.INSTAGRAM).first()
        log.warning(member)
        if member is None:
            member = Member.objects.update_or_create(member_id=request.POST['member_id'], first_name=request.POST['first_name'], last_name=request.POST['last_name'], username=request.POST['username'],
                                                     type=Member.INSTAGRAM, is_blacklisted=True)
        else:
            member.is_blacklisted =True
            member.save()

        return JsonResponse({'msg': 'success', })
    return JsonResponse({'msg': 'Invalid Username'}, safe=False)


@login_required
def t_member_leech(request, username=None):
    if username:
        t_client = TinClient.getConnection(type=TinClient.TELEGRAM)
        result = t_client(ResolveUsernameRequest(username[1:].strip())) if username.startswith("@") else t_client(ResolveUsernameRequest(username.strip()))

        if len(result.users) > 0:
            user = result.users[0]

            return JsonResponse({'msg': 'success', 'tuser': {"first_name": user.first_name, "id": user.id, "username": user.username, "last_name": user.last_name}})
        else:
            return JsonResponse({'msg': 'Invalid Username'}, safe=False)
    elif request.method == "POST":
        member = Member.objects.filter(member_id=request.POST['member_id'], type=Member.TELEGRAM).first()
        log.warning(member)
        if member is None:
            member = Member.objects.update_or_create(member_id=request.POST['member_id'], first_name=request.POST['first_name'], last_name=request.POST['last_name'], username=request.POST['username'], type=Member.TELEGRAM, is_blacklisted=False)

        try:
            Leech.objects.create(member=member, group=Group(id=request.POST['group_id']))
            Defaulter.objects.filter(member=member, group=Group(id=request.POST['group_id'])).delete()
        except IntegrityError as err:
            return JsonResponse({'msg': 'Something went wrong'}, safe=False)

        return JsonResponse({'msg': 'success', })
    return JsonResponse({'msg': 'Invalid Username'}, safe=False)


@login_required
def member_whitelist(request, id, action="whitelist"):
    return member_blacklist(request, id, action)


@login_required
def member_blacklist(request, id=None, action="blacklist"):
    if id is None:
        members=Member.objects.filter(is_blacklisted=True, type=Member.INSTAGRAM)
        return render(request, 'bot/i-blacklisted.html', context={'context': members })
    else:
        Member.objects.filter(id=id).update(is_blacklisted=(action == "blacklist"))

    context = Member.objects.all().order_by('-created', 'member_id')
    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(member_id=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(user__username__icontains=q)).order_by('-created', 'member_id')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/member-details.html', context={'context': context, 'q': q, 'type': app_type,})

@login_required
def member_blacklisted(request, gid, json=False):
    context = Member.objects.filter(idefaulter__group__id=gid).distinct().order_by('-created', 'member_id')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(member_id=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(user__username__icontains=q)).order_by('-created', 'member_id')

    if json:
        return JsonResponse(list(context.values_list('member_id', flat=True)), safe=False)

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/member-details.html', context={'context': context, 'q': q, 'type': app_type,})



@login_required
def tdefaulter(request, id=None):
    if id:
        context = Defaulter.objects.filter(id=id).order_by('-created', 'member_id')
    else:
        context = Defaulter.objects.all().order_by('-created', 'member_id')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(id__icontains=q) | Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(member__username__icontains=q) | Q(member__user__username__icontains=q)).order_by('-created', 'member__id')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/defaulter-details.html', context={'context': context, 'q': q, 'type': app_type,})


@login_required
def idefaulter(request, id=None):
    # if id:
    #     context = IDefaulter.objects.filter(id=id).order_by('-created', 'member_id')
    # else:
    #     context = IDefaulter.objects.all().order_by('-created', 'member_id')

    cursor = connection.cursor()
    cursor.execute('SELECT m.member_id, m.first_name, m.last_name, m.username, g.title, m.id, g.id, m.is_blacklisted, count(*) as count FROM bot_idefaulter d LEFT JOIN bot_member m ON d.member_id =m.id LEFT JOIN bot_group g on d.group_id=g.id GROUP BY  m.member_id, m.first_name, m.last_name, m.username, g.title, m.id, g.id, m.is_blacklisted')
    rows = cursor.fetchall()
    log.warning(rows)
    q = request.GET.get('q', None)
    # if q:
    #     q = None if q == "None" else q
    #     context = context.filter(Q(id__icontains=q) | Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(member__username__icontains=q) | Q(member__user__username__icontains=q)).order_by('-created', 'member__id')

    # page = request.GET.get('page', 1)
    #
    # paginator = Paginator(context, 200)
    # try:
    #     context = paginator.page(page)
    # except PageNotAnInteger:
    #     context = paginator.page(1)
    # except EmptyPage:
    #     context = paginator.page(paginator.num_pages)

    return render(request, 'bot/idefaulter-details.html', context={'context': rows, 'q': q, 'type': app_type,})


@login_required
def leech(request, id=None):
    if id:
        context = Leech.objects.filter(id=id).order_by('-created', 'member__id')
    else:
        context = Leech.objects.all().order_by('-created', 'id')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(id__icontains=q) | Q(member__first_name__icontains=q) | Q(member__last_name__icontains=q) | Q(member__username__icontains=q) | Q(member__user__username__icontains=q)).order_by('-created', 'member__id')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/leech-details.html', context={'context': context, 'q': q, 'type': app_type,})


@login_required
def leech_remove(request, member_id, group_id, action="remove"):
    return leech_add(request, member_id, group_id, action)


@login_required
def leech_add(request, member_id, group_id, action="add"):
    if action == "add":
        try:
            Leech.objects.create(member=Member(id=member_id), group=Group(id=group_id))
            Defaulter.objects.filter(member=Member(id=member_id), group=Group(id=group_id)).delete()
        except IntegrityError as err:
            pass
    elif action == "remove":
        Leech.objects.filter(member__id=member_id, group__id=group_id).delete()

    context = Leech.objects.all()
    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/leech-details.html', context={'context': context, 'type': app_type,})


@login_required
def group(request, id=None, action=None):
    if id:
        context = Group.objects.filter(id=id).order_by('title')
    else:
        context = Group.objects.all().order_by('title')

    if id and action in ['enable', 'disable'] and len(context) > 0 and request.method == "POST":
        group = context[0]
        group.enabled = True if action == 'enable' else False
        group.save()
        context = []
        context.append(group)
        return JsonResponse({'msg': "Completed Successfully...", 'type': "Success"})
    elif id and action == "update" and len(context) > 0 and request.method == "POST":
        group = context[0]
        log.warning("here to update")
        log.warning(group)
        log.warning(request.POST['category'])
        group.category = request.POST['category']
        group.save()
        return JsonResponse({'msg': "Completed Successfully...", 'type': "Success"})

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(id__icontains=q) | Q(title__icontains=q) | Q(username__icontains=q) | Q(type__icontains=q)).order_by('title')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/group-details.html', context={'context': context, 'q': q, 'type': app_type,})


@staff_member_required
def processor_stop(request, id, method_name, action="stop"):
    return processor(request, id, method_name, action)


@staff_member_required
def processor(request, id, method_name, action="start"):
    return redirect("{}?msg={}".format(reverse("core:home"), "Operation Disabled"))
    id = int(id)

    # client = TeleClient.get_client(id)
    client = TeleClient()
    client.set_id(id)

    if not client:
        return redirect("{}?msg={}".format(reverse("core:home"), "Something went wrong"))

    msg = "Processor was not On"
    method = None
    if method_name == "push_2_mail_db":
        method = client.push_2_mail_db
    elif method_name == "callback":
        method = client.callback

    if method and action in ["start", "stop"]:
        start = True
        # for_id = client.get_me().id
        for h in client.get_client(client.id).list_update_handlers():
            log.warning("Method Name: %s " % h.__name__)
            if h.__name__ == method_name:
                start = False
                client.get_client(client.id).remove_update_handler(h)
                # client.id = id
                msg = "Processor Stopped..."
                if action == "start":
                    start = False
                    # h.__defaults__ = (None, id)
                    client.get_client(client.id).add_update_handler(h)
                    client.get_client(client.id).idle()
                    client.get_client(client.id).disconnect()
                    msg = "Processor Started..."
                break
        if start and action == "start":
            # method.__defaults__ = (None, id)
            client.get_client(client.id).add_update_handler(method)
            msg = "Processor Started..."
    else:
        msg = None

    return redirect("{}?msg={}".format(reverse("core:home"), msg))


def coin_data(request, name=None, id=None):
    if id:
        id = int(id)
        context = Coin.objects.filter(id=id)
    elif name:
        context = Coin.objects.filter(name=name).order_by('-created')
    else:
        context = Coin.objects.all().order_by('-created')

    q = request.GET.get('q', None)
    if q:
        q = None if q == "None" else q
        context = context.filter(Q(name__icontains=q)).order_by('-created')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/coin-market.html', context={'context': context, 'q': q, 'type': app_type, })


def coin_result(request, name=None, id=None):
    if id:
        id = int(id)
        context = Result.objects.filter(id=id)
    elif name:
        context = Result.objects.filter(name=name).order_by('-created')
    else:
        context = Result.objects.all().order_by('-created')

    q = request.GET.get('q', None)
    if q:
        q = None if q=="None" else q
        context = context.filter(Q(channel__title__icontains=q) | Q(client__phone__icontains=q) | Q(client__first_name__icontains=q) | Q(source__icontains=q) | Q(coin_name__icontains=q) | Q(type__icontains=q)).order_by('-created')

    page = request.GET.get('page', 1)

    paginator = Paginator(context, 200)
    try:
        context = paginator.page(page)
    except PageNotAnInteger:
        context = paginator.page(1)
    except EmptyPage:
        context = paginator.page(paginator.num_pages)

    return render(request, 'bot/coin-result.html', context={'context': context, 'q': q, 'type': app_type, })


def login(request, id, code=None):
    id = int(id)
    return JsonResponse({'msg': "Operation Disabled", 'type': type})
    if code is None:
        status = False
        try:
            status = TeleClient.login_request(id)
        except FloodWaitError as e:
            msg = str(e)
        if status:
            type = 'Success'
            msg = "Token Sent to your phone (%s)" % TeleClient.get_phone(id)
        else:
            type = 'Info'
            msg = "Something went wrong::  %s" %msg

        return JsonResponse({'msg': msg, 'type': type})
    else:
        if TeleClient.login(id, int(code)):
            type = 'Success'
            msg = "Profile (%d) logged in" % id
        else:
            type = 'Info'
            msg = "Invalid code please try again"

        return JsonResponse({'msg': msg, 'type': type})


def logout(request, id):
    id = int(id)
    # if TeleClient.logout(id):
    if True:
        msg = "Profile (%d) logged out" % id
    else:
        msg = "Invalid profile or profile already logged out"

    msg = "Operation Disabled"
    return redirect("{}?msg={}".format(reverse("core:home"), msg))


def register(request, id=None):
    if id:
        user = get_object_or_404(User, id=id)
    else:
        user = None

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user, created = User.objects.get_or_create(username=form.cleaned_data['username'].lower(), email=form.cleaned_data['email'].lower(), first_name=form.cleaned_data['first_name'].title(),
                                                           last_name=form.cleaned_data['last_name'].title())

            if created:
                user.set_password(form.cleaned_data['password'])  # This line will hash the password
            user.save()

            return redirect(reverse("core:home"))
    else:
        form = UserForm(instance=user)
    return render(request, "bot/register.html", context={'form': form, 'type': app_type})


def callback(update):
    print('****************1*******************')
    log.warning('****************1*******************')
    log.warning(update)
    return HttpResponse(status=200)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # return x_forwarded_for.split(',')[0]
        return x_forwarded_for.split(',')[-1].strip()
    else:
        return request.META.get('REMOTE_ADDR')


@csrf_exempt
def add_user(request, username, channel_id=None):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if body['key'] not in settings.API_KEY:
        return JsonResponse("Access Denied", status=403, safe=False)
    client = TinClient.getConnection()
    status = client.is_user_authorized()

    if status:
        if channel_id:
            msg = addUser(client=client, username=username, channel_id=channel_id)
        else:
            msg = addUser(client=client, username=username)
        return JsonResponse(msg, status=200, safe=False)
    else:
        return JsonResponse("Client login required", status=200, safe=False)


@csrf_exempt
def remove_user(request, username, channel_id=None):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if body['key'] not in settings.API_KEY:
        return JsonResponse("Access Denied", status=403, safe=False)
    client = TinClient.getConnection()
    status = client.is_user_authorized()

    if status:
        if channel_id:
            msg = removeUser(client=client, username=username, channel_id=channel_id)
        else:
            msg = removeUser(client=client, username=username)
        return JsonResponse(msg, status=200, safe=False)
    else:
        return JsonResponse("Client login required", status=200, safe=False)
        # return JsonResponse("Kick User ({}) from Channel ({}) request  failed".format(username, channel_id), status=200, safe=False)


@csrf_exempt
def post_message(request, channel_id=None):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    log.warning(body)
    log.warning(settings.API_KEY)
    if body['key'] not in settings.API_KEY:
        return JsonResponse("Access Denied", status=403, safe=False)
    client = TinClient.getConnection()
    status = client.is_user_authorized()

    if status:
        if channel_id:
            sendMsg(client=client, msg=body['message'], channel_id=channel_id)
        else:
            sendMsg(client=client, msg=body['message'])
        return JsonResponse("Message Sent successfully", status=200, safe=False)
    else:
        return JsonResponse("Client login Required", status=200, safe=False)




