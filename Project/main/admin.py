from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser  # Импортируйте вашу кастомную модель

# Регистрируем кастомную модель пользователя
admin.site.register(CustomUser, UserAdmin)