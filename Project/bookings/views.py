# Project/bookings/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.views.decorators.http import require_http_methods

import logging
logger = logging.getLogger(__name__)

from main.models import Profile
from bookings.models import Booking
from staff.models import Event, BirthdayPackage   # ← подключаем BirthdayPackage
from bookings.forms import BookingForm  # импорт формы бронирования


@login_required
def profile(request):
    user = request.user

    # Загружаем бронирования пользователя и связанные с ними события
    bookings = Booking.objects.filter(user=user).order_by('-event_date')
    user_events = Event.objects.filter(booking__user=user)

    # Добавляем все пакеты "День рождения" в контекст, чтобы шаблон мог их отобразить
    birthday_packages = BirthdayPackage.objects.all()

    return render(request, 'accounts/profile.html', {
        'user': user,
        'bookings': bookings,
        'user_events': user_events,
        'birthday_packages': birthday_packages,  # ← передаём в шаблон
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name='Admin').exists() or
                              u.groups.filter(name='Manager').exists() or
                              u.is_superuser)
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user

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
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user

    if not (user == booking.user or
            user.groups.filter(name__in=['Admin', 'Manager']).exists() or
            user.is_superuser):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Доступ запрещён'}, status=403)
        messages.error(request, 'У вас нет прав для редактирования этого бронирования.')
        return redirect('profile')

    if booking.status == 'approved':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False,
                                  'message': 'Нельзя редактировать подтверждённое бронирование'},
                                 status=400)
        messages.error(request, 'Нельзя редактировать подтверждённое бронирование.')
        return redirect('profile')

    enforce_future_date = not (user.groups.filter(name__in=['Admin', 'Manager']).exists() or
                               user.is_superuser)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking, enforce_future_date=enforce_future_date)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True,
                                     'message': 'Бронирование успешно обновлено!'},
                                    status=200)
            messages.success(request, 'Бронирование успешно обновлено!')
            return redirect('profile')

        errors = {field: errors for field, errors in form.errors.items()}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Исправьте ошибки в форме',
                'errors': errors
            }, status=200)
    else:
        form = BookingForm(instance=booking, enforce_future_date=enforce_future_date)

    return render(request, 'bookings/edit_booking.html', {
        'form': form,
        'booking': booking,
        'today': timezone.now().strftime('%Y-%m-%dT%H:%M')
    })


@login_required
@user_passes_test(lambda u: u.groups.filter(name='Admin').exists() or
                              u.groups.filter(name='Manager').exists() or
                              u.is_superuser)
def edit_booking_admin(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            booking_obj = form.save(commit=False)
            user = request.user
            if user.groups.filter(name='Admin').exists():
                booking_obj.edited_by = "Администратор"
            elif user.groups.filter(name='Manager').exists():
                booking_obj.edited_by = "Менеджер"
            booking_obj.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True}, status=200)
            messages.success(request, 'Бронирование успешно обновлено!')
            return redirect('staff:admin-dashboard')

        errors = {field: errors for field, errors in form.errors.items()}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Исправьте ошибки в форме',
                'errors': errors
            }, status=200)
    else:
        form = BookingForm(instance=booking)

    return render(request, 'bookings/edit_booking_admin.html', {
        'form': form,
        'booking': booking
    })


@login_required
def delete_booking(request, booking_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    booking = get_object_or_404(Booking, id=booking_id)
    user = request.user

    if not (user == booking.user or
            user.groups.filter(name__in=['Admin', 'Manager']).exists()):
        return JsonResponse({'success': False, 'error': 'Доступ запрещён'}, status=403)

    if booking.status == 'approved':
        return JsonResponse({'success': False,
                              'error': 'Нельзя удалить подтверждённое бронирование'},
                             status=400)

    try:
        Event.objects.filter(booking=booking).delete()
        booking.delete()
        return JsonResponse({'success': True, 'message': 'Бронирование удалено'}, status=200)
    except Exception as e:
        logger.error(f"Booking deletion error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Ошибка сервера'}, status=500)


@login_required
@require_http_methods(["POST"])
def create_booking(request):
    form = BookingForm(request.POST, enforce_future_date=True)

    if form.is_valid():
        try:
            booking = form.save(commit=False)
            booking.user = request.user

            if booking.booking_type == 'other' and form.cleaned_data.get('custom_type'):
                booking.event_name = form.cleaned_data['custom_type']
            else:
                booking.event_name = booking.get_booking_type_display()

            booking.save()
            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно создано! Ожидайте подтверждения.',
                'redirect_url': '/profile/'
            }, status=200)
        except Exception as e:
            logger.error(f"Ошибка создания бронирования: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Внутренняя ошибка сервера'}, status=500)
    else:
        errors = {field: errors for field, errors in form.errors.items()}
        return JsonResponse({
            'success': False,
            'message': 'Исправьте ошибки в форме',
            'errors': errors
        }, status=200)
