from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На модерации'),
        ('approved', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('completed', 'Завершено')
    ]

    BOOKING_TYPES = (
        ('birthday', 'День рождения'),
        ('vr', 'VR-арена'),
        ('animation', 'Выездная анимация'),
        ('other', 'Другое'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_name = models.CharField('Название мероприятия', max_length=255)
    booking_type = models.CharField(
        'Тип бронирования',
        max_length=20,
        choices=BOOKING_TYPES,
        default='birthday'
    )
    location = models.CharField(
        'Местоположение',
        max_length=255,
        blank=True,
        null=True
    )
    custom_type = models.CharField(
        'Свой вариант',
        max_length=255,
        blank=True,
        null=True
    )
    event_date = models.DateTimeField('Дата мероприятия')
    children_count = models.PositiveIntegerField(
        'Количество детей',
        validators=[MinValueValidator(1)]
    )
    comment = models.TextField('Комментарий', blank=True, null=True)
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    prepayment = models.DecimalField(
        'Предоплата',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    cashier_payment = models.DecimalField(
        'Оплата кассиром',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    paid_amount = models.DecimalField(
        'Оплаченная сумма',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    @property
    def total_payment(self):
        return self.prepayment + self.cashier_payment + self.paid_amount

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_name} ({self.event_date.strftime('%d.%m.%Y')})"

    def save(self, *args, **kwargs):
        if not self.event_name:
            if self.booking_type == 'other' and self.custom_type:
                self.event_name = self.custom_type
            else:
                self.event_name = self.get_booking_type_display()
        super().save(*args, **kwargs)

    def clean(self):
        if self.booking_type == 'animation' and not self.location:
            raise ValidationError({'location': 'Для выездной анимации укажите адрес'})
        if self.booking_type == 'other' and not self.custom_type:
            raise ValidationError({'custom_type': 'Укажите тип мероприятия'})