from django.db import models
from django.conf import settings

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    event_name = models.CharField(max_length=255, verbose_name='Название мероприятия')
    booking_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата бронирования')
    event_date = models.DateTimeField(verbose_name='Дата мероприятия')
    status = models.CharField(max_length=50, blank=True, null=True, default='Активно', verbose_name='Статус')
    children_count = models.PositiveIntegerField(default=1, blank=True, null=True, verbose_name='Количество детей')
    comment = models.TextField(max_length=255, blank=True, null=True, verbose_name='Комментарий')
    edited_by = models.CharField(max_length=50, blank=True, null=True, verbose_name='Отредактировано')  # Новое поле

    def __str__(self):
        return f"{self.event_name} - {self.event_date}"

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'