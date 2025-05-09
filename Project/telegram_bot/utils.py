from django.utils import timezone
from datetime import timedelta
import secrets
import string

def generate_telegram_code():
    """Генерация 6-значного кода"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def get_code_expiration():
    """Получение времени истечения кода (текущее время + 5 минут)"""
    return timezone.now() + timedelta(minutes=5)