from django.contrib import admin
from .models import StaffProfile

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone_number')

    def has_change_permission(self, request, obj=None):
        # Разрешаем изменять роли только superuser и администраторам (admin)
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'staffprofile') and request.user.staffprofile.role == 'admin':
            return True
        return False

    def has_add_permission(self, request):
        # Разрешаем добавление только администраторам и суперпользователям
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'staffprofile') and request.user.staffprofile.role == 'admin':
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        # Разрешаем удаление только администраторам и суперпользователям
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'staffprofile') and request.user.staffprofile.role == 'admin':
            return True
        return False
