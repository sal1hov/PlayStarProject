from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from staff.models import StaffProfile

class StaffProfileInline(admin.StackedInline):  # Встраиваем StaffProfile в профиль пользователя
    model = StaffProfile
    can_delete = False
    verbose_name_plural = 'Сотрудничество'

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'phone_number', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
