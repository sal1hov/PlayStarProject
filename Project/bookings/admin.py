from django.contrib import admin
from .models import Booking
from .forms import BookingForm

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingForm
    list_display = ['event_name', 'event_date', 'status', 'paid_amount']
    list_filter = ['status', 'prepayment']