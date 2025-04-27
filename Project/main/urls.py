from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.events_list, name='events_list'),
]