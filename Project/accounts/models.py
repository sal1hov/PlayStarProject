from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SocialAccount(models.Model):
    PROVIDER_CHOICES = [
        ('telegram', 'Telegram'),
        ('telegram_pending', 'Telegram (Pending)'),
        ('google', 'Google'),
        ('vk', 'VKontakte'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social_accounts',
        null=True,
        blank=True
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    uid = models.CharField(max_length=191)
    extra_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('provider', 'uid')
        verbose_name = 'Социальный аккаунт'
        verbose_name_plural = 'Социальные аккаунты'

    def __str__(self):
        username = self.user.username if self.user else 'temp'
        return f"{username} - {self.get_provider_display()}"

    @property
    def is_telegram(self):
        return self.provider == 'telegram'

    def get_telegram_username(self):
        return self.extra_data.get('username', '') if self.is_telegram else ''

    @classmethod
    def create_pending_telegram_account(cls, telegram_id, code, purpose='login', user=None):
        """Создает временную запись для входа/привязки Telegram"""
        return cls.objects.create(
            provider='telegram_pending',
            uid=f"telegram_{telegram_id}",
            user=user,
            extra_data={
                'code': code,
                'telegram_id': telegram_id,
                'expires_at': (timezone.now() + timedelta(minutes=5)).isoformat(),
                'purpose': purpose
            }
        )