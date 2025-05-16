from django import forms
from .models import Booking
from django.utils import timezone
from django.core.exceptions import ValidationError


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['booking_type', 'event_date', 'children_count', 'comment', 'location', 'custom_type']
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
            'children_count': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, enforce_future_date=True, exclude_status=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.enforce_future_date = enforce_future_date
        if exclude_status:
            self.fields.pop('status', None)

        if 'event_date' in self.fields:
            self.fields['event_date'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and self.enforce_future_date and event_date < timezone.now():
            raise ValidationError("Дата мероприятия не может быть в прошлом")
        return event_date

    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get('booking_type')
        children_count = cleaned_data.get('children_count')

        if booking_type == 'birthday' and children_count > 25:
            self.add_error('children_count', 'Максимальное количество детей для Дня рождения - 25')

        if booking_type == 'vr' and children_count > 10:
            self.add_error('children_count', 'Максимальное количество участников для VR-арены - 10')

        if booking_type == 'animation' and not cleaned_data.get('location'):
            self.add_error('location', 'Для выездной анимации необходимо указать адрес')

        if booking_type == 'other' and not cleaned_data.get('custom_type'):
            self.add_error('custom_type', 'Укажите тип мероприятия для варианта "Другое"')

        return cleaned_data