from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .models import CustomUser, Child

class RegisterForm(UserCreationForm):
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
        validators=[MinValueValidator(0), MaxValueValidator(18)]
    )

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

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'example@mail.ru'})
    )

    privacy_policy = forms.BooleanField(required=True, label="Я согласен на обработку персональных данных")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name',
                 'child_name', 'child_age', 'phone_number',
                 'password1', 'password2', 'privacy_policy']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'CLIENT'
        if commit:
            user.save()
            Child.objects.create(
                profile=user.profile,
                name=self.cleaned_data['child_name'],
                age=self.cleaned_data['child_age']
            )
        return user