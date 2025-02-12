# staff/forms.py
from django import forms
from django.contrib.auth.models import User
from main.models import Profile, Child
from .models import SiteSettings
from .models import Event, EVENT_TYPES, MODERATION_STATUS

# Форма для обновления данных пользователя
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

# Форма для обновления данных профиля
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number']

# Форма для добавления ребенка
class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'birthdate', 'gender']

# Форма для редактирования настроек сайта
class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['site_title', 'meta_description', 'meta_keywords', 'google_analytics']

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'location', 'image', 'event_type', 'moderation_status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Название мероприятия'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Описание мероприятия', 'rows': 4}),
            'date': forms.DateTimeInput(attrs={'class': 'w-full p-2 border rounded-lg', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Местоположение'}),
            'event_type': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'moderation_status': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg'}),
        }