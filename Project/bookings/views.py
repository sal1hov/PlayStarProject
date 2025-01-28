from django.shortcuts import render
from .models import Booking

def booking_history(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')[:5]  # Последние 5 бронирований
    return render(request, 'bookings/history.html', {'bookings': bookings})