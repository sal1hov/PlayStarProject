from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Импортируем RedirectView
from core import views  # Импортируем представление

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('bookings/', include('bookings.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    # path('', RedirectView.as_view(url='/users/profile/')),  # Перенаправление на страницу профиля
    path('', views.home, name='home'),  # Домашняя страница
]