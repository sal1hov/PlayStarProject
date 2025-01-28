from django.db import models
from django.contrib.auth.models import User

class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('employee', 'Сотрудник'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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