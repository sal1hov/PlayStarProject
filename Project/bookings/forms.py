# bookings/forms.py
from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['event_name', 'event_date', 'status']