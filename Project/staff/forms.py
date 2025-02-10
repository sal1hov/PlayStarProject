# staff/forms.py
from django import forms
from django.contrib.auth.models import User
from main.models import Profile, Child
from .models import SiteSettings

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
