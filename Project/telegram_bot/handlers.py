from aiogram import types
from aiogram.dispatcher import FSMContext
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import SocialAccount
from django.conf import settings
from datetime import datetime
import json

User = get_user_model()


async def start_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Привет! Отправь мне код, который ты видишь в своем профиле, "
        "чтобы привязать Telegram аккаунт."
    )


async def auth_code_handler(message: types.Message, state: FSMContext):
    code = message.text.strip()

    # Здесь должна быть логика проверки кода в Django сессии
    # Это упрощенный пример - в реальном проекте нужно использовать Redis или БД

    try:
        # В реальном проекте нужно проверять код в БД или Redis
        # и находить соответствующего пользователя
        user = User.objects.get(profile__telegram_auth_code=code)

        # Создаем или обновляем социальный аккаунт
        social_account, created = SocialAccount.objects.update_or_create(
            provider='telegram',
            uid=str(message.from_user.id),
            defaults={
                'user': user,
                'extra_data': json.dumps({
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                })
            }
        )

        await message.answer(
            f"✅ Твой аккаунт успешно привязан к {user.username}!\n\n"
            f"Теперь ты можешь входить в систему через Telegram."
        )

        # Очищаем код (в реальном проекте нужно обновить в БД)
        user.profile.telegram_auth_code = None
        user.profile.save()

    except ObjectDoesNotExist:
        await message.answer(
            "❌ Неверный код или срок его действия истек. "
            "Попробуй сгенерировать новый код в своем профиле."
        )