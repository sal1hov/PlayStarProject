# bookings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Booking
from .forms import BookingForm  # Предполагается, что форма создана в bookings/forms.py

def role_required(*group_names):
    """Декоратор для проверки групп."""
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно отредактировано.')
            return redirect('admin_dashboard')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/edit_booking.html', {'form': form, 'booking': booking})

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if action == 'approve':
        booking.status = 'approved'
        booking.save()
        messages.success(request, 'Бронирование успешно утверждено.')
    elif action == 'reject':
        booking.status = 'rejected'
        booking.save()
        messages.success(request, 'Бронирование успешно отклонено.')
    else:
        messages.error(request, 'Неверное действие.')
    return redirect('admin_dashboard')

@login_required
def booking_history(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')[:5]  # Последние 5 бронирований
    return render(request, 'bookings/history.html', {'bookings': bookings})