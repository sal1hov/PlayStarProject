from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Booking
from .forms import BookingForm  # Импортируем форму для бронирований
from staff.views import role_required  # Импортируем функцию role_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.http import HttpResponseNotAllowed

@login_required
@user_passes_test(role_required('Admin', 'Manager'))  # Доступ для администраторов и менеджеров
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

@login_required
def edit_booking(request, booking_id):
    # Если пользователь является администратором, менеджером или суперпользователем – разрешаем редактирование любого бронирования
    if request.user.groups.filter(name__in=['Admin', 'Manager']).exists() or request.user.is_superuser:
        booking = get_object_or_404(Booking, id=booking_id)
    else:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Бронирование успешно обновлено!'})
        else:
            print(form.errors)
            return JsonResponse({'success': False, 'message': 'Исправьте ошибки в форме.', 'errors': form.errors})
    else:
        form = BookingForm(instance=booking)

    return render(request, 'bookings/edit_booking.html', {'form': form, 'booking': booking})

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def edit_booking_admin(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            # Устанавливаем значение в поле edited_by в зависимости от роли текущего пользователя
            if request.user.groups.filter(name='Admin').exists():
                booking.edited_by = "Администратор"
            elif request.user.groups.filter(name='Manager').exists():
                booking.edited_by = "Менеджер"
            else:
                booking.edited_by = ""
            booking.save()
            # Если запрос отправлен через AJAX, возвращаем JSON, иначе делаем редирект
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                messages.success(request, 'Бронирование успешно обновлено!')
                return redirect('admin_dashboard')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Ошибка при обновлении бронирования.', 'errors': form.errors})
            else:
                messages.error(request, 'Ошибка при обновлении бронирования.')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/edit_booking_admin.html', {'form': form, 'booking': booking})


@login_required
def delete_booking(request, booking_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    # Если пользователь — администратор или сотрудник, удаляем бронирование независимо от владельца.
    # Иначе, ищем бронирование, принадлежащее только текущему пользователю.
    if request.user.is_superuser or request.user.is_staff:
        booking = get_object_or_404(Booking, id=booking_id)
    else:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    booking.delete()
    messages.success(request, 'Бронирование успешно удалено.')

    # Перенаправляем в зависимости от роли пользователя
    if request.user.is_superuser or request.user.is_staff:
        return redirect('admin_dashboard')
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
            return JsonResponse({
                'success': False,
                'message': 'Ошибка при создании бронирования. Проверьте данные.',
                'errors': form.errors
            })
    return JsonResponse({
        'success': False,
        'message': 'Недопустимый метод запроса.'
    })
