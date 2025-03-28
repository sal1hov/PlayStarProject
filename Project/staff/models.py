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

# Константы для выбора типа и статуса модерации
EVENT_TYPES = (
    ('выездные анимации', 'Выездные анимации'),
    ('открытые анимации', 'Открытые анимации'),
    ('панорамик', 'Панорамик'),
    ('другое', 'Другое'),
)

MODERATION_STATUS = (
    ('approved', 'Принято'),
    ('rejected', 'Отказано'),
    ('unavailable', 'Недоступно'),
    ('pending', 'На модерации'),
)


class Event(models.Model):
    LOCATION_CHOICES = [
        ('main', 'Основная площадка'),
        ('secondary', 'Дополнительная площадка')
    ]

    # Существующие поля
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(
        max_length=100,
        choices=LOCATION_CHOICES,
        default='main'  # Важно!
    )
    event_type = models.CharField(max_length=50)
    moderation_status = models.CharField(max_length=20, default='pending')
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Добавьте эти поля
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    max_participants = models.PositiveIntegerField(
        default=10,  # Добавляем значение по умолчанию
        verbose_name='Максимальное количество участников')

    def __str__(self):
        return self.name