from django import forms
from django.contrib.auth import get_user_model
from main.models import Profile, Child  # Импортируем модели из main

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number']  # Убрали child_name
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone_number': 'Номер телефона',
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = []  # Поле bio удалено

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'age']  # Исправлено на name и age (как в модели Child из main/models.py)
        labels = {
            'name': 'Имя ребенка',  # Исправлено на name
            'age': 'Возраст ребенка',  # Исправлено на age
        }