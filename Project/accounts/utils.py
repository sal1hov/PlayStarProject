from django.conf import settings
from datetime import datetime, timedelta
import random
import string

def generate_telegram_code(length=6):
    """Генерация цифрового кода для Telegram"""
    return ''.join(random.choice(string.digits) for _ in range(length))

def get_code_expiration():
    """Получение времени истечения срока действия кода"""
    return datetime.now() + timedelta(minutes=getattr(settings, 'TELEGRAM_CODE_EXPIRE_MINUTES', 5))