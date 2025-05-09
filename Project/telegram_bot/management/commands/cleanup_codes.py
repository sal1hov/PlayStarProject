from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import SocialAccount
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Удаляет просроченные коды подтверждения Telegram'

    def handle(self, *args, **options):
        try:
            expired_time = timezone.now() - timedelta(minutes=10)  # Удаляем коды, просроченные более 10 минут назад
            deleted_count, _ = SocialAccount.objects.filter(
                provider='telegram_pending',
                extra_data__expires_at__lt=expired_time.isoformat()
            ).delete()

            logger.info(f"Удалено {deleted_count} просроченных кодов Telegram")
            self.stdout.write(self.style.SUCCESS(f'Удалено {deleted_count} просроченных кодов'))
        except Exception as e:
            logger.error(f"Ошибка при очистке кодов: {str(e)}", exc_info=True)
            self.stderr.write(self.style.ERROR(f'Ошибка: {str(e)}'))