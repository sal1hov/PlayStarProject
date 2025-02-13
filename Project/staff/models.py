from django.db import models
from django.contrib.auth import get_user_model

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

# Новые константы для выбора типа и статуса модерации
EVENT_TYPES = (
    ('holiday', 'Праздник'),
    ('birthday', 'День рождения'),
    ('animators', 'Открытые анимации'),
    ('other', 'Другое'),
)

MODERATION_STATUS = (
    ('approved', 'Принято'),
    ('rejected', 'Отказано'),
    ('unavailable', 'Недоступно'),
    ('pending', 'На модерации'),
)

class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='other', verbose_name="Тип мероприятия")
    moderation_status = models.CharField(max_length=50, choices=MODERATION_STATUS, default='pending', verbose_name="Статус модерации")
    # Добавляем связь с бронированием (если событие создано по бронированию)
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Бронирование')

    def __str__(self):
        return self.name
