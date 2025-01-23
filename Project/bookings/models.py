from django.db import models
from users.models import User

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    service = models.CharField(max_length=100)

class Schedule(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    approved = models.BooleanField(default=False)

class Task(models.Model):
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    completed = models.BooleanField(default=False)