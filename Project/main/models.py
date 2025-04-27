# main/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Роли пользователей
    ROLE_CHOICES = [
        ('CLIENT', 'Клиент'),
        ('STAFF', 'Сотрудник'),
        ('MANAGER', 'Менеджер'),
        ('ADMIN', 'Администратор'),
    ]
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='CLIENT',  # По умолчанию роль "Клиент"
        verbose_name='Роль'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_staff_member(self):
        """Проверяет, является ли пользователь сотрудником (staff или выше)"""
        return self.role in ['STAFF', 'MANAGER', 'ADMIN']

    def is_manager_or_higher(self):
        """Проверяет, является ли пользователь менеджером или администратором"""
        return self.role in ['MANAGER', 'ADMIN']

# Модель профиля, связанная с кастомным пользователем
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)  # Используйте CustomUser
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