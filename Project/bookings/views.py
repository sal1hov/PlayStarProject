from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Booking
from .forms import BookingForm
from staff.views import role_required
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.utils.dateparse import parse_date
# Импортируем модель Event из приложения staff
from staff.models import Event

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
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
    if request.user.groups.filter(name__in=['Admin', 'Manager']).exists() or request.user.is_superuser:
        booking = get_object_or_404(Booking, id=booking_id)
        enforce = False  # Администратор/менеджер может редактировать даже с прошедшей датой
    else:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        enforce = True   # Обычный пользователь – дата не должна быть в прошлом

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking, enforce_future_date=enforce)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Бронирование успешно обновлено!'})
        else:
            return JsonResponse({'success': False, 'message': 'Исправьте ошибки в форме.', 'errors': form.errors})
    else:
        form = BookingForm(instance=booking, enforce_future_date=enforce)
    return render(request, 'bookings/edit_booking.html', {'form': form, 'booking': booking})

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
            else:
                booking.edited_by = ""
            booking.save()
            messages.success(request, 'Бронирование успешно обновлено!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Ошибка при обновлении бронирования.')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/edit_booking_admin.html', {'form': form, 'booking': booking})

@login_required
def delete_booking(request, booking_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    if request.user.is_superuser or request.user.is_staff:
        booking = get_object_or_404(Booking, id=booking_id)
    else:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    booking.delete()
    messages.success(request, 'Бронирование успешно удалено.')

    if request.user.is_superuser or request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('profile')

@login_required
def create_booking(request):
    if request.method == 'POST':
        # Передаём exclude_status=True, чтобы пользователю не показывалось поле status
        form = BookingForm(request.POST, exclude_status=True)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            # Устанавливаем автоматический статус для нового бронирования
            booking.status = 'active'  # 'active' будет отображаться как "На модерации"
            booking.save()

            # Создаем мероприятие и сохраняем связь с бронированием
            Event.objects.create(
                name=booking.event_name,
                description=booking.comment or 'Событие создано по бронированию.',
                date=booking.event_date,
                location='Не указано',  # Можно заменить на нужное значение
                event_type='birthday',  # Фиксированное значение для бронирований
                moderation_status='pending',  # По умолчанию мероприятие на модерации
                booking=booking  # Привязываем бронирование
            )

            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно создано! Ожидайте звонка от менеджера или подтверждения на сайте.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при создании бронирования. Проверьте данные.',
                'errors': form.errors
            })
    return JsonResponse({
        'success': False,
        'message': 'Недопустимый метод запроса.'
    })
