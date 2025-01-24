from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class RegisterForm(UserCreationForm):
    # Валидация имени, фамилии и имени ребёнка (только буквы и пробелы)
    name_validator = RegexValidator(
        regex=r'^[a-zA-Zа-яА-ЯёЁ\s]+$',
        message="Используйте только буквы и пробелы."
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Имя",
        validators=[name_validator]
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Фамилия",
        validators=[name_validator]
    )
    child_name = forms.CharField(
        max_length=100,
        required=True,
        label="Имя ребёнка",
        validators=[name_validator]
    )

    # Валидация номера телефона (только цифры)
    phone_validator = RegexValidator(
        regex=r'^\+7\d{10}$',
        message="Номер телефона должен быть в формате +7XXXXXXXXXX."
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label="Номер телефона",
        validators=[phone_validator]
    )

    privacy_policy = forms.BooleanField(required=True, label="Я согласен на обработку персональных данных")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'child_name', 'phone_number', 'password1', 'password2', 'privacy_policy']