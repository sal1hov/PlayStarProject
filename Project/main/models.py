# main/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

# Кастомная модель пользователя
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('staff', 'Staff'), ('client', 'Client')], default='client', verbose_name="Роль")

    def __str__(self):
        return self.username

# Модель профиля, связанная с кастомным пользователем
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)  # Используйте CustomUser
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

# Модель для ребенка, связанная с профилем
class Child(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=100, verbose_name="Имя ребенка")
    age = models.PositiveIntegerField(verbose_name="Возраст ребенка")
    birthdate = models.DateField(verbose_name="Дата рождения", blank=True, null=True)  # Добавлено поле birthdate
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], verbose_name="Пол", blank=True, null=True)  # Добавлено поле gender

    def __str__(self):
        return f"{self.name} ({self.age} лет)"
