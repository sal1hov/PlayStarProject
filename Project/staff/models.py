from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group

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

    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    date = models.DateTimeField(verbose_name="Дата и время")
    location = models.CharField(
        max_length=100,
        choices=LOCATION_CHOICES,
        default='main',
        verbose_name="Место проведения"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        verbose_name="Тип мероприятия"
    )
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending',
        verbose_name="Статус модерации"
    )
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Бронирование"
    )
    image = models.ImageField(
        upload_to='events/',
        null=True,
        blank=True,
        verbose_name="Изображение"
    )
    max_participants = models.PositiveIntegerField(
        default=10,
        verbose_name='Максимальное количество участников'
    )

    def __str__(self):
        return self.name

    def get_event_type_display(self):
        """Возвращает читаемое название типа мероприятия"""
        return dict(EVENT_TYPES).get(self.event_type, self.event_type)

    def get_moderation_status_display(self):
        """Возвращает читаемое название статуса модерации"""
        return dict(MODERATION_STATUS).get(self.moderation_status, self.moderation_status)

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ['date']  # Сортировка по дате (от ближайших к дальним)


class Shift(models.Model):
    SHIFT_TYPES = (
        ('morning', 'Утро (9:00-15:00)'),
        ('afternoon', 'День (15:00-21:00)'),
        ('night', 'Ночь (21:00-9:00)'),
        ('full', 'Полный день (9:00-21:00)'),
    )

    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES)
    date = models.DateField()
    max_staff = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.get_shift_type_display()} - {self.date.strftime('%d.%m.%Y')}"


class ShiftRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Утверждено'),
        ('rejected', 'Отклонено'),
        ('modified', 'Изменено администратором'),
    )

    employee = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='shift_requests')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_comment = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'shift')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.username} - {self.shift} ({self.get_status_display()})"

    def get_details(self):
        return {
            'employee': self.employee.get_full_name(),
            'shift_type': self.shift.get_shift_type_display(),
            'date': self.shift.date.strftime("%d.%m.%Y"),
            'status': self.get_status_display(),
            'created_at': self.created_at.strftime("%d.%m.%Y %H:%M"),
            'admin_comment': self.admin_comment or 'Нет комментария'
        }

@receiver(post_migrate)
def verify_groups_exist(sender, **kwargs):
    """Проверяет существование необходимых групп (выводит предупреждение если нет)"""
    required_groups = ['Admin', 'Manager', 'Staff']
    for group_name in required_groups:
        if not Group.objects.filter(name=group_name).exists():
            print(f'Внимание: требуемая группа "{group_name}" не найдена! Создайте её в админке.')