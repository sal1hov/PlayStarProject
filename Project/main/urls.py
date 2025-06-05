# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.events_list, name='events_list'),
    path('prices/', views.prices_view, name='prices'),
]
