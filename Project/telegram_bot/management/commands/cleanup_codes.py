from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import SocialAccount
from datetime import timedelta


class Command(BaseCommand):
    help = 'Cleans up expired Telegram verification codes'

    def handle(self, *args, **options):
        try:
            expired_time = timezone.now() - timedelta(minutes=5)
            count, _ = SocialAccount.objects.filter(
                provider='telegram_pending',
                user__isnull=True,
                extra_data__expires_at__lt=expired_time.isoformat()
            ).delete()

            self.stdout.write(self.style.SUCCESS(f"Удалено {count} просроченных кодов"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при очистке кодов: {str(e)}"))