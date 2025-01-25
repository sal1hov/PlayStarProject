from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    # Добавьте дополнительные поля профиля, если нужно
    # Например:
    # bio = models.TextField(blank=True, verbose_name="О себе")
    # avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")

    def __str__(self):
        return f"Профиль {self.user.username}"

class Child(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=100, verbose_name="Имя ребенка")
    age = models.PositiveIntegerField(verbose_name="Возраст ребенка")

    def __str__(self):
        return f"{self.name} ({self.age} лет)"