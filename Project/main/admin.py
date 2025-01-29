# main/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal data', {'fields': ('first_name', 'last_name', 'email', 'role')}),
        ('Access rights', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
