import logging
import random
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from django.conf import settings
from asgiref.sync import sync_to_async
from accounts.models import SocialAccount
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user:
            raise ValueError("User not found in update")

        # Генерация 6-значного кода
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=5)

        # Удаляем старые pending-записи для этого пользователя
        await sync_to_async(SocialAccount.objects.filter(
            provider='telegram_pending',
            uid=f"temp_{user.id}"
        ).delete)()

        # Создаем новую запись
        account = await sync_to_async(SocialAccount.objects.create)(
            provider='telegram_pending',
            uid=f"temp_{user.id}",
            user=None,  # Явно указываем NULL
            extra_data={
                'code': code,
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'expires_at': expires_at.isoformat()
            }
        )

        await update.message.reply_text(
            f"🔐 Ваш код подтверждения: <b>{code}</b>\n\n"
            "Введите этот код на сайте PlayStar для привязки аккаунта.\n"
            "Код действителен 5 минут.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при генерации кода. Пожалуйста, попробуйте позже."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка в боте: {context.error}", exc_info=True)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )

def setup_bot():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error_handler)
    return application