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

    BOOKING_SOURCE = (
        ('online', 'Онлайн'),
        ('offline', 'Оффлайн'),
    )

    booking_source = models.CharField(
        'Источник бронирования',
        max_length=20,
        choices=[('website', 'Сайт'), ('telegram', 'Телеграм')],
        default='website'
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    booking_date = models.DateTimeField(auto_now_add=True)
    event_date = models.DateTimeField()
    children_count = models.PositiveIntegerField(
        'Количество детей',
        default=1,
        validators=[MinValueValidator(1)]
    )
    comment = models.TextField('Комментарий', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    prepayment = models.BooleanField(default=False)
    prepayment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1000.00'),
        editable=False
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )

    @property
    def total_payment(self):
        return self.prepayment_amount + self.paid_amount if self.prepayment else self.paid_amount

    def clean(self):
        super().clean()
        if self.booking_type == 'birthday' and self.children_count > 25:
            raise ValidationError({'children_count': 'Для Дня рождения максимальное количество детей - 25'})

        if self.booking_type == 'vr' and self.children_count > 10:
            raise ValidationError({'children_count': 'Для VR-арены максимальное количество участников - 10'})

        if self.booking_type == 'animation' and not self.location:
            raise ValidationError({'location': 'Для выездной анимации необходимо указать адрес'})

        if self.booking_type == 'other' and not self.custom_type:
            raise ValidationError({'custom_type': 'Укажите тип мероприятия для варианта "Другое"'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_booking_type_display()} - {self.event_date}"

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'