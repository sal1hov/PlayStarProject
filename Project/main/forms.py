from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import CustomUser

class RegisterForm(UserCreationForm):
    # Валидация имени, фамилии и имени ребёнка (только буквы и пробелы)
    name_validator = RegexValidator(
        regex=r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$',
        message="Используйте только буквы, пробелы и дефисы."
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Имя",
        validators=[name_validator],
        help_text="Минимум 2 символа, только буквы и пробелы."
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Фамилия",
        validators=[name_validator],
        help_text="Минимум 2 символа, только буквы и пробелы."
    )
    child_name = forms.CharField(
        max_length=100,
        required=True,
        label="Имя ребёнка",
        validators=[name_validator],
        help_text="Минимум 2 символа, только буквы и пробелы."
    )
    child_age = forms.IntegerField(
        required=True,
        label="Возраст ребёнка",
        min_value=0,
        max_value=18,
        help_text="Возраст должен быть от 0 до 18 лет."
    )

    # Валидация номера телефона (только цифры, формат +7XXXXXXXXXX)
    phone_validator = RegexValidator(
        regex=r'^\+7\d{10}$',
        message="Номер телефона должен быть в формате +7XXXXXXXXXX (11 цифр)."
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label="Номер телефона",
        validators=[phone_validator],
        help_text="Формат: +7XXXXXXXXXX (11 цифр)."
    )

    privacy_policy = forms.BooleanField(
        required=True,
        label="Я согласен на обработку персональных данных"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'child_name', 'child_age', 'phone_number', 'password1', 'password2', 'privacy_policy']

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if len(first_name.strip()) < 2:
            raise forms.ValidationError("Имя должно содержать минимум 2 символа.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if len(last_name.strip()) < 2:
            raise forms.ValidationError("Фамилия должна содержать минимум 2 символа.")
        return last_name

    def clean_child_name(self):
        child_name = self.cleaned_data.get('child_name')
        if len(child_name.strip()) < 2:
            raise forms.ValidationError("Имя ребенка должно содержать минимум 2 символа.")
        return child_name