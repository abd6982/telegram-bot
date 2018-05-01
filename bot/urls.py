from django.conf.urls import url

from bot import views

app_name = 'core'

urlpatterns = [
    url(r'admin/telegram/client/$', views.home, name='client'),
    url(r'^$', views.index, name='index'),
    url(r'^index/$', views.index, name='index'),
    url(r'^home/$', views.home, name='home'),
    url(r'^start/$', views.init, name='init'),

    # url(r'^instaback/$', views.instagram, name='instaback'),

    url(r'^register/$', views.register, name='register'),
    url(r'^messages/$', views.messages, name='messages-list'),
    url(r'^messages/(?P<id>[\d]+)/$', views.messages, name='messages'),
    url(r'^processor/stop/(?P<id>[\d]+)/(?P<method_name>[\w\-]+)/$', views.processor_stop, name='processor-stop'),
    url(r'^processor/start/(?P<id>[\d]+)/(?P<method_name>[\w\-]+)/$', views.processor, name='processor-start'),

    url(r'^callbacks/$', views.callback, name='callback'),

    url(r'^bot/$', views.bot, name='bot-list'),
    url(r'^bot/rule/add/$', views.rule_add, name='bot-rule-add'),
    url(r'^bot/rule/detail/(?P<type>[\w]+)/$', views.rule_detail, name='bot-rule-detail'),

    url(r'^channel/member/add/(?P<username>[\w]+)/$', views.add_user, name='add-member'),
    url(r'^channel/member/add/(?P<username>[\w]+)/(?P<channel_id>[\d]+)/$', views.add_user, name='add-member'),
    url(r'^channel/member/kick/(?P<username>[\w]+)/$', views.remove_user, name='kick-member'),
    url(r'^channel/member/kick/(?P<username>[\w]+)/(?P<channel_id>[\d]+)/$', views.remove_user, name='kick-member'),
    url(r'^channel/message/post/$', views.post_message, name='post-message'),
    url(r'^channel/message/post/(?P<channel_id>[\d]+)/$', views.post_message, name='post-message'),

    url(r'^member/$', views.member, name='member-list'),
    # url(r'^member/blacklisted/(?P<gid>-?\d+)$', views.member_blacklisted, name='member-blacklist'),
    url(r'^member/blacklisted/(?P<gid>-?\d+)/True|False$', views.member_blacklisted, name='member-blacklist'),
    url(r'^t/defaulter/$', views.tdefaulter, name='t-defaulter-list'),
    url(r'^i/defaulter/$', views.idefaulter, name='i-defaulter-list'),
    url(r'^i/member/search/(?P<username>@?.*)$', views.i_member_blacklist, name='i-member-detail'),
    url(r'^i/member/blacklist/$', views.i_member_blacklist, name='i-member-blacklist'),
    url(r'^i/blacklist/$', views.member_blacklist, name='i-blacklisted'),
    url(r'^i/blacklist/(?P<id>-?\d+)$', views.member_blacklist, name='i-blacklist'),
    url(r'^i/whitelist/(?P<id>-?\d+)$', views.member_whitelist, name='i-whitelist'),

    url(r'^t/member/search/$', views.t_member_leech, name='t-member-detail'),
    url(r'^t/member/search/(?P<username>@?.*)$', views.t_member_leech, name='t-member-detail'),

    url(r'^leech/$', views.leech, name='leech-list'),
    url(r'^leech/add/(?P<member_id>[\d]+)/(?P<group_id>-?\d+)/$', views.leech_add, name='leech-add'),
    url(r'^leech/remove/(?P<member_id>[\d]+)/(?P<group_id>-?\d+)/$', views.leech_remove, name='leech-remove'),

    url(r'^group/$', views.group, name='group-list'),
    url(r'^group/(?P<id>[\w]+)/$', views.group, name='group-detail'),
    url(r'^group/(?P<id>-?\d+)/(?P<action>[enable|disable]+)/$', views.group, name='group-action'),
    url(r'^group/(?P<id>-?\d+)/(?P<action>[update]+)/$', views.group, name='group-edit'),

    url(r'^client/$', views.client, name='client-list'),
    url(r'^client/(?P<id>[\w]+)/$', views.client, name='client-details'),

    url(r'^client/login/request/(?P<id>[\d]+)/$', views.login, name='client-login-request'),
    url(r'^client/login/(?P<id>[\d]+)/(?P<code>[\d]+)/$', views.login, name='client-login'),
    url(r'^client/logout/(?P<id>[\d]+)/$', views.logout, name='client-logout'),

    url(r'^coin/data/$', views.coin_data, name='coin-data'),
    url(r'^coin/data/(?P<id>[\d]+)/$', views.coin_data, name='coin-data'),
    url(r'^coin/data/(?P<name>[\w]+)/$', views.coin_data, name='coin-data'),

    url(r'^coin/result/$', views.coin_result, name='coin-result'),
    url(r'^coin/result/(?P<id>[\d]+)/$', views.coin_result, name='coin-result'),
    url(r'^coin/result/(?P<name>[\w]+)/$', views.coin_result, name='coin-result'),

    url(r'^service/restart/$', views.restart_service, name='service-restart'),


]
