from django.db import models
from django.contrib.auth import get_user_model
from main.models import CustomUser  # Импортируем CustomUser

class StaffProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.username} - {self.position}'

class SiteSettings(models.Model):
    site_title = models.CharField(max_length=255, verbose_name="Заголовок сайта")
    meta_description = models.TextField(blank=True, null=True, verbose_name="Мета описание")
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ключевые слова")
    google_analytics = models.TextField(blank=True, null=True, verbose_name="Код Google Analytics")

    def __str__(self):
        return "Настройки сайта"

    class Meta:
        verbose_name = "Настройка сайта"
        verbose_name_plural = "Настройки сайта"

class Notification(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)  # Используем get_user_model()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Флаг для отображения прочитано ли уведомление

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}..."

class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='events/', null=True, blank=True)

    def __str__(self):
        return self.name