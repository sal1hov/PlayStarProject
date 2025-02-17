from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from main.models import Profile, Child  # Импортируем модели из main

User = get_user_model()

# Валидатор для имени и фамилии: допускаются только буквы (английские и русские)
name_validator = RegexValidator(
    regex=r'^[A-Za-zА-Яа-яЁё]+$',
    message='Поле может содержать только буквы.'
)

# Валидатор для номера телефона: допускается цифры и опционально символ "+" в начале
phone_validator = RegexValidator(
    regex=r'^\+?\d+$',
    message='Номер телефона может содержать только цифры и символ "+" в начале.'
)

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя',
        validators=[name_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-zА-Яа-яЁё]+',
            'title': 'Поле может содержать только буквы.'
        })
    )
    last_name = forms.CharField(
        label='Фамилия',
        validators=[name_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-zА-Яа-яЁё]+',
            'title': 'Поле может содержать только буквы.'
        })
    )
    phone_number = forms.CharField(
        label='Номер телефона',
        validators=[phone_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': r'^\+?\d+$',
            'title': 'Номер телефона может содержать только цифры и символ "+" в начале.'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number']
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
    name = forms.CharField(
        label='Имя ребенка',
        validators=[name_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-zА-Яа-яЁё]+',
            'title': 'Поле может содержать только буквы.'
        })
    )

    class Meta:
        model = Child
        fields = ['name', 'age']
        labels = {
            'name': 'Имя ребенка',
            'age': 'Возраст ребенка',
        }
