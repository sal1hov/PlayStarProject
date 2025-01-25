from django.urls import path
from .views import profile, profile_edit, delete_child

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/delete_child/<int:child_id>/', delete_child, name='delete_child'),
]