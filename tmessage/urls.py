"""tmessage URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls import url, include


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^account/', include('account.urls')),

    # url(r'^processing/', include('permabots.urls_processing', namespace="permabots")),
    #
    # url(r'^rest-auth/', include('rest_auth.urls')),
    # url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),


    url(r'^', include('bot.urls')),
]


if 'django_telegrambot' in settings.INSTALLED_APPS:
    urlpatterns.append(url(r'^', include('django_telegrambot.urls')),)


if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if 'rest_framework.authtoken' in settings.INSTALLED_APPS:
    from account.view import get_token
    urlpatterns.append(url(r'^api/account/token/$', get_token, name='token'))


admin.site.site_header = "Telegram Bot/Client Administration"
admin.site.site_title = "Telegram Bot/Client"