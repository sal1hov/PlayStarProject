from django.contrib import admin
from .models import Booking, Schedule, Task

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'time', 'service')
    list_filter = ('date', 'service')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'start_time', 'end_time', 'approved')
    list_filter = ('date', 'approved')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('assigned_to', 'description', 'completed')
    list_filter = ('completed',)