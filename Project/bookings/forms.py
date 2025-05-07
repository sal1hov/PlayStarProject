from django import forms
from .models import Booking
from django.utils import timezone
from django.core.exceptions import ValidationError


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['event_name', 'event_date', 'children_count', 'comment']
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, enforce_future_date=True, exclude_status=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.enforce_future_date = enforce_future_date
        if exclude_status:
            self.fields.pop('status', None)

        # Установка минимальной даты
        if 'event_date' in self.fields:
            self.fields['event_date'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and self.enforce_future_date and event_date < timezone.now():
            raise ValidationError("Дата мероприятия не может быть в прошлом")
        return event_date

    def clean(self):
        cleaned_data = super().clean()
        # Дополнительные проверки можно добавить здесь
        return cleaned_data