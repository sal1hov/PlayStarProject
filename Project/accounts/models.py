from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    def __str__(self):
        return f"Профиль {self.user.username}"

class Child(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='children')
    child_name = models.CharField(max_length=100, verbose_name="Имя ребенка")
    child_age = models.PositiveIntegerField(verbose_name="Возраст ребенка")

    def __str__(self):
        return f"{self.name} ({self.age} лет)"