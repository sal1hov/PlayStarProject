from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+7\d{10}$',
                message="Номер телефона должен быть в формате +7XXXXXXXXXX."
            )
        ]
    )
    child_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username