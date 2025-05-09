from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from main.models import Child, Profile
from .models import SocialAccount

User = get_user_model()

name_validator = RegexValidator(
    regex=r'^[A-Za-zА-Яа-яЁё\s-]+$',
    message=_('Поле может содержать только буквы, пробелы и дефисы.')
)

phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message=_('Номер телефона может содержать только цифры и символ "+" в начале.')
)

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_('Имя'),
        validators=[name_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-zА-Яа-яЁё\\s-]+',
            'title': _('Только буквы, пробелы и дефисы'),
            'class': 'form-input'
        })
    )
    last_name = forms.CharField(
        label=_('Фамилия'),
        validators=[name_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-zА-Яа-яЁё\\s-]+',
            'title': _('Только буквы, пробелы и дефисы'),
            'class': 'form-input'
        })
    )
    username = forms.CharField(
        label=_('Имя пользователя'),
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    phone_number = forms.CharField(
        label=_('Номер телефона'),
        validators=[phone_validator],
        required=True,
        widget=forms.TextInput(attrs={
            'pattern': r'^\+?\d+$',
            'title': _('Только цифры и символ "+"'),
            'class': 'form-input'
        })
    )
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = self.instance.email

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = []

class ChildForm(forms.ModelForm):
    name = forms.CharField(
        label=_('Имя ребенка'),
        validators=[name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'pattern': '[A-Za-zА-Яа-яЁё\\s-]+'
        })
    )
    age = forms.IntegerField(
        label=_('Возраст'),
        min_value=0,
        max_value=18,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': '0',
            'max': '18'
        })
    )
    birthdate = forms.DateField(
        label=_('Дата рождения'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input'
        }),
        required=False
    )
    gender = forms.ChoiceField(
        label=_('Пол'),
        choices=Child.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    class Meta:
        model = Child
        fields = ['name', 'age', 'birthdate', 'gender']

class EmailChangeForm(forms.Form):
    current_password = forms.CharField(
        label=_('Текущий пароль'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'current-password'
        })
    )
    new_email = forms.EmailField(
        label=_('Новый email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'autocomplete': 'email'
        })
    )
    confirm_email = forms.EmailField(
        label=_('Подтвердите email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'autocomplete': 'email'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_email = cleaned_data.get('new_email')
        confirm_email = cleaned_data.get('confirm_email')
        current_password = cleaned_data.get('current_password')

        if new_email and confirm_email and new_email != confirm_email:
            raise ValidationError(_("Email адреса не совпадают"))

        if current_password and not self.user.check_password(current_password):
            raise ValidationError(_("Неверный текущий пароль"))

        if User.objects.filter(email=new_email).exclude(pk=self.user.pk).exists():
            raise ValidationError(_("Этот email уже используется другим пользователем"))

        return cleaned_data

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})

def clean_email(self):
    email = self.cleaned_data.get('email')
    if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
        raise ValidationError(_("Этот email уже используется другим пользователем"))
    return email

class SocialAccountDisconnectForm(forms.Form):
    account_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_account_id(self):
        account_id = self.cleaned_data['account_id']
        try:
            account = SocialAccount.objects.get(id=account_id, user=self.user)
            return account
        except SocialAccount.DoesNotExist:
            raise forms.ValidationError(_("Социальный аккаунт не найден"))