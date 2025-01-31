from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from .models import CustomUser, Child, Profile

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
    child_age = forms.IntegerField(
        required=True,
        label="Возраст ребёнка",
        validators=[MinValueValidator(0), MaxValueValidator(18)]  # Возраст от 0 до 18 лет
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
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'child_name', 'child_age', 'phone_number', 'password1', 'password2', 'privacy_policy']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'CLIENT'  # Устанавливаем роль по умолчанию
        if commit:
            user.save()
            # Проверяем, существует ли профиль для пользователя
            profile, created = Profile.objects.get_or_create(user=user)
            # Создаем ребенка, если профиль был создан или уже существует
            Child.objects.create(
                profile=profile,
                name=self.cleaned_data['child_name'],
                age=self.cleaned_data['child_age']
            )
        return user