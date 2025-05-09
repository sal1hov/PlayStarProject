from django.core.management.base import BaseCommand
from telegram_bot.bot import setup_bot
import asyncio
import logging
import sys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запускает Telegram бота в режиме polling'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))

        try:
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            application = setup_bot()
            application.run_polling()

        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {str(e)}", exc_info=True)
            self.stderr.write(self.style.ERROR(f'Ошибка: {str(e)}'))