from django.urls import path
from .views import (
    profile,  # Добавляем импорт profile
    profile_edit,
    add_child,
    delete_child,
    change_password,
    change_email
)

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/add_child/', add_child, name='add_child'),
    path('profile/delete_child/<int:child_id>/', delete_child, name='delete_child'),
    path('change-password/', change_password, name='change_password'),  # Используем кастомное представление
    path('change-email/', change_email, name='change_email'),
]
