from django.db import models
from django.conf import settings

STATUS_CHOICES = (
    ('active', 'На модерации'),
    ('approved', 'Подтверждено'),
    ('rejected', 'Отклонено'),
)

class Booking(models.Model):
    ONLINE = 'online'
    OFFLINE = 'offline'
    BOOKING_TYPES = [
        (ONLINE, 'Онлайн'),
        (OFFLINE, 'Оффлайн'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    event_name = models.CharField(max_length=255, verbose_name='Название мероприятия')
    booking_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата бронирования')
    event_date = models.DateTimeField(verbose_name='Дата мероприятия')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    children_count = models.PositiveIntegerField(default=1, blank=True, null=True, verbose_name='Количество детей')
    comment = models.TextField(max_length=255, blank=True, null=True, verbose_name='Комментарий')
    edited_by = models.CharField(max_length=50, blank=True, null=True, verbose_name='Отредактировано')
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPES, default=ONLINE, verbose_name='Тип бронирования')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Сумма')
    prepayment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Предоплата')  # Новое поле

    def __str__(self):
        return f"{self.event_name} - {self.event_date}"

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'