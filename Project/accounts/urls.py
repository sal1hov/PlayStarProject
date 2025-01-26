from django.urls import path
from .views import profile, profile_edit, delete_child, add_child, change_password

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/add_child/', add_child, name='add_child'),
    path('profile/delete_child/<int:child_id>/', delete_child, name='delete_child'),
    path('change-password/', change_password, name='change_password'),  # Используем кастомное представление
]