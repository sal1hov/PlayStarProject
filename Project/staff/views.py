# staff/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from main.models import CustomUser  # Используем кастомную модель пользователя
from bookings.models import Booking  # Предполагается, что модель бронирований находится в приложении bookings
from django.core.paginator import Paginator  # Добавь этот импорт


def role_required(*group_names):
    """Декоратор для проверки групп."""
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)
@login_required
@user_passes_test(role_required('Admin'))
def admin_dashboard(request):
    users = CustomUser.objects.all()  # Используем кастомную модель пользователя
    paginator = Paginator(users, 5)  # Показывать по 5 пользователей на странице
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    bookings = Booking.objects.all()

    return render(request, 'staff/admin_dashboard.html', {'users': page_obj, 'bookings': bookings})

@login_required
@user_passes_test(role_required('Admin'))
def edit_user(request, user_id):
    if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        user_to_edit = get_object_or_404(CustomUser, id=user_id)  # Используем кастомную модель пользователя

        if request.method == 'POST':
            # Получаем данные из формы
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            children = request.POST.get('children')
            phone = request.POST.get('phone')
            password = request.POST.get('password')

            # Обновляем данные пользователя
            user_to_edit.username = username
            user_to_edit.first_name = first_name
            user_to_edit.last_name = last_name
            user_to_edit.children = children
            user_to_edit.phone = phone

            if password:
                user_to_edit.set_password(password)  # Если пароль был изменен, обновляем его

            user_to_edit.save()

            # Если пароль был изменен, необходимо обновить сессию
            if password:
                update_session_auth_hash(request, user_to_edit)

            messages.success(request, 'Пользователь успешно обновлен.')
            return redirect('admin_dashboard')

        return render(request, 'staff/edit_user.html', {'user': user_to_edit})
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Admin'))
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(CustomUser, id=user_id)  # Используем кастомную модель пользователя
    user_to_delete.delete()
    messages.success(request, 'Пользователь успешно удален.')
    return redirect('admin_dashboard')

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
    elif action == 'edit':
        # Логика для редактирования бронирования
        pass
    else:
        messages.error(request, 'Неверное действие.')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def manager_dashboard(request):
    bookings = Booking.objects.all()
    return render(request, 'staff/manager_dashboard.html', {'bookings': bookings})

@login_required
@user_passes_test(role_required('Staff'))
def employee_dashboard(request):
    return render(request, 'staff/employee_dashboard.html')
