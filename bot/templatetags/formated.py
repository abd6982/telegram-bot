from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def formate_account(obj):
    html = ""
    for o in obj:
        html += "<li>"+o+"</li>"
    return mark_safe("herrrr")