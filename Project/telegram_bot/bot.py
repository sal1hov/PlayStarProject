import logging
import random
from datetime import timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from django.conf import settings
from asgiref.sync import sync_to_async
from accounts.models import SocialAccount
from django.utils import timezone

logger = logging.getLogger(__name__)


def run_bot():
    """Функция для прямого запуска бота"""
    application = setup_bot()
    application.run_polling()


if __name__ == '__main__':
    run_bot()


def check_settings():
    required_settings = ['TELEGRAM_BOT_TOKEN']
    for setting in required_settings:
        if not getattr(settings, setting, None):
            raise ValueError(f"Необходимо указать {setting} в настройках Django")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        await update.message.reply_text(
            "👋 Привет! Я бот для авторизации в PlayStar.\n\n"
            "Доступные команды:\n"
            "/login - Вход в систему\n"
            "/bind - Привязка Telegram к аккаунту"
        )
        logger.info(f"Пользователь {user.id} вызвал команду /start")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        logger.info(f"Пользователь {user.id} запросил код для входа")

        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        await sync_to_async(
            SocialAccount.objects.filter(
                provider='telegram_pending',
                uid=f"telegram_{user.id}"
            ).delete,
            thread_sensitive=True
        )()

        await sync_to_async(SocialAccount.create_pending_telegram_account, thread_sensitive=True)(
            telegram_id=user.id,
            code=code,
            purpose='login'
        )

        await update.message.reply_text(
            f"🔐 Ваш код для входа: <b>{code}</b>\n\n"
            f"⏳ Действителен до: {(timezone.now() + timedelta(minutes=5)).strftime('%H:%M')}\n\n"
            "Введите этот код в форме входа на сайте.\n\n"
            "⚠️ Никому не сообщайте этот код!",
            parse_mode='HTML'
        )
        logger.info(f"Для пользователя {user.id} сгенерирован код входа")
    except Exception as e:
        logger.error(f"Error in login command: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при генерации кода. Попробуйте позже.")


async def bind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        logger.info(f"Пользователь {user.id} запросил код для привязки")

        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=5)

        await sync_to_async(
            SocialAccount.objects.filter(
                provider='telegram_pending',
                uid=f"telegram_{user.id}"
            ).delete,
            thread_sensitive=True
        )()

        await sync_to_async(SocialAccount.objects.create, thread_sensitive=True)(
            provider='telegram_pending',
            uid=f"telegram_{user.id}",
            extra_data={
                'code': code,
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'expires_at': expires_at.isoformat(),
                'purpose': 'bind'
            }
        )

        await update.message.reply_text(
            f"🔐 Код для привязки: <b>{code}</b>\n\n"
            f"⏳ Действителен до: {expires_at.strftime('%H:%M')}\n\n"
            "Введите этот код в настройках профиля на сайте.",
            parse_mode='HTML'
        )
        logger.info(f"Для пользователя {user.id} сгенерирован код привязки")
    except Exception as e:
        logger.error(f"Error in bind command: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при генерации кода. Попробуйте позже.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Bot error: {context.error}", exc_info=True)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )


def setup_bot():
    check_settings()

    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("bind", bind_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    application.add_error_handler(error_handler)

    return application