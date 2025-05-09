from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from main.models import CustomUser
import json
from django import forms

User = get_user_model()

class SocialAccount(models.Model):
    PROVIDER_CHOICES = [
        ('telegram', 'Telegram'),
        ('telegram_pending', 'Telegram (Pending)'),  # Добавлено для временных записей
        ('google', 'Google'),
        ('vk', 'VKontakte'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social_accounts',
        null=True,  # Разрешаем NULL для временных записей
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


class SocialAccountDisconnectForm(forms.Form):
    account_id = forms.IntegerField()

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_account_id(self):
        account_id = self.cleaned_data['account_id']
        try:
            return SocialAccount.objects.get(id=account_id, user=self.user)
        except SocialAccount.DoesNotExist:
            raise forms.ValidationError("Аккаунт не найден")