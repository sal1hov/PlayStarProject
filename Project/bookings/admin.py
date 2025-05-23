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
        'prepayment'  # Исправлено с prepayment_amount на существующее поле
    ]
    list_filter = ['status', 'booking_type']  # Удален несуществующий фильтр prepayment
    form = BookingForm

    def get_booking_type_display(self, obj):
        return obj.get_booking_type_display()
    get_booking_type_display.short_description = 'Тип бронирования'