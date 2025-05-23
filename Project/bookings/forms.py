from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['booking_type', 'event_date', 'children_count', 'comment', 'location', 'custom_type']
        widgets = {
            'booking_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_booking_type'
            }),
            'event_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'id': 'id_event_date'
            }),
            'children_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'id': 'id_children_count'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'id': 'id_comment'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_location'
            }),
            'custom_type': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_custom_type'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.enforce_future_date = kwargs.pop('enforce_future_date', True)
        super().__init__(*args, **kwargs)

        # Установка минимальной даты
        self.fields['event_date'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

        # Настройка обязательных полей
        self.fields['custom_type'].required = False
        self.fields['location'].required = False

    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get('booking_type')
        event_date = cleaned_data.get('event_date')
        children_count = cleaned_data.get('children_count')
        location = cleaned_data.get('location')
        custom_type = cleaned_data.get('custom_type')

        # Валидация даты
        if self.enforce_future_date and event_date and event_date < timezone.now():
            self.add_error('event_date', 'Дата мероприятия не может быть в прошлом')

        # Валидация количества детей
        if booking_type == 'birthday' and children_count and children_count > 25:
            self.add_error('children_count', 'Максимум 25 детей для Дня рождения')

        if booking_type == 'vr' and children_count and children_count > 10:
            self.add_error('children_count', 'Максимум 10 участников для VR-арены')

        # Валидация специальных полей
        if booking_type == 'animation' and not location:
            self.add_error('location', 'Укажите адрес для выездной анимации')

        if booking_type == 'other' and not custom_type:
            self.add_error('custom_type', 'Укажите тип мероприятия')

        return cleaned_data