from django.contrib import admin
from .models import Booking
from .forms import BookingForm

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'get_booking_type_display',
        'event_date',
        'status',
        'paid_amount',
        'prepayment_amount'
    ]
    list_filter = ['status', 'prepayment', 'booking_type']

    def get_booking_type_display(self, obj):
        return obj.get_booking_type_display()

    get_booking_type_display.short_description = 'Тип бронирования'