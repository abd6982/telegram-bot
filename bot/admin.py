from django.contrib import admin

# Register your models here.
from bot.models import Message, Member, MessageTemplate

MAX_SHOW_ALL = 2000
PER_PAGE = 500


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('from_id', 'message_id', 'source_id', 'created', 'treated', 'text')
    search_fields = ['from_id', 'message_id', 'source_id', 'text', 'for_id']
    date_hierarchy = 'created'
    list_filter = ('treated',)
    list_max_show_all = MAX_SHOW_ALL
    list_per_page = PER_PAGE


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'first_name', 'last_name', 'username', 'group', 'type', 'is_bot', 'user', 'is_blacklisted', 'created')
    search_fields = ['member_id', 'first_name', 'last_name', 'username']
    date_hierarchy = 'created'
    list_filter = ('is_bot', 'is_blacklisted', 'group')
    list_max_show_all = MAX_SHOW_ALL
    list_per_page = PER_PAGE


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'text')
    search_fields = ['text']
    date_hierarchy = 'created'
    list_filter = ('type', )
    list_max_show_all = MAX_SHOW_ALL
    list_per_page = PER_PAGE
    readonly_fields = ('group',)

