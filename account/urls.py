from django.conf.urls import url
from django.conf import settings
from django.contrib.auth import views as auth

# from . import views as local_view


app_name = "account"
urlpatterns = [

    # Session Login
    url(r'^login/$', auth.login, {'template_name': 'account/login.html'}, name="login"),
    # url(r'^login/$', auth.login, {'template_name': 'account/login.html', 'authentication_form': LoginForm}, name="login"),
    # url(r'^login/$', auth.login, name="login"),
    url(r'^logout/$', auth.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    # url(r'^password/change/$', auth.password_change, {'post_change_redirect': 'account:password_change_done'}, name='password_change'),
    # url(r'^password/change/done/$', auth.password_change_done, name='password_change_done'),
    # url(r'^password/reset/$', auth.password_reset, {'post_reset_redirect': 'account:password_reset_done', 'email_template_name': 'account/mail_templates/password_reset_email.html',
    #                                                    'html_email_template_name': 'account/mail_templates/password_reset_email_html.html'}, name='password_reset'),
    # url(r'^password/reset/done/$', auth.password_reset_done, name='password_reset_done'),
    # url(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth.password_reset_confirm, {'post_reset_redirect': 'account:password_reset_complete'},
    #     name='password_reset_confirm'),
    # url(r'^password/reset/complete/$', auth.password_reset_complete, name='password_reset_complete'),

]

if 'rest_framework.authtoken' in settings.INSTALLED_APPS:
    from rest_framework.authtoken import views as rest_framework_views
    from account.view import get_token
