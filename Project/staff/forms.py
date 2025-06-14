from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from main.models import Profile, Child, CustomUser
from .models import SiteSettings, Event, Shift, ShiftRequest
from bookings.models import Booking

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number']


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'birthdate', 'gender']


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['site_title', 'meta_description', 'meta_keywords', 'google_analytics']


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'image', 'event_type', 'moderation_status', 'max_participants']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-lg',
                'placeholder': 'Название мероприятия'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded-lg',
                'placeholder': 'Описание мероприятия',
                'rows': 4
            }),
            'date': forms.DateTimeInput(
                attrs={
                    'class': 'w-full p-2 border rounded-lg',
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'event_type': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'moderation_status': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'max_participants': forms.NumberInput(attrs={
                'class': 'w-full p-2 border rounded-lg',
                'placeholder': 'Максимальное количество участников'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['date'].initial = self.instance.date.strftime('%Y-%m-%dT%H:%M')


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['paid_amount', 'status']
        labels = {
            'paid_amount': 'Сумма оплаты',
            'status': 'Статус'
        }


class ShiftRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftRequest
        fields = ['date', 'start_time', 'end_time', 'role', 'comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Необязательный комментарий'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.professional_role != 'none':
            self.fields['role'].initial = self.user.professional_role

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if date and date < timezone.now().date():
            raise forms.ValidationError("Нельзя создавать смены на прошедшие даты")

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Время окончания смены должно быть позже времени начала")

        today = timezone.now().date()
        if today.weekday() not in [5, 6]:
            raise forms.ValidationError("Заявки на смены можно подавать только в субботу и воскресенье")

        return cleaned_data


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['date', 'role', 'shift_type', 'staff']
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'shift_type': forms.Select(attrs={'class': 'form-control'}),
            'staff': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ограничиваем список сотрудников
        self.fields['staff'].queryset = CustomUser.objects.filter(
            role__in=['STAFF', 'MANAGER', 'ADMIN']
        )

        # Отключаем поле max_staff, оно удалено из формы

        # Зафиксировать поля "role" и "shift_type" под текущие значения
        instance = kwargs.get('instance')
        if instance:
            role_display = instance.get_role_display()
            self.fields['role'].choices = [(instance.role, role_display)]
            self.fields['shift_type'].choices = [
                (instance.shift_type, instance.get_shift_type_display())
            ]
            self.fields['role'].widget.attrs['readonly'] = True
            self.fields['shift_type'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        shift_type = cleaned_data.get('shift_type')

        valid_combinations = {
            'animator': ['full', 'morning', 'evening'],
            'additional': ['full', 'additional_evening'],
            'vr_operator': ['full', 'vr_evening'],
            'cashier': ['full']
        }

        if role and shift_type:
            if shift_type not in valid_combinations.get(role, []):
                raise ValidationError(
                    f"Недопустимый тип смены для роли {dict(Shift.ROLE_CHOICES).get(role)}"
                )

        return cleaned_data
