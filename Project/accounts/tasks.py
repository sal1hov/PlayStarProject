from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_codes():
    try:
        call_command('cleanup_codes')
    except Exception as e:
        logger.error(f"Ошибка при очистке кодов: {str(e)}", exc_info=True)
        raise