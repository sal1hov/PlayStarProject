from django import forms
from django.contrib.auth import get_user_model
from .models import Profile, Child

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
        fields = ['child_name', 'child_age']
        labels = {
            'name': 'Имя ребенка',
            'age': 'Возраст ребенка',
        }