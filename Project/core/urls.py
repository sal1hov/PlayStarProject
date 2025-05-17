from django.contrib import admin
from django.urls import path, include
from main.views import index, register, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bookings/', include(('bookings.urls', 'bookings'), namespace='bookings')),
    path('staff/', include('staff.urls', namespace='staff')),
    path('profile/', profile_view, name='profile'),
    path('', include('main.urls')),
]