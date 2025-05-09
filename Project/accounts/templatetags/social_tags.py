from django import template
from social_django.models import UserSocialAuth
from accounts.models import SocialAccount

register = template.Library()

@register.filter
def get_social_account(user, provider):
    if provider == 'telegram':
        return SocialAccount.objects.filter(user=user, provider=provider).first()
    return UserSocialAuth.objects.filter(user=user, provider=provider).first()

@register.filter
def has_social_account(user, provider):
    if provider == 'telegram':
        return SocialAccount.objects.filter(user=user, provider=provider).exists()
    return UserSocialAuth.objects.filter(user=user, provider=provider).exists()