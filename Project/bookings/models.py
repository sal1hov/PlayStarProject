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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=255)
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
        if self.prepayment and self.paid_amount < 0:
            raise ValidationError("Доплата не может быть отрицательной при активной предоплате")

    def save(self, *args, **kwargs):
        if self.prepayment and self.paid_amount < 0:
            raise ValidationError("Доплата не может быть отрицательной")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_name} - {self.event_date}"

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'