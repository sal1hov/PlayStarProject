from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['booking_type', 'event_date', 'children_count', 'comment', 'location', 'custom_type']
        widgets = {
            'event_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'min': timezone.now().strftime('%Y-%m-%dT%H:%M')}
            ),
            'children_count': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        enforce_future_date = kwargs.pop('enforce_future_date', True)
        super().__init__(*args, **kwargs)
        self.enforce_future_date = enforce_future_date

    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get('booking_type')
        children_count = cleaned_data.get('children_count')

        if booking_type == 'birthday' and children_count > 25:
            self.add_error('children_count', 'Максимум 25 детей для Дня рождения')

        if booking_type == 'vr' and children_count > 10:
            self.add_error('children_count', 'Максимум 10 участников для VR-арены')

        if booking_type == 'animation' and not cleaned_data.get('location'):
            self.add_error('location', 'Укажите адрес для выездной анимации')

        if booking_type == 'other' and not cleaned_data.get('custom_type'):
            self.add_error('custom_type', 'Укажите тип мероприятия')

        return cleaned_data