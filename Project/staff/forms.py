from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Profile, Child
from .models import SiteSettings, Event, Shift, ShiftRequest
from bookings.models import Booking

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

# Форма для создания и редактирования мероприятий
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
        # Если редактируем существующее событие, форматируем дату для input datetime-local
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['date'].initial = self.instance.date.strftime('%Y-%m-%dT%H:%M')

# Форма для управления доходами
class IncomeForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['paid_amount', 'status']  # Удалено event_name
        labels = {
            'paid_amount': 'Сумма оплаты',
            'status': 'Статус'
        }


class ShiftRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftRequest
        fields = ['shift', 'comment']
        widgets = {
            'shift': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Необязательный комментарий'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем смены: только будущие
        self.fields['shift'].queryset = Shift.objects.filter(
            date__gte=timezone.now().date()
        ).order_by('date')  # Убрана сортировка по start_time