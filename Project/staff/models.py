# staff/models.py
from django.db import models
from django.contrib.auth import get_user_model

class StaffProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.username} - {self.position}'
