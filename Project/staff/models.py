from django.db import models
from django.conf import settings  # Импортируем settings для использования AUTH_USER_MODEL

class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('employee', 'Сотрудник'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Используем AUTH_USER_MODEL
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_employee(self):
        return self.role == 'employee'

    def is_manager(self):
        return self.role == 'manager'

    def is_admin(self):
        return self.role == 'admin'


class Child(models.Model):
    name = models.CharField(max_length=100)
    birthdate = models.DateField()  # Add birthdate
    gender = models.CharField(max_length=10)  # Add gender