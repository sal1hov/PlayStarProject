from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Booking


class BookingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.enforce_future_date = kwargs.pop('enforce_future_date', True)
        exclude_status = kwargs.pop('exclude_status', False)
        super().__init__(*args, **kwargs)

        if exclude_status:
            del self.fields['status']

    class Meta:
        model = Booking
        fields = ['event_name', 'event_date', 'status']  # Убедитесь, что здесь только существующие поля

        widgets = {
            'event_name': forms.TextInput(attrs={
                'class': 'w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'event_date': forms.DateTimeInput(attrs={
                'class': 'w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.instance._state.adding:
            cleaned_data['booking_type'] = 'online'
        return cleaned_data

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and self.enforce_future_date and event_date < timezone.now():
            raise ValidationError("Дата мероприятия не может быть в прошлом!")
        return event_date