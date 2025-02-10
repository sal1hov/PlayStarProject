from django.contrib import admin
from .models import Booking
from .forms import BookingForm

class BookingAdmin(admin.ModelAdmin):
    form = BookingForm

admin.site.register(Booking, BookingAdmin)
