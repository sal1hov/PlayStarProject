from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Booking

class BookingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Если enforce_future_date True – проверяем, что дата не в прошлом.
        self.enforce_future_date = kwargs.pop('enforce_future_date', True)
        # Если exclude_status True – удаляем поле status из формы
        exclude_status = kwargs.pop('exclude_status', False)
        super().__init__(*args, **kwargs)
        if exclude_status:
            self.fields.pop('status', None)

    class Meta:
        model = Booking
        # Поле status остается в Meta, но может быть исключено в __init__
        fields = ['event_name', 'event_date', 'status', 'children_count', 'comment']
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
            'children_count': forms.NumberInput(attrs={
                'class': 'w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
        }

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and self.enforce_future_date and event_date < timezone.now():
            raise ValidationError("Дата мероприятия не может быть в прошлом!")
        return event_date