# bookings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Booking
from .forms import BookingForm  # Импортируем форму для бронирований
from staff.views import role_required  # Импортируем функцию role_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date


@login_required
@user_passes_test(role_required('Admin', 'Manager'))  # Используем импортированную функцию
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
        if action == 'approve':
            booking.status = 'Подтверждено'
            booking.save()
            messages.success(request, 'Бронирование успешно утверждено.')
        elif action == 'reject':
            booking.status = 'Отклонено'
            booking.save()
            messages.success(request, 'Бронирование успешно отклонено.')
        else:
            messages.error(request, 'Неверное действие.')
        return redirect('admin_dashboard')
    return redirect('index')  # Перенаправление, если роль не подходит


from django.utils import timezone


@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)

        if form.is_valid():
            # Если форма прошла валидацию, сохраняем
            form.save()
            return JsonResponse({'success': True, 'message': 'Бронирование успешно обновлено!'})
        else:
            # Вывод ошибок в консоль для отладки
            print(form.errors)  # Выведет ошибки в консоль
            return JsonResponse({'success': False, 'message': 'Исправьте ошибки в форме.', 'errors': form.errors})

    else:
        form = BookingForm(instance=booking)

    return render(request, 'bookings/edit_booking.html', {'form': form, 'booking': booking})

@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)  # Проверяем, что бронирование принадлежит текущему пользователю
    booking.delete()
    messages.success(request, 'Бронирование успешно удалено.')
    return redirect('profile')


@login_required
def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            return JsonResponse({
                'success': True,
                'message': 'Бронирование успешно создано! Ожидайте звонка от менеджера или подтверждения на сайте.'
            })
        else:
            # Возвращаем ошибки формы
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при создании бронирования. Проверьте данные.',
                'errors': form.errors  # Добавляем ошибки формы в ответ
            })
    return JsonResponse({
        'success': False,
        'message': 'Недопустимый метод запроса.'
    })