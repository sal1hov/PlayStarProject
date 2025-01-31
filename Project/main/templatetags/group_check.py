# main/templatetags/group_check.py
from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    if isinstance(user, Group):
        return False
    if not hasattr(user, 'groups'):
        return False
    return user.groups.filter(name=group_name).exists()