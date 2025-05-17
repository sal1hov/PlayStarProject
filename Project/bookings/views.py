from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Booking
from .forms import BookingForm
from staff.views import role_required
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.utils.dateparse import parse_date
from staff.models import Event
import traceback
from django.views.decorators.csrf import csrf_exempt
import logging
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(
            name='Manager').exists() or request.user.is_superuser:
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
    return redirect('index')


@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Проверка прав доступа
    if not (request.user == booking.user or
            request.user.groups.filter(name__in=['Admin', 'Manager']).exists() or
            request.user.is_superuser):
        messages.error(request, 'У вас нет прав для редактирования этого бронирования.')
        return redirect('profile')

    # Проверка статуса бронирования
    if booking.status == 'approved':
        messages.error(request, 'Нельзя редактировать подтвержденное бронирование.')
        return redirect('profile')

    # Проверка даты мероприятия (для обычных пользователей)
    enforce_future_date = not (request.user.groups.filter(name__in=['Admin', 'Manager']).exists() or
                               request.user.is_superuser)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking, enforce_future_date=enforce_future_date)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно обновлено!')
            return redirect('profile')
    else:
        form = BookingForm(instance=booking, enforce_future_date=enforce_future_date)

    return render(request, 'bookings/edit_booking.html', {
        'form': form,
        'booking': booking,
        'today': timezone.now().strftime('%Y-%m-%dT%H:%M')
    })


@login_required
@role_required('Admin', 'Manager')
def edit_booking_admin(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            if request.user.groups.filter(name='Admin').exists():
                booking.edited_by = "Администратор"
            elif request.user.groups.filter(name='Manager').exists():
                booking.edited_by = "Менеджер"
            booking.save()
            messages.success(request, 'Бронирование успешно обновлено!')
            return redirect('admin_dashboard')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/edit_booking_admin.html', {
        'form': form,
        'booking': booking
    })


@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not (request.user == booking.user or
            request.user.groups.filter(name__in=['Admin', 'Manager']).exists()):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    if booking.status == 'approved':
        return JsonResponse({'error': 'Нельзя удалить подтвержденное бронирование'}, status=400)

    try:
        Event.objects.filter(booking=booking).delete()
        booking.delete()
        return JsonResponse({'success': True, 'message': 'Бронирование удалено'})
    except Exception as e:
        logger.error(f"Booking deletion error: {str(e)}")
        return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@login_required
def create_booking(request):
    if request.method == 'POST':
        try:
            form = BookingForm(request.POST, enforce_future_date=True)
            if form.is_valid():
                booking = form.save(commit=False)
                booking.user = request.user
                booking.status = 'pending'

                if form.cleaned_data['booking_type'] == 'other':
                    booking.event_name = form.cleaned_data['custom_type']
                else:
                    booking.event_name = booking.get_booking_type_display()

                booking.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Бронирование успешно создано! Ожидайте звонка от менеджера.'
                })
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        except Exception as e:
            logger.error(f"Booking creation error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Ошибка сервера при создании бронирования'
            }, status=500)
    return JsonResponse({
        'success': False,
        'message': 'Недопустимый метод запроса'
    }, status=405)
