from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    child_name = models.CharField(max_length=100, blank=True, null=True)  # Поле для имени ребенка
    child_age = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.username