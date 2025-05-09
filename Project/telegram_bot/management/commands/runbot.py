from django.core.management.base import BaseCommand
from telegram_bot.bot import setup_bot
import asyncio


class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))

        application = setup_bot()

        async def run():
            await application.initialize()
            await application.start()
            await application.updater.start_polling()

            # Бесконечный цикл для поддержания работы бота
            while True:
                await asyncio.sleep(1)

        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Stopping bot...'))
            asyncio.run(application.stop())