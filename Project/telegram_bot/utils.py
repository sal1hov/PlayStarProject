from django.conf import settings
from asgiref.sync import sync_to_async
from accounts.models import SocialAccount

@sync_to_async
def get_user_by_telegram_id(telegram_id):
    try:
        return SocialAccount.objects.get(provider='telegram', uid=str(telegram_id)).user
    except SocialAccount.DoesNotExist:
        return None