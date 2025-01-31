# staff/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.models import Group
from main.models import CustomUser  # Используем кастомную модель пользователя
from bookings.models import Booking  # Предполагается, что модель бронирований находится в приложении bookings

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
    if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        # Получаем всех пользователей системы
        users = CustomUser.objects.all()  # Используем кастомную модель пользователя
        paginator = Paginator(users, 5)  # Показывать по 5 пользователей на странице
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Получаем все бронирования
        bookings = Booking.objects.all()

        return render(request, 'staff/admin_dashboard.html', {'users': page_obj, 'bookings': bookings})
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Admin'))
def edit_user(request, user_id):
    if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        user_to_edit = get_object_or_404(CustomUser, id=user_id)  # Используем кастомную модель пользователя
        # Ваш логик для редактирования пользователя
        # Например, форма для редактирования пользователя и сохранение изменений
        # ...
        return render(request, 'staff/edit_user.html', {'user': user_to_edit})
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Admin'))
def delete_user(request, user_id):
    if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        user_to_delete = get_object_or_404(CustomUser, id=user_id)  # Используем кастомную модель пользователя
        user_to_delete.delete()
        messages.success(request, 'Пользователь успешно удален.')
        return redirect('admin_dashboard')
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def manage_booking(request, booking_id, action):
    if request.user.groups.filter(name='Admin').exists() or request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
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
            # ...
            pass
        else:
            messages.error(request, 'Неверное действие.')
        return redirect('admin_dashboard')
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def manager_dashboard(request):
    if request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        # Здесь можно добавить логику для панели менеджера
        # Например, получить список бронирований или других данных, которые нужны менеджеру
        bookings = Booking.objects.all()
        return render(request, 'staff/manager_dashboard.html', {'bookings': bookings})
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Staff'))
def employee_dashboard(request):
    if request.user.groups.filter(name='Staff').exists():
        # Здесь можно добавить логику для панели сотрудника
        # Например, получить список задач или других данных, которые нужны сотруднику
        return render(request, 'staff/employee_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит